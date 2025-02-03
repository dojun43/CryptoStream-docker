resource "google_storage_bucket" "upbit-orderbook" {
  name                        = "upbit-orderbook-1"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"

  # 30일 지난 객체 스토리지 클래스 변경
  lifecycle_rule {
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"    
    }
    condition {
      age = 30 
    }
  }
}