---
status: draft
updated: 2026-08-20
---

# Tasks: assistant and headless operation

### TASK-001 - Command bus with validation
- satisfies: AC-001
- depends_on: workspace/TASK-001
- done_when: every state change in the product goes through one bus, and an unknown or malformed
  command is refused with a named reason and no state change (AC-012)

### TASK-002 - Undo grouping
- satisfies: AC-002
- depends_on: TASK-001
- done_when: commands sharing a group apply and undo as one step

### TASK-003 - Rollback on partial failure
- satisfies: AC-004
- depends_on: TASK-002
- done_when: a group whose second command fails leaves the @Workspace as it was and names the part that
  failed

### TASK-004 - Effect summary and dry run
- satisfies: AC-005
- depends_on: TASK-001
- done_when: a command can be asked what it would change without applying it, and destructive or
  wide-reaching commands report the number of places affected

### TASK-005 - Audit log
- satisfies: AC-011
- depends_on: TASK-001
- done_when: every operation records its inputs, its outcome and its origin - interface, chat or
  external - in a local log the user can read

### TASK-006 - Operation set parity
- satisfies: AC-010
- depends_on: TASK-001
- done_when: a test asserts the interface and the command surface expose the same operations (INV-006)

### TASK-007 - External adapter with authorisation
- satisfies: AC-006
- depends_on: TASK-004, TASK-006
- done_when: an external caller reaches the bus with machine-readable results, and operations needing
  confirmation are refused without explicit authorisation rather than assumed

### TASK-008 - Value origin recorded
- satisfies: AC-007
- depends_on: TASK-001
- done_when: every value the assistant can state carries whether it came from a @Dataset or from
  @Reference material, with the source named

### TASK-009 - Data outranks documents
- satisfies: AC-008
- depends_on: TASK-008
- done_when: a reference document contradicting the loaded data yields the dataset value with the
  disagreement stated, asserted by a test that plants the contradiction (INV-008)

### TASK-010 - Absent values are absent
- satisfies: AC-009
- depends_on: TASK-008
- done_when: a value not present in the @Dataset is reported unavailable rather than taken from a
  document

### TASK-011 - Configuration schema without an evaluator
- satisfies: AC-016
- depends_on: TASK-001
- done_when: view and graph configurations are expressed as enumerated values and identifiers with no
  expression field, validated against an allow-list on arrival (XC-080)

### TASK-012 - Requests outside the schema are refused
- satisfies: AC-017
- depends_on: TASK-011
- done_when: a request that cannot be expressed in the schema is refused with what was not expressible,
  rather than approximated

### TASK-013 - Instruction to command mapping
- satisfies: AC-003
- depends_on: TASK-011
- done_when: an instruction that cannot be mapped changes nothing and says what it could not map

### TASK-014 - Working without a model
- satisfies: AC-013
- depends_on: TASK-006
- done_when: with no model configured and the network blocked, every operation except the assistant
  itself completes (INV-007)

### TASK-015 - Disclosure before data leaves
- satisfies: AC-014
- depends_on: TASK-014
- done_when: configuring a model states which data would leave the machine, per workspace, before any
  request is made

### TASK-016 - Provider unreachable
- satisfies: AC-015
- depends_on: TASK-015
- done_when: an unreachable provider is reported and every operation not needing it continues

### TASK-018 - One module for everything that leaves the machine
- satisfies: AC-021
- depends_on: TASK-001
- done_when: every outbound request goes through MOD-014 and lands in an exportable audit, asserted by
  a test that fails if any other module opens a connection

### TASK-019 - Search permission per workspace
- satisfies: AC-018
- depends_on: TASK-018
- done_when: a fresh workspace permits nothing, and a denied search names the unanswered question

### TASK-020 - The query is shown before it is sent
- satisfies: AC-019
- depends_on: TASK-019
- done_when: the query is visible, and per-search confirmation blocks sending until confirmed

### TASK-021 - Workspace content withheld from queries
- satisfies: AC-020
- depends_on: TASK-020
- done_when: values, case names and paths are stripped unless allowed for that search

### TASK-022 - Host allow-list
- satisfies: AC-022
- depends_on: TASK-018
- done_when: an unlisted host is refused by name, with no fallback source

### TASK-023 - Results become dated reference material
- satisfies: AC-023
- depends_on: TASK-018
- done_when: retained results carry address and retrieval date and are offered only by identifier

### TASK-024 - Data beats retrieved documents
- satisfies: AC-024
- depends_on: TASK-023
- done_when: a contradicting document yields the data value plus a stated disagreement

### TASK-025 - Empty results do not fall back to memory
- satisfies: AC-025
- depends_on: TASK-023
- done_when: nothing found is reported as nothing found, with the query shown

### TASK-026 - Model and effort selection
- satisfies: AC-026
- depends_on: TASK-001
- done_when: models come from the provider, and effort is selectable, with no compiled-in list

### TASK-027 - Deep research permission and cost preview
- satisfies: AC-027
- depends_on: TASK-018, TASK-026
- done_when: a separate toggle gates it and the intended request count and estimated cost are stated first

### TASK-028 - Unavailable models
- satisfies: AC-028
- depends_on: TASK-026
- done_when: an unavailable model is named and the previous choice kept

### TASK-029 - Report-level override
- satisfies: AC-029
- depends_on: TASK-026
- done_when: a report may set model and effort without changing the product setting

### TASK-030 - Chat obeys the network permission
- satisfies: AC-030
- depends_on: TASK-019
- done_when: chat cannot search where the workspace forbids it, and says so

### TASK-031 - Chat searches are audited like any other
- satisfies: AC-031
- depends_on: TASK-030
- done_when: query shown, allow-list applied, request in the same audit

### TASK-032 - The evaluation set
- satisfies: AC-032
- depends_on: TASK-001
- done_when: recorded instructions run against expected commands with a pass rate against a stated bar

### TASK-033 - Re-run on model or prompt change
- satisfies: AC-033
- depends_on: TASK-032
- done_when: changing either re-runs the set before release

### TASK-034 - A skipped evaluation is not a pass
- satisfies: AC-034
- depends_on: TASK-032
- done_when: a build with no model reports the evaluation as skipped

### TASK-035 - Capability description generated from the contracts
- satisfies: AC-035
- depends_on: TASK-001
- done_when: the description is produced from CT-002 and CT-003 with no maintained copy

### TASK-036 - Context without bulk numbers
- satisfies: AC-036
- depends_on: TASK-035
- done_when: a test asserts no field-value array reaches the model

### TASK-037 - Adding an operation needs one edit
- satisfies: AC-037
- depends_on: TASK-035
- done_when: adding an operation changes the description without a second file being touched

### TASK-038 - One conversation store for both UI surfaces
- satisfies: AC-038
- depends_on: TASK-001
- done_when: instruction-bar and Chat submissions append exactly once to one ordered active-conversation
  store, and both render the same messages, responses and command activity

### TASK-039 - Preserve conversation state while changing presentation
- satisfies: AC-039
- depends_on: TASK-038
- done_when: moving between a work area and Chat preserves the conversation id, draft, pending response,
  confirmations, failures and settings while changing only compact versus full-height rendering

### TASK-040 - Conversation selection controls both surfaces
- satisfies: AC-040
- depends_on: TASK-038
- done_when: selecting a conversation in Chat immediately makes it the instruction bar's conversation,
  with no hidden quick-command session left behind

### TASK-041 - Prove behaviour parity between the two composers
- satisfies: AC-041
- depends_on: TASK-038, TASK-039, TASK-040
- done_when: one parametrized integration test submits equivalent inputs through each surface and asserts
  identical command mapping, validation, undo, permissions, provenance and audit results

### TASK-042 - Add the work-area conversation drawer
- satisfies: AC-042
- depends_on: TASK-038
- done_when: every non-Chat work area can reveal the active conversation in a dismissible right overlay
  inside the central surface while the existing right properties sidebar remains in place

### TASK-043 - Keep exactly one active composer
- satisfies: AC-043
- depends_on: TASK-042
- done_when: opening the drawer moves the shared composer to its bottom and removes the compact input
  until the drawer closes

### TASK-044 - Preserve one conversation across all three presentations
- satisfies: AC-044
- depends_on: TASK-039, TASK-042, TASK-043
- done_when: compact, drawer and full-height Chat preserve one id, history, draft and pending state, and
  `チャットで開く` changes presentation without copying or replaying anything

### TASK-045 - Keep the drawer safe at narrow widths
- satisfies: AC-045
- depends_on: TASK-042
- done_when: the drawer can cover the available centre surface, remains dismissible and creates no
  application-level overflow
