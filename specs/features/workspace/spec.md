---
status: draft
updated: 2026-08-22
---

# Feature: workspace, cases and variables

## Users and purpose

- intended user: an analysis engineer who runs the same study many times with changed parameters, and
  who cannot write scripts to keep the results organised
- job to be done: keep one investigation - every run, every setting, every figure - in a single place
  that can be reopened months later and still produce the same output
- success condition: reopening a saved @Workspace and exporting again produces the same deliverable,
  and changing one @Variable updates every place that used it without hunting

## Out of scope

- running the solver, now or ever - this product reads results, it does not produce them
- version control of the analysis input files themselves
- multi-user concurrent editing of one @Workspace
- automatic detection of which runs belong together (the user says so)

## Files and interfaces involved

- the @Workspace document format and its schema (CT-001)
- MOD-007 workspace, MOD-001 domain-core
- the case tree and variable panel of [../../11_ui.md](../../11_ui.md)

## Requirements

### REQ-001 - A Workspace holds a nested hierarchy of Cases
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-001: When the user creates a @Case beneath another, the system shall record it as a child at any
    depth and show it nested in the case tree
  - AC-002: When a parent @Case is deleted, the system shall require confirmation naming how many
    descendants will be deleted with it
  - AC-003: If a hierarchy operation would make a @Case its own ancestor, then the system shall refuse
    it and leave the hierarchy unchanged

### REQ-002 - Inheritance is chosen per variable, and an inherited variable is read-only
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-004: When a @Variable value changes on a parent @Case, the system shall change it in every
    descendant that inherits it, in the same operation
  - AC-005: While a @Variable is inherited in a child @Case, the system shall refuse to edit it there
    and shall follow the parent's value; while it is independent, the system shall leave the child
    unchanged when the parent value changes (XC-117)
  - AC-044: When a @Variable is switched from inherited to independent, the system shall take the
    current value as its starting point and shall state that the child no longer follows the parent
  - AC-006: When the user adds a @Variable to a child @Case, the system shall accept it as a child-only
    variable and shall not add it to the parent
  - AC-007: If the user attempts to delete an inherited @Variable from a child @Case, then the system
    shall refuse and shall state that it is defined on the named ancestor
  - AC-008: If a @Variable is referenced but has no value in scope, then the system shall report it as
    unresolved and shall not substitute a value

### REQ-003 - Variables are usable wherever a value is
- priority: MUST
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-009: When the user drops a @Variable onto a numeric input, the system shall bind that input to
    the variable so later changes follow
  - AC-010: If a @Variable is bound to an input whose unit differs from the variable's, then the
    system shall refuse the binding and shall name both units

### REQ-004 - A Workspace reopens to the same state
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-011: When a saved @Workspace is reopened with its input files present, the system shall
    reproduce every @View, @Graph and @Report definition it contained
  - AC-012: If an input file referenced by a @Case is missing or changed, then the system shall open
    the @Workspace, mark that @Case as unresolved, and shall not delete or rewrite anything
  - AC-013: If the @Workspace file cannot be parsed, then the system shall leave the original file
    untouched and shall report what could not be read

### REQ-005 - Cases carry tags for filtering
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-014: When the user filters by a tag, the system shall show only matching @Case and shall state
    how many are hidden
  - AC-015: If a tag rule would hide the currently selected @Case, then the system shall keep the
    selection visible and shall mark it as outside the filter

### REQ-006 - Automatic hierarchy and variable suggestions on import
- priority: COULD
- phase: later
- decidedness: Open
- open: OPEN-005
- acceptance:
  - AC-016: When several result files are imported together, the system shall propose a hierarchy and
    the variables that appear to differ between them, as a proposal the user accepts or rejects
  - AC-017: If the proposal is rejected, then the system shall import the files unchanged and shall
    not re-propose the same grouping

### REQ-007 - One quantity list, with provenance always visible
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-018: When the quantity list is shown, the system shall display each entry's provenance -
    declared, read from data, computed, or from reference material - and its unit or the undeclared
    marker (XC-088, INV-013)
  - AC-019: Where a quantity is computed, the system shall show the expression that produced it
  - AC-020: If a computed quantity cannot be evaluated for a @Case, then the system shall show it as
    unavailable for that case rather than omitting it from the list
  - AC-021: When a value is shown anywhere in the product, the system shall display it to the
    significant digits its stored precision supports (INV-014)

### REQ-008 - One naming rule, everywhere a script or an expression can reach
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-064 (T1), E-067 (T2)
- acceptance:
  - AC-022: When any object is created, the system shall assign it a stable identifier that is never
    reused, and shall store every reference to it by that identifier rather than by its name (XC-103)
  - AC-023: If a creation or rename would give two objects of the same kind the same name, then the
    system shall refuse it and shall name the object already holding it, rather than appending a suffix
  - AC-024: When an object is looked up by name, the system shall return exactly one object or shall
    fail with what it found, and shall never return a list for the caller to choose from
  - AC-025: When an object is renamed, the system shall leave every stored reference to it working

### REQ-009 - Work in progress survives a crash, and a workspace is never edited twice at once
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-026: When the @Workspace changes, the system shall append the change to a journal beside the
    workspace file without rewriting the file itself
  - AC-027: When the product starts after an abnormal exit, the system shall offer the journalled work
    and shall leave the saved file untouched until the user accepts it
  - AC-028: When a @Workspace is already open elsewhere, the system shall open it **read-only** and say
    which process holds it, rather than refusing or opening it twice for editing
  - AC-029: If the lock cannot be taken or released - a lost network share, a killed process - then the
    system shall say what it found and shall offer to open read-only

### REQ-010 - Workspace artefacts are distinct from reusable templates
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-088 (T1)
- acceptance:
  - AC-030: When a @View, @Graph, @Report or simulation definition is created, the system shall store it
    as a concrete item on the @Workspace, not as a @Template and not on any @Case (XC-109)
  - AC-031: When the user edits an item while a @Case is selected, the system shall change that item;
    it shall not change its source template or any sibling item, and switching case shall re-render the
    same item unless the item has an explicit case binding
  - AC-032: When the user chooses `テンプレートとして保存`, the system shall copy the current definition into
    a new @Template revision in the selected workspace or shared scope, leaving the item independently
    editable (GL-019)
  - AC-061: When the user applies a @Template, the system shall show its resolution result and, only
    after acceptance, create a new independently editable workspace item carrying the source template
    identifier and revision; subsequent edits on either side shall not propagate silently
  - AC-062: When multiple @View, @Graph or @Report items exist, the corresponding list shall let the
    user open, create, duplicate, rename and delete them under the Japanese labels `ビュー一覧`,
    `グラフ一覧` and `レポート一覧`, without presenting those items as templates; Simulation remains
    the later-release placeholder specified by XC-091

### REQ-011 - Numbers read by a person follow the locale; numbers read by a machine do not
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-033: When a number is displayed, the system shall format it for the interface language
  - AC-034: When a number is written to a machine-readable output, the system shall use a period
    decimal separator and no digit grouping regardless of locale (INV-018)
  - AC-035: Where a file is meant to be read by both, the system shall state in the file which
    convention it used

### REQ-012 - A reusable template travels: to the shared library, and to a file
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1), E-088 (T1)
- acceptance:
  - AC-036: When a @Template is promoted to the **shared** @Library scope, the system shall make it
    available in every @Workspace on the machine and shall leave the originating workspace able to open
    on its own
  - AC-037: When a template is promoted or exported, the system shall write down what it requires from
    a target - fields, units, variables, parts, dependent entries - and shall report anything that was
    resolvable only inside the originating workspace, without refusing the promotion
  - AC-038: When a template is exported, the system shall produce **one self-contained file** with its
    dependent assets embedded, and shall list by name any asset whose licence forbids embedding rather
    than including it (XC-025)
  - AC-039: When an exported template is imported elsewhere, the system shall place it in the chosen
    scope, record where it came from, and apply it as far as it resolves with the rest listed (XC-090)
  - AC-040: Where a template states its arity, the system shall apply it to one @Case or to a set
    accordingly, and shall refuse a use that contradicts it rather than guessing
  - AC-063: When a template revision changes after workspace items were created from it, the system
    shall leave those items unchanged; any future linked-template feature shall be explicit and is not
    part of r1

### REQ-013 - Tags are proposed on import and confirmed by a person
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-041: When result files are imported, the system shall propose tags from what it can read - the
    solver, the mesh size, which variables differ between siblings - and shall apply none until accepted
    (XC-120)
  - AC-042: Where a language model is configured, the system shall additionally propose tags inferred
    from the case's own naming, marked as inferred
  - AC-043: If a proposal is rejected, then the system shall not offer the same one again in the session

### REQ-014 - A case is in one of six states, and everything branches on them
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-045: When a @Case changes state, the system shall move it only along the transitions of XC-136
    and shall show the state in the case tree
  - AC-046: If an input file becomes missing or changed, then the system shall move the @Case to
    unresolved from whatever state it was in, without discarding its definitions
  - AC-047: When a @Pipeline decides to skip a @Case, the system shall decide from the @Case state
    rather than from a separate check

### REQ-015 - A workspace can be sent, and it says what it could not take
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-001 (T1)
- acceptance:
  - AC-048: When a @Workspace is packed, the system shall include the document, its workspace-scoped
    templates and assets, and the referenced input data if the user asks for it, stating the size before
    writing (XC-140)
  - AC-049: When a pack is created, the system shall name everything it could not include - a linked
    folder, an asset whose licence forbids redistribution
  - AC-050: When a pack without data is opened, the system shall recreate the @Workspace with every
    @Case in the unresolved state rather than appearing to work (XC-136)
  - AC-051: When a quantity is declared, the system shall record whether it is absolute or a difference,
    and shall convert it by the matching rule (INV-028)

### REQ-016 - Output is bounded on purpose, not by accident
- priority: SHOULD
- phase: r1
- decidedness: Bounded
- acceptance:
  - AC-052: When run output passes LIM-012, the system shall report the space in use and offer pruning
    by run, oldest first (XC-141)
  - AC-053: When pruning runs, the system shall name what will be deleted, shall keep the run records,
    and shall never touch input data
  - AC-054: When any time is recorded, the system shall store it in UTC with the local offset beside it,
    and shall display it in the reader's own zone (XC-142)

### REQ-017 - Workspace and Workspace list are distinct shell destinations
- priority: MUST
- phase: r1
- decidedness: Fixed
- basis: E-080 (T1), E-083 (T1), E-084 (T1), E-089 (T1), E-090 (T1), E-091 (T1), E-095 (T1)
- acceptance:
  - AC-055: When the application header is shown, it shall provide `Workspace` and `Workspace list`
    destinations and shall not label the workspace collection as `Case list`
  - AC-056: When the Workspace list is open, it shall provide search, filtering, grid/list controls,
    new-workspace action and workspace cards without presenting invented analysis values
  - AC-057: When a workspace is open, the second toolbar shall place the left-panel toggle at its far
    left and the right-panel toggle at its far right, so either panel can be reopened after closing;
    neither sidebar shall repeat those controls, and the left sidebar shall not show a
    `Workspace`/`Conversation` plus-button title row; the right sidebar shall not show a generic
    mode-name-plus-collection heading above its functional tabs; every non-chat right sidebar shall use
    a vertical icon rail with no horizontal tab scrolling, shall keep only the selected Japanese tab
    name visible in its content header without repeating the work-area name above it, and shall expose
    each icon name on hover, focus and to assistive technology. View shall retain that single rail and
    use a decorative, assistive-technology-hidden and non-focusable separator between its whole-View
    and active-object tab groups (XC-146)
  - AC-058: When the top application menu is shown, it shall expose File, Edit, View, Filter, Tools and
    Help groups over the same command surface used elsewhere (INV-006)
  - AC-059: When the design mockup shows the Workspace list, each card shall reuse its assigned
    `cae-saa-s` reference thumbnail in a 4:3 cover-filled viewport, the browser-default desktop grid
    shall show four equal cards on one row, and the card shall label that artwork as not connected to
    analysis values; the shipping application shall instead use that workspace's derived preview or an
    explicit missing-preview state
  - AC-060: When the selected material-library category is Template, Object, Material, Background or Font
    in View; Template, Style or Font in Graph; or Template, Layout, Style or Font in Report, the shelf
    shall place horizontal `サンプル` and `オリジナル` tabs immediately below its title, then provide one
    primary text search, a compact `タグ` filter trigger and a compact sort button, then show results or
    an icon-labelled empty/no-match state named for that section using the same shared composition;
    opening Tag shall show a filterable
    multi-select list derived only from tags in the selected source and scope, selected tags shall be
    removable chips, sort shall offer only Default and ascending/descending Name orders until another
    sortable field is owned by the relevant library contract, Tag and sort popovers shall be mutually
    exclusive, and Simulation shall not expose the material-library shelf (XC-147); the user-facing tab
    for the internal Font `assetKind` shall be named `テキスト` in every area (XC-183)
  - AC-064: When Simulation, View, Graph or Report is open, its persistent work-area header shall
    identify the current workspace item and show exactly one matching `＋ 新規シミュレーション`,
    `＋ 新規ビュー`, `＋ 新規グラフ` or `＋ 新規レポート` action rather than generic `＋ 新規作成`; it
    shall show neither `テンプレート` nor `テンプレートとして保存`, while the centre-bottom Template
    library category remains available where specified, and r1 Simulation shall continue to state that
    external-solver driving is unavailable rather than claiming creation succeeded (XC-091, XC-148)
  - AC-065: When View, Graph or Report is open, the material library shall sit below the centre canvas
    and above the instruction bar, shall label its top bar only `素材ライブラリ` in collapsed and open
    states, shall keep an up-to-expand or down-to-collapse chevron visibly rendered in a dedicated slot
    immediately after that label rather than at the far edge or beneath another control, shall place
    category tabs in that same row when open, shall put Sample/Original, search, Tag
    and sort together in the next row, shall default to collapsed, shall make the whole collapsed bar
    open it by pointer or keyboard, shall make the whole open bar close it except when a category tab
    or top-edge resize splitter performs its own action, shall expose no separate one-row/multi-row icon,
    shall open to one complete thumbnail row,
    shall support expansion to multiple complete rows without shortening the right property editor, and
    shall overlay the lower canvas above the instruction bar at narrow width; the right rail shall retain
    its functional tabs as current-item/current-selection editors without Sample/Original, search, Tag,
    sort or result browsing, shall name its former Template tab `全体`, and shall keep Template as a
    material-library category; click shall select and preview, drag shall apply to a target, an explicit
    `適用` shall provide a non-drag path, and Chat shall show no material library (XC-149)
  - AC-072: When View current state is shown, its right property rail shall name instantiated display
    entities `Objects`; when the material library, scope, revision, import or export is shown, the shell
    shall reserve `Asset` for reusable resources and shall name the reusable View category `Object`
    (XC-166)
  - AC-067: When Graph or Report shows its vertical property rail, it shall include an `出力` section
    using the shared File Output icon as the final visual, DOM and keyboard tab, shall use the same spacing
    as the preceding tab without physical-bottom anchoring, and shall keep the selected Japanese name,
    tooltip and tab semantics used by every other rail section; Graph shall describe image, vector and
    tabular-data output conditions, while Report shall describe document format and delivery conditions
    (XC-152)
  - AC-066: When a visible left or right sidebar is resized from its complete inner-boundary splitter,
    pointer horizontal movement and Left/Right arrow keys shall change only that sidebar's width within
    bounds that retain a usable centre surface; when an open material library is resized from its
    complete top-boundary splitter, pointer vertical movement and Up/Down arrow keys shall change its
    height while its width remains docked to and follows the centre column; each splitter shall expose
    separator role, orientation, controlled panel, current value and bounds, shall show no corner
    decoration, and shall accent its otherwise quiet boundary only during hover, focus or drag; shelf
    pointer resizing shall use its rendered pointer-down height as the baseline and follow pointer
    displacement without a height transition or a jump to stored expanded height, shall derive its
    maximum from current centre-column height after reserving the other persistent bars, and shall not
    increase application viewport height or cause application-level vertical scrolling; a
    collapsed or hidden panel shall expose no splitter, and resizing shall change workspace UI state
    without changing analysis or item definitions (XC-149)

  - AC-073: When the persistent top work-area tabs or a material-library category-tab group is shown,
    every tab within that group shall have the same width and shall retain that width when selection
    changes; the top group and each library group may use different widths, the top group shall switch
    to equal-width icon tabs when its labels do not fit, and a library group that does not fit shall
    preserve equal readable tab widths and scroll horizontally rather than assigning widths from each
    label or silently truncating labels (XC-168)
  - AC-074: When any Simulation, Automation, View, Graph, Report, Settings or Network right-rail tab is
    selected, the system shall show controls specific to that tab's responsibility rather than a shared
    placeholder form; dependent controls shall appear only for their active mode, unresolved or
    unsupported capabilities shall state that condition, and output tabs shall distinguish their
    supported image, video, vector, tabular or document conditions as applicable (XC-182)

### REQ-018 - A workspace owns multiple saved Simulation flows
- priority: MUST
- phase: later
- decidedness: Fixed
- basis: E-080 (T1)
- acceptance:
  - AC-068: When Simulation is available, a @Workspace shall own zero or more independently identified,
    named, revisioned and explicitly ordered @Simulation items and `シミュレーション一覧` shall let the
    user create, open, duplicate, rename, reorder and delete them without presenting them as @Case or
    @Pipeline entries (XC-154)
  - AC-069: When a valid @Simulation is saved, its definition shall contain the explicit conditions for
    one or more external-solver executions in declared order; an empty or unresolved flow may remain a
    draft but shall be refused at execution rather than treated as a successful no-op
  - AC-070: When the @Workspace is saved, closed and reopened, every Simulation identifier, name,
    revision, order, solver adapter, input reference and parameter binding shall round-trip without
    inventing a result, execution or value
  - AC-071: When a @Pipeline invokes a Simulation, its unit shall pin the Simulation identifier and
    revision and shall add only successfully produced result Cases to its target set; later Simulation
    edits shall not silently change that pinned unit

## End-to-end verification

Create a @Workspace with a parent @Case and two children; create two named Views and switch between
them through `ビュー一覧`; declare a @Variable on the parent and bind it in one View on both children;
override it on one child; change the parent value and confirm the inheriting child changed while the
overriding child did not. Save that View as a workspace template, create a third View from it, then edit
the template and confirm all three Views remain unchanged. Save, close, reopen, and export from both
children - the workspace-item identities, source-template provenance and exported deliverables are
identical to the ones before saving. For the later Simulation feature, create two saved flows with one
and three execution conditions, save and reopen, and confirm their identities, revisions, ordering and
conditions survive independently; pin the first revision in a Pipeline, edit the Simulation, and confirm
the Pipeline still resolves the pinned revision until explicitly updated.
