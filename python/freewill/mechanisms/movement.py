"""Movement — FREE_WILL_draft.md Section 4.11.

Per PRD Section 4.2 step 2: the candidate-move computation (Personal Affinity, stay
threshold, epsilon-greedy exploration/exploitation) is vectorized; collision resolution
among agents contesting the same cell is the one sub-step most naturally iterative
(sequential priority resolution) but operates only on the (typically small) set of
contested cells each tick, not the whole population.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix


def compute_personal_affinity(
    grid_positions: np.ndarray,  # PRD 4.1
    trust_tensor: object,
    belief_matrix: csr_matrix,
) -> np.ndarray:
    """Compute Section 4.11's Personal Affinity PA(A) for every agent — vectorized.

    TODO(draft 4.11): implement once FREE_WILL_draft.md Section 4.11's formula is
    available in this repo. Per PRD Section 2.3, no formula is invented here ahead of the
    draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.11 (Personal Affinity)")


def compute_candidate_moves(
    grid_positions: np.ndarray,
    personal_affinity: np.ndarray,
    tau_still: float,  # PRD Section 5 / 11 run-time parameter
    epsilon_explore: float,  # PRD Section 5 / 11 run-time parameter
    rng: np.random.Generator,
) -> np.ndarray:
    """Compute each agent's candidate next-cell move: stay-threshold check followed by
    epsilon-greedy exploration/exploitation — vectorized over the whole population.

    TODO(draft 4.11): implement once FREE_WILL_draft.md Section 4.11's formula is
    available in this repo. Per PRD Section 2.3, no formula is invented here ahead of the
    draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.11 (candidate moves)")


def resolve_collisions(candidate_moves: np.ndarray, priority: np.ndarray) -> np.ndarray:
    """Resolve agents contesting the same target cell by sequential priority.

    Deliberately iterative over the (small) set of contested cells (PRD Section 4.2 step
    2) — the candidate-move computation feeding into this stays vectorized.

    TODO(draft 4.11): implement once FREE_WILL_draft.md Section 4.11's collision-resolution
    rule is available in this repo. Per PRD Section 2.3, no formula is invented here ahead
    of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.11 (collision resolution)")
