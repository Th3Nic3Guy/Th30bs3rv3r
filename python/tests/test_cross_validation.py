"""Cross-validation of the vectorized mechanism functions against the iterative
reference oracle (PRD Section 4.4) — see
`freewill/validation/iterative_reference.py`'s module docstring for which functions this
covers and why. Randomized over many seeds and small populations rather than one
hand-picked example, per PRD Section 4.4's "run against small populations... and
cross-checked for exact numerical agreement... on identical seeds."
"""

from __future__ import annotations

import numpy as np
import pytest

from freewill.engine.state import NO_OPERAND, DagAdjacency, PropositionSchema, TrustStore
from freewill.mechanisms import composite_trust, flowback, reluctance
from freewill.mechanisms.fuzzy_resolution import ExprType, resolve
from freewill.mechanisms.smoothstep import degree_from_sigma
from freewill.mechanisms.trust_belief_update import compute_alpha
from freewill.validation.iterative_reference import (
    iterative_alpha,
    iterative_composite_trust_targets,
    iterative_omega_psi_flux,
    iterative_revelation_candidates,
    iterative_rho,
)

SEEDS = range(20)
NUM_AGENTS = 10


def _random_dag(rng: np.random.Generator, num_props: int) -> DagAdjacency:
    # A handful of random antecedent -> consequent edges, no self-loops.
    edges = [(a, c) for a in range(num_props) for c in range(num_props) if a != c and rng.random() < 0.25]
    if not edges:
        edges = [(0, 1)]
    antecedent_idx = np.array([e[0] for e in edges])
    consequent_idx = np.array([e[1] for e in edges])
    return DagAdjacency.from_edges(antecedent_idx, consequent_idx, num_props)


class TestRhoCrossValidation:
    def test_matches_iterative_reference(self):
        num_props = 6
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            dag = _random_dag(rng, num_props)
            belief = rng.uniform(-0.5, 0.5, size=(NUM_AGENTS, num_props))

            vectorized = reluctance.compute_rho(belief, dag)
            iterative = iterative_rho(belief, dag)

            np.testing.assert_allclose(vectorized, iterative, rtol=1e-10, atol=1e-12)


class TestAlphaCrossValidation:
    def test_matches_iterative_reference(self):
        # Alpha's formula is prop-agnostic; using an axiom proposition avoids
        # compute_alpha's composite-trust-derivation side effect (draft 3.9), which the
        # iterative reference deliberately does not perform, so this isolates exactly the
        # weighted-consensus-sum formula being cross-validated.
        schema = PropositionSchema(
            expr_type=np.array([ExprType.AXIOM]),
            operand_left=np.array([NO_OPERAND]),
            operand_right=np.array([NO_OPERAND]),
        )
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            trust = TrustStore(num_agents=NUM_AGENTS)
            phi = rng.uniform(-0.5, 0.5, size=(NUM_AGENTS, 1))
            for receiver in range(NUM_AGENTS):
                for publisher in range(NUM_AGENTS):
                    if rng.random() < 0.4:
                        trust.set(
                            0, np.array([receiver]), np.array([publisher]), np.array([rng.uniform(-0.5, 0.5)])
                        )

            vectorized = compute_alpha(trust, schema, phi, np.array([0]))[0]
            iterative = iterative_alpha(trust, phi, 0, NUM_AGENTS)

            np.testing.assert_allclose(vectorized, iterative, rtol=1e-10, atol=1e-12)


class TestOmegaPsiFluxCrossValidation:
    def test_matches_iterative_reference(self):
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            n = rng.integers(1, 8)
            omega_prev = rng.uniform(-0.5, 0.5, size=n)
            beta_target = rng.uniform(-0.5, 0.5, size=n)
            mu = rng.uniform(0.01, 1.0, size=n)
            degree = degree_from_sigma(rng.uniform(0, 1, size=n))

            delta_v, omega_new_v = flowback.omega_flux(omega_prev, beta_target, mu, degree)
            delta_i, omega_new_i = iterative_omega_psi_flux(omega_prev, beta_target, mu, degree)

            np.testing.assert_allclose(delta_v, delta_i, rtol=1e-10, atol=1e-12)
            np.testing.assert_allclose(omega_new_v, omega_new_i, rtol=1e-10, atol=1e-12)


class TestRevelationCandidatesCrossValidation:
    def _random_schema(self, rng: np.random.Generator, num_props: int) -> PropositionSchema:
        expr_type = np.empty(num_props, dtype=int)
        left = np.full(num_props, NO_OPERAND)
        right = np.full(num_props, NO_OPERAND)
        for i in range(num_props):
            if i < 2 or rng.random() < 0.4:
                expr_type[i] = ExprType.AXIOM
            else:
                expr_type[i] = rng.choice([ExprType.AND, ExprType.OR, ExprType.IMPLIES])
                left[i] = rng.integers(0, i)
                right[i] = rng.integers(0, i)
        return PropositionSchema(expr_type=expr_type, operand_left=left, operand_right=right)

    def test_matches_iterative_reference(self):
        num_props = 8
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            schema = self._random_schema(rng, num_props)
            known = rng.random((NUM_AGENTS, num_props)) < 0.5
            orphan = schema.is_composite[None, :] & (rng.random((NUM_AGENTS, num_props)) < 0.5)

            agents_v, props_v = self._sorted(*_find_revelation_candidates(schema, known, orphan))
            agents_i, props_i = self._sorted(*iterative_revelation_candidates(schema, known, orphan))

            np.testing.assert_array_equal(agents_v, agents_i)
            np.testing.assert_array_equal(props_v, props_i)

    @staticmethod
    def _sorted(agents: np.ndarray, props: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        order = np.lexsort((props, agents))
        return agents[order], props[order]


def _find_revelation_candidates(schema, known, orphan):
    from freewill.mechanisms.orphan_revelation import find_revelation_candidates

    return find_revelation_candidates(schema, known, orphan)


class TestCompositeTrustCrossValidation:
    def _random_trust_and_schema(
        self, rng: np.random.Generator
    ) -> tuple[TrustStore, PropositionSchema]:
        schema = PropositionSchema(
            expr_type=np.array([ExprType.AXIOM, ExprType.AXIOM, ExprType.AND]),
            operand_left=np.array([NO_OPERAND, NO_OPERAND, 0]),
            operand_right=np.array([NO_OPERAND, NO_OPERAND, 1]),
        )
        trust = TrustStore(num_agents=NUM_AGENTS)
        for receiver in range(NUM_AGENTS):
            for publisher in range(NUM_AGENTS):
                for prop in (0, 1, 2):
                    if rng.random() < 0.3:
                        trust.set(
                            prop,
                            np.array([receiver]),
                            np.array([publisher]),
                            np.array([rng.uniform(-0.5, 0.5)]),
                        )
        return trust, schema

    def test_derived_targets_and_values_match_iterative_reference(self):
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            trust, schema = self._random_trust_and_schema(rng)

            # Read-only reference computed *before* the vectorized function mutates trust.
            exp_receivers, exp_publishers = iterative_composite_trust_targets(trust, schema, 2, NUM_AGENTS)
            expected_values = {}
            for r, p in zip(exp_receivers, exp_publishers):
                tau_left = trust.get(0, np.array([r]), np.array([p]))[0]
                tau_right = trust.get(1, np.array([r]), np.array([p]))[0]
                expected_values[(int(r), int(p))] = float(
                    resolve(np.array([ExprType.AND]), np.array([tau_left]), np.array([tau_right]))[0]
                )

            composite_trust.derive_missing_for_proposition(trust, schema, 2)

            for (r, p), expected_value in expected_values.items():
                assert trust.has_entry(2, np.array([r]), np.array([p]))[0]
                actual = trust.get(2, np.array([r]), np.array([p]))[0]
                assert actual == pytest.approx(expected_value, abs=1e-12)
