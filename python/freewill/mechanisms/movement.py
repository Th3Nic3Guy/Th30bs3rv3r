"""Movement, grid mechanics, and conversation reach — FREE_WILL_draft.md Section 4.11.

The candidate-move computation (Personal Affinity, stay threshold, epsilon-greedy
exploration/exploitation) is vectorized over the whole population; collision resolution
operates only on the (typically small) set of contested cells each tick (PRD 4.2 step 2).
`compute_reach` (draft 4.11's landing-consequences formula) lives here rather than in
influencer.py since it is stated as part of this section's grid mechanics, not Section
4.6's influencer definition — see influencer.py's docstring.
"""

from __future__ import annotations

import numpy as np

# 8-direction full Moore neighborhood (draft 4.11).
DIRECTIONS = np.array(
    [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)], dtype=float
)
_DIRECTION_NORMS = DIRECTIONS / np.linalg.norm(DIRECTIONS, axis=1, keepdims=True)


def mean_trust(trust_values: np.ndarray) -> np.ndarray:
    """tau_bar(A,P) = mean trust across whichever leaf/axiomatic propositions A holds
    trust data on regarding P (draft 4.11). `trust_values` is already the gathered set
    of tau_A(P|I) values for one (A,P) pair across its shared leaf propositions; callers
    handle the empty case (N_A undefined) separately, per `compute_personal_affinity`."""
    return float(np.mean(trust_values)) if len(trust_values) else 0.0


def compute_personal_affinity(
    agent_pos: np.ndarray, neighbor_pos: np.ndarray, mean_trust_per_neighbor: np.ndarray
) -> np.ndarray:
    """PA(A) = sum_{P in N_A} tau_bar(A,P) * unit(pos(P) - pos(A)) (draft 4.11). A
    trusted P pulls PA(A) toward it; a distrusted P repels it — both fall directly out of
    tau_bar being signed, no separate repulsion rule. If `neighbor_pos` is empty (N_A is
    empty — no interactions yet), returns the zero vector; callers must treat that case
    as "PA(A) undefined" (cold-start uniform random walk, draft 4.11), not as "affinity is
    genuinely zero" — those are different and this function alone cannot distinguish
    them, since a population of exactly-cancelling trusted/distrusted neighbors is a
    legitimate zero PA(A) too."""
    if len(neighbor_pos) == 0:
        return np.zeros(2)
    offsets = neighbor_pos - agent_pos
    norms = np.linalg.norm(offsets, axis=1, keepdims=True)
    norms_safe = np.where(norms == 0, 1.0, norms)
    unit_offsets = offsets / norms_safe
    return (mean_trust_per_neighbor[:, None] * unit_offsets).sum(axis=0)


def choose_direction(
    personal_affinity: np.ndarray, epsilon_explore: float, rng: np.random.Generator
) -> np.ndarray:
    """d_hat(A): uniform random direction w.p. epsilon_explore (explore), else
    argmax_d PA(A).d (exploit) — draft 4.11's epsilon-greedy rule."""
    if rng.random() < epsilon_explore:
        return DIRECTIONS[rng.integers(len(DIRECTIONS))]
    scores = _DIRECTION_NORMS @ personal_affinity
    return DIRECTIONS[int(np.argmax(scores))]


def should_stay(personal_affinity: np.ndarray, num_neighbors: int, tau_still: float) -> bool:
    """stay if |PA_bar(A)| < tau_still, where PA_bar(A) = PA(A)/|N_A| (draft 4.11).
    Checked *before* the explore/exploit rule; if N_A is empty this is not applicable —
    callers route the cold-start case (uniform random walk) separately, matching the
    draft's explicit statement that PA(A) is undefined (not zero) when N_A is empty."""
    if num_neighbors == 0:
        return False
    normalized = personal_affinity / num_neighbors
    return bool(np.linalg.norm(normalized) < tau_still)


def resolve_collisions(
    candidate_cells: np.ndarray, move_scores: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Given every agent's candidate destination cell and its PA(A).d_hat score for that
    move, resolve contested cells by priority to the higher score; losers stay at their
    current cell rather than falling back to a secondary choice (draft 4.11). Exact ties
    broken by random draw. Returns a boolean "move approved" mask, same shape as
    `candidate_cells`'s first axis."""
    approved = np.ones(len(candidate_cells), dtype=bool)
    # Group agents by destination cell.
    _, inverse, counts = np.unique(candidate_cells, axis=0, return_inverse=True, return_counts=True)
    for cell_idx in np.nonzero(counts > 1)[0]:
        contestants = np.nonzero(inverse == cell_idx)[0]
        scores = move_scores[contestants]
        best = np.max(scores)
        winners = contestants[scores == best]
        winner = winners[0] if len(winners) == 1 else winners[rng.integers(len(winners))]
        approved[contestants] = False
        approved[winner] = True
    return approved


def compute_reach(baseline: np.ndarray, crowd_size: np.ndarray) -> np.ndarray:
    """reach(A,t) = max(baseline(A), K(A,t)) — draft 4.11's landing-consequences formula.
    `baseline` is 1 for ordinary agents, R for influencers (draft 4.6); `crowd_size` is
    the number of other agents present after A moves. `max`, not summation, so a crowded
    influencer does not receive a double boost."""
    return np.maximum(baseline, crowd_size)
