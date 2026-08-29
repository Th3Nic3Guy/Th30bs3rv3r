output "cloudsql_connection_name" {
  description = "PROJECT:REGION:INSTANCE — pass as -cloudsql-instance to the orchestrator and as RunRegistry's instance_connection_name (PRD Section 6.4)."
  value       = google_sql_database_instance.freewill.connection_name
}

output "redis_host" {
  description = "Memorystore Redis private IP — combine with port 6379 for -redis-addr (PRD Section 6.3)."
  value       = google_redis_instance.freewill.host
}

output "checkpoints_bucket" {
  description = "Cloud Storage bucket for checkpoint archives (PRD Section 6.2)."
  value       = google_storage_bucket.checkpoints.name
}

output "event_logs_bucket" {
  description = "Cloud Storage bucket for the event-log archive (PRD Section 6.5)."
  value       = google_storage_bucket.event_logs.name
}

output "run_instance_service_account" {
  description = "Service account email for per-run Compute Engine instances (PRD Section 6.0)."
  value       = google_service_account.run_instance.email
}

output "orchestrator_service_account" {
  description = "Service account email for the Go orchestrator (PRD Section 9)."
  value       = google_service_account.orchestrator.email
}

output "network" {
  description = "VPC network self-link shared by Cloud SQL, Redis, and run instances."
  value       = google_compute_network.main.self_link
}
