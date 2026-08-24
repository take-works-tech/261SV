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
- done: 2026-08-24, `domain_core/frame.py` and `engine/reader.py`. Both halves are rules rather than a
  CGNS path, because **this build has no CGNS reader** and its fixture cannot be written (XC-085). The
  first half holds by construction and is asserted: nothing in the reader ever sets a unit, so a field
  is undeclared whatever the file carried. The second is enforced where a reader is added -
  `FORMATS_CARRYING_UNIT_INFORMATION` records, from measurement (E-130), that CGNS carries `LengthUnits`
  and `DimensionalExponents` and that no other format in this stack carries any, and `ReaderChoice`
  **refuses to be constructed** for such a format unless it either reads that information or states that
  it does not. The statement reaches the interface through `support_level`, beside the other known gaps
  (AC-032), so nothing new has to be asked for it

### TASK-012 - Time series and partitioned sets as one Case
- satisfies: AC-026
- depends_on: TASK-001
- done_when: a series or partitioned set presents as one @Case with a time axis and states how many
  steps and parts it found
- done: 2026-08-24, `domain_core/case_contents.py` and `engine/survey.py`. Surveying is separate from
  reading: it answers what is present from manifests and filenames, before anything is loaded, so an
  interface can state the extent up front.
  **The axis is not always time, and this build cannot read one.** GL-036 already said the first;
  E-130 establishes the second - no format read here declares a time value. A directory of numbered
  files therefore reports `UNDECLARED` with no positions, because a modal run and a transient run are
  the same directory of numbered files and calling the third one `t = 3` states something false about
  the physics. `AxisKind.UNDECLARED` exists for exactly that and is not a fifth kind of physics.
  **The piece manifest is parsed here rather than taken from the toolkit**, because reporting a part
  that is *missing* (AC-027) needs what the file claimed: a reader that returns the pieces it opened
  cannot describe the one it did not. A `<Piece>` with no `Source` counts as missing rather than being
  skipped - the manifest said a piece was there.
  No VTK is imported, so all 12 tests run on a machine with no engine environment

### TASK-013 - Partial sets marked, and the mark propagated
- satisfies: AC-027
- depends_on: TASK-012
- done_when: a missing part marks the @Dataset partial and every derived number carries the mark
- done: 2026-08-24, `domain_core/reported_value.py`. The second half needed a type that did not exist:
  until now a number was a bare `float`, and GL-016 requires @Provenance to travel with a value from
  the moment it exists. `ReportedValue` carries the value, its unit, the digits it honestly holds, where
  it came from and its caveats - and **`derive` unions the caveats of its inputs**, which is what makes
  "every derived number carries the mark" a property of the type rather than a rule each call site
  remembers.
  **`Dataset` already had `partial` and `partial_reason`**, from the initial import, whose docstring
  promised that every derived number could say so and which nothing read. They are kept for an
  incompleteness the survey cannot describe, and `is_partial` answers from either source so no path can
  be incomplete in a way the other does not see.
  Two distinctions the type forces, both found by writing the first ratio: a value with no unit carries
  `UNDECLARED_UNIT` rather than a blank, and **dimensionless is not undeclared** - a safety factor has no
  unit because it has none. And a derived value is no more precise than its inputs (XC-230).
  No VTK, so all 15 tests run without the engine environment

### TASK-014 - Boundary points counted once
- satisfies: AC-027
- depends_on: TASK-012
- done_when: an integral over a partitioned dataset equals the same dataset in one piece (INV-010)
- done: 2026-08-24, `domain_core/partitions.py` (the ghost vocabulary and the mask),
  `Dataset.maximum/total/mean/counted_entries`, `CaseContents.ghost_level`, and the `GhostLevel` read in
  `engine/survey.py`. 18 tests in `tests/test_partitions.py`, none needing VTK.
  Measuring the toolkit corrected INV-010 rather than confirming it (E-131). Two findings changed the
  shape of the task: an **extremum has no duplicates to exclude**, so promising that it excludes them
  described work that is not done; and a `.pvtu` at the writer's default `GhostLevel="0"` **carries no
  ghost array at all**, so in the common case the duplicates cannot be identified and the affected sums
  and means are refused with the reason rather than reported (XC-232). Cells are repeated only above
  ghost level 0, so a cell quantity over a flat partitioning is already exact.
  `Association` moved to its own module: the ghost vocabulary needs it because the same bit means
  `HIDDENPOINT` for a point and `HIGHCONNECTIVITYCELL` for a cell, and a word two modules share is not
  owned by whichever was written first (XC-231).

### TASK-015 - Reduction for display, marked
- satisfies: AC-030
- depends_on: TASK-001
- done_when: a @Dataset above LIM-002 displays reduced and the view says so
- partly done: 2026-08-24, the **separation** exists - `domain_core/mesh.py` holds `Cells` (the
  connectivity the file declared) and `DisplayGeometry` (the triangulated surface with its map back to
  the dataset's own points and cells), and `reader.read` fills both. Found while measuring the toolkit
  for a compatibility specification: the reader had been storing the extracted surface **as** the
  dataset's geometry while reading the fields from the original grid, so on a volume mesh every index
  correspondence was wrong (E-132, XC-233, INV-001's correction). What remains for this task is the
  reduction itself - decimation above LIM-002 and the view saying so; `DisplayGeometry.reduced` is the
  flag it will set, and nothing sets it yet.

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
