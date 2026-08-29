"""Iterative fallback / validation harness (PRD Section 4.4).

A deliberately slow, per-agent-loop reference implementation of the *entire* tick cycle,
run against small populations (10-20 agents) and cross-checked for exact numerical
agreement with the vectorized engine (freewill.engine) on identical seeds.

This is a correctness oracle (PRD Section 2.1's "iterative as secondary" mandate), not a
production fallback. CI should run `run_iterative_reference` against
`freewill.engine.run_tick` on every change to a mechanism module (PRD Section 4.4).

Every per-agent step here should mirror one mechanism module's formula exactly, just
computed one agent at a time instead of as a batched tensor op — so this file stays a
stub for the same reason the mechanism modules do (PRD Section 2.3): the formulas
themselves are not yet in this repo.
"""

from __future__ import annotations

from freewill.config.params import RunConfig
from freewill.engine.state import SimulationState


def run_iterative_reference(state: SimulationState, config: RunConfig, num_ticks: int) -> SimulationState:
    """Run `num_ticks` ticks of the naive per-agent-loop reference implementation.

    Intended only for small populations (10-20 agents, PRD Section 4.4) during
    development/CI, never for production runs (PRD Section 2.1).

    TODO: implement per-agent versions of each mechanism module's formula once
    FREE_WILL_draft.md's formulas are available in this repo (PRD Section 2.3).
    """
    raise NotImplementedError(
        "iterative reference oracle pending FREE_WILL_draft.md mechanism formulas"
    )
