from airflow.hooks.base import BaseHook
import json
from google.cloud import storage
from datetime import datetime, timedelta
import pyarrow as pa
import pyarrow.parquet as pq
import io

class CustomGcsHook(BaseHook):
    def __init__(self, gcs_conn_id, **kwargs):
        self.gcs_conn_id = gcs_conn_id

        # gcs client 생성 
        gcp_conn = BaseHook.get_connection(self.gcs_conn_id)
        GCP_KEY = gcp_conn.extra_dejson['keyfile_dict']
        GCP_KEY = json.loads(GCP_KEY)
        self.storage_client = storage.Client.from_service_account_info(GCP_KEY)
    

    def create_prefixes(self, ticker, start_time_str, end_time_str) -> list:
        # 문자열을 datetime 객체로 변환
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')

        # 시간 간격을 1분으로 설정
        time_interval = timedelta(minutes=1)

        # 각 시간에 해당하는 prefix 생성
        prefixes = []
        current_time = start_time
        
        while current_time < end_time:
            prefix = f"{ticker}/{current_time.strftime('%Y/%m/%d/%H/%M')}"
            prefixes.append(prefix)
            current_time += time_interval

        return prefixes 


    def load_json_from_orderbook_bucket(self, bucket_name, prefix) -> list:
        # bucket 가져오기
        bucket = self.storage_client.get_bucket(bucket_name)

        # 지정된 경로의 모든 객체 목록 가져오기
        blobs = bucket.list_blobs(prefix=prefix)

        # 객체 목록 읽고 변환
        datas = []

        for blob in blobs:
            if blob.name.endswith('.jsonl'):
                # JSONL 파일 다운로드
                file_content = blob.download_as_string()

                # JSON 파싱
                for line in file_content.splitlines():
                    data = json.loads(line)
                    # 변환
                    data_dict = {'timestamp' : data['timestamp'], 
                                'timestamp_date' : data['timestamp_date'], 
                                'ask_price1' : data['orderbook'][0]['ap'], 'ask_size1' : data['orderbook'][0]['as'], 
                                'bid_price1' : data['orderbook'][0]['bp'], 'bid_size1' : data['orderbook'][0]['bs'], 
                                'ask_price2' : data['orderbook'][1]['ap'], 'ask_size2' : data['orderbook'][1]['as'], 
                                'bid_price2' : data['orderbook'][1]['bp'], 'bid_size2' : data['orderbook'][1]['bs'], 
                                'ask_price3' : data['orderbook'][2]['ap'], 'ask_size3' : data['orderbook'][2]['as'], 
                                'bid_price3' : data['orderbook'][2]['bp'], 'bid_size3' : data['orderbook'][2]['bs'], 
                                'ask_price4' : data['orderbook'][3]['ap'], 'ask_size4' : data['orderbook'][3]['as'], 
                                'bid_price4' : data['orderbook'][3]['bp'], 'bid_size4' : data['orderbook'][3]['bs'], 
                                'ask_price5' : data['orderbook'][4]['ap'], 'ask_size5' : data['orderbook'][4]['as'], 
                                'bid_price5' : data['orderbook'][4]['bp'], 'bid_size5' : data['orderbook'][4]['bs'] 
                                }
                    # append
                    datas.append(data_dict)

        if len(datas) > 0:
            self.log.info(f"{prefix} last json: {datas[-1]}")
        else:
            self.log.info(f"Json does not exist in {prefix}")

        return datas


    def upload_parquet_to_bucket(self, bucket_name, blob_name, table):
        # 메모리 버퍼에 parquet 파일 쓰기
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression='gzip')
        buffer.seek(0)
    
        # bucket 가져오기
        bucket = self.storage_client.get_bucket(bucket_name)
    
        # upload parquet
        blob = bucket.blob(blob_name)
        blob.upload_from_file(
            buffer, 
            content_type="application/vnd.apache.parquet"
            )
        
        self.log.info(f"upload '{blob_name}' to '{bucket_name}'")
    
    
    def load_parquet_from_bucket(self, bucket_name, blob_name):
        # bucket에서 parquet 읽어오기
        bucket = self.storage_client.get_bucket(bucket_name)        
        blob = bucket.blob(blob_name)
        
        # 메모리 버퍼에 parquet 파일 쓰기
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
    
        # Parquet 파일 읽기
        table = pq.read_table(buffer)

        self.log.info(f"load '{blob_name}' to '{bucket_name}'")

        return table