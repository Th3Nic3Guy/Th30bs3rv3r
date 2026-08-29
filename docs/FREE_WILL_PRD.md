# FREE WILL — Product Requirements Document
**Simulation Engine, Storage, Observability, and Visualization**

*Companion to: FREE_WILL_draft.md (formal model), FREE_WILL_decisions_log.md,
FREE_WILL_checklist.md, and the 10 domain axiom-hierarchy documents.*

> **Stack note (2026-08-29):** this document has been revised from its original
> form to target **Google Cloud Platform**, per the decision recorded in
> [`docs/adr/0001-gcp-tech-stack.md`](adr/0001-gcp-tech-stack.md). Section 5
> (Data Storage) and Section 6 (Logging and Observability) are rewritten
> accordingly; the rest of the document — the simulation engine's design
> (Section 4) — is unchanged, since the tech-stack decision governs *where
> state lives*, not the mathematics of the model.

---

## 1. Purpose and Scope

Build the software system that implements the FREE WILL formal model (draft Sections 3–4)
as an executable, tensor-native agent-based simulation, capable of running the full
experiment budget (~3,960 runs: 3,030 core factorial + 900 robustness-check + 30
sequence-sensitivity, per the checklist's resolved Experiment Budget section) and
producing the metrics needed to test H1–H11.

This PRD covers: the simulation engine's mathematical implementation, state storage,
logging/observability, and a local visualization UI. It does not cover statistical
post-processing of completed runs (Section 4.8's analysis plan) — that is a downstream
consumer of this system's outputs, not part of this build.

---

## 2. Design Principles (non-negotiable, stated by author)

1. **Tensor calculus and matrix operations are the primary computational method.**
   Per-agent iteration is secondary — used only (a) where a mechanism genuinely does not
   vectorize (Section 4.9 identifies exactly one: the ad hominem/halo-effect leak), or
   (b) as a slow, naive reference implementation for cross-validating the vectorized path's
   correctness during development. Iteration is never the primary path for something
   Section 4.9 already describes as vectorizable.
2. **Raw development — no agent-based-modeling framework (e.g., Mesa).** The original 2022
   source dissertation used Mesa; this implementation does not. Mesa's per-agent
   object-oriented `step()` model is structurally incompatible with the batched
   sparse-tensor tick processing this design requires. The simulation loop, grid, and agent
   representation are built directly on NumPy/SciPy.
3. **Every formula implemented must trace to a specific section of FREE_WILL_draft.md.**
   No implementation-time invention of mechanisms not already formalized there. Where the
   draft has an open TODO (e.g., χ/θ/π calibration, ε_explore/τ_still ranges), the
   implementation must expose these as configurable parameters, not hardcode a guess.
4. **Simulation compute is one Compute Engine instance per run** (Section 6.0). The engine
   must not assume a shared multi-tenant host, a job queue inside one VM, or local-disk
   permanence beyond a single run's lifetime.
5. **Cloud Storage, Cloud SQL, and Redis are the only systems of record for anything that
   must survive a VM's teardown.** Nothing written only to local disk on the run instance
   is considered durable.

---

## 3. System Architecture (high level)

```
┌─────────────────────────────────────────────────────────────────┐
│              Simulation Engine  (Python — Compute Engine,       │
│                      one VM per run, Section 6.0)                │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  State    │  │  Tick     │  │  Mechanism    │  │  Metrics  │ │
│  │  Tensors  │→ │  Loop     │→ │  Modules      │→ │  Computer │ │
│  │ (Sec. 4.9)│  │(Sec. 4.1, │  │ (Sec. 3.2–3.9,│  │(Sec. 4.7) │ │
│  │           │  │ 4.11)     │  │  4.6)         │  │           │ │
│  └───────────┘  └───────────┘  └──────────────┘  └───────────┘ │
│         │              │               │                │       │
│         ▼              ▼               ▼                ▼       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Event Log (append-only, JSON-lines, local buffer)     │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────┬───────────────┬───────────────┬───────────────┬─────┘
           │                │               │               │
   ┌───────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐ ┌─────▼─────┐
   │ Cloud Storage │ │  Cloud SQL   │ │ Memorystore  │ │  Cloud    │
   │ checkpoints + │ │ (PostgreSQL) │ │  (Redis)     │ │  Logging  │
   │ event-log     │ │ run registry,│ │ run config,  │ │ (event    │
   │ archives      │ │ run summaries│ │ DAG cache,   │ │  stream,  │
   │ (Sec. 6.2)    │ │ (Sec. 6.1,   │ │ live-tick    │ │  VM logs) │
   │               │ │  6.4)        │ │ pub/sub      │ │ (Sec. 7)  │
   └───────┬───────┘ └───────┬──────┘ └──────┬───────┘ └─────┬─────┘
           │                 │               │               │
           └────────┬────────┴───────┬───────┴───────┬───────┘
                     │                │               │
            ┌────────▼────────────────▼───────────────▼────────┐
            │      Go: Run Orchestrator + Log/Event Shipper      │
            │  (provisions/tears down GCE instances one-per-run, │
            │   ships local event-log to Cloud Logging/GCS,      │
            │   writes run-registry rows to Cloud SQL)           │
            └────────────────────────┬────────────────────────┘
                                      │
                          ┌───────────▼───────────┐
                          │  Local Visualization UI │
                          │  (Dash — grid view,     │
                          │   metric graphs, agent   │
                          │   memory-chain drill-    │
                          │   down; reads Cloud SQL, │
                          │   GCS, Redis)             │
                          └───────────────────────┘
```

---

## 4. Core Simulation Engine

### 4.1 State representation (tensor-primary)

| Structure | Shape / type | Sparsity | Draft reference |
|---|---|---|---|
| Belief matrix $\mathbf{B}$ | agents × propositions, `scipy.sparse.csr_matrix` | High — most agents haven't encountered most propositions | Sections 3.2–3.3, 4.9 |
| Trust tensor $\mathbf{T}$ | agents × sources × propositions | Very high — requires two specific agents to have interacted on a specific topic | Section 3.2, 4.9 |
| DAG adjacency (consequent) $D$ | propositions × propositions, row-normalized | Sparse, static per domain | Section 3.3 |
| DAG adjacency (antecedent) $A$ | propositions × propositions | Sparse, static per domain | Section 4.2 |
| Communication matrix $C$ | agents × agents, 0/1 | Rebuilt fresh every tick, ephemeral | Section 4.1, 4.6 |
| Grid positions | agents × 2, dense `numpy.ndarray` | N/A (dense, small) | Section 4.11 |
| Personal Affinity | agents × 2, dense, recomputed every tick | N/A | Section 4.11 |
| Per-agent coefficient table | agents × 9 (λ, μ, η, ξ, σ, χ, θ, π, $k^*$) | Dense, small | Section 3.6 |
| $k(I)$ assertion counts | agents × propositions, sparse | High | Section 3.7 |

**Trust tensor implementation note**: a true 3D sparse array is required. Two viable
approaches, in priority order:
1. `pydata/sparse` (N-dimensional sparse arrays, NumPy-compatible API, COO-backed) —
   preferred for code clarity and direct correspondence to the draft's tensor notation.
2. Fallback if (1) underperforms at target scale: a Python dict keyed by proposition ID,
   mapping to per-proposition `scipy.sparse` (agents × sources) matrices. Less elegant,
   but every individual 2D operation stays on well-optimized `scipy.sparse` code paths.

A benchmarking spike (Section 8, Milestone 0) must decide between these before committing.

**Static per-domain tensors** (the DAG adjacency matrices $D$ and $A$) are loaded once per
run from Cloud Storage and cached in Redis (Section 6.3) so that repeated runs against the
same domain — the common case across the ~3,960-run factorial — don't re-parse them from
scratch on every fresh Compute Engine instance.

### 4.2 Tick loop (Sections 4.1, 4.11)

Per tick, in order:
1. Compute Personal Affinity $\text{PA}(A)$ for every agent (Section 4.11) — vectorized:
   this is a sparse matrix operation over the whole population (gather known-neighbor
   positions and $\bar\tau$ values, weighted sum), not a per-agent loop.
2. Resolve movement: stay-threshold check → ε-greedy exploration/exploitation → collision
   resolution (Section 4.11). Collision resolution is the one sub-step most naturally
   iterative (sequential priority resolution among colliding agents at each contested
   cell) — but the *candidate move computation* feeding into it remains vectorized.
3. Trigger discovery (Section 3.8) and conversation (Section 4.1, 4.6) automatically based
   on resulting positions — vectorized via sparse boolean masks over occupied/seeded cells.
4. Apply belief and trust updates for all triggered events this tick: Alpha Flux, Forward
   Flow, flowback (Omega/Psi Flux), fallacy extensions (Section 3.7), composite trust
   derivation (Section 3.9) — all as batched sparse operations over the tick's dirty set
   (propositions/agents actually touched this tick), per Section 4.9's design.
5. Apply the ad hominem/halo-effect leak (Section 3.7) — the one mechanism requiring a
   batched per-pair gather/scatter rather than a single global matmul (Section 4.9).
6. Append all state-changing events from this tick to the event log (local buffer on the
   run's Compute Engine instance; shipped per Section 6.2/6.5).
7. Every $N$ ticks (configurable, default 50): write a full checkpoint to Cloud Storage.

### 4.3 Mechanism module boundaries

Each of the following is a separate, independently testable module, mapping 1:1 to a
draft section, so that the "trace every formula to a section" principle (Section 2.3) is
enforced structurally, not just by convention:

`fuzzy_resolution.py` (3.1) · `trust_belief_update.py` (3.2) · `reluctance.py` (3.3) ·
`smoothstep.py` (3.5) · `fallacy_extensions.py` (3.7) · `orphan_revelation.py` (3.8) ·
`composite_trust.py` (3.9) · `flowback.py` (4.2) · `influencer.py` (4.6) ·
`movement.py` (4.11)

### 4.4 Iterative fallback / validation harness

A separate, deliberately slow, per-agent-loop reference implementation of the *entire*
tick cycle must be built alongside the vectorized engine, run against small populations
(e.g., 10–20 agents) during development, and cross-checked for exact numerical agreement
with the vectorized path on identical seeds. This is the "iterative as secondary" mandate
from Section 2.1 — not a fallback for production use, but a correctness oracle. CI should
run this cross-validation on every change to a mechanism module.

---

## 5. Run-time Parameters and Configuration

Section 9's open items (χ/θ/π calibration, $\varepsilon_{\text{explore}}$/$\tau_{\text{still}}$
ranges, influencer reach $R$, Beta-shape robustness configurations) — plus the checkpoint
interval (Section 4.2 step 7) and every other tunable the draft leaves open — are supplied
per run as a single config document, never hardcoded in a mechanism module (Section 2.3,
Section 9).

- **Source of truth**: a row in Cloud SQL's `runs` table (`config` `jsonb` column,
  Section 6.1) — one row per run, written before the run's Compute Engine instance boots.
- **Hot path**: on instance start, the orchestrator (Go) pulls that row's config and the
  run's static domain tensors and writes them into **Redis** under a run-scoped key
  (`run:{run_id}:config`, `run:{run_id}:dag`). The simulation engine reads from Redis, not
  Cloud SQL, during the tick loop — Cloud SQL is not sized or latency-tuned for per-tick
  reads.
- Redis is a cache, not a system of record: if it is unreachable at instance start, the
  engine falls back to reading the Cloud SQL row (and the domain tensor from Cloud
  Storage) directly, then retries populating Redis. Losing Redis mid-run must never lose
  or corrupt config — the engine treats it as read-mostly, populated once at run start.

---

## 6. Data Storage (GCP)

### 6.0 Compute placement
Each run is assigned exactly **one Compute Engine instance** for its full lifetime
(Section 2, principle 4). The instance:
1. Boots from a prebuilt image/container carrying the Python simulation engine (Section 4).
2. Pulls its config from Cloud SQL and caches it in Redis (Section 5).
3. Pulls the run's static domain tensors ($D$, $A$) from Cloud Storage (Section 6.2).
4. Runs the tick loop entirely against local, in-memory tensors (Section 4.1) — no
   per-tick network I/O to any GCP service.
5. Periodically flushes checkpoints (Section 6.2) and event-log batches (Section 6.5) to
   Cloud Storage / Cloud Logging.
6. On completion (or failure), writes the run summary (Section 6.4) to Cloud SQL and is
   torn down by the Go orchestrator.

This placement is a fleet-provisioning problem for the ~3,960-run experiment budget
(Section 1), not a batch-queue-inside-one-VM problem — see Section 8's Go orchestrator.

### 6.1 Runtime state
In-memory tensors as specified in Section 4.1. No persistence during normal tick
processing on the instance's own disk — persistence happens only at checkpoint boundaries
(to Cloud Storage) and via the event log (to Cloud Logging / Cloud Storage), matching the
original design's intent that local disk is never the durable copy.

### 6.2 Checkpoints (Cloud Storage)
Full sparse-tensor snapshots at a configurable tick interval (default every 50 ticks) plus
always at run start/end. One archive per checkpoint, containing:
- $\mathbf{B}$, $\mathbf{T}$ (or the per-proposition dict fallback), grid positions, and
  the per-agent coefficient table.
- Format: a single compressed archive per checkpoint — `.npz` for the scipy-sparse/dense
  numpy pieces, bundled with a small Parquet file for the coefficient table (tabular, not
  sparse — Parquet is a better fit than embedding it in the npz).
- Written to a per-run prefix in a dedicated Cloud Storage bucket:
  `gs://freewill-checkpoints/{run_id}/tick_{tick:06d}.npz` (+ a sibling `.parquet`).
- **Explicitly not one file per agent.** At 500 agents × ~20 checkpoints/run × 3,960 runs,
  per-agent files would produce tens of millions of small files/objects — untenable for
  Cloud Storage request volume and for any downstream batch analysis.
- Cloud SQL's `checkpoints` table (Section 6.1's companion index) stores one row per
  checkpoint object (`run_id`, `tick`, `gcs_uri`, `created_at`) so the UI (Section 7) and
  memory-chain reconstruction (Section 7.4) can locate a checkpoint without listing the
  bucket.

### 6.3 Config and caching (Redis / Memorystore)
Covered in Section 5. Redis additionally serves as the **live-tick pub/sub** channel for
the currently-watched run in the visualization UI (Section 7.1's "live monitoring" use
case): the simulation engine publishes a lightweight per-tick summary (tick number,
positions delta, dirty-set size) to a run-scoped Redis channel; the Dash UI subscribes
while a run is being actively watched. This is an optimization for the handful of runs
actually watched live, not a substitute for the checkpoint/event-log record.

### 6.4 Run registry and run summary records (Cloud SQL / PostgreSQL)
Cloud SQL is the relational system of record for everything that is naturally row-shaped:
- **`runs`**: one row per run — `run_id`, `domain`, `seed`, `config` (`jsonb`, Section 5),
  `status`, `compute_instance`, `started_at`, `ended_at`.
- **`run_summaries`**: one row per completed run, written on run completion — Section
  4.7's metrics (saturation curves, stabilization times, polarization indices — both
  bimodality and variance, belief/trust cluster assignments, NMI/ARI), stored as
  structured columns plus a `jsonb` column for anything not worth a dedicated column.
  This is what the Section 4.8 statistical analysis plan consumes — not raw event logs or
  checkpoints.
- **`checkpoints`**: index over Cloud Storage checkpoint objects (Section 6.2).

See `infra/sql/schema.sql` for the DDL.

### 6.5 Event log (Cloud Logging, archived to Cloud Storage)
Append-only, one structured log entry per state-changing event, matching the original
JSON-lines record shape:
```json
{"run_id": "...", "tick": 142, "agent_id": 37, "event_type": "trust_update",
 "mechanism": "credibility_surprise", "proposition_id": 8, "source_id": 91,
 "old_value": -0.12, "new_value": 0.05}
```
`event_type` values: `discovery`, `revelation`, `message_received`, `trust_update`,
`belief_update`, `flowback`, `movement`, `fallacy_triggered` (with `mechanism` naming
which of Section 3.7's four — or, if later formalized, more — fallacies fired).

- The simulation engine writes each tick's events to a local JSON-lines buffer, then the
  Go log shipper (`go/cmd/logshipper`) ships batches as **structured Cloud Logging
  entries** (log name `freewill-events`, with `run_id`/`tick`/`event_type` as indexed
  labels for querying) and, in parallel, appends the same batch to a per-run object in
  Cloud Storage (`gs://freewill-event-logs/{run_id}/events.jsonl`) as the durable,
  full-fidelity archive — Cloud Logging has retention/ingestion limits unsuited to being
  the *only* copy of a multi-run experiment's full event history.
- This one log (Cloud Storage copy, indexed via Cloud Logging) serves three purposes with
  no duplication:
  1. **Correctness debugging** during development (via Cloud Logging's Log Explorer).
  2. **Observability** (Section 7) for real-time and post-hoc queries.
  3. **Per-agent memory-chain reconstruction** (Section 7.4's UI feature) — filter by
     `agent_id`, replay events in tick order, no separate storage needed.

---

## 7. Logging and Observability (Cloud Logging)

**Cloud Logging** is the observability backend, replacing the original design's
self-hosted Elastic Stack — same role (structured event search, near-real-time tailing of
a running instance, dashboards for cross-run comparison), native to the GCP stack the rest
of the system already runs on.

- Every Compute Engine instance runs with the Cloud Logging agent (or emits directly via
  the Cloud Logging API through the Go log shipper, Section 6.5) so simulation stdout/
  stderr, engine-level errors, and the structured event stream all land in the same
  project's log store.
- **Log-based structure**: two logical streams —
  - `freewill-events` — the per-tick event stream (Section 6.5), labeled by `run_id`,
    `tick`, `event_type`, `mechanism` for fast filtering in Log Explorer.
  - `freewill-runs` — lifecycle/orchestration logs from the Go orchestrator (instance
    provisioned, config loaded, checkpoint written, run completed/failed) plus GCE
    VM/serial console output.
- **Dashboards**: Cloud Monitoring dashboards over log-based metrics extracted from
  `freewill-events` (e.g., events/sec, fallacy-trigger rate) for (a) a live view of the
  handful of runs actually watched during development and the Section 4.10
  expectation-vs-reality pilot pass, and (b) aggregate views across a batch of runs.
  Cross-run *statistical* comparison (polarization index by domain, by seeding condition)
  is a Cloud SQL query over `run_summaries` (Section 6.4), not a log query — Cloud Logging
  is for the event stream and operational logs, Cloud SQL for the structured per-run
  metrics that feed Section 4.8's analysis plan.
- **Retention**: Cloud Logging's own retention window covers debugging/near-term
  observability; the Cloud Storage copy of the event log (Section 6.5) is the long-term,
  full-fidelity archive for the entire ~3,960-run budget.

---

## 8. Local Visualization UI

### 8.1 Scope decision
Given ~3,960 total runs, a live UI cannot reasonably be the primary interface for most of
them. The UI's two use cases:
1. **Live monitoring** — attached to a currently-running single run via Redis pub/sub
   (Section 6.3), used during development and the Section 4.10 pilot pass.
2. **Post-hoc replay/exploration** — reconstructing any completed run's state from its
   Cloud Storage checkpoints and event log, for deep-dive analysis of a specific
   interesting result.

### 8.2 Recommended stack
**Dash (Plotly)**, over Streamlit, given the need for multiple linked, interactive panels
(grid + graphs + drill-down) rather than a single linear script-driven page. Streamlit
remains a reasonable faster-to-build MVP alternative if Dash's development overhead proves
too high initially. The UI runs locally (a developer's machine) and connects out to Cloud
SQL, Cloud Storage, and Redis using the same project's credentials — it is not itself
deployed to GCP in this phase.

### 8.3 Required views
- **Grid view**: agent positions on the sandbox grid, color-coded by belief on a
  user-selected axiom or by detected cluster (Section 4.7); seeded axiom locations shown
  distinctly; a tick scrubber to move through simulation history (live-tailing via Redis
  pub/sub during a live run, or replaying from Cloud Storage checkpoints/event log for a
  completed run).
- **Belief/trust graphs**: population-level distributions per axiom over time (mean,
  variance, bimodality), and the belief-network/trust-network graphs from Section 4.7
  (reusing the same visual language as the earlier ideological-clustering diagrams already
  produced for this project — dense within-cluster ties, sparse cross-cluster ties, trust
  alliances vs. belief-agreement overlays).
- **Trust matrix heatmap**: a heatmap slice of $\mathbf{T}$ for a selected proposition.

### 8.4 Per-agent memory-chain visualization
On selecting an agent, reconstruct and display its temporal belief/trust evolution by
filtering the event log (Cloud Storage archive, Section 6.5) for that `agent_id` and
replaying events in tick order — directly analogous to the source dissertation's own
Temporal Memory Model figures (its Figures 2–3), but reconstructed on demand from the
event log rather than stored as a separate per-agent structure. This requires no new
storage — it is a query and rendering feature over data already being collected for
Section 7's logging pipeline.

---

## 9. Run Orchestration (Go)

Introduced by the GCP tech-stack decision (ADR 0001); not present in the original PRD.

- **`go/cmd/orchestrator`**: given a batch of run configs (the ~3,960-run experiment
  matrix), creates the Cloud SQL `runs` row, provisions one Compute Engine instance per
  run (from a prebuilt image), waits for completion/failure, and tears the instance down.
  Responsible for fleet-level concerns the Python engine should not own: retry-on-preempt,
  concurrency caps against project quota, and marking a run `failed` in Cloud SQL if its
  instance dies without writing a summary.
- **`go/cmd/logshipper`**: runs on each simulation instance alongside the Python engine;
  tails the local JSON-lines event-log buffer and ships batches to Cloud Logging and Cloud
  Storage (Section 6.5).
- Rationale for Go over Python for this layer: these are long-running, concurrent,
  infra-facing services (fleet management, log shipping) rather than numerical simulation
  code — a better fit for Go's concurrency model and static binaries in a container image,
  and keeps the Python side (Section 2) focused solely on the tensor-native simulation
  engine.

---

## 10. Milestones

- **M0 — Spike**: benchmark `pydata/sparse` vs. per-proposition dict-of-scipy-sparse for
  the trust tensor at representative scale (500 agents, growing proposition count over
  1000 ticks); decide Section 4.1's open implementation question.
- **M0.5 — Infra**: provision the GCP project's Cloud SQL instance, Memorystore Redis
  instance, Cloud Storage buckets (checkpoints, event logs), the Compute Engine instance
  template/image, and Cloud Logging sinks (`infra/terraform`); validate the Go
  orchestrator can provision and tear down a single instance end-to-end.
- **M1 — Core engine**: tick loop, state tensors, mechanism modules (Section 4.3), passing
  cross-validation against the iterative reference implementation (Section 4.4) on a small
  population.
- **M2 — Storage**: checkpointing (Cloud Storage) and event log (Cloud Logging + Cloud
  Storage), tested for correctness of the memory-chain reconstruction (Section 8.4)
  against known small-run ground truth.
- **M3 — Observability**: Cloud Logging ingestion live, Cloud Monitoring dashboards over
  a real run's event stream.
- **M4 — UI**: Dash app with all four required views (Section 8.3–8.4), live-tailing a
  single in-progress run via Redis pub/sub.
- **M5 — Scale validation**: run the Section 4.10 expectation-vs-reality pilot pass
  end-to-end through the full pipeline (orchestrator → N instances → Cloud SQL/Storage/
  Logging → UI) before committing to the 3,960-run core matrix.

---

## 11. Open Items Carried From the Formal Model

These are not implementation decisions — they are still-open modeling decisions from
FREE_WILL_checklist.md that the implementation must expose as configuration (Section 5)
rather than resolve unilaterally: χ/θ/π calibration (parked), $\varepsilon_{\text{explore}}$
and $\tau_{\text{still}}$ ranges (routed through Section 4.10's validation pass), the
influencer reach $R$ (range 20–50, one value to be selected via the same pass), and the
Beta-shape robustness-check configurations. The engine must accept all of these as
run-time parameters sourced from Cloud SQL/Redis (Section 5), never hardcoded defaults
baked into mechanism modules.
