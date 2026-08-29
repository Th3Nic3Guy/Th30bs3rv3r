"""Smoothstep transfer function — FREE_WILL_draft.md Section 3.5.

Vectorized: a pure elementwise numpy ufunc-style transform, reused by several other
mechanism modules rather than duplicated.
"""

from __future__ import annotations

import numpy as np


def smoothstep(x: np.ndarray, edge0: float, edge1: float) -> np.ndarray:
    """Apply Section 3.5's smoothstep transfer function elementwise.

    TODO(draft 3.5): implement once FREE_WILL_draft.md Section 3.5's formula is available
    in this repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.5")
