---
status: draft
updated: 2026-08-21
---

# Tasks: pipeline

### TASK-001 - Pipeline document and schema
- satisfies: AC-002
- depends_on: workspace/TASK-001
- done_when: units and their order are stored on the workspace, round-trip through CT-009, and an
  unknown unit kind is rejected on open

### TASK-002 - Editing with validation
- satisfies: AC-001
- depends_on: TASK-001
- done_when: dropping a workspace artefact or template adds a pinned, source-labelled definition
  reference or is refused with the reason, never leaving the pipeline invalid

### TASK-003 - A multiple selection becomes one case unit
- satisfies: AC-023
- depends_on: TASK-002
- done_when: dropping six selected cases produces exactly one case unit holding six

### TASK-004 - Unresolved definition-reference units
- satisfies: AC-003
- depends_on: TASK-002
- done_when: a unit whose workspace item, template or pinned revision is gone is kept and marked with
  the exact missing reference, and the run is refused until resolved

### TASK-005 - Nesting limit
- satisfies: AC-020
- depends_on: TASK-002
- done_when: an edit exceeding the LIM-007 depth is refused and names the limit

### TASK-006 - Depth counts loops, conditions and simulations alike
- satisfies: AC-025
- depends_on: TASK-005
- done_when: each containing kind consumes one level, asserted for all three

### TASK-007 - The target set
- satisfies: AC-004
- depends_on: TASK-001
- done_when: a case unit adds to the set and the size after each unit is reported

### TASK-008 - Units act on the whole accumulated set
- satisfies: AC-005
- depends_on: TASK-007
- done_when: a view unit below two case units acts on the cases of both

### TASK-009 - Case units holding a selection
- satisfies: AC-006
- depends_on: TASK-007
- done_when: a selection resolves through CT-007 at run start and the resolved cases are listed

### TASK-010 - An empty target set skips rather than fails
- satisfies: AC-007
- depends_on: TASK-008
- done_when: a unit with nothing in the set is skipped, stated as empty, and the run continues

### TASK-011 - The expression evaluator
- satisfies: AC-030
- depends_on: analysis module
- done_when: the language of 13_scripting.md evaluates without a Python interpreter, and the result
  carries the unit the expression produced

### TASK-012 - Incompatible units refused
- satisfies: AC-031
- depends_on: TASK-011
- done_when: a length added to a time is refused with both units named

### TASK-013 - Unbound references refused at edit time
- satisfies: AC-032
- depends_on: TASK-011
- done_when: an expression naming something not bound at that point is refused when it is written

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

### TASK-022 - Dry run states loop counts and condition values
- satisfies: AC-024
- depends_on: TASK-021, TASK-017, TASK-015
- done_when: the dry run of a pipeline with loops and conditions states both

### TASK-023 - Destructive authorisation
- satisfies: AC-009
- depends_on: TASK-021
- done_when: a run with a clear unit requires one authorisation naming the unit and its case count

### TASK-024 - Declined authorisation
- satisfies: AC-010
- depends_on: TASK-023
- done_when: declining runs the non-destructive units and reports the rest as not authorised

### TASK-025 - Per-case failure isolation
- satisfies: AC-011
- depends_on: TASK-020
- done_when: a failing case skips its own remaining units and every other case completes

### TASK-026 - No partial exports
- satisfies: AC-012
- depends_on: TASK-025
- done_when: a report whose input failed is not written, and the skip is recorded with its reason

### TASK-027 - Stop on first failure, when chosen
- satisfies: AC-013
- depends_on: TASK-025
- done_when: the chosen mode stops at the first failure and reports what was already written

### TASK-028 - Cancellation
- satisfies: AC-014
- depends_on: TASK-025
- done_when: cancelling stops at a unit boundary, keeps completed work, and names where it stopped

### TASK-029 - Run record
- satisfies: AC-015
- depends_on: TASK-025
- done_when: pipeline, version, resolved cases, per-case per-unit outcome and target-set size are
  recorded

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
