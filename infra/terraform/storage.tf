# Cloud Storage — checkpoint archives (PRD Section 6.2) and the event-log archive (PRD
# Section 6.5). Explicitly not one-file-per-agent (PRD 6.2): objects are one-per-checkpoint
# and one-per-shipped-batch, keyed under a {run_id}/ prefix.

resource "google_storage_bucket" "checkpoints" {
  name     = "${var.checkpoints_bucket_name}-${var.project_id}"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365 # long-lived: checkpoints are the durable per-run state (PRD 6.1)
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

resource "google_storage_bucket" "event_logs" {
  name     = "${var.event_logs_bucket_name}-${var.project_id}"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 180 # full-fidelity archive backing Cloud Logging's shorter retention (PRD 7)
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}
