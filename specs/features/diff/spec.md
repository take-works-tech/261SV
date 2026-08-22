---
status: draft
updated: 2026-08-20
---

# Feature: diff between cases

## Users and purpose

- intended user: an engineer who changed one thing and needs to know what it did
- job to be done: see the difference between two @Case as a field, not as two pictures side by side
- success condition: the difference is a quantity with a unit, a provenance and - where the two cases do
  not share a mesh - an honest statement of how much of it is interpolation

## Out of scope

- differencing cases of different physics or incompatible quantities: refused, with both named
- a "percentage difference" where the denominator can be zero, unless the user states the reference

## Files and interfaces involved

- GL-011 @Diff, and the engine operation that computes it (CT-003)
- MOD-004 analysis, MOD-002 dataset-io, MOD-003 visualization
- the view and graph areas of [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - On a shared mesh, a diff is a direct difference
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-054 (T1)
- acceptance:
  - AC-001: When two @Case share a mesh, the system shall compute the difference point by point, or
    cell by cell, keeping the association of the source fields (INV-003)
  - AC-002: When the two cases carry @Source identifier, the system shall match locations by identifier
    rather than by array position (INV-023)
  - AC-003: If the fields have different declared units, then the system shall refuse the diff and shall
    name both units (INV-002)
  - AC-004: If a location is missing in either case, then the difference at that location shall be
    missing, never zero (INV-011)

### REQ-002 - Across different meshes, a diff discloses what it cost
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-056 (T1)
- acceptance:
  - AC-005: When two @Case do not share a mesh, the system shall require the user to name the dataset
    being resampled onto, and shall not choose a direction silently
  - AC-006: When a cross-mesh diff is produced, the system shall report the resampling direction, the
    number of points that fell outside the target, and the round-trip error, and shall carry all three
    with the result wherever it appears (GL-011)
  - AC-007: If a point falls outside the source mesh, then the system shall report it as missing and
    shall not extrapolate a value
  - AC-008: Where a cross-mesh diff appears in a @Report, the report shall state that physical
    difference and interpolation error are both present in the number

### REQ-003 - A diff is a quantity like any other
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-009: When a diff is computed, the system shall make it available as a @Field with a unit and a
    @Provenance naming both cases and the method used
  - AC-010: Where a relative difference is requested, the system shall require the reference case to be
    named and shall report locations where the reference is zero as undefined rather than infinite

## End-to-end verification

Difference the same field between two cases on one mesh and confirm the result matches a hand-computed
value at a known location addressed by its source identifier. Then difference two cases whose meshes
differ, confirm the direction had to be chosen, and confirm the outside-point count and round-trip error
travel into a report that states both contributions are present in the number.
