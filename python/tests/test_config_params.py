"""Tests for freewill.config.params.RunConfig — the run-time parameter schema (PRD
Section 5 / Section 11). These are the only tests that don't depend on mechanism
formulas not yet in this repo, so they're a reasonable smoke test for the scaffold."""

import pytest

from freewill.config.params import BetaShapeConfig, RunConfig, load_run_config


def _base_kwargs(**overrides):
    kwargs = {
        "run_id": "run-0001",
        "domain": "climate",
        "seed": 42,
        "chi_range": (0.1, 0.9),
        "theta_range": (0.0, 1.0),
        "pi_range": (0.2, 0.8),
        "epsilon_explore": 0.1,
        "tau_still": 0.5,
        "influencer_reach": 30,
        "num_agents": 500,
        "num_ticks": 1000,
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


def test_rejects_inverted_range():
    with pytest.raises(ValueError):
        RunConfig(**_base_kwargs(chi_range=(0.9, 0.1)))


def test_influencer_reach_bounds_from_draft():
    # draft-specified range is 20-50 (PRD Section 4.6 / 11)
    with pytest.raises(ValueError):
        RunConfig(**_base_kwargs(influencer_reach=10))
    with pytest.raises(ValueError):
        RunConfig(**_base_kwargs(influencer_reach=60))


def test_optional_beta_shape_for_robustness_check_runs():
    config = RunConfig(**_base_kwargs(beta_shape=BetaShapeConfig(alpha=2.0, beta=5.0)))
    assert config.beta_shape.alpha == 2.0

    default_config = RunConfig(**_base_kwargs())
    assert default_config.beta_shape is None
