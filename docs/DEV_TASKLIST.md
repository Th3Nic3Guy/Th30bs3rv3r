# Development Task List

Working checklist for building out the FREE WILL simulation platform from its current
scaffold (see `FREE_WILL_PRD.md` for design, `adr/0001-gcp-tech-stack.md` for the GCP
stack). Ordered by the PRD's milestones (`FREE_WILL_PRD.md` Section 10); check items off
as they land. Each item names the file(s) it touches.

## Blocking prerequisite

- [x] **Add `FREE_WILL_draft.md` to this repo.** Landed at `docs/FREE_WILL_draft.md`.
      The companion decisions log / checklist / 10 domain axiom-hierarchy documents are
      still not in the repo — nothing below needs them yet (M1's mechanism math is fully
      specified in the draft alone), but M2's metrics work and loading real domain axiom
      hierarchies into `PropositionSchema` will need them.

## M0 — Trust tensor spike

- [x] **Decision made without the benchmark** (`docs/adr/0002-engine-state-representation.md`):
      trust tensor is `dict[proposition_id -> scipy.sparse]` (PRD 4.1's own stated
      fallback), belief/omega are dense NumPy. This unblocked M1 since no GCP infra was
      reachable this session to actually run the benchmark.
- [ ] Still worth doing before the full run matrix: benchmark `pydata/sparse` vs. the
      dict-of-scipy-sparse choice actually made, at representative scale (500 agents,
      growing proposition count, 1000 ticks), to confirm ADR 0002 holds at that scale —
      not just re-litigate it from scratch.

## M0.5 — Infra live

- [x] **Local dev stack** (`docker-compose.yml`, `docs/LOCAL_DEV.md`): Postgres + Redis +
      `fake-gcs-server` stand in for Cloud SQL/Memorystore/Cloud Storage with no GCP
      project needed. Cloud Storage needed zero code changes (both storage client
      libraries auto-detect `STORAGE_EMULATOR_HOST`); Cloud SQL needed a real bypass path
      since it has no official emulator (`RunRegistry.for_local_postgres`,
      `cloudsql.OpenLocal`); Cloud Logging has no local stand-in at all
      (`go/cmd/logshipper -local` just logs to stdout instead). `python/scripts/
      local_smoke_run.py` exercises all three round-trips end-to-end and is what the new
      `docker-compose` CI job runs — this sandbox has no Docker daemon, so, same as
      Terraform, CI is the only place this has actually been run against live containers.
      **Confirmed green**: [run 33378857533](https://github.com/Th3Nic3Guy/Th30bs3rv3r/actions/runs/33378857533),
      all 4 jobs passed; the `docker-compose` job's own log shows the smoke script's real
      output — `Postgres OK: create/mark/get/summary/checkpoint round-tripped`,
      `Redis OK: RunConfig round-tripped through put_config/get_config`,
      `GCS emulator OK: wrote/read gs://freewill-checkpoints/smoke-test-run/tick_000000.npz`,
      `ALL LOCAL STACK CHECKS PASSED` — not just a green checkmark taken on faith.
- [ ] `go/cmd/orchestrator`: no local-dev path — its whole job is GCE-specific and has no
      local equivalent (there's nothing to "provision" on a laptop). Not a gap to close;
      just don't expect `docker-compose.yml` to exercise it.
- [x] **CI wired and confirmed actually running** (`.github/workflows/ci.yml`) — a first
      attempt used `on: push: branches: [main]` and silently never ran on this
      feature-branch-only workflow (zero recorded runs); fixed to trigger on every push.
      Run [33376607581](https://github.com/Th3Nic3Guy/Th30bs3rv3r/actions/runs/33376607581)
      confirms all three jobs green on GitHub's runners: `terraform fmt/init/validate`
      against the real `hashicorp/google` provider (this sandbox's network policy blocks
      `registry.terraform.io`, so this is the first time the Terraform was actually
      schema-validated, not just formatted), `go build/vet/test/gofmt` on a clean
      checkout, and `pip install -e ".[dev,ui]"` + `ruff` + `pytest` with every dependency
      resolved for real (including the `cloud-sql-python-connector[psycopg]` fix and the
      `dash`/`plotly` UI extras).
- [ ] Build the run-instance image from `python/Dockerfile` + `go/Dockerfile.logshipper`
      (PRD Section 6.0 step 1) and publish it; fill in
      `infra/terraform/terraform.tfvars.example`'s `run_instance_source_image`. Needs a
      real GCP project/registry — no credentials available in this session's sandbox.
- [ ] `terraform init && terraform plan && terraform apply` in `infra/terraform/` against
      a real GCP project. `validate` is now confirmed clean (above); `plan`/`apply` need
      real project credentials this sandbox doesn't have.
- [ ] Apply `infra/sql/schema.sql` to the provisioned Cloud SQL instance.
- [ ] Validate `go/cmd/orchestrator` can provision and tear down a single real Compute
      Engine instance end-to-end (`-project`, `-cloudsql-instance`, `-redis-addr`,
      `-source-image`, `-service-account` flags all point at the real resources).

## M1 — Core engine

All ten original mechanism modules are implemented against the draft, plus an eleventh
(`message_formulation.py`, draft 4.12) the original module list missed — see PRD Section
4.3's "Added during M1 implementation" note. `engine/state.py` was rebuilt around them
(`docs/adr/0002-engine-state-representation.md`) and `engine/tick_loop.py` wires them
into draft 4.11's six-step tick sequence end-to-end (checked with a hand-built 6-agent
smoke run — belief converges plausibly toward an influencer's agenda, discovery/known
tracking behaves correctly, no crashes over 20 ticks). Unit tests
(`tests/test_mechanisms.py`, `tests/test_config_params.py`) cover the pure-math pieces
(fuzzy resolution, SmoothStep, reluctance, fallacy extensions) against hand-worked values
from the draft's own formulas. 37 tests pass (including the cross-validation harness
below); `ruff check .` is clean.

- [x] `fuzzy_resolution.py` (3.1), `trust_belief_update.py` (3.2), `reluctance.py` (3.3),
      `smoothstep.py` (3.5), `fallacy_extensions.py` (3.7), `orphan_revelation.py` (3.8),
      `composite_trust.py` (3.9), `flowback.py` (4.2), `influencer.py` (4.6),
      `movement.py` (4.11), `message_formulation.py` (4.12, new).
- [x] `engine/tick_loop.py` wired to real implementations, with a seeded
      `np.random.Generator` threaded through, `k_assertions` incremented on each outgoing
      message, and events appended to `EventLogBuffer` for discovery/belief_update/
      revelation/message_received.
- [x] `python/tests/test_mechanisms.py`: real assertions (not stubs) for the pure-math
      modules.

**Known gaps left from this pass** (none silent — each is a real follow-up, not a
correctness bug found and left unfixed):

- [x] `composite_trust.py` (draft 3.9) is now wired into `compute_alpha`
      (`trust_belief_update.py`): before each proposition's matvec, composite operands'
      trust masks are AND-ed to find every (receiver, publisher) pair with trust on both
      operands but not on the composite itself, and derives+stores the fallback in one
      batched call — `composite_trust.derive_missing_for_proposition`, replacing the
      earlier per-pair `find_derivable`/`derive_and_store` stubs (never wired anywhere)
      with a properly vectorized version. 4 new unit tests
      (`tests/test_mechanisms.py::TestCompositeTrust`) check derivation, the
      both-operands-required gate, that an existing direct entry is never clobbered by
      the structural fallback, and the axiom no-op case.
- [ ] `tick_loop.py`'s per-tick scheduling (Personal Affinity's neighbor gather, move
      resolution, conversation triggering) is a Python loop over agents, not vectorized —
      documented as an intentional scope trim in the module's own docstring (correctness
      over population-scale performance for this pass), but real follow-up work before
      running at 300–500 agents × 1000 ticks × ~3,960 runs. `TrustStore.known_neighbors`
      plus a fixed-width neighbor-set padding scheme is the likely vectorization path.
- [ ] `influencer.top_up_reach`'s selection rule (which agents fill an under-crowded
      influencer's reach up to $R$) is a documented implementation choice (uniform random)
      — the draft states *that* R agents are reached but not *how* the selection works
      beyond physical co-location. Flag for the Section 4.10 validation pass or an
      explicit decisions-log entry, not a silent assumption.
- [ ] `engine/tick_loop.py`'s `_apply_message` reluctance/gamma computation
      (`reluctance.compute_rho`/`compute_gamma`) recomputes over the *entire* belief
      matrix once per message rather than restricting to the touched agent — correct but
      wasteful; tighten once a real profiling run justifies it.
- [ ] `python/freewill/__main__.py`: still raises `NotImplementedError` — implement the
      real pipeline (load `RunConfig` via `freewill.storage.{run_registry,config_cache}`,
      build the initial `SimulationState` — including loading a real domain's
      `PropositionSchema`/`DagAdjacency` from an axiom-hierarchy document, which doesn't
      exist in this repo yet — call `freewill.engine.run_simulation`).
- [ ] `engine/tick_loop.py` `_write_checkpoint`: writes dense arrays directly into the
      `.npz`; revisit once `CheckpointStore`'s sparse-serialization assumption (PRD 6.2)
      is reconciled with ADR 0002's dense-array decision — probably just works as-is
      (`np.savez_compressed` handles dense arrays natively) but hasn't been exercised
      against a real GCS bucket.

Validation harness (PRD Section 4.4):

- [x] `python/freewill/validation/iterative_reference.py`: naive per-agent-loop
      references for the five functions where a real vectorized-vs-naive contrast exists
      today — `reluctance.compute_rho`, `trust_belief_update.compute_alpha`,
      `flowback.omega_flux`, `orphan_revelation.find_revelation_candidates`,
      `composite_trust.derive_missing_for_proposition` — with a scope note in the
      module's own docstring on why this isn't a from-scratch reference of the whole tick
      cycle (the vectorized engine already processes most of a tick per-message, not in
      population-wide batches, so a full re-implementation would mostly duplicate that
      same per-message code rather than exercise a different path). Revisit the scope if
      `tick_loop.py`'s per-agent scheduling loop is later vectorized further.
- [x] `python/tests/test_cross_validation.py`: real tests now (the un-skip), cross-
      checking all five functions above against 20 random seeds and 10-agent populations
      each — `np.testing.assert_allclose` for the numeric ones, exact set-equality plus
      independently-recomputed expected values for the two trigger-scan functions. 37
      tests pass total (32 unit + 5 cross-validation classes), `ruff check .` clean.
- [x] Given its own explicit, separately-named step in the `python` CI job
      (`.github/workflows/ci.yml`) so a regression shows as its own failing step in the
      Actions UI, not buried inside the general `pytest -q` run. Runs on every push (not
      path-filtered to `mechanisms/` specifically — GitHub Actions doesn't support
      per-step path filters, only per-workflow, and this workflow already covers Python/
      Go/Terraform/compose together) — broader than PRD 4.4's literal "on every change to
      a mechanism module" but strictly a superset of it.
      **Confirmed green**: [run 33418247784](https://github.com/Th3Nic3Guy/Th30bs3rv3r/actions/runs/33418247784),
      all 4 jobs passed, with "Cross-validate mechanism modules against the iterative
      reference (PRD 4.4)" showing as its own distinct, passing step in the Python job —
      not just planned, actually landed and running that way. The two preceding commits
      (composite-trust wiring, the harness itself) were also both green on GitHub's
      runners.

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

- [x] `python/freewill/config/params.py`: rebuilt against draft Section 3.6's actual
      per-agent coefficient distributions (`AgentCoefficientDistributions`, one `BetaSpec`
      per coefficient) plus `PopulationStability`/`SeedingCondition` enums for draft
      4.3/4.4/4.6's run conditions — superseding the pre-draft placeholder schema.
- [ ] `go/internal/cloudsql`, `go/internal/rediscache`: add tests (both currently have
      none — they were type-checked via `go build`/`go vet` but not exercised against a
      real or emulated backend).
- [ ] Decide on and wire up structured logging inside the Python engine itself (today it
      relies entirely on the event log + the Go log shipper; engine-level errors/warnings
      have no destination yet).
- [ ] `infra/terraform/`: run a real `terraform plan` review for cost/quota sanity before
      M5's 3,960-run commitment — `n2-standard-4` × concurrent-run-count against project
      quota isn't sized yet.
