---
status: draft
updated: 2026-08-25
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
  machine-readable keyboard scheme for AC-013, no machine-readable parameter list for OPEN-028, and -
  where the gate is run somewhere without a `src/` tree - the generated catalogue it could not compare.
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

### TASK-006 - First run opens a View
- satisfies: AC-001
- depends_on: TASK-005
- done_when: a first launch opens the View area with the sample offered first

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
