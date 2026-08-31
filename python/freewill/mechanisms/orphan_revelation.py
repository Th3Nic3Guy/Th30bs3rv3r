"""New information: arrival, orphans, revelation, self-discovery — FREE_WILL_draft.md
Section 3.8.

Vectorized via boolean masks over the belief/known/orphan arrays (PRD 4.2 step 3, 4.9):
the orphan-trigger check is a single elementwise AND across those arrays, and the
satisfaction-check update is elementwise arithmetic once triggered rows are gathered —
this is exactly what the draft's binarization requirement (every composite has exactly
two operands) exists to make possible.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import NO_OPERAND, PropositionSchema
from freewill.mechanisms.fuzzy_resolution import ExprType, resolve
from freewill.mechanisms.reluctance import decay


def arrival_belief(nu: np.ndarray, tau_p_given_i: np.ndarray) -> np.ndarray:
    """beta(I)|arrival = nu * tau(P|I) — no prior belief to blend against (draft 3.8)."""
    return nu * tau_p_given_i


def find_revelation_candidates(
    schema: PropositionSchema, known: np.ndarray, orphan: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Every (agent, proposition) pair currently orphaned whose operand(s) are now known
    to that agent — the single elementwise boolean AND across sparse-ish arrays PRD 4.9
    describes. Returns (agent_idx, prop_idx) arrays for the triggered batch.

    NOT is unary (draft Table 1): its `operand_right` is `NO_OPERAND` by construction
    (`PropositionSchema`'s own docstring), so revelation for a NOT node must trigger off
    `operand_left` alone — requiring `right != NO_OPERAND` too, as a naive "both operands
    known" check would, means a NOT composite could never be revealed at all.
    """
    left = schema.operand_left
    right = schema.operand_right
    is_not = schema.expr_type == ExprType.NOT

    has_operands = (left != NO_OPERAND) & (is_not | (right != NO_OPERAND))
    # known[:, left] / known[:, right] gather each proposition's operand-known status per
    # agent in one indexed read — shape (agents, propositions). For NOT columns, right is
    # NO_OPERAND (an out-of-range index that numpy silently wraps to the last column), so
    # known[:, right] there is meaningless -- ORing with is_not discards it rather than
    # letting it accidentally gate revelation on an unrelated proposition's known status.
    operands_known = known[:, left] & (is_not[None, :] | known[:, right])
    triggered = orphan & operands_known & has_operands[None, :]
    return np.nonzero(triggered)


def compute_omega_struct(
    schema: PropositionSchema, belief: np.ndarray, agent_idx: np.ndarray, prop_idx: np.ndarray
) -> np.ndarray:
    """omega_struct(I) = Fz(expr(I), beta(I_left), beta(I_right)) for a batch of
    (agent, proposition) pairs (draft 3.8)."""
    left = schema.operand_left[prop_idx]
    right = schema.operand_right[prop_idx]
    beta_left = belief[agent_idx, left]
    # For NOT rows, `right` is NO_OPERAND (-1); numpy silently reads the last column
    # rather than raising, but `resolve` ignores beta_right wherever expr_type is NOT
    # (fuzzy_resolution.py), so that harmlessly-wrong read never reaches the result.
    beta_right = belief[agent_idx, right]
    return resolve(schema.expr_type[prop_idx], beta_left, beta_right)


def apply_revelation(
    belief: np.ndarray,
    orphan: np.ndarray,
    schema: PropositionSchema,
    agent_idx: np.ndarray,
    prop_idx: np.ndarray,
    gamma: np.ndarray,
) -> None:
    """Apply the satisfaction-check update in place for a triggered (agent, prop) batch:
    gamma as a *multiplier* when structural derivation confirms the standing belief's
    sign, as a *divisor* when it contradicts it (draft 3.8's bidirectional use of gamma,
    distinct from Section 3.3's damping-only role). Promotes each pair from orphan to
    fully structured on completion.
    """
    omega_struct = compute_omega_struct(schema, belief, agent_idx, prop_idx)
    beta_current = belief[agent_idx, prop_idx]
    satisfies = np.sign(omega_struct) == np.sign(beta_current)
    delta_reveal = omega_struct - beta_current

    updated = beta_current.copy()
    updated[satisfies] += gamma[satisfies] * delta_reveal[satisfies]
    updated[~satisfies] += delta_reveal[~satisfies] / gamma[~satisfies]

    belief[agent_idx, prop_idx] = updated
    orphan[agent_idx, prop_idx] = False


def self_discovery_trust_init(rng: np.random.Generator, n: int) -> np.ndarray:
    """tau(SELF|I)|discovery ~ Beta(a=2, b=2) scaled to [.25, .5] (draft 3.8)."""
    raw = rng.beta(2, 2, size=n)
    return 0.25 + raw * 0.25


def self_discovery_delta_tau(mu: np.ndarray, nu_discovery: np.ndarray, beta_now: np.ndarray) -> np.ndarray:
    """delta_tau(SELF|I)|t = mu*(nu_discovery - beta(I)|t). `nu_discovery` is
    phi(I|SELF), permanently fixed at the original observed confidence since SELF sends
    no further messages after discovery (draft 3.8) — callers supply it from
    `SimulationState.phi[agent, prop]`, which `update_phi` must never be called on again
    for a SELF (agent, agent, prop) triple after the initial observation."""
    return mu * (nu_discovery - beta_now)


def default_trust_init_x(trust_known_count: np.ndarray) -> np.ndarray:
    """x in the default-trust-initialization equation (draft 3.3, reused here for a
    first-time encounter that isn't self-discovery): count of *other* sources the agent
    already has trust data for, on the same proposition — exactly
    `TrustStore.known_count` evaluated *before* the new entry is set."""
    return trust_known_count


__all__ = [
    "apply_revelation",
    "arrival_belief",
    "compute_omega_struct",
    "decay",  # re-exported for convenience; canonical home is reluctance.py (draft 3.3)
    "default_trust_init_x",
    "find_revelation_candidates",
    "self_discovery_delta_tau",
    "self_discovery_trust_init",
]
