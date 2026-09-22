---
status: draft
updated: 2026-09-22
---

# Tasks: running the product

### TASK-001 - Contract coverage gate
- satisfies: AC-010
- depends_on: -
- done_when: an operation present in CT-003 and absent from CT-002, or the reverse, fails the gate,
  proven by adding one in each direction
- done: 2026-08-25, `validate/check_commands.py`, proven in both directions by
  `tests/test_check_commands.py`.
  It was half done and reported as whole, which is worth writing down. The gate compared CT-003's
  catalogue against **CT-003's own schema** and nothing compared it against CT-002 - and CT-002's
  `command` was an unconstrained string, so the abstract surface could not refuse the unknown command
  its own prose says it refuses. AC-010 asks for the comparison between the two contracts, and that half
  did not exist.
  Fixed by removing the second set rather than by comparing two: CT-002's `command` now refers to
  CT-003's enumeration (`$ref CT-003.json#/properties/operation`), so there is one set and no copy to
  drift. The gate still fails an operation present in one and absent from the other, proven against a
  surface that lists its own set, and fails an unconstrained `command` outright.
### TASK-002 - The gate reports its own blind spots
- satisfies: AC-012
- depends_on: TASK-001
- done_when: the output names what was checked and what could not be, and a run with no interface code
  says so rather than reporting success
- done: 2026-08-25. Every run prints what it checked and what it could not, and the blind spots
  are part of the output rather than a comment: no interface code to examine for AC-011, no
  machine-readable keyboard scheme for AC-013, and - where the gate is run somewhere without a `src/`
  tree - the generated catalogue it could not compare.
  One of those blind spots closed the same day. OPEN-028 said CT-003 stated its parameters in prose, so
  nothing compared a handler's declaration against the contract; the contract now carries a parameter
  schema per operation - 134 parameters over 61 operations - the generated catalogue carries them into
  the code, and a handler **cannot declare its own** any more. What CT-002 promises about an unknown
  parameter is now a promise against the contract rather than against whatever the handler listed.
  A gate that finds nothing and reports success is worse than no gate, because it is believed.
### TASK-003 - Interface actions dispatch commands
- satisfies: AC-011
- depends_on: TASK-002
- done_when: an interface action that mutates state without a command fails the gate

### TASK-004 - Keyboard scheme
- satisfies: AC-013
- depends_on: TASK-001
- done_when: every command has a keyboard route following the documented scheme

### TASK-005 - Generated sample workspace
- satisfies: AC-002
- depends_on: ingest/TASK-001
- done_when: the sample ships with data this project generated, carrying no third-party terms
- done: 2026-09-21 (XC-298, #237). The sample is code: `engine/sample.py` generates a cantilever
  beam from beam theory and `workspace.sample` writes it, with two cases and the units its author
  declares, where the person chose; nothing is shipped as data and nothing is copied from the
  installation. `tests/test_sample.py` checks the file against the formulas (E-220).

### TASK-006 - First run opens a View
- satisfies: AC-001
- depends_on: TASK-005
- done_when: a first launch opens the View area with the sample offered first
- partly done: 2026-09-21 (XC-298). The Workspace list offers the sample first while nothing was
  opened yet, and opening it lands in the View area with the first case drawn. The launch itself
  still lands on the Workspace list rather than the View area; that landing is what remains.

### TASK-007 - Empty workspace still opens a View
- satisfies: AC-003
- depends_on: TASK-006
- done_when: choosing empty opens the View area with its empty state, not a dialogue

### TASK-008 - Tutorial pointing at real controls
- satisfies: AC-004
- depends_on: TASK-006
- done_when: steps point at live controls and advance on use

### TASK-009 - Tutorial resume
- satisfies: AC-005
- depends_on: TASK-008
- done_when: dismissing records the position and resuming continues from it

### TASK-010 - Tutorial never blocks
- satisfies: AC-006
- depends_on: TASK-008
- done_when: an unexpected action is allowed and the tutorial re-points

### TASK-011 - Logs without field values
- satisfies: AC-007
- depends_on: -
- done_when: a test asserts no field value appears in any log line
- done: 2026-08-25, `src/service/egress/diagnostics.py`. A log line **cannot carry a float**, and the
  rule is the type rather than a review habit: names are strings, counts are integers (INV-015), and a
  value measured from a dataset is a float - so refusing floats catches the shape a field value arrives
  in. An array is refused for the same reason.
  What it does **not** catch is a float somebody formatted into a string first, and there is a test
  asserting that limit rather than leaving it to be discovered by whoever relies on the check. It makes
  the accident hard and does not make the deliberate act impossible.
  The log stays local, asserted structurally: the module reaches no network client, so it cannot send
  itself whatever it currently does (XC-126).
### TASK-012 - Support bundle manifest
- satisfies: AC-008
- depends_on: TASK-011
- done_when: the manifest lists case names and paths before the bundle is created
- done: 2026-08-25. The manifest exists **before** the bundle: `create` takes the manifest rather
  than the ingredients, so a bundle cannot come into being without a list having been shown. One that
  reported its contents afterwards is a bundle somebody found out about.
  Case names and file paths are listed **individually** rather than counted. "3 files" is a number
  somebody accepts without reading; a customer's part name in the list is the thing they would have
  objected to, and they can only object to what they can see - so the manifest also says which of its
  entries are the customer's own information.
  Two acceptances are needed and they are different: one for what goes into the bundle, one for sending
  it. Accepting the manifest is not agreeing to send it anywhere, and the gate refuses without its own
  consent (XC-126). What the audit records is the **manifest's own lines**, so what was audited is what
  the user accepted - two descriptions of one bundle is one too many.
### TASK-013 - Consent and audit for transfer
- satisfies: AC-009
- depends_on: TASK-012, assistant/TASK-018
- done_when: sending requires consent and appears in the outbound audit
- done: 2026-08-25. Satisfied by the two halves that landed together: `service/egress/diagnostics.py`
  requires the manifest to be accepted before a bundle exists, and `service/egress/gate.py` requires
  explicit consent before it leaves and records the transfer in the outbound audit (XC-106).
  The two acceptances are deliberately separate and both are tested: accepting what goes **into** the
  bundle is not agreeing to **send** it, and the gate refuses without its own consent. What the audit
  records is the manifest's own lines, so what was audited is what the user accepted.
### TASK-014 - Samples update alongside
- satisfies: AC-018
- depends_on: workspace/TASK-029
- done_when: an updated sample is added without touching user copies

### TASK-015 - Newer-version notice on copies
- satisfies: AC-019
- depends_on: TASK-014
- done_when: a copy with a sample origin shows that a newer version exists

### TASK-016 - Headless authentication
- satisfies: AC-014
- depends_on: pipeline/TASK-034
- done_when: an unknown caller is refused by default

### TASK-017 - Per-workspace authorisation
- satisfies: AC-015
- depends_on: TASK-016
- done_when: authorisation is granted per workspace, not per installation

### TASK-018 - Identity in the audit
- satisfies: AC-016
- depends_on: TASK-016
- done_when: every operation records the identity that issued it

### TASK-019 - Agents get no implicit trust
- satisfies: AC-017
- depends_on: TASK-018
- done_when: an agent caller has exactly the rights of its authenticated identity

### TASK-020 - Launch budget
- satisfies: AC-020
- depends_on: TASK-006
- done_when: launch to first rendered result is measured on the E-063 class and recorded in LIM-010

### TASK-021 - Selection budget
- satisfies: AC-021
- depends_on: TASK-020
- done_when: selection to reflected change is measured and recorded in LIM-011

### TASK-022 - Shared-component uniqueness gate
- satisfies: AC-022
- depends_on: TASK-002
- done_when: each component of the shared table resolves to one implementation in its owning module

### TASK-023 - A second implementation fails the gate
- satisfies: AC-023
- depends_on: TASK-022
- done_when: a deliberate duplicate is reported with both locations named

### TASK-024 - The gate admits when it cannot look
- satisfies: AC-024
- depends_on: TASK-022
- done_when: with no interface code the output says so rather than claiming uniqueness

### TASK-025 - The failure report type
- satisfies: AC-025
- depends_on: -
- done_when: one type carries reason, subject, missing and changed, and validates against CT-010

### TASK-026 - Nothing internal in what a person reads
- satisfies: AC-026
- depends_on: TASK-025
- done_when: summaries carry no paths or stacks and logs carry no field values

### TASK-027 - Refusals are distinguishable from failures
- satisfies: AC-027
- depends_on: TASK-025
- done_when: a caller can branch on the group without reading the sentence

### TASK-028 - Headless exit status follows the group
- satisfies: AC-028
- depends_on: TASK-025, pipeline/TASK-034
- done_when: partial results exit zero and real failures do not

### TASK-029 - The command list is generated and the engine says what answers
- satisfies: AC-029
- depends_on: TASK-001
- done_when: the settings list every operation of CT-003 from the generated catalogue with its
  class, parameters and answer members, and mark each as answered or not from `system.operations`
- done: 2026-09-20 (XC-277, CT-003 3.7.0). `validate/check_client_types.py` emits
  `OPERATION_FACTS` beside the types, from the schema and the catalogue table's class column;
  `src/ui/logic/commands.ts` groups and filters the rows; the shortcut section shows them under the
  design-state keymap, labelled as such with an engine. No operation has a key, and each row says so

### TASK-030 - The command palette
- satisfies: AC-030
- depends_on: TASK-029
- done_when: the top bar's palette lists every operation, runs one whose parameters the interface
  holds through the store's own dispatch, refuses the rest with the reason, and shows the answer as
  given
- done: 2026-09-20 (XC-278). `src/ui/logic/palette.ts` decides what can run and with what;
  `engineState.run` dispatches through the same `ask` as every screen, so a write enters the journal;
  the refusal comes back as the outcome's reason. No key is bound
### TASK-031 - Each area says which case it shows, and follows the tree or is pinned
- satisfies: AC-021
- depends_on: TASK-021
- done_when: with an engine connected, the case tree lists the document's cases; each of the View,
  Graph and Report areas names in its header the case it shows and why; selecting another case moves
  every following area, a pinned one stays, and an item that names its cases is not overridden
- done: 2026-09-21 (XC-292). `src/ui/logic/subject.ts` holds the rule and the labels;
  `src/ui/state/session.ts` holds the tree selection and the per-area binding (16_application_model
  §8.2); `src/ui/state/engine.ts` keeps what was loaded per case and moves the View area with its
  subject, and asks `graph.data` with the Graph area's case as its context (CT-003 3.15.0);
  `src/ui/shared/SubjectBadge.tsx` is the header badge with its one control. Proven by
  `src/ui/logic/subject.test.ts` and the two-case thread in `src/ui/state/engine.connected.test.ts`.
  The LIM-011 budget itself stays TASK-021: it is unmeasured, and this task does not claim it.

### TASK-032 - The support bundle, listed and written
- satisfies: AC-031
- depends_on: TASK-012
- done_when: the list can be read before anything exists, the case names and paths are the person's
  choice, the free text of the log goes in only with both, the archive is whole or absent, and a
  bundle whose list was not shown is refused
- done: 2026-09-22 (XC-302, CT-003 3.19.0, #231, #419). `system.supportManifest` answers the list
  from `src/service/egress/diagnostics.py` (`manifest_for` with `Include`), the session keeps it as
  shown, and `system.supportBundle` writes the archive (`write_bundle`: `manifest.txt`,
  `manifest.json`, `environment.json`, the log as JSON lines with its free text kept or replaced,
  `cases.json` and `sources.json` where listed) beside its target and moves it into place. The
  Settings page's 診断 panel asks the engine for the list whenever the choice changes and creates
  the file where the shell's save dialogue says; the design state stays for a page with no engine.
  Proven by `tests/test_diagnostics.py::TestTheBundleOnDisk`,
  `tests/test_handlers.py::TestASupportBundle` and the sample thread of
  `src/ui/state/engine.connected.test.ts`. Sending remains the gate's (TASK-013) and this build
  injects no transport.

### TASK-033 - What is on screen while the engine starts, and how long it took
- satisfies: AC-032
- depends_on: TASK-012
- done_when: under the shell the page shows the engine starting, counted, until the engine answers,
  and the reason with a restart if it failed; the shell's notes record the launch timeline; the
  launch is measured and recorded as evidence
- done: 2026-09-22 (XC-304, E-222, #307). `src/ui/shared/EngineStarting.tsx` replaces every screen
  under the shell until `/health` answers, with `src/ui/logic/startup.ts` choosing the words; the
  store gained the `starting` reachability the shell already reported; `src/shell/main.ts` records
  the window, the interface and the engine in milliseconds after its start, prints them under
  `--measure-launch` and keeps a `--profile` launch out of the person's profile;
  `spike/measure_launch.py` measures and `spike/results.json` `launch` records. Proven by
  `src/ui/logic/startup.test.ts` and `src/ui/state/reachability.test.ts`; the measurement is the
  evidence's.

### TASK-034 - The budgets as numbers, and the overrun said
- satisfies: AC-033
- depends_on: TASK-033
- done_when: LIM-010 and LIM-011 hold numbers with one source of truth, a launch past the budget
  says so on the starting page, a switch past the budget says so in the work-area bar, and the
  selection measurement is recorded as evidence
- done: 2026-09-22 (XC-305, E-223, E-224, #243). `src/ui/logic/budgets.ts` holds both numbers;
  `describeStartup` names the launch budget once passed; the store times every subject move and
  the work-area bar shows `describeReflection` when over. Proven by `src/ui/logic/budgets.test.ts`
  and the connected thread, which measures six switches and records them; OPEN-017 is closed.
