from airflow.models.baseoperator import BaseOperator
from hooks.custom_gcs_hook import CustomGcsHook
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime


class JsonToParquetOperator(BaseOperator):
    def __init__(self, ticker, gcs_conn_id, **kwargs):
        super().__init__(**kwargs)
        self.ticker = ticker
        self.gcs_conn_id = gcs_conn_id

    def execute(self, context):
        custom_gcs_hook = CustomGcsHook(gcs_conn_id=self.gcs_conn_id)

        # bucket의 patition에서 json load
        bucket_name = "upbit-orderbook-cts-1"

        start_time_str = context.get('data_interval_start').in_timezone('Asia/Seoul').strftime('%Y-%m-%d %H:%M')
        end_time_str = context.get('data_interval_end').in_timezone('Asia/Seoul').strftime('%Y-%m-%d %H:%M')
        prefixes = custom_gcs_hook.create_prefixes(self.ticker, start_time_str, end_time_str)

        data_list = []

        for prefix in prefixes:
            prefix_datas = custom_gcs_hook.load_json_from_orderbook_bucket(bucket_name, prefix)            
            data_list = data_list + prefix_datas

        # parquet schema 
        schema = pa.schema([
            ('timestamp', pa.float64()),
            ('timestamp_date', pa.string()),
            ('ask_price1', pa.float64()), ('ask_size1', pa.float64()),
            ('bid_price1', pa.float64()), ('bid_size1', pa.float64()),
            ('ask_price2', pa.float64()), ('ask_size2', pa.float64()),
            ('bid_price2', pa.float64()), ('bid_size2', pa.float64()),
            ('ask_price3', pa.float64()), ('ask_size3', pa.float64()),
            ('bid_price3', pa.float64()), ('bid_size3', pa.float64()),
            ('ask_price4', pa.float64()), ('ask_size4', pa.float64()),
            ('bid_price4', pa.float64()), ('bid_size4', pa.float64()),
            ('ask_price5', pa.float64()), ('ask_size5', pa.float64()),
            ('bid_price5', pa.float64()), ('bid_size5', pa.float64())
        ])
    
        # pyArrow Table로 변환
        table = pa.Table.from_pylist(data_list, schema=schema) 

        # upload parquet
        bucket_name = "upbit-orderbook-cts-parquet-1"

        dt_start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        date_patition = dt_start_time.strftime('%Y/%m/%d/%H')
        blob_name = f"{self.ticker}/{date_patition}/{self.ticker}-{dt_start_time.strftime('%Y%m%d%H%M')}.parquet"

        custom_gcs_hook.upload_parquet_to_bucket(bucket_name, blob_name, table)

        return blob_name