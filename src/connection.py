import os
import logging
import time
import psycopg2


def connect_to_postgres():
    while True:
        try:
            conn = psycopg2.connect(
                                host=os.getenv('POSTGRES_HOST'),  
                                port=os.getenv('POSTGRES_PORT'),
                                user=os.getenv('POSTGRES_USER'),   
                                password=os.getenv('POSTGRES_PASSWORD'),
                                database="cryptostream"
                            )
            logging.info("Connected to Postgres")
            return conn

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logging.error(f"Postgres Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)