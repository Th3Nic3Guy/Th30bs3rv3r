"""Redis (Memorystore) client for run config, static domain tensors, and live-tick
pub/sub (PRD Section 5, 6.3).

Redis is a cache, not a system of record (PRD Section 2, principle 5): every value here
must be reconstructable from Cloud SQL (config) or Cloud Storage (domain tensors). Callers
must treat a cache miss as expected, not exceptional, and fall back to the durable source.
"""

from __future__ import annotations

import json
from typing import Any

import redis

from freewill.config.params import RunConfig

_CONFIG_KEY = "run:{run_id}:config"
_DAG_KEY = "domain:{domain}:dag"
_LIVE_TICK_CHANNEL = "run:{run_id}:live"

_CONFIG_TTL_SECONDS = 24 * 3600  # config is read-mostly; a generous TTL just bounds staleness
_DAG_TTL_SECONDS = 7 * 24 * 3600  # static per-domain tensors change rarely


class ConfigCache:
    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    # -- run config (PRD Section 5) -----------------------------------------------------

    def put_config(self, config: RunConfig) -> None:
        self._r.set(_CONFIG_KEY.format(run_id=config.run_id), config.to_json(), ex=_CONFIG_TTL_SECONDS)

    def get_config(self, run_id: str) -> RunConfig | None:
        raw = self._r.get(_CONFIG_KEY.format(run_id=run_id))
        if raw is None:
            return None
        return RunConfig.from_json(raw)

    # -- static per-domain DAG adjacency cache (PRD Section 4.1, 6.3) -------------------

    def put_domain_dag(self, domain: str, serialized_dag: bytes) -> None:
        """`serialized_dag` is whatever compact byte representation the engine's tensor
        serialization layer produces for D and A (PRD 4.1) — this cache is opaque to it."""
        self._r.set(_DAG_KEY.format(domain=domain), serialized_dag, ex=_DAG_TTL_SECONDS)

    def get_domain_dag(self, domain: str) -> bytes | None:
        return self._r.get(_DAG_KEY.format(domain=domain))

    # -- live-tick pub/sub for the visualization UI (PRD Section 6.3, 8.1) --------------

    def publish_tick_summary(self, run_id: str, tick: int, summary: dict[str, Any]) -> None:
        payload = json.dumps({"tick": tick, **summary})
        self._r.publish(_LIVE_TICK_CHANNEL.format(run_id=run_id), payload)

    def subscribe_live_tick(self, run_id: str) -> redis.client.PubSub:
        pubsub = self._r.pubsub()
        pubsub.subscribe(_LIVE_TICK_CHANNEL.format(run_id=run_id))
        return pubsub
