---
status: draft
updated: 2026-09-20
---

# Contract: engine API

### CT-003 - Engine API
- purpose: the wire form of the command surface (CT-002) between the interface and the engine process,
  and between a remote client and a hosted engine. The same operations, the same shapes, whether the
  engine is a child process on loopback or a service across a network
- schema: schema/CT-003.json
- version: 3.4.0
- correction: 2026-09-20, version 3.3.0 to 3.4.0. `view.render` and `view.pick` take `camera` - the
  CT-004 camera shape, referenced rather than copied. A camera move is a class-1 transition
  (XC-270): it reaches the engine as the camera the picture is drawn and picked with, and never
  as a change to the view's definition, which until this change was rewritten by every orbit and
  entered the undo history and the unsaved work each time. Additive
- correction: 2026-09-20, version 3.2.0 to 3.3.0. `workspace.open` answers `readOnly` and `lock` -
  what was found, who holds it and where the lock file is - and takes `takeOverStaleLock` for a
  person who has read that a lock is stale or unreadable and says to take it over. Until this
  change nothing took the lock at all: the mechanism and its tests had existed since 2026-08-24
  and every open was an editor (#262, XC-269). Additive
- correction: 2026-09-20, version 3.1.0 to 3.2.0. `output.list` and `output.plan` are added and
  `output.prune` gains `expectedFiles`. The prune had been in the contract since 2.x with nothing
  answering it and nothing to show a person what it would take: the list says what is there,
  the plan names every file that would go for the runs a person chose, and the act names the
  files it expects so that a folder changed in between is refused rather than pruned (XC-268,
  #314). Additive
- correction: 2026-09-20, version 3.0.0 to 3.1.0. `system.capabilities` answers `egress`: whether this
  build has a way out at all, the open workspace's permission (search, language model, update
  check, the allow-list, per-search confirmation, workspace content) and how many audit entries
  there are and how many left. #317 asks that a person be able to check that nothing was sent
  rather than read that it is the policy; `system.audit`, already in the contract, gains its
  handler in the same change. Additive
- correction: 2026-09-20, version 2.9.0 to 3.0.0. Every time an answer carries is the one wire form
  `{utc, offsetMinutes}` (CT-001 `$defs.recordedTime`, XC-266): `history.list` entries `atUtc`
  become `at`; `pipeline.run` `startedUtc` and `finishedUtc` become `started` and `finished`;
  `report.provenance` `sources[].modifiedUtc` becomes `modified` and the answer gains `produced`;
  `system.audit` entries `atUtc` become `at`; `dataset.inspect` `modifiedIso` becomes `modified`,
  present only when the file exists. The engine had held both facts of every one of these in
  memory and written one of them to the wire. Breaking; no released client existed
- correction: 2026-09-20, version 2.8.0 to 2.9.0. `history.list` says what memory no longer holds:
  each entry carries `undoable`, and the answer carries the undo cap and how many groups it dropped
  (LIM-014), the history cap and how many entries fell out (LIM-015). #315's condition is that a
  person can tell what was lost when the cap is exceeded; this is where they are told. Additive
- correction: 2026-09-20, version 2.7.0 to 2.8.0. `system.capabilities` answers `diagnostics`: where
  the log is written, at what level, the size it rotates at, how many files are kept and for how
  long, and what is there now. #312 asks that the location be reachable from the interface, and
  the capabilities answer is where a build says what it is. Additive
- correction: 2026-09-19, version 2.6.0 to 2.7.0. `dataset.inspect` is added: the home screen's import
  review states a format's support level and the reader's gaps **before anything loads** (ingest/REQ-015,
  XC-049), and nothing in the contract answered that without reading the file. It reads the path's
  extension and the file's size and time, never its contents. Additive
- correction: 2026-09-19, version 2.5.0 to 2.6.0. `workspace.open` answers the items the document
  holds. Found by the recovery path of #306: after an engine restart the interface reopened the
  saved document and then created its working view again under the same name, which the document
  refuses because names are unique within a kind (workspace/AC-030) - correctly. Nothing in the
  contract let a caller learn what a document it had just opened contained, so it could neither
  update the saved view nor know it existed. Additive; no listing operation is added, because the
  moment of opening is when the answer is wanted
- correction: 2026-09-19, version 2.4.0 to 2.5.0. `$defs.transport` gains `connectionFile`, the name of
  the file the engine writes and the shell reads. The shell (MOD-018) defined it a second time in
  TypeScript and the duplication gate caught it the same hour; the two sides cannot import from each
  other, so the name is generated to both from here like the header and the paths. Additive
- correction: 2026-09-19, version 2.3.0 to 2.4.0. `view.render` takes `legend`, default true. A
  document must carry its colour bar inside the picture because nothing else in a document can
  (XC-254); a screen has chrome beside the picture that carries the legend **with its unit**, which
  the picture's own bar cannot (E-192: the embedded face draws Japanese as nothing). Drawn in both
  places, the screen showed two scales for one image. The legend is a property of the drawing, like
  width and format, not of the view, so it is a render parameter and not a CT-004 field. Additive
- correction: 2026-09-19, version 2.2.0 to 2.3.0. `dataset.probe` takes a point in canonical metres,
  which is the right thing for a script and the wrong thing for a person: an interface has a **pixel**
  a person clicked, and turning one into the other needs the camera the picture was drawn with. The
  interface does not have that camera; the engine drew with it. So `view.pick` is added, taking the
  view and a pixel and answering what `dataset.probe` answers. Additive - `dataset.probe` is
  unchanged and is still how a script asks. Recorded because the alternative was the interface
  passing something it had computed from a fraction of a pane, which would put a number in the
  readout belonging to a place nobody clicked
- correction: 2026-09-18, version 2.1.0 to 2.2.0. `dataset.probe` took a dataset id, a point and a
  result position and answered "the value at that point" - **of no named field**. The operation could
  not be implemented as written: a dataset holds several fields and nothing in the request said
  which. It now takes a `fieldName`. Additive to an operation no release has shipped, and recorded
  here rather than silently, because the row read as complete for three weeks and was not
- strictness: unknown fields are **rejected** - a request carrying a parameter the engine does not
  understand is refused, because the caller believes something is happening that is not (CT-002)
- compatibility: an operation name and its parameters keep their meaning once shipped. Behaviour
  changes get a new name. The engine states the versions it speaks and refuses politely below its floor
- migration: not applicable - a live protocol, not stored data
- decidedness: Fixed
- basis: E-001 (T1)

## Shape

Every call is one request object and one response object. There is no implicit state: an operation
that needs a previous result takes its identifier as a parameter, so a dropped connection loses
nothing but the answer.

```
request  { protocol, operation, parameters, targets?, groupId?, authorisation?, dryRun? }
response { status, changed?, effectSummary?, reason?, undoId?, result?, warnings? }
```

`status` is one of `applied`, `refused`, `failed`, or `answered` for a read. **A refusal always carries
a reason and changes nothing**; a failure carries a reason and states whether anything changed.

## Operations

The catalogue is the contract. Anything the interface can do appears here, and nothing appears here
that the interface cannot do (INV-006).

**The Parameters column says what each parameter means; `schema/CT-003.json` says what they are.**
`$defs.operationParameters` carries one JSON Schema per operation - the name, the type, and whether it
is required - and an implementation takes its accepted parameters from there rather than declaring its
own (XC-249). The two are not two copies of one list: a schema cannot say that a template reference is
optional *because the item may be original*, and a column cannot be compared against code.

**The Result column says the same about answers.** `$defs.operationResults` carries one JSON Schema per
operation, and where an answer holds a measured number it holds a `$defs.reportedValue` - whose `value`,
`unit`, `digits` and `provenance` are **required** (XC-253). That is the reason for doing this at all:
XC-003, INV-013 and INV-014 are statements about what a result carries, and prose can ask for them while
a schema can require them. The command surface fails a handler whose result carries a field the contract
does not declare or omits one it requires - `failed` and not `refused`, because the caller did nothing
wrong. A dry run is held to the field names and not to the required ones: it applies nothing, so it has
no identifier to report.

| Operation | Reads or writes | Parameters | Result |
|---|---|---|---|
| `workspace.open` | write | path, take over stale lock? | workspace id, unresolved cases, format version, the items the document holds (views, graphs, reports: id, name, dataset), whether it opened read-only, and what the lock said - state, holder, file (XC-241, XC-269) |
| `workspace.save` | write | workspace id, path? | path written, previous version kept |
| `workspace.close` | write | workspace id | - |
| `case.create` | write | workspace id, parent case id?, name | case id |
| `case.delete` | write | case id | affected descendant ids |
| `case.move` | write | case id, new parent id | - |
| `case.tag` | write | case id, tags | - |
| `dataset.inspect` | read | path | what can be said before the file is read: format, the support level this build promises for it, the reader's known gaps, size, modification time (ingest/AC-032) |
| `dataset.load` | write | case id, file paths | dataset id, fields with association, support level, gaps |
| `dataset.describe` | read | dataset id | point and cell counts, bounds in metres, time steps, partial flag |
| `field.declareUnit` | write | dataset id, field name, unit symbol | - |
| `field.statistics` | read | dataset id, field name, region? | min, max, mean, missing count, the association used |
| `variable.declare` | write | workspace id or case id, name, value, unit? | variable id |
| `variable.set` | write | variable id, value | ids of every place that changed |
| `variable.detach` | write | case id, variable id | the value it kept - the variable stops following the parent (XC-117) |
| `view.create` | write | workspace id, definition (CT-004), source template id and revision? | workspace view id and revision; source is provenance, not a live link (XC-109) |
| `view.update` | write | view id, definition | - |
| `view.duplicate` | write | view id, new name | new independent workspace view id |
| `view.rename` | write | view id, new name | new revision; stored id references unchanged |
| `view.delete` | write | view id | deleted id; dependent pipeline units retained as unresolved |
| `view.render` | read | view id, width, height, format, legend (default true), camera? | image bytes or a handle to them; a camera given draws the picture from there and leaves the definition's camera as it is (XC-270) |
| `view.pick` | read | view id, width, height, pixel x and y, camera? | the value under that pixel with its unit, digits, provenance and location, and which point or cell it is - or nothing, where the pixel is off the model (view/AC-027, view/AC-029) |
| `graph.create` | write | workspace id, definition (CT-005), source template id and revision? | workspace graph id and revision (XC-109) |
| `graph.update` | write | graph id, definition | new graph revision |
| `graph.duplicate` | write | graph id, new name | new independent workspace graph id |
| `graph.rename` | write | graph id, new name | new revision; stored id references unchanged |
| `graph.delete` | write | graph id | deleted id; dependent pipeline units retained as unresolved |
| `graph.data` | read | graph id | the series as numbers, with units and provenance |
| `diff.create` | write | case id a, case id b, basis case id | diff id, outside-point count and proportion, round-trip error |
| `report.create` | write | workspace id, definition (CT-006), source template id and revision? | workspace report id and revision (XC-109) |
| `report.update` | write | report id, definition | new report revision |
| `report.duplicate` | write | report id, new name | new independent workspace report id |
| `report.rename` | write | report id, new name | new revision; stored id references unchanged |
| `report.delete` | write | report id | deleted id; dependent pipeline units retained as unresolved |
| `report.export` | write | report id, path | path written, bytes, reductions applied, elements omitted |
| `system.capabilities` | read | - | machine class, renderer backends available, formats and levels |
| `system.protocols` | read | - | protocol versions this engine speaks |
| `history.undo` | write | undo id | ids restored |
| `history.list` | read | workspace id | operations with origin, time and outcome |
| `dataset.probe` | read | dataset id, field name, point in metres, result position | value, association, unit, significant digits, provenance - missing where there is none (view/AC-027) |
| `dataset.parts` | read | dataset id | source-named parts with type, parent identifier where present, counts and bounds (GL-029, GL-042); absent hierarchy remains absent |
| `field.derive` | read | dataset id, field name, quantity from the catalogue, frame? | the derived field with the formula and conventions it used (INV-020) |
| `field.setDisplayUnit` | write | workspace id, quantity, unit symbol | - - presentation only; storage stays canonical (INV-026) |
| `frame.declare` | write | workspace id, name, kind, origin, axis | frame id (XC-122) |
| `measurement.import` | write | case id, values with units and uncertainties, source | ids imported, anything undeclared named (XC-125) |
| `case.proposeTags` | read | case ids | proposals with the signal behind each; nothing applied (XC-120) |
| `template.createFromItem` | write | workspace item id and revision, target scope, name | new template id and revision; source item remains independent (XC-109) |
| `template.apply` | write | template id and revision, workspace id, target selection | resolution result; after acceptance, new independent workspace item id (XC-090, XC-109) |
| `template.promote` | write | template id, target scope | new template id, and what it requires from a target (workspace/AC-037) |
| `template.export` | write | template id, path | path written, assets embedded, assets listed instead of embedded |
| `template.import` | write | path, target scope | template id, origin recorded, unresolved references |
| `library.list` | read | scope? kind? | entries with scope, origin and whether a newer sample exists (XC-130) |
| `pipeline.create` | write | workspace id, definition (CT-009) | pipeline id |
| `pipeline.update` | write | pipeline id, definition | - |
| `pipeline.dryRun` | read | pipeline id, starting cases? | per unit: the target set, loop counts, condition values, artefacts that would be written (pipeline/AC-008) |
| `pipeline.run` | write | pipeline id, starting cases?, destructive authorisation? | run id, and the outcome per case and per unit (XC-046) |
| `pipeline.cancel` | write | run id | the unit boundary it stopped at, and what was kept |
| `script.run` | write | script text or path, authorisation | ids changed, grouped as one undo step (XC-102) |
| `report.provenance` | read | exported path or report id | the inputs it was produced from, and whether any has since changed (INV-027) |
| `system.audit` | read | since? | outbound requests with host, time and what was sent (XC-106) |
| `system.supportBundle` | write | path, consent | the manifest, then the bundle - listed before it is written (operations/AC-008) |
| `workspace.pack` | write | workspace id, path, include data? | path written, size, what it contains, and what could not be included (XC-140) |
| `output.list` | read | workspace id | the runs under the output folder with their sizes and times - and where each time came from - the total against LIM-012, and which runs pruning oldest-first would take (XC-141) |
| `output.plan` | read | workspace id, runs to remove | every file that would go, by path, the records that stay and the bytes freed - shown before anything is deleted (workspace/AC-053) |
| `output.prune` | write | workspace id, runs to remove, expected files? | space recovered, artefacts removed by name - run records are kept, so what was made stays reproducible (XC-141); refused with nothing deleted where the folder no longer matches the plan (XC-268) |

The catalogue grew from twenty-five to forty-five when the features were compared against it: a feature
that specifies behaviour with no operation to invoke it cannot satisfy INV-006, because the interface
would have to reach past the surface to do it. The gate compares the catalogue against its schema
(XC-127); comparing it against the features is still a reading job, and this is what that reading found.

Adding an operation is additive and needs no change to existing callers. **Changing what one means is
forbidden**; the replacement is a new name and the old one is retired with a pointer to it.

## How it is carried

The envelope above is the shape; **HTTP/1.1 with JSON bodies on the loopback interface is how it
travels** (XC-258). `POST /command` takes one request and answers with one response; `GET /handle/{id}`
fetches the bytes a response named; `GET /health` answers the protocol versions and nothing else. The
engine binds 127.0.0.1 on a port the operating system chooses and writes that port and a per-session
token to a file the shell reads. **Every request but `/health` carries the token**, and one without it
is refused with `authorisation.required` - loopback is reachable by every process running as the user,
so a port without a token is a command surface any program on the machine can drive.

The hosted transport (XC-032) is the same framing with a different host and a certificate. A
WebSocket becomes right the day the engine must speak first, and is added beside this rather than
instead of it, because one request and one response fits both.

## Large payloads

Geometry does not travel in a response body. `dataset.describe` and `view.render` return handles, and
the bytes are fetched separately - measured here at 16 MB compressed for a million-point surface, which
is beyond what a request-response envelope should carry (E-051). A handle names its lifetime, and using
one after it expires is a refusal, never a stale answer.

## Errors

An error is a stable identifier, a message resolved through the catalogue (XC-020), and the operation
that produced it. The identifier is what a support conversation quotes and what a caller matches on;
the message text is for people and may be translated (XC-021).

```
{ "status": "refused", "reason": { "id": "unit.undeclared", "message": "...", "operation": "field.statistics" } }
```

Refusals a caller must be prepared for, in every build: `format.unsupported`, `file.unreadable`,
`unit.undeclared`, `association.mismatch`, `limit.exceeded`, `authorisation.required`,
`handle.expired`, `protocol.unsupported`.
