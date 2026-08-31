"""Run-time parameter schema.

PRD Section 2.3 / Section 11: anything the draft leaves open must be a configurable,
run-time parameter — never a constant baked into a mechanism module. With
`FREE_WILL_draft.md` now in the repo, this schema is built directly against its Section
3.6 (per-agent coefficient distributions) and the specific still-open items named in
Sections 3.7, 4.6, 4.10, 4.12: chi/theta default calibration, epsilon_explore/tau_still,
the influencer reach R, and whether epsilon_topic is tied to epsilon_explore.

`RunConfig` is the schema for one run's config document. The source of truth for a
submitted run is the `config` jsonb column on Cloud SQL's `runs` table
(PRD Section 5 / infra/sql/schema.sql); at run start it is cached into Redis under
`run:{run_id}:config` (PRD Section 5's "hot path") and read from there during the tick
loop.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class BetaSpec(BaseModel):
    """A Beta(a, b) distribution scaled to [low, high], per draft Section 3.6's table.

    `round_to_int` supports k* (draft: "scaled and rounded to integers in [1,10] via
    k* = round(1 + 9*Beta)").
    """

    a: float = Field(gt=0)
    b: float = Field(gt=0)
    low: float
    high: float
    round_to_int: bool = False

    @model_validator(mode="after")
    def _validate_range(self) -> BetaSpec:
        if self.low > self.high:
            raise ValueError(f"low ({self.low}) exceeds high ({self.high})")
        return self

    def sample(self, rng, n: int):
        """Draw `n` i.i.d. samples, scaled to [low, high] (and rounded, for k*)."""
        raw = rng.beta(self.a, self.b, size=n)
        scaled = self.low + raw * (self.high - self.low)
        if self.round_to_int:
            import numpy as np

            return np.round(scaled).astype(int)
        return scaled


class AgentCoefficientDistributions(BaseModel):
    """The per-agent parameter tuple (lambda, mu, eta, xi, sigma, chi, theta, pi, k_star),
    each independently Beta-distributed per draft Section 3.6's table. Defaults are the
    draft's own specified (a, b, range) values — these are not "open" in the sense
    Section 11 means (the draft is explicit about them), but PRD Section 9/11's
    "Beta-shape robustness-check configurations" vary exactly these shape parameters as a
    modeling-assumption robustness check (draft Section 5.3), so every field is
    overridable per run rather than hardcoded in a mechanism module.

    Note on chi/theta: draft Section 3.7 flags "default value for chi and theta still
    needs pre-registration/calibration" as a TODO, but Section 3.6's table already gives
    both a concrete Beta distribution — that table is the more specific, later-stated
    formalization and is what this schema implements; the 3.7 TODO is treated as
    superseded by it (see docs/adr/0002-engine-state-representation.md's scope note).
    """

    lambda_: BetaSpec = Field(default=BetaSpec(a=2, b=2, low=0.0, high=1.0), alias="lambda")
    mu: BetaSpec = BetaSpec(a=2, b=2, low=0.0, high=1.0)
    eta: BetaSpec = BetaSpec(a=2, b=5, low=0.0, high=1.0)
    xi: BetaSpec = BetaSpec(a=2, b=4, low=0.0, high=1.0)
    sigma: BetaSpec = BetaSpec(a=2, b=2, low=0.0, high=1.0)
    chi: BetaSpec = BetaSpec(a=2, b=3, low=0.0, high=1.0)
    theta: BetaSpec = BetaSpec(a=2, b=2, low=1.0, high=3.0)
    pi_: BetaSpec = Field(default=BetaSpec(a=2, b=2, low=1.0, high=3.0), alias="pi")
    k_star: BetaSpec = BetaSpec(a=2, b=3, low=1.0, high=10.0, round_to_int=True)

    model_config = {"populate_by_name": True}


class PopulationStability(str, Enum):
    """Draft Section 4.3/4.4 rows. Governs whether per-agent coefficient tuples (and,
    under FIXED, influencer designation/agenda) are reused across runs or freshly drawn."""

    FIXED = "fixed"
    SEMI_FIXED = "semi_fixed"
    RANDOM = "random"


class SeedingCondition(str, Enum):
    """Draft Section 4.4/4.6 columns."""

    FULLY_BALANCED = "fully_balanced"
    FIRST_HALF_BALANCED = "first_half_balanced"
    LAST_HALF_BALANCED = "last_half_balanced"
    FULLY_RANDOM = "fully_random"
    INFLUENCER = "influencer"


class RunConfig(BaseModel):
    """Full run-time parameter set for a single simulation run."""

    run_id: str
    domain: str
    seed: int

    population_stability: PopulationStability
    seeding_condition: SeedingCondition

    agent_coefficients: AgentCoefficientDistributions = AgentCoefficientDistributions()

    # Movement (draft 4.11). Not yet assigned values in the draft — routed through the
    # Section 4.10 expectation-vs-reality pilot pass; the draft's own proposed starting
    # ranges are epsilon_explore in [0.05, 0.15], tau_still in [0.02, 0.1]. No default
    # here: a run must state its value explicitly rather than silently inherit a guess.
    epsilon_explore: float = Field(ge=0.0, le=1.0)
    tau_still: float = Field(ge=0.0)

    # Message formulation (draft 4.12). Whether this is the same draw as epsilon_explore
    # (one "exploratory personality" trait) or independent is an explicitly open design
    # fork (draft 4.12 TODO), routed through the same Section 4.10 pass. `None` means
    # "tied to epsilon_explore" (the default reading); an explicit value makes it
    # independent for this run.
    epsilon_topic: float | None = Field(default=None, ge=0.0, le=1.0)

    # Influencer mechanism (draft 4.6). R's draft-specified range is 20-50; the specific
    # value is resolved via the Section 4.10 validation pass, not hardcoded here.
    influencer_reach: int = Field(ge=20, le=50)
    num_influencers: int = Field(default=5, gt=0)  # draft 4.6: "Exactly 5 agents per run"

    # Population / duration (draft 4.4: "300-500 agents, 1000 ticks").
    num_agents: int = Field(gt=0)
    num_ticks: int = Field(default=1000, gt=0)

    # Metrics (draft 4.7's time-to-stabilization definition).
    saturation_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    stabilization_window_ticks: int = Field(default=50, gt=0)
    stabilization_epsilon: float = Field(default=0.01, gt=0.0)

    # Engine-level tunable (PRD Section 4.2 step 7 / 6.2), not part of the formal model.
    checkpoint_interval_ticks: int = Field(default=50, gt=0)

    model_config = {"populate_by_name": True}

    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True)

    @classmethod
    def from_json(cls, raw: str | bytes) -> RunConfig:
        return cls.model_validate(json.loads(raw))

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)


def load_run_config(source: dict[str, Any] | str | bytes) -> RunConfig:
    """Parse a RunConfig from a dict (e.g. a Cloud SQL jsonb row) or raw JSON (e.g. a
    Redis string value)."""
    if isinstance(source, (str, bytes)):
        return RunConfig.from_json(source)
    return RunConfig.model_validate(source)
