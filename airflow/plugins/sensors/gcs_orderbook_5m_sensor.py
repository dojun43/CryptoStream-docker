from airflow.sensors.base import BaseSensorOperator
from airflow.hooks.base import BaseHook
import json
from google.cloud import storage
from datetime import datetime
from dateutil.relativedelta import relativedelta


class GcsOrderbook5mSensor(BaseSensorOperator):
    def __init__(self, ticker, **kwargs):
        '''
        ticker: GCS bucket에서 확인할 ticker 명 
        '''
        super().__init__(**kwargs)
        self.ticker = ticker

        # GCS client 생성 
        gcp_conn = BaseHook.get_connection('conn-gcp-cryptostream')
        GCP_KEY = gcp_conn.extra_dejson['keyfile_dict']
        GCP_KEY = json.loads(GCP_KEY)
        self.storage_client = storage.Client.from_service_account_info(GCP_KEY)

        # bucket 연결
        GCS_BUCKET = "upbit-orderbook-cts-1"
        self.bucket = self.storage_client.get_bucket(GCS_BUCKET)
        
    def poke(self, context):
        # data_interval_end 기준 prefix 
        end_time_str = context.get('data_interval_end').in_timezone('Asia/Seoul').strftime('%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
        search_prefix = f"{self.ticker}/{end_time.strftime('%Y/%m/%d/%H/%M')}"

        # 해당 prefix를 가진 blob이 있는지 확인
        blobs = self.bucket.list_blobs(prefix=search_prefix, max_results=1)
        
        for blob in blobs:
            if blob.name.startswith(search_prefix):
                self.log.info(f"Prefix '{search_prefix}' exists in the bucket.")
                return True
            
        self.log.info(f"Prefix '{search_prefix}' does not exist in the bucket.")


        # data_interval_end + 1분 기준 prefix 
        end_time_str = (context.get('data_interval_end').in_timezone('Asia/Seoul') + relativedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
        search_prefix = f"{self.ticker}/{end_time.strftime('%Y/%m/%d/%H/%M')}"

        # 해당 prefix를 가진 blob이 있는지 확인
        blobs = self.bucket.list_blobs(prefix=search_prefix, max_results=1)
        
        for blob in blobs:
            if blob.name.startswith(search_prefix):
                self.log.info(f"Prefix '{search_prefix}' exists in the bucket.")
                return True
            
        self.log.info(f"Prefix '{search_prefix}' does not exist in the bucket.")

        return False