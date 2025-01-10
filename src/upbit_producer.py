import os
import sys
import configparser
import logging
import websockets
import json
import redis
import time
import asyncio
from producer import create_kafka_producer, create_kafka_topic

class upbit_producer:
    def __init__(self, producer_name: str):
        # log setting
        log_directory = "/CryptoStream/logs/producer"  
        log_filename = f"{producer_name}.log"  
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
        config.read('/CryptoStream/conf/producer.conf')

        # variables
        self.producer_name = producer_name
        self.topic_name = config.get(producer_name, 'topic_name')
        self.tickers = config.get(producer_name,'tickers')
        self.tickers = self.tickers.split(',')

        logging.info(f"{self.producer_name} topic_name: {self.topic_name}")
        logging.info(f"{self.producer_name} tickers: {self.tickers}")

        # websocket setting
        self.uri = "wss://api.upbit.com/websocket/v1"
        codes = ["KRW-" + ticker.upper() + ".5" for ticker in self.tickers]
        self.subscribe_fmt = [
            {"ticket": "UNIQUE_TICKET"},
            {
                "type": "orderbook",
                "codes": codes,
                "isOnlyRealtime": True
            },
            {"format": "SIMPLE"}
        ]

    async def up_ws_client(self):     
        # create kafka producer   
        kafka_producer = create_kafka_producer()

        # create topic
        create_kafka_topic(client_id = self.producer_name, 
                           topic_name = self.topic_name, 
                           num_partitions = 1, 
                           replication_factor = 2)

        # webdocket connetion
        websocket = await websockets.connect(self.uri, ping_interval=60)
        await websocket.send(json.dumps(self.subscribe_fmt))

        while True:
            if websocket.open:
                try:
                    data = await websocket.recv()
                    data = json.loads(data)

                    kafka_producer.send(self.topic_name, value=data).get(timeout=5)

                except Exception as e:
                    logging.error(f"upbit producer error: {e}")
                    time.sleep(5)

            else:
                try:
                    logging.error(f"upbit websocket is NOT connected. Reconnecting...")

                    websocket = await websockets.connect(self.uri, ping_interval=60)
                    await websocket.send(json.dumps(self.subscribe_fmt))

                    logging.error(f"upbit websocket is connected.")
                
                except Exception as e:
                    logging.error(f"upbit websocket Unable to reconnect: {e}")
                    time.sleep(5)

    async def up_connecter(self):
        await self.up_ws_client()

    def up_producer(self):
        asyncio.run(self.up_connecter())
    
    def run(self):
        self.up_producer()

if __name__ == '__main__':
    upbit_producer(sys.argv[1]).run()