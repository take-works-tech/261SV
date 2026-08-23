---
status: draft
updated: 2026-08-22
---

# User scenarios

Eleven paths through the complete product, written as what a person does and what the product shows
back. They exist because a screen inventory can be complete and still describe a product nobody can
finish a job in: the inventory answers "does this surface exist", and only a path answers "can the
number reach the deliverable without the user guessing once".

Each scenario names the Screen and Area of [16_application_model.md](16_application_model.md), the
command issued, and the failure that path can meet. Where a step would be refused, the refusal is part
of the scenario rather than an appendix - the refusals are the product.

Read as verification material: these are the end-to-end sequences
[verification/plan.md](verification/plan.md) covers per feature, joined up.

## Scenario 1 - From a result file to the first picture

- actor: an engineer with a finished solver run and no workspace open
- starts with: a folder of result files
- ends with: a saved @Workspace, one @Case, one @View showing geometry with no colour claim

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | Workspace list | drops the folder | the import review: format support per file, field associations read as authored, units listed as undeclared, coordinate frames resolved or not |
| 2 | import review | reads the proposed grouping and tags | proposals only - nothing is applied, and rejecting one removes it for the session (XC-120) |
| 3 | import review | accepts, imports | a cancellable read naming the file; cancelling leaves no partial @Case (XC-060) |
| 4 | View Screen, `outliner` | expands the tree | the source hierarchy exactly as the file carries it; an unnamed element stays unnamed |
| 5 | View Screen, `viewport` | frames the model | geometry in a neutral material, no colour map, no legend - nothing has been declared yet |
| 6 | `information` | checks what arrived | per field: association, component names as authored, undeclared unit, measured range, missing count |

Failure paths: an unreadable file is refused with the reason and the original untouched (XC-007); a
coordinate frame that cannot be resolved refuses the import rather than assuming global Cartesian; a
format at Limited support names its specific gaps rather than reporting success.

What it proves: nothing is inferred between the file and the screen.

## Scenario 2 - Declaring a unit, and what changes

- actor: the same engineer, who knows the solver wrote pascals
- starts with: a @Field whose unit is undeclared
- ends with: a declared unit, a legend that can carry a label, and a conversion that is now legal

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | `information` or the variable list | selects the field | the undeclared marker, and that no conversion is available |
| 2 | Settings, 単位 | declares Pa for this quantity kind, and MPa as the @Display unit | the declaration recorded with who declared it and when - it becomes @Provenance, not a guess |
| 3 | Settings | mistypes a display unit | the value is refused at the field, the previous one is kept, and the message names the rejected text |
| 4 | View Screen | returns | the legend now carries MPa; the stored numbers did not change, only their display |
| 5 | `table` | reads a column | the value at its @Stored precision, its @Significant digits, its unit and its provenance in one row |

What it proves: a unit is a declaration with an author, and declaring it changes labels and conversions
without touching a stored number (XC-003, XC-134).

## Scenario 3 - Comparing two cases

- actor: an engineer who changed the plate thickness
- starts with: two @Case in one @Workspace
- ends with: a @Diff that states what it cost, and a picture that says which case is which

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | View Screen | switches to the Compare preset | two `viewport` Areas, one following the tree and one pinned; each pane names its @Case |
| 2 | pane header | turns camera synchronisation on | both cameras move together; each pane keeps its own @Case and its own result position |
| 3 | `diff` | names case A, case B and the quantity | the method: shared mesh, or resampled with the target chosen by the user - never chosen silently |
| 4 | `diff` | reads the disclosure | resampling direction, how many points fell outside the target, the round-trip error - carried with the result everywhere it appears |
| 5 | `viewport` | shows the difference as a field | one colour map, referenced by both panes, so the two screenshots are comparable (XC-194) |
| 6 | `table` | checks three elements | the difference, both source values, and that a location missing in either case is missing here - never zero |

Failure paths: different declared units refuse the diff and name both (INV-002); a quantity present in
only one case is named rather than treated as zero in the other.

What it proves: the comparison the product exists for produces a number a reviewer can question.

## Scenario 4 - A graph across five runs

- actor: an engineer writing up a parameter study
- starts with: five @Case differing in one @Variable
- ends with: a saved @Graph whose series say where each point came from

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | Graph Screen | creates a new @Graph | an empty chart and three entry points: manual, recommended, assistant-suggested - none applied automatically |
| 2 | properties, 詳細 | sets the case selection to a declarative condition | the condition, and how many cases it resolved to right now |
| 3 | properties, 系列 | adds a series, picks the quantity for Y and the varied @Variable for X | the unit and the @Provenance appear beside the choice, not after the fact |
| 4 | properties, 系列 | adds a second series as an @Expression | the expression editor: names in scope, unit checking, and the error at the character it occurred |
| 5 | `chart` | notices one case is flat | that case is drawn as no data and stays in the legend, with which quantity it lacks |
| 6 | properties, 軸 | sets the left axis to log and gives the right axis the second series | four independent axes; each with its own title, unit, range rule, notation and precision |
| 7 | properties, 出力 | exports vector plus tabular data | preflight first; the table carries provenance columns, and machine-readable numbers do not follow the interface language (XC-110) |

Failure paths: a selection that resolves to nothing says which condition emptied it (CT-007); mixing
series from different @Result axis kinds sets the note that says so rather than plotting a mode index
against a time.

What it proves: a figure is a definition over identified quantities, not a picture of numbers someone
pasted.

## Scenario 5 - Checking a number

- actor: a reviewer who does not trust a figure in a draft report
- starts with: a @Report block showing a maximum
- ends with: either confidence, or a named reason the figure cannot be supported

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | `report` | clicks the figure | what produced it: the item, the @Case, the result position, the quantity |
| 2 | Inspect preset | opens `viewport`, `table` and `information` together | the same subject in three forms |
| 3 | `find` | builds a threshold selection over the quantity | the count that matched, resolved at a stated result position |
| 4 | `table` | filters to the selection | the values at their stored precision with unit and provenance |
| 5 | `viewport` | probes the element the table points at | the probe readout: value, unit, digits, provenance, result position - and an explicit action to keep it as a @Variable |
| 6 | `information` | checks the field | that the field is point data, that its unit is declared, and how many values are missing |

Failure paths: a reduced display representation is marked as reduced, and every number here comes from
the full dataset in the @Canonical frame (INV-001, INV-009); a @Deformation scale other than 1.0 is
drawn into the picture, so measuring the screen is visibly not measuring the model (INV-024).

What it proves: the product's central claim is checkable from inside the product.

## Scenario 6 - Authoring a material that shows a result

- actor: an engineer preparing a presentable picture
- starts with: an analysis mesh and a stress field
- ends with: a saved @Material Asset revision bound to that field, and a picture that says what it shows

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | View Screen, shelf | opens the material library, filters by tag | rendered thumbnails; a data-dependent asset says サンプルデータ; an asset with no thumbnail says so rather than borrowing one |
| 2 | shelf | applies to the active object | a new Material Slot on that object; the whole-object or a non-overlapping part target |
| 3 | properties, マテリアル | selects 基本 | OpenPBR Surface named once, its published inputs, and Base Color as 単色 / 画像 / カラーマップ / 数式 |
| 4 | 基本 | chooses カラーマップ and the stress variable | the variable selector, then minimum, colour bar and maximum in one compact row; out-of-range values evaluate to alpha zero |
| 5 | colour-map editor | edits opacity above, colour below | interior points added, moved and removed; the two endpoints follow the range; the map is a workspace object other panes reference |
| 6 | Author material preset | opens `nodes` | the typed graph in a real canvas; nodes 基本 cannot show are retained, not flattened |
| 7 | ソース | edits the `.mtlx` | validation on load and on every edit; save re-validates and creates a new immutable revision |
| 8 | `viewport` | before the field resolves | the target and the live preview are diagnostic magenta, the legend is suppressed, and the missing input is named (XC-175) |

What it proves: a presentable picture and a traceable one are the same picture.

## Scenario 7 - Automating forty cases

- actor: an engineer who now has to do it every week
- starts with: one @View, one @Graph and one @Report that work on one @Case
- ends with: a saved @Pipeline, a dry run, an authorised run, and a record of what it wrote

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | Automation Screen | creates a @Pipeline, drags a multiple case selection in | **one** case unit holding all of them, and the accumulating @Target set count on every unit below |
| 2 | properties, ユニット | adds view, graph and report units | each pinned to an item by identifier and revision, so a later edit to the item does not silently change the run |
| 3 | `pipeline` | wraps two units in a condition zone | a bounded zone, not indentation; the condition edited in the @Expression editor with unit checking |
| 4 | `pipeline` | adds a clear unit at the end | the unit marked destructive, and the run blocked until its scope is authorised |
| 5 | `pipeline` | runs a dry run | targets and artefacts per unit, nothing written |
| 6 | scope confirmation | authorises the clear unit | which unit, and how many @Case it covers - once for the run, not per case (XC-094) |
| 7 | anywhere | watches | progress in the top bar; viewing continues; editing this workspace is blocked with the reason |
| 8 | `log` | after a failure on one case | that case failed at that unit, its remaining units skipped, the other cases continued (XC-095) |
| 9 | `log` | reads the outcome table | case against unit: applied, skipped, failed, refused - with the value a false condition evaluated to |
| 10 | `log` | decides to discard the run | the files it wrote, by name, offered for deletion - undo restores the document, not the disk (XC-061) |

What it proves: the run's scope, its cost and its wreckage are all visible before and after.

## Scenario 8 - Asking for it in words, then taking it back

- actor: an engineer who would rather describe the job than click it
- starts with: a workspace with cases loaded
- ends with: the same result as the manual path, and one undo step

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | composer, any Area | types the instruction | the compact bar; opening it reveals the conversation as a drawer beside the properties, not instead of them |
| 2 | drawer | reads the proposed effect | what the assistant will do, as the effect summary of the commands it would issue - before it issues them |
| 3 | drawer | accepts | the same commands the interface issues, journalled with the assistant as issuer |
| 4 | `script` | opens the log of what just happened | the same operations as Python over `sv.ops`, copyable and re-runnable |
| 5 | anywhere | undoes | the whole instruction as one step, including its multi-part changes (XC-061) |
| 6 | Chat Screen | continues the conversation | the same messages, the same draft, the same model and effort - one conversation, two presentations (XC-150) |

Failure paths: the assistant fails before any command is sent, and the workspace is unchanged with the
reason stated (XC-005); an instruction that would need the network states what would be sent and to
which host, and sends nothing until permitted (XC-106).

What it proves: natural language is a caller of the command surface, not a second product.

## Scenario 9 - Producing something a recipient can open

- actor: an engineer sending results to a customer with nothing installed
- starts with: a finished @Report definition
- ends with: one self-contained file, produced offline, that says what it does not know

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | Report Screen, properties 全体 | reviews the mandatory content | @Provenance, @Declared unit, limitations and product version present and not removable |
| 2 | properties 詳細 | turns on generated commentary | direction, depth, model and whether a search may be made - and that nothing is sent until permitted |
| 3 | commentary review | reads the passages | each with which of the four kinds it is and its source; the omissions listed with why they failed the standard (XC-104) |
| 4 | properties 出力 | chooses interactive HTML | the preflight: fonts and the glyphs actually used, 3D handling for this format, unresolved content, destination |
| 5 | preflight | a face cannot draw a glyph | the element and the character are named; nothing is exported as an empty box |
| 6 | export | runs with the network blocked | it completes; nothing network-dependent was attempted (INV-007) |
| 7 | recipient | opens the file | geometry, values with units, graphs, commentary and the verdict, with no installation |

What it proves: the deliverable is the product, and it is honest about its gaps without a person editing
them in.

## Scenario 10 - Meeting a broken input

- actor: anyone, on the day the run did not finish cleanly
- starts with: a truncated file, a renderer that will not start, and a template that half applies
- ends with: three refusals a person can act on, and a workspace that changed nothing it could not

| # | Where | Sees |
|---|---|---|
| 1 | Workspace list | the file named, the reason it could not be read, that no @Case was created and the original is untouched (XC-007) |
| 2 | View Screen | which renderer backend failed and which still runs, with the work that remains possible (XC-004) |
| 3 | template application | the unresolved list before anything is drawn: what resolved, what did not and why, with the source @Template identifier and revision kept reachable from the item created (XC-063) |
| 4 | `viewport` | a field the @View asks for and this @Case lacks is listed as unresolved, and the rest is still drawn (XC-090) |
| 5 | result axis | a requested position that does not exist is named, not rounded to the nearest (view/AC-033) |
| 6 | `log` | all five, still there after the banners were dismissed |

What it proves: the failure states are the ones a demonstration never shows and a user meets on day one.

## Scenario 11 - Handing the work to a colleague

- actor: two engineers, one leaving for holiday
- starts with: a workspace with original templates and materials in the workspace scope
- ends with: a colleague who can open it and change one thing without archaeology

| # | Where | Does | Sees |
|---|---|---|---|
| 1 | shelf, オリジナル | reviews what is workspace-scoped | each original labelled このワークスペース or 共有, inside the オリジナル source rather than folded into it |
| 2 | shelf | drags a workspace original to the shared scope | a copy, not a move - the workspace stays openable on its own (GL-019) |
| 3 | item menu | saves the @View as a @Template | a copy of the definition into the chosen @Library scope, with no live link; editing the template later changes no existing item (XC-109) |
| 4 | `library` | fills in the metadata | author, description, tags, licence, revision, what depends on it, and where it is used |
| 5 | colleague | opens the workspace | the same items, the same identities, the same numbers - and any asset that could not be resolved named rather than substituted |
| 6 | colleague | creates from the template | the resolution preview first, then a new independent item carrying the template identifier and revision as provenance |

What it proves: reuse is copying with a recorded origin, never a hidden link that changes results later.

## What these scenarios do not cover

Recorded so the gap is not mistaken for coverage:

- **running a solver.** @Simulation execution is a later release (XC-091); Scenario 7 starts from
  results that already exist
- **collaboration on one workspace at once.** The exclusive edit lock is stated in the workspace
  settings; two people editing simultaneously is not designed here
- **the hosted transport.** The same core over a different transport is named in the product
  description and is not exercised by any path above
- **a study larger than the stated capacity.** LIM-005 bounds the case count these paths assume; the
  behaviour at the boundary is a limit question, not a scenario
