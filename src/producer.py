import os
import logging
import time
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic


def create_kafka_producer():
    while True:
        try:
            bootstrap_servers = [f"'{os.getenv('KAFKA_NODE1_INTERNAL_IP')}':9092",
                                f"'{os.getenv('KAFKA_NODE2_INTERNAL_IP')}':9092",
                                f"'{os.getenv('KAFKA_NODE3_INTERNAL_IP')}':9092",
                                ] 

            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,  
                value_serializer=lambda x: x.decode('utf-8')      
                )
            
            return producer
        
        except Exception as e:
            logging.error(f"Create kafka producer failed: {e}")
            time.sleep(5)


def create_kafka_topic(client_id, topic_name, num_partitions, replication_factor):
    while True:
        try:
            bootstrap_servers = [f"'{os.getenv('KAFKA_NODE1_INTERNAL_IP')}':9092",
                                f"'{os.getenv('KAFKA_NODE2_INTERNAL_IP')}':9092",
                                f"'{os.getenv('KAFKA_NODE3_INTERNAL_IP')}':9092",
                                ] 

            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id=client_id
            )
            
            # 새 토픽 정의
            topic_list = [
                NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
            ]
            
            # 토픽 생성 요청
            existing_topics = admin_client.list_topics()

            if topic_name in existing_topics:
                logging.info(f"Topic '{topic_name}' already exists.")
                return

            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            logging.info(f"Topic '{topic_name}' created successfully.")

        except Exception as e:
            logging.info(f"Failed to create topic '{topic_name}': {e}")
            time.sleep(5)

        finally:
            admin_client.close()