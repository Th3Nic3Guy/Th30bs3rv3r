# Th30bs3rv3r
Publisher Platform

## FREE WILL simulation platform

This repo also hosts the FREE WILL simulation engine — a tensor-native, agent-based
simulation on GCP. Start here:

- [`docs/FREE_WILL_PRD.md`](docs/FREE_WILL_PRD.md) — system design: simulation engine,
  storage, observability, visualization UI.
- [`docs/FREE_WILL_draft.md`](docs/FREE_WILL_draft.md) — the formal model every
  mechanism module traces back to.
- [`docs/adr/0001-gcp-tech-stack.md`](docs/adr/0001-gcp-tech-stack.md) — the GCP
  tech-stack decision (Cloud SQL, Memorystore Redis, Cloud Storage, Compute Engine,
  Cloud Logging) this build targets.
- [`docs/LOCAL_DEV.md`](docs/LOCAL_DEV.md) — run the whole stack locally with
  `docker compose up`, no GCP project needed.
- [`docs/DEV_TASKLIST.md`](docs/DEV_TASKLIST.md) — what's done, what's next.

Layout:

| Path | What |
|---|---|
| `python/` | Simulation engine (tick loop, mechanism modules, metrics) |
| `go/` | Run orchestrator + log shipper (infra-facing services) |
| `infra/terraform/` | GCP infrastructure-as-code |
| `infra/sql/` | Cloud SQL run-registry schema |
| `infra/docker/` | Local dev stack support files (GCS emulator bucket seeds) |
| `docker-compose.yml` | Local dev stack (Postgres/Redis/GCS emulator) — see `docs/LOCAL_DEV.md` |
| `docs/` | PRD, formal model, architecture decision records |
