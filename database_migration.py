"""
    This script is used to migrate data from the local PostgreSQL database to the Cloud SQL PostgreSQL database.
"""


import psycopg
from psycopg.rows import dict_row
from django.conf import settings
from django.core.management import call_command
import os
import django
from contextlib import contextmanager
from platform_new.decorators import local_environment_required
from platform_new.scrapper.logger import get_logger
from google.cloud import secretmanager

logger = get_logger(__name__)

TABLES_TO_COPY = ["platform_new_path", "platform_new_training"]

PROJECT_ID = os.environ.get("TF_VAR_project_id") # Project id var is already set for the terraform project
if not PROJECT_ID:
    raise RuntimeError(
        "TF_VAR_project_id environment variable is not set. "
        "Please ensure your .envrc or environment exports TF_VAR_project_id."
    )

def _get_local_db_settings() -> dict:
    """Get local database settings in Django format."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scrappingchef.settings")
    return settings.DATABASES["default"]


def _get_local_db_connection_params() -> dict:
    """Get local database connection parameters for psycopg."""
    django_settings = _get_local_db_settings()
    return {
        "host": django_settings["HOST"],
        "port": django_settings["PORT"],
        "dbname": django_settings["NAME"],
        "user": django_settings["USER"],
        "password": django_settings["PASSWORD"],
    }


def _get_remote_db_settings() -> dict:
    """
    Get remote database settings from Google Secret Manager.
    
    Returns:
        Dictionary with database connection parameters for psycopg
    """
    return {
        "host": _get_secret("DB_HOST"),
        "port": int(_get_secret("DB_PORT")),
        "dbname": _get_secret("DB_NAME"),
        "user": _get_secret("DB_USER"),
        "password": _get_secret("DB_PASSWORD"),
    }


def _get_secret(secret_name: str) -> str:
    """
    Fetch a secret from Google Secret Manager.
    
    Args:
        secret_name: The name of the secret (e.g., 'DB_PASSWORD')
        
    Returns:
        The secret value as a string
        
    Raises:
        Exception: If secret cannot be fetched
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch secret '{secret_name}': {e}")
        raise


@contextmanager
def _temporary_database_settings(new_settings: dict):
    """
    Context manager to temporarily change database settings and restore them.
    
    Args:
        new_settings: Dictionary with the new database settings
    """
    original_settings = settings.DATABASES["default"].copy()
    try:
        settings.DATABASES["default"] = new_settings
        yield
    finally:
        settings.DATABASES["default"] = original_settings
        logger.info("Database settings restored to original values")


@local_environment_required
def apply_migrations_on_remote_db():
    """
    This function applies the migrations on the remote database.
    """    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scrappingchef.settings")
    
    # Get remote database settings from Secret Manager
    remote_db_settings = _get_remote_db_settings()
    
    # Create remote database settings dictionary
    remote_db_config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": remote_db_settings["dbname"],
        "USER": remote_db_settings["user"],
        "PASSWORD": remote_db_settings["password"],
        "HOST": remote_db_settings["host"],
        "PORT": remote_db_settings["port"],
    }
    
    # Use context manager to temporarily change settings to the remote database and restore them to the original local settings after the migrations are applied
    with _temporary_database_settings(remote_db_config):
        django.setup()
        call_command("makemigrations", interactive=False, verbosity=1)
        call_command("migrate", interactive=False, verbosity=1)


@local_environment_required
def copy_table_from_local_to_remote(table_name: str):
    logger.info(f"Copying table: {table_name}")
    
    local_db_connection_params = _get_local_db_connection_params()
    remote_db_settings = _get_remote_db_settings()
    
    with psycopg.connect(**local_db_connection_params, row_factory=dict_row) as src_conn, \
         psycopg.connect(**remote_db_settings) as dest_conn:

        src_cur = src_conn.cursor()
        dest_cur = dest_conn.cursor()

        src_cur.execute(f"SELECT * FROM {table_name};")
        rows = src_cur.fetchall()

        if not rows:
            logger.info(f"→ {table_name}: no rows found.")
            return

        columns = rows[0].keys()
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)

        # Use ON CONFLICT DO NOTHING to handle duplicate keys
        insert_query = f"""
            INSERT INTO {table_name} ({col_names}) 
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        try:
            dest_cur.executemany(insert_query, [tuple(row.values()) for row in rows])
            dest_conn.commit()
            logger.info(f"→ {table_name}: {len(rows)} rows processed (duplicates ignored).")
        except Exception as e:
            logger.error(f"→ {table_name}: Error during copy: {e}")
            dest_conn.rollback()
            raise


def main():
    apply_migrations_on_remote_db()
    for table in TABLES_TO_COPY:
        copy_table_from_local_to_remote(table_name=table)


if __name__ == "__main__":
    main()
