"""Fallacy extensions — FREE_WILL_draft.md Section 3.7.

Two entry points, mirroring PRD Section 4.2's tick loop:

- `apply_fallacy_extensions`: Section 3.7's four (or, if later formalized, more)
  fallacies as batched sparse operations over the tick's dirty set (tick step 4,
  PRD 4.2, 4.9) — vectorized.
- `apply_ad_hominem_halo_leak`: the ad hominem/halo-effect leak (tick step 5, PRD 4.2,
  4.9) — the *one* mechanism the PRD identifies as not vectorizable; a batched per-pair
  gather/scatter, run after the vectorized fallacy batch. This is the one place per-agent
  iteration is the primary path (PRD Section 2.1), not a fallback.
"""

from __future__ import annotations

from scipy.sparse import csr_matrix


def apply_fallacy_extensions(
    belief_matrix: csr_matrix,
    k_assertion_counts: csr_matrix,  # k(I), agents x propositions, PRD 4.1 / draft 3.7
    dirty_propositions: csr_matrix,
) -> csr_matrix:
    """Apply Section 3.7's fallacy extensions (excluding the ad hominem/halo leak) as a
    batched sparse operation over the tick's dirty set.

    TODO(draft 3.7): implement once FREE_WILL_draft.md Section 3.7's formulas are
    available in this repo. Per PRD Section 2.3, no formula is invented here ahead of the
    draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.7")


def apply_ad_hominem_halo_leak(
    trust_tensor: object,  # PRD 4.1
    colliding_pairs: list[tuple[int, int]],
) -> object:
    """Apply the ad hominem/halo-effect leak for this tick's colliding agent pairs.

    Deliberately per-pair (PRD Section 4.9): this is the one mechanism the design
    explicitly does not vectorize, run as a batched gather/scatter over `colliding_pairs`
    rather than a single global matmul.

    TODO(draft 3.7): implement once FREE_WILL_draft.md Section 3.7's ad hominem/halo-effect
    formula is available in this repo. Per PRD Section 2.3, no formula is invented here
    ahead of the draft.
    """
    raise NotImplementedError("pending FREE_WILL_draft.md Section 3.7 (ad hominem/halo leak)")
