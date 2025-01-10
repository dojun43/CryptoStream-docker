resource "google_compute_network" "cryptostream-network" {
  name = "cryptostream-network"
}

resource "google_compute_subnetwork" "cryptostream-subnet" {
  name          = "cryptostream-subnet"
  region        = var.region
  network       = google_compute_network.cryptostream-network.name
  ip_cidr_range = "192.168.0.0/24" 
}