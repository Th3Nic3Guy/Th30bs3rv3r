"""Fuzzy resolution — FREE_WILL_draft.md Section 3.1, Table 1.

| Boolean       | Fuzzy         |
|---------------|---------------|
| AND(x,y)      | MIN(x,y)      |
| OR(x,y)       | MAX(x,y)      |
| NOT(x)        | -x            |
| IMPLIES(x,y)  | MAX(-x,y)     |

This is the `Fz` operator referenced throughout the draft: applied to belief for
revelation (Section 3.8) and to trust for composite derivation (Section 3.9). Vectorized:
`resolve` takes a batch of nodes that may each carry a *different* operator (the tick's
dirty set can touch AND/OR/NOT/IMPLIES composites in the same call) and resolves all of
them in one pass via boolean masks — no Python-level loop over nodes.
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np


class ExprType(IntEnum):
    """A proposition's node type in the DAG (draft Section 3.1). AXIOM has no operands —
    `resolve` is never called for it; axioms are leaves whose belief is set by messages
    (draft Section 3.8), not derived. NOT is unary; `right` is ignored for NOT nodes."""

    AXIOM = 0
    AND = 1
    OR = 2
    NOT = 3
    IMPLIES = 4


def resolve(expr_type: np.ndarray, left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Batched fuzzy resolution over Table 1.

    `expr_type`, `left`, `right` are same-shaped arrays (one row per node being
    resolved this call); `right` is ignored wherever `expr_type == ExprType.NOT`.
    Raises if any node's `expr_type` is `AXIOM` — axioms are never resolved via Fz.
    """
    expr_type = np.asarray(expr_type)
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if np.any(expr_type == ExprType.AXIOM):
        raise ValueError("resolve() called on an AXIOM node — axioms have no operands to resolve")

    out = np.empty_like(left, dtype=float)
    is_and = expr_type == ExprType.AND
    is_or = expr_type == ExprType.OR
    is_not = expr_type == ExprType.NOT
    is_implies = expr_type == ExprType.IMPLIES

    out[is_and] = np.minimum(left[is_and], right[is_and])
    out[is_or] = np.maximum(left[is_or], right[is_or])
    out[is_not] = -left[is_not]
    out[is_implies] = np.maximum(-left[is_implies], right[is_implies])
    return out
