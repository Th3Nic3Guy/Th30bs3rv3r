"""Tests for freewill.config.params.RunConfig — the run-time parameter schema, built
directly against FREE_WILL_draft.md Section 3.6 (per-agent coefficient distributions)
and the open items in Sections 3.7, 4.6, 4.10, 4.12 (PRD Section 5 / Section 11)."""

import pytest

from freewill.config.params import (
    AgentCoefficientDistributions,
    BetaSpec,
    PopulationStability,
    RunConfig,
    SeedingCondition,
    load_run_config,
)


def _base_kwargs(**overrides):
    kwargs = {
        "run_id": "run-0001",
        "domain": "climate",
        "seed": 42,
        "population_stability": PopulationStability.RANDOM,
        "seeding_condition": SeedingCondition.FULLY_RANDOM,
        "epsilon_explore": 0.1,
        "tau_still": 0.05,
        "influencer_reach": 30,
        "num_agents": 500,
    }
    kwargs.update(overrides)
    return kwargs


def test_round_trips_through_json():
    config = RunConfig(**_base_kwargs())
    restored = load_run_config(config.to_json())
    assert restored == config


def test_loads_from_dict():
    config = RunConfig(**_base_kwargs())
    restored = load_run_config(config.to_dict())
    assert restored.run_id == config.run_id


def test_draft_defaults_match_section_3_6_table():
    """draft 3.6: lambda/mu/sigma ~ Beta(2,2); eta ~ Beta(2,5); xi ~ Beta(2,4);
    chi ~ Beta(2,3) on [0,1]; theta/pi ~ Beta(2,2) on [1,3];
    k* ~ Beta(2,3) on [1,10], rounded."""
    coeffs = AgentCoefficientDistributions()
    assert coeffs.lambda_ == BetaSpec(a=2, b=2, low=0.0, high=1.0)
    assert coeffs.eta == BetaSpec(a=2, b=5, low=0.0, high=1.0)
    assert coeffs.xi == BetaSpec(a=2, b=4, low=0.0, high=1.0)
    assert coeffs.chi == BetaSpec(a=2, b=3, low=0.0, high=1.0)
    assert coeffs.theta == BetaSpec(a=2, b=2, low=1.0, high=3.0)
    assert coeffs.k_star == BetaSpec(a=2, b=3, low=1.0, high=10.0, round_to_int=True)


def test_influencer_reach_bounds_from_draft():
    # draft-specified range is 20-50 (draft Section 4.6 / PRD Section 11)
    with pytest.raises(ValueError):
        RunConfig(**_base_kwargs(influencer_reach=10))
    with pytest.raises(ValueError):
        RunConfig(**_base_kwargs(influencer_reach=60))


def test_epsilon_topic_defaults_to_tied_to_epsilon_explore():
    # draft 4.12 TODO: whether epsilon_topic is the same draw as epsilon_explore or an
    # independent coefficient is an open design fork; None is the "tied" reading.
    config = RunConfig(**_base_kwargs())
    assert config.epsilon_topic is None

    independent = RunConfig(**_base_kwargs(epsilon_topic=0.2))
    assert independent.epsilon_topic == 0.2


def test_beta_shape_overridable_for_robustness_check():
    custom = AgentCoefficientDistributions(chi=BetaSpec(a=5, b=5, low=0.0, high=1.0))
    config = RunConfig(**_base_kwargs(agent_coefficients=custom))
    assert config.agent_coefficients.chi.a == 5


def test_num_ticks_defaults_to_draft_1000():
    config = RunConfig(**_base_kwargs())
    assert config.num_ticks == 1000
