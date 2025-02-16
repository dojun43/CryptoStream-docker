## disk mount
sudo mkfs.ext4 /dev/sdb  # 파일 시스템 생성
sudo mkdir /data
sudo mount /dev/sdb /data


## install docker

echo "Starting Docker installation" >> /var/log/startup_script.log

# docker version
VERSION_STRING="5:27.1.2-1~ubuntu.22.04~jammy"

# Update package list and install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker's repository to apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list and install Docker
sudo apt-get update
sudo apt-get install -y docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

echo "End Docker installation" >> /var/log/startup_script.log


## set up
sudo mkdir -p /data/postgresql/data
sudo chown -R 1000:1000 /data/postgresql/data

# git clone
cd /data
git clone https://github.com/dojun43/CryptoStream-docker.git

# airflow setting
cd /data/CryptoStream-docker/airflow
sudo mkdir -p ./dags ./logs ./plugins ./config
sudo echo -e "AIRFLOW_UID=$(id -u)" > .env