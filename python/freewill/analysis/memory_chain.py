"""Per-agent memory-chain reconstruction — PRD Section 7.4 (the source dissertation's
"Temporal Memory Model", its Figures 2-3).

Reconstructs one agent's temporal belief/trust evolution by filtering the event log for
that `agent_id` and replaying events in tick order — no new storage, "a query and
rendering feature over data already being collected" (PRD 7.4), which is exactly what
`build_memory_chain` below is: it reads the same JSON-lines event records
`freewill.storage.event_log.Event` already writes (PRD Section 6.5) and does nothing but
filter + sort + wrap them.

**The reasoning half.** Each event already carries a `mechanism` field naming which
mechanism produced it (arrival, `alpha_flux`, `forward_flow`, `orphan_revelation`,
`ad_hominem_halo_leak`, ...) — PRD Section 6.5's schema. `MemoryStep.explain()` turns
that into a one-line human-readable trace entry, so replaying an agent's chain doesn't
just show *that* a belief or trust value changed at some tick, but *why*, in the same
terms the mechanism modules and `docs/FREE_WILL_draft.md` use. This is the "reasoning
system" half of the memory-chain feature: it explains history already recorded, not a
live re-derivation from current DAG/trust state (that would be a different, forward-
looking feature — see `docs/DEV_TASKLIST.md` for the distinction, which was called out
explicitly when this module's scope was chosen).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# Event types that change belief(I) — the trajectory `belief_trajectory` follows.
_BELIEF_EVENT_TYPES = frozenset({"discovery", "belief_update", "revelation"})
# Event types that change trust(P|I) — the trajectory `trust_trajectory` follows.
_TRUST_EVENT_TYPES = frozenset({"trust_update", "fallacy_triggered"})


@dataclass(frozen=True)
class MemoryStep:
    """One event from an agent's own history, as recorded in the event log (PRD 6.5)."""

    tick: int
    event_type: str
    mechanism: str | None
    proposition_id: int | None
    source_id: int | None
    old_value: float | None
    new_value: float | None

    def explain(self) -> str:
        """One-line human-readable trace entry — the "reasoning" behind this step."""
        parts = [f"tick {self.tick}: {self.event_type}"]
        if self.proposition_id is not None:
            parts.append(f"I={self.proposition_id}")
        if self.source_id is not None:
            parts.append(f"from agent {self.source_id}")
        if self.mechanism:
            parts.append(f"via {self.mechanism}")
        if self.old_value is not None and self.new_value is not None:
            parts.append(f"({self.old_value:+.4f} -> {self.new_value:+.4f})")
        elif self.new_value is not None:
            parts.append(f"(-> {self.new_value:+.4f})")
        return " ".join(parts)


@dataclass(frozen=True)
class MemoryChain:
    """One agent's full recorded history for a run, in tick order."""

    run_id: str
    agent_id: int
    steps: list[MemoryStep]

    def belief_trajectory(self, proposition_id: int) -> list[MemoryStep]:
        """Every step that changed `belief(proposition_id)` for this agent, in tick
        order — the Temporal Memory Model's belief curve for one axiom (PRD 7.4)."""
        return [
            s for s in self.steps if s.proposition_id == proposition_id and s.event_type in _BELIEF_EVENT_TYPES
        ]

    def trust_trajectory(self, proposition_id: int, source_id: int | None = None) -> list[MemoryStep]:
        """Every step that changed `trust(source_id|proposition_id)` for this agent (or,
        if `source_id` is omitted, trust in *any* source on that proposition), in tick
        order."""
        return [
            s
            for s in self.steps
            if s.proposition_id == proposition_id
            and s.event_type in _TRUST_EVENT_TYPES
            and (source_id is None or s.source_id == source_id)
        ]

    def known_propositions(self) -> set[int]:
        """Every proposition this agent's history touches at all."""
        return {s.proposition_id for s in self.steps if s.proposition_id is not None}

    def explain_all(self) -> list[str]:
        """The full reasoning trace, one line per step, in tick order."""
        return [s.explain() for s in self.steps]


def build_memory_chain(events: Iterable[dict], agent_id: int, run_id: str = "") -> MemoryChain:
    """Filter `events` (already-parsed JSON-lines records, e.g. from `read_memory_chain`
    or a Cloud Storage download) for `agent_id` and replay in tick order (PRD 7.4).
    `run_id` is only used to label the resulting `MemoryChain`; if omitted it's taken
    from the first matching event, if any."""
    filtered = [e for e in events if e.get("agent_id") == agent_id]
    filtered.sort(key=lambda e: e["tick"])

    if not run_id and filtered:
        run_id = filtered[0].get("run_id", "")

    steps = [
        MemoryStep(
            tick=e["tick"],
            event_type=e["event_type"],
            mechanism=e.get("mechanism"),
            proposition_id=e.get("proposition_id"),
            source_id=e.get("source_id"),
            old_value=e.get("old_value"),
            new_value=e.get("new_value"),
        )
        for e in filtered
    ]
    return MemoryChain(run_id=run_id, agent_id=agent_id, steps=steps)


def _iter_jsonl(text: str) -> Iterable[dict]:
    for line in text.splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def read_memory_chain(path: str | Path, agent_id: int) -> MemoryChain:
    """Build a `MemoryChain` from a local JSON-lines event-log file — either the
    engine's own local staging file (`freewill.storage.event_log.EventLogBuffer`'s
    `staging_path`) or a downloaded copy of the Cloud Storage archive (PRD 6.5)."""
    text = Path(path).read_text()
    return build_memory_chain(_iter_jsonl(text), agent_id)


def read_memory_chain_from_gcs(bucket_name: str, run_id: str, agent_id: int, client=None) -> MemoryChain:
    """Build a `MemoryChain` directly from the Cloud Storage event-log archive (PRD
    6.5), without downloading the whole thing to disk first.

    Tries the single consolidated `{run_id}/events.jsonl` archive object PRD 6.5
    describes first; `go/cmd/logshipper` doesn't produce that yet (its own TODO notes
    the compaction step is still pending), so this falls back to reading every
    `{run_id}/batches/*.jsonl` object — the layout the log shipper actually writes today
    — concatenated in name order (which is tick-batch order, since batch sequence
    numbers are zero-padded).
    """
    from google.cloud import storage

    client = client or storage.Client()
    bucket = client.bucket(bucket_name)

    events: list[dict] = []
    consolidated = bucket.blob(f"{run_id}/events.jsonl")
    if consolidated.exists(client):
        events.extend(_iter_jsonl(consolidated.download_as_text()))
    else:
        blobs = sorted(client.list_blobs(bucket, prefix=f"{run_id}/batches/"), key=lambda b: b.name)
        for blob in blobs:
            events.extend(_iter_jsonl(blob.download_as_text()))

    return build_memory_chain(events, agent_id, run_id=run_id)
