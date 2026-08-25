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
- done: 2026-08-25. A case unit carries **either** an explicit list or a CT-007 selection, and
  holding both is refused: the two disagree precisely when a case was added after the pipeline was
  written, which is the case the selection form exists for, so which one wins is not something this
  product should decide on somebody's behalf.
  The selection is checked when the unit is written and resolved when the run starts, and both forms
  list what they resolved to before anything runs. A selection with **nothing to resolve against** is
  refused rather than resolved to nothing - an empty target set is a legitimate outcome that later units
  skip on (AC-007), and producing one from a missing argument would make it look like a study with no
  matching runs.
  The dry run resolves it as well, because a plan that could not say which cases a selection picks would
  be describing a different execution from the one that follows.
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
- done: 2026-08-25. A variable unit binds its name for the units below it and **leaves the
  workspace's own variables alone** unless it says otherwise: a pipeline that quietly rewrote one would
  change every other pipeline that reads it, and the change would be invisible from the pipeline that
  made it. A formula unit binds the result with the unit the expression produced (AC-030) - `span /
  duration` binds `0.05 m·s^-1`, not a number with a unit somebody typed beside it.
  A collision found and fixed at the cause: the quantity kind of INV-028 is written under
  **`quantityKind`**, because a unit already has a `kind` - `variable`, `formula`, `loop` - and handing
  the whole unit to a reader of quantity kinds made it read "variable" as a temperature scale and
  refuse. Two meanings of one word in one document is the kind of collision that stays invisible until
  it is a wrong number.
  A several-valued variable binds **nothing**: it is what a loop counts over, and outside that loop
  there is no single value its name could mean.
### TASK-015 - Condition units
- satisfies: AC-033
- depends_on: TASK-011, TASK-008
- done_when: contents run when the expression is true and are skipped when it is false
- done: 2026-08-25. Contents run when the expression is true and are skipped when it is
  false, with the condition's own value recorded either way.
### TASK-016 - A false condition is recorded, not omitted
- satisfies: AC-034
- depends_on: TASK-015
- done_when: skipped contents carry the value the expression evaluated to
- done: 2026-08-25. The skipped contents are recorded individually, each carrying the
  expression and the value it evaluated to (AC-034). Leaving them out of the record would make a report
  never written look identical to one never asked for, and the second is fine while the first needs
  somebody to look.
### TASK-017 - Loop units
- satisfies: AC-026
- depends_on: TASK-008
- done_when: all three sources of the count work, the count is resolved before the loop starts, and
  which source was used is recorded
- done: 2026-08-25. All three sources of the count work - a literal, the number of values a
  variable holds, and one iteration per case in the target set - and naming more than one is refused:
  accepting both would mean the product choosing which count a pipeline meant, and the two would
  disagree the day somebody edited only one of them.
  The count is resolved **before anything runs**, on the same pass the dry run uses, so the ceiling
  check and the plan cannot disagree. Which source was used is recorded: two loops that ran three times
  for different reasons behave differently the next time a case is added, and afterwards the record is
  the only place that difference survives.
### TASK-018 - The loop index
- satisfies: AC-027
- depends_on: TASK-017
- done_when: contained units see the index under the declared name
- done: 2026-08-25. Under the name the unit declares, and under `index` where it declares
  none - written in one place rather than defaulted at each reader, so a pipeline that omits the name
  still means one thing. The index leaves scope with the loop.
### TASK-019 - The iteration ceiling
- satisfies: AC-028
- depends_on: TASK-017
- done_when: a count above LIM-008 is refused before the run, naming the unit and the count
- done: 2026-08-25. Refused before the run starts, naming the unit and the count it
  resolved to (AC-028). Asserted with a run that would have acted: nothing was touched before the
  refusal.
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
- correction: 2026-08-25, and the caveat above is now wrong in both halves. The loop count and the
  condition value are **resolved from the document**, and the two parameters that let a caller supply
  them were removed rather than left as a second way to say it - a count passed in would be a second
  answer to a question XC-100 says the document settles, and the two would disagree the day somebody
  edited only one.
  What replaced the caveat is a narrower and truer one: a step **inside a loop** is reported as
  undetermined with the reason, because binding the index to its first value would let a formula and a
  condition there resolve to the answer for iteration zero, stated as though it were the answer for all
  of them. A condition reading `i > 0` would be planned as false and run as true twice out of three
  times - and the plan is what somebody authorises a destructive step against.
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
- done: 2026-08-25, `src/service/pipeline/reproduce.py`. Two runs of the same pipeline on the same
  inputs are compared by a canonical form of the run record with the timestamps removed - which is what
  AC-016's "save for recorded timestamps" needs in order to be checkable at all. The record now carries
  `started` and `finished`, so there is something real to exclude and the test can assert the two runs'
  times genuinely differed rather than passing on two records that recorded no time.
  **Nothing is sorted.** Two runs that acted on the same cases in a different order are not the same
  run, and a canonical form that tidied that away would report agreement where there is none.
  `differences` names where two runs part company rather than answering yes or no: a boolean is the
  least useful form of a correct answer, and what somebody needs is the unit. `digest` answers whether,
  in one comparison. Artefacts are compared by content and keyed by **file name**, because two runs
  write into two directories and a comparison keyed by absolute path reports every file as missing from
  the other side.
  The property is asserted for the failing runs too, not only the clean one - otherwise it holds only
  for the runs nobody needs to compare.
### TASK-031 - Produced cases know their unit
- satisfies: AC-017
- depends_on: TASK-029
- done_when: a case produced by a run records the unit that produced it, readable from the case

### TASK-032 - The clear unit
- satisfies: AC-018
- depends_on: TASK-008
- done_when: the target set is emptied and loaded data released, with source files hash-identical
  before and after
- done: 2026-08-25, `src/service/pipeline/memory.py`. A clear unit empties the target set and
  releases every case the run was holding, and the release is recorded on the unit.
  What "touches no source file" is verified by is narrow and worth stating: the ledger holds integers
  and case identifiers and names no path type at all, asserted against its own source. Hashing two files
  either side of a run confirms the behaviour; the structural check is what makes it stay true.
  Releasing a hold means the pipeline stops counting that case against the budget. It does not claim to
  free memory - a module reporting an outcome it cannot observe is worse than one that says less.
### TASK-033 - Memory ceiling
- satisfies: AC-019
- depends_on: TASK-032
- done_when: exceeding the limit stops that case with required-versus-available stated, and the process
  survives
- done: 2026-08-25. A hold past the budget is refused with **both** numbers - what was needed
  and what was available (AC-019) - and the refusal travels the path a per-case failure already travels,
  so the case stops, the rest of its units skip, and the study continues. The process returns a record
  rather than being killed, which is the whole point.
  `budget_bytes` and `size_of` are supplied together or not at all: a budget with nothing to measure
  measures nothing, and a size with no budget has nothing to refuse against. Neither is defaulted -
  see the correction below.
  A defect found here and fixed at the cause, before it could produce a wrong number: `limits.py` said
  in its module docstring that **every** constant in the file was the integrated-graphics class. That is
  right for LIM-002 and wrong for LIM-001, whose rationale is a 32 GB workstation - so this ceiling,
  the constant's first consumer, would have allowed a laptop twice what LIM-001 permits, in the
  direction that ends with the operating system killing the process. The one sentence for the whole file
  is now a statement per constant, the split is a table derived from the constant rather than a second
  literal, and `dataset_budget_bytes(machine)` makes asking for the budget require saying which machine
  it is for.
  Also fixed at the cause on the way past: the byte formatter existed **twice**, in
  `workspace/output.py` and `workspace/pack.py`, identical and both labelling binary steps with decimal
  names - 1 GiB printed as "1.0 GB". One implementation now, in `domain_core/locale_format.py`, spelling
  it the way the limits spell their own human values.
### TASK-034 - Headless entry point
- satisfies: AC-022
- depends_on: TASK-020, TASK-029
- done_when: a headless run reports machine-readable progress and outcome and exits non-zero when any
  case failed
- done: 2026-08-25, `src/service/pipeline/headless.py`. JSON Lines to standard output, one object
  per line, flushed per line (XC-243), and an exit code that answers one question: 0 when no case
  failed, 1 when one or more did, 2 when the run was refused before it started. Two rather than one for
  the refusal because "a case failed" and "the run never happened" are different facts to whatever is
  calling.
  Progress is emitted **while the run happens**. That needed one structural change: every result now
  reaches the record through a single function, so a watcher and the record cannot disagree. Thirteen
  call sites appended directly before; a fourteenth added later would have been invisible to the
  watcher, and the failure would be a headless run silently missing a step it did perform.
  The plan is emitted before the first unit, so the log is usable as the record of what was authorised
  rather than something reconstructed afterwards.
  **What this does not yet satisfy is the first half of AC-021.** The units are identical because this
  module calls the same `run` and holds no execution of its own - asserted against its own source - but
  "through the identical command surface" waits on TASK-020, which does not exist. The identity today is
  structural, not yet CT-002's.
### TASK-035 - The scripting object model
- satisfies: AC-035
- depends_on: TASK-001, TASK-020
- done_when: a script builds a pipeline document equal to one built by hand, asserted by comparison
- done: 2026-08-25, `src/service/scripting/model.py`. A script builds the same CT-009 document the
  editor builds, asserted by **equality** with one built by hand rather than by resemblance: two
  documents that look alike diverge on the first rule one of them enforces and the other does not.
  Every edit goes through MOD-011's own functions, so a pipeline a script builds is refused by exactly
  the rules that refuse one built by hand - a builder that assembled the dictionary itself would be a
  second implementation of the edit-time rules, and the copy would be the one that stopped refusing.
  XC-103's lookup rule is implemented here and it is where both reference products differ from this one:
  one appends a numeric suffix so `Cube` silently becomes `Cube.002` (E-064), the other returns every
  match so the documented idiom is to take the first and hope (E-067). This one refuses, naming what
  holds the name - the only one of the three that never quietly points a reference at the wrong object.
### TASK-036 - Nothing stored executes itself
- satisfies: AC-036
- depends_on: TASK-035
- done_when: opening a workspace and running a stored pipeline both start no interpreter, asserted
- done: 2026-08-25. Asserted structurally rather than behaviourally: a workspace arrives by
  email, and the claim is about what the code can do, not about the payloads somebody thought to try.
  No module anywhere under `src/` reaches `eval`, `exec`, `__import__` or `importlib` - swept over the
  whole tree rather than over a named list, so a module added later is covered without anybody
  remembering to add it. A stored pipeline carrying a `python` unit with code in it is refused because
  CT-009's set of unit kinds is closed, and the code is a string that never runs. An expression is
  evaluated by this product's own evaluator, which has no interpreter behind it (XC-101).
### TASK-037 - Scripted changes are commands, and undo as one step
- satisfies: AC-037
- depends_on: TASK-035
- done_when: every change a script makes is in the log and one undo returns the prior state
- done: 2026-08-25. Every call a script makes goes through MOD-012 with `Origin.SCRIPT` and the
  script's group id, so it is in the log and refused by the same rules as a click - there is no
  privileged form. One undo returns the prior state for the whole script (XC-061, XC-102), which is
  deliberately unlike the reference application, where operators called from Python skip the undo stack
  by default so a script does not push a step per operator (E-064). That trade suits a tool whose
  scripts run before anyone is watching; here the customer asks an agent to build forty reports and must
  be able to take it back.
  A script that only reads produces no log entry that can be undone and no undo step, which is why
  `sv.data` and `sv.ops` are separate rather than one object.
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
