# Compute Engine instance template for simulation runs (PRD Section 6.0, 2 principle 4:
# one instance per run). The orchestrator (go/cmd/orchestrator) creates one instance per
# run from this template's image rather than reusing it directly, since each instance
# needs a run-specific name and "run-id" metadata value.

resource "google_compute_instance_template" "run_instance" {
  name_prefix  = "freewill-run-"
  machine_type = var.run_instance_machine_type
  region       = var.region

  scheduling {
    preemptible       = true
    automatic_restart = false
  }

  disk {
    source_image = var.run_instance_source_image
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network    = google_compute_network.main.id
    subnetwork = google_compute_subnetwork.run_instances.id
    # No access_config block: run instances have no external IP, matching PRD 6.0's
    # "no per-tick network I/O to any GCP service" — the only egress they need
    # (Cloud SQL, Redis, Cloud Storage, Cloud Logging) is reachable over the private
    # VPC / Google APIs, not the public internet.
  }

  service_account {
    email  = google_service_account.run_instance.email
    scopes = ["cloud-platform"]
  }

  lifecycle {
    create_before_destroy = true
  }
}
