#!/usr/bin/env python3
"""Sample run: the "Flat Earth" domain (draft Section 4.3's own naming — one of the 10
concept domains, "Empirically resolvable, consensus contested").

**This domain's axiom hierarchy is illustrative test data, not an authoritative
draft-companion document.** The real project anticipates 10 domain-specific
axiom-hierarchy documents (PRD Section 1, `docs/DEV_TASKLIST.md`'s blocking-prerequisite
note) that are not in this repo. The propositions below were written for this demo so
there is *something* concrete to run the already-implemented mechanism modules against —
the mechanisms themselves are the draft's math verbatim; only the domain content is
demo-authored.

Axiom hierarchy (5 axioms, 5 composites, all binary per draft 3.8's binarization
requirement):

    I0  axiom  "Ships disappear hull-first over the horizon"
    I1  axiom  "Star trails/constellations shift systematically with latitude"
    I2  axiom  "Commercial flight times between southern-hemisphere cities match a
                round-Earth great-circle model"
    I3  axiom  "Large bodies of standing water appear flat to the naked eye"
                (the "water finds its level" flat-Earth argument)
    I4  axiom  "High-altitude/spacecraft photography shows a curved horizon"

    I5  AND(I0, I4)  "direct observational evidence supports curvature"
    I6  AND(I1, I2)  "astronomical/navigational evidence supports a round Earth"
    I7  OR(I5, I6)   "there is strong evidence the Earth is round"
    I8  NOT(I3)      "the water-level appearance argument does not hold up as
                       counter-evidence" -- exercises the NOT/unary path end to end
    I9  IMPLIES(I8, I7)  "if the water-level argument doesn't hold up, the round-Earth
                           evidence stands" -- the root proposition this demo tracks

**A real gap this demo works around.** draft 4.11 describes agents discovering axioms by
landing on a seeded grid cell; that mechanic isn't implemented yet (see
`docs/DEV_TASKLIST.md`) -- the engine currently only supports discovery via a received
message. This demo seeds initial beliefs directly through the *already-implemented*
self-discovery mechanism (draft 3.8: `orphan_revelation.self_discovery_trust_init`,
SELF as an ordinary publisher) instead of inventing a workaround mechanism -- a handful
of agents "directly observe" one axiom each at tick 0, then belief/trust propagate
through the population via the ordinary tick loop from there.

Usage: `PYTHONPATH=. python scripts/demo_flat_earth.py`
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from freewill.analysis.memory_chain import read_memory_chain
from freewill.config.params import PopulationStability, RunConfig, SeedingCondition
from freewill.engine.state import (
    COEFFICIENT_COLUMNS,
    NO_OPERAND,
    DagAdjacency,
    PropositionSchema,
    SimulationState,
    TrustStore,
)
from freewill.engine.tick_loop import run_tick
from freewill.mechanisms.fuzzy_resolution import ExprType
from freewill.mechanisms.orphan_revelation import self_discovery_trust_init
from freewill.mechanisms.smoothstep import degree_from_sigma
from freewill.storage.event_log import EventLogBuffer

PROPOSITION_LABELS = {
    0: "Ships disappear hull-first over the horizon",
    1: "Star trails shift systematically with latitude",
    2: "Southern-hemisphere flight times match a round-Earth model",
    3: "Standing water appears flat (\"water finds its level\")",
    4: "High-altitude photography shows a curved horizon",
    5: "AND(I0,I4): direct observational evidence supports curvature",
    6: "AND(I1,I2): astronomical/navigational evidence supports round Earth",
    7: "OR(I5,I6): there is strong evidence the Earth is round",
    8: "NOT(I3): the water-level argument doesn't hold up",
    9: "IMPLIES(I8,I7): round-Earth evidence stands  [ROOT]",
}


def build_flat_earth_schema() -> PropositionSchema:
    expr_type = np.array(
        [
            ExprType.AXIOM, ExprType.AXIOM, ExprType.AXIOM, ExprType.AXIOM, ExprType.AXIOM,  # I0-I4
            ExprType.AND, ExprType.AND, ExprType.OR, ExprType.NOT, ExprType.IMPLIES,          # I5-I9
        ]
    )
    operand_left = np.array([NO_OPERAND] * 5 + [0, 1, 5, 3, 8])
    operand_right = np.array([NO_OPERAND] * 5 + [4, 2, 6, NO_OPERAND, 7])
    return PropositionSchema(expr_type=expr_type, operand_left=operand_left, operand_right=operand_right)


def build_dag() -> DagAdjacency:
    # antecedent -> consequent edges, matching each composite's operands (draft 4.2).
    antecedents = np.array([0, 4, 1, 2, 5, 6, 3, 8, 7])
    consequents = np.array([5, 5, 6, 6, 7, 7, 8, 9, 9])
    return DagAdjacency.from_edges(antecedents, consequents, num_propositions=10)


def build_initial_state(rng: np.random.Generator, num_agents: int, run_id: str) -> tuple[SimulationState, int]:
    schema = build_flat_earth_schema()
    dag = build_dag()
    num_props = schema.num_propositions

    belief = np.zeros((num_agents, num_props))
    omega = np.zeros((num_agents, num_props))
    known = np.zeros((num_agents, num_props), dtype=bool)
    orphan = np.zeros((num_agents, num_props), dtype=bool)
    k_assertions = np.zeros((num_agents, num_props), dtype=int)
    phi = np.zeros((num_agents, num_props))
    phi_message_count = np.zeros((num_agents, num_props), dtype=int)
    trust = TrustStore(num_agents=num_agents)

    from freewill.config.params import AgentCoefficientDistributions

    dists = AgentCoefficientDistributions()
    coeff_data = {
        "lambda": dists.lambda_.sample(rng, num_agents),
        "mu": dists.mu.sample(rng, num_agents),
        "eta": dists.eta.sample(rng, num_agents),
        "xi": dists.xi.sample(rng, num_agents),
        "sigma": dists.sigma.sample(rng, num_agents),
        "chi": dists.chi.sample(rng, num_agents),
        "theta": dists.theta.sample(rng, num_agents),
        "pi": dists.pi_.sample(rng, num_agents),
        "k_star": dists.k_star.sample(rng, num_agents),
    }
    coefficients = pd.DataFrame(coeff_data)[COEFFICIENT_COLUMNS]
    smoothstep_degree = degree_from_sigma(coefficients["sigma"].to_numpy())

    grid_size = int(np.ceil(np.sqrt(num_agents * 1.4)))
    grid_positions = rng.integers(0, grid_size, size=(num_agents, 2)).astype(float)
    personal_affinity = np.zeros((num_agents, 2))

    # -- influencer: agent 0 pushes the flat-Earth "water level" axiom (I3) --
    is_influencer = np.zeros(num_agents, dtype=bool)
    is_influencer[0] = True
    influencer_agenda_proposition = np.full(num_agents, NO_OPERAND)
    influencer_agenda_proposition[0] = 3
    influencer_agenda_confidence = np.zeros(num_agents)
    influencer_agenda_confidence[0] = 0.45

    last_raised_topic = np.full((num_agents, num_agents), NO_OPERAND)

    # -- seed initial self-discovery (draft 3.8's arrival-via-SELF, PRD 4.11's environmental
    # discovery isn't implemented yet -- see this module's docstring).
    #
    # Composites are seeded too, not just axioms: an agent never spontaneously reasons
    # "I already know both operands, therefore I know I5" -- draft 3.8's orphan/revelation
    # machinery only starts tracking a composite once someone actually *asserts* it to the
    # agent (arrival), which requires it to already be in some speaker's known_topics.
    # Without at least one agent starting out knowing each composite, I5-I9 could never
    # enter circulation at all -- confirmed by an earlier run of this exact script, where
    # every composite sat at 0% saturation for the full 150 ticks despite every axiom
    # partially propagating. This isn't an engine gap, just what draft 3.8 actually says.
    seed_groups: list[tuple[list[int], int, float]] = [
        ([0], 3, 0.45),          # the influencer genuinely holds its own agenda belief
        ([1, 2, 3], 0, 0.30),
        ([4, 5, 6], 4, 0.35),
        ([7, 8], 1, 0.25),
        ([9, 10], 2, 0.20),
        ([11, 12, 13], 3, 0.40),
        ([14, 15], 5, 0.30),     # AND(I0,I4): a few agents start out already holding the
        ([16, 17], 6, 0.28),     # AND(I1,I2) composite claim directly
        ([18], 8, 0.30),         # NOT(I3) -- exercises the NOT-node fix end to end
        ([19], 9, 0.35),         # the root claim itself, asserted directly by one agent
    ]
    for agent_ids, prop, nu in seed_groups:
        agent_ids = [a for a in agent_ids if a < num_agents]
        if not agent_ids:
            continue
        idx = np.array(agent_ids)
        tau0 = self_discovery_trust_init(rng, len(idx))
        for a, t0 in zip(idx, tau0):
            trust.set(int(prop), np.array([a]), np.array([a]), np.array([t0]))
            phi[a, prop] = nu
            phi_message_count[a, prop] = 1
            belief[a, prop] = nu * t0
            known[a, prop] = True

    return SimulationState(
        run_id=run_id, tick=0, schema=schema, dag=dag,
        belief=belief, omega=omega, known=known, orphan=orphan, k_assertions=k_assertions,
        phi=phi, phi_message_count=phi_message_count, trust=trust,
        coefficients=coefficients, smoothstep_degree=smoothstep_degree,
        grid_positions=grid_positions, personal_affinity=personal_affinity,
        is_influencer=is_influencer, influencer_agenda_proposition=influencer_agenda_proposition,
        influencer_agenda_confidence=influencer_agenda_confidence, last_raised_topic=last_raised_topic,
    ), grid_size


def population_stats(state: SimulationState, prop_id: int) -> dict:
    mask = state.known[:, prop_id]
    n_known = int(mask.sum())
    if n_known == 0:
        return {"n_known": 0, "mean": None, "std": None, "saturation": 0.0}
    values = state.belief[mask, prop_id]
    return {
        "n_known": n_known,
        "mean": float(values.mean()),
        "std": float(values.std()),
        "saturation": n_known / state.num_agents,
    }


def main() -> None:
    seed = 20260831
    rng = np.random.default_rng(seed)
    num_agents = 30
    num_ticks = 250
    run_id = "demo-flat-earth"

    state, grid_size = build_initial_state(rng, num_agents, run_id)
    config = RunConfig(
        run_id=run_id, domain="flat_earth", seed=seed,
        population_stability=PopulationStability.RANDOM, seeding_condition=SeedingCondition.INFLUENCER,
        epsilon_explore=0.10, tau_still=0.03, influencer_reach=20,
        num_agents=num_agents, num_ticks=num_ticks,
    )

    out_dir = Path(__file__).parent / "demo_output"
    out_dir.mkdir(exist_ok=True)
    events_path = out_dir / "flat_earth_events.jsonl"
    if events_path.exists():
        events_path.unlink()
    event_log = EventLogBuffer(events_path, flush_every=1)

    print(f"=== FREE WILL demo: Flat Earth domain ({num_agents} agents, {num_ticks} ticks, seed={seed}) ===\n")
    print("Propositions:")
    for i, label in PROPOSITION_LABELS.items():
        print(f"  I{i}: {label}")
    print()

    trajectory = []
    grid_shape = (grid_size, grid_size)
    checkpoints = set(range(0, num_ticks, 5)) | {num_ticks - 1}
    for t in range(num_ticks):
        state = run_tick(state, config, event_log, rng, grid_shape)
        if t in checkpoints:
            row = {"tick": t + 1}
            for prop_id in range(10):
                stats = population_stats(state, prop_id)
                row[f"I{prop_id}_saturation"] = stats["saturation"]
                row[f"I{prop_id}_mean"] = stats["mean"]
            trajectory.append(row)
            if t % 25 == 0 or t == num_ticks - 1:
                print(
                    f"tick {t + 1:4d}: I3 (water-level) sat={row['I3_saturation']:.2f} mean={row['I3_mean']}  |  "
                    f"I9 (root) sat={row['I9_saturation']:.2f} mean={row['I9_mean']}"
                )

    event_log.close()

    traj_path = out_dir / "flat_earth_trajectory.json"
    traj_path.write_text(json.dumps(trajectory, indent=2))
    print(f"\nWrote per-tick trajectory to {traj_path}")
    print(f"Wrote event log to {events_path}")

    event_counts: dict[str, int] = {}
    for line in events_path.read_text().splitlines():
        et = json.loads(line)["event_type"]
        event_counts[et] = event_counts.get(et, 0) + 1
    print(f"\nEvent counts over the run: {event_counts}")

    print("\n=== Final population belief snapshot ===")
    for prop_id in range(10):
        stats = population_stats(state, prop_id)
        mean_str = f"{stats['mean']:+.3f}" if stats["mean"] is not None else "  n/a"
        std_str = f"{stats['std']:.3f}" if stats["std"] is not None else "n/a"
        print(
            f"  I{prop_id}: saturation={stats['saturation']:.2f}  mean={mean_str}  std={std_str}"
            f"   -- {PROPOSITION_LABELS[prop_id]}"
        )

    # Agent 16 was seeded holding I6 (AND(I1,I2), a composite) directly -- but everything
    # else in its belief/trust history is organic, picked up from other agents during the
    # run. Its recorded trace shows it later encountering I3 (the influencer's dominant
    # axiom, which saturates the whole population) and I5 (the *other* curvature
    # composite) purely through message-passing -- a good illustration of how a seeded
    # composite belief interacts with organically-spreading axioms and revelation. (An
    # agent seeded with nothing at all, e.g. agent 22 or 25, never touches a composite in
    # this run -- composites only spread by being asserted in conversation, and the
    # unseeded agents this run happened to talk to never had one to assert.)
    trace_agent = 16
    print(f"\n=== Sample reasoning trace: agent {trace_agent} (seeded with I6; rest organic) ===")
    chain = read_memory_chain(events_path, agent_id=trace_agent)
    print(f"{len(chain.steps)} total recorded steps for agent {trace_agent}.")
    print(f"Propositions this agent ever encountered: {sorted(chain.known_propositions())}")
    print("\nFirst 20 steps of its full reasoning trace:")
    for line in chain.explain_all()[:20]:
        print(f"  {line}")


if __name__ == "__main__":
    main()
