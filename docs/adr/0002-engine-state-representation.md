# ADR 0002: Engine state representation for M1

- **Status**: Accepted
- **Date**: 2026-08-31

## Context

`FREE_WILL_draft.md` is now in the repo (Sections 3–4). Implementing its mechanism
modules (PRD Section 4.3) against the actual formulas surfaces state-representation
questions PRD Section 4.1 left open pending M0's benchmarking spike — which this session
cannot run (no GCP infra access). Two decisions had to be made now to unblock M1 rather
than left open indefinitely:

## Decision 1: Belief (B) and internal-logic (Ω) matrices are dense NumPy, not sparse

PRD 4.1 specifies `scipy.sparse` for the belief matrix. In practice: at the draft's own
target scale (300–500 agents × the propositions in one domain's axiom hierarchy — order
tens to low hundreds of nodes, Section 4.3), a dense `agents × propositions` array of
`float64` is at most a few hundred thousand cells — a few MB. That's smaller than the
sparse-matrix bookkeeping overhead buys back, and dense arrays make the batched,
index-array-driven updates every mechanism module needs (fancy indexing over a tick's
"dirty set" of `(agent, proposition)` pairs) far simpler to get correct than mutating
`scipy.sparse` structures in place.

Belief and "has this agent ever formed a belief on I at all" are genuinely different
things (β=0 is a valid neutral belief; "never encountered" is not the same as β=0), so
`SimulationState` also carries an explicit boolean `known` mask (and an `orphan` mask for
composites awaiting revelation, draft Section 3.8) alongside `B` and `Ω`, rather than
overloading a sparse matrix's implicit zeros.

This does not touch PRD 4.1's `T` (trust tensor) — see Decision 2 — or the DAG adjacency
matrices, which are genuinely sparse and stay `scipy.sparse`.

## Decision 2: Trust tensor is `dict[proposition_id -> scipy.sparse matrix]`

This is PRD 4.1's own stated fallback option, adopted directly rather than benchmarked
against `pydata/sparse` (M0 remains open — see `docs/DEV_TASKLIST.md`). Trust actually is
sparse at any real scale (it requires two specific agents to have interacted on a specific
topic, PRD 4.1), and per-proposition `agents × agents` matrices keep every individual
operation on well-optimized 2D `scipy.sparse` code paths, exactly as PRD 4.1 argued.

**Sources are agents, not a separate axis.** `FREE_WILL_draft.md` Section 3.8 treats
`SELF` (an agent's trust in its own direct observation) as "an ordinary entry in the
publisher set P... not a special case." The natural implementation is that the publisher
axis of the trust tensor *is* the agent axis: `T[I][a, a]` (the diagonal) is agent `a`'s
self-trust on proposition `I`, and `T[I][a, p]` for `p != a` is `a`'s trust in agent `p`
as a source. This collapses PRD 4.1's three-axis tensor (agents × sources × propositions)
to a dict of square `agents × agents` matrices with no information lost, and needs no
special-cased SELF handling anywhere in `trust_belief_update.py` or `orphan_revelation.py`
— matching the draft's own stated intent.

## Consequences

- `freewill/engine/state.py`'s `SimulationState` is restructured around this: dense
  `belief`, `omega`, `known`, `orphan`, `k_assertions` arrays; `TrustStore` (the
  dict-of-sparse-matrix wrapper); a `PropositionSchema` (expression type + operand indices
  per proposition, needed by `fuzzy_resolution.py` for revelation and composite trust
  derivation); and `DagAdjacency` (raw + row-normalized consequent/antecedent matrices,
  both derived from one edge list).
- M0's benchmarking spike is still worth running before the full 3,030-run matrix (PRD
  Milestone M0), specifically to check Decision 1 holds at the largest domains' actual
  proposition counts — this ADR is a reasoned default to unblock M1, not a claim that
  benchmarking is now unnecessary.
