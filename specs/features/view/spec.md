---
status: draft
updated: 2026-08-22
---

# Feature: view

## Users and purpose

- intended user: an analysis engineer who can read a result but cannot write a visualisation pipeline,
  and who needs the picture to be presentable rather than merely correct
- job to be done: make the result look the way it will look in the document, without assembling a
  scene by hand each time
- success condition: a saved @View reproduces exactly, applies to the next @Case, and produces an
  image whose numbers match what the interface reported

## Out of scope

- editing geometry or moving nodes
- computing new physical results - a @View displays, it never solves
- executing imported MaterialX source-code implementations; Basic, Node and Source authoring edit only
  declarative MaterialX content and bounded SOLVIA expressions
- photorealistic rendering as a requirement - it is an optional path (XC-037)

## Files and interfaces involved

- MOD-003 visualization, MOD-002 dataset-io
- CT-004 view definition, CT-008 library entry, CT-010 failure report, CT-011 Material Asset definition
- the right sidebar of [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - A view is a saved definition, reproducible and multiple per case
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-001: When the user saves a @View, the system shall store it as a definition referencing fields
    and assets by identifier, with no values or images inside it
  - AC-002: When a saved @View is reopened with the same inputs, the system shall reproduce the same
    picture and the same reported numbers
  - AC-003: While a @Case is selected, the system shall allow more than one @View on it and show which
    one is active
  - AC-004: If a @View references a field the @Case does not have, then the system shall show the view
    without that element and list it as unresolved rather than substituting another field

### REQ-002 - Renderer choice changes the picture, never the numbers
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-063 (T1)
- acceptance:
  - AC-005: When the user switches between the light and photorealistic paths, the system shall report
    identical values for the same @View
  - AC-006: If the selected renderer cannot run on this machine, then the system shall name it, say
    what it requires, and offer one that runs (XC-004)
  - AC-007: While a @Dataset exceeds LIM-002, the system shall render a reduced representation, mark
    the view as reduced, and keep reported numbers computed on the full data
  - AC-089: When View rendering properties are shown, lighting shall remain one conditional `照明`
    group inside `描画`, while `背景` shall own only the visible background and its environment Asset,
    rotation, display strength and camera visibility. Selecting `背景の環境` as the light source shall
    reference that one Asset and rotation without duplicating them; background visibility and display
    strength shall remain independent from lighting strength, and no separate Lighting tab shall appear

### REQ-003 - Engineering presentation styles
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-008: When the user selects a drawing presentation, the system shall offer the orthographic
    three-view arrangement and a dimensioned drawing style alongside the shaded 3D view
  - AC-009: When a dimension is placed, the system shall label it with the value in the declared unit,
    or with the undeclared marker if none is declared (XC-003)
  - AC-010: If a dimension is placed on display geometry that has been reduced, then the system shall
    measure the full @Dataset rather than the reduction (INV-001)

### REQ-004 - Backgrounds, materials and assets come from a library
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-011: When the user applies a material, colour map, font or background, the system shall take it
    from the library with its scope shown - sample, workspace or shared (GL-019)
  - AC-012: When an asset is imported, the system shall record where it came from and its stated
    licence, and shall refuse to embed it in an export whose terms it cannot satisfy (XC-025)
  - AC-013: If a referenced Asset is missing, then the system shall name it and shall use only that
    Asset revision's explicit fallback. A missing Material Asset or required material resource shall
    draw its affected target diagnostic magenta; no plausible default material shall replace it

### REQ-005 - A view travels to another case and to another workspace
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-014: When a @View is saved as a @Template, the system shall allow using it to create an
    independent View in another @Workspace
  - AC-015: When a @Template is selected, the system shall show what would resolve and what would not
    before creating or drawing the new View (XC-090, XC-109)
  - AC-016: If nothing in a @Template resolves against the target, then the system shall refuse the
    application and say so, rather than producing an empty view that looks like a result

### REQ-006 - Time series are navigable
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-017: While a @Case has more than one time step, the system shall offer playback and a time
    position, and shall state which step is displayed
  - AC-018: If a field is absent at the displayed step, then the system shall draw it as missing rather
    than carrying the previous step forward

### REQ-007 - Images and video are output from the definition
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-019: When an image is exported, the system shall produce it from the saved @View so that the
    same definition yields the same image
  - AC-020: Where a camera path is selected, the system shall produce a video following it, and shall
    state the time mapping used for a time-varying @Case
  - AC-021: If a video cannot be encoded on this machine, then the system shall say which encoder was
    missing and shall still produce the frames

### REQ-008 - Transfer to an external tool preserves what it can
- priority: SHOULD
- phase: later
- decidedness: Fixed
- basis: E-040 (T1)
- acceptance:
  - AC-022: When the user exports a @View for external work, the system shall write USD stating
    `metersPerUnit` and `upAxis` explicitly (XC-048)
  - AC-023: If an element of the @View cannot be represented in USD, then the system shall name it
    before writing rather than omitting it silently

### REQ-009 - Views are compared side by side, with camera synchronisation stated
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-024: When the view area is split, the system shall show up to four panes, each rendering a
    @View against a @Case the user chose for that pane
  - AC-025: While camera synchronisation is on, the system shall apply a camera change in one pane to
    every pane, and shall record the synchronisation state on any image exported from the split
  - AC-026: If two panes use different colour-map ranges, then the system shall mark the panes as not
    directly comparable and shall offer to make the ranges common
  - AC-057: When the design mockup opens any populated one- to four-pane View state, then each pane
    shall contain an interactive Three.js placeholder with orbit, zoom, fit, auto-rotation,
    representation controls, grid and orientation gizmo; it shall state that no analysis data is
    connected inside the viewport, shall not present invented values, units, metadata or provenance,
    and shall fill the centre display region without a decorative outer border, generic wrapper
    padding or separate status footer around the Canvas; the XYZ orientation gizmo shall be
    right-aligned directly below the upper-right representation controls in every split size, with a
    visible gap, without clipping any axis head, and with visually prominent axis-head circles and
    legible X, Y and Z labels at browser-default zoom (XC-145)

### REQ-010 - A point can be probed, and what comes back is a real value
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-027: When the user probes a point, the system shall report the value at that point from the
    canonical data, with its unit, its significant digits and its @Provenance (INV-001, INV-014)
  - AC-028: When a probed point falls on cell data, the system shall report the cell's value and say so,
    and shall not interpolate it to a point value (INV-003)
  - AC-029: If a probed point has no value - outside the mesh, or a missing entry - then the system
    shall report it as missing rather than as zero (INV-011)
  - AC-030: Where a probed value is kept, the system shall make it a @Variable carrying the case, the
    position and the time it was taken at

### REQ-011 - The displayed time step is a variable
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-031: When a @Case has several time steps, the system shall hold the displayed one as the @Current time step, bindable like any @Variable and iterable by a @Pipeline loop
  - AC-032: When a value is shown or exported, the system shall state which time step it came from
  - AC-033: If a @Case lacks the requested time step, then the system shall report it and shall not
    substitute the nearest one

### REQ-012 - Dataset components are first-class in the Outliner
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1), E-079 (T1), E-080 (T1)
- acceptance:
  - AC-034: When a @Dataset carries named components and parent-child relations, the View area's
    @Outliner shall list them at the top of the right sidebar as a tree, with a disclosure control for
    parents, a type icon and the exact source-file name on every row; the exact dataset root shall be
    the first tree row and no static `Dataset` button shall appear in the header; at browser-default
    zoom the design mockup shall render names at 10 px in 27 px rows, separate its light-neutral header,
    tools and tree surfaces, mark selection with both a pale-blue surface and a left accent, and omit a
    persistent `Shift`/`Ctrl` shortcut footer (INV-019, XC-143, XC-144)
  - AC-035: When a @Summary statistic is shown, the system shall state whether its scope was one @Part
    or the whole model
  - AC-055: When an Outliner row is selected or its visibility control is changed, the active viewport
    shall reflect the same component selection or visibility; `Shift` shall apply visibility through
    descendants and `Ctrl` shall isolate the branch
  - AC-056: If the source supplies no hierarchy, no names, no loaded dataset, or only a partial
    structure, then the Outliner shall respectively show siblings, explicit unnamed markers, an empty
    state, or only confirmed nodes with the read failure; it shall not infer a plausible tree

### REQ-013 - Whichever backgrounds ship, they are appearance and they are budgeted
- priority: MUST
- phase: r1
- decidedness: Open
- open: OPEN-016
- acceptance:
  - AC-036: When a background of any kind is applied, the system shall treat it as appearance and shall
    produce identical reported values with and without it (INV-002)
  - AC-037: When an imported 3D model is placed as a prop, or a splat scene is added, the system shall
    state the cost against LIM-009 before applying it
  - AC-038: If background content would exceed LIM-009, then the system shall refuse to apply it
    silently and shall never reduce the result geometry to make room

### REQ-014 - Two-dimensional and three-dimensional presentation of one case
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-039: When a two-dimensional presentation is chosen, the system shall offer orthographic views
    including a three-view arrangement, sharing the same @View definition as the 3D presentation
  - AC-040: Where a dimension line or annotation is placed, the system shall compute its value from the
    canonical data and shall show it with unit and significant digits (INV-001, INV-014)

### REQ-015 - Video output states its camera path and its time mapping
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-041: When a video is produced, the system shall use a named camera path from the library and
    shall state the path and the playback speed used
  - AC-042: Where the @Case has a time axis, the system shall state how wall-clock seconds map to
    simulated time, and shall keep that mapping in any report using the video

### REQ-016 - Derived quantities come from the catalogue, in a named frame
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-073 (T1)
- acceptance:
  - AC-043: When a @Derived quantity is requested, the system shall compute it from the catalogue of
    15_derived_quantities.md and shall record the formula and any convention it used (INV-020)
  - AC-044: When principal values are shown, the system shall order them largest to smallest and shall
    state that ordering wherever they appear (E-073)
  - AC-045: When a component is reported, the system shall name its @Component frame, defaulting to
    global Cartesian (INV-021)
  - AC-046: If a component is requested in a frame that cannot be resolved, then the system shall refuse
    it and shall name what is missing
  - AC-047: If cell values are converted to point values, then the system shall not average across a
    @Part or material boundary and shall label the result as averaged (INV-022)

### REQ-017 - Deformation is drawn at true scale, and the factor is in the picture
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-077 (T2)
- acceptance:
  - AC-048: When a deformed shape is drawn, the system shall use a @Deformation scale of 1.0 unless the
    user changes it, and shall offer auto-scaling as one action (XC-132)
  - AC-049: When a scale other than 1.0 is in use, the system shall draw the factor into the view and
    into every exported image, video and report block, not only into a toolbar (INV-024)
  - AC-050: When a probe, dimension line or reported value is produced, the system shall compute it from
    undeformed canonical coordinates, and shall label any value the user asked for on the deformed
    configuration

### REQ-018 - A seeded, integrated picture records how it was made
- priority: SHOULD
- phase: r1
- decidedness: Fixed
- basis: E-078 (T1)
- acceptance:
  - AC-051: When streamlines or particle traces are produced, the system shall record the seed source,
    integrator, step size, step limit and termination criteria in the @View definition, and shall
    regenerate identical geometry from it (INV-025)
  - AC-052: When such a picture appears beside measured quantities, the system shall label it a derived
    visualisation

### REQ-019 - Values are shown in the unit the reader works in
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-053: When a @Display unit is chosen for a quantity, the system shall show that quantity in it
    everywhere, beside the value, while storage and computation stay canonical (INV-026)
  - AC-054: If a quantity has no @Declared unit, then the system shall refuse to apply a display unit to
    it and shall keep the undeclared marker (XC-003)

### REQ-020 - View objects and reusable assets have separate identities
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1), E-095 (T1)
- acceptance:
  - AC-058: When a mesh, scalar field, vector field, trajectory, point cloud, annotation or effect is
    instantiated, selected or edited in a @View, the system shall call it a View object, give it identity
    within that View, and keep it separate from the source @Dataset and reusable @Asset (XC-159, XC-166)
  - AC-059: When an Object asset is applied, the system shall preview resolution and create a new,
    independently editable View object carrying the source Asset identifier and immutable revision as
    provenance; later edits or deletion of that Asset shall not silently alter or invalidate the Object
  - AC-060: When the View's current state is edited, the right sidebar and Outliner shall use `Object`
    and `選択中のオブジェクト`; when reusable resources are browsed, the library shall use its `Object`
    category while retaining `Asset` for scope, revision, import, export and reusable-resource lifecycle

### REQ-021 - Texture mapping preserves reference UV and derives analysis UV only when required
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-096 (T1), E-097 (T1), E-098 (T1)
- acceptance:
  - AC-061: When a reference Mesh View object supplies one or more authored UV sets, the system shall
    preserve each set's name, coordinate values, indexing and interpolation and shall use the selected
    set without overwriting it with generated coordinates
  - AC-062: When an analysis Mesh is drawn with uniform appearance, PBR parameters or field-driven
    `ColorBinding` that consumes no two-dimensional texture coordinate, the system shall generate no UV
    data and shall produce the same reported values with or without that appearance (INV-002)
  - AC-063: When a Material Asset declares object-space triplanar or an explicit projection mapping,
    the rendering backend shall use that declared mode, scale stored in canonical metres and rotation
    without adding an atlas to the source @Dataset
  - AC-064: When a Material Asset requires unique two-dimensional UVs and the selected Mesh has no
    authored set, the rendering backend shall lazily generate a deterministic charted atlas on the
    display surface, record the generator name, version and parameters in CT-004, key its cache by the
    display-topology identity, and keep the coordinates and any seam vertices out of canonical data
  - AC-065: When texture mapping is inspected for a selected View object, the Materials properties
    shall show the resolved mode, scale, rotation and authored, generated, pending, degraded or
    unsupported status, shall expose an authored UV-set selector only for `authoredUv` and an XY, XZ
    or YZ projection-plane selector only for `planar`, and shall not expose a UV-coordinate editor or
    repeat coordinate/projection selection inside a published Surface input
  - AC-066: If the declared mapping cannot be generated or rendered, then the system shall name the
    failed mode and reason, shall use only a fallback explicitly declared by the Material Asset, and
    otherwise shall leave the texture unapplied rather than silently choosing another projection

### REQ-022 - Object properties follow the selected View object type
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-100 (T1), E-101 (T1), E-102 (T1), E-104 (T1), E-001 (T1)
- acceptance:
  - AC-067: When an analysis Mesh, reference Mesh, Scalar field, Vector field, Trajectory, Point cloud,
    Annotation or Effect View object is selected, the right sidebar's Object section shall name that
    exact object and type and shall show only the source, representation, visibility and type-specific
    controls that can change that object without editing the source @Dataset. Mesh shall use one
    `表示形式` selector for Surface, Surface plus Edges or Wireframe and shall not duplicate it with an
    Edge checkbox. Object shall store one `表示不透明度` multiplier per object; an edge-bearing mode
    shall reveal one per-object Edge group for colour, output-pixel width and opacity, while Surface
    shall hide it. CT-004 shall store these separately from Material Bindings (XC-159, XC-171, XC-180)
  - AC-068: When selection changes in the viewport or @Outliner, the Object, Materials and contextual Text sections
    shall follow the same active View object without retaining fields or appearance from the previous
    active object; if several objects are selected, the most recently selected or reselected object
    shall be active and the others shall remain selected without producing an aggregate property form.
    The View property rail shall group whole-View `全体`, `描画`, `背景` and `出力` first, then place one
    decorative, assistive-technology-hidden and non-focusable separator before the active-object `オブジェクト`, conditional `テキスト` and
    `マテリアル` tabs. Keyboard navigation shall cross the separator as one continuous tab sequence,
    and accessible names shall state which of the two scopes each View tab edits
  - AC-069: If a property is unsupported, unresolved or inapplicable to the selected object type, then
    the sidebar shall omit it or name its state and reason and shall not enable it with a plausible default.
    The View property rail shall name the object-specific typography section `テキスト`, shall show it
    only for an active `テキスト・注釈` object, and shall omit the entire tab rather than show an empty
    state for every other object type. That Text section shall own content and typography while Object
    retains kind, anchor and provenance; text generated from a dimension or point label shall not make
    its canonical measured value or unit editable

### REQ-023 - One material-slot model supports data-independent and data-dependent graphs
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-100 (T1), E-102 (T1), E-104 (T1), E-105 (T1), E-106 (T1), E-108 (T1), E-111 (T1), E-117 (T1), E-001 (T1)
- acceptance:
  - AC-070: When material state is stored for a View object, CT-004 shall allow zero or more Material
    Bindings by immutable Asset identifier and revision, each targeted to the whole object, a part or an
    element set; it shall reject overlapping subset targets and shall resolve one root MaterialX
    material per surface element (XC-176)
  - AC-071: When Materials properties or the material library list an Asset, the UI shall use one
    Material Asset and Material Slot model and shall derive `解析データ依存`, resource and unresolved
    badges from CT-011 requirements rather than showing or storing PBR, analysis or composite kinds
  - AC-072: When the active Material declares a required `solviaResult` input, the Materials properties
    shall show that input's expected type, association and unit dimension and its current field,
    component, result-position and declared-unit binding; a data-independent graph shall not show an
    empty analysis form and no form shall ask the user to select a material type
  - AC-073: When Materials or contextual Text properties are shown, they shall edit the active View object from the
    shared viewport and @Outliner selection and shall not provide a second target-selection state or a
    redundant recipient-object block; applying a Material Asset without an active compatible object
    shall leave Material Bindings unchanged and name the incompatibility
  - AC-074: When Material properties show the material viewer, it shall render a neutral
    sphere by default and allow cube, plane, cylinder and `2D面` test geometry. The 3D choices shall
    support orbiting, while `2D面` shall remain front-facing and shall not rotate. Object properties shall
    not show or reserve space for that viewer. Materials shall place its Slot list above the viewer and
    its editing tabs below in one vertical property scroll. Its test-geometry controls shall be accessible icon buttons in
    a vertical right-edge rail. An independently selected vertical left-edge rail shall switch between
    the combined material and its evaluated PBR or graph-declared result outputs. The Materials property
    tab, material library category and combined-material output shall use one shaded sphere icon, while
    Base Color shall retain its distinct palette icon. A
    data-dependent library preview may use only the versioned synthetic fixture and shall say
    `サンプルデータ`; a live preview shall use the selected object's real bindings and shall become
    diagnostic magenta when they do not resolve (XC-177)
  - AC-075: If Material application is cancelled or its root terminal is structurally incompatible with
    the selected target, then the prior bindings shall remain unchanged and the reason shall be named.
    If the user accepts a structurally compatible Asset whose required data is unresolved, then the
    system shall create a repairable failed binding, show its missing inputs and draw its target
    diagnostic magenta rather than retaining the prior successful pixels (XC-175)
  - AC-076: When any Material Asset is offered in the library, the UI shall use that revision's square
    transparent-background rendered thumbnail and shall keep name, source, revision, sample-data state
    and resolution state as text outside the image. The selected object's Material Slot list shall show
    compact material-name rows without thumbnails because the live viewer below it renders the active
    slot; adjacent add and remove controls shall allow zero or more slots. If a library thumbnail is
    unavailable, the UI shall name that state and shall not borrow another Asset's sphere or a plausible
    generic material
  - AC-077: When Materials properties are shown, they shall list and switch among targeted Material Slots
    and make the selected row active in three synchronised views named `基本`, `ノード` and `ソース`.
    Basic shall edit published graph inputs by constant, texture, colour map or restricted expression
    without discarding unrepresented nodes. A Base Color input-source selector shall offer `単色`,
    `画像`, `カラーマップ` and `数式`, shall not offer `RGB`, `解析結果` or `ノード接続`, and shall
    replace its dependent rows in place for the selected source. Analysis results and coordinates shall
    be selectable as typed variables within every mode whose input type they satisfy rather than as a
    material or source kind. When `カラーマップ` is selected, Materials properties shall show its
    variable selector and one compact row containing editable minimum and maximum values at the sides of
    a horizontal colour-map button, and no other transfer-function detail. Adjusting the bounds shall
    make values outside `[minimum, maximum]` transparent rather than clamping them. Activating the bar
    shall open a dedicated editor with independent opacity control points above colour control points;
    it shall support selecting, adding, moving and removing interior points, exact position/colour/opacity
    editing, interpolation and presets while retaining the domain endpoints. A minimum greater than or
    equal to its maximum shall be refused. No other Basic source selector shall offer `ノード接続`.
    Existing arbitrary graph connections shall remain intact
    and be editable in Node or Source. Node shall expose
    type-compatible connections and open its full editor in the central work area; Source shall directly
    edit declarative MaterialX XML and name the active revision's source file. Loading and editing shall
    validate automatically; the shared save action shall validate again, refuse an invalid document and
    create a new immutable revision, so Source shall not add a separate manual validation button. Basic
    shall name the active shader model without a single-option picker, group published Surface and
    type-compatible variables in the dependent Base Color rows, expose OpenPBR `Opacity` through its
    float `geometry_opacity` input without treating Object display opacity as a material value, omit a
    generic Height input, and show the per-binding Mapping group only when
    the active Asset requires texture coordinates or declares a coordinate source other than `none`.
    Basic shall keep coordinate-source and projection controls in that one Mapping group rather than
    repeating a coordinate selector under Base Color or another published Surface input. Node shall show only nodes in the
    active graph and shall retain explicit height-to-normal or displacement networks that Basic does not
    represent. Those views shall
    not repeat the live viewer or add a separate output-preview canvas. They shall not produce three graph copies,
    show separate `サーフェス` and `結果カラー` cards, or offer a PBR/analysis/composite type selector
    (XC-174, XC-177)

### REQ-024 - MaterialX graphs preserve and programmatically bind material meaning
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-108 (T1), E-109 (T1), E-110 (T1), E-111 (T1), E-112 (T1), E-113 (T1), E-114 (T1), E-001 (T1)
- acceptance:
  - AC-078: When a `material` Library entry is saved, it shall validate against CT-011 and identify one
    qualified root MaterialX element without an appearance/analysis/composite kind; graph values and
    connections shall exist only in MaterialX, not as a second JSON parameter copy (XC-174)
  - AC-079: When a MaterialX graph declares one or more `solviaResult` inputs, each Material Instance
    shall bind field identifier, component, point/cell association, result position and declared unit,
    and MOD-003 shall lower those bindings to validity-bearing VTK/GPU attributes or USD primvars read
    by standard geometry-property nodes without allowing shader code to open storage or a network
  - AC-080: When a SOLVIA MaterialX document is loaded, its `solvia_asset_id`, revision, contract,
    contract version and logical manifest URI shall match CT-008/CT-011 in both directions; if they do
    not, then the originals shall be preserved, left unlinked and reported unresolved
  - AC-081: If any required result, component, association, result position, unit dimension, resource,
    hash, MaterialX node or backend feature is unavailable, then the whole affected target shall render
    diagnostic magenta, its ordinary legend shall be suppressed, CT-010 shall name every cause and no
    zero, previous value, previous pixels or undeclared fallback shall be used (XC-175)
  - AC-082: If a resolved result contains missing values for only some elements, then an explicit
    validity attribute shall mark only those elements with the missing-data diagnostic while all valid
    elements retain their declared material result
  - AC-083: When MaterialX source is imported or generated, the system shall retain and hash its exact
    source bytes and every dependency, validate the parsed graph with the pinned official API, preserve
    unknown content and execute no imported source-code implementation; an upgrade shall create a new
    immutable Asset revision and retain original provenance
  - AC-084: When a Material is resolved for native VTK or vtk.js, a versioned backend manifest shall
    classify every required feature `exact`, `baked` or `unsupported`; baking shall require explicit
    approval and shall record graph hash, tool/version, resolution, colour space and approximation
  - AC-085: When a Material is exported to USD, the writer shall package original MaterialX through an
    `mtlx` render context using `sourceAsset` plus `subIdentifier`, independently write SOLVIA identity
    metadata, use non-overlapping material-bind subsets and create a universal UsdPreviewSurface only
    from exact or explicitly baked channels; it shall report every unsupported feature
  - AC-086: When MaterialX includes or resource URIs are resolved, the resolver shall remain inside the
    package, reject traversal and symlink escape, make no network request offline and enforce measured
    depth/count/byte/image limits; unknown or external executable implementations shall be preserved but
    not run
  - AC-087: When a result input affects displayed colour, CT-011 shall identify its visible effects,
    exact transfer-function element and legend output. If the graph cannot prove that relationship,
    then it may be retained as unverified appearance but shall not produce a presentable analysis image,
    video, USD or Report
  - AC-088: When any rendering Material Asset is applied, then no density, elastic modulus, Poisson
    ratio, yield strength, temperature dependence or other engineering property shall be inferred or
    changed, even if the Asset is named after an engineering material (INV-029, XC-179)

## End-to-end verification

Load a case, colour it by a field with a declared unit, place a dimension, apply a material and an
HDRI background from the sample library, instantiate an Object asset, save the view, save it as a template, and create a new View
from it in a different workspace whose field names differ. Confirm the unresolved list names exactly
the missing references, that editing the source Object asset does not alter the instantiated Object,
and that editing the template does not alter either existing View. Export an
image and confirm the reported maximum equals the value the interface showed.
