"""Fallacy-based reaction extensions — FREE_WILL_draft.md Section 3.7.

Four rules, each grounded in a specific psychology/argumentation-theory finding (see the
draft for citations). Three are elementwise over whatever delta_beta the tick already
computed (negativity bias, doubling-down defiance — cheap, fully vectorized); the fourth
(ad hominem drift / halo-effect leak) is PRD 4.9's one deliberately non-vectorized
mechanism: a batched per-pair gather/scatter over `TrustStore.propositions_for_pair`,
looped over the (small) set of (receiver, publisher) pairs actually touched this tick —
not a per-agent loop over the whole population.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import TrustStore
from freewill.mechanisms.smoothstep import smoothstep


def apply_negativity_bias(delta_beta: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """delta_beta'(I) = theta*delta_beta(I) if delta_beta(I)<0 else delta_beta(I).
    theta=1 recovers the symmetric baseline (draft 3.7)."""
    out = delta_beta.copy()
    negative = delta_beta < 0
    out[negative] = theta[negative] * delta_beta[negative]
    return out


def apply_doubling_down_defiance(
    delta_beta_prime: np.ndarray,
    pi: np.ndarray,
    tau_p_given_i: np.ndarray,
    disagreement: np.ndarray,
    k_assertions: np.ndarray,
    k_star: np.ndarray,
) -> np.ndarray:
    """delta_beta''(I) = pi*delta_beta'(I) where tau(P|I)<0 AND disagreement AND
    k(I)>=k*, else delta_beta'(I) unchanged. Applied *after* negativity bias, on top of
    whatever delta_beta' already is (draft 3.7's stated composition order) — callers pass
    `delta_beta_prime` from `apply_negativity_bias`'s output, not the raw delta_beta."""
    out = delta_beta_prime.copy()
    triggers = (tau_p_given_i < 0) & disagreement & (k_assertions >= k_star)
    out[triggers] = pi[triggers] * delta_beta_prime[triggers]
    return out


def is_disagreement(message_nu: np.ndarray, receiver_belief: np.ndarray) -> np.ndarray:
    """A message "disagrees" with the receiver's standing belief when their signs
    differ. Not stated as an explicit equation in the draft; this is the direct reading
    of "an untrusted source... sends a disagreeing message" (Section 3.7) in terms of
    quantities the model already tracks (nu, beta), not an additional invented mechanism."""
    return np.sign(message_nu) != np.sign(receiver_belief)


def apply_ad_hominem_halo_leak(
    trust: TrustStore,
    chi: np.ndarray,
    smoothstep_degree: np.ndarray,
    receiver: np.ndarray,
    publisher: np.ndarray,
    prop_id: np.ndarray,
    delta_tau: np.ndarray,
) -> None:
    """For each (receiver, publisher, prop_id, delta_tau) trust-update event this tick,
    leak chi*delta_tau to every *other* proposition that (receiver, publisher) pair
    already holds a trust value for (draft 3.7). Mutates `trust` in place.

    This is the batched per-pair gather/scatter PRD Section 4.9 calls out as the one
    mechanism that doesn't reduce to a single global matmul: the outer loop below is over
    the tick's *touched pairs* (bounded by how many conversations happened this tick, not
    by population size), and every trust update within one pair's leak set is applied as
    one vectorized `TrustStore.set` call — never a per-agent Python loop.
    """
    for r, p, i, dt, ss_n in zip(receiver, publisher, prop_id, delta_tau, smoothstep_degree[receiver]):
        leak_targets = trust.propositions_for_pair(int(r), int(p)) - {int(i)}
        if not leak_targets:
            continue
        targets = np.array(sorted(leak_targets))
        chi_r = chi[r]
        prev = np.array([trust.get(int(t), np.array([r]), np.array([p]))[0] for t in targets])
        leaked = chi_r * dt
        new_vals = smoothstep(prev + leaked, ss_n)
        for t, v in zip(targets, new_vals):
            trust.set(int(t), np.array([r]), np.array([p]), np.array([v]))
