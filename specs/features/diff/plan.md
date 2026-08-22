---
status: draft
updated: 2026-08-20
---

# Plan: diff

- approach: a diff is a computed @Field, not a display mode. Computing it in the analysis module means
  it inherits provenance, units and missing-value handling for free, and can be plotted, reported and
  probed like anything else
- modules touched: MOD-004 analysis, MOD-002 dataset-io, MOD-003 visualization
- contracts touched: CT-003 (the operation), CT-004 and CT-005 (a diff is a field a view or graph names)
- technology: the resampling for cross-mesh diffs is the toolkit's, used explicitly rather than
  implicitly - the direction is a parameter with no default, because a default here silently decides
  which mesh's discretisation the answer inherits
- risks: the cross-mesh case is the one that produces a plausible wrong number. Physical difference and
  interpolation error arrive added together, and only the disclosure separates them

## Order of work

1. same-mesh difference with identifier matching and missing propagation (REQ-001)
2. the diff as an ordinary field with provenance (REQ-003)
3. cross-mesh resampling with direction, outside-point count and round-trip error (REQ-002)
4. the report statement that both contributions are present (AC-008)

## What must be proven before this feature is called done

- a hand-computed difference at a location addressed by its source identifier matches
- a location missing in one case is missing in the diff, not zero
- the outside-point count and round-trip error reach a report unchanged
