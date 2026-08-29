"""Cross-validation of the vectorized tick loop against the iterative reference oracle
(PRD Section 4.4). CI runs this on every change to a mechanism module.

Currently skipped: both sides depend on FREE_WILL_draft.md's mechanism formulas, which
are not yet part of this repo (PRD Section 2.3 forbids guessing them). Once a mechanism
module is implemented against the draft, un-skip and extend this test to assert exact
numerical agreement between freewill.engine.run_tick and
freewill.validation.run_iterative_reference on identical seeds, for a small (10-20 agent)
population, per PRD Section 4.4.
"""

import pytest


@pytest.mark.skip(reason="pending FREE_WILL_draft.md mechanism formulas (PRD Section 2.3)")
def test_vectorized_matches_iterative_reference_on_small_population():
    ...
