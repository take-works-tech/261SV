---
status: draft
updated: 2026-08-22
---

# Tasks: view

### TASK-001 - View definition, save and reopen
- satisfies: AC-001
- depends_on: workspace/TASK-001
- done_when: a saved view holds identifiers only, and reopening reproduces the picture and the numbers

### TASK-002 - Resolution and the unresolved list
- satisfies: AC-004
- depends_on: TASK-001
- done_when: every reference in a definition is resolved against the target, and what does not resolve
  is listed by name and reason - the same path templates use later (XC-090)

### TASK-003 - Multiple views per case
- satisfies: AC-003
- depends_on: TASK-001
- done_when: a case carries several views with the active one identified

### TASK-004 - Renderer interface and capability probe
- satisfies: AC-006
- depends_on: TASK-001
- done_when: available renderers are probed at start, an unavailable one names its requirement, and an
  alternative is offered

### TASK-005 - Numbers identical across renderers
- satisfies: AC-005
- depends_on: TASK-004
- done_when: a golden test runs one view through each backend and compares reported values, not images

### TASK-006 - Reduced display with numbers from full data
- satisfies: AC-007
- depends_on: TASK-004
- done_when: a dataset above LIM-002 draws reduced, is marked reduced, and reports full-data values

### TASK-007 - Library panel and scopes
- satisfies: AC-011
- depends_on: TASK-001
- done_when: materials, colour maps, fonts and backgrounds apply from sample, workspace or shared
  scope, with the scope shown

### TASK-008 - Import with terms recorded
- satisfies: AC-012
- depends_on: TASK-007
- done_when: an imported asset records its origin and stated licence, and an export that cannot satisfy
  the terms is refused

### TASK-009 - Missing asset falls back and says so
- satisfies: AC-013
- depends_on: TASK-007
- done_when: a missing asset draws with the default and is named

### TASK-010 - Templates across workspaces
- satisfies: AC-014
- depends_on: TASK-002
- done_when: a view saved as a template creates an independent View in another workspace, showing
  resolved and unresolved before creation or drawing

### TASK-011 - Refusal when nothing resolves
- satisfies: AC-016
- depends_on: TASK-010
- done_when: a template matching nothing is refused rather than drawing an empty view

### TASK-012 - Time navigation
- satisfies: AC-017
- depends_on: TASK-001
- done_when: playback and a time position exist, the displayed step is stated, and a field absent at a
  step draws as missing rather than carrying forward

### TASK-013 - Drawing presentations
- satisfies: AC-008
- depends_on: TASK-001
- done_when: an orthographic three-view arrangement and a dimensioned style are selectable

### TASK-014 - Dimensions measured on the dataset
- satisfies: AC-010
- depends_on: TASK-013
- done_when: a dimension on a reduced display reports the full-data value, asserted by test

### TASK-015 - Dimension labels carry units
- satisfies: AC-009
- depends_on: TASK-013
- done_when: a dimension shows the declared unit or the undeclared marker

### TASK-016 - Image export from the definition
- satisfies: AC-019
- depends_on: TASK-004
- done_when: the same definition produces the same image bytes

### TASK-017 - Camera paths and video
- satisfies: AC-020
- depends_on: TASK-016
- done_when: a video follows the selected path and states the time mapping; a missing encoder is named
  and frames are still written

### TASK-018 - USD export stating unit and axis
- satisfies: AC-022
- depends_on: TASK-001
- done_when: the written file carries metersPerUnit and upAxis, and an unrepresentable element is named
  before writing

### TASK-019 - Split layout
- satisfies: AC-024
- depends_on: TASK-001
- done_when: one to four panes each render a chosen case through the open workspace View

### TASK-020 - Camera synchronisation
- satisfies: AC-025
- depends_on: TASK-019
- done_when: synchronisation moves every pane and its state is written onto exported images

### TASK-021 - Range comparability
- satisfies: AC-026
- depends_on: TASK-019
- done_when: differing colour-map ranges are marked and a common range is offered

### TASK-022 - Probe
- satisfies: AC-027
- depends_on: TASK-001
- done_when: a probed value comes from canonical data with unit, digits and provenance

### TASK-023 - Probe on cell data
- satisfies: AC-028
- depends_on: TASK-022
- done_when: cell values are reported as cell values, never interpolated to points

### TASK-024 - Probe outside the mesh
- satisfies: AC-029
- depends_on: TASK-022
- done_when: no value reports as missing rather than zero

### TASK-025 - Kept probes become variables
- satisfies: AC-030
- depends_on: TASK-022
- done_when: a kept probe carries case, position and time step

### TASK-026 - Current time step as a variable
- satisfies: AC-031
- depends_on: TASK-001
- done_when: the displayed step binds like any variable and a pipeline loop iterates it

### TASK-027 - Time stated on output
- satisfies: AC-032
- depends_on: TASK-026
- done_when: every displayed and exported value names its time step

### TASK-028 - Absent time steps refused
- satisfies: AC-033
- depends_on: TASK-026
- done_when: a missing step is reported, with no nearest-step substitution

### TASK-029 - View Outliner
- satisfies: AC-034, AC-055, AC-056
- depends_on: ingest/TASK-001
- done_when: the right sidebar's Blender-style tree preserves source names and hierarchy, synchronizes
  selection and visibility with the active viewport, and shows explicit flat, empty and partial states
  without inventing nodes

### TASK-030 - Statistic scope stated
- satisfies: AC-035
- depends_on: TASK-029
- done_when: every summary states whether it covered one part or the model

### TASK-031 - Background kinds, chosen while building them
- satisfies: AC-036
- depends_on: TASK-001
- done_when: each kind that ships is measured on the E-063 hardware class, the set is recorded against
  OPEN-016, and every kind is asserted to leave reported values unchanged

### TASK-032 - Background cost stated
- satisfies: AC-037
- depends_on: TASK-031
- done_when: adding a splat scene or a prop states its cost against LIM-009 first

### TASK-033 - Background budget enforced
- satisfies: AC-038
- depends_on: TASK-032
- done_when: over-budget content is refused and result geometry is never reduced for it

### TASK-034 - Orthographic and three-view
- satisfies: AC-039
- depends_on: TASK-001
- done_when: 2D presentations share the 3D view definition

### TASK-035 - Dimension lines from canonical data
- satisfies: AC-040
- depends_on: TASK-034
- done_when: an annotation's value comes from canonical data with unit and digits

### TASK-036 - Video from a named camera path
- satisfies: AC-041
- depends_on: TASK-001
- done_when: path and playback speed are recorded on the output

### TASK-037 - Time mapping on video
- satisfies: AC-042
- depends_on: TASK-036, TASK-026
- done_when: wall-clock to simulated time is stated and travels into reports

### TASK-038 - The derived-quantity catalogue
- satisfies: AC-043
- depends_on: analysis module
- done_when: every catalogue entry matches an analytic answer and records its formula

### TASK-039 - Principal ordering
- satisfies: AC-044
- depends_on: TASK-038
- done_when: values are ordered largest to smallest and the ordering is stated where shown

### TASK-040 - Component frames
- satisfies: AC-045
- depends_on: TASK-038
- done_when: every component names its frame, defaulting to global Cartesian

### TASK-041 - Unresolvable frames refused
- satisfies: AC-046
- depends_on: TASK-040
- done_when: a component with no resolvable frame is refused with the reason

### TASK-042 - Averaging stops at boundaries
- satisfies: AC-047
- depends_on: TASK-029
- done_when: cell-to-point conversion never crosses a part or material boundary and labels its output

### TASK-043 - True scale by default
- satisfies: AC-048
- depends_on: TASK-001
- done_when: deformation draws at 1.0 unless changed, with auto-scale one action away

### TASK-044 - The factor is in the picture
- satisfies: AC-049
- depends_on: TASK-043
- done_when: a non-unit factor appears in the view and in every export

### TASK-045 - Measurements on undeformed coordinates
- satisfies: AC-050
- depends_on: TASK-043
- done_when: probes and dimension lines are unaffected by the scale, and deformed measurement is labelled

### TASK-046 - Streamline parameters recorded
- satisfies: AC-051
- depends_on: TASK-001
- done_when: a stored definition regenerates identical geometry and a parameter change changes it

### TASK-047 - Derived visualisation labelled
- satisfies: AC-052
- depends_on: TASK-046
- done_when: seeded pictures are labelled where they appear beside measured values

### TASK-048 - Display units
- satisfies: AC-053
- depends_on: TASK-001
- done_when: display changes and storage and computation do not

### TASK-049 - No display unit without a declared unit
- satisfies: AC-054
- depends_on: TASK-048
- done_when: an undeclared quantity refuses a display unit and keeps its marker

### TASK-050 - View-object identity
- satisfies: AC-058
- depends_on: TASK-001, TASK-029
- done_when: every instantiated display entity has View-local object identity and remains distinct from
  its source Dataset and any reusable Asset

### TASK-051 - Object-asset instantiation
- satisfies: AC-059
- depends_on: TASK-002, TASK-007, TASK-050
- done_when: applying an Object asset creates an independent View object with source Asset id and
  revision provenance, and later Asset changes do not silently propagate

### TASK-052 - Object and Asset UI terminology
- satisfies: AC-060
- depends_on: TASK-050, TASK-051
- done_when: current-state controls say Object, the View library category says Object, and Asset remains
  reserved for reusable-resource lifecycle language

### TASK-053 - Preserve authored reference-mesh UV sets
- satisfies: AC-061
- depends_on: TASK-050
- done_when: every imported reference-mesh UV set round-trips with the same name, values, indices and
  interpolation, and automatic mapping never overwrites one

### TASK-054 - Resolve and lazily generate analysis-mesh texture mapping
- satisfies: AC-062, AC-063, AC-064
- depends_on: TASK-004, TASK-050, TASK-053
- done_when: UV-free appearances allocate no UV data; triplanar and declared projections use their
  stored mapping parameters; unique-UV materials generate a deterministic charted display atlas whose
  cache is topology-keyed and whose data never enters the canonical Dataset

### TASK-055 - Texture-mapping status and fail-closed application
- satisfies: AC-065, AC-066
- depends_on: TASK-007, TASK-054
- done_when: the Materials properties expose the resolved high-level mapping and status without a UV
  editor, and a failed or unsupported mode names its reason and uses no undeclared fallback

### TASK-056 - CT-011 MaterialX Asset loader and code-managed library
- satisfies: AC-078, AC-080, AC-083, AC-088
- depends_on: TASK-007
- done_when: one CT-008 material kind loads exactly one qualified MaterialX root, validates with the
  pinned official API, round-trips original bytes and unknown content, verifies its SOLVIA backlink and
  hashes, creates immutable upgrades, and has no rendering path into engineering properties

### TASK-057 - Targeted Material Bindings and result-input lowering
- satisfies: AC-070, AC-079
- depends_on: TASK-050, TASK-056
- done_when: CT-004 binds immutable material revisions to whole objects or non-overlapping subsets,
  rejects overlap, resolves one root per surface element and lowers every typed `solviaResult` input to
  a validity-bearing display attribute without storing a result array in the View

### TASK-058 - Backend material capability and diagnostic failure
- satisfies: AC-081, AC-082, AC-084
- depends_on: TASK-004, TASK-057
- done_when: native VTK and vtk.js classify every graph requirement exact, explicitly baked or
  unsupported; a missing required dependency makes the whole target diagnostic magenta with CT-010
  detail, while a sparse missing value marks only its own elements and no previous pixels remain

### TASK-059 - Loss-accounted MaterialX USD export
- satisfies: AC-085
- depends_on: TASK-056, TASK-057
- done_when: USD packages the original MaterialX sourceAsset/subIdentifier context, independent SOLVIA
  identity metadata, non-overlapping material subsets, exact-or-approved-baked preview fallback and a
  conversion report that names every unsupported feature

### TASK-060 - Package-bounded MaterialX resolver
- satisfies: AC-086
- depends_on: TASK-056
- done_when: includes and resources cannot escape the package through paths or symlinks, attempt no
  network access offline, enforce the measured limits and preserve but never execute imported source
  implementations

### TASK-061 - Result-to-legend material traceability
- satisfies: AC-087
- depends_on: TASK-057
- done_when: every result input affecting colour names its exact transfer function, visible effects and
  legend output, while a graph whose relationship cannot be validated is retained but refused for
  presentable analysis export

### TASK-062 - Unified Material Slots and dependency repair UI
- satisfies: AC-071, AC-072, AC-073, AC-074, AC-075, AC-076, AC-077
- depends_on: TASK-055, TASK-056, TASK-057, TASK-058
- done_when: the active object's compact slot list drives one graph shown through Basic, Node and Source
  views; the single live viewer below the slot list switches evaluated channels independently from test
  geometry and includes a non-rotating 2D surface; Basic groups published inputs, Node mirrors the
  active graph and expands centrally, Source automatically validates the active revision's file, Basic
  switches Base Color dependent rows among solid colour, image, colour map and restricted formula,
  exposes analysis and coordinate inputs as type-compatible variables rather than modes, keeps only
  variable/range/bar in the compact colour-map view, and opens a dedicated colour/opacity control-point
  editor whose out-of-range output is transparent, without offering node connection,
  omits generic Height and omits Mapping when no coordinate source is required while Node and Source
  retain explicit height-to-normal or displacement networks, and
  one shared save action revalidates before creating a revision; restricted expressions preserve
  unrepresented nodes, live failures become diagnostic
  magenta and no PBR/result kind selector or second graph copy exists
