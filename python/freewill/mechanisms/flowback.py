"""Flowback (Omega/Psi Flux) — FREE_WILL_draft.md Section 4.2.

Vectorized: a batched sparse operation over the tick's dirty set (PRD 4.2 step 4, 4.9).
"""

from __future__ import annotations

from scipy.sparse import csr_matrix


def apply_omega_flux(
    belief_matrix: csr_matrix,
    dag_antecedent: csr_matrix,  # A, PRD 4.1
    dirty_propositions: csr_matrix,
) -> csr_matrix:
    """Apply Section 4.2's Omega Flux flowback update over the tick's dirty set.

    TODO(draft 4.2): implement once FREE_WILL_draft.md Section 4.2's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.2 (Omega Flux)")


def apply_psi_flux(
    belief_matrix: csr_matrix,
    trust_tensor: object,
    dirty_propositions: csr_matrix,
) -> object:
    """Apply Section 4.2's Psi Flux flowback update over the tick's dirty set.

    TODO(draft 4.2): implement once FREE_WILL_draft.md Section 4.2's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.2 (Psi Flux)")
