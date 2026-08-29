"""Trigger discovery / orphan revelation — FREE_WILL_draft.md Section 3.8.

Vectorized via sparse boolean masks over occupied/seeded cells (PRD 4.2 step 3, 4.9).
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix


def trigger_discovery(
    grid_positions: np.ndarray,  # agents x 2, PRD 4.1
    seeded_cells: np.ndarray,
    belief_matrix: csr_matrix,
) -> csr_matrix:
    """Apply Section 3.8's discovery/revelation trigger for agents landing on seeded or
    orphan-revealing cells this tick.

    TODO(draft 3.8): implement once FREE_WILL_draft.md Section 3.8's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.8")
