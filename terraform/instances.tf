# 고정 ip
resource "google_compute_address" "cryptostream-node1-static-ip" {
  name   = "cryptostream-node1-static-ip"
  project = var.project
  region  = var.region
}

resource "google_compute_address" "kafka-node1-static-ip" {
  name   = "kafka-node1-static-ip"
  project = var.project
  region  = var.region
}

resource "google_compute_address" "kafka-node2-static-ip" {
  name   = "kafka-node2-static-ip"
  project = var.project
  region  = var.region
}

resource "google_compute_address" "kafka-node3-static-ip" {
  name   = "kafka-node3-static-ip"
  project = var.project
  region  = var.region
}



# instances

resource "google_compute_instance" "cryptostream-node1" {
  name         = "cryptostream-node1"
  machine_type = "n2-standard-4"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  attached_disk {
    source      = google_compute_disk.cryptostream-node1-disk.id
    device_name = "cryptostream-node1-disk"
  }

  network_interface {
    network = google_compute_network.cryptostream-network.name
    subnetwork = google_compute_subnetwork.cryptostream-subnet.name
    network_ip = "192.168.0.5"
    access_config {
      nat_ip = google_compute_address.cryptostream-node1-static-ip.address
    }
  }

  metadata_startup_script = file("node_startup_script.sh")

  tags = ["allow-ssh", "allow-icmp", "allow-postgres", "allow-superset"]
}


resource "google_compute_instance" "kafka-node1" {
  name         = "kafka-node1"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  attached_disk {
    source      = google_compute_disk.kafka-node1-disk.id
    device_name = "kafka-node1-disk"
  }

  network_interface {
    network = google_compute_network.cryptostream-network.name
    subnetwork = google_compute_subnetwork.cryptostream-subnet.name
    network_ip = "192.168.0.2"
    access_config {
      nat_ip = google_compute_address.kafka-node1-static-ip.address
    }
  }

  metadata_startup_script = file("kafka_node_startup_script.sh")

  tags = ["allow-ssh", "allow-icmp", "allow-kafka-ports", "allow-kafka-inner-ports"]
}

resource "google_compute_instance" "kafka-node2" {
  name         = "kafka-node2"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  attached_disk {
    source      = google_compute_disk.kafka-node2-disk.id
    device_name = "kafka-node2-disk"
  }

  network_interface {
    network = google_compute_network.cryptostream-network.name
    subnetwork = google_compute_subnetwork.cryptostream-subnet.name
    network_ip = "192.168.0.3"
    access_config {
      nat_ip = google_compute_address.kafka-node2-static-ip.address
    }

  }

  metadata_startup_script = file("kafka_node_startup_script.sh")

  tags = ["allow-ssh", "allow-icmp", "allow-kafka-ports", "allow-kafka-inner-ports"] 
}

resource "google_compute_instance" "kafka-node3" {
  name         = "kafka-node3"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  attached_disk {
    source      = google_compute_disk.kafka-node3-disk.id
    device_name = "kafka-node3-disk"
  }

  network_interface {
    network = google_compute_network.cryptostream-network.name
    subnetwork = google_compute_subnetwork.cryptostream-subnet.name
    network_ip = "192.168.0.4"
    access_config {
      nat_ip = google_compute_address.kafka-node3-static-ip.address
    }
  }

  metadata_startup_script = file("kafka_node_startup_script.sh")

  tags = ["allow-ssh", "allow-icmp", "allow-kafka-ports", "allow-kafka-inner-ports"]
}