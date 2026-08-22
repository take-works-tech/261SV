---
description: List the open questions with what would settle each, and which are actually blocking
---

Run `python validate/check_specs.py --report` and read the open questions it lists out of
`specs/08_decisions.md` and `specs/05_limits.md`.

For each, report in one line: the question, what would settle it (`resolve_by` / `closes_when`), and
whether it **blocks** anything today. Most do not — say so, because an Open that blocks nothing is not
urgent, and treating it as though it were crowds out the ones that are.

Then flag separately any Open whose text has gone **stale**: one that describes something as unmeasured
or undecided when the item it points at has since been settled. That has happened here before — OPEN-008
described LIM-002 as an assumption after E-063 measured it, including the exact problem it named as
outstanding. Cross-check each Open against the current state of every item in its `affects` list, and
check the reverse direction too: an item declaring `open: OPEN-nnn` that the Open does not list back.
