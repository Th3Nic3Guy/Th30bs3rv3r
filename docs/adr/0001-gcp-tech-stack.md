# ADR 0001: GCP Tech Stack for the FREE WILL Simulation Platform

- **Status**: Accepted
- **Date**: 2026-08-29
- **Author decision, recorded verbatim from the project owner**

## Context

`FREE_WILL_PRD.md` (the simulation engine / storage / observability / visualization
PRD) originally proposed a stack built around local files, a self-hosted Elastic
Stack (Elasticsearch/Logstash/Kibana), and a Dash UI running against on-disk
checkpoints. The project owner has since decided the whole system runs on GCP.
This ADR records that decision and supersedes the storage/observability choices
in PRD Sections 5–6 wherever they conflict.

## Decision

| Concern | Original PRD proposal | GCP decision |
|---|---|---|
| Cloud provider | unspecified / local | **Google Cloud Platform** |
| Relational storage | none (files only) | **Cloud SQL for PostgreSQL** — run registry, run-summary records (PRD §5.4), checkpoint index |
| Config / caching | none | **Memorystore for Redis** — hot run config, static per-domain DAG adjacency, live-tick pub/sub for the UI |
| Blob / object storage | local filesystem | **Cloud Storage** — checkpoint archives (`.npz` + Parquet, PRD §5.2) and the append-only event log (PRD §5.3) |
| Simulation compute | unspecified | **Compute Engine, one instance per run** — a run is scheduled onto a single GCE VM for its lifetime; no shared multi-tenant simulation host |
| Logs / observability | Elastic Stack (ELK) | **Cloud Logging** — structured log entries per PRD §5.3's event schema, plus GCE VM/serial logs |
| Simulation & mechanism code | Python (NumPy/SciPy/pydata-sparse) | **Python**, unchanged — PRD §2 and §4 principles (tensor-first, no Mesa, iterative reference oracle) stand as written |
| Orchestration / infra-facing services | unspecified | **Go** — run orchestration (provisioning/tearing down the per-run GCE instance), the log/event shipper into Cloud Logging, and any CloudSQL/GCS/Redis-facing service code |

## Consequences

- PRD §5 ("Data Storage") and §6 ("Logging and Observability") are superseded by
  `docs/FREE_WILL_PRD.md`'s GCP-specific rewrite in this repo; the Elastic Stack
  option is dropped rather than kept as an alternative.
- PRD §5.4's "same log-server backend" for run summaries now means **Cloud SQL**
  (structured, queryable rows), not an Elasticsearch index — a better fit for the
  relational run/config/summary shape than a search index.
  Cloud Logging remains the destination for the raw event stream (§5.3), since
  it is genuinely log-shaped (append-only, high-volume, JSON records).
- "One Compute Engine instance per run" means the ~3,960-run experiment budget
  (PRD §1) is a fleet-provisioning problem, not a single-host batch-queue
  problem — the Go orchestrator is responsible for instance lifecycle
  (create → run → checkpoint/upload → delete), not a job scheduler inside one
  VM.
- Redis is explicitly **not** a system of record. Anything it holds (config,
  cached DAG adjacency, live-tick pub/sub messages for the UI) must be
  reconstructable from Cloud SQL / Cloud Storage; losing the Redis instance
  must never lose simulation state.
- Section 9's open items (χ/θ/π, ε_explore/τ_still, influencer reach R,
  Beta-shape robustness configs) are stored as part of a run's config row in
  Cloud SQL and mirrored into Redis for fast per-tick reads by the running
  instance — never hardcoded in mechanism modules, per PRD §2.3/§9.
- The local visualization UI (PRD §7) keeps its Dash recommendation; "local"
  now means it reads Cloud SQL (run summaries), Cloud Storage (checkpoints,
  event log), and Redis (live-tick pub/sub for the currently-watched run)
  instead of a local filesystem.
