---
status: draft
updated: 2026-08-22
---

# Tasks: workspace, cases and variables

### TASK-001 - Document schema and round trip
- satisfies: AC-011
- depends_on: none
- done_when: a @Workspace saves and reopens with every definition intact, and the schema file matches
  the prose version (CT-001)

### TASK-002 - Unknown fields preserved
- satisfies: AC-011
- depends_on: TASK-001
- done_when: a document containing fields this build does not understand keeps them through a load and
  save cycle, asserted by test

### TASK-003 - Damaged files never overwritten
- satisfies: AC-013
- depends_on: TASK-001
- done_when: opening a truncated document reports what could not be read and leaves the file
  byte-identical on disk

### TASK-004 - Previous good version kept on save
- satisfies: AC-013
- depends_on: TASK-003
- done_when: a save keeps the previous version beside the new one until the new one is written
  completely (XC-055)

### TASK-005 - Nested case hierarchy
- satisfies: AC-001
- depends_on: TASK-001
- done_when: a @Case can be created beneath another at any depth and reopens at that depth

### TASK-006 - Cycle and deletion guards
- satisfies: AC-003
- depends_on: TASK-005
- done_when: an operation making a @Case its own ancestor is refused with the hierarchy unchanged, and
  deleting a parent requires confirmation naming the descendant count (AC-002)

### TASK-007 - Variable declaration and resolution
- satisfies: AC-004
- depends_on: TASK-005
- done_when: a @Variable is declared once and resolved through the hierarchy on load, never copied
  into children (INV-004)

### TASK-008 - Override and inheritance state
- satisfies: AC-005
- depends_on: TASK-007
- done_when: changing a parent value changes every inheriting descendant in one operation and leaves
  overriding descendants untouched, with the state visible per variable

### TASK-009 - Child-only variables
- satisfies: AC-006
- depends_on: TASK-007
- done_when: a variable added to a child does not appear on the parent, and deleting an inherited
  variable from a child is refused naming the ancestor that defines it (AC-007)

### TASK-010 - Unresolved variables are reported
- satisfies: AC-008
- depends_on: TASK-007
- done_when: a referenced variable with no value in scope reports as unresolved and no value is
  substituted

### TASK-011 - Variable binding into inputs
- satisfies: AC-009
- depends_on: TASK-007
- done_when: dropping a @Variable onto a numeric input binds it, and later changes reach the input

### TASK-012 - Unit mismatch refused at binding
- satisfies: AC-010
- depends_on: TASK-011
- done_when: binding a variable whose unit differs from the input's is refused naming both units

### TASK-013 - Missing and changed input files
- satisfies: AC-012
- depends_on: TASK-001
- done_when: a @Case whose source file is missing or modified opens as unresolved, and nothing is
  deleted or rewritten

### TASK-014 - Tags and filtering
- satisfies: AC-014
- depends_on: TASK-005
- done_when: filtering by tag shows matching cases and states how many are hidden, and the selected
  case stays visible marked as outside the filter (AC-015)

### TASK-015 - Import grouping proposal
- satisfies: AC-016
- depends_on: TASK-005, ingest/TASK-007
- done_when: importing several files proposes a hierarchy from a deterministic signal, names the signal
  it used, and applies nothing until accepted (XC-081)

### TASK-016 - Rejected proposals are not repeated
- satisfies: AC-017
- depends_on: TASK-015
- done_when: a rejected grouping is not proposed again in the same session

### TASK-017 - One quantity list with provenance
- satisfies: AC-018
- depends_on: TASK-005
- done_when: declared, read, computed and reference-material quantities appear in one list, each with
  its provenance and its unit or the undeclared marker

### TASK-018 - Computed quantities show their expression
- satisfies: AC-019
- depends_on: TASK-017
- done_when: a computed entry displays the expression that produced it

### TASK-019 - Unavailable rather than absent
- satisfies: AC-020
- depends_on: TASK-018
- done_when: a quantity that cannot be evaluated for a case is shown as unavailable for that case

### TASK-020 - Significant digits from stored precision
- satisfies: AC-021
- depends_on: TASK-017
- done_when: a value's displayed digits are derived from its stored precision, in one shared component,
  asserted for both single and double precision fields (INV-014)

### TASK-021 - Stable identifiers, references by identifier
- satisfies: AC-022
- depends_on: TASK-001
- done_when: every object carries an identifier that is never reused, and no stored reference contains
  a name

### TASK-022 - Duplicate names refused
- satisfies: AC-023
- depends_on: TASK-021
- done_when: a colliding create or rename is refused with the holder named, for every kind

### TASK-023 - Lookup returns one or fails
- satisfies: AC-024
- depends_on: TASK-022
- done_when: name lookup never returns a collection, and a miss reports what was searched

### TASK-024 - Rename keeps references working
- satisfies: AC-025
- depends_on: TASK-021
- done_when: renaming an object leaves views, pipelines and expressions resolving to it

### TASK-025 - Change journal
- satisfies: AC-026
- depends_on: TASK-001
- done_when: every change is appended beside the file, which is itself untouched

### TASK-026 - Recovery on start
- satisfies: AC-027
- depends_on: TASK-025
- done_when: journalled work is offered after an abnormal exit and applied only on acceptance

### TASK-027 - Workspace lock
- satisfies: AC-028
- depends_on: TASK-001
- done_when: a second open is read-only and names the holding process

### TASK-028 - Stale locks
- satisfies: AC-029
- depends_on: TASK-027
- done_when: an unreadable or orphaned lock is reported and read-only is offered

### TASK-029 - Workspace items and templates stored separately
- satisfies: AC-030
- depends_on: TASK-001
- done_when: concrete definitions are written to `workspaceItems`, reusable workspace templates to the
  library envelope, and neither is written onto a case

### TASK-030 - Editing changes only the workspace item
- satisfies: AC-031
- depends_on: TASK-029
- done_when: an edit made while one case is selected changes the open item and no source template or
  sibling item; switching case reuses that item unless it has an explicit binding

### TASK-031 - Save as template
- satisfies: AC-032
- depends_on: TASK-029
- done_when: View, Graph and Report can snapshot the current item as a new template revision in a
  chosen scope without establishing a live link

### TASK-032 - Locale-aware display
- satisfies: AC-033
- depends_on: TASK-001
- done_when: displayed numbers follow the interface language

### TASK-033 - Locale-independent output
- satisfies: AC-034
- depends_on: TASK-032
- done_when: machine-readable output is byte-identical across locales

### TASK-034 - Stated convention in dual-purpose files
- satisfies: AC-035
- depends_on: TASK-033
- done_when: a CSV carries the numeric convention it used

### TASK-035 - Promotion to the shared library
- satisfies: AC-036
- depends_on: TASK-029
- done_when: a promoted template is visible in every workspace and the origin still opens alone

### TASK-036 - Requirements written down on promotion
- satisfies: AC-037
- depends_on: TASK-035
- done_when: field, unit, variable, part and entry references are collected and reported

### TASK-037 - Self-contained export
- satisfies: AC-038
- depends_on: TASK-036
- done_when: one file carries the definition and embeddable assets; the rest are listed by name

### TASK-038 - Import
- satisfies: AC-039
- depends_on: TASK-037
- done_when: an imported template lands in the chosen scope with its origin and unresolved list

### TASK-039 - Arity enforced
- satisfies: AC-040
- depends_on: TASK-029
- done_when: a contradicting use is refused with the arity named

### TASK-040 - Tag proposals from readable signals
- satisfies: AC-041
- depends_on: ingest/TASK-001
- done_when: proposals come from solver, mesh size and differing variables, applied only on acceptance

### TASK-041 - Model-inferred tags
- satisfies: AC-042
- depends_on: TASK-040
- done_when: name-inferred proposals appear marked as inferred

### TASK-042 - Rejected proposals stay rejected
- satisfies: AC-043
- depends_on: TASK-041
- done_when: a rejected proposal is not repeated in the session

### TASK-043 - Per-variable inheritance state
- satisfies: AC-044
- depends_on: TASK-005
- done_when: inherited variables are read-only in the child and detaching is an explicit action that
  keeps the current value

### TASK-044 - Case state machine
- satisfies: AC-045
- depends_on: TASK-001
- done_when: only the transitions of XC-136 are permitted and the tree shows the state

### TASK-045 - Missing inputs move to unresolved
- satisfies: AC-046
- depends_on: TASK-044
- done_when: a removed or changed input moves the case to unresolved, keeping its definitions

### TASK-046 - Pipelines read the state
- satisfies: AC-047
- depends_on: TASK-044, pipeline/TASK-013
- done_when: skipping decisions come from the case state, not a separate check

### TASK-047 - Packing a workspace
- satisfies: AC-048
- depends_on: TASK-001
- done_when: document, workspace assets and optionally data are packed, with the size stated first

### TASK-048 - What a pack could not take
- satisfies: AC-049
- depends_on: TASK-047
- done_when: linked folders and non-redistributable assets are named rather than dropped

### TASK-049 - Opening a pack without data
- satisfies: AC-050
- depends_on: TASK-047, TASK-044
- done_when: every case opens unresolved rather than appearing to work

### TASK-050 - Absolute and difference declarations
- satisfies: AC-051
- depends_on: TASK-001
- done_when: a declaration records which it is and conversion follows the matching rule

### TASK-051 - Output size and pruning
- satisfies: AC-052
- depends_on: pipeline/TASK-029
- done_when: passing the limit reports the size and offers pruning by run

### TASK-052 - Pruning keeps the record
- satisfies: AC-053
- depends_on: TASK-051
- done_when: artefacts go, run records and input data stay, and nothing is deleted unnamed

### TASK-053 - Times in UTC with the offset
- satisfies: AC-054
- depends_on: TASK-001
- done_when: stored times are UTC plus offset and are displayed in the reader's zone

### TASK-054 - Workspace shell navigation
- satisfies: AC-055, AC-058
- depends_on: TASK-001
- done_when: the two-row shell offers the six menu groups and switches between Workspace and Workspace
  list without mislabelling the latter as cases

### TASK-055 - Workspace list
- satisfies: AC-056
- depends_on: TASK-054
- done_when: search, filters, grid/list controls, create action and cards all operate on workspaces and
  no preview invents analysis values

### TASK-056 - Reopenable side panels
- satisfies: AC-057
- depends_on: TASK-054
- done_when: panel toggles remain at the outer toolbar edges while their panels open and close

### TASK-057 - Create an independent item from a template
- satisfies: AC-061
- depends_on: TASK-029, view/TASK-010, graph/TASK-013
- done_when: resolution is previewed before acceptance, a new workspace item records its source
  template id and revision, and later edits on either side do not propagate

### TASK-058 - Workspace item lists
- satisfies: AC-062
- depends_on: TASK-029
- done_when: View, Graph and Report lists open, create, duplicate, rename and delete concrete items and
  never label them as templates; Simulation remains the later-release placeholder

### TASK-059 - Template revisions remain independent
- satisfies: AC-063
- depends_on: TASK-031, TASK-057
- done_when: updating a template creates a later revision and leaves every item created from an earlier
  revision unchanged

### TASK-060 - Shared material-library composition
- satisfies: AC-060
- depends_on: TASK-056
- done_when: every named View, Graph and Report material-library category uses the shared
  `サンプル`/`オリジナル`, search, `タグ`, sort and result/empty-state composition, while Simulation
  exposes no material-library shelf

### TASK-061 - Work-area header names the new workspace item
- satisfies: AC-064
- depends_on: TASK-058
- done_when: Simulation, View, Graph and Report headers respectively expose `＋ 新規シミュレーション`,
  `＋ 新規ビュー`, `＋ 新規グラフ` and `＋ 新規レポート`, never generic `＋ 新規作成`, and show no
  persistent Template or Save-as-template button, while Simulation continues to state its r1
  unavailability and the centre-bottom Template library category remains present where specified

### TASK-062 - Bottom material shelf and current-state properties
- satisfies: AC-065
- depends_on: TASK-060
- done_when: View, Graph and Report place a collapsed-by-default full-width `素材ライブラリ` bar whose
  title is immediately followed by an up-to-expand or down-to-collapse chevron rather than a detached
  far-edge icon; its whole surface opens a complete-row, expandable material library; the open bar shares its row with
  category tabs and closes from its non-control surface while category tabs and the top-edge resize
  splitter remain operable; no redundant one-row/multi-row icon remains; Sample/Original and retrieval
  controls share the next row; the material library remains
  above the instruction bar with narrow-width drawer behaviour, selection, drag and explicit apply;
  right rails edit current state only and rename Template to `全体`; Chat shows no shelf

### TASK-063 - Dock boundary resizing
- satisfies: AC-066
- depends_on: TASK-062
- done_when: visible sidebars resize horizontally from their complete inner boundaries, the open
  material shelf resizes vertically from its complete top boundary, the quiet borders gain an accent
  only during interaction, WAI-ARIA splitter semantics and arrow keys provide equivalent accessible
  adjustment, shelf dragging starts at the rendered height and follows pointer displacement without
  height animation, its maximum is derived from the centre column's available rendered height, the app
  remains viewport-bounded without application-level vertical scrolling, centre usability bounds stop
  the drag, hidden panels expose no splitter and no content data changes

### TASK-064 - Put Graph and Report Output last
- satisfies: AC-067
- depends_on: TASK-057
- done_when: Graph and Report each expose one File Output tab as the last visual, DOM and keyboard item
  with the ordinary preceding-tab gap and no physical-bottom anchoring, while shared selected-name,
  tooltip and tab semantics remain intact

### TASK-065 - Store multiple Simulation flows on the Workspace
- satisfies: AC-068, AC-069, AC-070, AC-071
- depends_on: TASK-001, pipeline/TASK-001
- done_when: `シミュレーション一覧` manages multiple independently identified and revisioned flows;
  each executable flow holds one or more explicit external-solver execution conditions, round-trips
  without invented outputs, and a Pipeline reference stays pinned to its chosen Simulation revision

### TASK-066 - Separate Object controls from Asset lifecycle language
- satisfies: AC-072
- depends_on: TASK-060, TASK-062, view/TASK-052
- done_when: View current-state controls use Object, its reusable library category is Object, and Asset
  remains the term for scope, revision, import, export and reuse

### TASK-067 - Keep peer-tab widths stable and equal
- satisfies: AC-073
- depends_on: TASK-060, TASK-061, TASK-062
- done_when: top work-area tabs and each material-library category group use one stable width per group;
  the top group becomes equal-width icon tabs at its narrow breakpoint, and an overflowing library group
  scrolls without unequal or truncated labels
