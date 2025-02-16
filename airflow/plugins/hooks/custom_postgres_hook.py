from airflow.hooks.base import BaseHook
import psycopg2
import pandas as pd
from psycopg2 import sql


class CustomPostgresHook(BaseHook):
    def __init__(self, postgres_conn_id, **kwargs):
        self.postgres_conn_id = postgres_conn_id

        # postgres connection
        postgres_conn_info = BaseHook.get_connection(self.postgres_conn_id)
        self.postgres_conn = psycopg2.connect(host=postgres_conn_info.host, 
                                              user=postgres_conn_info.login, 
                                              password=postgres_conn_info.password, 
                                              dbname=postgres_conn_info.schema, 
                                              port=postgres_conn_info.port)
        self.cursor = self.postgres_conn.cursor()


    def rollback(self):
        self.postgres_conn.rollback()


    def close_conn(self):
        self.cursor.close()
        self.postgres_conn.close()

        self.log.info(f"close postgres connection")
    

    def create_ohlc_table(self, ticker: str, time_interval: str):
        table_name = f"ohlc_{time_interval}_{ticker}"

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            event_time TIMESTAMP,
            event_date DATE,
            open_price NUMERIC(20, 10),
            high_price NUMERIC(20, 10),
            low_price NUMERIC(20, 10),
            close_price NUMERIC(20, 10),
            PRIMARY KEY (event_time, event_date) 
        ) PARTITION BY RANGE (event_date);
        """
        create_table_query=sql.SQL(create_table_query)

        self.cursor.execute(create_table_query)
        self.postgres_conn.commit()

        self.log.info(f"Create table: {table_name}")  


    def create_ohlc_table_partition(self, ticker: str, time_interval: str, event_date: str, next_event_date: str):
        table_name = f"ohlc_{time_interval}_{ticker}"
        partition_name = f"ohlc_{time_interval}_{event_date}_{ticker}"

        create_partition_query = f"""
        CREATE TABLE IF NOT EXISTS {partition_name}
        PARTITION OF {table_name}
        FOR VALUES FROM (%s) TO (%s);
        """
        create_partition_query=sql.SQL(create_partition_query)

        self.cursor.execute(create_partition_query, (event_date, next_event_date))
        self.postgres_conn.commit()

        self.log.info(f"Create partition: {partition_name}")
    
    
    def insert_data_into_ohlc_table(self, data: dict, time_interval: str):        
        table_name = f"ohlc_{time_interval}_{data['ticker']}"

        insert_query = f"""
        INSERT INTO {table_name} (
            event_time, 
            event_date, 
            open_price, 
            high_price, 
            low_price, 
            close_price
        ) 
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_time, event_date) 
        DO UPDATE SET 
            event_time = EXCLUDED.event_time,
            event_date = EXCLUDED.event_date,
            open_price = EXCLUDED.open_price, 
            high_price = EXCLUDED.high_price, 
            low_price = EXCLUDED.low_price, 
            close_price = EXCLUDED.close_price
        ;
        """
        insert_query = sql.SQL(insert_query)
        self.cursor.execute(insert_query, (data['event_time'],
                                           data['event_date'],
                                           data['open_price'],
                                           data['high_price'],
                                           data['low_price'],
                                           data['close_price']
                                          ))
        self.postgres_conn.commit()

        self.log.info(f"insert data into {table_name}")