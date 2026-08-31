"""SmoothStep clamping function — FREE_WILL_draft.md Section 3.5.

$$S_n(x) = \\begin{cases} -0.5 & x \\le -0.5 \\\\
(x+0.5)^{n+1}\\sum_{k=0}^{n}\\binom{n+k}{k}\\binom{2n+1}{n-k}(-(x+0.5))^k - 0.5 & -0.5 \\le x \\le 0.5 \\\\
0.5 & x \\ge 0.5 \\end{cases}$$

This is Ken Perlin's generalized smoothstep family, shifted from its usual [0,1] domain to
[-0.5, 0.5] to match the model's native trust/belief range. The polynomial degree $n$ is
per-agent ($n = \\text{round}(9\\sigma)$, draft Section 3.5), so a batch being clamped in
the same call can span multiple distinct $n$ values — since $n \\in \\{0, ..., 9\\}$ (only
10 possible integers), this is handled by grouping the batch by $n$ rather than resolving
per element, keeping the whole operation vectorized (10 boolean-masked sub-calls, not one
per array element).
"""

from __future__ import annotations

from math import comb

import numpy as np


def _poly01(u: np.ndarray, n: int) -> np.ndarray:
    """The base generalized-smoothstep polynomial on u in [0,1], satisfying poly(0)=0,
    poly(1)=1. draft Section 3.5's sum, with u substituted for (x+0.5)."""
    total = np.zeros_like(u)
    for k in range(n + 1):
        coeff = comb(n + k, k) * comb(2 * n + 1, n - k)
        total += coeff * (-u) ** k
    return u ** (n + 1) * total


def smoothstep(x: np.ndarray, n: np.ndarray | int) -> np.ndarray:
    """Apply $S_n(x)$ elementwise. `n` may be a scalar (applied to every element) or an
    array broadcastable to `x`'s shape (per-element degree, e.g. one degree per agent)."""
    x = np.asarray(x, dtype=float)
    n_arr = np.broadcast_to(np.asarray(n), x.shape)

    out = np.clip(x, -0.5, 0.5)
    mid = (x > -0.5) & (x < 0.5)
    if np.any(mid):
        u = x[mid] + 0.5
        n_mid = n_arr[mid]
        result = np.empty_like(u)
        for nv in np.unique(n_mid):
            sel = n_mid == nv
            result[sel] = _poly01(u[sel], int(nv)) - 0.5
        out[mid] = result
    return out


def degree_from_sigma(sigma: np.ndarray) -> np.ndarray:
    """n = round(9*sigma), draft Section 3.5 — maps sigma in [0,1] to the SmoothStep
    polynomial degree range [0,9] illustrated in the source dissertation's Figure 7."""
    return np.clip(np.round(9 * np.asarray(sigma)).astype(int), 0, 9)
