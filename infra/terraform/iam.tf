# Service accounts for the two Go services / the run instance (PRD Section 9, 6.0):
# - orchestrator: provisions/tears down run instances, writes the run registry
# - run_instance: the per-run Compute Engine instance (Python engine + Go log shipper)

resource "google_service_account" "orchestrator" {
  account_id   = "freewill-orchestrator"
  display_name = "FREE WILL run orchestrator (PRD Section 9)"
}

resource "google_service_account" "run_instance" {
  account_id   = "freewill-run-instance"
  display_name = "FREE WILL simulation run instance (PRD Section 6.0)"
}

resource "google_project_iam_member" "orchestrator_compute_admin" {
  project = var.project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "orchestrator_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "orchestrator_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "orchestrator_cloudsql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "run_instance_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run_instance.email}"
}

resource "google_project_iam_member" "run_instance_cloudsql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.run_instance.email}"
}

resource "google_project_iam_member" "run_instance_logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.run_instance.email}"
}

resource "google_storage_bucket_iam_member" "run_instance_checkpoints_writer" {
  bucket = google_storage_bucket.checkpoints.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run_instance.email}"
}

resource "google_storage_bucket_iam_member" "run_instance_event_logs_writer" {
  bucket = google_storage_bucket.event_logs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run_instance.email}"
}
