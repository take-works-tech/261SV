---
status: draft
updated: 2026-08-20
---

# Tasks: result ingest

Each task is at most half a day and links back to the criterion it satisfies. A task with no criterion
is either missing a requirement or is not work this specification asked for.

### TASK-001 - Reader entry point returning a Dataset
- satisfies: AC-020
- depends_on: none
- done_when: one call takes a path and returns a @Dataset with geometry, fields and their association,
  with the reader that ran recorded on it

### TASK-002 - Canonical frame conversion on load
- satisfies: AC-028
- depends_on: TASK-001
- done_when: geometry arrives in metres with Z up, the source frame and scale applied are recorded, and
  a unit test asserts the transform to 1e-12 relative

### TASK-003 - Refuse frames the reader does not support
- satisfies: AC-029
- depends_on: TASK-002
- done_when: an unsupported frame or scale refuses the import and names what it did not support
- done: 2026-08-24, `domain_core/frame.py`. The rule lives in the domain rather than the reader,
  because it is about what a coordinate means and because it is then verifiable with no VTK installed.
  **What the formats actually declare was measured first** (E-130): CGNS declares a length unit, with
  the enumeration this reader converts; the VTK XML formats and STL declare nothing, so `_declared_frame`
  returns an empty declaration for every format this build reads today and the criterion's refusal path
  is exercised by its rule rather than end to end. Adding a format that declares is a change in one
  place

### TASK-004 - Field listing with association preserved
- satisfies: AC-023
- depends_on: TASK-001
- done_when: every field is listed with point or cell association, and a test asserts a cell field is
  still cell-associated after load (INV-003)

### TASK-005 - Undeclared units everywhere
- satisfies: AC-024
- depends_on: TASK-004
- done_when: a value requested in a unit while none is declared refuses the conversion and names the
  reason; no code path infers a unit

### TASK-006 - Undeclared marker survives display and export
- satisfies: AC-025
- depends_on: TASK-005
- done_when: a field with no declared unit exports as a bare number carrying the marker

### TASK-007 - Drop to load in the shell
- satisfies: AC-020
- depends_on: TASK-001
- done_when: dropping supported files on the window creates or updates a @Case and lists its fields

### TASK-008 - Unsupported and unreadable files
- satisfies: AC-021
- depends_on: TASK-007
- done_when: an unsupported format names itself and creates no partial @Case; a truncated file reports
  the failure and leaves the @Workspace unchanged (AC-022)

### TASK-009 - Support level table and its display
- satisfies: AC-032
- depends_on: TASK-007
- done_when: the level of the detected format - Verified, Offered or Absent - is shown with the loaded
  @Case, generated from the table in XC-049 rather than typed twice

### TASK-010 - Named gaps for Offered formats
- satisfies: AC-033
- depends_on: TASK-009
- done_when: an Offered format shows the specific documented gaps of its reader, not a generic warning

### TASK-011 - Units present in the file but unread
- satisfies: AC-034
- depends_on: TASK-005, TASK-009
- done_when: a CGNS file carrying dimensional units still reports the unit as undeclared, and the
  interface says the file has unit information the reader does not read

### TASK-012 - Time series and partitioned sets as one Case
- satisfies: AC-026
- depends_on: TASK-001
- done_when: a series or partitioned set presents as one @Case with a time axis and states how many
  steps and parts it found

### TASK-013 - Partial sets marked, and the mark propagated
- satisfies: AC-027
- depends_on: TASK-012
- done_when: a missing part marks the @Dataset partial and every derived number carries the mark

### TASK-014 - Boundary points counted once
- satisfies: AC-027
- depends_on: TASK-012
- done_when: an integral over a partitioned dataset equals the same dataset in one piece (INV-010)

### TASK-015 - Reduction for display, marked
- satisfies: AC-030
- depends_on: TASK-001
- done_when: a @Dataset above LIM-002 displays reduced and the view says so

### TASK-016 - Numbers computed on the full dataset
- satisfies: AC-031
- depends_on: TASK-015
- done_when: a reported maximum on a reduced view equals the value from the full data, asserted by test
  (INV-001)

### TASK-017 - Reduction computed once and cached
- satisfies: AC-030
- depends_on: TASK-015
- done_when: repeated display of the same @Case does not recompute the reduction, which was measured at
  22 seconds for a million-point surface

### TASK-018 - Preserve source identifiers
- satisfies: AC-035
- depends_on: TASK-001
- done_when: global and pedigree identifiers survive reading and reach extreme-value reporting

### TASK-019 - Absent identifiers stated
- satisfies: AC-036
- depends_on: TASK-018
- done_when: a file without identifiers reports their absence and no index is shown as one

### TASK-020 - Measurement data import
- satisfies: AC-037
- depends_on: TASK-001
- done_when: measured values attach to a case and are usable as a source of numbers

### TASK-021 - Uncertainty travels with a measured value
- satisfies: AC-038
- depends_on: TASK-020
- done_when: a comparison can state both the computed and the measured uncertainty

### TASK-022 - Undeclared measured units
- satisfies: AC-039
- depends_on: TASK-020
- done_when: no unit is inferred from the field being compared against

### TASK-023 - Integration-point values read as written
- satisfies: AC-040
- depends_on: TASK-001
- done_when: values at integration points are not extrapolated by this product

### TASK-024 - Modal results
- satisfies: AC-041
- depends_on: TASK-001
- done_when: modes are indexed by number and each carries its eigenfrequency

### TASK-025 - Harmonic results stay complex
- satisfies: AC-042
- depends_on: TASK-024
- done_when: real and imaginary parts are kept together and indexed by frequency

### TASK-026 - Unknown result kinds
- satisfies: AC-043
- depends_on: TASK-024
- done_when: an ambiguous index reports unknown rather than being called time

### TASK-027 - Mixed axes are stated
- satisfies: AC-044
- depends_on: TASK-025
- done_when: combining results of different axes carries a statement
