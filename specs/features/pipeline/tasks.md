---
status: draft
updated: 2026-08-25
---

# Tasks: pipeline

### TASK-001 - Pipeline document and schema
- satisfies: AC-002
- depends_on: workspace/TASK-001
- done_when: units and their order are stored on the workspace, round-trip through CT-009, and an
  unknown unit kind is rejected on open
- done: 2026-08-24, `src/service/pipeline/document.py` - MOD-011's first code. Units and their
  order live on the workspace and round-trip through CT-009's shape.
### TASK-002 - Editing with validation
- satisfies: AC-001
- depends_on: TASK-001
- done_when: dropping a workspace artefact or template adds a pinned, source-labelled definition
  reference or is refused with the reason, never leaving the pipeline invalid
- done: 2026-08-24. A drop is validated **before it lands**, so a pipeline is never briefly
  invalid - a state the editor would have to render and the user would have to interpret.
  A reference states whether it is a workspace item or a template and is never inferred from the
  identifier: the two have separate identity and lifecycle (XC-109), and guessing would silently follow
  whichever one still existed. A reference missing its revision is refused rather than filled in -
  **a revision this build supplied is a pin nobody chose**, and it would follow whatever the newest one
  happened to be on the day it ran.
### TASK-003 - A multiple selection becomes one case unit
- satisfies: AC-023
- depends_on: TASK-002
- done_when: dropping six selected cases produces exactly one case unit holding six
- done: 2026-08-24. Six units of one case each look the same on screen and behave differently the
  moment somebody reorders or removes one.
### TASK-004 - Unresolved definition-reference units
- satisfies: AC-003
- depends_on: TASK-002
- done_when: a unit whose workspace item, template or pinned revision is gone is kept and marked with
  the exact missing reference, and the run is refused until resolved
- done: 2026-08-24. The unit **stays** and the run is refused. Removing it would lose the user's
  work over somebody else's deletion; running without it would produce a study missing a step nobody
  noticed.
  The revision is part of the comparison: a reference that resolved to a different revision is a unit
  that would run something else.
### TASK-005 - Nesting limit
- satisfies: AC-020
- depends_on: TASK-002
- done_when: an edit exceeding the LIM-007 depth is refused and names the limit
- done: 2026-08-24. Refused at edit time naming LIM-007's three levels, and a refused edit leaves
  the pipeline exactly as it was rather than half-applied.
### TASK-006 - Depth counts loops, conditions and simulations alike
- satisfies: AC-025
- depends_on: TASK-005
- done_when: each containing kind consumes one level, asserted for all three
- done: 2026-08-24, asserted for all three. A depth rule that counted only loops would let a
  condition inside a simulation inside a loop through. The containing kinds are written out rather than
  derived from "has a units field", so adding one is a decision somebody makes rather than a side effect
  of a schema edit.
### TASK-007 - The target set
- satisfies: AC-004
- depends_on: TASK-001
- done_when: a case unit adds to the set and the size after each unit is reported
- done: 2026-08-24. Every unit that changes or reads the set writes a line, so "how many cases did
  this act on" is answerable afterwards rather than reconstructed from the pipeline and the case list.
### TASK-008 - Units act on the whole accumulated set
- satisfies: AC-005
- depends_on: TASK-007
- done_when: a view unit below two case units acts on the cases of both
- done: 2026-08-24, including cases added by earlier case units (AC-005).
### TASK-009 - Case units holding a selection
- satisfies: AC-006
- depends_on: TASK-007
- done_when: a selection resolves through CT-007 at run start and the resolved cases are listed

### TASK-010 - An empty target set skips rather than fails
- satisfies: AC-007
- depends_on: TASK-008
- done_when: a unit with nothing in the set is skipped, stated as empty, and the run continues
- done: 2026-08-24, stated and the run continues. A unit with nothing to do is not a failure, and
  stopping there would end a study because one branch happened to be empty.
### TASK-011 - The expression evaluator
- satisfies: AC-030
- depends_on: analysis module
- done_when: the language of 13_scripting.md evaluates without a Python interpreter, and the result
  carries the unit the expression produced
- done: 2026-08-25, `src/engine/analysis/expression.py` and `src/domain_core/dimension.py`.
  A tokeniser, a precedence-climbing parser and an evaluator, with **no `eval`, `exec` or `compile`** -
  asserted structurally against the module's own source, because a behavioural test only covers the
  attempts somebody thought of (XC-101).
  Units travel as a **dimension** rather than as a symbol (XC-242): a length over a time is
  `m·s^-1`, and Pa is reported as `Pa` rather than as the correct and unreadable `kg·m^-1·s^-2`.
  A value is held in the internal unit and **labelled with the internal unit**. The first version
  labelled it with the symbol the user wrote, so `max(1 MPa, 200 kPa)` printed `1e+06 MPa` while holding
  1e6 Pa - a number shown in one unit and labelled with another, which is the failure this product
  exists not to commit. Fixed by splitting the one field into two: `unit_name` is what the magnitude is
  in, `written_unit` is what to quote back in a refusal.
  The syntax is spelled the way the language table spells it - `and or not`, `**`, and `X if C else Y`.
  Chained comparisons are refused rather than reinterpreted: `a < b < c` reads as a range to a person
  and as `(a < b) < c` in the language the syntax comes from.
### TASK-012 - Incompatible units refused
- satisfies: AC-031
- depends_on: TASK-011
- done_when: a length added to a time is refused with both units named
- done: 2026-08-25, naming both (INV-002). The rule is dimensional rather than textual, so
  `1 MPa + 200 kPa` adds and `1 m + 1 s` is refused.
  Two refusals here cost the user something and were taken deliberately. **`stress > 200` is refused**
  because a threshold with no unit is the mistake that reads as correct - the comparison succeeds, the
  verdict prints, and whether it meant 200 Pa or 200 MPa is nowhere in the record (XC-003). And **a unit
  with an offset may not be multiplied**: doubling 20 degC gives 313.15 K one way and 586.3 K the other,
  and the gap is the offset itself (E-141), so any answer would be one the product invented. Subtracting
  two of them cancels the offsets and yields a difference, which may then be scaled.
### TASK-013 - Unbound references refused at edit time
- satisfies: AC-032
- depends_on: TASK-011
- done_when: an expression naming something not bound at that point is refused when it is written
- done: 2026-08-25. `check(source, bound=...)` parses, resolves every name against what is
  bound at that position, and checks each function's arity - before the run. A study that fails at
  midnight on a name somebody could have seen was wrong is the failure this removes.
  What it does **not** check is whether the units combine: that needs the values, and this pass has only
  the names. Said here rather than left to be discovered.
### TASK-014 - Variable and formula units
- satisfies: AC-029
- depends_on: TASK-011
- done_when: a binding is visible to the units below and leaves the workspace's own variables alone

### TASK-015 - Condition units
- satisfies: AC-033
- depends_on: TASK-011, TASK-008
- done_when: contents run when the expression is true and are skipped when it is false

### TASK-016 - A false condition is recorded, not omitted
- satisfies: AC-034
- depends_on: TASK-015
- done_when: skipped contents carry the value the expression evaluated to

### TASK-017 - Loop units
- satisfies: AC-026
- depends_on: TASK-008
- done_when: all three sources of the count work, the count is resolved before the loop starts, and
  which source was used is recorded

### TASK-018 - The loop index
- satisfies: AC-027
- depends_on: TASK-017
- done_when: contained units see the index under the declared name

### TASK-019 - The iteration ceiling
- satisfies: AC-028
- depends_on: TASK-017
- done_when: a count above LIM-008 is refused before the run, naming the unit and the count

### TASK-020 - Interpreter over the command surface
- satisfies: AC-021
- depends_on: TASK-008
- done_when: every unit executes as commands from CT-002, with no execution path that bypasses them

### TASK-021 - Dry run
- satisfies: AC-008
- depends_on: TASK-020
- done_when: the interpreter runs with execution disabled, reports the target set and artefacts per
  unit, and a test asserts the dry-run list equals what the real run then does
- done: 2026-08-24, `src/service/pipeline/run.py`. The dry-run list is asserted **equal to what the
  real run then does**, and the first version of that test failed: the plan credited the addCases unit
  with three cases and the run recorded it as acting on none. A dry run that describes a different
  execution from the one that follows is worse than no dry run, because the authorisation was given for
  the first one. Fixed at the structure - a step's `cases` is what it acts on, and the size of the
  target set afterwards is a separate `set_size`.
  `dry_run` has **no parameter** for the callable that performs a unit, so there is nothing for it to
  call even by mistake; the test asserts that rather than watching a callback stay untouched.
### TASK-022 - Dry run states loop counts and condition values
- satisfies: AC-024
- depends_on: TASK-021, TASK-017, TASK-015
- done_when: the dry run of a pipeline with loops and conditions states both
- done: 2026-08-24, both stated. Until TASK-015 and TASK-017 land the iteration count and the
  condition value are **supplied by the caller** rather than computed from the pipeline - the dry run
  states what it was told, and cannot yet derive it.
### TASK-023 - Destructive authorisation
- satisfies: AC-009
- depends_on: TASK-021
- done_when: a run with a clear unit requires one authorisation naming the unit and its case count
- done: 2026-08-24. One authorisation naming the unit and its case count (XC-094), produced from
  the dry run so the two figures cannot drift. Confirming per case is safer for one case and unusable
  for forty, which is how people learn to click through confirmations. An authorisation for three cases
  does not cover thirty: the number is what the user weighed.
  Which kinds are destructive is a stated list rather than a guess from the name, so a kind called
  `cleanup` does not become destructive by spelling.
### TASK-024 - Declined authorisation
- satisfies: AC-010
- depends_on: TASK-023
- done_when: declining runs the non-destructive units and reports the rest as not authorised
- done: 2026-08-24. Declining runs everything else and reports the destructive unit as not
  authorised (AC-010), rather than refusing the whole run for one step somebody declined.
### TASK-025 - Per-case failure isolation
- satisfies: AC-011
- depends_on: TASK-020
- done_when: a failing case skips its own remaining units and every other case completes
- done: 2026-08-24. XC-095's shape: forty cases with one truncated file produce thirty-nine
  results and one clear failure. The failed case skips **its own** remaining units - continuing within
  it would build a report on a state nobody checked.
### TASK-026 - No partial exports
- satisfies: AC-012
- depends_on: TASK-025
- done_when: a report whose input failed is not written, and the skip is recorded with its reason
- done: 2026-08-24. The skip is recorded with its reason and the reason is readable per case.
  A document with a hole in it is a document somebody sends.
### TASK-027 - Stop on first failure, when chosen
- satisfies: AC-013
- depends_on: TASK-025
- done_when: the chosen mode stops at the first failure and reports what was already written
- done: 2026-08-24. Continuing is the default and stopping is a mode somebody picks (AC-013);
  the record names the unit it stopped at and lists what had already been written.
### TASK-028 - Cancellation
- satisfies: AC-014
- depends_on: TASK-025
- done_when: cancelling stops at a unit boundary, keeps completed work, and names where it stopped
- done: 2026-08-24. Cancellation arrives at this layer as a **unit boundary** to stop after,
  keeping completed work and naming where it stopped.
### TASK-029 - Run record
- satisfies: AC-015
- depends_on: TASK-025
- done_when: pipeline, version, resolved cases, per-case per-unit outcome and target-set size are
  recorded
- done: 2026-08-24. Pipeline, revision, resolved cases, and one result per unit per case with
  its outcome and the target-set size it acted on. The record also holds the map from a produced case to
  the unit that produced it (TASK-031), which nothing fills yet because no unit produces cases until the
  simulation unit exists.
### TASK-030 - Reproducible reruns
- satisfies: AC-016
- depends_on: TASK-029
- done_when: a second run on the same inputs produces identical artefacts, asserted by comparison

### TASK-031 - Produced cases know their unit
- satisfies: AC-017
- depends_on: TASK-029
- done_when: a case produced by a run records the unit that produced it, readable from the case

### TASK-032 - The clear unit
- satisfies: AC-018
- depends_on: TASK-008
- done_when: the target set is emptied and loaded data released, with source files hash-identical
  before and after

### TASK-033 - Memory ceiling
- satisfies: AC-019
- depends_on: TASK-032
- done_when: exceeding the limit stops that case with required-versus-available stated, and the process
  survives

### TASK-034 - Headless entry point
- satisfies: AC-022
- depends_on: TASK-020, TASK-029
- done_when: a headless run reports machine-readable progress and outcome and exits non-zero when any
  case failed

### TASK-035 - The scripting object model
- satisfies: AC-035
- depends_on: TASK-001, TASK-020
- done_when: a script builds a pipeline document equal to one built by hand, asserted by comparison

### TASK-036 - Nothing stored executes itself
- satisfies: AC-036
- depends_on: TASK-035
- done_when: opening a workspace and running a stored pipeline both start no interpreter, asserted

### TASK-037 - Scripted changes are commands, and undo as one step
- satisfies: AC-037
- depends_on: TASK-035
- done_when: every change a script makes is in the log and one undo returns the prior state

### TASK-038 - Unattended execution is off by default
- satisfies: AC-038
- depends_on: TASK-035
- done_when: a fresh workspace refuses to run a script unattended, and enabling it is a per-workspace
  setting

### TASK-039 - Actions shown as script text
- satisfies: AC-039
- depends_on: TASK-020
- done_when: the script form of an action is produced from the command log and re-runs to the same state

### TASK-040 - Workspace held still during a run
- satisfies: AC-040
- depends_on: TASK-020
- done_when: viewing continues and edits are blocked with the reason stated

### TASK-041 - Artefacts deletable from the run record
- satisfies: AC-041
- depends_on: TASK-029
- done_when: the run record lists what it wrote and can delete it

### TASK-042 - Definition-reference source stays explicit
- satisfies: AC-042
- depends_on: TASK-002, TASK-004
- done_when: every artefact unit displays `workspaceItem` or `template` plus id and revision, and never
  infers the source or advances the revision automatically
