"""GCP-backed storage clients (PRD Section 6).

- checkpoint_store — Cloud Storage, sparse-tensor archives (PRD 6.2)
- event_log        — local JSON-lines buffer + Cloud Storage archive (PRD 6.5)
- run_registry     — Cloud SQL, `runs` / `run_summaries` / `checkpoints` tables (PRD 6.4)
- config_cache     — Redis, run config + static domain tensors (PRD 5, 6.3)
"""
