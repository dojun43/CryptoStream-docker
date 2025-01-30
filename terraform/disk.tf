resource "google_compute_disk" "cryptostream-node1-disk" {
  name  = "cryptostream-node1-disk"
  zone  = var.zone
  size  = 100 
  type  = "pd-standard"
}

resource "google_compute_disk" "kafka-node1-disk" {
  name  = "kafka-node1-disk"
  zone  = var.zone
  size  = 268 
  type  = "pd-standard"
}

resource "google_compute_disk" "kafka-node2-disk" {
  name  = "kafka-node2-disk"
  zone  = var.zone
  size  = 268 
  type  = "pd-standard"
}

resource "google_compute_disk" "kafka-node3-disk" {
  name  = "kafka-node3-disk"
  zone  = var.zone
  size  = 268 
  type  = "pd-standard"
}