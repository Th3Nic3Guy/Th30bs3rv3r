"""Message formulation — FREE_WILL_draft.md Section 4.12.

**Not in PRD Section 4.3's original module list** — that list predates
`FREE_WILL_draft.md` being in this repo (the PRD was written from the checklist/decisions
log alone). Section 4.12 is a real, separately-formalized mechanism the tick loop needs
(step 4 of draft 4.11's "Tick sequence, in full": "for each triggered conversation,
determine outgoing message content via Section 4.12"), so it gets its own module rather
than being folded into an existing one — `docs/FREE_WILL_PRD.md` Section 4.3 has been
updated to list it alongside the original ten.

Three-tier policy, in priority order: agenda override (draft 4.6, restated here as the
top branch) > exploit an established channel with this specific recipient > explore by
leading with one's own strongest belief.
"""

from __future__ import annotations

import numpy as np

from freewill.engine.state import NO_OPERAND
from freewill.mechanisms.influencer import agenda_override


def choose_message(
    rng: np.random.Generator,
    speaker: int,
    recipient: int,
    is_influencer: np.ndarray,
    agenda_proposition: np.ndarray,
    agenda_confidence: np.ndarray,
    known_topics: np.ndarray,
    belief_row: np.ndarray,
    last_raised_topic: np.ndarray,
    epsilon_topic: float,
) -> tuple[int, float]:
    """Choose (I_chosen, nu) for `speaker` addressing `recipient` this tick (draft 4.12).

    `known_topics` is the array of proposition indices `speaker` currently holds any
    belief on (`Topics(A)`); `belief_row` is `speaker`'s full belief row (indexed by
    proposition); `last_raised_topic[speaker, recipient]` is ell(A,P), `NO_OPERAND` if
    undefined (no prior interaction with this recipient).
    """
    override = agenda_override(is_influencer, agenda_proposition, agenda_confidence, speaker)
    if override is not None:
        return override

    prior_channel = int(last_raised_topic[speaker, recipient])
    explore = prior_channel == NO_OPERAND or rng.random() < epsilon_topic
    if explore:
        strongest = known_topics[np.argmax(np.abs(belief_row[known_topics]))]
        chosen = int(strongest)
    else:
        chosen = prior_channel

    nu = float(belief_row[chosen])
    return chosen, nu
