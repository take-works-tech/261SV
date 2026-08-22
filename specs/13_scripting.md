---
status: draft
updated: 2026-08-21
---

# Scripting and the expression language

Two surfaces, one rule. **Python** builds documents and drives the product; the **expression language**
computes values inside a @Pipeline. Neither is a second way for something to happen: both go through
the command surface the interface uses (CT-002), so anything either one does is logged, undoable and
dry-runnable exactly like a click.

This file is product-wide on purpose. A naming rule invented per feature is how the same object becomes
reachable as `case`, `caseId` and `Case` in three places, and how a script that worked last month stops
working for a reason nobody can name.

## The one rule

**A script issues commands; it does not reach past them.** There is no path from Python into a module's
internals, no direct write to the @Workspace document, and no way to produce a @View that the command
log does not contain. The reason is not tidiness: it is that undo, the run record, reproducibility and
the dry run are all built on the command log, and an action that skipped it would be invisible to all
four at once.

Deliberately unlike the reference application: **commands issued by a script are undoable**, grouped so
that one script is one undo step (XC-061). There, operators called from Python bypass the undo stack by
default so that scripts do not push a step per operator (E-064). That trade makes sense for a tool
whose scripts mostly run before anyone is watching. Here the customer asks an agent to build forty
reports and must be able to take it back.

## The object model

One root module. Data is reached through collections named by kind, indexed by name; the current
subject is reached through the context; operations are called as commands.

| Surface | What it is | Example shape |
|---|---|---|
| `sv.data` | everything the @Workspace holds, by kind | `sv.data.cases["Run 12"]`, `sv.data.views["Pressure top"]`, `sv.data.variables["inlet_velocity"]` |
| `sv.data.templates` | the library, by kind, across scopes (CT-008) | `sv.data.templates.views["Pressure top"]` |
| `sv.context` | what is currently selected, and where | `sv.context.workspace`, `sv.context.selected_cases` |
| `sv.ops` | the command surface (CT-002) - everything that changes state | `sv.ops.view.apply_template(...)` |
| `sv.pipeline` | building and running a @Pipeline (CT-009) | `sv.pipeline.new("Weekly report")` |
| `sv.units` | declared units, conversion, the undeclared marker (XC-003) | `sv.units.declare(field, "Pa")` |

`sv.data` is readable and `sv.ops` is writable, and the split is not cosmetic: reading needs no command,
so a script that only reads produces no log entries and no undo steps.

**A script reads values as arrays.** The restriction in XC-097 is on what reaches a *language model*,
not on what local code may hold: a script runs on the customer's machine, so it may read a million
numbers. What it may not do is hand them to a model, and the surface makes that hard rather than
convenient - `sv.assistant` accepts statistics and metadata, and refuses arrays.

## Names and identity

The rule of XC-103, stated once for every kind of object:

- every object has a **stable identifier**, assigned once and never reused
- every object has a **name unique within its kind** - two cases may not share a name; a case and a
  variable may
- **stored references use the identifier.** Renaming an object rewires nothing, because nothing stored
  ever pointed at the name
- **lookup by name resolves to exactly one object, or raises.** It never returns a list to be indexed
- **creating or renaming to a name in use is refused**, naming the object that holds it

The last two are where the two reference products diverge, and the divergence is instructive. One
enforces uniqueness by appending a numeric suffix, so `Cube` silently becomes `Cube.002` and a script
written against the name it asked for gets something else (E-064). The other allows duplicates and
returns every match, so the documented idiom is to take the first and hope; its own documentation says
the lookup is robust only where names happen to be unique (E-067). **Refusing is the only one of the
three that never quietly points a reference at the wrong object** - and in a product whose output is
numbers attached to names, the wrong object is a wrong answer with a plausible label.

### Referring to a template from a script

A @Template lives in a scope - sample or original, workspace or shared (GL-019) - and the same name may
exist in two scopes. Lookup is therefore **scope-first, name-second**, with an explicit default:

- `sv.data.templates.views["Pressure top"]` searches workspace originals, then shared originals, then
  samples, and **raises if the name exists in more than one of them** rather than choosing
- `sv.data.templates.views.workspace["Pressure top"]` names the scope and does not search
- applying a template returns a resolution preview; accepting that result creates and returns a new
  independent workspace item with source-template provenance (XC-090, XC-109)

Workspace Views, Graphs and Reports are reached directly through `sv.data.views`, `sv.data.graphs` and
`sv.data.reports`. They are not included in `sv.data.templates`. `save_as_template(item, scope)` copies
an item's current revision into the library; neither that operation nor `apply_template` establishes a
live link.

## The expression language

The language of formula units, conditional units and computed quantities. One language, one evaluator,
no interpreter behind it (XC-101) - so an expression evaluates identically whether or not scripting is
enabled, and a workspace from an untrusted source can be opened and its formulas read without running
anything.

| Category | Contents |
|---|---|
| arithmetic | `+ - * / ** %`, parentheses |
| comparison | `== != < <= > >=` |
| boolean | `and or not`, and the ternary conditional |
| functions | `abs min max sum mean median std sqrt exp log log10 sin cos tan atan2 floor ceil round clamp` |
| references | `@Variable` by name, recorded quantities of the case in scope, and the loop index |
| literals | numbers with an optional unit, `true`, `false`, and text |

**Units travel through an expression.** A length divided by a time yields a velocity; a length added to
a time is refused with both units named (INV-002). A literal may carry a unit, and a bare number in an
expression with declared units is treated as undeclared rather than assumed to match (XC-003).

Not present, and each for a reason: attribute access and indexing, because they are the door into the
object model; imports and function definitions, because they turn the language into a program; any call
that writes, because an expression that changes state cannot be evaluated twice for a dry run.

## Running a script

- a script is run by an explicit action - a person, or an agent the workspace has been configured to
  allow. **Opening a workspace never runs anything** (XC-102)
- scripts run in a separate process with the capabilities of XC-089: no network, filesystem access
  limited to the workspace and the paths it references, a wall-clock limit and a memory limit
- a failure leaves the workspace as it was: the script's commands undo as one group
- **unattended execution is off by default** and is enabled per workspace. The application this rule is
  modelled on shipped the permissive default first and had to retrofit the preference (E-065)

## Discovering the API

Every action in the interface has a command, and every command has a script form. The interface can
therefore **show what it just did as script text**, which is how a user who has never opened the
documentation finds the call they need: do it once by hand, read the line, put it in a loop.

This is nearly free here - the command log already exists for undo and the run record - and it is the
difference between an API that is documented and one that is discovered.

## What a language model is told

The same rule as everywhere else, applied to the model: **one definition, generated outward** (XC-139).

- the **operations it may call** are generated from CT-002 and CT-003 - never a hand-written list
  beside them, which drifts within a release and then makes the model look poor for calling something
  that no longer exists
- the **workspace it is working in** arrives as a summary: the case tree, the quantity list with units
  and provenance, the templates available, the states of things. **Never bulk numeric data** (XC-097)
- the **words** are the glossary's (00_glossary.md), so the vocabulary in a generated report is the
  vocabulary in the interface

This is also what makes the evaluation set of XC-138 mean something: when a result gets worse, the
cause is the model or the prompt, and never a description that quietly went stale.

## Compatibility

The script surface is versioned with the product and follows the command surface (CT-002): an operation
may gain optional arguments, and an argument never changes meaning. A removed operation is deprecated
for one release with its replacement named, and a script using it reports that rather than failing
obscurely. **The expression language's function set only grows**, because a saved formula that stops
evaluating is a report that stops being reproducible.

## What is deliberately absent

- **no callbacks or event handlers.** A script runs and finishes; nothing registers itself to run later
  inside the application, because a workspace that carries live code is a workspace nobody can safely
  open
- **no user interface from a script.** Panels and dialogs belong to the product, so that every
  installation looks the same to the person supporting it
- **no direct rendering calls.** A script asks for a @View to be produced through the same path the
  interface uses, so that the picture in a scripted report and the picture on screen cannot diverge
