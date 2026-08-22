---
status: draft
updated: 2026-08-20
---

# Feature: assistant and headless operation

## Users and purpose

- intended user: an engineer who would rather say what they want than find it in a menu, and an
  external program or language model driving the product with no human present
- job to be done: operate the product by instruction, and get commentary that is grounded in the
  loaded data rather than in a plausible-sounding paragraph
- success condition: an instruction either happens exactly and is undoable as one step, or does not
  happen and says why - and every number the assistant states can be traced to where it came from

## Out of scope

- the assistant deciding engineering conclusions on the user's behalf
- generating arbitrary code that runs in the product
- any operation the interface does not also offer (INV-006)
- sending @Dataset content anywhere without an explicit, per-workspace opt-in

## Files and interfaces involved

- MOD-008 assistant, MOD-007 workspace
- the command surface contract (CT-002)
- the chat area of [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - Every instruction maps to a command a user could issue
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-001: When an instruction is accepted, the system shall execute it through the same command
    surface the interface uses, with the same validation
  - AC-002: When an instruction produces several commands, the system shall apply them as one undoable
    step
  - AC-003: If an instruction cannot be mapped to a command, then the system shall say what it could not
    map and shall change nothing
  - AC-004: If part of a multi-command instruction fails, then the system shall roll back the whole
    instruction and shall report which part failed

### REQ-002 - Destructive and wide-reaching instructions are confirmed
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-005: Where an instruction would delete a @Case, overwrite a file, or change an inherited
    @Variable, the system shall describe the effect and the number of places affected before applying it
  - AC-006: While @Headless agent mode is active, the system shall apply the same confirmation policy,
    refusing rather than assuming consent, unless the caller supplied explicit authorisation for that
    class of operation

### REQ-003 - Data outranks documents
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-007: When the assistant states a value, the system shall show whether it came from a @Dataset or
    from @Reference material, and shall name the source
  - AC-008: If @Reference material contradicts the loaded @Dataset, then the system shall report the
    @Dataset value and shall state that the material disagrees
  - AC-009: If a value cannot be found in the @Dataset, then the system shall say it is not available
    rather than taking it from @Reference material

### REQ-004 - The product is operable with no human present
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-010: When an external caller connects to the command surface, the system shall expose the same
    operation set as the interface, with machine-readable results
  - AC-011: When an operation completes, the system shall record it in an audit log with its inputs,
    its outcome and its origin
  - AC-012: If the command surface receives an unknown or malformed command, then the system shall
    reject it, name the problem, and change nothing

### REQ-005 - Language-model use is optional, visible and refusable
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-013: While no language model is configured, the system shall remain fully operable through the
    interface and the command surface
  - AC-014: Where a language model is configured, the system shall state which data would leave the
    machine before it leaves, per workspace
  - AC-015: If a configured language model is unreachable, then the system shall report it and shall
    continue to run every operation that does not need it

### REQ-006 - Generated visual and graph definitions stay inside the safe set
- priority: SHOULD
- phase: later
- decidedness: Open
- open: OPEN-006
- acceptance:
  - AC-016: Where the assistant proposes a @Graph or @View configuration, the system shall build it
    from the template set rather than executing generated code
  - AC-017: If a proposal cannot be expressed in the template set, then the system shall say so instead
    of approximating it

### REQ-007 - Searching the web is a permission, not a capability
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1), E-065 (T1)
- acceptance:
  - AC-018: While search is not permitted for the @Workspace, the system shall send no request and shall
    state which question it could not answer without one, and the rest of the operation shall continue
    (XC-106)
  - AC-019: When a search is about to be sent, the system shall show the query that will leave the
    machine, and where per-search confirmation is configured shall not send it until it is confirmed
  - AC-020: If a query would contain a value, @Case name or file path from the workspace, then the
    system shall withhold it unless the user has allowed it for that search
  - AC-021: When any request leaves the machine, the system shall record it - what was sent, to which
    host, and when - in an audit the user can read and export
  - AC-022: If a host is not on the workspace's allow-list, then the system shall refuse the request and
    shall name the host, rather than silently substituting another source

### REQ-008 - Retrieved material is evidence with a date, never a source of numbers
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-072 (T2)
- acceptance:
  - AC-023: When a search returns results, the system shall store each retained result as reference
    material with its address and retrieval date, and shall offer it to generation only by identifier
    (XC-105)
  - AC-024: If a retrieved document states a value that contradicts the @Dataset, then the system shall
    carry the data value and state the disagreement (XC-013)
  - AC-025: If a search returns nothing retained, then the system shall state that nothing was found for
    the query shown, and shall not answer from the model's own memory instead

### REQ-009 - Chat works like a conversation, with its costs stated
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-006 (T1)
- acceptance:
  - AC-026: When chat is used, the system shall allow the model and its effort level to be chosen, and
    shall list the models the provider reports rather than a compiled-in set (XC-116)
  - AC-027: Where deep research is requested, the system shall require its own permission, separate
    from ordinary search, and shall state the number of requests it intends and the estimated cost
    before starting (XC-115)
  - AC-028: If a chosen model is unavailable, then the system shall report it by name and keep the
    previous choice rather than substituting one
  - AC-029: When report generation specifies its own model or effort, the system shall use it for that
    report and leave the product-wide setting unchanged

### REQ-010 - Chat is not an exception to the network permission
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-030: While search is not permitted for the @Workspace, the system shall refuse to search from
    chat as well, and shall say so in the conversation (XC-106)
  - AC-031: When chat searches, the system shall show the query, apply the host allow-list, and record
    the request in the same audit as every other outbound request

### REQ-011 - The assistant is measured against a kept evaluation set
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-032: When the build runs, the system shall evaluate recorded instructions against the commands
    they should produce and shall report the pass rate against a stated bar (XC-138)
  - AC-033: When the model or the prompt changes, the system shall re-run the evaluation set so a
    regression is visible before release rather than after
  - AC-034: If the evaluation set cannot be run - no model configured in the build - then the system
    shall report that it was skipped rather than reporting a pass

### REQ-012 - What the model knows about the product is generated from the contracts
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-035: When the assistant is given its capability description, the system shall generate it from
    CT-002 and CT-003 rather than from a maintained copy (XC-139)
  - AC-036: When the assistant is given workspace context, the system shall send the case tree, the
    quantity list with units and @Provenance, the templates and the states - and no bulk numeric data
    (XC-097)
  - AC-037: If an operation is added or removed, then the description the model receives shall change
    with it, without anyone editing a second file

### REQ-013 - The instruction bar and Chat mode are one conversation
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-080 (T1)
- acceptance:
  - AC-038: When an instruction is submitted from the centre-bottom instruction bar or Chat mode, the
    system shall append it exactly once to the same active conversation and shall expose the same ordered
    user message, response and command activity from both surfaces (XC-150)
  - AC-039: When the user moves between any work area and Chat mode, the system shall preserve the active
    conversation identifier, draft, pending response, confirmation, failure and conversation settings,
    changing only the compact or full-height presentation
  - AC-040: When the user selects another conversation in Chat mode, the instruction bar shall address
    that same newly active conversation and shall not create or retain a hidden quick-command conversation
  - AC-041: Whether input originates in the instruction bar or Chat mode, command mapping, validation,
    undo grouping, permissions, provenance and audit behaviour shall be identical
  - AC-042: When the user opens the assistant from a non-Chat work area, the system shall show the active
    conversation in a dismissible drawer over the right edge of the central work surface, immediately
    left of and without replacing or resizing the right properties sidebar (XC-151)
  - AC-043: While the conversation drawer is open, the system shall render the one active composer at
    the drawer bottom and shall not leave another active instruction input underneath it
  - AC-044: When the user closes the conversation drawer or chooses `チャットで開く`, the system shall
    preserve the active conversation identifier, ordered history, draft and pending state while changing
    only among compact, drawer and full-height presentations
  - AC-045: If the available centre width is narrow, then the drawer shall remain dismissible, may cover
    the available central work surface, and shall not cause application-level horizontal or vertical
    scrolling

## End-to-end verification

With networking disabled and no model configured, drive the product entirely through the command
surface: load a @Case, create a @View, export a report, and confirm the audit log records each step.
Then configure a model, ask in chat for a value that exists in the data and one that exists only in a
contradicting reference document, and confirm the first is answered from the @Dataset with its origin
named and the second is reported as a disagreement rather than answered from the document. Start one
conversation in the instruction bar, continue it in the work-area drawer, open the same conversation in
Chat mode, return to another work area and confirm the ordered history, draft, active settings and any
pending or completed result remain one shared state. Confirm that only one composer is active in each
presentation and that the drawer does not replace the right properties sidebar.
