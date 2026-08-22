---
status: draft
updated: 2026-08-20
---

# Plan: pipeline

- approach: a pipeline is a document, and running it is an interpreter over the command surface. There
  is no second execution path: each unit becomes the same commands the interface issues, which is what
  makes headless, scripted and interactive runs identical rather than merely similar (INV-006). The
  interpreter carries one piece of state - the target set - and that single choice is what makes the
  editor readable top to bottom
- modules touched: MOD-011 pipeline, MOD-012 command, MOD-013 scripting, MOD-007 workspace, MOD-004
  analysis (the expression evaluator)
- contracts touched: CT-009 pipeline, CT-001 workspace document, CT-002 command surface
- technology: nothing new. The expression evaluator is the one that already computes derived
  quantities, reused rather than reimplemented - two evaluators would mean a formula that differs
  between a computed quantity and a pipeline formula, which is the sort of difference nobody finds
  until a report disagrees with a screen
- risks: three, in order. Memory across a long run is what ends a study at case twenty-nine. Per-case
  failure isolation is design, not tuning, and cannot be retrofitted onto a loop that stops. And the
  dry run only stays honest if it is the same interpreter with execution disabled - the moment it
  becomes a separate estimator it starts to drift, and it drifts exactly where the pipeline is complex

## Order of work

1. the document and its schema, with editing, validation and the depth limit (REQ-001, REQ-007)
2. the target set: case units, accumulation, clear, and the empty case (REQ-002)
3. the expression evaluator, shared with computed quantities (REQ-010)
4. conditions and loops over it, with the iteration ceiling (REQ-011, REQ-009)
5. the interpreter over the command surface, execution disabled - the dry run (REQ-003)
6. execution with per-case isolation and cancellation (REQ-004)
7. the run record, and the link from a produced @Case back to its unit (REQ-005)
8. the clear unit against the memory ceiling (REQ-006)
9. the headless entry point over the same interpreter (REQ-008)
10. the scripting object model, building the same document (REQ-012)

The dry run is built before execution deliberately: it is the cheapest possible way to be wrong about
what a pipeline does, and building it second would mean building it against an implementation rather
than against the contract. The evaluator comes before loops and conditions because both are expressed
in it, and a loop count that cannot be resolved before the run is a loop that cannot be dry-run.

Scripting comes last, and that ordering is the argument for the whole design: if the script surface can
only construct documents the editor could have constructed, it can be added at the end without changing
anything underneath. If it were an execution path of its own, it would have had to come first.

## What must be proven before this feature is called done

- a dry run's list of cases, artefacts, loop counts and condition values matches what a real run then
  does, asserted by test rather than by inspection
- a study where one case fails yields every other case's artefacts
- a pipeline built by script and one built by hand produce equal documents, and running either
  produces identical artefacts
- opening a workspace, and running a stored pipeline, start no Python interpreter
- a forty-case study completes within the memory ceiling with a clear unit in place, and reports rather
  than dies without it
