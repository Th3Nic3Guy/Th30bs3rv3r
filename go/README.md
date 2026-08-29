# go

Infra-facing Go services for the FREE WILL simulation platform (PRD Section 9): run
orchestration and log shipping. The tensor-native simulation engine itself is Python
(`../python`) — see `docs/adr/0001-gcp-tech-stack.md` for why the split.

## Layout

- `cmd/orchestrator` — provisions and tears down the one Compute Engine instance per
  simulation run (PRD Section 6.0, 9).
- `cmd/logshipper` — runs alongside the Python engine on each run instance; ships the
  local event-log buffer to Cloud Logging + Cloud Storage (PRD Section 6.5).
- `internal/compute` — Compute Engine instance lifecycle (create/get/delete).
- `internal/cloudsql` — Cloud SQL run registry client (mirrors
  `python/freewill/storage/run_registry.py`).
- `internal/rediscache` — Memorystore Redis client for warming run config (mirrors
  `python/freewill/storage/config_cache.py`; keys must stay in sync between the two).
- `internal/gcs` — Cloud Storage object upload used by the log shipper.

## Build

```sh
go build ./...
go vet ./...
go test ./...
```

Container images: `Dockerfile.orchestrator`, `Dockerfile.logshipper`.
