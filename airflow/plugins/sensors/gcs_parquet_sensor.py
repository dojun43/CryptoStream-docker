from airflow.sensors.base import BaseSensorOperator
from airflow.hooks.base import BaseHook
import json
from google.cloud import storage


class GcsParquetSensor(BaseSensorOperator):
    def __init__(self, json_to_parquet_task_id, **kwargs):
        '''
        ticker: GCS bucket에서 확인할 ticker 명 
        '''
        super().__init__(**kwargs)

        # GCS client 생성 
        gcp_conn = BaseHook.get_connection('conn-gcp-cryptostream')
        GCP_KEY = gcp_conn.extra_dejson['keyfile_dict']
        GCP_KEY = json.loads(GCP_KEY)
        self.storage_client = storage.Client.from_service_account_info(GCP_KEY)

        # bucket 연결
        GCS_BUCKET = "upbit-orderbook-cts-parquet-1"
        self.bucket = self.storage_client.get_bucket(GCS_BUCKET)

        self.json_to_parquet_task_id = json_to_parquet_task_id
        
    def poke(self, context):
        ti = context['ti']
        blob_name = ti.xcom_pull(task_ids=self.json_to_parquet_task_id)

        # 해당 prefix를 가진 blob이 있는지 확인
        blobs = self.bucket.list_blobs(prefix=blob_name, max_results=1)
        
        for blob in blobs:
            if blob.name.startswith(blob_name):
                self.log.info(f"Prefix '{blob_name}' exists in the bucket.")
                return True
            
        self.log.info(f"Prefix '{blob_name}' does not exist in the bucket.")
        return False