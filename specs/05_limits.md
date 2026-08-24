---
status: draft
updated: 2026-08-24
---

# Capacity limits

Maximum counts, sizes, ranges and rates, each with the single place that holds the value. Without this
file every layer invents its own limit and the layers disagree: the interface accepts what the engine
rejects.

**A limit becomes Fixed when it has been measured, and carries the label it has earned until then.**
The earlier version of this line read "limits are Fixed by definition", which was contradicted by six
of the thirteen entries below and, worse, invited the reader to treat an unmeasured guess as settled.
Three labels are in use here and they mean different things to an implementer:

| Label | What it means for this limit | Which |
|---|---|---|
| Fixed | measured, cited, and held in one place the linter compares against the code | LIM-001, LIM-002, LIM-003, LIM-004, LIM-006, LIM-007 |
| Bounded | a working value is in force and enforced, but the number itself is a judgement nobody has yet had to defend against a real case | LIM-008, LIM-009, LIM-012 |
| Open | no number exists, or the one written is a placeholder; the tracking ID says what would settle it | LIM-005, LIM-010, LIM-011, LIM-013 |

A Bounded limit still has a value in the code, because a guard with no number guards nothing. The
label is about the **standing of the number**, not its presence: a Fixed one may not be changed
without changing the specification in the same commit, while a Bounded one is expected to move the
first time a real case argues with it, and moving it is not a defect.

Limits are what makes an acceptance criterion boundary-testable, whichever label they carry.

**Every limit below is a first-release starting point to be measured, not a physical constant.** The
numbers come from what the platform documents and from a published measurement; the product measures
its own and updates them before release. A limit copied from another product's benchmark is a guess
wearing a citation.

**Two machine classes are supported, and the limits differ between them** (XC-086). A business laptop
with integrated graphics and an analysis workstation with a discrete card are not the same product
experience, and pretending otherwise means either refusing work the workstation could do or promising
the laptop something it cannot deliver. The product measures the machine it is on at first start and
applies the matching row; the class it chose is visible in settings, and can be overridden.

### LIM-001 - Dataset held in memory per Case
- value: 8589934592
- unit: bytes
- human_value: 8 GiB, which at the measured 103.8 bytes per point is about 77 million points
- value_by_class: half this on the integrated-graphics class, this value on the workstation class
- source_of_truth: src/engine/limits.py:MAX_DATASET_BYTES
- rationale: a budget for a 32 GB workstation running the shell, the engine and the user's other
  tools. Measured here, a triangulated surface with one field costs 103.8 bytes per point, stable from
  40 thousand to 810 thousand points, so this budget is about 77 million points of that shape - which
  is the number to show a user, since nobody knows their mesh in gigabytes
- on_exceed: the load is refused with the size that failed and the limit that refused it; never
  silently truncated or streamed without saying so
- decidedness: Fixed
- basis: E-053 (T1)

### LIM-002 - Triangles rendered interactively
- value: 10000000
- unit: triangles
- value_by_class: 10 million measured on the integrated-graphics class; the workstation class is
  unmeasured and inherits this number until it is measured, which understates it
- source_of_truth: src/engine/limits.py:MAX_INTERACTIVE_TRIANGLES
- rationale: measured here on integrated graphics with every frame hashed and confirmed distinct:
  11.5 million triangles rendered at 20.6 frames a second **including a per-frame framebuffer readback
  the product does not pay**, and the readback alone accounts for about 26 ms of that. Netting it out
  leaves roughly 43 frames a second at 11.5 million. Ten million is therefore a measured-supported
  ceiling rather than the twenty million previously carried, which was extrapolated from a published
  benchmark on a discrete card (E-020), which remains the only indication of what the workstation class
  can do and is not treated as a measurement of it
- on_exceed: a reduced representation is displayed and marked as reduced - with **how much** was left
  out, because "reduced" alone does not distinguish a view showing a tenth of its triangles from one
  showing 99% - while reported numbers stay computed on the full @Dataset (ingest/AC-030, ingest/AC-031). The
  reduction is `vtkDecimatePro`, which keeps the map back to the dataset's own points, and it is
  computed once per budget and cached: it costs 2.63 s at a million triangles and 22.34 s at 2.25
  million, against a frame of about 23 ms (E-134, XC-235)
- decidedness: Fixed
- basis: E-063 (T1)

### LIM-003 - Single GPU buffer for field data
- value: 134217728
- unit: bytes
- source_of_truth: src/engine/render_limits.py:MAX_FIELD_BUFFER_BYTES
- rationale: the WebGPU default maximum storage-buffer binding size is 128 MiB and the maximum buffer
  size 256 MiB; a field array larger than one binding must be split, and the splitting rule has to
  exist before a field of that size arrives rather than after
- on_exceed: the field is chunked for display; reported values are unaffected because they are not
  computed on the display path (INV-001)
- decidedness: Fixed
- basis: E-018 (T1)

### LIM-004 - Installer size the product accepts
- value: 900
- unit: megabytes
- source_of_truth: planned: build/limits.json:maxInstallerMegabytes
- rationale: measured here, the installed VTK **9.5.2** wheel alone occupies 393.8 MB (E-051), and the
  Electron runtime adds 143.2 MB before anything of ours. ParaView's comparable Windows installer is
  495.5 MB. The ceiling exists so that a dependency added casually shows up as a build failure rather
  than as a download nobody finishes
- note: the 80.4 MB wheel figure recorded in E-021 is a **download size for 9.7.0**, a different
  release from the 9.5.2 that was installed and measured. An earlier version of this rationale set the
  two side by side as though they described one artefact, which understates the installed cost by a
  factor of about five and attributes it to the wrong version. Download and install are different
  quantities of different releases, and this limit is about what lands on disk (OPEN-019)
- on_exceed: the build fails and names what grew
- decidedness: Fixed
- basis: E-021 (T1), E-051 (T1)

### LIM-005 - Cases in one Workspace
- value: 500
- unit: cases
- source_of_truth: src/engine/limits.py:MAX_CASES_PER_WORKSPACE
- rationale: a parameter sweep of a few hundred runs is the shape this product is for; beyond that the
  case tree stops being navigable and the answer is filtering, not a bigger tree
- on_exceed: the import is refused with the count and the limit; the user is offered a filtered import
- decidedness: Open
- open: OPEN-008

### LIM-006 - Report file size
- value: 20
- unit: megabytes
- source_of_truth: planned: src/engine/report_limits.py:MAX_REPORT_BYTES
- rationale: measured here, one million-point surface costs 16.1 MB as compressed geometry and 34.4 MB
  through the free export path. A deliverable an engineer emails has to stay under what a mail system
  accepts, so the report path reduces geometry until it fits and says by how much - the numbers stay
  computed on the full data (INV-001)
- on_exceed: the report is produced with a further reduced representation, marked as reduced, and the
  reduction ratio is stated in the document
- decidedness: Fixed
- basis: E-051 (T1)

### LIM-007 - Pipeline nesting depth
- value: 3
- unit: levels
- source_of_truth: src/engine/limits.py:MAX_PIPELINE_DEPTH
- rationale: a pipeline that nests deeper than this cannot be read at a glance, and a pipeline nobody
  can predict is one nobody should authorise to delete data (CT-009). Three levels covers a simulation
  template containing a view step containing an export
- on_exceed: the pipeline is refused at edit time, naming the step that exceeded the depth
- decidedness: Fixed
- basis: E-001 (T1)

### LIM-008 - Loop iterations in one pipeline unit
- value: 1000
- unit: iterations
- source_of_truth: src/engine/limits.py:MAX_LOOP_ITERATIONS
- rationale: a loop count is resolved before the loop runs (XC-100), so this is a guard against a
  mistake rather than against divergence - a formula that yields a million iterations should stop at
  edit time, not after a night of running. A thousand covers a parameter sweep an engineer would
  actually read the results of
- on_exceed: the pipeline is refused before the run starts, naming the unit and the count it resolved to
- decidedness: Bounded
- open: OPEN-014
- basis: E-001 (T1)

### LIM-009 - Background scene budget
- value: 4000000
- unit: primitives per @View, counting a splat and a triangle alike
- note: the value is written in whole primitives, as the constant is written. A limit stated in
  millions beside a constant counting units is how a thousand-fold error passes a parity check that
  compares literals - the failure LIM-001 already survived once, recorded in `src/engine/limits.py`
- source_of_truth: src/engine/limits.py:MAX_BACKGROUND_PRIMITIVES
- rationale: background is appearance, and appearance must not spend the frame budget the result needs.
  Four million leaves the interactive ceiling of LIM-002 intact for the data itself on the measured
  hardware class (E-063). The limit is stated in primitives so that it applies to whichever background
  kinds turn out to ship (OPEN-016) rather than naming any of them
- on_exceed: the background is offered with its cost stated and is not applied until accepted; the
  result geometry is never reduced to make room for it
- decidedness: Bounded
- open: OPEN-008
- basis: E-063 (T1)

### LIM-010 - Time to first rendered result
- value: TBD
- unit: seconds from launch to a rendered sample result
- rationale: the first impression of a desktop tool is how long it takes to show something. The number
  is not written here until it is measured on the hardware class of E-063, because a limit nobody
  measured is a wish (XC-137)
- on_exceed: the launch path is profiled and the cause named; the budget is not raised to fit the code
- decidedness: Open
- open: OPEN-017

### LIM-011 - Selection to reflected change
- value: TBD
- unit: milliseconds from selecting a @Case to every area showing it
- rationale: the product's central promise is that switching case changes the subject everywhere at
  once (11_ui.md). If that takes long enough to notice, the promise is not kept
- on_exceed: profiled and named, never absorbed by removing the promise
- decidedness: Open
- open: OPEN-017

### LIM-012 - Output before the product asks about it
- value: 20
- unit: gigabytes of run output in one @Workspace
- rationale: output grows by one folder per run and is never overwritten (XC-113), so it grows without
  limit. This is not a refusal - it is the point at which the product says how much space is in use and
  offers to prune by run (XC-141). Twenty gigabytes is roughly a forty-case study exported many times
  over, which is when a user would want to be asked rather than to discover it
- on_exceed: the workspace reports its output size and offers pruning, oldest run first, naming what
  would be deleted; nothing is removed without the user choosing it
- decidedness: Bounded
- open: OPEN-008
- basis: E-001 (T1)

### LIM-013 - Imported MaterialX expansion and decoded-resource ceilings
- value: four independent ceilings are required before the parser ships - XML/tree depth, XInclude
  depth and dependency count, total expanded material-package bytes, and decoded image pixels; their
  numerical values are unset until the hostile-input spike measures the pinned parser and image stack
- unit: levels, dependencies, bytes and decoded pixels per imported Material Asset revision
- rationale: one aggregate file-size limit misses a tiny deeply recursive XML document and a small
  compressed image that expands to excessive memory. Setting numbers without measuring the pinned
  libraries would only move the denial-of-service threshold from unknown to invented (XC-178)
- on_exceed: refuse before allocating or following the next dependency, preserve the package, report
  `limitExceeded` with the dimension and observed count, and make no network or out-of-package request
- decidedness: Open
- open: OPEN-018
