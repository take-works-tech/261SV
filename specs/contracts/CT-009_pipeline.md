---
status: draft
updated: 2026-08-21
---

# Contract: pipeline

### CT-009 - Pipeline
- purpose: a repeatable flow registered on a @Workspace, above @Case - the thing that turns "make this
  view, this graph and this report" into "do that for every result, including the ones that do not
  exist yet"
- schema: schema/CT-009.json
- version: 3.0.0
- strictness: unknown fields are **rejected** - a pipeline carrying a unit this build does not
  understand would silently skip work the user believes was done
- compatibility: a unit kind added later is additive; a unit kind never changes meaning
- migration: a stored pipeline is upgraded on open, like the document that holds it (CT-001). A 2.0
  unit's `templateId` becomes `definitionRef.source=template` with the same id and the revision that
  existed at migration; if that revision cannot be established, the unit stays unresolved and running
  is refused rather than binding it to the newest revision
- decidedness: Fixed
- basis: E-001 (T1), E-088 (T1)

## What a pipeline is

A **declarative, ordered list of units**, stored on the @Workspace rather than on any @Case. It runs
with no simulation involved: the entry point is the cases the workspace already holds. Units are
dragged in, reordered and removed; a pipeline is edited, not recorded (XC-093).

Running one carries exactly one piece of state - the **target set** (GL-026) - and this is the whole
execution model:

| Unit | What it does to the run |
|---|---|
| `addCases` | **adds** cases to the target set |
| `clear` | **empties** the target set and releases the data those cases had loaded |
| `view` `graph` `report` `export` `tag` | acts on **everything currently in the target set** |
| `loop` | runs the units it contains a fixed number of times |
| `variable` | binds a name to a value for the units below |
| `formula` | computes a value from variables and quantities, and binds it |
| `condition` | runs the units it contains when its @Expression is true |
| `simulation` | runs a pinned saved @Simulation flow - later release (XC-091, XC-154) - and adds each successful execution's result Case to the target set |

A view unit placed under three case units therefore applies to all three groups, because that is what
"everything accumulated above it" means. This is the property the design turns on: **adding a case to a
study means editing one unit, not every unit below it** (XC-099).

## The case unit

Dropping a multiple selection creates **one** unit holding all of the selected cases - not one unit per
case. A case unit holds either:

- an **explicit list** of cases, which is what dragging produces, or
- a **selection** resolved when the run starts (CT-007), which is how a pipeline picks up cases that
  did not exist when it was written

Both forms list what they resolved to before anything runs.

## Definition references

A `view`, `graph`, `report` or future `simulation` unit contains one `definitionRef` (XC-109). For a
simulation unit, the concrete `workspaceItem` reference identifies one saved @Simulation flow; Simulation
templates are not implied by sharing the generic envelope:

- `workspaceItem` references a concrete item in this workspace when the pipeline must reproduce that
  configured artefact
- `template` references a reusable library blueprint when the same pipeline is intended to travel or
  be applied across workspaces
- both forms store identifier and revision; exactly one source is named, and a missing revision makes
  the unit unresolved rather than falling forward to a newer definition

The run record stores the resolved definition reference. Editing an item or template creates a later
revision and does not rewrite existing pipeline units. Updating a unit to the later revision is an
explicit edit whose resolution report is shown before the next run.

## The clear unit

`clear` is what makes a study larger than memory possible: it empties the target set and releases the
loaded @Dataset of the cases that were in it. It deletes **loaded data, never source files**, and it is
destructive in the sense of XC-094 - it is authorised once for the run, with its scope named.

The pattern it exists for: add ten cases, produce their figures, clear, add the next ten. Without it a
forty-case study fails at case twenty-nine, and the user sees a crash rather than a limit.

## Loops, variables, formulas and conditions

Repetition and arithmetic are bounded on purpose (XC-100, XC-101).

- a `loop` repeats a **count fixed before it starts**: a literal, the values of a @Variable, or one
  iteration per case in the target set. There is no `while` and no user-written break; the loop index
  is available to the units inside
- a `variable` unit binds a name for the units below it, and a `formula` unit binds the result of an
  @Expression. Both are scoped to the pipeline run and do not alter the @Workspace's own variables
  unless a unit explicitly writes one
- a `condition` unit holds an @Expression and runs its contents when it is true. A condition that is
  false is **recorded as skipped with the condition's value**, not omitted from the record - otherwise
  a report that never got written looks the same as one that was never asked for

The expression language, its functions and what it deliberately cannot do: [../13_scripting.md](../13_scripting.md).

## Nesting

`loop`, `condition` and `simulation` units contain others, to LIM-007 levels. Each of the three
consumes a level. **The limit exists so that a pipeline can be read**: past a few levels nobody can say
what will run, and a pipeline nobody can predict is one nobody should authorise to delete data.

## Running

Every run records the pipeline and its version, the resolved cases, and the outcome per case and per
unit. That record is what makes a run reproducible and what a reviewer reads afterwards (XC-046).

- **Dry run first.** A pipeline can be asked what it would do: the target set at every unit, the
  iteration count of every loop, the value of every condition, which artefacts would be written, and
  every destructive unit with its case count. This is possible only because loops are bounded and
  expressions have no side effects - the two constraints pay for this one property
- **Destructive units need explicit authorisation for the run**, not per case, naming how many cases
  and which unit it covers (XC-094)
- **Failure is per case.** A unit that fails on one case does not stop the others; the remaining units
  for *that* case are skipped rather than run on a broken state, and the case is reported as failed
  with the unit that failed
- **Nothing partial is written.** A report whose graph unit failed is not exported with a gap where the
  figure should be; the export is skipped and the reason recorded

## Written in Python

The same pipeline can be built by script (XC-102). The script **constructs this document** - it does
not become the pipeline. Opening a workspace never executes anything, and running a stored pipeline
never runs Python. What a script produces and what the editor produces are the same structure, which is
why a pipeline written by an agent can be opened, read, edited by hand and re-run.

## Why per-case isolation rather than stop-on-first-failure

Stopping the whole run is the safer-looking choice and the wrong default here. A forty-case study where
case seven has a truncated file should produce thirty-nine results and one clear failure, not zero
results and one clear failure. **Stop-on-first-failure remains available** for the case where later
units depend on earlier ones being complete - but it is chosen, not assumed.
