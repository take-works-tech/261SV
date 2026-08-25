---
status: draft
updated: 2026-08-26
---

# Invariants

What must always be true. Each is written so that a machine, or a mechanical review pass, can judge
it. An invariant that cannot be judged is not an invariant - it is a wish.

### INV-001 - Reported numbers come from the canonical frame
- statement: every number shown, exported or written into a @Report is computed on the @Dataset in the
  canonical frame and its declared unit, never from display geometry. The canonical frame's coordinates
  are **float64**, refused otherwise at construction (XC-245): `vtkPoints` stores single precision by
  default and a cell volume computed from it carries about 5e-8 of relative error (E-142), which
  INV-017's volume weighting then multiplies into the reported value
- rationale: display geometry is scaled, decimated and tessellated to make a picture; measuring it
  produces a number that is wrong in a way that looks right
- checked_by: a test that renders a case at two zoom levels and two decimation settings and asserts
  every reported value is bit-identical; and a test that reads a volume mesh and asserts that a field
  index and a geometry index name the same point, which the two-triangle fixture could never show
  because its surface is itself
- correction: the invariant was right and the code was not, which is recorded here because the two
  looked alike for four tasks. The reader stored the extracted display surface as the @Dataset's
  geometry while reading the fields from the original grid, so `points_m` was display geometry by
  construction - 26 points against 27 field values on a 3x3x3 block of hexahedra, in a different order
  (E-132). Every reported **aggregate** stayed correct, because the fields came from the full grid,
  which is why nothing failed; anything computed from a **coordinate** came from display geometry, and
  a probe would have returned a real value belonging to another point. Fixed at the structure rather
  than at the reader: a @Dataset now holds both geometries and refuses a field whose length belongs to
  neither (XC-233)
- decidedness: Fixed
- basis: E-001 (T1), E-132 (T1)

### INV-002 - Renderer choice does not change numbers
- statement: switching @Renderer backend changes pixels only; every reported value is unchanged
- checked_by: a golden test that runs the same @View through each available backend and compares the
  reported values, not the images
- decidedness: Fixed
- basis: E-001 (T1)

### INV-003 - Point and cell association is carried, never assumed
- statement: every @Field keeps its association through load, conversion, diff, graph and report, and
  any conversion between them is an explicit, recorded operation
- checked_by: a test asserting that a cell-associated field reported at a point raises rather than
  silently averaging
- decidedness: Fixed
- basis: E-001 (T1)

### INV-004 - One source of truth for a Variable
- statement: a @Variable has exactly one definition in a @Workspace; a child @Case either inherits it
  or holds an override that is recorded as an override
- checked_by: a test that changes a parent value and asserts every inheriting descendant changes and
  every overriding descendant does not
- decidedness: Fixed
- basis: E-001 (T1)

### INV-005 - A Workspace reproduces its output
- statement: opening a saved @Workspace and re-running its @View, @Graph and @Report produces the same
  output as when it was saved, given the same input files
- checked_by: a round-trip test that saves, reopens and compares exported artefacts
- decidedness: Fixed
- basis: E-001 (T1)

### INV-006 - The assistant cannot do what a user cannot
- statement: every operation available to @Headless agent mode is an operation available in the
  interface, and every operation goes through the same command surface with the same validation
- rationale: a second, privileged path is a second implementation of the rules, and the two will
  disagree - usually in the direction of the machine being allowed to break something quietly
- checked_by: a test asserting the command surface and the interface expose the same operation set
- decidedness: Fixed
- basis: E-001 (T1)

### INV-007 - Offline means offline
- statement: with networking disabled, every operation not explicitly marked as network-dependent
  completes normally, and no network call is attempted. A **produced deliverable** is held to the same
  rule: an exported document that reaches a host renders one way online and another way offline, which
  is the failure this exists to prevent, and the ordinary case is a customer opening it with no network
- checked_by: a test run with outbound network blocked, asserting both completion and zero attempts;
  and for an export, the produced text searched for an external reference and the file refused if one
  is found - checked of the output rather than trusted of the writer (XC-254)
- decidedness: Fixed
- basis: E-001 (T1)

### INV-008 - Provenance travels with a number
- statement: any value the assistant states carries whether it came from a @Dataset or from
  @Reference material, and material never overrides data
- checked_by: a test that plants a contradicting value in reference material and asserts the dataset
  value is the one reported, with its origin named
- decidedness: Fixed
- basis: E-001 (T1)

### INV-009 - A reported number never comes from a linear approximation of a high-order cell
- statement: high-order elements are read without loss, but surface extraction, contour and clip all
  operate on linear sub-cells, and integration defaults to a linear strategy. Any integral this
  product reports uses Gaussian quadrature and states when a cell fell back to the linear path; no
  number reported to the user is taken from an isosurface or a display surface
- rationale: the picture is allowed to be an approximation and the number is not. The two are produced
  by different code paths in the library this product embeds, and the approximate one is the default
- checked_by: a test integrating a field over a mesh with a known analytic answer, in both quadratic
  and Lagrange cells, asserting the reported value against the analytic value and asserting that a
  fallback to linear is reported rather than silent
- decidedness: Fixed
- basis: E-037 (T1), E-038 (T1)

### INV-010 - Duplicated points at partition boundaries are never counted twice
- statement: a partitioned dataset repeats the points on each partition interface, and repeats cells as
  well where the piece manifest declares ghost layers. Where the duplicates are marked, every count,
  mean and sum excludes them; where nothing marks them, those numbers are refused with the reason rather
  than reported. An extremum is reported either way
- rationale: the reader performs no merging, so a naive sum over a 64-piece run over-counts every
  interface. The error is small enough to look plausible and large enough to be wrong
- checked_by: a test comparing a reported integral over a partitioned dataset against the same dataset
  in one piece, and a test that the same numbers are refused when nothing marks the duplicates
- correction: the first statement said that every count, mean, integral **and extremum** excludes the
  duplicates, and implied that this is always possible. Measuring the toolkit showed both halves to be
  wrong (E-131). An extremum has nothing to exclude - the largest of a set is unchanged by writing part
  of it twice - so promising that it excludes duplicates described work that is not done and cannot be
  checked. And a `.pvtu` written at the default `GhostLevel="0"` carries no ghost array at all, so in the
  common case the duplicates are unidentifiable and no aggregate can exclude them; the reachable
  guarantee there is that the number is not reported (XC-232). Left as written, the invariant would have
  been satisfied by a merge-by-coordinate with a tolerance - which welds a crack face shut and would have
  been adopted on the authority of this line
- decidedness: Fixed
- basis: E-039 (T1), E-131 (T1)

### INV-011 - A point that could not be sampled is missing, not zero
- statement: wherever a value is transferred between meshes, points that fall outside the source carry
  the missing-value marker and are excluded from every derived number; the library's default of filling
  them with zero is overridden at the one place the transfer happens
- rationale: the embedded library initialises those outputs with zero and signals the failure only
  through a separate validity mask. A zero in a stress field is not obviously wrong to a reader - it is
  the single most dangerous default this product inherits, and it violates XC-001 out of the box
- checked_by: a test resampling onto a mesh that extends beyond the source, asserting the outside points
  report as missing rather than zero and are absent from the reported extrema and integrals
- decidedness: Fixed
- basis: E-054 (T1)

### INV-012 - Cell values are not silently promoted to points
- statement: transferring a cell-associated field between meshes keeps it cell-associated; where the
  library would copy the containing cell's value into a point, the product records that this happened
  and reports the association it now has
- rationale: the same transfer that interpolates point data merely copies cell data, and the result
  arrives as point data. A user comparing element stresses would be shown something that is neither the
  original association nor an interpolation, with nothing saying so (INV-003)
- checked_by: a test transferring a cell field and asserting the association and the recorded operation
- decidedness: Fixed
- basis: E-054 (T1)

### INV-013 - A quantity is never shown without its provenance
- statement: every quantity in the variable list, in an input bound to it, on a graph axis, in a table
  and in an exported report is displayed with its @Provenance - declared, read from data, computed, or
  taken from reference material - and a computed one carries its expression
- rationale: the list deliberately mixes values a person typed with values a solver produced (XC-088).
  Mixing them is convenient; mixing them invisibly would make every number in the product unfalsifiable
- checked_by: a test rendering a list containing one of each origin and asserting each is labelled, and
  an export test asserting the labels survive into the document
- decidedness: Fixed
- basis: E-001 (T1)

### INV-014 - A displayed number never claims more precision than its source
- statement: every value shown, exported or written into a report is formatted to the significant
  digits its @Stored precision supports; a 32-bit source is never shown with more than its meaningful
  digits, and a value derived from mixed precision takes the weakest
- rationale: the product's claim is that its numbers can be trusted, and a padded decimal expansion is
  the cheapest possible way to break that claim - it looks like precision and is noise
- checked_by: a test formatting a 32-bit field and asserting the digit count, and an export test
  asserting the same value appears with the same digits in the document
- decidedness: Fixed
- basis: E-001 (T1)

### INV-015 - Counts are integers and stay integers
- statement: cell counts, point counts, indices, time-step numbers and case counts are integer types
  end to end; none of them is ever stored, transported or compared as a floating-point value
- rationale: an index that has been through a float is an index that can be off by one at large
  magnitudes, and a count shown as 1.0000000001 destroys confidence in everything beside it
- checked_by: a type test over the engine interface asserting integer types on every count and index
- decidedness: Fixed
- basis: E-001 (T1)

### INV-016 - Physical values are never compared for exact equality
- statement: comparisons between physical quantities use a stated tolerance, and the tolerance is
  recorded with the comparison; exact equality is reserved for identifiers, counts and enumerations
- rationale: unit conversion multiplies by factors that are not exactly representable, so two values
  that are physically identical routinely differ in the last bits. Code that tests them for equality
  works on the developer's file and fails on the customer's
- checked_by: a test converting a value through two unit paths and asserting the product treats them as
  equal within the stated tolerance rather than as different
- decidedness: Fixed
- basis: E-001 (T1)

### INV-017 - A summary statistic carries its reduction, scope and weighting
- statement: every single number reduced from a @Field - mean, maximum, integral, standard deviation -
  records which reduction it is, over which scope (@Part, selection, or whole model), and with which
  weighting. The default is **volume-weighted for cell data and dual-volume-weighted for point data**;
  an unweighted arithmetic reduction is available and is labelled as such wherever it appears
- rationale: the arithmetic mean of a field over an unstructured mesh weights a millimetre-sized element
  the same as a metre-sized one. Both reductions are defensible and they are different numbers, so a
  reported "average" that does not say which it is has not been reported. This is the single easiest way
  for this product to be confidently wrong
- checked_by: a test on a mesh with deliberately non-uniform element sizes, asserting the two reductions
  differ and that each output carries its weighting label. The weights are cell volumes, so this
  invariant is why the canonical frame holds double-precision coordinates (XC-245, E-142) - the error in
  a single-precision volume arrives in the weighted mean
- decidedness: Fixed
- basis: E-001 (T1)

### INV-018 - Machine-readable output does not follow the locale
- statement: numbers written to CSV, JSON, script text and any other machine-readable output use a
  period as the decimal separator and no digit grouping, whatever the interface language is. Only
  numbers **displayed to a person** follow the locale
- rationale: in several European locales a comma is the decimal separator and a period groups thousands,
  so `1.234` is one thousand two hundred and thirty-four. A file written under one locale and read under
  another is silently off by a factor of a thousand, and every value in it still looks plausible
- checked_by: a test writing and re-reading an export under a comma-decimal locale, asserting the file
  bytes are identical to the period-locale output and that the round-trip value is unchanged
- decidedness: Fixed
- basis: E-001 (T1)

### INV-019 - A part keeps its name, hierarchy and own summaries
- statement: parts named by the source file survive reading with their names and source-authored
  parent-child relations, are individually selectable and displayable, and a @Summary statistic states
  whether its scope was one part or the whole model. Parts are never silently merged, renamed or put
  into an inferred hierarchy
- rationale: engineers discuss results by part name. A reader that flattens blocks into one mesh loses
  the vocabulary the result is discussed in, and a maximum over the whole model reported as if it were
  a part's maximum is a wrong number with a right-looking label
- checked_by: a test on a nested multi-block file asserting names and parent-child relations round-trip,
  a flat file remains flat, and a per-part maximum differs from the model maximum
- decidedness: Fixed
- basis: E-001 (T1)

### INV-020 - A derived quantity carries the formula that produced it
- statement: every @Derived quantity comes from the catalogue of 15_derived_quantities.md, is computed
  in the analysis module from canonical data, and records its formula and any convention it depended on
  - the ordering rule for principal values, the frame for a component
- rationale: von Mises computed with a sign error is the right shape and a plausible size, and nothing
  downstream can tell. The formula travelling with the value is what lets a reviewer check it instead of
  trusting it
- checked_by: a test computing each catalogue entry on a tensor with a known analytic answer, asserting
  both the value and the recorded formula
- decidedness: Fixed
- basis: E-073 (T1)

### INV-021 - A component is reported in a named frame or not at all
- statement: every vector or tensor component names its @Component frame. A component requested with no
  resolvable frame is refused, naming what is missing
- rationale: "radial stress" is not a quantity until an axis exists. Assuming the global Z axis is right
  most of the time, and the rest of the time it is wrong in a way that looks exactly like being right
- checked_by: a test requesting a cylindrical component with no frame defined, asserting refusal rather
  than a default axis
- decidedness: Fixed
- basis: E-073 (T1)

### INV-022 - Values are never averaged across a part or material boundary
- statement: cell values are not converted to point values unless asked for (INV-003), and when they
  are, cells on either side of a @Part or material boundary are not averaged together. An averaged value
  is labelled averaged wherever it appears
- rationale: the standard conversion averages every cell touching a point, restricted only by cell
  dimension (E-074). At a material interface that mixes values belonging to different physics into one
  number, and the result records nothing about it
- checked_by: a test on a two-material mesh asserting the interface points keep one value per material
  and that a whole-mesh average of the same field differs
- decidedness: Fixed
- basis: E-074 (T1)

### INV-023 - Identifiers come from the file, or are absent
- statement: global and pedigree identifiers written by the source are preserved and are what extreme
  values and cross-case correspondence are reported against. Where a file carries none, the product says
  so; an array index is never presented as an identifier
- rationale: "the maximum is at node 12345" is checkable in the solver; "the maximum is at index 8412"
  is checkable nowhere, and changes if the file is written again
- checked_by: a test reading a file with global identifiers and one without, asserting preservation in
  the first and an explicit absence in the second
- decidedness: Fixed
- basis: E-075 (T1)

### INV-024 - A measurement is taken on the undeformed body, and a deformed picture says its factor
- statement: distances, probes, dimension lines and every reported value are computed from the
  undeformed canonical coordinates unless the user explicitly asks for the deformed configuration,
  which is then labelled. **Every image, video and report block drawn with a @Deformation scale other
  than 1.0 carries that factor visibly**, in the picture itself and not only in a toolbar
- rationale: the established tool defaults to an automatically computed exaggeration and shows the
  factor in its toolbar, and its own knowledge base carries the recurring question of why the plot does
  not measure correctly against the on-screen ruler (E-077). Showing the factor somewhere is necessary
  and demonstrably not sufficient: a reader measuring the picture does not read the toolbar, and an
  exported image has no toolbar at all
- checked_by: a test rendering one case at scale 1.0 and at scale 50, asserting the reported values are
  identical, that the exported image carries the factor, and that a probe returns the undeformed
  position in both
- decidedness: Fixed
- basis: E-077 (T2)

### INV-025 - A derived visualisation records the parameters that produced it
- statement: anything computed by seeding and integrating - streamlines, particle traces, path lines -
  records its seed source, integrator, step size, step limit and termination criteria in the @View
  definition, and is labelled a derived visualisation rather than a measurement
- rationale: change the seed or the step size and the picture changes, from the same data. A line that
  cannot be regenerated identically is a line nobody can check, and one presented beside measured values
  borrows their authority (E-078)
- checked_by: a test producing streamlines twice from a stored definition and asserting the geometry is
  identical, and a second asserting a changed step size changes it
- decidedness: Fixed
- basis: E-078 (T1)

### INV-026 - A display unit never reaches storage or a computation
- statement: showing a length in millimetres changes the presentation only. Stored values stay canonical
  (GL-021), computation happens in canonical units, and any machine-readable export states the unit it
  wrote
- rationale: a unit chosen for reading that leaks into storage produces a file whose numbers mean
  something different from the file written yesterday, with nothing to distinguish them
- checked_by: a test switching the display unit and asserting the stored bytes and every computed
  result are unchanged
- decidedness: Fixed
- basis: E-001 (T1)

### INV-027 - A produced deliverable records the data it was produced from
- statement: every exported @Report records, for each @Case it used, the content identity of the input
  data and the version of the @Workspace, so that a delivered document can be told apart from one whose
  inputs have since changed
- rationale: a report is regenerated from definitions, which keeps it reproducible - and says nothing
  about the file already sent to a customer. Without a recorded identity, "is this the current result"
  has no answer
- checked_by: a test producing a report, changing an input file, and asserting the product reports the
  earlier deliverable as produced from data that has changed
- decidedness: Fixed
- basis: E-001 (T1)

### INV-028 - Temperature is affine, and a temperature difference is not a temperature
- statement: conversion between temperature units applies **scale and offset**; conversion of a
  temperature **difference** applies the scale only. A quantity is declared as one or the other, and a
  quantity declared as neither is treated as absolute
- rationale: 10 degrees Celsius is 283.15 K and a rise of 10 degrees Celsius is 10 K. A conversion
  that multiplies without adding puts every absolute temperature 273.15 K too low; one that adds to a
  difference inflates it by the same amount. **The second is harder to notice**, because the answer
  stays in a plausible range - which is the failure mode this whole product exists to refuse
- checked_by: tests/test_units.py::test_celsius_is_affine_not_a_factor and
  tests/test_units.py::test_a_temperature_difference_carries_no_offset
- decidedness: Fixed
- basis: E-001 (T1)

### INV-029 - A material graph consumes a display binding, never canonical data or engineering properties
- statement: a CT-011 MaterialX graph may consume display attributes resolved from a CT-004
  Material Binding, but it cannot open, mutate or replace the canonical @Dataset, and applying a
  @Material cannot supply or change an Engineering material property. Probe, extrema, graph,
  table and report values are identical before and after any material edit
- rationale: a programmable data-driven appearance is useful only while its shader remains downstream
  of the number path. Letting a familiar material name or a shader query become an analysis input would
  make a visual edit capable of changing a result without appearing in the solver provenance
- checked_by: a test binding the same result through data-independent and data-dependent MaterialX
  graphs and asserting canonical arrays, engineering properties and every reported value are byte- or
  value-identical while only pixels and explicit material failure state change
- decidedness: Fixed
- basis: E-108 (T1), E-001 (T1)

### INV-030 - Every rendered surface element resolves one root material or the diagnostic failure material
- statement: each visible surface element resolves exactly one root MaterialX material from its
  whole-object and non-overlapping subset bindings. An ambiguous overlap or unresolved required input
  resolves to the diagnostic magenta failure material with CT-010 detail, never renderer-specific
  precedence, a previous successful material or an undeclared default
- rationale: two renderers choosing different winners for the same overlapping assignments produces
  two authoritative-looking pictures from one View; keeping old pixels after an input disappears makes
  stale analysis indistinguishable from current analysis
- checked_by: a partition test that renders the same binding set through native VTK, vtk.js and USD,
  plus overlap and missing-input cases that must produce the same failed targets and reason codes
- decidedness: Fixed
- basis: E-111 (T1), E-001 (T1)

An invariant with no `checked_by` is on its way to being false. Write the check when you write the
invariant, and prove the check can fail before trusting it.

### INV-031 - Every reduction and every difference is accumulated in double precision
- statement: sums, means, integrals, standard deviations and differences are computed in float64
  whatever precision the field is stored in, and the accumulation is pairwise or better - never a
  sequential loop over a large array. The **storage** precision still bounds what may be *displayed*
  (INV-014); this invariant is about the arithmetic in between, and the two are not the same rule
- rationale: measured here on ten million values of 300.0 varying by 1e-3 - the ordinary shape of a
  temperature field or a stress about a preload. A float32 field accumulated in float32 gives a mean of
  **300.000000000000** where the exact mean is **299.999999895342**: the variation the field was written
  to carry is gone, and what is printed is the offset. Accumulating the same float32 field in float64
  costs nothing and is 160 times closer; a sequential float64 loop is a thousand times worse than a
  pairwise one (E-143).
- checked_by: a test summing a float32 field of a large offset and a small variation, asserting the
  float32-accumulated mean returns the offset exactly while this product's returns the variation; and a
  test asserting the float64 sum against the **measured bound** of 1.6e-16 rather than against another
  implementation. The first version compared it against Python's built-in `sum()` and asserted this
  product was closer, which passed on 3.11 and failed on 3.12 - the interpreter changed `sum()` to
  Neumaier summation (E-146) and the assertion was measuring the interpreter
- correction: 2026-08-25, same day. This invariant was first written with a second argument attached:
  that a difference of two values 1e-7 apart "subtracts to exactly 0.0 in float32", so a @Diff computed
  in the storage precision would report a real difference as agreement. **That was wrong.** Both
  literals round to the same float32 before any subtraction happens, and subtraction of two float
  values within a factor of two is exact - measured over 100,000 pairs (E-143).
  Computing differences in float64 is still what this product does, and it is still worth doing where
  the two operands are of different precisions or come from earlier arithmetic. What it does **not** do
  is rescue a distinction that storage already lost, and the invariant should not be read as claiming
  it does. The loss that is real in a near-equal difference is significance, and it has its own rule
  (INV-034)
- decidedness: Fixed
- basis: E-143 (T1), E-146 (T1)

### INV-032 - A value at a shared node is several values, and a reported extremum says which it is
- statement: where a @Field is held per element, the value at a node shared by several elements is
  **several values**. Any extremum, contour or reported figure derived from them states whether it is
  **averaged** or **unaveraged**, and the two are recorded as different numbers rather than one number
  with a display option. Where a product reports an averaged extremum it also carries the **spread** at
  that node - the difference between the largest and smallest contributing element value
- rationale: measured here on a stress concentration inside a body carrying element values 10, 20, 200,
  20, 10 MPa. Averaging onto the shared nodes gives a maximum of **110 MPa against 200 MPa - 55 per
  cent of it, an under-report of 90 MPa** (E-144). A report that says "maximum von Mises stress
  110 MPa" is not wrong about the averaging it did; it is wrong about the question it was asked.
  The same concentration at an **end face** gives 200 MPa either way, because that node belongs to one
  element - so this is invisible to any check placed at a boundary and visible only where a
  concentration actually is.
  The spread is not a defect to hide: the reference product publishes it as Nodal Difference and states
  that a large one indicates the mesh needs refining there (E-145). It is the one discretisation
  indicator a post-processor can compute from a single solve, and suppressing it while reporting the
  smoothed peak is the combination that reads as precision
- checked_by: a test on a mesh with an interior concentration, asserting the averaged and unaveraged
  maxima differ, that each figure carries its label, and that the spread at the peak node is reported
- decidedness: Fixed
- basis: E-144 (T1), E-145 (T1)

### INV-033 - This product states discretisation error where it can measure it, and never implies convergence
- statement: no output of this product states or implies that a result is mesh-independent, converged,
  or accurate to a tolerance, unless it was given the evidence for that claim - two or more meshes of
  the same problem, compared here. What it may always state is what it can measure from one solve: the
  spread at shared nodes (INV-032), the outside-point count and round-trip error of a cross-mesh
  comparison (XC-038), and the precision the source supports (INV-014)
- rationale: verification and validation are different questions and mixing them is a defect (E-069).
  A post-processor sees one solve. It cannot know whether the mesh was fine enough, whether the solver
  converged, or whether the model represents the article - and a report that presents a number without
  that boundary invites the reader to assume all three, which is the assumption the number cannot carry.
  Stating the indicator it *can* compute is the honest half, and it is why INV-032 requires the spread
  to travel with the smoothed value rather than instead of it
- checked_by: the report language check (XC-104) rejecting a statement of convergence, accuracy or mesh
  independence that no comparison supports, tested with a sentence of each kind
- decidedness: Fixed
- basis: E-069 (T1), E-144 (T1)

### INV-034 - A difference reports the digits the subtraction left, not the digits its storage holds
- statement: where a value is the difference of two nearly equal quantities, the significant digits it
  may be shown to are computed from **the operands and the gap between them** - roughly the operands'
  digits less `log10(|a| / |a - b|)` - not from the type the result is stored in. A difference that has
  no significant digits left is reported as unresolvable rather than as a number
- rationale: two stresses of 300 MPa differing by 1e-7 MPa each carry about ten digits, and their
  difference carries **one**: 9.5 digits are gone in the subtraction (E-143). Stored in float64, that
  difference will happily print fifteen, and INV-014 does not catch it because INV-014 reads the
  **storage** precision, which is genuinely float64 and genuinely irrelevant here.
  This is the one place where the arithmetic is exact and the reported number is still a lie. The
  subtraction loses nothing - measured over a hundred thousand float32 pairs, single and double
  precision agree exactly - and what it loses is the meaning of the digits that survive
- checked_by: a test taking the difference of two values agreeing in nine digits and asserting the
  reported figure carries one digit rather than fifteen; and a test asserting a difference below the
  resolution of its operands is reported as unresolvable
- decidedness: Fixed
- basis: E-143 (T1)
