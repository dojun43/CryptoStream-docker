# CrytoStream 
## Overview
암호화폐 거래소 Upbit의 실시간 호가창 데이터를 추출하고 적재하기 위한 데이터 파이프라인입니다. Streaming과 Batch 형태로 데이터를 처리하도록 설계했습니다.
- **Streaming 처리:** WebSocket을 통해 실시간으로 호가창 데이터를 수신하고, 이를 메시지 브로커인 Kafka에 저장한 후, 메시지를 읽어 GCS Bucket에 적재합니다.
- **Batch 처리:** 5분 간격으로 GCS Bucket에서 JSON 데이터를 읽어 Parquet 형식으로 변환한 뒤, 데이터를 시가·고가·저가·종가(OHLC)로 가공하여 ohlc_5m_ticker 테이블에 적재합니다.

## Getting Started
### Prerequisites
- Google Cloud Platform (GCP) 계정
- Terraform v1.10.0
### Setup
해당 프로젝트는 Google Cloud Platform과 Docker에서 동작합니다. 아래 단계에 따라 환경을 설정하고, 필요한 의존성 설치 및 구성 방법을 안내합니다.

**1. Google Cloud 인프라 구성 (Terraform 사용)**
- gcp service account json 파일을 git repository home의 private 경로에 생성합니다.
```
CryptoStream-docker/private/gcp_account.json
```
- terraform/variables.tf에서 credentials의 default에 gcp_account.json의 경로를 지정하고, project의 default에 GCP 프로젝트 이름 지정합니다.
```
variable "credentials" {
  description = "GCP에 액세스하기 위한 json 파일"
  default = "[gcp_account.json 경로 지정]"
}

variable "project" {
  description = "GCP 프로젝트 이름"
  default = "[GCP 프로젝트 이름 지정]" 
}
```
- terraform을 초기화하고, 적용하여 인프라를 프로비저닝합니다.
```
terraform init
terraform apply
```

**2. Kafka cluster 구성 (kafka-node1, kafka-node2, kafka-node3에서 해당 태스크 수행)**
- .env에 kafka 노드의 내부 IP와 외부 IP 정보를 입력합니다.
```
cd /data/CryptoStream-docker/kafka
sudo vi .env


KAFKA_NODE1_INTERNAL_IP=192.168.0.2
KAFKA_NODE2_INTERNAL_IP=192.168.0.3
KAFKA_NODE3_INTERNAL_IP=192.168.0.4

KAFKA_NODE1_EXTERNAL_IP=[kafka-node1 외부 IP]
KAFKA_NODE2_EXTERNAL_IP=[kafka-node2 외부 IP]
KAFKA_NODE3_EXTERNAL_IP=[kafka-node3 외부 IP]
```
- 각 노드에 맞는 docker-compose.yaml 파일을 사용하여 kafka를 실행합니다.
```
sudo docker compose -f docker-compose-kafka1.yaml up -d   # kafka-node1
sudo docker compose -f docker-compose-kafka2.yaml up -d   # kafka-node2
sudo docker compose -f docker-compose-kafka3.yaml up -d   # kafka-node3
```
- kafka ui로 접속하여 kafka cluster가 정상적으로 실행 중인지 확인합니다. kafka ui는 kafka-node1에서 실행됩니다.
```
[kafka-node1 외부 IP]:9000
```

**3. Data Pipeline 구성 (cryptostream-node1에서 해당 태스크 수행)**
- gcp service account json 파일을 해당 경로에 생성합니다.
```
/data/CryptoStream-docker/private/gcp_account.json
```
- .env 파일에 컨테이너 내부의 gcp_account.json의 경로, bucket 이름, DB 접속 정보, kafka 노드의 내부 IP를 입력합니다.
```
cd /data/CryptoStream-docker
sudo vi .env


KEY_PATH="/CryptoStream/private/gcp_account.json"
BUCKET_NAME="your_bucket_name"

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=[DB 유저명 설정]
POSTGRES_PASSWORD=[패스워드 설정]

KAFKA_NODE1_INTERNAL_IP=192.168.0.2
KAFKA_NODE2_INTERNAL_IP=192.168.0.3
KAFKA_NODE3_INTERNAL_IP=192.168.0.4
```

- producer.conf에서 각각의 producer가 사용할 topic의 이름, patition의 번호, 구독할 ticker의 목록을 지정합니다.
```
sudo vi /data/CryptoStream-docker/conf/producer.conf


[upbit_producer1]
topic_name=orderbook
partition_number=0
tickers=BTC,ETH,NEO,MTL,XRP,ETC,SNT,WAVES,XEM,QTUM

[upbit_producer2]
topic_name=orderbook
partition_number=1
tickers=LSK,STEEM,XLM,ARDR,ARK,STORJ,GRS,ADA,SBD,POWR

[upbit_producer3]
topic_name=orderbook
partition_number=2
tickers=ICX,EOS,TRX,SC,ONT,ZIL,POLYX,ZRX,LOOM,BCH

...

```

- consumer.conf에서 각각의 consumer 읽어올 topic의 이름, patition의 번호, topic을 소비하는 그룹명을 지정합니다.
```
sudo vi /data/CryptoStream-docker/conf/consumer.conf


[gcs_consumer1]
topic_name=orderbook
partition_number=0
group_name=gcs_consumer

[gcs_consumer2]
topic_name=orderbook
partition_number=1
group_name=gcs_consumer

[gcs_consumer3]
topic_name=orderbook
partition_number=2
group_name=gcs_consumer

...
```

- docker-compose.yaml 파일을 사용하여 Data Pipeline을 실행합니다.
```
sudo docker compose -f docker-compose.yaml up -d 
```

**4. Airflow 구성 (airflow-node1에서 해당 태스크 수행)**
- Airflow를 초기화하고 실행합니다.
```
cd /data/CryptoStream-docker/airflow


sudo docker compose up airflow-init
sudo docker compose up -d
```
- airflow webserver에 접속한 뒤 [Admin]->[connections]에서 gcp_account.json와 cryptostream-node1의 DB 접속 정보를 'conn-gcp-cryptostream'와 'conn-postgres'에 등록합니다.

![image](https://github.com/user-attachments/assets/125ef979-2e46-4afd-a43d-fe286853b346)


## Infra Architecture
terraform을 사용하여 GCP에서 Kafka, Data Pipeline, Airflow을 위한 인프라를 프로비저닝 했습니다. 생성한 리소스들은 다음과 같습니다.
- **VM:** kafka node 3개, data pipeline node 1개, airflow node 1개를 생성했습니다.
- **VPC:** Kafka와 Data Pipeline 간 내부 통신을 위해 cryptostream-subnet 서브넷을 생성하고, 모든 VM instance를 해당 서브넷에 배치했습니다.
- **Persistant Disk:** Kafka와 PostgreSQL의 데이터를 저장하기 위해 각각의 node 마다 Persistant Disk를 생성했습니다.
- **GCS Bucket:** JSON 타입의 호가창 데이터와 변환된 Parquet 파일을 저장하기 위한 Bucket을 2개 생성했습니다.
  
![image](https://github.com/user-attachments/assets/11db8594-77d1-4561-974c-121ade3d19f0)



## Data Pipeline
![image](https://github.com/user-attachments/assets/d8464379-ad5d-41e2-bcbf-36aa6d08da93)


### Data Sources
- **upbit 호가창 데이터:** https://docs.upbit.com/reference/general-info

### Streaming
- **데이터 수집:** Upbit Producer에서 WebSocket 방식으로 호가창 데이터를 구독하여 실시간으로 수집합니다.
- **Kafka에 전송:** 수집된 데이터를 Kafka의 topic에 전송합니다.
- **메시지 읽기:** GCS Consumer가 Kafka의 topic에서 메시지를 읽어옵니다.
- **데이터 적재:** JSON 타입의 호가창 데이터를 Ticker와 시간 별로 파티셔닝하여 GCS Bucket에 적재합니다.
     
  - 예시: ticker=BTC/year=2025/month=02/day=02/hour=16/minute=16/filename=ticker-timestamp.jsonl

### Batch
- **JSON 데이터를 Parquet 데이터로 변환:** 5분 간격으로 GCS Bucket에 적재된 JSON 데이터를 읽어서, Parquet로 변환 뒤 GCS Bucket에 시간 별로 파티셔닝하여 적재합니다.

    - 예시: ticker=BTC/year=2025/month=02/day=02/hour=16/filename=ticker-202502021605.parquet
- **데이터 변환 후 Postgres table에 적재:** GCS Bucket에서 5분 간격으로 생성된 Parquet 파일을 읽어오고, 시가·고가·저가·종가(OHLC) 데이터로 가공하여 ohlc_5m_ticker 테이블에 적재합니다.  
