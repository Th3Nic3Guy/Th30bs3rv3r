"""Simulation state (PRD Section 4.1, resolved per docs/adr/0002-engine-state-representation.md).

Holds every structure the mechanism modules operate on:

- Belief (`belief`), internal-logic (`omega`), "has this agent ever formed a belief on I"
  (`known`), and "composite awaiting revelation" (`orphan`) — dense `agents x propositions`
  arrays (ADR 0002 Decision 1).
- Trust (`TrustStore`) — dict of per-proposition sparse `agents x agents` matrices, the
  publisher axis *is* the agent axis (ADR 0002 Decision 2; draft Section 3.8's SELF
  convention).
- The DAG (`PropositionSchema` + `DagAdjacency`) — static per domain.
- Per-agent coefficients, grid positions, Personal Affinity, influencer roles, and the
  per-(agent-pair) last-raised-topic memory `ell` (draft Section 4.12).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, lil_matrix

from freewill.mechanisms.fuzzy_resolution import ExprType

# Per-agent coefficient column order, matching draft Section 3.6's tuple
# (lambda, mu, eta, xi, sigma, chi, theta, pi, k*) and PRD Section 4.1's "agents x 9" table.
COEFFICIENT_COLUMNS = ["lambda", "mu", "eta", "xi", "sigma", "chi", "theta", "pi", "k_star"]

NO_OPERAND = -1  # sentinel for "this proposition has no left/right operand at this slot"


@dataclass
class PropositionSchema:
    """Static per-domain proposition structure (draft Sections 3.1, 4.3).

    `expr_type[i]` is one of `ExprType`; `operand_left`/`operand_right` are proposition
    indices (or `NO_OPERAND`). Per draft Section 3.8's binarization requirement, every
    composite is binary — n-ary composites must already be rewritten as nested binary
    nodes in the source axiom-hierarchy document before this schema is built.
    """

    expr_type: np.ndarray  # int, shape (num_propositions,)
    operand_left: np.ndarray  # int, shape (num_propositions,)
    operand_right: np.ndarray  # int, shape (num_propositions,)

    @property
    def num_propositions(self) -> int:
        return self.expr_type.shape[0]

    @property
    def is_axiom(self) -> np.ndarray:
        return self.expr_type == ExprType.AXIOM

    @property
    def is_composite(self) -> np.ndarray:
        return ~self.is_axiom


@dataclass
class DagAdjacency:
    """DAG adjacency, derived from one edge list so the antecedent and (row-normalized)
    consequent views (PRD 4.1's D and A) can never drift out of sync with each other.

    `raw_antecedent[I, I_a] = 1` iff `I_a` is an antecedent of `I` (I_a -> I in the DAG).
    `raw_consequent` is its transpose: `raw_consequent[I_a, I_c] = 1` iff `I_c` is a
    consequent of `I_a`. `consequent_normalized` (PRD 4.1's `D`) row-normalizes
    `raw_consequent` so each row sums to 1 (or is all-zero for a leaf with no consequents,
    draft Section 3.3's rho=0 convention) — used by reluctance.py's rho computation.
    """

    raw_antecedent: csr_matrix
    raw_consequent: csr_matrix
    consequent_normalized: csr_matrix

    @classmethod
    def from_edges(
        cls, antecedent_idx: np.ndarray, consequent_idx: np.ndarray, num_propositions: int
    ) -> DagAdjacency:
        """Build from parallel arrays of (antecedent, consequent) edges, i.e. edge k is
        `antecedent_idx[k] -> consequent_idx[k]`."""
        data = np.ones(len(antecedent_idx))
        raw_consequent = csr_matrix(
            (data, (antecedent_idx, consequent_idx)),
            shape=(num_propositions, num_propositions),
        )
        raw_antecedent = raw_consequent.T.tocsr()

        row_sums = np.asarray(raw_consequent.sum(axis=1)).ravel()
        row_sums_safe = np.where(row_sums == 0, 1.0, row_sums)
        inv_row_sums = 1.0 / row_sums_safe
        consequent_normalized = raw_consequent.multiply(inv_row_sums[:, None]).tocsr()

        return cls(
            raw_antecedent=raw_antecedent,
            raw_consequent=raw_consequent,
            consequent_normalized=consequent_normalized,
        )


class TrustStore:
    """Trust tensor as a dict of per-proposition sparse matrices (ADR 0002 Decision 2).

    `store[prop_id]` is an `agents x agents` matrix; row = receiving agent, column =
    publisher (source), diagonal = SELF-trust (draft Section 3.8). A proposition with no
    trust data yet simply has no key — callers use `get_row`/`has_entry` rather than
    assuming every proposition is present.
    """

    def __init__(self, num_agents: int) -> None:
        self.num_agents = num_agents
        self._store: dict[int, lil_matrix] = {}
        # Companion "has this (receiver, publisher) entry ever been set" mask, kept
        # separate from `_store`'s values so a trust value that has decayed to exactly
        # 0.0 is still distinguishable from "never initialized" (draft Section 3.3's
        # default-trust-initialization rule depends on exactly that distinction, and
        # relying on scipy sparse's implicit-zero elision to encode it would be fragile).
        self._known: dict[int, lil_matrix] = {}
        # Reverse index: (receiver, publisher) -> set of proposition ids that pair has an
        # entry for. draft Section 3.7's ad hominem/halo leak needs, for a touched pair,
        # "every other proposition I' the agent holds a trust value for regarding the
        # same source" — PRD 4.9 names this the one mechanism that is a genuinely
        # irregular per-pair gather with no shared precomputable structure (unlike the
        # DAG); this index is what makes that gather a dict lookup instead of a scan over
        # every proposition's matrix.
        self._pair_propositions: dict[tuple[int, int], set[int]] = {}
        # receiver -> set of publishers it has ever interacted with (any proposition).
        # This is N_A in draft Section 4.11's Personal Affinity — "every other agent A
        # has interacted with (and therefore holds trust data for)".
        self._known_neighbors: dict[int, set[int]] = {}

    def _matrix(self, prop_id: int) -> lil_matrix:
        if prop_id not in self._store:
            self._store[prop_id] = lil_matrix((self.num_agents, self.num_agents))
            self._known[prop_id] = lil_matrix((self.num_agents, self.num_agents), dtype=bool)
        return self._store[prop_id]

    def has_proposition(self, prop_id: int) -> bool:
        return prop_id in self._store

    def get_matrix(self, prop_id: int) -> lil_matrix | None:
        """Read-only access to a proposition's full matrix, or None if never touched."""
        return self._store.get(prop_id)

    def known_matrix(self, prop_id: int) -> lil_matrix | None:
        """Read-only access to a proposition's "has an entry" boolean mask, or None if
        never touched. `composite_trust.py`'s batched derivation (draft 3.9) uses this to
        find every (receiver, publisher) pair with trust on *both* of a composite's
        operands via one elementwise AND, rather than a per-pair scan."""
        return self._known.get(prop_id)

    def get(self, prop_id: int, receiver: np.ndarray, publisher: np.ndarray) -> np.ndarray:
        """Batched read of tau(publisher|prop_id) for a receiver, indexed by parallel
        arrays. Missing entries (never initialized) read as 0.0 — callers needing to
        distinguish "no trust data yet" from "trust is exactly 0" should check
        `has_entry` first (draft Section 3.3's default-trust-initialization rule fires
        exactly on that distinction)."""
        mat = self._store.get(prop_id)
        if mat is None:
            return np.zeros(len(receiver))
        # lil_matrix's paired fancy-index read (mat[rows, cols]) returns a 1xN sparse
        # submatrix, not a flat array -- .todense() before .ravel() is required, or
        # np.asarray() alone silently wraps the sparse object in a 0-d object array.
        return np.asarray(mat[receiver, publisher].todense()).ravel()

    def has_entry(self, prop_id: int, receiver: np.ndarray, publisher: np.ndarray) -> np.ndarray:
        known = self._known.get(prop_id)
        if known is None:
            return np.zeros(len(receiver), dtype=bool)
        return np.asarray(known[receiver, publisher].todense()).ravel()

    def set(self, prop_id: int, receiver: np.ndarray, publisher: np.ndarray, values: np.ndarray) -> None:
        """Batched overwrite of tau(publisher|prop_id) for a receiver."""
        mat = self._matrix(prop_id)
        mat[receiver, publisher] = values
        self._known[prop_id][receiver, publisher] = True
        for r, p in zip(receiver, publisher):
            r, p = int(r), int(p)
            self._pair_propositions.setdefault((r, p), set()).add(prop_id)
            self._known_neighbors.setdefault(r, set()).add(p)

    def propositions_for_pair(self, receiver: int, publisher: int) -> set[int]:
        """Every proposition (receiver, publisher) has a trust entry for — the leak
        target set in draft Section 3.7's ad hominem drift / halo-effect mechanism."""
        return self._pair_propositions.get((receiver, publisher), set())

    def known_neighbors(self, receiver: int) -> np.ndarray:
        """N_A (draft Section 4.11): every publisher `receiver` has ever interacted with
        (self included, if self-discovery has occurred — SELF is an ordinary entry per
        draft Section 3.8, so it is not filtered out here)."""
        return np.array(sorted(self._known_neighbors.get(receiver, set())), dtype=int)

    def known_count(self, prop_id: int, receiver: np.ndarray) -> np.ndarray:
        """Number of publishers each receiving agent has *any* trust entry for, on this
        proposition — the |P| in draft Section 3.2's alpha(I) formula."""
        known = self._known.get(prop_id)
        if known is None:
            return np.zeros(len(receiver), dtype=int)
        csr = known.tocsr()
        counts = np.diff(csr.indptr)
        return counts[receiver]

    def matvec(self, prop_id: int, vector: np.ndarray) -> np.ndarray:
        """`T[prop_id] @ vector` — the per-proposition matvec draft Section 3.2's alpha(I)
        reduces to (see trust_belief_update.py)."""
        mat = self._store.get(prop_id)
        if mat is None:
            return np.zeros(self.num_agents)
        return np.asarray(mat.tocsr().dot(vector)).ravel()


@dataclass
class SimulationState:
    """One run's full in-memory state."""

    run_id: str
    tick: int

    schema: PropositionSchema
    dag: DagAdjacency

    # Dense agents x propositions arrays (ADR 0002 Decision 1).
    belief: np.ndarray  # beta(I) per agent
    omega: np.ndarray  # omega(I) for revealed non-orphan composites; ignored for
    #                    axioms/orphans, where omega(I):=beta(I) by convention (draft 3.2/3.8)
    known: np.ndarray  # bool: has this agent ever formed a belief on I
    orphan: np.ndarray  # bool: composite, known, but not yet revealed (draft 3.8)
    k_assertions: np.ndarray  # k(I): count of the agent's own outgoing messages asserting I

    # Publisher-indexed (not receiver-indexed): agents x propositions. phi(I|P) is P's own
    # running mean stated confidence across all its messages on I, draft Section 3.2 --
    # a property of the publisher, independent of who received each message.
    phi: np.ndarray
    phi_message_count: np.ndarray  # for the running-mean update

    trust: TrustStore

    coefficients: pd.DataFrame  # agents x 9, columns = COEFFICIENT_COLUMNS (draft 3.6)
    smoothstep_degree: np.ndarray  # n = round(9*sigma) per agent (draft 3.5), cached

    grid_positions: np.ndarray  # agents x 2
    personal_affinity: np.ndarray  # agents x 2, recomputed every tick (draft 4.11)

    is_influencer: np.ndarray  # bool, agents
    influencer_agenda_proposition: np.ndarray  # int, agents (NO_OPERAND if not an influencer)
    influencer_agenda_confidence: np.ndarray  # float, agents (draft 4.6's nu_a)

    last_raised_topic: np.ndarray  # int, agents x agents; ell(A,P), draft 4.12 (NO_OPERAND = none)

    communication_matrix: csr_matrix | None = None  # rebuilt fresh every tick (draft 4.1, 4.6)

    @property
    def num_agents(self) -> int:
        return self.grid_positions.shape[0]

    @property
    def num_propositions(self) -> int:
        return self.schema.num_propositions

    def get_omega(self, agent_idx: np.ndarray, prop_idx: np.ndarray) -> np.ndarray:
        """omega(I) respecting the orphan/axiom convention (draft 3.2, 3.8): axioms and
        orphans read as identically equal to their own beta; only revealed, non-orphan
        composites read from the stored `omega` array."""
        use_beta = self.schema.is_axiom[prop_idx] | self.orphan[agent_idx, prop_idx]
        out = self.omega[agent_idx, prop_idx].copy()
        out[use_beta] = self.belief[agent_idx[use_beta], prop_idx[use_beta]]
        return out
