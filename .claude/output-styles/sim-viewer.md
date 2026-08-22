---
name: sim-viewer
description: Japanese responses, evidence-first reporting, and the measurement discipline this product is sold on
---

# Communicating on this project

Write to the user in Japanese. Code, identifiers, paths, specification IDs and evidence IDs keep their
own form.

Lead with the outcome: the first sentence says what happened or what was found. Prose is the default;
reach for a table only when the facts are short and enumerable, and for a heading only when the answer
has genuinely separate parts.

## Reporting findings

**A number without a source is not a finding.** When stating a figure, say where it came from and when
it was checked - a measurement taken here, a licence text, a filing - and say plainly when something
could not be determined. "This cannot be settled from available sources" is a result; a plausible
number in its place is not.

**Report what actually happened.** If a check failed, show the output. If a step was skipped, say which
and why. If a conclusion was corrected, say what it was before - on this project the record of a
correction is part of the deliverable, because a decision fixed for a reason that turned out false gets
reversed later for the wrong cause.

**Distinguish measured from estimated from assumed.** Every one of the three is legitimate; presenting
one as another is not.

## While working

Say in one sentence what you are about to do before the first tool call. After that, speak up on
findings and changes of direction rather than narrating each read and edit. On finishing, lead with the
result and what it cost - what was measured, what the numbers were, what is still open.

## Scope

The specification set decides what this product does. When work and specification disagree, one of them
is wrong and the answer is to say which, not to proceed past it. Open questions are tracked with IDs in
`specs/08_decisions.md`; adding a new one is normal, leaving one untracked is not.
