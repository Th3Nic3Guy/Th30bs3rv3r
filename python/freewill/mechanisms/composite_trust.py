"""Composite trust derivation — FREE_WILL_draft.md Section 3.9.

Distinct from orphan/revelation (Section 3.8): this derives a *publisher's* trust value
on a composite from that same publisher's trust on the composite's two operands, computed
once when first needed and then stored as an ordinary, independently-evolving trust entry
(draft 3.9) — never recomputed via Fz again after that.

Batched over the whole population at once, not per (receiver, publisher) pair: "every
receiver with trust on both of I's operands but not on I itself" is a single elementwise
AND between the two operands' `TrustStore` boolean masks (PRD 4.9's vectorization
principle — this is a small sparse mask, not a scan).
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import PropositionSchema, TrustStore
from freewill.mechanisms.fuzzy_resolution import ExprType, resolve


def derive_missing_for_proposition(trust: TrustStore, schema: PropositionSchema, prop_id: int) -> None:
    """For composite `prop_id`, derive and store tau(P|I) = Fz(expr(I), tau(P|I_left),
    tau(P|I_right)) for every (receiver, publisher) pair that already has trust on the
    operand(s) but none on `prop_id` yet (draft 3.9's "only when P's trust is already
    known on both of I's operands"). No-op for axioms (no operands) and when nobody has
    trust on the relevant operand(s) yet. Mutates `trust` in place.

    NOT is unary (draft Table 1): its `operand_right` is `NO_OPERAND` by construction, so
    for a NOT composite this derives off `operand_left` alone — requiring the right
    operand's trust too, as a naive "both operands" reading would, means a NOT composite
    could never derive trust at all (see the identical fix in `orphan_revelation.
    find_revelation_candidates` for the same class of bug).
    """
    if schema.is_axiom[prop_id]:
        return

    left = int(schema.operand_left[prop_id])
    is_not = schema.expr_type[prop_id] == ExprType.NOT
    known_left = trust.known_matrix(left)
    if known_left is None:
        return

    if is_not:
        both_known = known_left.tocoo()
    else:
        right = int(schema.operand_right[prop_id])
        known_right = trust.known_matrix(right)
        if known_right is None:
            return
        both_known = known_left.multiply(known_right).tocoo()
    if both_known.nnz == 0:
        return
    receivers, publishers = both_known.row, both_known.col

    already = trust.has_entry(prop_id, receivers, publishers)
    if already.all():
        return
    receivers = receivers[~already]
    publishers = publishers[~already]

    tau_left = trust.get(left, receivers, publishers)
    # tau_right is unused by resolve() for NOT (fuzzy_resolution.py) -- pass zeros rather
    # than reading a nonexistent "right" proposition's trust.
    tau_right = np.zeros(len(receivers)) if is_not else trust.get(right, receivers, publishers)
    expr_type = np.full(len(receivers), schema.expr_type[prop_id])
    values = resolve(expr_type, tau_left, tau_right)
    trust.set(prop_id, receivers, publishers, values)
