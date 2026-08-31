"""Influencer role — FREE_WILL_draft.md Section 4.6.

Popularity (reach) and agenda-scripting are bundled into a single role for exactly 5
agents per run (`RunConfig.num_influencers`, draft default). The reach *formula* itself
(`reach(A,t) = max(baseline(A), K(A,t))`) is stated under Section 4.11's grid mechanics,
not here — see `movement.compute_reach`; this module owns influencer identity, agenda,
and picking who fills an under-crowded influencer's reach up to R.
"""

from __future__ import annotations

import numpy as np

NO_AGENDA = -1


def select_influencers(rng: np.random.Generator, num_agents: int, num_influencers: int) -> np.ndarray:
    """Uniformly select `num_influencers` distinct agent indices (draft 4.6: "Exactly 5
    agents per run are designated influencers"). Under the FIXED population-stability
    condition, callers reuse a *previous* run's selection instead of calling this again
    (draft 4.4: "the influencer designation and agenda... persist across runs... under
    Fixed"); this function is for SEMI_FIXED/RANDOM, where it is redrawn every run."""
    return rng.choice(num_agents, size=num_influencers, replace=False)


def assign_agendas(
    rng: np.random.Generator, influencer_idx: np.ndarray, candidate_propositions: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Assign each influencer one agenda proposition I_a and a fixed outgoing confidence
    nu_a (draft 4.6). "Mixed-bag composition": influencers are drawn independently, so a
    run may contain influencers pushing different, competing agendas — this function's
    per-influencer independent draw is exactly that; nothing here forces agreement."""
    agenda_prop = rng.choice(candidate_propositions, size=len(influencer_idx), replace=True)
    agenda_confidence = rng.uniform(-0.5, 0.5, size=len(influencer_idx))
    return agenda_prop, agenda_confidence


def agenda_override(
    is_influencer: np.ndarray, agenda_proposition: np.ndarray, agenda_confidence: np.ndarray, speaker: int
) -> tuple[int, float] | None:
    """Highest-priority branch of Section 4.12's message-formulation policy: if `speaker`
    is an influencer, it unconditionally raises its agenda proposition at its scripted
    confidence, regardless of audience or own belief (draft 4.6, restated as 4.12's top
    branch). Returns None if `speaker` is not an influencer, so callers fall through to
    the ordinary policy in message_formulation.py."""
    if not is_influencer[speaker]:
        return None
    return int(agenda_proposition[speaker]), float(agenda_confidence[speaker])


def top_up_reach(
    rng: np.random.Generator,
    already_present: np.ndarray,
    target_reach: int,
    num_agents: int,
    excluding: int,
) -> np.ndarray:
    """When an influencer's cell is under-crowded (draft 4.11: K(A,t) < baseline(A)=R),
    its actual reach is still R — this picks the additional (R - |already_present|)
    recipients. **Implementation note**: the draft specifies *that* an influencer reaches
    R distinct agents per tick (Section 4.6) but not *how* the top-up beyond whoever is
    physically co-located is chosen. This samples uniformly at random from agents not
    already reached, as the most neutral reading available absent a stated selection
    rule — flagged here rather than silently assumed, per PRD Section 2.3."""
    already_present = np.asarray(already_present, dtype=int)
    deficit = target_reach - len(already_present)
    if deficit <= 0:
        return already_present
    excluded = set(already_present.tolist()) | {excluding}
    pool = np.array([a for a in range(num_agents) if a not in excluded])
    if len(pool) == 0:
        return already_present
    extra = rng.choice(pool, size=min(deficit, len(pool)), replace=False)
    return np.concatenate([already_present, extra])
