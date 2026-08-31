"""Composite trust derivation — FREE_WILL_draft.md Section 3.9.

Distinct from orphan/revelation (Section 3.8): this derives a *publisher's* trust value
on a composite from that same publisher's trust on the composite's two operands, computed
once when first needed and then stored as an ordinary, independently-evolving trust entry
(draft 3.9) — never recomputed via Fz again after that.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import PropositionSchema, TrustStore
from freewill.mechanisms.fuzzy_resolution import resolve


def find_derivable(
    schema: PropositionSchema, trust: TrustStore, receiver: int, publisher: int, candidate_props: np.ndarray
) -> np.ndarray:
    """Which of `candidate_props` (composites `receiver` needs P's trust on but has no
    direct entry for) already have P's trust known on *both* operands, and so can be
    derived right now (draft 3.9: "only when P's trust is already known on both of I's
    operands")."""
    left = schema.operand_left[candidate_props]
    right = schema.operand_right[candidate_props]
    r = np.array([receiver])
    p = np.array([publisher])
    derivable = np.array(
        [
            bool(trust.has_entry(int(le), r, p)[0]) and bool(trust.has_entry(int(ri), r, p)[0])
            for le, ri in zip(left, right)
        ]
    )
    return candidate_props[derivable]


def derive_and_store(
    schema: PropositionSchema, trust: TrustStore, receiver: int, publisher: int, prop_id: int
) -> float:
    """tau(P|I) = Fz(expr(I), tau(P|I_left), tau(P|I_right)); stores the result as an
    ordinary trust entry (so it evolves via Alpha Flux from here on, draft 3.9) and
    returns it."""
    left = schema.operand_left[prop_id]
    right = schema.operand_right[prop_id]
    tau_left = trust.get(int(left), np.array([receiver]), np.array([publisher]))[0]
    tau_right = trust.get(int(right), np.array([receiver]), np.array([publisher]))[0]
    value = float(
        resolve(
            np.array([schema.expr_type[prop_id]]),
            np.array([tau_left]),
            np.array([tau_right]),
        )[0]
    )
    trust.set(prop_id, np.array([receiver]), np.array([publisher]), np.array([value]))
    return value
