"""Tick loop (PRD Section 4.2).

Orchestrates one run's ticks in the exact order PRD Section 4.2 specifies, delegating
each step to the corresponding mechanism module (PRD Section 4.3) so the loop itself stays
a thin sequencer rather than a place where mechanism math accumulates.
"""

from __future__ import annotations

from freewill.config.params import RunConfig
from freewill.engine.state import SimulationState
from freewill.mechanisms import (
    composite_trust,
    fallacy_extensions,
    flowback,
    influencer,
    movement,
    orphan_revelation,
    trust_belief_update,
)
from freewill.storage.checkpoint_store import CheckpointStore
from freewill.storage.event_log import EventLogBuffer


def run_tick(state: SimulationState, config: RunConfig, event_log: EventLogBuffer) -> SimulationState:
    """Advance `state` by exactly one tick, per PRD Section 4.2's seven steps.

    Each call below is a direct 1:1 mapping to PRD 4.2's ordered steps; see each
    mechanism module for its draft-section reference. This function does not itself
    implement any formula (PRD Section 2.3) — every step here is still a stub until its
    mechanism module is implemented.
    """
    # 1. Personal Affinity (draft 4.11) — vectorized.
    state.personal_affinity = movement.compute_personal_affinity(
        state.grid_positions, state.trust_tensor, state.belief_matrix
    )

    # 2. Movement: candidate moves (vectorized) -> collision resolution (iterative over
    #    contested cells only).
    candidate_moves = movement.compute_candidate_moves(
        state.grid_positions,
        state.personal_affinity,
        tau_still=config.tau_still,
        epsilon_explore=config.epsilon_explore,
        rng=None,  # TODO: thread a seeded np.random.Generator through from config.seed
    )
    state.grid_positions = movement.resolve_collisions(candidate_moves, priority=None)

    # 3. Trigger discovery + conversation (vectorized sparse boolean masks).
    state.belief_matrix = orphan_revelation.trigger_discovery(
        state.grid_positions, seeded_cells=None, belief_matrix=state.belief_matrix
    )
    state.communication_matrix = influencer.build_communication_matrix(
        state.grid_positions, influencer_reach=config.influencer_reach
    )

    # 4. Belief/trust updates over the tick's dirty set (all vectorized batched ops).
    dirty_propositions = None  # TODO: derive from step 3's discovery/conversation output
    state.belief_matrix = trust_belief_update.apply_alpha_flux(
        state.belief_matrix, state.trust_tensor, dirty_propositions
    )
    state.trust_tensor = trust_belief_update.apply_forward_flow(
        state.belief_matrix, state.trust_tensor, dirty_propositions
    )
    state.belief_matrix = flowback.apply_omega_flux(
        state.belief_matrix, state.dag_antecedent, dirty_propositions
    )
    state.trust_tensor = flowback.apply_psi_flux(
        state.belief_matrix, state.trust_tensor, dirty_propositions
    )
    state.belief_matrix = fallacy_extensions.apply_fallacy_extensions(
        state.belief_matrix, state.k_assertion_counts, dirty_propositions
    )
    state.trust_tensor = composite_trust.derive_composite_trust(
        state.trust_tensor, dirty_agents=None
    )

    # 5. Ad hominem/halo-effect leak (the one deliberately non-vectorized mechanism,
    #    PRD 4.9) over this tick's colliding agent pairs.
    state.trust_tensor = fallacy_extensions.apply_ad_hominem_halo_leak(
        state.trust_tensor, colliding_pairs=[]
    )

    # 6. Event log append happens inside each mechanism call above in the full
    #    implementation (each mechanism records its own events via `event_log`); this
    #    stub loop does not yet wire that through.

    state.tick += 1
    return state


def run_simulation(
    state: SimulationState,
    config: RunConfig,
    event_log: EventLogBuffer,
    checkpoint_store: CheckpointStore,
) -> SimulationState:
    """Run `config.num_ticks` ticks, checkpointing every `config.checkpoint_interval_ticks`
    ticks and always at start/end (PRD Section 4.2 step 7, Section 6.2)."""
    _write_checkpoint(state, checkpoint_store)

    for _ in range(config.num_ticks):
        state = run_tick(state, config, event_log)
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
            # TODO: serialize state.belief_matrix / state.trust_tensor to
            # savez-compatible component arrays (PRD 6.2's npz format).
            "grid_positions": state.grid_positions,
            "personal_affinity": state.personal_affinity,
        },
        coefficient_table=state.coefficient_table,
    )
