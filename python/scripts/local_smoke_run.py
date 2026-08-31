#!/usr/bin/env python3
"""Smoke-test the docker-compose local stack end-to-end: Postgres (RunRegistry), Redis
(ConfigCache), and the GCS emulator (CheckpointStore) — the three storage backends PRD
Section 6 describes, each reached without touching real GCP (docs/adr/0002 and
docker-compose.yml's own docstring explain how). Run from `python/` with the compose
stack up:

    docker compose up -d
    PYTHONPATH=. python scripts/local_smoke_run.py

Exits non-zero on the first failure, printing which backend it was exercising — this is
also what `.github/workflows/ci.yml`'s `docker-compose` job runs, so a real regression in
any of the three local-mode code paths (RunRegistry.for_local_postgres,
CheckpointStore's STORAGE_EMULATOR_HOST auto-detection, plain redis.Redis) fails CI, not
just a docker-compose file nobody re-checks.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import redis

from freewill.config.params import PopulationStability, RunConfig, SeedingCondition
from freewill.storage.checkpoint_store import CheckpointStore
from freewill.storage.config_cache import ConfigCache
from freewill.storage.run_registry import RunRegistry


def _step(name: str):
    print(f"--- {name} ---", flush=True)


def main() -> int:
    postgres_dsn = os.environ.get(
        "POSTGRES_DSN", "host=localhost user=freewill password=freewill dbname=freewill sslmode=disable"
    )
    redis_addr = os.environ.get("REDIS_ADDR", "localhost:6379")
    checkpoints_bucket = os.environ.get("CHECKPOINTS_BUCKET", "freewill-checkpoints")
    run_id = "smoke-test-run"

    _step("Postgres (RunRegistry.for_local_postgres)")
    registry = RunRegistry.for_local_postgres(postgres_dsn)
    try:
        registry.create_run(run_id, domain="smoke-test", seed=1, config={"note": "local smoke run"})
        registry.mark_run_status(run_id, "running", compute_instance="local")
        fetched = registry.get_run_config(run_id)
        assert fetched["note"] == "local smoke run", f"unexpected config round-trip: {fetched}"
        registry.write_run_summary(run_id, {"stabilization_tick": 42})
        registry.record_checkpoint(run_id, tick=0, gcs_uri=f"gs://{checkpoints_bucket}/{run_id}/tick_000000.npz")
        checkpoints = registry.list_checkpoints(run_id)
        assert len(checkpoints) == 1, f"expected 1 checkpoint row, got {checkpoints}"
        registry.mark_run_status(run_id, "completed", compute_instance="local")
        print("Postgres OK: create/mark/get/summary/checkpoint round-tripped")
    finally:
        registry.close()

    _step("Redis (ConfigCache)")
    host, _, port = redis_addr.partition(":")
    r = redis.Redis(host=host, port=int(port or 6379))
    cache = ConfigCache(r)
    config = RunConfig(
        run_id=run_id,
        domain="smoke-test",
        seed=1,
        population_stability=PopulationStability.RANDOM,
        seeding_condition=SeedingCondition.FULLY_RANDOM,
        epsilon_explore=0.1,
        tau_still=0.05,
        influencer_reach=30,
        num_agents=10,
    )
    cache.put_config(config)
    restored = cache.get_config(run_id)
    assert restored == config, f"config round-trip mismatch: {restored!r} != {config!r}"
    cache.publish_tick_summary(run_id, tick=1, summary={"note": "smoke"})  # exercises the publish path
    print("Redis OK: RunConfig round-tripped through put_config/get_config")

    _step("GCS emulator (CheckpointStore, via STORAGE_EMULATOR_HOST)")
    if not os.environ.get("STORAGE_EMULATOR_HOST"):
        print("STORAGE_EMULATOR_HOST not set -- skipping (see docker-compose.yml)")
    else:
        store = CheckpointStore(checkpoints_bucket)
        coeff_table = pd.DataFrame({"lambda": [0.5], "mu": [0.5]})
        ref = store.write_checkpoint(
            run_id, tick=0, arrays={"belief": np.zeros((2, 2))}, coefficient_table=coeff_table
        )
        arrays, table = store.read_checkpoint(run_id, tick=0)
        assert np.array_equal(arrays["belief"], np.zeros((2, 2))), "checkpoint array round-trip failed"
        assert list(table.columns) == ["lambda", "mu"], f"unexpected coefficient columns: {table.columns}"
        print(f"GCS emulator OK: wrote/read {ref.npz_uri}")

    print("\nALL LOCAL STACK CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
