---
description: Change a specification value and the code that holds it, together, in one change
argument-hint: [item id, e.g. LIM-002 or INV-011]
---

Change $1 and everything that must move with it. A specification change and the code it describes ship
**together, in one change** — check 7 leaves the project red in either other order.

1. Read the item and everything that references it: `grep -rn "$1" specs/ src/ tests/ evidence/`.
2. If it is Fixed, find its `source_of_truth` and change the value in that one place.
3. If it carries a `basis:`, check the evidence still says what the item claims. **If a measurement
   contradicts the recorded conclusion, correct the conclusion and keep the record of the correction** —
   add a `correction:` line saying what was believed before and why it was wrong.
4. Refresh `updated:` on every spec file touched.
5. If this reverses a decision, record it in `specs/08_decisions.md` and mark the old one superseded.
   Never delete it: the next reader re-proposes the option that already lost.
6. Run the gates. Report what moved and what it cost.

If the change would make a Fixed value cite tier T3, or would put a number in the spec that nobody
measured, stop and say so. "This cannot be settled from available sources" is a result.
