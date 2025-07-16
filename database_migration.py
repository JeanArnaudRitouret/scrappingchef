# Dump data from local sqlite3 database to json file
# python manage.py dumpdata --natural-primary --natural-foreign --exclude auth.permission --exclude contenttypes > db.json
# python manage.py dumpdata > db.json

import os
import django
from django.core.management import call_command
from datetime import datetime
from django.apps import apps

def migrate_sqlite_to_postgres():
    # Define the paths for the JSON data dump
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dump_file = f'data_export_{timestamp}.json'
    print(f"Dump file: {dump_file}")

    # Set the environment variable to use the Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrappingchef.settings')

    # Initialize Django
    django.setup()

    # Debug: Print installed apps
    from django.conf import settings
    print("\nInstalled apps:")
    print(settings.INSTALLED_APPS)

    call_command('makemigrations')
    call_command('migrate', database='migration')

    # Debug version to see what's being dumped
    print("Dumping data from SQLite database...")
    print("\nAvailable models:")
    for model in apps.get_models():
        print(f"- {model._meta.app_label}.{model._meta.model_name}")
        print(f"  Count: {model.objects.using('default').count()}")

    # Try explicitly dumping platform_new
    with open(dump_file, 'w') as f:
        call_command('dumpdata',
                    'platform_new',  # Explicitly specify platform_new
                    '--natural-primary',
                    '--natural-foreign',
                    '--exclude', 'auth.permission',
                    '--exclude', 'contenttypes',
                    '--verbosity', 2,
                    stdout=f,
                    database='default')
        breakpoint()

    # Load data into the PostgreSQL database using the 'migration' alias
    print("Loading data into PostgreSQL database...")
    with open(dump_file, 'r') as f:
        call_command('loaddata', dump_file, database='migration')

    # Clean up the dump file
    # os.remove(dump_file)
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
