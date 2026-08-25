---
status: draft
updated: 2026-08-25
---

# Contract: engine API

### CT-003 - Engine API
- purpose: the wire form of the command surface (CT-002) between the interface and the engine process,
  and between a remote client and a hosted engine. The same operations, the same shapes, whether the
  engine is a child process on loopback or a service across a network
- schema: schema/CT-003.json
- version: 2.1.0
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

| Operation | Reads or writes | Parameters | Result |
|---|---|---|---|
| `workspace.open` | write | path | workspace id, unresolved cases, format version |
| `workspace.save` | write | workspace id, path? | path written, previous version kept |
| `workspace.close` | write | workspace id | - |
| `case.create` | write | workspace id, parent case id?, name | case id |
| `case.delete` | write | case id | affected descendant ids |
| `case.move` | write | case id, new parent id | - |
| `case.tag` | write | case id, tags | - |
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
| `view.render` | read | view id, width, height, format | image bytes or a handle to them |
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
| `dataset.probe` | read | dataset id, point in metres, result position | value, association, unit, significant digits, provenance - missing where there is none (view/AC-027) |
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
| `output.prune` | write | workspace id, runs to remove | space recovered, artefacts removed - run records are kept, so what was made stays reproducible (XC-141) |

The catalogue grew from twenty-five to forty-five when the features were compared against it: a feature
that specifies behaviour with no operation to invoke it cannot satisfy INV-006, because the interface
would have to reach past the surface to do it. The gate compares the catalogue against its schema
(XC-127); comparing it against the features is still a reading job, and this is what that reading found.

Adding an operation is additive and needs no change to existing callers. **Changing what one means is
forbidden**; the replacement is a new name and the old one is retired with a pointer to it.

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
