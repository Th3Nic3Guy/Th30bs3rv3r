# Memorystore for Redis — run config cache, static per-domain DAG tensor cache, and
# live-tick pub/sub for the visualization UI (PRD Section 5, 6.3). Cache only, never a
# system of record (PRD Section 2 principle 5) — no persistence/AOF requirement.

resource "google_redis_instance" "freewill" {
  name           = "freewill-${var.environment}"
  region         = var.region
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb

  authorized_network = google_compute_network.main.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_2"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}
