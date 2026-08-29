"""Reluctance — FREE_WILL_draft.md Section 3.3.

Vectorized, applied against the DAG consequent adjacency D (PRD 4.1).
"""

from __future__ import annotations

from scipy.sparse import csr_matrix


def apply_reluctance(
    belief_matrix: csr_matrix,
    dag_consequent: csr_matrix,  # D, PRD 4.1
    coefficient_table: object,  # agents x 9 (lambda, mu, eta, xi, sigma, chi, theta, pi, k*), PRD 3.6
) -> csr_matrix:
    """Apply Section 3.3's reluctance mechanism to the belief matrix.

    TODO(draft 3.3): implement once FREE_WILL_draft.md Section 3.3's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.3")
