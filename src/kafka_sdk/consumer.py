import os
import logging
import time
from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError


def create_kafka_consumer(group_id, topic_name, partition_num):
    while True:
        try:
            bootstrap_servers = [f"{os.getenv('KAFKA_NODE1_INTERNAL_IP')}:9092",
                                f"{os.getenv('KAFKA_NODE2_INTERNAL_IP')}:9092",
                                f"{os.getenv('KAFKA_NODE3_INTERNAL_IP')}:9092",
                                ] 

            consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers, 
                group_id=group_id,  
                auto_offset_reset='earliest',  
                enable_auto_commit=False, 
                value_deserializer=lambda x: x.decode('utf-8'),
                fetch_max_wait_ms=10000,
                fetch_min_bytes=750000,
                max_partition_fetch_bytes=750000
            )

            partition = TopicPartition(topic_name, partition_num) 
            consumer.assign([partition])

            return consumer
        
        except Exception as e:
            logging.error(f"Create kafka consumer failed: {e}")
            time.sleep(5)