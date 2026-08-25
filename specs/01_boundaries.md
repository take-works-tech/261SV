---
status: draft
updated: 2026-08-26
---

# Modules and dependency direction

Vertical split = capability. Horizontal split = layer. Screen regions and folders are layout, not
boundaries: a panel that shows a graph belongs to the graph module wherever it is drawn.

**Review cost is decided here.** A change inside one module is reviewed inside that module, and the
modules that list it in `depends_on` are the blast radius. The reason this product needs the split
early is its two-sided delivery: the same core runs inside a desktop application and behind a web
service, and a boundary that exists only in one of them is a boundary that does not exist.

## Layers, top to bottom

Dependencies point downward only. A dependency pointing upward is a defect, not a shortcut.

| Layer | May depend on | What lives here |
|---|---|---|
| `ui` | ui-logic, state, shared-ui, domain-core | React components, canvas hosts, panels |
| `ui-logic` | state, client, domain-core | view models, formatting, interaction rules |
| `state` | client, domain-core | workspace document state, selection, undo |
| `client` | domain-core | typed calls to the local service, transport only |
| `service` | engine, domain-core | request handling, session, permissions, agent surface |
| `engine` | domain-core | reading, converting, computing, rendering offscreen |
| `domain-core` | - | types, units, frames, IDs, invariants. Depends on nothing |

`domain-core` is the only module every other module may depend on, and it holds no behaviour that
touches a file, a device or a clock.

## Modules

### MOD-001 - domain-core
- layer: domain-core
- paths: src/domain_core, src/engine/limits.py, src/engine/render_limits.py
- owns: the vocabulary of glossary section 1 as types - @Workspace, @Case, @Variable, @Field, units,
  the canonical frame, ID rules, and the invariants that guard them. Including the **two** geometries
  a @Dataset holds - the connectivity the file declared and the surface it is drawn as, which INV-001
  requires be distinguishable rather than merely distinguished by convention (XC-233)
- depends_on: nothing
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-002 - dataset-io
- layer: engine
- paths: src/engine/reader.py, src/engine/survey.py, src/engine/conversion.py, src/engine/completeness.py, src/engine/exodus.py, src/engine/cgns.py, src/engine/result_axis.py, src/engine/measurements.py, src/engine/dataset_io
- owns: reading result files into a @Dataset, time steps, multi-block and partitioned files, and the
  conversion into the canonical frame, and **the conversions CT-012 names** for the types accepted only
  after one - each run as the contract states it, at a cost read from the source before it is paid. Also
  importing @Measurement data, which is not a result file and has no format standard behind it, from a
  table whose columns are declared rather than recognised.
  Also writing @Dataset out as USD and VDB for the export path
- depends_on: domain-core
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-003 - visualization
- layer: engine
- paths: src/engine/visualization
- owns: turning a @Dataset plus a @View into pixels, colour maps, CT-011 MaterialX graphs, backgrounds,
  and the renderer backends behind one interface. It validates Material Assets, resolves CT-004
  Material Bindings, lowers trusted `solviaResult` requirements to derived VTK/GPU attributes or USD
  primvars, generates target shaders, produces the diagnostic-magenta failure material and publishes
  separate native-VTK and vtk.js capability reports. It also preserves authored reference texture
  coordinates and creates any explicitly required analysis-mesh projection or charted atlas as derived
  display data without changing the source @Dataset (XC-167, XC-174 to XC-178)
- depends_on: domain-core, dataset-io
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-004 - analysis
- layer: engine
- paths: src/engine/analysis
- owns: derived quantities - @Diff between cases, expressions over @Field values, statistics used by
  graphs and by recommendations. Every number a user is shown that was not read from a file is computed here.
  The expression language of [13_scripting.md](13_scripting.md) is evaluated here, dimensions and all
  (XC-242); MOD-011 decides *when* an expression runs and never *what* it evaluates to
- depends_on: domain-core, dataset-io
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-005 - graph
- layer: engine
- paths: src/engine/graph
- owns: graph definitions, the data selection behind them, and their rendering to a figure
- depends_on: domain-core, analysis
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-006 - report
- layer: engine
- paths: src/engine/report
- owns: assembling @Report output - the interactive HTML document, office formats, images and video -
  from @View, @Graph and text. It owns what an output **cannot** carry as well as what it can: the
  writer answers that before it writes, refuses until the list is accepted, and puts the same list in
  the document (XC-254)
- depends_on: domain-core, visualization, graph
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-007 - workspace
- layer: service
- paths: src/service/workspace
- owns: the @Workspace document - hierarchy, @Inheritance, tags, concrete workspace-item identity,
  workspace-scoped template identity and preference values, persistence, versioning, migration and
  recovery. It preserves the separation between working artefacts and reusable library entries
  (XC-109). Workspace preferences are exposed as explicitly scoped sections in the dedicated Settings
  page; this module does not own global application preferences or workspace-editor panel state (XC-165)
- depends_on: domain-core
- decidedness: Fixed
- basis: E-001 (T1), E-088 (T1)

### MOD-008 - assistant
- layer: service
- paths: src/service/assistant
- owns: natural-language operation - turning a sentence into commands, choosing what reference material
  to consult, and the rule that data beats documents. It **uses** the command surface and asks MOD-014
  for anything that leaves the machine; it owns neither
- depends_on: domain-core, workspace, command, egress
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-009 - app-shell
- layer: ui
- paths: src/ui/shell
- owns: windows, global navigation, navigation between work areas, licensing and update surface, and
  the dedicated Settings page shell. Settings composes its own category navigation and content without
  workspace-editor sidebars, panel toggles or the natural-language instruction bar (XC-165)
- depends_on: domain-core, shared-ui, workspace, assistant
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-010 - shared-ui
- layer: ui
- paths: src/ui/shared
- owns: the components named in [11_ui.md](11_ui.md) - one implementation each
- depends_on: domain-core
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-012 - command
- layer: service
- paths: src/service/command
- owns: the one command surface (CT-002) - dispatch, validation, undo grouping, the dry-run mode, and
  the log every command is recorded in
- depends_on: domain-core, dataset-io, visualization, analysis, graph, report, workspace
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-011 - pipeline
- layer: service
- paths: src/service/pipeline
- owns: the registered flows of a @Workspace (CT-009) - editing, case resolution, dry run, execution
  with per-case isolation, the run record, and the headless entry point
- depends_on: domain-core, workspace, command, analysis
  (`analysis` because a formula, a condition and a variable-driven loop count are expressions, and
  MOD-004 owns what an expression evaluates to. MOD-011 decides only *when* one runs; an evaluator of
  its own here would be a second answer to the same question)
- decidedness: Fixed
- basis: E-001 (T1)

**Why `command` is a module and not part of `assistant`.** The command surface began as the assistant's
way of acting, which made every other caller - the pipeline, the headless entry point, the instruction
bar - depend on the language-model module to press a button. One surface with several callers is a
module; a surface owned by one of its callers is a dependency waiting to be inverted (INV-006).

### MOD-013 - scripting
- layer: service
- paths: src/service/scripting
- owns: the Python surface (13_scripting.md) - the object model scripts reach, name and identifier
  resolution, the sandbox scripts run in, and the recording of interface actions as script text. It
  **builds documents and issues commands**; it holds no behaviour of its own
- depends_on: domain-core, command, workspace, pipeline
  (`pipeline` because `sv.pipeline` in 13_scripting.md's object model builds a CT-009 document, and
  MOD-011 owns what a valid one is. Building it here instead would be a second implementation of the
  edit-time rules, and the copy would be the one that stopped refusing)
- decidedness: Fixed
- basis: E-064 (T1)

### MOD-015 - ui-logic
- layer: ui-logic
- paths: src/ui/logic
- owns: view models, formatting for display, and interaction rules - what a panel shows given a state,
  what a gesture means, and how a value is written for a person to read. It holds **no** React component
  and **no** transport: a rule that can only be exercised by rendering a component is a rule nobody
  tests
- depends_on: state, client, domain-core
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-016 - state
- layer: state
- paths: src/ui/state
- owns: the @Workspace document as the interface holds it, the current selection, and the undo history
  as the interface presents it. It is the **client-side** view of state and never the authority: the
  authority is MOD-007 through the command surface, and a divergence between the two is resolved by
  asking rather than by merging
- depends_on: client, domain-core
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-017 - client
- layer: client
- paths: src/ui/client
- owns: typed calls to the local service and **nothing else** - one function per CT-003 operation,
  the transport under them, and the failure of the transport itself. It holds no retry policy, no
  caching and no interpretation of a result: each of those is a decision some layer above should be
  making visibly
- depends_on: domain-core
- decidedness: Fixed
- basis: E-001 (T1)

### MOD-014 - egress
- layer: service
- paths: src/service/egress
- owns: **every request that leaves this machine** - language-model calls, web search, update checks -
  with the permission each requires, the audit of what was sent, and the offline state. Nothing else in
  the product opens a connection.
  It also owns the **local diagnostic log** and the **support bundle** (XC-126). They are not requests,
  and they live here because the rule that governs them is the rule this module enforces: a log carries
  no field value, a bundle lists what it contains before it exists, and neither goes anywhere without
  consent. Splitting them off would put the redaction rule in one module and the sending rule in
  another, which is how a value reaches a bundle that egress then faithfully sends
- depends_on: domain-core
- decidedness: Fixed
- basis: E-001 (T1)

## Extension seams

**A new capability is added at a seam, and a seam is a place where adding one changes nothing else.**
These are the seams this architecture has, and the rule for each is the same: register the new thing,
and no caller changes.

| To add | Where | What must not change |
|---|---|---|
| a reader for a format | the reader table in MOD-002 | nothing above MOD-002 knows which reader ran |
| a pipeline unit kind | the unit table of CT-009, executed by MOD-011 | stored pipelines stay readable; a unit kind never changes meaning |
| a source of reference material | a retriever registered with MOD-014, permission-gated | nothing above MOD-014 knows whether an answer came from disk or the network |
| a function in the expression language | the function table of [13_scripting.md](13_scripting.md) | the language stays evaluable without an interpreter (XC-101) |
| an export format | a writer registered with MOD-006 | the report definition (CT-006) gains an enumerated target, not a new shape |
| a renderer backend | a backend registered with MOD-003 behind the one interface | the view definition (CT-004) gains an enumerated value; numbers are unaffected (INV-002) |
| an operation | the catalogue in CT-003 | existing operations keep their names and meanings; additive only |
| a MaterialX node or Material Asset | a trusted node library or CT-011 graph interpreted by MOD-003 | CT-004 keeps typed input bindings; no caller gains a PBR/result material kind (XC-174) |
| a colour map, representation or block type | an enumerated value plus one handler | the definitions in CT-004, CT-005 and CT-006 keep their shape |
| a language | a message catalogue file (XC-021) | no code changes at all - this is the test of whether the seam is real |
| an analysis filter | MOD-004, with a verification entry before it is exposed | nothing computes numbers outside MOD-004 |

**A change that has to touch a caller is a sign the seam is in the wrong place.** When that happens the
answer is to move the seam, not to make the change and move on - the second choice is how a codebase
stops being extensible one small exception at a time.

## Rules

Before adding a dependency, try in order: push the shared thing down into `domain-core`, lift it up
into `app-shell`, or accept that the two modules are really one. **Bidirectional dependency is never
allowed** - if neither direction can be removed, a third module is waiting to be extracted.

The desktop application and the web service differ only in how `service` is reached: in the desktop
build the client talks to a local process, in the web build to a remote one. **No module above
`client` may know which**, because the moment one does, the two products start to diverge and every
feature has to be built twice.
