"""Trust and belief update (Alpha Flux / Forward Flow) — FREE_WILL_draft.md Section 3.2.

Vectorized: batched sparse operations over the tick's dirty set (propositions/agents
actually touched this tick), per PRD Section 4.9 / 4.2 step 4.
"""

from __future__ import annotations

from scipy.sparse import csr_matrix


def apply_alpha_flux(
    belief_matrix: csr_matrix,
    trust_tensor: object,  # pydata/sparse array or per-proposition dict fallback, PRD 4.1
    dirty_propositions: csr_matrix,
) -> csr_matrix:
    """Apply Section 3.2's Alpha Flux belief update over the tick's dirty set.

    TODO(draft 3.2): implement once FREE_WILL_draft.md Section 3.2's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.2")


def apply_forward_flow(
    belief_matrix: csr_matrix,
    trust_tensor: object,
    dirty_propositions: csr_matrix,
) -> object:
    """Apply Section 3.2's Forward Flow trust update over the tick's dirty set.

    TODO(draft 3.2): implement once FREE_WILL_draft.md Section 3.2's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.2")
