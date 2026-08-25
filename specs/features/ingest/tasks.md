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
- done: recorded 2026-08-24 for work already in place. `engine/reader.read` and `read_case` return a @Dataset, and a @Case with its parts, with geometry, fields and their association, and the reader that ran on `Dataset.source`.
### TASK-002 - Canonical frame conversion on load
- satisfies: AC-028
- depends_on: TASK-001
- done_when: geometry arrives in metres with Z up, the source frame and scale applied are recorded, and
  a unit test asserts the transform to 1e-12 relative
- done: recorded 2026-08-24 for work already in place. `domain_core/frame.py` resolves the frame and `reader.read` applies the scale once, at one point, recording it in `SourceFrame`.
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
- done: recorded 2026-08-24 for work already in place. `Field.association` with `as_point_data`/`as_cell_data` refusing the other, covered by tests/test_reader.py.
### TASK-005 - Undeclared units everywhere
- satisfies: AC-024
- depends_on: TASK-004
- done_when: a value requested in a unit while none is declared refuses the conversion and names the
  reason; no code path infers a unit
- done: recorded 2026-08-24 for work already in place. `domain_core/units.py` raises `UndeclaredUnitError` rather than converting, covered by tests/test_units.py.
### TASK-006 - Undeclared marker survives display and export
- satisfies: AC-025
- depends_on: TASK-005
- done_when: a field with no declared unit exports as a bare number carrying the marker
- blocked: no export path exists yet, so the half of this task that is about export cannot be written or tested. The marker itself is carried (`Caveat.UNDECLARED_UNIT` on every `ReportedValue` with no unit); what is missing is a writer to carry it through.
### TASK-007 - Drop to load in the shell
- satisfies: AC-020
- depends_on: TASK-001
- done_when: dropping supported files on the window creates or updates a @Case and lists its fields
- blocked: there is no shell. The engine half is `reader.read_case`; the drop target is UI work and the mockup is a design state, never evidence of implemented behaviour.
### TASK-008 - Unsupported and unreadable files
- satisfies: AC-021
- depends_on: TASK-007
- done_when: an unsupported format names itself and creates no partial @Case; a truncated file reports
  the failure and leaves the @Workspace unchanged (AC-022)
- partly done: recorded 2026-08-24. The engine half is in place - `UnsupportedFormatError` names the format and `UnreadableFileError` the failure, both covered by tests. "Creates no partial @Case" needs the shell that TASK-007 waits for.
### TASK-009 - Support level table and its display
- satisfies: AC-032
- depends_on: TASK-007
- done_when: the level of the detected format - Verified, Offered or Absent - is shown with the loaded
  @Case, generated from the table in XC-049 rather than typed twice
- partly done: recorded 2026-08-24. `reader.support_level` returns the level and the gaps; showing it alongside the loaded @Case is UI work.
### TASK-010 - Named gaps for Offered formats
- satisfies: AC-033
- depends_on: TASK-009
- done_when: an Offered format shows the specific documented gaps of its reader, not a generic warning
- partly done: recorded 2026-08-24. Each `ReaderChoice` carries its own gap text - the partitioned reader's duplicated boundary points, STL's absent fields, Exodus's arrays that must be enabled by name - and `support_level` returns them. Displaying them is UI work.
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
- done: 2026-08-24, `domain_core/reduction.py` (the plan) and `engine/visualization/display.py` (the
  work, and MOD-003's first code). A surface above LIM-002 is reduced by `vtkDecimatePro` and the plan
  it carries states **how much**: "48 三角形のうち 12（25.0%）を描画" rather than "reduced", because a
  view showing a tenth of its triangles and one showing 99% are both reduced and only one is worth
  looking at twice.
  Two things this task turned up. The separation it needed did not exist: the reader had been storing
  the extracted surface **as** the dataset's geometry while reading fields from the original grid, so on
  a volume mesh every index correspondence was wrong (E-132, XC-233, and INV-001's correction). And the
  decimator had to be chosen on correctness rather than quality - `vtkQuadricDecimation` looks better and
  **drops `vtkOriginalPointIds` entirely**, leaving a reduced surface that cannot answer a pick at all,
  while `vtkDecimatePro` carries it through and moves no surviving point (E-134, XC-235).
  Display geometry also moved out of the reader: it is produced when a view asks for it, so reading a
  file no longer pays for a picture nobody wanted.

### TASK-016 - Numbers computed on the full dataset
- satisfies: AC-031
- depends_on: TASK-015
- done_when: a reported maximum on a reduced view equals the value from the full data, asserted by test
  (INV-001)
- done: 2026-08-24, structurally rather than by care at each call site: aggregates read `Dataset.fields`
  and `engine.visualization.display` never touches them, so there is no path along which a reduced view
  could reach a reported number. The test is the one the invariant asks for - the largest value in the
  fixture block is at its centre, and the centre is not on the surface at all, reduced or otherwise, so
  a maximum of 260 is a maximum the picture never had access to.

### TASK-017 - Reduction computed once and cached
- satisfies: AC-030
- depends_on: TASK-015
- done_when: repeated display of the same @Case does not recompute the reduction, which was measured at
  22 seconds for a million-point surface
- done: 2026-08-24, cached on the @Dataset and keyed by triangle budget, so two views of one @Case with
  different budgets keep both and neither evicts the other. On the @Dataset rather than in a module
  because the geometry is derived entirely from it and should die with it; a cache keyed by object
  identity elsewhere outlives what it describes.
- note: the 22 seconds is right but is not this scale. Re-measured on 2026-08-24: the same filter and
  the same 90% reduction cost **2.63 s at 977,200 triangles** and the export spike's 22.34 s was a
  2,251,442-cell mesh (E-134). Both are hundreds of frames, so the conclusion stands unchanged - the
  figure is recorded at the size it was taken at rather than left attached to the wrong one.

### TASK-018 - Preserve source identifiers
- satisfies: AC-035
- depends_on: TASK-001
- done_when: global and pedigree identifiers survive reading and reach extreme-value reporting
- done: 2026-08-24, `domain_core/identifiers.py` and `Dataset.identifiers`, with `maximum()` reporting
  the location. Verified end to end: a `.vtu` carrying `GlobalNodeId` reports its maximum at
  `GlobalNodeId 1003`, and in an assembly at `asm / gasket：node 3` - the part first, because every part
  may number its own nodes from one.
  The reader was **offering identifiers as variables**. `_fields` took every array on the dataset, and
  the identifier arrays are in that list (E-135), so `GlobalNodeId` arrived as a @Field with no declared
  unit - a physical quantity as far as anything downstream could tell, cast to float64 and plottable
  against itself. Now the attribute role the file declared decides, and identifiers are held apart
  (XC-236).

### TASK-019 - Absent identifiers stated
- satisfies: AC-036
- depends_on: TASK-018
- done_when: a file without identifiers reports their absence and no index is shown as one
- done: 2026-08-24. `NO_IDENTIFIER` is one sentence stated once, so two reports of the same absence
  agree, and it is phrased as a fact about the file rather than a failure of the reader - only one of
  the two can be fixed, by asking the solver to write identifiers. The test asserts that the index of
  the maximum does not appear anywhere in what is said, which is the failure mode: a plausible number
  in a sentence about location is one somebody takes to the solver and fails to find.

### TASK-020 - Measurement data import
- satisfies: AC-037
- depends_on: TASK-001
- done_when: measured values attach to a case and are usable as a source of numbers
- done: 2026-08-24, `domain_core/measurement.py` and `engine/measurements.py`. A measured value
  reports with `Provenance.MEASURED` - not DECLARED and not REFERENCE, because @Reference material may
  never supply a number and @Measurement data may, and the two have to be distinguishable in the value
  itself (XC-125).
  Two things are required rather than optional. A measured value **records what produced it**: one with
  no stated origin is a number somebody must take on trust with nobody left to ask. And a measurement
  file's columns are **declared, not recognised** - a column nobody reads is refused rather than
  ignored, because ignoring it loses data the user believes was imported. Every refusal names the row.
### TASK-021 - Uncertainty travels with a measured value
- satisfies: AC-038
- depends_on: TASK-020
- done_when: a comparison can state both the computed and the measured uncertainty
- done: 2026-08-24. `Uncertainty` says which kind it is, and **an expanded one carries its coverage
  factor or is refused**: the metrology guidance requires either U with its k or the combined standard
  u_c, and "±0.4" at k=1 and k=2 describe intervals that differ by a factor of two (E-070). A standard
  uncertainty carrying a k is refused too - it would be read as an expanded one by anyone who trusts
  the label.
  `comparison.compare` states both sides and **delivers no verdict** unless the user gave a threshold,
  which is then named (XC-107). A computed value carries no uncertainty in this build, so the
  comparison says the discretisation error is unquantified rather than omitting the subject - a bare
  computed figure beside a measured one with error bars reads as the exact one.
  `combined_uncertainty` combines in quadrature after converting each to standard form, and returns
  None where there is nothing to combine rather than treating an absent contribution as zero.
### TASK-022 - Undeclared measured units
- satisfies: AC-039
- depends_on: TASK-020
- done_when: no unit is inferred from the field being compared against
- done: 2026-08-24. A measured value with no declared unit stays undeclared beside a computed field
  in megapascals, and the **difference is refused** rather than computed: 231 from 235 is 4 whether
  both are megapascals or one is a pascal, and the answer looks the same either way. Differing declared
  units are refused too, rather than converted - a conversion happens when it is asked for.
  An empty cell in an imported table means **absent**, never zero and never a default.
### TASK-023 - Integration-point values read as written
- satisfies: AC-040
- depends_on: TASK-001
- done_when: values at integration points are not extrapolated by this product
- done: 2026-08-24. XC-123 in code: the extrapolation is not unimplemented, it is **unwritable** - it
  depends on the element formulation and the file does not carry it, so there is no correct version of
  it. `as_point_data` and `as_cell_data` refuse an integration-point field and say that, naming the file
  rather than the product: a user can act on "the file does not carry the element formulation" and
  cannot act on "unsupported".
  The structural half mattered as much. `Association` had two members, so an integration-point field had
  **nowhere truthful to sit** - anything holding one would have called it cell data, and every rule
  about cell data would then have applied to it wrongly. It is now a third association that must say how
  many points per cell, because a mesh of n cells with 8 points each and one of 8n cells with one each
  hold the same number of values.
  Two aggregates are refused with it: a sum and a mean need the **quadrature weights** of the rule the
  solver used, and the file does not carry those either. The extremum is reported - it is exactly the
  peak value the solver evaluated, with no weighting and no interpolation - and so is a count, which is
  a fact about the array rather than about the physics.
  Declared, never inferred: solvers name these arrays `sigma_xx_1` through `_8` by convention, and
  reading a convention as a fact is how eight independent results become one quantity nobody asked to
  combine.
### TASK-024 - Modal results
- satisfies: AC-041
- depends_on: TASK-001
- done_when: modes are indexed by number and each carries its eigenfrequency
- blocked: 2026-08-24, and the blocker is measured rather than assumed. The half about **indexing**
  is done - a sequence is read and carried with its values. The half about **eigenfrequency** cannot be:
  no reader in this build reports that a sequence is modal, and the one that will answer if asked
  guesses it from two time values being identical (E-138). Until a file's own statement is reachable -
  CGNS's `SimulationType_t` is the nearest - a mode number and its frequency are indistinguishable from
  a step number and its time, and this product says undeclared rather than choosing (XC-240).
  Re-measured 2026-08-25, after the CGNS reader landed. `vtkCGNSReader` exposes selections for bases,
  families and flow solutions and **nothing for `SimulationType_t`** - its property list has no
  `Simulation`, `Mode` or `Frequency` entry at all. The nearest declaration is still unreachable through
  the reader this product uses, so the blocker is unchanged rather than merely unrevisited.
### TASK-025 - Harmonic results stay complex
- satisfies: AC-042
- depends_on: TASK-024
- done_when: real and imaginary parts are kept together and indexed by frequency
- blocked: 2026-08-24, on the same measurement as TASK-024. Keeping the real and imaginary parts
  together is straightforward; knowing that a pair of arrays **is** a complex result, and that the
  sequence indexing it is frequency, requires a declaration no reader surfaces.
### TASK-026 - Unknown result kinds
- satisfies: AC-043
- depends_on: TASK-024
- done_when: an ambiguous index reports unknown rather than being called time
- done: 2026-08-24. `engine/result_axis.py` reads the values and reports the kind as `UNDECLARED`,
  and a test asserts that `axis_of` mentions no axis kind at all - the claim being about the code rather
  than about a loaded module, so it holds on a machine with no engine environment.
  Two things had to be settled that the task did not anticipate. `ResultAxis` **refused** positions
  without a kind, which measurement showed to be the ordinary case rather than an incoherent one
  (E-138); the refusal is now a correction recorded in the test that used to assert it. And a lone
  `[0.0]` is the CGNS reader's placeholder rather than a declaration, so it is discarded - a steady case
  reports no axis instead of a position nobody wrote.
### TASK-027 - Mixed axes are stated
- satisfies: AC-044
- depends_on: TASK-025
- done_when: combining results of different axes carries a statement
- done: 2026-08-24, `domain_core.case_contents.differing_axes`. The statement is produced in
  domain-core rather than at each display site, because a site that forgets it produces a chart that
  looks ordinary.
  **An undeclared axis produces a statement whatever it sits beside**, including another undeclared one
  carrying the same values: two files that both say "0, 0.5" and neither of which says what that is may
  be one transient run and one modal one, and silence would be read as a statement that they agree. A
  steady result has no positions to disagree about and produces none.
### TASK-028 - A composite is read as the parts of one Case
- satisfies: AC-026
- depends_on: TASK-012
- done_when: a `vtkMultiBlockDataSet` and a `vtkPartitionedDataSetCollection` each load as **one** @Case
  whose parts are counted and named from the block hierarchy, and whose partition count is separate from
  its part count (XC-234, CT-012)
- why: this is the common case rather than an extension. 19 of the 40 CAE readers in the pinned build
  return a `vtkMultiBlockDataSet` and 6 return a `vtkPartitionedDataSetCollection`, against 4 that return
  an unstructured grid directly (E-133), so `reader.read`'s `vtkDataSet` signature meets none of the
  formats this product exists for
- done: 2026-08-24, `domain_core/parts.py` (`Part`, `LoadedCase`) and `reader.read_case`, which walks a
  composite into named parts keeping the block hierarchy as the path - two assemblies may each hold a
  `gasket`, and a name alone would name both.
  **An empty block is a named part that is missing.** A block with a name and no data is exactly what
  AC-027 describes, and it comes back as an absence rather than being skipped, so an assembly cannot be
  incomplete without saying so.
  Only the extremum is offered case-wide, and `total` and `mean` are **not offered at all** rather than
  offered with a warning: adding a flange's values to a gasket's is arithmetically fine and means
  nothing (XC-234). Partitions of one dataset recombine into one part carrying its partition count, so
  INV-010 applies to it without anyone restating anything.
- correction: TASK-012 counted a `.pvtu`'s pieces as **parts**, and they are partitions - the other
  multiplicity entirely. Worse, `Partitioning.parts` was the same word for the same mistake one layer
  down, and `Dataset.partitioning` was built from `contents.parts`, so once composites arrived an
  assembly of three components would have had its aggregates refused as though its points were
  duplicates of each other. Renamed to `partitions` and re-derived; `CaseContents` now counts both and
  says which kind each absence is (XC-234)

### TASK-029 - Each conversion CT-012 names states its cost before it runs
- satisfies: AC-032
- depends_on: TASK-028
- done_when: reading a structured, rectilinear, image, explicit-structured, hyper-tree or cell grid
  performs exactly the conversion CT-012 names for it, records what that conversion cost on the
  @Dataset, and states a cost that exceeds LIM-002 **before** converting rather than after
- why: three of the costs are not recoverable afterwards. An image grid's spacing is the one number in a
  voxel result that carries a length; a hyper-tree grid's expansion is the memory the format exists to
  avoid; a cell grid's high-order basis does not survive at all, so INV-009 forbids reporting a number
  from the converted form
- done: 2026-08-24, `engine/conversion.py` runs the chain CT-012 names for each of the nine convertible
  types - not a chain that happens to work - and `domain_core/conversion.py` holds what it cost on the
  @Dataset that came out.
  **The cost is read from the source, so it is stated before it is paid.** A structured, rectilinear or
  image grid knows its cell count from its dimensions and a hyper-tree grid reports 0 cells until it is
  expanded but knows its leaf count, so `ConversionTooLarge` is raised before the filter runs and the
  choice is still the user's. Verified on an 11x11x11 image grid: 1,000 cells refused against a budget
  of 100, and produced when the cost is accepted.
  Its spacing and origin are captured at conversion time because after the points are explicit nothing
  remembers them.

### TASK-030 - A refused type names itself
- satisfies: AC-021
- depends_on: TASK-028
- done_when: every data object type CT-012 marks `refuse` produces a failure naming that type and the
  contract's stated reason, asserted by a test that walks the contract rather than a list written beside
  it
- why: a generic read failure tells a user their file is broken. Naming the type tells them what they
  opened, and the difference decides whether they go looking for a corrupt file that does not exist
- done: 2026-08-24. `src/domain_core/object_compatibility.py` is **generated from CT-012** by
  `check_object_compatibility.py --write`, and the gate regenerates and compares - so the disposition of
  a type and the reason it is refused exist once, and a checked-in generated file cannot drift.
  The test walks the contract rather than a list beside it, and it found something on its first run: 20
  of the refusals read `as vtkGraph` or `as vtkImageData`. Good prose in a document a person reads, and
  **nothing at all in an error message**. The generator now resolves a cross-reference to the words it
  points at, so the contract keeps the reference and the message carries the reason.

### TASK-031 - Exodus, with every result it holds
- satisfies: AC-032
- depends_on: TASK-028
- done_when: an Exodus file loads as one @Case of named parts carrying **every** result the file holds,
  and a result the file offered that did not arrive stops the read
- done: 2026-08-24, `engine/exodus.py`. The first Verified-tier format beyond the VTK XML family, and
  the one that exercises what TASK-018 and TASK-028 built: it arrives as a `vtkMultiBlockDataSet` of
  named element blocks and it carries global and pedigree identifiers.
  The reader's default is to read **no results at all** - 27 array categories, all off, no error
  (E-136). This product switches every one on and then checks that every result the file offered
  arrived, by name, refusing the read if one did not (XC-237). The check rather than the switching is
  the guarantee.
  `ObjectId`, the element-block number Exodus writes onto every cell, carries no identifier role, so
  nothing in the toolkit would have kept it out of the list a user picks a @Variable from.

### TASK-032 - CGNS, with its unread unit declaration stated
- satisfies: AC-034
- depends_on: TASK-031
- done_when: a CGNS file loads as one @Case whose fields are undeclared, and the reader states which
  declaration in the file it did not read
- done: 2026-08-24, `engine/cgns.py`. CGNS is the one format this build reads that **declares** its
  units, and `vtkCGNSReader` exposes no accessor whose name contains `unit`, `dimension` or `dataclass` -
  zero matches (E-137). So the declaration is in the file, this product can say that it is there, and
  every field stays undeclared. `ReaderChoice` refused to register the format without saying so, which
  is TASK-003's rule firing on the format it was written for.
  Its results are read only because every array is enabled - the same defect as Exodus through a
  different API, which is why the check that catches it moved into `engine/completeness.py` (XC-239).
  The fixture is **generated**, correcting XC-085: the toolkit has no CGNS writer, but CGNS/HDF5 is an
  HDF5 node layout and h5py writes it. One trap found doing it - `C1` character data must be native
  chars, and with h5py's string dtype the reader opens the file and misreads it, taking a 4-point
  unstructured zone for an 8-point structured one.

