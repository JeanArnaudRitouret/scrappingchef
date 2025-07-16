import os
import subprocess
from dotenv import load_dotenv

"""
    Move content files from local directory to GCS bucket.
    Content files are scraped files from the original website and used to generate the content of the new website.
    Args:
        local_directory (str): Local directory to move files from
        bucket_name (str): GCS bucket name
    Raises:
        Exception: If local directory does not exist
    """

load_dotenv()
BUCKET_NAME = os.getenv('BUCKET_NAME')

def move_files_to_gcs(local_directory, bucket_name):
    # Ensure the local directory exists
    if not os.path.exists(local_directory):
        raise Exception(f"Local directory {local_directory} does not exist.")

    # List files in the GCS bucket
    existing_files = subprocess.check_output(['gsutil', 'ls', f'gs://{bucket_name}/']).decode().splitlines()
    existing_files = [os.path.basename(file) for file in existing_files]

    # Get local files
    local_files = os.listdir(local_directory)

    # Filter out files that already exist in GCS
    files_to_move = [file for file in local_files if file not in existing_files]

    if not files_to_move:
        print("No new files to move.")
        return

    # Construct the gsutil command
    command = ['gsutil', '-m', 'cp'] + [os.path.join(local_directory, file) for file in files_to_move] + [f'gs://{bucket_name}/']

    try:
        # Execute the command
        subprocess.run(command, check=True)
        print(f"Successfully moved files from {local_directory} to gs://{bucket_name}/")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    move_files_to_gcs('platform_new/contents', BUCKET_NAME)
