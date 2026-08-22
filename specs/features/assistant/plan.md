---
status: draft
updated: 2026-08-19
---

# Plan: assistant and headless operation

- approach: one command bus is the only way anything changes - the interface, the chat and an external
  caller all go through it, and the bus is built before the assistant that talks to it. A language
  model produces commands in a schema with no expression language (XC-080); the bus validates them
  against an allow-list, applies them as one undoable group, and records what happened. External
  protocols are thin adapters over that bus, never a second path
- modules touched: MOD-008 assistant, MOD-007 workspace
- contracts touched: CT-002
- technology: the model provider is the user's own key; the product ships no provider and resells no
  tokens (XC-082)
- risks: this is the feature that can change a @Workspace with nobody watching. Every risk here is a
  risk of a silent, plausible, wrong change

## Order of work

1. the command bus, its validation and its undo grouping (REQ-001)
2. the audit log (REQ-004)
3. the external surface as an adapter, with authorisation (REQ-004, REQ-002)
4. grounding: values carry their origin, and material never outranks data (REQ-003)
5. chat over the same bus (REQ-001)
6. proposals from the template set only (REQ-006)

**The bus comes first and ships even if the assistant does not.** It is what makes the interface
undoable and the product scriptable, and it is the thing that makes an assistant safe to add rather
than the thing the assistant needs.

## What must be proven before this feature is called done

- the command surface and the interface expose the same operation set (INV-006)
- a multi-command instruction undoes as one step, and a failure rolls the whole instruction back
- a value stated by the assistant names whether it came from data or from a document (INV-008)
- with the network blocked and no model configured, everything else still works (INV-007)
