# VPC network shared by Cloud SQL (private IP), Memorystore Redis, and the per-run
# Compute Engine instances (PRD Section 6.0, 6.3, 6.4) — all internal-only traffic.

resource "google_project_service" "required" {
  for_each = toset([
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "servicenetworking.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "main" {
  name                    = var.network_name
  auto_create_subnetworks = false

  depends_on = [google_project_service.required]
}

resource "google_compute_subnetwork" "run_instances" {
  name          = "${var.network_name}-run-instances"
  ip_cidr_range = var.subnetwork_cidr
  region        = var.region
  network       = google_compute_network.main.id

  # Run instances have no external IP (infra/terraform/compute.tf) — Private Google
  # Access lets them still reach Cloud SQL/Redis/Cloud Storage/Cloud Logging APIs over
  # Google's network instead of the public internet.
  private_ip_google_access = true
}

# Private services access for Cloud SQL private IP + Memorystore (both PRD 6.3/6.4 are
# reached only from run instances on this VPC, never over the public internet).
resource "google_compute_global_address" "private_service_range" {
  name          = "${var.network_name}-private-service-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]
}

resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  network = google_compute_network.main.id

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }

  source_ranges = [var.subnetwork_cidr]
}
