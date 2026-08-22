---
status: draft
updated: 2026-08-22
---

# Glossary, units and coordinates

One word, one meaning. Settled first: a missing unit or axis convention stays consistent inside
round-trip conversions, so tests do not catch it, and in a product whose value is numerical
trustworthiness the correction is expensive twice - once in code, once in credibility.

Reference a term from any other spec by writing `@Term`.

## Product terms

### GL-001 - Workspace
- definition: the top-level container for one investigation - a set of related analysis runs, their
  saved @Simulation flows, visualisations, graphs, reports, variables and reference material, saved and
  reopenable as a unit
- not: a project folder on disk; a @Workspace is a document with its own format and version
- decidedness: Fixed
- basis: E-001 (T1)

### GL-002 - Case
- definition: one analysis result inside a @Workspace, nestable to any depth, inheriting settings and
  @Variable values from its parent unless overridden
- not: a single file; a @Case may carry many files and many time steps
- decidedness: Fixed
- basis: E-001 (T1)

### GL-003 - Variable
- definition: a named quantity in a @Workspace that can be referenced anywhere inside it. A variable is
  a single value, a value that varies over time or space, or an expression computed from other
  quantities - the user sees one list (XC-088)
- not: a value without a stated origin. **Every variable carries its @Provenance**, and a variable
  computed from data is not the same thing as one a person typed, even when both are numbers
- decidedness: Fixed
- basis: E-001 (T1)

### GL-016 - Provenance
- definition: where a quantity came from, carried with it everywhere it is shown or exported: declared
  by a person, read from a @Dataset, computed by an expression (with the expression), or taken from
  @Reference material
- not: a label applied at display time. Provenance travels with the value from the moment it exists,
  because a number's origin cannot be reconstructed after the fact
- decidedness: Fixed
- basis: E-001 (T1)

### GL-004 - Inheritance
- definition: the rule by which a child @Case takes its parent's @Variable values; per variable it is
  either inherited (child cannot edit, follows the parent) or overridden (child holds its own value)
- not: copying. An inherited value that stops following its parent is an override, and is recorded as one
- decidedness: Fixed
- basis: E-001 (T1)

### GL-005 - Dataset
- definition: the numerical result data of a @Case as loaded into memory - geometry plus the @Field
  values attached to it, at one or more time steps
- not: the file on disk. One @Dataset may come from many files, and one file may hold many @Dataset
- decidedness: Fixed
- basis: E-001 (T1)

### GL-006 - Field
- definition: one physical quantity carried by a @Dataset - pressure, velocity, stress - attached
  either to points or to cells, scalar or vector or tensor. A field appears in the variable list with
  the provenance "read from data"
- not: interchangeable with a value a person declared. The two share a list and a reference syntax;
  they do not share an origin, and the interface never lets that difference disappear (XC-088)
- decidedness: Fixed
- basis: E-001 (T1)

### GL-007 - Point data and cell data
- definition: a @Field attached to mesh points, or to mesh cells. Converting between them changes
  values - averaging cell values to points lowers extrema, and the peak stress a user is looking for
  can disappear in the conversion
- not: interchangeable. Which one a displayed or reported number came from is stated, never assumed
- decidedness: Fixed
- basis: E-001 (T1)

### GL-008 - View
- definition: one saved visual configuration - camera, renderer, colour map, materials, background,
  style - belonging to the @Workspace and applied to whichever @Case is in scope. A workspace may own
  multiple views and switch between them; a @View may be created from or saved as a @Template, but is
  not itself one (XC-109)
- not: a screenshot, and not a per-case setting. A @View is the recipe; the image is its output, and
  the case is an argument rather than an owner. It is also not a live alias of its source template
- decidedness: Fixed
- basis: E-088 (T1)

### GL-009 - Renderer backend
- definition: the engine that turns a @Dataset and a @View into pixels. Four exist, with separate jobs:
  the web renderer in the shell for interaction, the native renderer in the engine for large data and
  for report images, an experimental web path, and an optional photorealistic path (XC-087)
- not: a file format, and not a choice the user has to make to get a picture. Switching backend must
  not change the numbers reported, only the picture
- decidedness: Fixed
- basis: E-016 (T1), E-063 (T1)

### GL-015 - Graph
- definition: a saved figure definition belonging to the @Workspace - which @Field values, over which
  cases or time steps, with which styling. A workspace may own multiple graphs; each is a concrete
  editable artefact that may be created from or saved as a @Template (XC-109)
- not: the rendered image, and not the reusable template it may have come from. The definition is the
  workspace artefact; the picture is its output
- decidedness: Fixed
- basis: E-088 (T1)

### GL-010 - Report
- definition: a deliverable definition belonging to the @Workspace, producing an interactive 3D HTML
  document (primary), an office document, an image or a video from the cases in scope. A workspace may
  own multiple reports; each may be created from or saved as a @Template (XC-109)
- not: an export of raw data, a document owned by one case, or the reusable template it may have come
  from. A @Report is authored output intended for someone else to read
- decidedness: Fixed
- basis: E-088 (T1)

### GL-011 - Diff
- definition: the comparison of the same @Field between two @Case. On a shared mesh it is a direct
  point-by-point difference; across different meshes it is computed on a named resampled dataset the
  user asked for, and carries the resampling direction, the outside-point count and the round-trip
  error with it
- not: a file diff, and not a number that stands alone - a cross-mesh @Diff without its disclosure is
  physical difference, discretisation and interpolation added together and presented as one
- decidedness: Fixed
- basis: E-054 (T1), E-056 (T1)

### GL-012 - Reference material
- definition: user-supplied documents (specifications, papers, notes) that the assistant may consult
  when writing commentary
- not: a source of numbers. Values from @Reference material never override values read from a @Dataset,
  because the document may describe a different run than the one loaded
- decidedness: Fixed
- basis: E-001 (T1)

### GL-013 - Art style
- definition: the user-selectable visual identity applied to @View output and @Report - fonts, icon set,
  colour maps, graph styling - so that deliverables look like the user's own documents
- not: a theme for the application interface. A @Art style is applied to what is exported, not to the tool
- decidedness: Fixed
- basis: E-001 (T1)

### GL-014 - Headless agent mode
- definition: operating the product entirely from outside, by an external program or language model,
  through a documented command surface, with no human at the interface
- not: the in-application chat. That is a human asking; this is a machine driving
- decidedness: Fixed
- basis: E-001 (T1)

### GL-017 - Template
- definition: a reusable blueprint for creating a @View, @Graph or @Report. It stores the same
  definition shape as that artefact plus its requirements, scope and revision. Applying it resolves
  references against the target and creates a new, independently editable workspace artefact (XC-090,
  XC-109). A template may be limited to one @Workspace or shared across workspaces
- not: the currently open @View, @Graph or @Report, and not a live alias whose later edits silently
  propagate into artefacts already created from it. A workspace-scoped template is still a reusable
  blueprint, not the workspace's list of working artefacts
- decidedness: Fixed
- basis: E-088 (T1)

### GL-018 - Asset
- definition: a reusable, packaged resource stored in a @Library scope and applied or instantiated by
  identifier. Assets include materials, colour maps, fonts, backgrounds, display styles, camera paths
  and reusable View-object definitions. Asset describes the resource's storage and reuse lifecycle,
  not the type of thing shown in a View (XC-166)
- not: the working @View object or the source @Dataset. Applying an appearance Asset never changes a
  value (INV-002); instantiating an Object asset creates an independently editable View object rather
  than a live alias to the library entry
- decidedness: Fixed
- basis: E-001 (T1), E-095 (T1)

### GL-019 - Library scope
- definition: where a @Template or @Asset lives - **sample** (shipped with the product, never edited in
  place), **workspace** (belongs to one @Workspace and travels with its file), or **shared** (available
  to every @Workspace on this machine). In the interface, `Sample` is the shipped source and
  `Original` contains workspace/shared user entries; source and availability are not presented as the
  same choice
- not: a permission. Scope decides where something is found and what it travels with, not who may use it
- decidedness: Fixed
- basis: E-001 (T1)

### GL-022 - Pipeline
- definition: a registered, repeatable flow belonging to a @Workspace and standing **above** @Case: an
  ordered, editable list of @Pipeline unit that add cases to a @Target set and act on all of it. It
  runs with no simulation involved; a simulation unit, when it arrives, pins one saved @Simulation flow
  and adds each successful execution's result Case to the same target set (XC-154)
- not: a per-case setting, or a record of what already happened. A @Pipeline may reference a concrete
  workspace artefact or a @Template, and is also composed from bounded loops, variables, formulas and
  conditions - it computes, but only in a language with no interpreter behind it (XC-100, XC-101)
- not: a script. A script may **build** one (XC-102), and what is stored is this declarative list either
  way
- decidedness: Fixed
- basis: E-001 (T1)

### GL-023 - Stored precision
- definition: the numeric type a quantity was read or computed in - 32-bit float, 64-bit float, or an
  integer - carried with the quantity as part of its @Provenance
- not: the number of digits shown. A value read as a 32-bit float carries about seven significant
  decimal digits; displaying fifteen of them does not make it more precise, it makes the display a lie
- decidedness: Fixed
- basis: E-001 (T1)

### GL-024 - Significant digits
- definition: how many digits of a value are meaningful, derived from its @Stored precision and from
  any tolerance stated for the quantity - and the number of digits the interface and every export show
- not: a formatting preference. Digits are a claim about the measurement, so they are decided by the
  data rather than by whoever laid out the table
- decidedness: Fixed
- basis: E-001 (T1)

### GL-025 - Pipeline unit
- definition: one entry in a @Pipeline - add cases, apply a workspace @View, @Graph or @Report or its
  reusable @Template, export, clear, tag, loop, set a @Variable, compute a formula, or branch on a
  condition, or invoke a saved @Simulation flow in the later release. Units run in order, and a unit
  that contains others runs them for each repetition
- not: a step of a recorded history. A pipeline unit is written before anything runs, and editing one
  changes what the next run will do
- not: a physical unit. The interface calls these units, and this product's central discipline is about
  metres and pascals, so the specification always says **pipeline unit** and never the bare word
- decidedness: Fixed
- basis: E-001 (T1)

### GL-026 - Target set
- definition: the cases a @Pipeline is currently acting on. A case unit adds to it, a clear unit empties
  it, and every view, graph and report unit applies to all of it (XC-099)
- not: the selection in the interface. The interface's selection is what the user is looking at; the
  target set is what a run is working through, and the two are independent
- decidedness: Fixed
- basis: E-001 (T1)

### GL-027 - Expression
- definition: a formula written in this product's restricted language - arithmetic, comparison, boolean
  operators, the ternary conditional, a fixed set of mathematical functions, and references to
  @Variable and to recorded quantities - evaluated by this product rather than by a Python interpreter
  (XC-101). Units propagate through it, so incompatible units are refused rather than coerced
- not: code. There is no attribute access, no indexing into the product's objects, no imports and no
  function definitions, and nothing an expression can write to
- decidedness: Fixed
- basis: E-065 (T1)

### GL-028 - Script
- definition: Python that **builds** a @Pipeline, a @View, a @Graph or a @Report, or drives the product
  through the same command surface the interface uses (CT-002). A script is run deliberately; nothing
  stored in a @Workspace executes when the workspace is opened (XC-102)
- not: a stored format. What a script produces is the ordinary declarative document, which is what gets
  saved - so a workspace built by script and one built by hand are indistinguishable afterwards
- decidedness: Fixed
- basis: E-064 (T1)

### GL-029 - Part
- definition: one named region of a @Dataset as the solver wrote it - a block, a named selection, an
  assembly component. Parts are selectable, displayable and **summarisable on their own**
- not: a filter the user drew. A part came from the source file and carries the name the engineer gave
  it, which is how a result is discussed out loud
- decidedness: Fixed
- basis: E-001 (T1)

### GL-030 - Summary statistic
- definition: a single number reduced from a @Field over a scope - a @Part, a selection, or the whole
  model - carrying **which reduction, which scope, and which weighting** was used (INV-017)
- not: "the average". Arithmetic and volume-weighted means of the same field are different numbers, and
  both are defensible, so a summary statistic that does not say which it is has not been reported
- decidedness: Fixed
- basis: E-001 (T1)

### GL-031 - Current time step
- definition: which step of a @Case's time axis is being shown or measured, held as a @Variable so that it can
  be inherited, bound to an input, and iterated over by a @Pipeline loop
- not: an animation setting. Animation is a range of current-time values played in order; the value
  itself is what every number on screen refers to
- decidedness: Fixed
- basis: E-001 (T1)

### GL-032 - Derived quantity
- definition: a value computed from a @Field by a named entry of the catalogue in
  [15_derived_quantities.md](15_derived_quantities.md) - a component, a magnitude, von Mises, a
  principal value - carrying the formula that produced it in its @Provenance
- not: an expression a user wrote. Those are @Expression, shown wherever they appear; the catalogue is
  the fixed set the product computes on request, with conventions taken from the field (E-073)
- decidedness: Fixed
- basis: E-073 (T1)

### GL-033 - Component frame
- definition: the named coordinate frame a vector or tensor component is reported in - global Cartesian
  by default, or a cylindrical, spherical or local frame defined on the @Workspace with an origin and an
  orientation
- not: a display option. Changing the frame changes the numbers, so it is recorded with every value
  derived through it, and a component with no resolvable frame is refused (XC-122)
- decidedness: Fixed
- basis: E-073 (T1)

### GL-034 - Source identifier
- definition: the identifier a source file gave a point or cell - a numeric **global identifier**,
  unique in the dataset, and optionally a **pedigree identifier** that may be text and need not be
  unique (E-075)
- not: a position in an array. An index changes when the file is written differently, so it is never
  shown as an identifier and never cited in a @Report
- decidedness: Fixed
- basis: E-075 (T1)

### GL-035 - Measurement data
- definition: measured values imported against a @Case - from a test, a rig, a sensor - each able to
  carry its own uncertainty, so that a computed result can be compared with it (XC-107)
- not: @Reference material. A document describing an experiment is reference material and may not
  supply numbers; the experiment's values, imported as data, may
- decidedness: Fixed
- basis: E-070 (T1)

### GL-036 - Result axis
- definition: what indexes a @Case's results. **Time** for a transient run, **mode number** with its
  eigenfrequency for a modal run, **frequency** with a **phase angle** for a harmonic run, and nothing
  for a steady run. @Current time step is the position on this axis, whichever axis it is, so a
  @Pipeline loop iterates modes and frequencies exactly as it iterates time
- not: always time. A mode is not a moment, and a report that labels mode 3 as "t = 3" has said
  something false about the physics
- decidedness: Fixed
- basis: E-076 (T2)

### GL-037 - Complex result
- definition: a result with a real and an imaginary part, as a harmonic response is. Its **amplitude**
  is the square root of the sum of the squares of the two parts, and its value **at a phase angle** is
  the real part times the cosine of the angle minus the imaginary part times the sine
- not: two unrelated fields. Real and imaginary belong together, and a graph of one without the other,
  or without the phase it was taken at, is not interpretable
- decidedness: Fixed
- basis: E-076 (T2)

### GL-038 - Deformation scale
- definition: the multiplier applied to displacement when a body is drawn deformed. **1.0 is the real
  shape.** Any other value draws a body that does not exist at that shape, at that scale
- not: a rendering preference. The factor changes what a reader measures off the picture, so it travels
  with every image, video and report that used it (INV-024)
- decidedness: Fixed
- basis: E-077 (T2)

### GL-039 - Case state
- definition: where a @Case is in its lifecycle - **unresolved** (its files cannot be found or have
  changed), **unloaded**, **loading**, **loaded**, **partial** (loaded with gaps, XC-002) or **failed**
  - shown in the case tree and used by the @Pipeline to decide what to skip
- not: a filter or a tag. State is what the product observed; a tag is what a person decided
- decidedness: Fixed
- basis: E-001 (T1)

### GL-040 - Display unit
- definition: the unit a quantity is shown in - millimetres for length, megapascals for stress -
  chosen per quantity on the @Workspace. Storage stays canonical (GL-021); only presentation changes
- not: a @Declared unit. Declaring says what the numbers in the file mean; a display unit says what the
  reader sees, and one may not be inferred from the other (XC-003)
- decidedness: Fixed
- basis: E-001 (T1)

### GL-042 - Outliner
- definition: the tree at the top of the View area's right sidebar that exposes the selected
  @Dataset's source-authored containment: file root, assemblies, blocks, named selections and @Part
  entries.
  Each row carries an expand or collapse control where it has children, a type icon, the source name,
  selection state and visibility control
- not: the @Case tree, a geometry editor, or a hierarchy inferred from similar names. If the source
  carries no parent-child relation, its elements remain siblings and the interface says that the
  source supplied no hierarchy
- decidedness: Fixed
- basis: E-079 (T1)

### GL-043 - Simulation
- definition: one saved, editable external-solver execution flow belonging to a @Workspace. It groups
  the explicit conditions for **one or more solver executions** in their declared order: which solver
  adapter is used, which input references and parameter bindings each execution receives, and how its
  output is collected. A workspace may own multiple simulations and switch between them (XC-154)
- not: one solver process, one result @Case, or a @Pipeline. A Simulation describes how analysis results
  will be produced; a Case is a produced or imported result, while a Pipeline may invoke a saved
  Simulation and then apply Views, Graphs and Reports to its resulting cases. This product still never
  computes the physical solution itself (XC-091)
- decidedness: Fixed
- basis: E-080 (T1)

### GL-044 - View object
- definition: one instantiated, selectable display entity owned by a @View. A View object has a
  CAE-specific object type, visibility and display state; it may reference a @Dataset or a derived
  definition and may hold material slots or other appearance-Asset references (XC-159, XC-166)
- not: an @Asset or a @Dataset. Saving a reusable snapshot creates or updates an Object asset in a
  @Library scope; applying that Asset creates another independent View object and retains only its
  source identifier and revision as provenance
- decidedness: Fixed
- basis: E-001 (T1), E-095 (T1)

### GL-045 - Material
- definition: one immutable-revision @Asset whose CT-011 definition points to one root MaterialX
  material graph and declares every literal, texture, geometry property, SOLVIA result or referenced
  material input it requires. Whether it is data-independent, analysis-data-dependent or composite is
  derived from that interface, not stored as a material kind (XC-174)
- not: a physical or engineering material record, a resolved binding to one @Dataset, a thumbnail, or
  a renderer-native VTK/MDL property object
- decidedness: Fixed
- basis: E-108 (T1), E-001 (T1)

### GL-046 - Material Binding
- definition: one CT-004 instance that applies an immutable @Material revision to a whole
  @View object, part or element set and binds the graph's published inputs to literals, geometry
  properties, other Material Assets or SOLVIA result identifiers. Its resolved/failed state is derived
  against the current @Case and renderer (XC-175, XC-176)
- not: another Material Asset revision, an implicit material layer, or a container for result arrays
- decidedness: Fixed
- basis: E-108 (T1), E-111 (T1), E-001 (T1)

### GL-047 - Engineering material
- definition: a separately provenance- and unit-bearing definition of physical properties such as
  density, elastic modulus, Poisson ratio, yield strength or temperature dependence
- not: a @Material. A rendering graph or a name such as steel never supplies an engineering
  property and applying it never changes an analysis input (XC-179)
- decidedness: Fixed
- basis: E-001 (T1)

## Units

CAE result files usually carry no unit information: the solver wrote numbers, and the meaning of those
numbers lives in the engineer's head or in a document. A product that shows a number next to a unit it
guessed is worse than one that shows no unit at all.

### GL-041 - Absolute or difference
- definition: whether a declared quantity is a **point on a scale** or an **interval on it**. It
  matters wherever a unit has an offset - temperature is the everyday case - because the two convert
  by different rules (INV-028)
- not: a property the product can infer. A field named `dT` may hold absolute temperatures and a field
  named `T` may hold rises; only the person who ran the analysis knows, so it is declared beside the
  unit (XC-003)
- decidedness: Fixed
- basis: E-001 (T1)

### GL-020 - Declared unit
- definition: the unit a user states for a @Field, per @Case, and which every displayed number,
  axis label and report value then carries
- not: a detected unit. Nothing in this product infers units from data
- decidedness: Fixed
- basis: E-001 (T1)

| Quantity | Internal unit | Suffix in names | Example |
|---|---|---|---|
| length | m | `_m` | `bounds_min_m` |
| time | s | `_s` | `time_step_s` |
| memory | bytes | `_bytes` | `dataset_bytes` |
| angle | radians | `_rad` | `camera_azimuth_rad` |

Internally every length is metres; the declared unit is applied at display and export only. A name
with no unit suffix is a defect: it is a second, implicit definition of the unit (P7).

## Coordinate frames

### GL-021 - Canonical frame
- definition: the frame in which all geometry is held in memory: right-handed, Z up, metres
- not: the frame of any particular file. Every reader converts into this frame on load, and every
  writer converts out of it on export
- decidedness: Fixed
- basis: E-040 (T1)

| Frame | Origin | Up axis | Units | Used by |
|---|---|---|---|---|
| canonical | dataset bounds preserved as read | Z | m | in-memory @Dataset, @Diff, all reported numbers |
| USD export | as canonical | declared in the file (`upAxis`, `metersPerUnit`) | declared | Blender, Omniverse |
| Web renderer | as canonical, converted at the boundary | Y (WebGL convention) | m | browser display only |

Conversions between frames belong in exactly one named place, and the reported numbers are computed in
the canonical frame only - never in a display frame, which exists to make a picture and may be scaled.

**USD's own defaults disagree with both conventions**: `metersPerUnit` defaults to 0.01, that is
centimetres, and `upAxis` to Y, while CAE and Blender work in Z-up metres. Every file this product
writes therefore states both explicitly. A USD file that omits them is not neutral - it is a file that
says centimetres and Y-up to whoever opens it (XC-048).
