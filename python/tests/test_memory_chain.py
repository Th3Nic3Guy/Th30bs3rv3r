"""Tests for freewill.analysis.memory_chain (PRD Section 7.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from freewill.analysis.memory_chain import MemoryStep, build_memory_chain, read_memory_chain
from freewill.storage.event_log import Event, EventLogBuffer


def _event(agent_id, tick, event_type, **kwargs):
    return {"run_id": "run-1", "agent_id": agent_id, "tick": tick, "event_type": event_type, **kwargs}


class TestBuildMemoryChain:
    def test_filters_by_agent_id(self):
        events = [
            _event(0, 1, "discovery", proposition_id=5, new_value=0.2),
            _event(1, 1, "discovery", proposition_id=5, new_value=-0.1),
            _event(0, 2, "belief_update", mechanism="forward_flow", proposition_id=5, old_value=0.2, new_value=0.3),
        ]
        chain = build_memory_chain(events, agent_id=0)
        assert chain.agent_id == 0
        assert len(chain.steps) == 2
        assert all(s.tick in (1, 2) for s in chain.steps)

    def test_sorts_by_tick_even_if_input_is_out_of_order(self):
        events = [
            _event(0, 5, "belief_update", mechanism="forward_flow", proposition_id=1, new_value=0.1),
            _event(0, 1, "discovery", proposition_id=1, new_value=0.05),
            _event(0, 3, "trust_update", mechanism="alpha_flux", proposition_id=1, source_id=2, new_value=0.2),
        ]
        chain = build_memory_chain(events, agent_id=0)
        assert [s.tick for s in chain.steps] == [1, 3, 5]

    def test_run_id_defaults_from_first_matching_event(self):
        events = [_event(0, 1, "discovery", proposition_id=1, new_value=0.1)]
        chain = build_memory_chain(events, agent_id=0)
        assert chain.run_id == "run-1"

    def test_empty_when_agent_never_appears(self):
        events = [_event(1, 1, "discovery", proposition_id=1, new_value=0.1)]
        chain = build_memory_chain(events, agent_id=0)
        assert chain.steps == []


class TestTrajectories:
    def _chain(self):
        events = [
            _event(0, 1, "discovery", proposition_id=5, new_value=0.2),
            _event(0, 2, "trust_update", mechanism="alpha_flux", proposition_id=5, source_id=3, old_value=0.4, new_value=0.35),
            _event(0, 3, "belief_update", mechanism="forward_flow", proposition_id=5, old_value=0.2, new_value=0.28),
            _event(0, 4, "fallacy_triggered", mechanism="ad_hominem_halo_leak", proposition_id=5, source_id=3, old_value=0.35, new_value=0.3),
            _event(0, 5, "belief_update", mechanism="forward_flow", proposition_id=9, old_value=0.0, new_value=0.05),
            _event(0, 6, "revelation", mechanism="orphan_revelation", proposition_id=5, old_value=0.28, new_value=0.4),
        ]
        return build_memory_chain(events, agent_id=0)

    def test_belief_trajectory_includes_discovery_belief_update_and_revelation(self):
        chain = self._chain()
        traj = chain.belief_trajectory(5)
        assert [s.event_type for s in traj] == ["discovery", "belief_update", "revelation"]

    def test_belief_trajectory_excludes_other_propositions(self):
        chain = self._chain()
        traj = chain.belief_trajectory(5)
        assert all(s.proposition_id == 5 for s in traj)
        assert len(chain.belief_trajectory(9)) == 1

    def test_trust_trajectory_includes_trust_update_and_fallacy_triggered(self):
        chain = self._chain()
        traj = chain.trust_trajectory(5)
        assert [s.event_type for s in traj] == ["trust_update", "fallacy_triggered"]

    def test_trust_trajectory_filters_by_source_when_given(self):
        chain = self._chain()
        assert len(chain.trust_trajectory(5, source_id=3)) == 2
        assert len(chain.trust_trajectory(5, source_id=99)) == 0

    def test_known_propositions(self):
        chain = self._chain()
        assert chain.known_propositions() == {5, 9}


class TestExplain:
    def test_explain_includes_all_present_fields(self):
        step = MemoryStep(
            tick=3, event_type="belief_update", mechanism="forward_flow",
            proposition_id=5, source_id=2, old_value=0.2, new_value=0.28,
        )
        text = step.explain()
        assert "tick 3" in text
        assert "belief_update" in text
        assert "I=5" in text
        assert "from agent 2" in text
        assert "via forward_flow" in text
        assert "+0.2000" in text and "+0.2800" in text

    def test_explain_handles_missing_old_value(self):
        step = MemoryStep(
            tick=1, event_type="discovery", mechanism=None,
            proposition_id=5, source_id=0, old_value=None, new_value=0.2,
        )
        text = step.explain()
        assert "discovery" in text
        assert "-> +0.2000" in text

    def test_explain_all_matches_step_count(self):
        events = [
            _event(0, 1, "discovery", proposition_id=1, new_value=0.1),
            _event(0, 2, "belief_update", mechanism="forward_flow", proposition_id=1, old_value=0.1, new_value=0.15),
        ]
        chain = build_memory_chain(events, agent_id=0)
        assert len(chain.explain_all()) == 2


class TestReadMemoryChain:
    def test_round_trips_through_the_real_event_log_writer(self, tmp_path: Path):
        # Exercises the real Event/EventLogBuffer serialization (PRD 6.5), not just
        # hand-rolled dicts, to catch drift between what the engine writes and what this
        # module reads.
        staging = tmp_path / "events.jsonl"
        buf = EventLogBuffer(staging, flush_every=1)
        buf.record(Event(run_id="run-9", tick=0, agent_id=2, event_type="discovery", proposition_id=4, source_id=2, new_value=0.3))
        buf.record(Event(run_id="run-9", tick=1, agent_id=7, event_type="discovery", proposition_id=4, source_id=7, new_value=-0.1))
        buf.record(
            Event(
                run_id="run-9", tick=2, agent_id=2, event_type="trust_update", mechanism="alpha_flux",
                proposition_id=4, source_id=7, old_value=0.5, new_value=0.42,
            )
        )
        buf.close()

        chain = read_memory_chain(staging, agent_id=2)

        assert chain.run_id == "run-9"
        assert [s.event_type for s in chain.steps] == ["discovery", "trust_update"]
        assert chain.steps[1].old_value == pytest.approx(0.5)
        assert chain.steps[1].new_value == pytest.approx(0.42)

    def test_missing_agent_yields_empty_chain(self, tmp_path: Path):
        staging = tmp_path / "events.jsonl"
        buf = EventLogBuffer(staging, flush_every=1)
        buf.record(Event(run_id="run-9", tick=0, agent_id=1, event_type="discovery", proposition_id=4, new_value=0.1))
        buf.close()

        chain = read_memory_chain(staging, agent_id=999)
        assert chain.steps == []
