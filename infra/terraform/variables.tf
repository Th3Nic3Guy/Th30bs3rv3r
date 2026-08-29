variable "project_id" {
  description = "GCP project the FREE WILL stack is provisioned in."
  type        = string
}

variable "region" {
  description = "Primary GCP region (Cloud SQL, Redis, Cloud Storage buckets)."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Primary GCP zone for Compute Engine run instances (PRD Section 6.0)."
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment label (e.g. dev, staging, prod) used in resource naming."
  type        = string
  default     = "dev"
}

# --- Cloud SQL (PRD Section 6.4) --------------------------------------------------

variable "cloudsql_tier" {
  description = "Cloud SQL machine tier for the run registry instance."
  type        = string
  default     = "db-custom-2-7680"
}

variable "cloudsql_db_name" {
  description = "Database name for the run registry (runs / run_summaries / checkpoints tables)."
  type        = string
  default     = "freewill"
}

# --- Redis / Memorystore (PRD Section 6.3) -----------------------------------------

variable "redis_memory_size_gb" {
  description = "Memorystore Redis instance size in GB. Config/cache only (PRD Section 2 principle 5) — sized for run config + per-domain DAG cache, not simulation state."
  type        = number
  default     = 4
}

variable "redis_tier" {
  description = "Memorystore Redis service tier."
  type        = string
  default     = "BASIC"
}

# --- Cloud Storage (PRD Section 6.2, 6.5) ------------------------------------------

variable "checkpoints_bucket_name" {
  description = "Cloud Storage bucket for checkpoint archives (PRD Section 6.2)."
  type        = string
  default     = "freewill-checkpoints"
}

variable "event_logs_bucket_name" {
  description = "Cloud Storage bucket for the event-log archive (PRD Section 6.5)."
  type        = string
  default     = "freewill-event-logs"
}

# --- Compute Engine (PRD Section 6.0) ----------------------------------------------

variable "run_instance_machine_type" {
  description = "Machine type for one simulation run's Compute Engine instance (PRD Section 2 principle 4: one instance per run)."
  type        = string
  default     = "n2-standard-4"
}

variable "run_instance_source_image" {
  description = "Source image for run instances — carries the Python simulation engine + Go log shipper (python/Dockerfile, go/Dockerfile.logshipper)."
  type        = string
}

variable "network_name" {
  description = "VPC network name for Cloud SQL private IP, Redis, and run instances."
  type        = string
  default     = "freewill-network"
}

variable "subnetwork_cidr" {
  description = "CIDR range for the run-instance subnetwork."
  type        = string
  default     = "10.10.0.0/20"
}
