---
status: draft
updated: 2026-08-20
---

# Contract: command surface

### CT-002 - Command surface
- purpose: the single set of operations through which anything changes - the interface, the assistant
  and @Headless agent mode all go through it. Exchanged between the product and any external caller
  driving it
- schema: schema/CT-002.json
- version: 1.0.0
- strictness: unknown fields are **rejected**
- compatibility: a command name and its parameters, once shipped, keep their meaning; a changed
  meaning is a new command name
- migration: not applicable - this contract is a live protocol, not stored data. A caller pinned to an
  older version keeps working because commands are added, never repurposed
- decidedness: Fixed
- basis: E-001 (T1)

## Why reject rather than preserve, when CT-001 preserves

The two contracts differ deliberately, and the reason is the failure each one risks.

A **document** outlives the program that wrote it, and dropping a field the reader does not recognise
destroys the user's work. A **command** is executed immediately: an unrecognised parameter means the
caller believes something is happening that is not. Preserving it would let an external agent think it
disabled a safety check when it merely misspelled it.

## Who calls it

Four callers, one surface: the **interface**, the **assistant**, a **script** (XC-102) and a
**@Pipeline** (CT-009). None of them has a private path. That is what makes an instruction, a click and
a headless run produce the same result and the same log, and it is the reason undo, the run record and
the dry run each need to be built only once.

## Properties every command carries

- an operation name, its parameters, and the identifiers of what it acts on
- whether it changes state - a read never needs confirmation and never enters the undo history
- an effect summary the product can show before applying it, used by assistant/AC-005
- a result that names what changed, so a caller can verify rather than assume
- **the identity that issued it**, once the headless form exists: authentication is required, an unknown
  caller is refused, and an autonomous agent is a caller like any other (XC-128)
- **a dry-run mode**: the same command, resolved and reported, changing nothing (CT-003)

## Invariants this contract carries

- **The set is the same everywhere.** Any operation the interface can perform is in this contract, and
  nothing is in this contract that the interface cannot perform (INV-006). **This is now checked rather
  than asserted**: `validate/check_commands.py` compares the catalogue against its schema and reports
  what it could not examine (XC-127). It was prose in three files until a rename left the schema behind
  and nothing noticed
- **A script's commands undo like anyone else's.** One script is one undo step, deliberately unlike the
  reference application, where operators called from Python skip the undo stack by default (XC-102)
- **One instruction, one undo.** A group of commands submitted together undoes together
  (assistant/AC-002)
- **Refusal beats assumption.** An unknown command, a malformed parameter, or an operation needing
  confirmation without authorisation is refused with a named reason, changing nothing
  (assistant/AC-012)
