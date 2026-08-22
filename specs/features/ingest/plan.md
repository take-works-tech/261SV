---
status: draft
updated: 2026-08-19
---

# Plan: result ingest

HOW. Kept separate from `spec.md` so the requirements survive a change of technology.

- approach: the engine wraps the toolkit's readers behind one entry point that returns a @Dataset in
  the canonical frame with its association and support level attached. Nothing above that entry point
  knows which reader ran. Format detection is by content where the reader offers it and by extension
  otherwise, and a detection that is uncertain asks rather than guesses
- modules touched: MOD-002 dataset-io, MOD-001 domain-core. Blast radius: everything downstream reads
  @Dataset, so a change to its shape reaches MOD-003, MOD-004, MOD-005 and MOD-006
- contracts touched: CT-001 (the source references a @Workspace records)
- technology: VTK readers as shipped (XC-049); no reader is written here in the first release
- risks: the readers are the largest untrusted-input surface in the product (XC-047), and the ones we
  promise least about are the ones customers are most likely to bring

## Order of work

The first milestone is the walking skeleton, and it belongs to this feature: **a file dropped, a
surface on screen, a number reported that provably came from the full dataset.** Until that exists,
every other estimate in this specification is theory.

1. the reader entry point and the canonical-frame conversion (REQ-013)
2. field listing with association and undeclared units (REQ-011)
3. drop-to-load in the shell (REQ-010)
4. support levels surfaced at load (REQ-015)
5. time series and partitioned sets (REQ-012)
6. the reduction path and its marking (REQ-014)

## What must be proven before this feature is called done

- a reported maximum equals the value computed on the full dataset, not the reduced display (INV-001)
- a field that arrived as cell data is still cell data after every step (INV-003)
- points that fall outside a source are missing, not zero (INV-011)
- a partitioned dataset is not double-counted at its boundaries (INV-010)

Each of those is a defect the toolkit produces by default. They are listed here because they are the
work, not the checklist afterwards.
