resource "google_compute_firewall" "allow-ssh" {
  name    = "allow-ssh"
  project = var.project
  network = google_compute_network.cryptostream-network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-ssh"]
}

resource "google_compute_firewall" "allow-icmp" {
  name    = "allow-icmp"
  project = var.project
  network = google_compute_network.cryptostream-network.name

  allow {
    protocol = "icmp"
  }

  source_ranges = ["192.168.0.0/24"] 
  target_tags   = ["allow-icmp"]
}

resource "google_compute_firewall" "allow-superset" {
  name    = "allow-superset"
  project = var.project
  network = google_compute_network.cryptostream-network.name

  allow {
    protocol = "tcp"
    ports    = ["8088"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-superset"]
}

resource "google_compute_firewall" "allow-postgres" {
  name    = "allow-postgres"
  project = var.project
  network = google_compute_network.cryptostream-network.name

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-postgres"]
}

resource "google_compute_firewall" "allow-kafka-ports" {
  name    = "allow-kafka-ports"
  project = var.project
  network = google_compute_network.cryptostream-network.name

  allow {
    protocol = "tcp"
    ports    = ["29092", "9000"]
  }

  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["allow-kafka-ports"]
}

resource "google_compute_firewall" "allow-kafka-inner-ports" {
  name    = "allow-kafka-inner-ports"
  project = var.project
  network = google_compute_network.cryptostream-network.name

  allow {
    protocol = "tcp"
    ports    = ["9092", "9093"]
  }

  source_ranges = ["192.168.0.0/24"] 
  target_tags   = ["allow-kafka-inner-ports"]
}