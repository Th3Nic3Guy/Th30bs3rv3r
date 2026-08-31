"""Unit tests for the mechanism modules' pure-math functions, checked against hand-worked
values from FREE_WILL_draft.md's own formulas (Sections 3.1, 3.3, 3.5, 3.7, 3.9)."""

import numpy as np
import pytest

from freewill.engine.state import NO_OPERAND, DagAdjacency, PropositionSchema, TrustStore
from freewill.mechanisms import composite_trust, fallacy_extensions, reluctance
from freewill.mechanisms.fuzzy_resolution import ExprType, resolve
from freewill.mechanisms.orphan_revelation import find_revelation_candidates
from freewill.mechanisms.smoothstep import degree_from_sigma, smoothstep


class TestFuzzyResolution:
    def test_and_is_min(self):
        out = resolve(np.array([ExprType.AND]), np.array([0.3]), np.array([-0.1]))
        assert out[0] == pytest.approx(-0.1)

    def test_or_is_max(self):
        out = resolve(np.array([ExprType.OR]), np.array([0.3]), np.array([-0.1]))
        assert out[0] == pytest.approx(0.3)

    def test_not_negates_left_only(self):
        out = resolve(np.array([ExprType.NOT]), np.array([0.3]), np.array([999.0]))
        assert out[0] == pytest.approx(-0.3)

    def test_implies_is_max_neg_left_right(self):
        # IMPLIES(x,y) = MAX(-x,y)
        out = resolve(np.array([ExprType.IMPLIES]), np.array([0.2]), np.array([0.1]))
        assert out[0] == pytest.approx(max(-0.2, 0.1))

    def test_batched_mixed_operators_in_one_call(self):
        out = resolve(
            np.array([ExprType.AND, ExprType.OR, ExprType.NOT, ExprType.IMPLIES]),
            np.array([0.1, 0.1, 0.1, 0.1]),
            np.array([0.4, 0.4, 0.0, 0.4]),
        )
        assert out == pytest.approx([0.1, 0.4, -0.1, 0.4])

    def test_axiom_raises(self):
        with pytest.raises(ValueError):
            resolve(np.array([ExprType.AXIOM]), np.array([0.1]), np.array([0.1]))


class TestSmoothstep:
    def test_clamps_outside_range(self):
        assert smoothstep(np.array([-2.0]), n=0)[0] == -0.5
        assert smoothstep(np.array([2.0]), n=0)[0] == 0.5

    def test_boundary_values_exact(self):
        assert smoothstep(np.array([-0.5]), n=5)[0] == pytest.approx(-0.5)
        assert smoothstep(np.array([0.5]), n=5)[0] == pytest.approx(0.5)

    def test_zero_maps_to_zero_for_every_degree(self):
        for n in range(10):
            assert smoothstep(np.array([0.0]), n=n)[0] == pytest.approx(0.0, abs=1e-12)

    def test_degree_zero_is_linear(self):
        # n=0's generalized-smoothstep polynomial collapses to the identity ramp.
        x = np.array([-0.3, 0.0, 0.25])
        assert smoothstep(x, n=0) == pytest.approx(x)

    def test_degree_one_is_canonical_cubic_smoothstep(self):
        # S_1 on [0,1] is the textbook 3u^2 - 2u^3; shifted here to [-0.5,0.5].
        x = 0.2
        u = x + 0.5
        expected = (3 * u**2 - 2 * u**3) - 0.5
        assert smoothstep(np.array([x]), n=1)[0] == pytest.approx(expected)

    def test_handles_per_element_degree_batch(self):
        out = smoothstep(np.array([0.2, 0.2]), n=np.array([0, 1]))
        assert out[0] != pytest.approx(out[1])  # different n -> different curve

    def test_degree_from_sigma_matches_draft_formula(self):
        # n = round(9*sigma), draft 3.5
        assert list(degree_from_sigma(np.array([0.0, 1.0, 0.5]))) == [0, 9, round(9 * 0.5)]


class TestReluctance:
    def _simple_dag(self):
        # I0 -> I2, I1 -> I2 (I2's antecedents are I0, I1; I0 and I1's only consequent is I2)
        return DagAdjacency.from_edges(np.array([0, 1]), np.array([2, 2]), num_propositions=3)

    def test_rho_averages_consequent_belief(self):
        dag = self._simple_dag()
        belief = np.array([[0.2, 0.4, 0.0]])  # one agent
        rho = reluctance.compute_rho(belief, dag)
        # I0's only consequent is I2 (belief 0.0) -> rho(I0) = 0.0
        assert rho[0, 0] == pytest.approx(0.0)
        # I2 has no consequents -> rho(I2) = 0 by the leaf convention (draft 3.3)
        assert rho[0, 2] == pytest.approx(0.0)

    def test_gamma_is_one_at_rho_zero(self):
        gamma = reluctance.compute_gamma(np.array([[0.0]]), xi=np.array([0.5]))
        assert gamma[0, 0] == pytest.approx(1.0)

    def test_gamma_never_below_one(self):
        rho = np.array([[-0.4, 0.0, 0.3]])
        gamma = reluctance.compute_gamma(rho, xi=np.array([0.3]))
        assert np.all(gamma >= 1.0)

    def test_reluctance_damped_update_divides_not_smoothsteps(self):
        beta_prev = np.array([0.1])
        delta = np.array([0.2])
        gamma = np.array([2.0])
        out = reluctance.apply_reluctance_damped_update(beta_prev, delta, gamma)
        assert out[0] == pytest.approx(0.1 + 0.2 / 2.0)

    def test_default_trust_init_decays_with_more_known_sources(self):
        eta = np.array([0.3, 0.3])
        first = reluctance.default_trust_init(np.array([0.0]), eta[:1])[0]
        later = reluctance.default_trust_init(np.array([5.0]), eta[:1])[0]
        assert first > later > 0
        assert first <= 0.5


class TestFallacyExtensions:
    def test_negativity_bias_only_amplifies_negative_deltas(self):
        delta = np.array([-0.1, 0.1])
        theta = np.array([2.0, 2.0])
        out = fallacy_extensions.apply_negativity_bias(delta, theta)
        assert out[0] == pytest.approx(-0.2)
        assert out[1] == pytest.approx(0.1)

    def test_doubling_down_defiance_requires_all_three_conditions(self):
        delta_prime = np.array([0.1, 0.1, 0.1, 0.1])
        pi = np.array([3.0, 3.0, 3.0, 3.0])
        tau = np.array([-0.1, 0.1, -0.1, -0.1])  # only rows 0,2,3 have tau<0
        disagreement = np.array([True, True, False, True])
        k = np.array([5, 5, 5, 1])
        k_star = np.array([3, 3, 3, 3])
        out = fallacy_extensions.apply_doubling_down_defiance(delta_prime, pi, tau, disagreement, k, k_star)
        # row 0: tau<0, disagree, k>=k* -> amplified
        assert out[0] == pytest.approx(0.3)
        # row 1: tau not < 0 -> unchanged
        assert out[1] == pytest.approx(0.1)
        # row 2: no disagreement -> unchanged
        assert out[2] == pytest.approx(0.1)
        # row 3: k < k* -> unchanged
        assert out[3] == pytest.approx(0.1)

    def test_is_disagreement_compares_signs(self):
        out = fallacy_extensions.is_disagreement(np.array([0.2, -0.2]), np.array([-0.1, -0.1]))
        assert list(out) == [True, False]


class TestCompositeTrust:
    def _schema(self, expr_type: ExprType) -> PropositionSchema:
        # prop 0, 1 are axioms (operands); prop 2 is the composite under test.
        return PropositionSchema(
            expr_type=np.array([ExprType.AXIOM, ExprType.AXIOM, expr_type]),
            operand_left=np.array([NO_OPERAND, NO_OPERAND, 0]),
            operand_right=np.array([NO_OPERAND, NO_OPERAND, 1]),
        )

    def test_derives_for_pair_known_on_both_operands(self):
        schema = self._schema(ExprType.AND)
        trust = TrustStore(num_agents=3)
        # receiver 0's trust in publisher 1 on both operands.
        trust.set(0, np.array([0]), np.array([1]), np.array([0.4]))
        trust.set(1, np.array([0]), np.array([1]), np.array([-0.1]))

        composite_trust.derive_missing_for_proposition(trust, schema, 2)

        assert trust.has_entry(2, np.array([0]), np.array([1]))[0]
        # AND(x,y) = MIN(x,y) -- draft Table 1.
        assert trust.get(2, np.array([0]), np.array([1]))[0] == pytest.approx(min(0.4, -0.1))

    def test_does_not_derive_when_only_one_operand_known(self):
        schema = self._schema(ExprType.OR)
        trust = TrustStore(num_agents=3)
        trust.set(0, np.array([0]), np.array([1]), np.array([0.4]))
        # No trust set on operand 1 for this pair.

        composite_trust.derive_missing_for_proposition(trust, schema, 2)

        assert not trust.has_entry(2, np.array([0]), np.array([1]))[0]

    def test_does_not_overwrite_an_existing_direct_entry(self):
        schema = self._schema(ExprType.AND)
        trust = TrustStore(num_agents=3)
        trust.set(0, np.array([0]), np.array([1]), np.array([0.4]))
        trust.set(1, np.array([0]), np.array([1]), np.array([-0.1]))
        trust.set(2, np.array([0]), np.array([1]), np.array([0.25]))  # already-established direct trust

        composite_trust.derive_missing_for_proposition(trust, schema, 2)

        # Derivation must not clobber a direct entry with the structural fallback.
        assert trust.get(2, np.array([0]), np.array([1]))[0] == pytest.approx(0.25)

    def test_noop_for_axiom(self):
        schema = self._schema(ExprType.AND)
        trust = TrustStore(num_agents=3)
        trust.set(0, np.array([0]), np.array([1]), np.array([0.4]))
        # prop 0 is itself an axiom -- calling on it must not raise or do anything.
        composite_trust.derive_missing_for_proposition(trust, schema, 0)
        assert trust.get_matrix(0) is not None  # unchanged, still just the one entry set above

    def test_derives_for_not_composite_from_left_operand_only(self):
        # NOT is unary (draft Table 1): operand_right is NO_OPERAND by construction.
        # Regression test for a bug where requiring "both operands known" (the AND/OR/
        # IMPLIES reading) meant a NOT composite could never derive trust at all.
        schema = PropositionSchema(
            expr_type=np.array([ExprType.AXIOM, ExprType.NOT]),
            operand_left=np.array([NO_OPERAND, 0]),
            operand_right=np.array([NO_OPERAND, NO_OPERAND]),
        )
        trust = TrustStore(num_agents=3)
        trust.set(0, np.array([0]), np.array([1]), np.array([0.3]))

        composite_trust.derive_missing_for_proposition(trust, schema, 1)

        assert trust.has_entry(1, np.array([0]), np.array([1]))[0]
        assert trust.get(1, np.array([0]), np.array([1]))[0] == pytest.approx(-0.3)


class TestOrphanRevelationCandidates:
    def test_and_composite_needs_both_operands_known(self):
        schema = PropositionSchema(
            expr_type=np.array([ExprType.AXIOM, ExprType.AXIOM, ExprType.AND]),
            operand_left=np.array([NO_OPERAND, NO_OPERAND, 0]),
            operand_right=np.array([NO_OPERAND, NO_OPERAND, 1]),
        )
        known = np.array([[True, False, False]])  # only operand 0 known
        orphan = np.array([[False, False, True]])
        agents, props = find_revelation_candidates(schema, known, orphan)
        assert len(agents) == 0

        known = np.array([[True, True, False]])  # both operands now known
        agents, props = find_revelation_candidates(schema, known, orphan)
        assert list(zip(agents, props)) == [(0, 2)]

    def test_not_composite_triggers_off_left_operand_alone(self):
        # Regression test: requiring right != NO_OPERAND too (the AND/OR reading) meant a
        # NOT composite could never be revealed, since its operand_right is always
        # NO_OPERAND.
        schema = PropositionSchema(
            expr_type=np.array([ExprType.AXIOM, ExprType.NOT]),
            operand_left=np.array([NO_OPERAND, 0]),
            operand_right=np.array([NO_OPERAND, NO_OPERAND]),
        )
        known = np.array([[True, False]])
        orphan = np.array([[False, True]])
        agents, props = find_revelation_candidates(schema, known, orphan)
        assert list(zip(agents, props)) == [(0, 1)]

    def test_axiom_never_triggers(self):
        schema = PropositionSchema(
            expr_type=np.array([ExprType.AXIOM]),
            operand_left=np.array([NO_OPERAND]),
            operand_right=np.array([NO_OPERAND]),
        )
        known = np.array([[True]])
        orphan = np.array([[False]])  # axioms are never orphaned in the first place
        agents, _props = find_revelation_candidates(schema, known, orphan)
        assert len(agents) == 0
