import os
import logging
import time
from google.cloud import storage

def connect_to_gcs():
    while True:
        try:
            storage_client = storage.Client.from_service_account_json(os.getenv('KEY_PATH'))
            bucket = storage_client.get_bucket(os.getenv('BUCKET_NAME'))

            logging.info("Connected to GCS")
            return bucket

        except Exception as e:
            logging.error(f"GCS Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)