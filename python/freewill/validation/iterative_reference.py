"""Iterative fallback / validation harness (PRD Section 4.4).

Deliberately slow, per-agent-loop reference implementations, cross-checked for exact
numerical agreement against the vectorized engine on identical inputs — the correctness
oracle PRD Section 2.1 calls for, not a production fallback.

**Scope note, read before extending this file.** PRD Section 4.4's original wording asks
for a reference implementation of "the *entire* tick cycle." As built,
`freewill.engine.tick_loop` already processes most of a tick's belief/trust updates one
message at a time (`_apply_message` operates on single-element arrays, not a
population-wide batch) — so a from-scratch "iterative" re-implementation of that
per-message path would, for most of the tick, just be the same formula copied into a
`for` loop around the same single-element calls, exercising no genuinely different code
path. The places a real vectorized-vs-naive contrast exists — where PRD Section 4.9
explicitly claims the vectorized path "reduces to a single sparse matrix multiplication"
or an elementwise batch over *many* pairs at once, rather than one message's worth of
data — are exactly the functions below: reluctance's `rho` (draft 3.3, a `belief @ D.T`
matmul across the whole population), Alpha Flux's weighted-consensus sum (draft 3.2, a
per-proposition matvec against the whole trust matrix), flowback's Omega/Psi Flux applied
to *every* antecedent/consequent of a target in one array op (draft 4.2), and the
whole-population trigger scans in orphan/revelation (draft 3.8) and composite trust
derivation (draft 3.9). Each `iterative_*` function here recomputes its vectorized
counterpart's result via an explicit Python loop, no array batching anywhere, cross-
checked in `tests/test_cross_validation.py` across randomized small populations and
seeds. If the tick-loop scheduling itself is later vectorized further (the
`docs/DEV_TASKLIST.md` follow-up on `tick_loop.py`'s per-agent scheduling), extend this
file's scope to match at that point — narrowing to what's actually vectorized differently
today isn't a shortcut, it's what makes this harness test something real.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import NO_OPERAND, DagAdjacency, PropositionSchema, TrustStore


def iterative_rho(belief: np.ndarray, dag: DagAdjacency) -> np.ndarray:
    """Naive per-(agent, proposition) loop computing rho(I_c|I) (draft 3.3) — the
    reference for `reluctance.compute_rho`'s `belief @ D.T` matmul."""
    num_agents, num_props = belief.shape
    raw = dag.raw_consequent.tocsr()
    rho = np.zeros((num_agents, num_props))
    for prop in range(num_props):
        consequents = raw.getrow(prop).indices
        if len(consequents) == 0:
            continue
        for agent in range(num_agents):
            rho[agent, prop] = float(np.mean([belief[agent, c] for c in consequents]))
    return rho


def iterative_alpha(trust: TrustStore, phi: np.ndarray, prop_id: int, num_agents: int) -> np.ndarray:
    """Naive nested loop over every (receiver, publisher) pair computing alpha(I) (draft
    3.2) — the reference for `trust_belief_update.compute_alpha`'s per-proposition
    `T[I] @ phi[:,I]` matvec."""
    alpha = np.zeros(num_agents)
    for receiver in range(num_agents):
        total = 0.0
        count = 0
        for publisher in range(num_agents):
            r = np.array([receiver])
            p = np.array([publisher])
            if trust.has_entry(prop_id, r, p)[0]:
                total += float(phi[publisher, prop_id]) * float(trust.get(prop_id, r, p)[0])
                count += 1
        alpha[receiver] = 2.0 * total / count if count > 0 else 0.0
    return alpha


def iterative_omega_psi_flux(
    omega_antecedent_prev: np.ndarray,
    beta_target: np.ndarray,
    mu: np.ndarray,
    smoothstep_degree: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Element-by-element Python loop computing Omega Flux (draft 4.2) for a batch of
    antecedents — the reference for `flowback.omega_flux`'s array-batched version."""
    from freewill.mechanisms.smoothstep import smoothstep

    n = len(omega_antecedent_prev)
    delta = np.zeros(n)
    omega_new = np.zeros(n)
    for i in range(n):
        d = float(mu[i]) * (float(omega_antecedent_prev[i]) - float(beta_target[i]))
        delta[i] = d
        omega_new[i] = float(
            smoothstep(np.array([omega_antecedent_prev[i] + d]), np.array([smoothstep_degree[i]]))[0]
        )
    return delta, omega_new


def iterative_revelation_candidates(
    schema: PropositionSchema, known: np.ndarray, orphan: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Explicit nested loop over every (agent, proposition) pair finding revelation
    triggers (draft 3.8) — the reference for
    `orphan_revelation.find_revelation_candidates`'s boolean-mask version."""
    num_agents, num_props = known.shape
    agents: list[int] = []
    props: list[int] = []
    for agent in range(num_agents):
        for prop in range(num_props):
            if not orphan[agent, prop]:
                continue
            left = int(schema.operand_left[prop])
            right = int(schema.operand_right[prop])
            if left == NO_OPERAND or right == NO_OPERAND:
                continue
            if known[agent, left] and known[agent, right]:
                agents.append(agent)
                props.append(prop)
    return np.array(agents, dtype=int), np.array(props, dtype=int)


def iterative_composite_trust_targets(
    trust: TrustStore, schema: PropositionSchema, prop_id: int, num_agents: int
) -> tuple[np.ndarray, np.ndarray]:
    """Explicit nested loop over every (receiver, publisher) pair finding composite
    trust derivation triggers (draft 3.9) — the reference for
    `composite_trust.derive_missing_for_proposition`'s AND-of-masks version."""
    if schema.is_axiom[prop_id]:
        return np.array([], dtype=int), np.array([], dtype=int)
    left = int(schema.operand_left[prop_id])
    right = int(schema.operand_right[prop_id])
    receivers: list[int] = []
    publishers: list[int] = []
    for receiver in range(num_agents):
        for publisher in range(num_agents):
            r = np.array([receiver])
            p = np.array([publisher])
            if (
                trust.has_entry(left, r, p)[0]
                and trust.has_entry(right, r, p)[0]
                and not trust.has_entry(prop_id, r, p)[0]
            ):
                receivers.append(receiver)
                publishers.append(publisher)
    return np.array(receivers, dtype=int), np.array(publishers, dtype=int)
