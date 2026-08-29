"""Influencer conversation reach — FREE_WILL_draft.md Section 4.6.

Vectorized: builds the tick's communication matrix C (agents x agents, PRD 4.1) via
sparse boolean masks, then feeds it into the belief/trust update batch (PRD 4.2 step 3-4).
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix


def build_communication_matrix(
    grid_positions: np.ndarray,  # agents x 2, PRD 4.1
    influencer_reach: int,  # R, draft range 20-50, PRD Section 5 / 11 run-time parameter
) -> csr_matrix:
    """Build this tick's communication matrix C, including Section 4.6's influencer reach
    extension to ordinary adjacency-based conversation.

    TODO(draft 4.6): implement once FREE_WILL_draft.md Section 4.6's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    `influencer_reach` must come from the run's RunConfig (freewill.config.params) — never
    a hardcoded value, per PRD Section 11.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.6")
