import os
import sys
import configparser
import logging
import time
import json
import concurrent.futures
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from connection import connect_to_gcs

sys.path.append('/CryptoStream/src/')
from kafka_sdk.consumer import create_kafka_consumer

class gcs_consumer:
    def __init__(self, consumer_name: str):
        # log setting
        log_directory = "/CryptoStream/logs/consumer"  
        log_filename = f"{consumer_name}.log"  
        log_file_path = os.path.join(log_directory, log_filename)

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        logging.basicConfig(
            level=logging.INFO,  
            format='%(asctime)s - %(levelname)s - %(message)s',  
            filename=log_file_path, 
            filemode='a' # a: append
        )

        # read conf
        config = configparser.ConfigParser()
        config.read('/CryptoStream/conf/consumer.conf')

        # variables
        self.consumer_name = consumer_name
        self.topic_name = config.get(consumer_name,'topic_name')
        self.partition_number = int(config.get(consumer_name,'partition_number'))
        self.group_name = config.get(consumer_name,'group_name')

        logging.info(f"{self.consumer_name} topic_name: {self.topic_name}")
        logging.info(f"{self.consumer_name} group: {self.group_name}")

        # connection GCS
        self.bucket = connect_to_gcs()

        # create kafka consumer
        self.kafka_consumer = create_kafka_consumer(group_id=self.group_name, 
                                                    topic_name=self.topic_name, 
                                                    partition_num=self.partition_number
                                                    )

    def transform_data(self, up_data: dict[str, any]) -> dict:
        timestamp = up_data['tms'] / 1000
        dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo("Asia/Seoul"))
    
        return_dict = {'ticker': up_data['cd'][4:],
                       'timestamp': timestamp,
                       'timestamp_date': dt,
                       'orderbook': up_data['obu']
                      }

        return return_dict

    def upload_buffer_to_gcs(self, buffer: dict[str, any]):
        for partition_key, data_list in buffer.items():
            # JSONL 포맷으로 변환
            jsonl_data = "\n".join(json.dumps(d) for d in data_list)

            # GCS 업로드
            last_data = data_list[-1]
            blob_name = f"{partition_key}/{last_data['ticker']}-{str(last_data['timestamp'])}.jsonl"

            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(
                data=jsonl_data, 
                content_type="application/json"
                )

    def main(self):                
        while True:
            try:
                # 메시지 처리
                msg = self.kafka_consumer.poll(timeout_ms=20000)
                buffer = defaultdict(list)

                if msg:
                    for topic_partition, messages in msg.items():
                        for message in messages:
                            up_data = json.loads(message.value)
                            up_data = self.transform_data(up_data)
                            
                            # 파티션 키 생성
                            partition_date = up_data["timestamp_date"].strftime("%Y/%m/%d/%H/%M")
                            partition_key = f"{up_data['ticker']}/{partition_date}"

                            # timestamp_date 포멧 변경
                            up_data["timestamp_date"] = str(up_data["timestamp_date"])

                            # 버퍼에 데이터 추가
                            buffer[partition_key].append(up_data)
                    
                    self.upload_buffer_to_gcs(buffer)
                    self.kafka_consumer.commit()

            except Exception as e:                
                logging.error(f"gcs consumer error: {e}")
                time.sleep(5)

    def run(self):
        self.main()

if __name__ == '__main__':
    gcs_consumer(sys.argv[1]).run()