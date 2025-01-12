# CrytoStream 
## Overview
암호화폐 거래소인 Upbit에서 제공하는 실시간 호가창 데이터를 추출하고 저장하기 위한 데이터 파이프라인 입니다.

WebSocket을 통해 실시간으로 호가창 데이터를 수신받고, 메시지 브로커인 kafka에 저장하고, 메시지를 읽어와 변환 후 PostgreSQL에 데이터를 적재하도록 설계했습니다. 
## Getting Started
### Prerequisites
- Google Cloud Platform (GCP) 계정
- Terraform v1.10.0
### Setup
해당 프로젝트는 Google Cloud Platform과 Docker에서 동작합니다. 아래 단계에 따라 환경을 설정하고, 필요한 의존성 설치 및 구성 방법을 안내합니다.
1. Google Cloud 인프라 구성 (Terraform 사용)
- gcp service account json파일을 git repository home의 private 경로에 생성합니다.
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

2. Kafka cluster 구성 (kafka-node1, kafka-node2, kafka-node3에서 해당 태스크 수행)
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
sudo docker compose -f docker-compose-kafka3.yaml up -d   # kafka-node1
```
- kafka ui로 접속하여 kafka cluster가 정상적으로 실행 중인지 확인합니다. kafka ui는 kafka-node1에서 실행됩니다.
```
[kafka-node1 외부 IP]:9000
```

3. Data Pipeline 구성 (cryptostream-node1에서 해당 태스크 수행)
- .env 파일에 DB 접속 정보와 kafka 노드의 내부 IP를 입력합니다.
```
cd /data/CryptoStream-docker
sudo vi .env


POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=[DB 유저명 설정]
POSTGRES_PASSWORD=[패스워드 설정]

KAFKA_NODE1_INTERNAL_IP=192.168.0.2
KAFKA_NODE2_INTERNAL_IP=192.168.0.3
KAFKA_NODE3_INTERNAL_IP=192.168.0.4
```

- producer.conf에서 각각의 producer가 사용할 topic의 이름과 구독할 ticker의 목록을 지정합니다.
```
sudo vi /data/CryptoStream-docker/conf/producer.conf


[upbit_producer1]
topic_name=orderbook1
tickers=BTC,ETH

[upbit_producer2]
topic_name=orderbook2
tickers=SOL,ETC

[upbit_producer3]
topic_name=orderbook3
tickers=XRP,BCH
```

- dataloader.conf에서 각각의 dataloader가 읽어올 topic의 이름, topic을 소비하는 그룹명, Postgres에 commit할 row의 수를 지정합니다.
```
sudo vi /data/CryptoStream-docker/conf/dataloader.conf


[upbit_dataloader1]
topic_name=orderbook1
group_name=upbit_dataloader1
commit_count=1

[upbit_dataloader2]
topic_name=orderbook2
group_name=upbit_dataloader2
commit_count=1

[upbit_dataloader3]
topic_name=orderbook3
group_name=upbit_dataloader3
commit_count=1
```

- docker-compose.yaml 파일을 사용하여 Data Pipeline을 실행합니다.
```
sudo docker compose -f docker-compose.yaml up -d 
```
## Infra Architecture
terraform을 사용하여 GCP에서 Kafka와 Data Pipeline을 위한 인프라를 프로비저닝 했습니다. 생성한 리소스들은 다음과 같습니다.
- **VM:** kafka node 3개와 data pipeline node 1개를 생성했습니다.
- **VPC:** Kafka와 Data Pipeline 간 내부 통신을 위해 cryptostream-subnet 서브넷을 생성하고, 모든 VM을 해당 서브넷에 배치했습니다.
- **Persistant Disk:** Kafka와 PostgreSQL의 데이터를 저장하기 위해 Persistant Disk를 생성했습니다.

![image](https://github.com/user-attachments/assets/c7e70844-82c1-4403-bd6e-4f3b3fed75e9)

## Data Pipeline
![image](https://github.com/user-attachments/assets/b6219dde-fd36-40d7-99bb-b7a901a15ab5)

### Data Sources
- **upbit 호가창 데이터:** https://docs.upbit.com/reference/general-info

### Extract
- **데이터 수집:** Upbit Producer에서 WebSocket 방식으로 호가창 데이터를 구독하여 실시간으로 수집합니다.
- **Kafka에 추가:** 수집된 데이터를 Kafka의 topic에 추가합니다.

### Transform & Load
- **메시지 읽기:** Dataloader가 Kafka에서 메시지를 읽어옵니다.
- **데이터 변환:** JSON 형식의 호가창 데이터를 PostgreSQL 테이블 구조에 맞게 변환합니다.
- **데이터 저장:** 변환된 데이터를 PostgreSQL에 저장하며, 데이터는 날짜별로 파티셔닝하여 관리됩니다.

### Visualization
- PostgreSQL과 Superset을 연동 후 적재한 데이터를 SQL 구문을 활용해서 변환합니다.
- 수집한 암호화폐의 시세를 기간 별로 시각화합니다.
<img width="880" alt="image" src="https://github.com/user-attachments/assets/308bffa1-e05f-468c-a70c-396626cd0cb4" />
