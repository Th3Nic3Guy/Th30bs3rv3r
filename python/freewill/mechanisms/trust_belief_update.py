"""Trust and belief update (Alpha Flux / Forward Flow) — FREE_WILL_draft.md Section 3.2.

`phi(I|P)` (the mean of a publisher's own stated confidence on I, across all its
messages, to anyone) is tracked per publisher/proposition, independent of any specific
receiver — see `update_phi`. `alpha(I)` and the trust/belief deltas are batched over
whatever the tick's dirty set is: `compute_alpha` over a proposition's whole population at
once (a single matvec against that proposition's trust matrix, PRD 4.9); the Alpha Flux
trust delta over the specific (receiver, publisher, proposition) message events that
actually occurred this tick.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import PropositionSchema, SimulationState, TrustStore
from freewill.mechanisms.composite_trust import derive_missing_for_proposition


def update_phi(
    phi: np.ndarray, phi_message_count: np.ndarray, publisher: np.ndarray, prop: np.ndarray, nu: np.ndarray
) -> None:
    """Running-mean update of phi(I|P), in place, for a batch of outgoing messages
    (publisher, prop, nu). draft 3.2: "the mean of nu across all of P's messages on I"."""
    counts = phi_message_count[publisher, prop] + 1
    phi[publisher, prop] += (nu - phi[publisher, prop]) / counts
    phi_message_count[publisher, prop] = counts


def compute_alpha(
    trust: TrustStore, schema: PropositionSchema, phi: np.ndarray, prop_ids: np.ndarray
) -> dict[int, np.ndarray]:
    """alpha(I)|t = (2/|P|) * sum_P phi(I|P)*tau(P|I), for every proposition in
    `prop_ids`, over the whole population at once: `T[I] @ phi[:,I]` is exactly this sum
    (row = receiver, column = publisher), divided by each receiver's known-publisher
    count. Returns {prop_id: alpha_vector (agents,)}; a receiver with no known publishers
    on I (known_count=0) reads alpha=0 (an empty consensus contributes nothing, rather
    than being undefined).

    For each composite proposition, composite trust derivation (draft 3.9) runs first so
    a publisher with no *direct* trust entry on I, but trust on both of I's operands,
    still contributes to alpha(I) — matching the draft's fallback-derivation semantics
    rather than silently treating that publisher as unknown."""
    num_agents = trust.num_agents
    all_receivers = np.arange(num_agents)
    out: dict[int, np.ndarray] = {}
    for prop_id in prop_ids:
        derive_missing_for_proposition(trust, schema, int(prop_id))
        weighted_sum = trust.matvec(int(prop_id), phi[:, prop_id])
        known = trust.known_count(int(prop_id), all_receivers)
        known_safe = np.where(known == 0, 1, known)
        alpha = 2.0 * weighted_sum / known_safe
        alpha[known == 0] = 0.0
        out[int(prop_id)] = alpha
    return out


def alpha_flux_delta_tau(
    mu: np.ndarray, phi_prev: np.ndarray, beta_receiver: np.ndarray
) -> np.ndarray:
    """delta_tau(P|I)|t = mu * (phi(I|P)|t-1 - beta(I)|t), batched over a set of message
    events. `mu` is the *receiving* agent's own coefficient; `phi_prev` and
    `beta_receiver` are the already-gathered phi(I|P) and beta_receiver(I) values for
    each event."""
    return mu * (phi_prev - beta_receiver)


def forward_flow_delta_beta(
    alpha: np.ndarray, omega: np.ndarray, lam: np.ndarray, beta_prev: np.ndarray
) -> np.ndarray:
    """beta'(I)|t = lambda*alpha(I)|t + (1-lambda)*omega(I)|t; delta_beta = beta' -
    beta_prev. For axioms/orphans (omega(I):=beta(I) by convention, draft 3.2/3.8), this
    collapses algebraically to delta_beta(I) = lambda*(alpha(I) - beta(I)) — callers pass
    `omega` from `SimulationState.get_omega`, which already applies that convention, so
    this function needs no axiom/orphan special case itself."""
    beta_new = lam * alpha + (1 - lam) * omega
    return beta_new - beta_prev


def apply_dirty_set_update(state: SimulationState, agent_idx: np.ndarray, prop_idx: np.ndarray) -> np.ndarray:
    """Convenience wrapper: compute Forward Flow's delta_beta for a batch of (agent,
    proposition) pairs already known to be "dirty" this tick, using each proposition's
    already-computed alpha (via `compute_alpha`) and the state's own omega convention.
    Returns delta_beta for the batch; callers still apply Section 3.7's fallacy
    extensions and Section 3.3's reluctance damping before committing it to `belief`.
    """
    unique_props = np.unique(prop_idx)
    alpha_by_prop = compute_alpha(state.trust, state.schema, state.phi, unique_props)
    alpha = np.array([alpha_by_prop[int(p)][a] for a, p in zip(agent_idx, prop_idx)])
    omega = state.get_omega(agent_idx, prop_idx)
    lam = state.coefficients["lambda"].to_numpy()[agent_idx]
    beta_prev = state.belief[agent_idx, prop_idx]
    return forward_flow_delta_beta(alpha, omega, lam, beta_prev)
