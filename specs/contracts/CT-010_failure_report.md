---
status: draft
updated: 2026-08-22
---

# Contract: how a failure is reported

### CT-010 - Failure report
- purpose: the one shape every refusal, failure and partial result takes, wherever it surfaces - the
  interface, a command result, a pipeline run record, a headless exit, a report
- schema: schema/CT-010.json
- version: 1.1.0
- strictness: unknown fields are **preserved** - a failure written by a newer build must still be
  readable by an older one, because a failure report is exactly what gets sent to somebody for help
- compatibility: a reason code is never reused for a different meaning, and never removed while any
  stored run record might contain it
- migration: none; a failure report is produced, read and discarded, or stored inside a run record
  (CT-009) which migrates with it
- decidedness: Fixed
- basis: E-001 (T1)

## Why this exists

More than a hundred acceptance criteria in this specification end with some form of *and shall name
what is missing*. Written per feature, that becomes a hundred slightly different sentences, and the
first one an agent writes without the naming becomes the precedent for the next. **One shape, checked
once**, is what makes the promise real rather than aspirational.

## What every failure report carries

| Field | Meaning |
|---|---|
| `reason` | a stable code from the enumeration below - the thing a person can search for and a script can branch on |
| `summary` | one sentence, in the user's language, saying what did not happen |
| `subject` | what it happened to: the @Case, @Field, workspace @View/@Graph/@Report, @Template, @Pipeline unit or file, by identifier **and** by the name a person would recognise |
| `missing` | for a refusal, exactly what was absent - the unit that was not declared, the frame that could not be resolved, the field the template wanted |
| `changed` | whether anything was written or altered. **`false` is the default and the common case** |
| `remedy` | what the user can do, when there is something - declare a unit, choose a frame, re-import a file |
| `detail` | technical text for a support bundle; never required to understand the summary |

`changed` is not decoration. A user reading a failure needs to know whether their workspace is now in
a different state, and the answer in this product is almost always no (XC-005) - but "almost always"
is not something a reader should have to assume.

## Reason codes

Grouped by what the user has to do about them, because that is the only grouping that helps at the
moment of reading one.

| Group | Codes | The user's next move |
|---|---|---|
| something was not declared | `unitUndeclared`, `frameUnresolved`, `referenceUnbound` | declare it, then retry |
| something was not found | `fileMissing`, `fileChanged`, `workspaceItemMissing`, `templateMissing`, `definitionRevisionMissing`, `caseUnresolved` | point at it again, select an available revision, or remove the reference |
| a material dependency is unresolved | `materialInputMissing`, `materialResourceMissing`, `materialHashMismatch`, `unitDimensionMismatch` | repair the named Material Binding input or restore the exact resource revision; the target stays diagnostic magenta |
| something is not supported | `formatUnsupported`, `operationUnknown`, `arityMismatch`, `materialFeatureUnsupported` | a different input, material graph, renderer or operation |
| something was refused on purpose | `permissionDenied`, `authorisationDeclined`, `hostNotAllowed`, `nameInUse`, `limitExceeded` | change the permission, the name, or the size |
| something failed while running | `readFailed`, `computeFailed`, `renderFailed`, `materialCompileFailed`, `exportFailed` | read `detail`, or send a support bundle |
| stored bindings are ambiguous | `materialBindingOverlap` | repair the named part or element-set targets so each surface resolves one root material |
| something was incomplete | `partialData`, `unresolvedReferences` | the result exists and states its coverage (XC-002, XC-090) |

**A refusal is not an error.** `permissionDenied` and `nameInUse` are the product working correctly,
and they are reported in the same shape so that a caller - especially an agent - can tell "you may not"
from "it broke" without parsing prose.

## What a failure report never contains

- a substituted value, or a hint that the operation partly succeeded when it did not (XC-001)
- an internal path, stack or identifier in `summary`; those belong in `detail`
- a field value from the customer's data in anything written to a log (XC-126)
- an instruction to retry an operation that will fail identically

## Where it surfaces

The same object, rendered differently: **inline** on the element it concerns, in the **notification
history**, as the failed entry of a **pipeline run record** (CT-009), as the body of a **command
result** (CT-002), and as the machine-readable output of a **headless run**, whose exit status is
non-zero when any report has `changed: false` and a reason outside the incomplete group.

Version 1.1 adds Material Asset and Material Binding subjects and the stable dependency, hash,
capability, compilation and overlap codes required by XC-175 and XC-176. A failed Material Binding
normally has `changed: true` only when the user explicitly accepted creating that repairable binding;
subsequent failed resolution changes no source data and reports `changed: false`.

This is why the shape is a contract and not a convention: five surfaces, one object, and a script that
learns the shape once works against all five.
