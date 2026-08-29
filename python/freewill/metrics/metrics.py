"""Run-summary metrics (PRD Section 4.7, written to Cloud SQL per Section 6.4).

On run completion, `compute_run_metrics` produces the structured summary document
`RunRegistry.write_run_summary` (freewill.storage.run_registry) persists to the
`run_summaries` table. This is what the (out-of-scope, downstream) Section 4.8
statistical analysis plan consumes — not raw event logs or checkpoints (PRD 5.4/6.4).
"""

from __future__ import annotations

from dataclasses import dataclass

from freewill.engine.state import SimulationState


@dataclass
class RunMetrics:
    """PRD Section 4.7's metric set, one instance per completed run."""

    run_id: str
    saturation_curve: list[float]
    stabilization_tick: int | None
    polarization_bimodality: float
    polarization_variance: float
    belief_cluster_assignments: list[int]
    trust_cluster_assignments: list[int]
    nmi: float
    ari: float

    def to_dict(self) -> dict[str, object]:
        return {
            "saturation_curve": self.saturation_curve,
            "stabilization_tick": self.stabilization_tick,
            "polarization_bimodality": self.polarization_bimodality,
            "polarization_variance": self.polarization_variance,
            "belief_cluster_assignments": self.belief_cluster_assignments,
            "trust_cluster_assignments": self.trust_cluster_assignments,
            "nmi": self.nmi,
            "ari": self.ari,
        }


def compute_run_metrics(final_state: SimulationState, tick_history: list[SimulationState]) -> RunMetrics:
    """Compute Section 4.7's metrics from a completed run's final state and tick history.

    TODO(draft 4.7): implement once FREE_WILL_draft.md Section 4.7's metric definitions
    (saturation, stabilization, polarization indices, clustering) are available in this
    repo. Per PRD Section 2.3, no formula is invented here ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 4.7")
