# Development Task List

Working checklist for building out the FREE WILL simulation platform from its current
scaffold (see `FREE_WILL_PRD.md` for design, `adr/0001-gcp-tech-stack.md` for the GCP
stack). Ordered by the PRD's milestones (`FREE_WILL_PRD.md` Section 10); check items off
as they land. Each item names the file(s) it touches.

## Blocking prerequisite

- [ ] **Add `FREE_WILL_draft.md` (and the decisions log / checklist / axiom-hierarchy
      docs) to this repo.** Every mechanism module in `python/freewill/mechanisms/` and
      every metric in `python/freewill/metrics/metrics.py` is currently a stub raising
      `NotImplementedError` specifically because these source documents aren't here yet
      (PRD Section 2.3: no formula gets invented ahead of the draft). Nothing in M1–M5
      below can start for real until this lands.

## M0 — Trust tensor spike

- [ ] Benchmark `pydata/sparse` (COO-backed N-D arrays) vs. a `dict[proposition_id ->
      scipy.sparse]` fallback for the trust tensor $\mathbf{T}$, at representative scale
      (500 agents, growing proposition count, 1000 ticks) — PRD Section 4.1's
      implementation note.
- [ ] Record the decision (a short ADR, e.g. `docs/adr/0002-trust-tensor-backend.md`) and
      update `python/freewill/engine/state.py`'s `trust_tensor` docstring to name the
      chosen representation instead of leaving it `object`.

## M0.5 — Infra live

- [ ] Build the run-instance image from `python/Dockerfile` + `go/Dockerfile.logshipper`
      (PRD Section 6.0 step 1) and publish it; fill in
      `infra/terraform/terraform.tfvars.example`'s `run_instance_source_image`.
- [ ] `terraform init && terraform plan && terraform apply` in `infra/terraform/` against
      a real GCP project.
- [ ] Apply `infra/sql/schema.sql` to the provisioned Cloud SQL instance.
- [ ] Validate `go/cmd/orchestrator` can provision and tear down a single real Compute
      Engine instance end-to-end (`-project`, `-cloudsql-instance`, `-redis-addr`,
      `-source-image`, `-service-account` flags all point at the real resources).
- [ ] Wire CI (or a local script) to run `go build ./... && go vet ./...` in `go/` and
      `pytest` in `python/` on every push — nothing currently automates the checks this
      session ran by hand.

## M1 — Core engine

Implement each mechanism module against its draft section, replacing the
`NotImplementedError` stub:

- [ ] `python/freewill/mechanisms/fuzzy_resolution.py` — draft 3.1
- [ ] `python/freewill/mechanisms/trust_belief_update.py` — draft 3.2 (Alpha Flux, Forward Flow)
- [ ] `python/freewill/mechanisms/reluctance.py` — draft 3.3
- [ ] `python/freewill/mechanisms/smoothstep.py` — draft 3.5
- [ ] `python/freewill/mechanisms/fallacy_extensions.py` — draft 3.7 (batched extensions
      + the ad hominem/halo leak's per-pair gather/scatter)
- [ ] `python/freewill/mechanisms/orphan_revelation.py` — draft 3.8
- [ ] `python/freewill/mechanisms/composite_trust.py` — draft 3.9
- [ ] `python/freewill/mechanisms/flowback.py` — draft 4.2 (Omega Flux, Psi Flux)
- [ ] `python/freewill/mechanisms/influencer.py` — draft 4.6 (communication matrix + reach $R$)
- [ ] `python/freewill/mechanisms/movement.py` — draft 4.11 (Personal Affinity, candidate
      moves, collision resolution)

Wire the tick loop up to real implementations:

- [ ] `python/freewill/engine/tick_loop.py`: thread a seeded `np.random.Generator` from
      `config.seed` through to `movement.compute_candidate_moves` (currently `rng=None`).
- [ ] `python/freewill/engine/tick_loop.py`: derive `dirty_propositions` / `dirty_agents`
      from step 3's discovery/conversation output instead of the current `None`
      placeholders passed into steps 4–5.
- [ ] `python/freewill/engine/tick_loop.py`: pass `colliding_pairs` from
      `movement.resolve_collisions`'s output into `apply_ad_hominem_halo_leak` instead of
      the current `[]` placeholder.
- [ ] `python/freewill/engine/tick_loop.py`: wire each mechanism call to append its
      events to `EventLogBuffer` (PRD 4.2 step 6) — not yet threaded through the stub loop.
- [ ] `python/freewill/engine/tick_loop.py` `_write_checkpoint`: serialize
      `state.belief_matrix` / `state.trust_tensor` into `savez`-compatible component
      arrays instead of the current partial `arrays` dict.
- [ ] `python/freewill/__main__.py`: implement the real pipeline (load `RunConfig` via
      `freewill.storage.{run_registry,config_cache}`, build the initial
      `SimulationState`, call `freewill.engine.run_simulation`) — currently raises
      `NotImplementedError`.

Validation harness (PRD Section 4.4):

- [ ] `python/freewill/validation/iterative_reference.py`: implement the per-agent-loop
      reference for each mechanism, mirroring the vectorized modules above.
- [ ] `python/tests/test_cross_validation.py`: un-skip and assert exact numerical
      agreement between `freewill.engine.run_tick` and
      `freewill.validation.run_iterative_reference` on identical seeds, 10–20 agents.
- [ ] Add this cross-validation run to CI, gated on any change under
      `python/freewill/mechanisms/`, per PRD Section 4.4's "on every change" mandate.

## M2 — Storage

- [ ] `python/freewill/storage/checkpoint_store.py`: exercise `write_checkpoint` /
      `read_checkpoint` against a real (or emulated) GCS bucket once M1's tensor
      serialization exists; today it's untested beyond the stub interface.
- [ ] `python/freewill/storage/event_log.py` + `go/cmd/logshipper`: end-to-end test —
      engine writes to `EventLogBuffer`, log shipper tails the staging file, ships to
      Cloud Logging + GCS, and the batch objects are readable back.
- [ ] `go/cmd/logshipper/main.go`: replace the per-batch object layout
      (`{run_id}/batches/events-{seq}.jsonl`) with (or add a compaction step producing)
      the single `{run_id}/events.jsonl` archive PRD Section 6.5 describes — currently a
      TODO in that file.
- [ ] Build the per-agent memory-chain reconstruction (PRD Section 8.4): filter the
      Cloud Storage event-log archive by `agent_id`, replay in tick order. Test against a
      known small-run ground truth.
- [ ] `python/freewill/metrics/metrics.py`: implement `compute_run_metrics` against draft
      4.7 (saturation curves, stabilization time, polarization bimodality/variance,
      cluster assignments, NMI/ARI) and confirm it round-trips through
      `RunRegistry.write_run_summary` into `run_summaries`.

## M3 — Observability

- [ ] Run a real simulation end-to-end and confirm `freewill-events` / `freewill-runs`
      entries land in Cloud Logging with the expected `run_id`/`tick`/`event_type`/
      `mechanism` labels (`infra/terraform/logging.tf`'s bucket + log-based metric).
- [ ] Build the Cloud Monitoring dashboard(s) over `freewill_fallacy_triggered_count` and
      any other log-based metrics worth adding for the live/aggregate views (PRD Section 7).
- [ ] Write the Cloud SQL queries `run_summaries` needs to support cross-run comparison
      (polarization index by domain, by seeding condition — PRD Section 7, feeding
      Section 4.8's downstream analysis plan).

## M4 — UI

- [ ] Stand up the Dash app (`python/freewill`'s `ui` extra in `pyproject.toml` is
      declared but unused so far) with the four required views (PRD Section 8.3–8.4):
      grid view, belief/trust graphs, trust matrix heatmap, per-agent memory-chain
      drill-down.
- [ ] Live-tail a single in-progress run via `freewill.storage.config_cache.ConfigCache
      .subscribe_live_tick` (already implemented) — the engine side needs to actually
      call `publish_tick_summary` from the tick loop, which it doesn't yet.
- [ ] Post-hoc replay path: reconstruct a completed run's state from Cloud Storage
      checkpoints + the event-log archive via `CheckpointStore.read_checkpoint`.

## M5 — Scale validation

- [ ] Run the Section 4.10 expectation-vs-reality pilot pass end-to-end through the full
      pipeline (orchestrator → N instances → Cloud SQL/Storage/Logging → UI) before
      committing to the 3,960-run core matrix.
- [ ] `go/cmd/orchestrator/main.go`: implement batch mode over the full experiment matrix
      — today it only handles `-run-id` (a single run) and assumes the Cloud SQL row
      already exists; it needs to create rows itself, cap concurrency against project
      quota, and retry preemptible-instance preemption (all flagged as TODOs in that file).
- [ ] Decide and document the resolved values for Section 11's open items (χ/θ/π,
      $\varepsilon_{\text{explore}}$/$\tau_{\text{still}}$, influencer reach $R$ in
      [20, 50], Beta-shape robustness configs) coming out of the pilot pass, and set them
      as the defaults new `RunConfig` submissions use.

## Cross-cutting / hardening (not milestone-gated)

- [ ] `python/freewill/config/params.py`: confirm `RunConfig`'s field set actually covers
      every parameter the finished mechanism modules need — it was written ahead of the
      formulas, so expect additions once M1 lands.
- [ ] `go/internal/cloudsql`, `go/internal/rediscache`: add tests (both currently have
      none — they were type-checked via `go build`/`go vet` but not exercised against a
      real or emulated backend).
- [ ] Decide on and wire up structured logging inside the Python engine itself (today it
      relies entirely on the event log + the Go log shipper; engine-level errors/warnings
      have no destination yet).
- [ ] `infra/terraform/`: run a real `terraform plan` review for cost/quota sanity before
      M5's 3,960-run commitment — `n2-standard-4` × concurrent-run-count against project
      quota isn't sized yet.
