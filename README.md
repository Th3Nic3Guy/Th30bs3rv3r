# Th30bs3rv3r
Publisher Platform

## FREE WILL simulation platform

This repo also hosts the FREE WILL simulation engine — a tensor-native, agent-based
simulation on GCP. Start here:

- [`docs/FREE_WILL_PRD.md`](docs/FREE_WILL_PRD.md) — system design: simulation engine,
  storage, observability, visualization UI.
- [`docs/adr/0001-gcp-tech-stack.md`](docs/adr/0001-gcp-tech-stack.md) — the GCP
  tech-stack decision (Cloud SQL, Memorystore Redis, Cloud Storage, Compute Engine,
  Cloud Logging) this build targets.

Layout:

| Path | What |
|---|---|
| `python/` | Simulation engine (tick loop, mechanism modules, metrics) |
| `go/` | Run orchestrator + log shipper (infra-facing services) |
| `infra/terraform/` | GCP infrastructure-as-code |
| `infra/sql/` | Cloud SQL run-registry schema |
| `docs/` | PRD and architecture decision records |
