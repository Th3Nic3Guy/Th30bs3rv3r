"""Simulation state tensors (PRD Section 4.1).

Holds exactly the structures PRD Section 4.1's table lists. No structure here should be
added speculatively — every field traces to that table, which in turn traces to specific
draft sections.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


@dataclass
class SimulationState:
    """One run's full in-memory state, per PRD Section 4.1's table.

    Attributes:
        belief_matrix: B, agents x propositions, csr_matrix (draft 3.2-3.3, 4.9).
        trust_tensor: T, agents x sources x propositions. `pydata/sparse` array or the
            per-proposition dict-of-csr fallback (PRD 4.1 implementation note) — the
            benchmarking spike (PRD Milestone 0) decides which; kept as `object` here so
            the state container doesn't hardcode that decision.
        dag_consequent: D, propositions x propositions, row-normalized (draft 3.3).
        dag_antecedent: A, propositions x propositions (draft 4.2).
        communication_matrix: C, agents x agents, 0/1. Rebuilt fresh every tick (draft
            4.1, 4.6) — not persisted across ticks, so it is not part of a checkpoint
            (PRD 6.2).
        grid_positions: agents x 2, dense (draft 4.11).
        personal_affinity: agents x 2, dense, recomputed every tick (draft 4.11).
        coefficient_table: agents x 9 (lambda, mu, eta, xi, sigma, chi, theta, pi, k*),
            dense (draft 3.6). Stored as a pandas DataFrame so it round-trips directly to
            the checkpoint's Parquet sidecar (PRD 6.2).
        k_assertion_counts: k(I), agents x propositions, sparse (draft 3.7).
    """

    run_id: str
    tick: int

    belief_matrix: csr_matrix
    trust_tensor: object
    dag_consequent: csr_matrix
    dag_antecedent: csr_matrix
    communication_matrix: csr_matrix | None
    grid_positions: np.ndarray
    personal_affinity: np.ndarray
    coefficient_table: pd.DataFrame
    k_assertion_counts: csr_matrix

    @property
    def num_agents(self) -> int:
        return self.grid_positions.shape[0]

    @property
    def num_propositions(self) -> int:
        return self.belief_matrix.shape[1]
