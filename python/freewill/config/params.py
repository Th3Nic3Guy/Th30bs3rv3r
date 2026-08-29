"""Run-time parameter schema.

PRD Section 2.3 / Section 11 ("Open Items Carried From the Formal Model"): anything the
draft leaves open (chi/theta/pi calibration, epsilon_explore / tau_still ranges, the
influencer reach R, Beta-shape robustness-check configs) must be a configurable, run-time
parameter — never a constant baked into a mechanism module.

`RunConfig` is the schema for one run's config document. The source of truth for a
submitted run is the `config` jsonb column on Cloud SQL's `runs` table
(PRD Section 5 / infra/sql/schema.sql); at run start it is cached into Redis under
`run:{run_id}:config` (PRD Section 5's "hot path") and read from there during the tick
loop. This module only defines the schema and (de)serialization — see
freewill.storage.config_cache for the Redis-backed loader used by the running engine.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, model_validator


class BetaShapeConfig(BaseModel):
    """One Beta-distribution shape used for a robustness-check configuration.

    Beta(alpha, beta) over [0, 1], per FREE_WILL_checklist.md's robustness-check matrix
    (PRD Section 1, Section 11).
    """

    alpha: float = Field(gt=0)
    beta: float = Field(gt=0)


class RunConfig(BaseModel):
    """Full run-time parameter set for a single simulation run.

    Every field here corresponds to an explicitly open item in the formal model (PRD
    Section 11) or an engine-level tunable (checkpoint interval, PRD Section 4.2 step 7).
    Do not add a field whose value could instead be derived/hardcoded from the draft —
    per PRD Section 2.3, only genuinely open modeling decisions belong here.
    """

    run_id: str
    domain: str
    seed: int

    # Per-agent coefficient ranges (PRD 3.6, 4.1) — sampled per agent at population init,
    # not fixed constants. chi/theta/pi calibration is explicitly parked (PRD Section 11).
    chi_range: tuple[float, float]
    theta_range: tuple[float, float]
    pi_range: tuple[float, float]

    # Movement (PRD 4.11): epsilon-greedy exploration and the "stay" threshold.
    epsilon_explore: float = Field(ge=0.0, le=1.0)
    tau_still: float

    # Influencer reach (PRD 4.6): draft-specified range is 20-50; the specific value is
    # resolved via the Section 4.10 validation pass, not hardcoded here.
    influencer_reach: int = Field(ge=20, le=50)

    # Robustness-check Beta-shape configuration (PRD Section 11), optional — only set for
    # robustness-check runs in the experiment budget (PRD Section 1).
    beta_shape: BetaShapeConfig | None = None

    # Engine-level tunables.
    num_agents: int = Field(gt=0)
    num_ticks: int = Field(gt=0)
    checkpoint_interval_ticks: int = Field(default=50, gt=0)

    @model_validator(mode="after")
    def _validate_ranges(self) -> "RunConfig":
        for name in ("chi_range", "theta_range", "pi_range"):
            lo, hi = getattr(self, name)
            if lo > hi:
                raise ValueError(f"{name}: lower bound {lo} exceeds upper bound {hi}")
        return self

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str | bytes) -> "RunConfig":
        return cls.model_validate(json.loads(raw))

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def load_run_config(source: dict[str, Any] | str | bytes) -> RunConfig:
    """Parse a RunConfig from a dict (e.g. a Cloud SQL jsonb row) or raw JSON (e.g. a
    Redis string value)."""
    if isinstance(source, (str, bytes)):
        return RunConfig.from_json(source)
    return RunConfig.model_validate(source)
