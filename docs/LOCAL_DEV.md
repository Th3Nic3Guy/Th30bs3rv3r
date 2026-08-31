# Local Development (Docker Compose)

A GCP-free stand-in for `infra/terraform`'s real Cloud SQL / Memorystore / Cloud Storage
(PRD Section 6), so the engine and Go services can be developed and smoke-tested without
a GCP project or credentials. See `docker-compose.yml`'s own header comment for the
service-by-service mapping; this doc is the narrative version plus how to actually run
things.

## What's emulated, and what isn't

| PRD Section 6 backend | Local stand-in | Code changes needed |
|---|---|---|
| Cloud SQL (PostgreSQL) | plain `postgres` image | Yes — `RunRegistry.for_local_postgres` (Python) / `cloudsql.OpenLocal` (Go) bypass the Cloud SQL connector, which has nothing to dial locally |
| Memorystore (Redis) | plain `redis` image | None — both Redis clients already just take a `host:port` |
| Cloud Storage | `fsouza/fake-gcs-server` | None — both `google-cloud-storage` and `cloud.google.com/go/storage` auto-detect the `STORAGE_EMULATOR_HOST` env var and switch to anonymous requests against it |
| Cloud Logging | **nothing** — no official local emulator exists | `go/cmd/logshipper`'s `-local` flag skips it and logs to stdout instead |

The Compute Engine side (PRD Section 6.0 — one instance per run, provisioned by
`go/cmd/orchestrator`) has no local equivalent at all and isn't part of this stack: there
is nothing to "provision" on a laptop. For local development, run the Python engine
directly instead of through the orchestrator.

## Quick start

```sh
docker compose up -d postgres redis gcs-emulator
cd python
PYTHONPATH=. python scripts/local_smoke_run.py
```

The smoke script exercises all three storage backends end-to-end (create a run row,
round-trip its config through Redis, write and read back a checkpoint against the GCS
emulator) — see its own docstring. It's also what CI's `docker-compose` job runs on every
push, against real containers on GitHub's runners (this sandbox has no Docker daemon, so
that CI job is the only place this has actually been exercised so far — see
`docs/DEV_TASKLIST.md`).

To run it in a container instead of your host Python:

```sh
docker compose --profile smoke-test run --rm simulation-smoke-test
```

## Connecting to the stack manually

```sh
# Postgres
psql "host=localhost user=freewill password=freewill dbname=freewill"

# Redis
redis-cli -h localhost

# GCS emulator's JSON API
curl http://localhost:4443/storage/v1/b
```

## Using the local backends from your own code

```python
from freewill.storage.run_registry import RunRegistry

registry = RunRegistry.for_local_postgres(
    "host=localhost user=freewill password=freewill dbname=freewill sslmode=disable"
)
```

```python
import os
os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:4443"
from freewill.storage.checkpoint_store import CheckpointStore

store = CheckpointStore("freewill-checkpoints")  # works against the emulator automatically
```

```go
import "github.com/th3nic3guy/th30bs3rv3r/go/internal/cloudsql"

registry, err := cloudsql.OpenLocal(ctx, "host=localhost user=freewill password=freewill dbname=freewill sslmode=disable")
```

```sh
# go/cmd/logshipper against the local stack
STORAGE_EMULATOR_HOST=http://localhost:4443 go run ./cmd/logshipper \
  -local -bucket freewill-event-logs -run-id smoke-test -staging-path /tmp/events.jsonl
```
