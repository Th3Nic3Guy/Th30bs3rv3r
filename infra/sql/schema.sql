-- Cloud SQL (PostgreSQL) schema for the FREE WILL run registry (PRD Section 6.4).
-- Applied to the database Terraform provisions (infra/terraform/cloudsql.tf).

CREATE TABLE IF NOT EXISTS runs (
    run_id            text PRIMARY KEY,
    domain            text NOT NULL,
    seed              bigint NOT NULL,
    -- Run-time parameters (PRD Section 5 / 11): chi/theta/pi ranges, epsilon_explore,
    -- tau_still, influencer_reach, beta_shape, checkpoint interval, etc. — the full
    -- freewill.config.params.RunConfig document.
    config            jsonb NOT NULL,
    status            text NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'provisioning', 'running', 'completed', 'failed')),
    compute_instance  text,
    started_at        timestamptz NOT NULL DEFAULT now(),
    ended_at          timestamptz
);

CREATE INDEX IF NOT EXISTS idx_runs_domain_status ON runs (domain, status);

-- One row per completed run: PRD Section 4.7's metric set, consumed by the (downstream,
-- out-of-scope) Section 4.8 statistical analysis plan. Structured columns for the metrics
-- named explicitly in the PRD; `metrics` holds the full document (including anything not
-- worth a dedicated column) so freewill.metrics.RunMetrics can round-trip without a
-- migration for every new metric.
CREATE TABLE IF NOT EXISTS run_summaries (
    run_id                    text PRIMARY KEY REFERENCES runs (run_id),
    stabilization_tick        integer,
    polarization_bimodality   double precision,
    polarization_variance     double precision,
    nmi                       double precision,
    ari                       double precision,
    metrics                   jsonb NOT NULL,
    created_at                timestamptz NOT NULL DEFAULT now()
);

-- Index over Cloud Storage checkpoint objects (PRD Section 6.2), so the UI (Section 8)
-- and per-agent memory-chain reconstruction (Section 8.4) can locate a checkpoint
-- without listing the bucket.
CREATE TABLE IF NOT EXISTS checkpoints (
    id          bigserial PRIMARY KEY,
    run_id      text NOT NULL REFERENCES runs (run_id),
    tick        integer NOT NULL,
    gcs_uri     text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, tick)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_run_id ON checkpoints (run_id);
