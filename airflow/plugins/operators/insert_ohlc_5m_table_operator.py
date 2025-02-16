from airflow.models.baseoperator import BaseOperator
from hooks.custom_gcs_hook import CustomGcsHook
from hooks.custom_postgres_hook import CustomPostgresHook
import pyarrow.compute as pc
from datetime import datetime, timedelta
import psycopg2


class InsertOhlc5mTableOperator(BaseOperator):
    def __init__(self, ticker, gcs_conn_id, postgres_conn_id, json_to_parquet_task_id, **kwargs):
        super().__init__(**kwargs)
        self.ticker = ticker
        self.gcs_conn_id = gcs_conn_id
        self.postgres_conn_id = postgres_conn_id
        self.json_to_parquet_task_id = json_to_parquet_task_id

    def execute(self, context):
        # custom_hook
        custom_gcs_hook = CustomGcsHook(gcs_conn_id=self.gcs_conn_id)
        custom_postgres_hook = CustomPostgresHook(postgres_conn_id=self.postgres_conn_id)

        # bucket에서 parquet 읽어오기
        bucket_name = "upbit-orderbook-cts-parquet-1"
        ti = context['ti']
        blob_name = ti.xcom_pull(task_ids=self.json_to_parquet_task_id)
        table = custom_gcs_hook.load_parquet_from_bucket(bucket_name, blob_name)

        # 정렬
        table = table.sort_by([('timestamp', 'ascending')])

        # price 계산 구하기 
        ask_price1_column = table['ask_price1']
        bid_price1_column = table['bid_price1']
        sum_price_column = pc.add(ask_price1_column, bid_price1_column)
        price_column = pc.divide(sum_price_column, 2)

        # 저가, 고가 계산
        min_max_price = pc.min_max(price_column)
        high_price = min_max_price['max'].as_py()
        low_price = min_max_price['min'].as_py()

        # 시가, 종가 
        open_price = price_column[0].as_py()
        close_price = price_column[-1].as_py()

        # date
        start_time_str = context.get('data_interval_start').in_timezone('Asia/Seoul').strftime('%Y-%m-%d %H:%M')
        dt_object = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        event_time = dt_object.strftime('%Y-%m-%d %H:%M')
        event_date = dt_object.strftime('%Y%m%d')
        next_event_date = dt_object + timedelta(days=1)
        next_event_date = next_event_date.strftime('%Y%m%d')

        # data
        data = {'ticker': self.ticker,
                'event_time': event_time,
                'event_date': event_date,
                'next_event_date': next_event_date,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price
               }
        
        self.log.info(f"data: {data}")

        # insert data
        try:
            custom_postgres_hook.insert_data_into_ohlc_table(data, '5m')
            custom_postgres_hook.close_conn()

        # create table
        except psycopg2.errors.UndefinedTable:
            custom_postgres_hook.rollback()
            
            custom_postgres_hook.create_ohlc_table(self.ticker, '5m')
            custom_postgres_hook.create_ohlc_table_partition(self.ticker, '5m', data['event_date'], data['next_event_date'])
            custom_postgres_hook.insert_data_into_ohlc_table(data, '5m')

            custom_postgres_hook.close_conn()

        # create partition
        except psycopg2.IntegrityError as e:
            if "no partition of relation" in str(e):
                custom_postgres_hook.rollback()
                
                custom_postgres_hook.create_ohlc_table_partition(self.ticker, '5m', data['event_date'], data['next_event_date'])
                custom_postgres_hook.insert_data_into_ohlc_table(data, '5m')
                
                custom_postgres_hook.close_conn()
            
            else:
                custom_postgres_hook.close_conn()
                raise e

        except Exception as e:                
            custom_postgres_hook.close_conn()
            raise e
