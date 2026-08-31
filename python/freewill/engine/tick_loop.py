"""Tick loop — FREE_WILL_draft.md Section 4.11's "Tick sequence, in full":
(1) Personal Affinity, (2) resolve moves, (3) trigger discovery/conversation,
(4) message formulation, (5) apply belief/trust updates, (6) tick ends.

**Scope note on vectorization.** Every *formula* below (reluctance, flowback,
orphan/revelation, Alpha Flux/Forward Flow's per-proposition matvec) is the vectorized
implementation PRD Section 4.9 specifies — batched over the whole population or the
tick's dirty set in one array operation, not a per-agent Python loop. What *is* a Python
loop here is the tick's own *scheduling*: iterating over which agent is doing what this
tick (its Personal Affinity's neighbor gather, its chosen move, its triggered
conversations). That loop is bounded by population size and reach, not by proposition or
DAG size, and unlike the numerical formulas it is not a place PRD 4.9 claims reduces to a
single matmul — the draft's own Personal Affinity is inherently per-agent (each agent's
known-neighbor set has different size and membership, draft 4.11). Vectorizing this
scheduling loop further (e.g. padding neighbor sets to a fixed width) is real follow-up
work, tracked in docs/DEV_TASKLIST.md, not silently skipped.
"""

from __future__ import annotations

import numpy as np

from freewill.config.params import RunConfig
from freewill.engine.state import SimulationState
from freewill.mechanisms import (
    fallacy_extensions,
    flowback,
    influencer,
    message_formulation,
    movement,
    orphan_revelation,
    reluctance,
    trust_belief_update,
)
from freewill.mechanisms.smoothstep import smoothstep
from freewill.storage.checkpoint_store import CheckpointStore
from freewill.storage.event_log import Event, EventLogBuffer


def _compute_all_personal_affinities(state: SimulationState) -> None:
    """Draft 4.11 step 1. Loops over agents (see module docstring's scope note); each
    agent's own per-neighbor trust gather is a handful of `TrustStore` reads."""
    axioms = np.nonzero(state.schema.is_axiom)[0]
    for a in range(state.num_agents):
        neighbors = state.trust.known_neighbors(a)
        if len(neighbors) == 0:
            state.personal_affinity[a] = 0.0
            continue
        mean_trust_per_neighbor = np.empty(len(neighbors))
        for j, p in enumerate(neighbors):
            known_axioms = [i for i in axioms if state.trust.has_entry(int(i), np.array([a]), np.array([p]))[0]]
            if not known_axioms:
                mean_trust_per_neighbor[j] = 0.0
                continue
            vals = np.array(
                [state.trust.get(int(i), np.array([a]), np.array([p]))[0] for i in known_axioms]
            )
            mean_trust_per_neighbor[j] = movement.mean_trust(vals)
        state.personal_affinity[a] = movement.compute_personal_affinity(
            state.grid_positions[a], state.grid_positions[neighbors], mean_trust_per_neighbor
        )


def _resolve_moves(state: SimulationState, config: RunConfig, rng: np.random.Generator, grid_shape: tuple[int, int]) -> None:
    """Draft 4.11 step 2: stay-threshold check -> epsilon-greedy -> collision resolution."""
    candidate_cells = np.empty_like(state.grid_positions)
    move_scores = np.empty(state.num_agents)
    for a in range(state.num_agents):
        num_neighbors = len(state.trust.known_neighbors(a))
        if num_neighbors == 0:
            direction = movement.DIRECTIONS[rng.integers(len(movement.DIRECTIONS))]
        elif movement.should_stay(state.personal_affinity[a], num_neighbors, config.tau_still):
            direction = np.zeros(2)
        else:
            direction = movement.choose_direction(state.personal_affinity[a], config.epsilon_explore, rng)
        candidate_cells[a] = (state.grid_positions[a] + direction) % grid_shape
        move_scores[a] = float(state.personal_affinity[a] @ direction)

    approved = movement.resolve_collisions(candidate_cells, move_scores, rng)
    state.grid_positions[approved] = candidate_cells[approved]


def _trigger_and_converse(
    state: SimulationState, config: RunConfig, rng: np.random.Generator, event_log: EventLogBuffer
) -> list[tuple[int, int, int, float]]:
    """Draft 4.11 steps 3-4: automatic discovery + conversation based on resulting
    positions, then message content via Section 4.12. Returns the tick's message events
    as (receiver, publisher, proposition, nu) tuples for step 5 to apply."""
    events: list[tuple[int, int, int, float]] = []
    baseline = np.where(state.is_influencer, config.influencer_reach, 1)

    cell_occupants: dict[tuple[int, int], list[int]] = {}
    for a in range(state.num_agents):
        cell_occupants.setdefault(tuple(state.grid_positions[a]), []).append(a)

    for a in range(state.num_agents):
        present = [p for p in cell_occupants[tuple(state.grid_positions[a])] if p != a]
        reach = movement.compute_reach(np.array([baseline[a]]), np.array([len(present)]))[0]
        if state.is_influencer[a] and len(present) < reach:
            present = influencer.top_up_reach(rng, np.array(present), int(reach), state.num_agents, a).tolist()

        known_topics = np.nonzero(state.known[a])[0]
        epsilon_topic = config.epsilon_topic if config.epsilon_topic is not None else config.epsilon_explore

        for p in present:
            if len(known_topics) == 0:
                continue
            chosen, nu = message_formulation.choose_message(
                rng,
                a,
                p,
                state.is_influencer,
                state.influencer_agenda_proposition,
                state.influencer_agenda_confidence,
                known_topics,
                state.belief[a],
                state.last_raised_topic,
                epsilon_topic,
            )
            state.last_raised_topic[a, p] = chosen
            # k(I): "count of the agent's own outgoing messages asserting I" (draft 3.4,
            # 3.7) -- incremented for the *speaker* here; doubling-down defiance later
            # reads it for whichever agent is on the receiving end of a future message.
            state.k_assertions[a, chosen] += 1
            events.append((p, a, chosen, nu))
            event_log.record(
                Event(
                    run_id=state.run_id,
                    tick=state.tick,
                    agent_id=int(p),
                    event_type="message_received",
                    proposition_id=chosen,
                    source_id=int(a),
                    new_value=nu,
                )
            )
    return events


def _apply_message(state: SimulationState, config: RunConfig, event: tuple[int, int, int, float], event_log: EventLogBuffer) -> None:
    """Draft 4.11 step 5, one message at a time: Section 3.8's arrival (if new), else
    Alpha Flux + Forward Flow (Section 3.2), Section 3.7's fallacy extensions, Section
    3.3's reluctance-damped commit, and Section 4.2's flowback."""
    receiver, publisher, prop, nu = event
    coeffs = state.coefficients

    # Alpha Flux (below) needs phi(I|P)|t-1 -- P's mean stated confidence *before* this
    # message's own contribution (draft 3.2). Capture it now, then fold this message into
    # the running mean; the delta computation later reads `phi_prev`, never `state.phi`
    # directly, so it can't accidentally observe this message's own contribution.
    phi_prev = float(state.phi[publisher, prop])
    trust_belief_update.update_phi(state.phi, state.phi_message_count, np.array([publisher]), np.array([prop]), np.array([nu]))

    had_entry = state.trust.has_entry(prop, np.array([receiver]), np.array([publisher]))[0]
    if not had_entry:
        known_count = state.trust.known_count(prop, np.array([receiver]))[0]
        tau0 = reluctance.default_trust_init(np.array([float(known_count)]), coeffs["eta"].to_numpy()[[receiver]])[0]
        state.trust.set(prop, np.array([receiver]), np.array([publisher]), np.array([tau0]))
        tau_p_i = tau0
    else:
        tau_p_i = state.trust.get(prop, np.array([receiver]), np.array([publisher]))[0]

    if not state.known[receiver, prop]:
        beta0 = orphan_revelation.arrival_belief(np.array([nu]), np.array([tau_p_i]))[0]
        state.belief[receiver, prop] = beta0
        state.known[receiver, prop] = True
        state.orphan[receiver, prop] = state.schema.is_composite[prop]
        event_log.record(
            Event(run_id=state.run_id, tick=state.tick, agent_id=receiver, event_type="discovery",
                  proposition_id=prop, source_id=publisher, new_value=float(beta0))
        )
    else:
        delta_tau = trust_belief_update.alpha_flux_delta_tau(
            coeffs["mu"].to_numpy()[[receiver]], np.array([phi_prev]), state.belief[[receiver], [prop]]
        )[0]
        n_receiver = state.smoothstep_degree[receiver]
        new_tau = smoothstep(np.array([tau_p_i + delta_tau]), np.array([n_receiver]))[0]
        state.trust.set(prop, np.array([receiver]), np.array([publisher]), np.array([new_tau]))
        event_log.record(
            Event(run_id=state.run_id, tick=state.tick, agent_id=receiver, event_type="trust_update",
                  mechanism="alpha_flux", proposition_id=prop, source_id=publisher,
                  old_value=float(tau_p_i), new_value=float(new_tau))
        )

        leaked = fallacy_extensions.apply_ad_hominem_halo_leak(
            state.trust, coeffs["chi"].to_numpy(), state.smoothstep_degree,
            np.array([receiver]), np.array([publisher]), np.array([prop]), np.array([delta_tau]),
        )
        for _r, _p, target_prop, old_v, new_v in leaked:
            event_log.record(
                Event(run_id=state.run_id, tick=state.tick, agent_id=receiver, event_type="fallacy_triggered",
                      mechanism="ad_hominem_halo_leak", proposition_id=target_prop, source_id=publisher,
                      old_value=old_v, new_value=new_v)
            )

        delta_beta = trust_belief_update.apply_dirty_set_update(state, np.array([receiver]), np.array([prop]))
        delta_beta_prime = fallacy_extensions.apply_negativity_bias(delta_beta, coeffs["theta"].to_numpy()[[receiver]])
        disagreement = fallacy_extensions.is_disagreement(np.array([nu]), state.belief[[receiver], [prop]])
        delta_beta_final = fallacy_extensions.apply_doubling_down_defiance(
            delta_beta_prime, coeffs["pi"].to_numpy()[[receiver]], np.array([new_tau]), disagreement,
            state.k_assertions[[receiver], [prop]], coeffs["k_star"].to_numpy()[[receiver]],
        )

        rho = reluctance.compute_rho(state.belief[[receiver]], state.dag)
        gamma = reluctance.compute_gamma(rho, coeffs["xi"].to_numpy()[[receiver]])[0]
        old_beta = state.belief[receiver, prop]
        new_beta = reluctance.apply_reluctance_damped_update(
            np.array([old_beta]), delta_beta_final, np.array([gamma[prop]])
        )[0]
        state.belief[receiver, prop] = new_beta
        event_log.record(
            Event(run_id=state.run_id, tick=state.tick, agent_id=receiver, event_type="belief_update",
                  mechanism="forward_flow", proposition_id=prop, source_id=publisher,
                  old_value=float(old_beta), new_value=float(new_beta))
        )

        # Flowback (draft 4.2): antecedents' Omega Flux, then Psi Flux onward to each
        # antecedent's own consequents.
        antecedents = flowback.antecedents_of(state.dag, prop)
        if len(antecedents):
            omega_prev = state.get_omega(np.full(len(antecedents), receiver), antecedents)
            n_r = np.full(len(antecedents), state.smoothstep_degree[receiver])
            delta_omega, omega_new = flowback.omega_flux(
                omega_prev, np.full(len(antecedents), new_beta), coeffs["mu"].to_numpy()[[receiver] * len(antecedents)], n_r
            )
            for idx, ia in enumerate(antecedents):
                if not (state.schema.is_axiom[ia] or state.orphan[receiver, ia]):
                    state.omega[receiver, ia] = omega_new[idx]
                for ic in flowback.consequents_of(state.dag, int(ia)):
                    if state.schema.is_axiom[ic] or state.orphan[receiver, ic]:
                        continue
                    om_c_prev = state.omega[receiver, ic]
                    new_om_c = flowback.psi_flux(
                        np.array([om_c_prev]), np.array([delta_omega[idx]]),
                        coeffs["mu"].to_numpy()[[receiver]], np.array([state.smoothstep_degree[receiver]]),
                    )[0]
                    state.omega[receiver, ic] = new_om_c

    # Revelation check (draft 3.8): now that this message may have completed an operand
    # pair for some orphaned composite, check the whole population's dirty orphans once.
    agent_idx, prop_idx = orphan_revelation.find_revelation_candidates(state.schema, state.known, state.orphan)
    if len(agent_idx):
        rho = reluctance.compute_rho(state.belief, state.dag)
        gamma = reluctance.compute_gamma(rho, coeffs["xi"].to_numpy())
        old_beliefs = state.belief[agent_idx, prop_idx].copy()
        orphan_revelation.apply_revelation(
            state.belief, state.orphan, state.schema, agent_idx, prop_idx, gamma[agent_idx, prop_idx]
        )
        for a, i, old_v in zip(agent_idx, prop_idx, old_beliefs):
            event_log.record(
                Event(run_id=state.run_id, tick=state.tick, agent_id=int(a), event_type="revelation",
                      mechanism="orphan_revelation", proposition_id=int(i),
                      old_value=float(old_v), new_value=float(state.belief[a, i]))
            )



def run_tick(
    state: SimulationState, config: RunConfig, event_log: EventLogBuffer, rng: np.random.Generator, grid_shape: tuple[int, int]
) -> SimulationState:
    """Advance `state` by exactly one tick, per draft 4.11's six-step sequence."""
    _compute_all_personal_affinities(state)
    _resolve_moves(state, config, rng, grid_shape)
    events = _trigger_and_converse(state, config, rng, event_log)
    for event in events:
        _apply_message(state, config, event, event_log)

    state.tick += 1
    return state


def run_simulation(
    state: SimulationState,
    config: RunConfig,
    event_log: EventLogBuffer,
    checkpoint_store: CheckpointStore,
    grid_shape: tuple[int, int],
    rng: np.random.Generator | None = None,
) -> SimulationState:
    """Run `config.num_ticks` ticks, checkpointing every `config.checkpoint_interval_ticks`
    ticks and always at start/end (PRD Section 4.2 step 7, Section 6.2)."""
    rng = rng if rng is not None else np.random.default_rng()
    _write_checkpoint(state, checkpoint_store)

    for _ in range(config.num_ticks):
        state = run_tick(state, config, event_log, rng, grid_shape)
        if state.tick % config.checkpoint_interval_ticks == 0:
            _write_checkpoint(state, checkpoint_store)

    event_log.close()
    _write_checkpoint(state, checkpoint_store)
    return state


def _write_checkpoint(state: SimulationState, checkpoint_store: CheckpointStore) -> None:
    checkpoint_store.write_checkpoint(
        state.run_id,
        state.tick,
        arrays={
            "belief": state.belief,
            "omega": state.omega,
            "known": state.known,
            "orphan": state.orphan,
            "grid_positions": state.grid_positions,
            "personal_affinity": state.personal_affinity,
        },
        coefficient_table=state.coefficients,
    )
