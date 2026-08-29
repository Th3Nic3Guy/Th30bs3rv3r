# Cloud SQL for PostgreSQL — run registry (PRD Section 6.4): `runs`, `run_summaries`,
# `checkpoints` tables. DDL lives in infra/sql/schema.sql, applied out-of-band (this
# module provisions the instance/database/users only).

resource "google_sql_database_instance" "freewill" {
  name             = "freewill-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = var.cloudsql_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "freewill" {
  name     = var.cloudsql_db_name
  instance = google_sql_database_instance.freewill.name
}

# IAM database users (PRD Section 6.0/9): the Go orchestrator and the Python simulation
# engine authenticate via IAM, not static passwords — matches
# go/internal/cloudsql.Config.UseIAMAuthN and the "prefer IAM auth" note in
# python/freewill/storage/run_registry.py.
resource "google_sql_user" "orchestrator" {
  name     = trimsuffix(google_service_account.orchestrator.email, ".gserviceaccount.com")
  instance = google_sql_database_instance.freewill.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

resource "google_sql_user" "run_instance" {
  name     = trimsuffix(google_service_account.run_instance.email, ".gserviceaccount.com")
  instance = google_sql_database_instance.freewill.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}
