"""Event log (PRD Section 6.5).

The simulation engine appends one JSON-lines record per state-changing event to a local
buffer during the tick loop (PRD 4.2 step 6) — no per-event network I/O. The buffer is
flushed periodically; the Go log shipper (go/cmd/logshipper) is responsible for the
durable path (Cloud Logging structured entries + a Cloud Storage archive object) in
production runs. This module owns the local buffer and its on-disk staging file only.

event_type values: discovery, revelation, message_received, trust_update, belief_update,
flowback, movement, fallacy_triggered (PRD 6.5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

EventType = Literal[
    "discovery",
    "revelation",
    "message_received",
    "trust_update",
    "belief_update",
    "flowback",
    "movement",
    "fallacy_triggered",
]


@dataclass
class Event:
    run_id: str
    tick: int
    agent_id: int
    event_type: EventType
    mechanism: str | None = None
    proposition_id: int | None = None
    source_id: int | None = None
    old_value: float | None = None
    new_value: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        record = {
            "run_id": self.run_id,
            "tick": self.tick,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "mechanism": self.mechanism,
            "proposition_id": self.proposition_id,
            "source_id": self.source_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            **self.extra,
        }
        return json.dumps({k: v for k, v in record.items() if v is not None})


class EventLogBuffer:
    """Local, append-only JSON-lines staging file for one run's events.

    Flushed to disk incrementally (`flush_every` events) so a crashed instance loses at
    most a partial batch, and periodically handed off (by run-tick number, not by this
    class) to the log shipper for upload. This class does not talk to GCP directly — see
    go/cmd/logshipper and PRD Section 6.5 for the durable path.
    """

    def __init__(self, staging_path: Path, flush_every: int = 500) -> None:
        self._path = staging_path
        self._flush_every = flush_every
        self._pending: list[Event] = []
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: Event) -> None:
        self._pending.append(event)
        if len(self._pending) >= self._flush_every:
            self.flush()

    def flush(self) -> None:
        if not self._pending:
            return
        with self._path.open("a", encoding="utf-8") as f:
            for event in self._pending:
                f.write(event.to_json())
                f.write("\n")
        self._pending.clear()

    def close(self) -> None:
        self.flush()
