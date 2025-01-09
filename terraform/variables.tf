# provider

variable "credentials" {
  description = "GCP에 액세스하기 위한 json 파일"
  default = "/Users/dodo/CryptoStream-docker/private/cryptostream-docker.json"
}

variable "project" {
  description = "GCP 프로젝트 ID"
  default = "cryptostream-docker" 
}

variable "region" {
  default = "asia-northeast3" 
}


# main

variable "zone" {
  default = "asia-northeast3-b" 
}
