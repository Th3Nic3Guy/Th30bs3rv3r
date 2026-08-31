"""Reluctance — FREE_WILL_draft.md Section 3.3.

Covers everything Section 3.3 defines: the consequential mean belief rho, the rise
function zeta (reluctance itself, gamma), the companion decay function epsilon (used for
default trust initialization, and for self-discovery trust in orphan_revelation.py), and
the reluctance-damped committed belief update.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import DagAdjacency


def compute_rho(belief: np.ndarray, dag: DagAdjacency) -> np.ndarray:
    """rho(I_c|I) for every agent and every proposition I, in one matmul against the
    row-normalized consequent adjacency D (draft 3.3; PRD 4.9: "reduces to a single
    sparse matrix multiplication"). rho=0 for a leaf with no consequents falls out of D's
    all-zero row for that I, matching the draft's stated convention exactly."""
    return belief @ dag.consequent_normalized.T


def rise(x: np.ndarray, xi: np.ndarray) -> np.ndarray:
    """zeta(x, xi) = e^(x^2/xi). xi > 0 is enforced by RunConfig's BetaSpec bounds, so
    this never divides by zero for a well-formed run."""
    return np.exp(x**2 / xi)


def decay(x: np.ndarray, eta: np.ndarray) -> np.ndarray:
    """epsilon(x, eta) = e^(-x/(eta*100))."""
    return np.exp(-x / (eta * 100))


def compute_gamma(rho: np.ndarray, xi: np.ndarray) -> np.ndarray:
    """gamma(I) = zeta(rho(I_c|I), xi). `xi` is per-agent; broadcasts over the
    propositions axis. gamma >= 1 always (x^2 >= 0, xi > 0), equality exactly at rho=0 —
    reluctance only damps, never amplifies (draft 3.3)."""
    return rise(rho, xi[:, None])


def default_trust_init(x: np.ndarray, eta: np.ndarray) -> np.ndarray:
    """tau(P|I)|first_encounter = 0.5 * epsilon(x, eta), draft 3.3's reconstructed
    connecting equation. `x` is the count of other sources already encountered for the
    same proposition (per receiving agent); `eta` is that receiving agent's own trust
    decay coefficient."""
    return 0.5 * decay(x, eta)


def apply_reluctance_damped_update(
    beta_prev: np.ndarray, delta_beta: np.ndarray, gamma: np.ndarray
) -> np.ndarray:
    """beta(I)|t = beta(I)|t-1 + delta_beta(I)|t / gamma(I). Deliberately *not* passed
    through SmoothStep (draft 3.3: this asymmetry with the trust update is inherited
    directly from the source dissertation's Forward Flow derivation)."""
    return beta_prev + delta_beta / gamma
