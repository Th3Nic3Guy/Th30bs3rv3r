# Cloud Logging (PRD Section 7). The "freewill-events" and "freewill-runs" logs
# (go/cmd/logshipper, go/cmd/orchestrator) use Cloud Logging's default project bucket —
# no custom sink is required for that. This file provisions the pieces that do need
# explicit config: a longer-retention bucket for the event stream (Cloud Logging's own
# retention is deliberately short, PRD Section 6.5/7 — the Cloud Storage archive is the
# long-term copy) and a log-based metric feeding the live/aggregate dashboards (PRD
# Section 7).

resource "google_logging_project_bucket_config" "freewill_events" {
  project        = var.project_id
  location       = "global"
  bucket_id      = "freewill-events"
  retention_days = 30

  depends_on = [google_project_service.required]
}

resource "google_logging_metric" "fallacy_trigger_rate" {
  name   = "freewill_fallacy_triggered_count"
  filter = "logName=\"projects/${var.project_id}/logs/freewill-events\" AND jsonPayload.event_type=\"fallacy_triggered\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}
