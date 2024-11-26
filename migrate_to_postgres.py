import os
from pathlib import Path
import subprocess
import sys
import time
import django
from django.db import connections
from dotenv import load_dotenv

def init_django_settings():
    """Initialize Django with migration settings"""
    load_dotenv()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrappingchef.settings')
    django.setup()
    from scrappingchef.settings import DATABASES
    return DATABASES


def run_command(command, error_message, ignore_errors=False, env=None, stdout=None):
    """Execute a shell command and handle errors appropriately.
    Args:
        command (str|list): The shell command to execute
        error_message (str): Error message to display if command fails
        ignore_errors (bool): If True, return False instead of raising errors
        env (dict): Environment variables for the command
        stdout: File object to write stdout to
    Returns:
        bool: True if command succeeded, False if failed
    """
    try:
        # Use list form of command to avoid shell injection vulnerabilities
        if isinstance(command, str):
            command = command.split()

        result = subprocess.run(
            command,
            shell=False,
            check=True,
            capture_output=stdout is None,  # Only capture output if we're not redirecting
            text=True,
            encoding='utf-8',
            env=env,
            stdout=stdout
        )

        if result.stdout and stdout is None:  # Only print stdout if we're not redirecting
            print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: {error_message}", file=sys.stderr)
        if e.stderr:
            print(f"Details: {e.stderr}", file=sys.stderr)
        return ignore_errors  # Return False if we're not ignoring errors

    except Exception as e:
        print(f"Unexpected error running command: {str(e)}", file=sys.stderr)
        return ignore_errors


def wait_for_postgres(max_attempts=30, retry_interval=2, password=None, host='127.0.0.1', port=None, user=None):
    """Wait for PostgreSQL to be ready

    Args:
        max_attempts (int): Maximum number of connection attempts
        retry_interval (int): Seconds to wait between attempts
        password (str): PostgreSQL password
        port (str): PostgreSQL port
        user (str): PostgreSQL user
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be greater than 0")
    if retry_interval < 1:
        raise ValueError("retry_interval must be greater than 0")
    if not password:
        raise ValueError("Password is required")

    # Check if PostgreSQL is ready
    command = [
        'psql',
        '-h', str(host),
        '-p', str(port),
        '-U', str(user),
        '-c', '\\l'
    ]
    env = os.environ.copy()
    env['PGPASSWORD'] = password

    attempts = 0
    while attempts < max_attempts:
        try:
            subprocess.run(
                command,
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            print("PostgreSQL is ready!")
            return True
        except subprocess.CalledProcessError as e:
            attempts += 1
            if attempts == max_attempts:
                print(f"Failed to connect after {max_attempts} attempts")
                print(f"Last error: {e.stderr}")
                return False

            print(f"Waiting for PostgreSQL... ({attempts}/{max_attempts})")
            time.sleep(retry_interval)

def validate_database_settings(settings):
    """Validate that all required database settings are present.

    Args:
        settings (dict): Dictionary of database settings

    Returns:
        bool: True if all settings are valid, False otherwise
    """
    required_vars = {
        'DB_NAME': settings['NAME'],
        'DB_USER': settings['USER'],
        'DB_PASSWORD': settings['PASSWORD'],
        'DB_HOST': settings['HOST'],
        'DB_PORT': settings['PORT']
    }

    missing_vars = [var for var, val in required_vars.items() if not val]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

def start_cloud_sql_proxy(port, instance_connection_name):
    """Start Cloud SQL Proxy and return the process.

    Args:
        port (str): Port number for the proxy
        instance_connection_name (str): Full instance connection name (project:region:instance)

    Returns:
        subprocess.Popen: Running proxy process or None if startup failed
    """
    proxy_command = f"cloud-sql-proxy --port {port} {instance_connection_name}"
    proxy_process = subprocess.Popen(proxy_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Give proxy time to start
    time.sleep(2)

    if proxy_process.poll() is not None:
        _, stderr = proxy_process.communicate()
        print(f"Failed to start Cloud SQL Proxy: {stderr.decode()}")
        return None

    return proxy_process

def main():
    # Initialize Django and get database settings
    db_settings = init_django_settings()

    if not validate_database_settings(settings=db_settings['migration']):
        return

    # Get database settings
    db_migration_name = db_settings['migration']['NAME']
    db_migration_user = db_settings['migration']['USER']
    db_migration_password = db_settings['migration']['PASSWORD']
    db_migration_host = db_settings['migration']['HOST']
    db_migration_port = db_settings['migration'].get('PORT')

    proxy_process = None
    try:
        # Start Cloud SQL Proxy
        proxy_process = start_cloud_sql_proxy(
            port=db_migration_port,
            instance_connection_name="scrappingchef:europe-north1:scrappingchef"
        )
        if not proxy_process:
            return

        # Wait for PostgreSQL with timeout
        print("Waiting for PostgreSQL connection...")
        if not wait_for_postgres(
            max_attempts=30,
            retry_interval=2,
            password=db_migration_password,
            host=db_migration_host,
            port=db_migration_port,
            user=db_migration_user
        ):
            print("Could not establish PostgreSQL connection")
            return

        # Create database if it doesn't exist
        create_db_command = [
            'psql',
            '-h', str(db_migration_host),
            '-p', str(db_migration_port),
            '-U', str(db_migration_user),
            '-c', f'CREATE DATABASE {str(db_migration_name)};'
        ]
        env = os.environ.copy()
        env['PGPASSWORD'] = db_migration_password

        print(f"Checking/creating database '{db_migration_name}'...")
        db_created = run_command(create_db_command, "Database already exists", ignore_errors=True, env=env)
        if not db_created:
            print("Database already exists - continuing with migration")
        else:
            print("Database created successfully")

        # Add a small delay to ensure connection is stable
        time.sleep(2)

        # Create export file from local sqlite3 database
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        export_file = f"data_export_{timestamp}.json"

        print(f"Creating export data file at {export_file}...")
        with open(export_file, 'w') as f:
            dump_command = [
                'python', 'manage.py', 'dumpdata',
                '--exclude', 'contenttypes',
                '--exclude', 'auth.permission',
                '--indent', '2'
            ]
            if not run_command(dump_command, "Failed to create export file", stdout=f):
                return

        print("Export file created successfully!")

        # Apply migrations with proper error handling
        print("Applying migrations to PostgreSQL...")
        if not run_command("python manage.py migrate --noinput --database migration", "Failed to apply migrations"):
            return

        # Load data with progress indication
        print("Loading data into PostgreSQL...")
        if not run_command(f"python manage.py loaddata {export_file} --database migration", "Failed to load data"):
            return

        print("Migration completed successfully!")

        # Cleanup while preserving backup
        print("Cleaning up...")
        print(f"Backup file preserved at: {export_file}")

    except Exception as e:
        print(f"An error occurred during migration: {str(e)}")
        return

    finally:
        # Ensure Cloud SQL Proxy is properly terminated
        if proxy_process:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_process.kill()

        # Additional cleanup of any proxy processes
        subprocess.run(["pkill", "-f", "cloud-sql-proxy"],
                      capture_output=True,
                      check=False)

if __name__ == "__main__":
    main()