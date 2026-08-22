---
status: draft
updated: 2026-08-21
---

# Feature: pipeline

## Users and purpose

- intended user: an analysis engineer who has settled how one result should be looked at, and now has
  forty of them
- job to be done: register that flow once - these views, these graphs, this report - and have it run
  for every result, including results that do not exist yet
- success condition: a study of forty results produces forty sets of figures and one report without the
  user repeating a single action, and a reviewer can read afterwards exactly what ran
- **it works with no simulation.** The entry point is cases the @Workspace already holds; producing
  cases from a solver is a later release (XC-091) whose unit pins one saved @Simulation flow and adds
  the resulting cases to the target set (XC-154), not a precondition

## Out of scope

- unbounded repetition: there is no `while` and no user-written break (XC-100)
- an expression language that can reach the object model, import, define functions or write anything
  (XC-101)
- scheduling - a pipeline is started, not triggered by a clock
- storing Python as the pipeline: a script builds the declarative document, and that is what is saved
  (XC-102)

## Files and interfaces involved

- the pipeline contract and its schema (CT-009), stored on the @Workspace document (CT-001)
- the command surface every unit goes through (CT-002), and the dry-run mode of CT-003
- the scripting surface and the expression language ([../../13_scripting.md](../../13_scripting.md))
- MOD-011 pipeline, MOD-012 command, MOD-013 scripting, MOD-007 workspace
- the dedicated Automation work area, its pipeline list, central editor and right-side unit/property
  rail in [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - A pipeline is built by editing, not by recording
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-001: When the user drags a workspace @View, @Graph or @Report or a @Template into a pipeline,
    the system shall add a @Pipeline unit with the source, identifier and revision explicit, and shall
    keep the pipeline valid or refuse the drop with the reason
  - AC-002: When units are reordered or removed, the system shall store the new order on the
    @Workspace and shall leave any artefacts an earlier run produced untouched
  - AC-003: If a unit names a workspace item, template or revision that no longer exists, then the
    system shall keep the unit, mark the exact missing reference unresolved, and refuse to run until it
    is updated or removed
  - AC-023: When several @Case are selected and dropped together, the system shall create **one** case
    unit holding all of them, not one unit per case
  - AC-042: When an artefact unit is inspected, the system shall state whether it uses a
    `workspaceItem` or `template` reference; it shall never infer one from the identifier or silently
    fall forward to a later revision (CT-009)

### REQ-002 - The target set accumulates, and units act on all of it
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-004: When a case unit runs, the system shall add its cases to the @Target set and shall state
    how many cases the set now holds
  - AC-005: When a view, graph, report, export or tag unit runs, the system shall act on **every** case
    in the target set at that point, including cases added by earlier case units (XC-099)
  - AC-006: Where a case unit carries a selection rather than an explicit list, the system shall
    resolve it through CT-007 when the run starts and shall list the cases it resolved to
  - AC-007: If a unit runs with an empty target set, then the system shall skip it, state that the set
    was empty, and continue with the remaining units

### REQ-003 - Nothing runs before it can be read
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-008: When a dry run is requested, the system shall report every unit with the cases it would act
    on and the artefacts it would write, and shall change nothing
  - AC-009: When a run contains a destructive unit, the system shall require an authorisation naming
    the unit and how many cases it covers, once for the run rather than once per case (XC-094)
  - AC-010: If authorisation is declined, then the system shall run the non-destructive units and shall
    report the destructive ones as not authorised
  - AC-024: When a dry run reports a pipeline containing loops and conditions, the system shall state
    each loop's iteration count and each condition's value, because both are fixed before the run
    (XC-100, XC-101)

### REQ-004 - A failure stops one case, not the study
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-011: If a unit fails for one @Case, then the system shall skip that case's remaining units,
    record the unit that failed, and continue with the other cases (XC-095)
  - AC-012: If a report's input unit failed, then the system shall not export a partial document and
    shall record why the export was skipped
  - AC-013: Where stop-on-first-failure is chosen for a run, the system shall stop at the first failure
    and shall report what had already been written
  - AC-014: When a run is cancelled, the system shall stop before the next unit, keep what completed,
    and report the boundary it stopped at

### REQ-005 - A run is a record, not a side effect
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-015: When a run finishes, the system shall record the pipeline and its version, the resolved
    cases, and the outcome of every unit for every case, with the target-set size each unit acted on
    (XC-046)
  - AC-016: When the same pipeline is run again on the same inputs, the system shall produce artefacts
    identical to the first run, save for recorded timestamps
  - AC-017: Where a run produced a @Case, the system shall record which unit produced it, so a result's
    origin is answerable from the case itself

### REQ-006 - Memory is managed by the pipeline, not by luck
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-016 (T1)
- acceptance:
  - AC-018: When a clear unit runs, the system shall empty the @Target set and release the loaded data
    of the cases it held, and shall not touch any source file
  - AC-019: If loading a @Case would exceed the configured memory limit, then the system shall stop that
    case with a statement of what was needed and what was available, rather than being terminated by the
    operating system (LIM-001)

### REQ-007 - Nesting is bounded so a pipeline can be predicted
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-020: If nesting would exceed the depth of LIM-007, then the system shall refuse the edit and
    shall name the limit
  - AC-025: When depth is counted, the system shall count a loop, a condition and a simulation unit as
    one level each

### REQ-008 - The same pipeline runs without an interface
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-021: When a pipeline is run headlessly, the system shall execute the identical units through the
    identical command surface and shall produce identical artefacts (INV-006)
  - AC-022: When run headlessly, the system shall report progress and outcome in a machine-readable
    form, and shall exit non-zero if any case failed

### REQ-009 - Loops repeat a count that is known before they start
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-066 (T1)
- acceptance:
  - AC-026: When a loop unit runs, the system shall repeat the units it contains a number of times
    fixed before the loop begins - a literal count, the values of a @Variable, or one iteration per case
    in the @Target set - and shall state which
  - AC-027: While a loop is running, the system shall make the iteration index available to the units
    inside it under the name the unit declares
  - AC-028: If a loop's count resolves above LIM-008, then the system shall refuse the run before it
    starts, naming the unit and the count it resolved to

### REQ-010 - Variables and formulas, in a language with no interpreter behind it
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-065 (T1)
- acceptance:
  - AC-029: When a variable unit runs, the system shall bind its name for the units below it, and shall
    not change the @Workspace's own variables unless the unit says to
  - AC-030: When a formula unit runs, the system shall evaluate its @Expression with this product's own
    evaluator and shall bind the result with the unit that the expression produced
  - AC-031: If an expression combines incompatible units, then the system shall refuse it and shall
    name both units (INV-002)
  - AC-032: If an expression references a name that is not bound at that point, then the system shall
    refuse it at edit time, naming the reference, rather than at run time

### REQ-011 - Conditions choose what runs, and record what did not
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-033: When a condition unit's @Expression is true, the system shall run the units it contains,
    and when it is false shall skip them
  - AC-034: When a condition is false, the system shall record its contents as skipped **with the value
    the expression evaluated to**, so that a report never written is distinguishable from one never
    asked for

### REQ-012 - A pipeline can be written in Python, and nothing stored ever executes itself
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-064 (T1), E-065 (T1)
- acceptance:
  - AC-035: When a script builds a pipeline, the system shall produce the same declarative document the
    editor produces, openable and editable by hand afterwards (XC-102)
  - AC-036: When a @Workspace is opened, the system shall execute no script it contains, and when a
    stored pipeline runs, shall execute no Python
  - AC-037: When a script changes state, the system shall route every change through the command
    surface, record it in the log, and make the whole script undoable as one step (XC-061)
  - AC-038: Where unattended script execution has not been enabled for a workspace, the system shall
    refuse to run a script without a person authorising it, and that setting shall be off by default
  - AC-039: When an action is performed in the interface, the system shall be able to show the script
    text for that action, so the API is discovered rather than only documented

### REQ-013 - A run holds the workspace still
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-040: While a @Pipeline run is in progress, the system shall allow viewing and shall block edits
    to the @Workspace it is running against, stating why
  - AC-041: When a run finishes, the system shall offer to delete the artefacts it wrote, naming them,
    because undo restores the workspace and not the disk (XC-061)

## End-to-end verification

Register a pipeline with no simulation: drop six cases as one selection (one case unit), then a pinned
workspace View, a Graph template and a Report template, then a clear unit, then a second case unit with
two more cases and the same three definition references. One of the six has a truncated file. Dry-run it and confirm the
report states six cases at the first view unit, two at the second, and names the clear unit's scope.
Authorise and run. Five of the first six produce all three artefacts; the sixth reports the unit that
failed and has its later units skipped, with no partial report written. Wrap the first three artefact
units in a loop over three values of a variable and confirm the dry run states nine artefacts rather
than three. Build the identical pipeline from a script, confirm the stored documents are equal, and run
it headlessly with a non-zero exit code for the failed case.
