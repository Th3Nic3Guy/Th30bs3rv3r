"""Flowback (Omega Flux / Psi Flux) — FREE_WILL_draft.md Section 4.2.

On receipt of a message targeting I, updates propagate to I's antecedents (Omega Flux)
and, from each of those antecedents, onward to *that antecedent's own* consequents (Psi
Flux) — which includes I itself plus any siblings that share the same antecedent. Reading
this: the draft's Psi Flux equation reuses the symbol "I" generically for "whichever
proposition's omega just changed" (i.e. each antecedent I_a from the Omega Flux step, not
literally the original message target) — see docs/adr/0002-engine-state-representation.md
for why this reading was adopted; it is what makes the mechanism a genuine multi-hop
*flowback* rather than a single point update, and is the only reading under which the
consequent-side formula's `Δω(I)` is a quantity anything upstream of it actually computed.

Both reduce to a single sparse matmul against the precomputed DAG adjacency followed by
elementwise arithmetic, for the whole population at once (PRD 4.9).
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import DagAdjacency
from freewill.mechanisms.smoothstep import smoothstep


def omega_flux(
    omega_antecedent_prev: np.ndarray, beta_target: np.ndarray, mu: np.ndarray, smoothstep_degree: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """For every antecedent I_a of the message's target I:
    delta_omega(I_a) = mu*(omega(I_a)|t-1 - beta(I)|t); omega(I_a)|t = S_n(omega(I_a)|t-1
    + delta_omega(I_a)). Note the asymmetry with Alpha Flux (Section 3.2): the comparison
    term is the *target's* belief, not the antecedent's own (draft 4.2).

    `omega_antecedent_prev` and `beta_target` must already be broadcast to the same
    shape (one row per (agent, antecedent) pair being updated); `mu`,
    `smoothstep_degree` are per-agent, broadcast the same way. Returns
    (delta_omega, omega_new) — callers need both: the delta feeds Psi Flux, the new value
    is what gets written back to `SimulationState.omega`.
    """
    delta_omega = mu * (omega_antecedent_prev - beta_target)
    omega_new = smoothstep(omega_antecedent_prev + delta_omega, smoothstep_degree)
    return delta_omega, omega_new


def psi_flux(
    omega_consequent_prev: np.ndarray, delta_omega_antecedent: np.ndarray, mu: np.ndarray, smoothstep_degree: np.ndarray
) -> np.ndarray:
    """delta_psi(I_c|I_a) = mu*delta_omega(I_a); omega(I_c)|t =
    S_n(omega(I_c)|t-1 + delta_psi(I_c|I_a)), for every consequent I_c of an antecedent
    I_a that just received Omega Flux (draft 4.2; "renamed from the source
    dissertation's 'Gamma Flux'"). Same broadcast contract as `omega_flux`."""
    delta_psi = mu * delta_omega_antecedent
    return smoothstep(omega_consequent_prev + delta_psi, smoothstep_degree)


def antecedents_of(dag: DagAdjacency, prop_id: int) -> np.ndarray:
    """Proposition indices of every antecedent I_a of `prop_id`."""
    row = dag.raw_antecedent.getrow(prop_id)
    return row.indices


def consequents_of(dag: DagAdjacency, prop_id: int) -> np.ndarray:
    """Proposition indices of every consequent I_c of `prop_id` (the raw, unnormalized
    adjacency — Psi Flux applies mu*delta to *each* consequent in full, not divided
    across them the way reluctance's rho averages; row-normalization is specific to
    Section 3.3's rho, not to flowback)."""
    row = dag.raw_consequent.getrow(prop_id)
    return row.indices
