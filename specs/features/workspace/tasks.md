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
- done: 2026-08-24, `src/service/workspace/document.py` - MOD-007's first code. A document saves and
  reopens with every definition intact, and a test compares the version this build writes against the
  version in `schema/CT-001.json`: the contract states it in prose, in the schema and now in code, and
  three places that must agree need a test rather than an intention.
### TASK-002 - Unknown fields preserved
- satisfies: AC-011
- depends_on: TASK-001
- done_when: a document containing fields this build does not understand keeps them through a load and
  save cycle, asserted by test
- done: 2026-08-24, and **structurally** rather than by care. The document is held as the parsed
  mapping itself and read through, not unpacked into typed attributes and repacked on save. Unpacking is
  how a field nobody wrote an attribute for disappears - silently, in a file the user believes they
  saved - and it is why a nested unknown survives here as reliably as a top-level one, which the tests
  check separately.
  A document declaring a newer major version opens, keeps every field, and **refuses to be written
  back**: writing it would claim to understand a shape that changed (CT-001 compatibility). Top-level
  unknowns can be named to the user; nested ones are kept and not listed, because naming them would mean
  walking a schema this build does not have for a version it does not know.
### TASK-003 - Damaged files never overwritten
- satisfies: AC-013
- depends_on: TASK-001
- done_when: opening a truncated document reports what could not be read and leaves the file
  byte-identical on disk
- done: 2026-08-24. `load` opens read-only and reads the whole file before parsing anything, so
  AC-013's "leaves the original untouched" holds by construction rather than by the absence of a bug -
  and the test asserts the bytes are identical afterwards rather than trusting the reasoning.
  A refusal says where the parse stopped, by line and column, and points at the previous version's
  filename. "Damaged" with no location is something a user cannot act on.
  A document missing a required field is refused as **not a workspace** rather than as an old one: a
  file without `cases` is not a workspace missing a feature.
### TASK-004 - Previous good version kept on save
- satisfies: AC-013
- depends_on: TASK-003
- done_when: a save keeps the previous version beside the new one until the new one is written
  completely (XC-055)
- done: 2026-08-24, as a sequence of renames rather than as an intention. The new document is
  written to a temporary file beside the target and **flushed to the platform** first - a rename
  following an unflushed write moves a file whose contents the operating system has not committed - then
  the existing file is moved aside and the new one moved into place.
  Between those two renames the data exists **twice**, as the previous version and as the temporary, and
  at no point zero times. A copy instead of the first rename would spend the same moment with two names
  for bytes that may not both be on disk.
  The previous version keeps a visible `.previous` suffix beside the file it replaced, because XC-055's
  restore procedure is "a file operation the user can perform without the product" and that requires a
  file they can find.
### TASK-005 - Nested case hierarchy
- satisfies: AC-001
- depends_on: TASK-001
- done_when: a @Case can be created beneath another at any depth and reopens at that depth
- done: 2026-08-24, `src/service/workspace/hierarchy.py`. A case nests to any depth and a new one
  carries the fields CT-001 requires and nothing invented beyond them - a field this build makes up is
  one a later version has to keep forever.
### TASK-006 - Cycle and deletion guards
- satisfies: AC-003
- depends_on: TASK-005
- done_when: an operation making a @Case its own ancestor is refused with the hierarchy unchanged, and
  deleting a parent requires confirmation naming the descendant count (AC-002)
- done: 2026-08-24. The cycle check runs **before anything is detached**, so AC-003's "leaves the
  hierarchy unchanged" is a state that cannot occur rather than one that gets cleaned up afterwards.
  Deletion takes the descendant count the caller put in front of the user and **refuses if it disagrees**
  with what is actually there. A confirmation is only a confirmation if what was confirmed is what
  happens: a dialogue saying "2 descendants" over a tree that now has 3 is worse than no dialogue, and
  only the layer holding the tree can tell.
### TASK-007 - Variable declaration and resolution
- satisfies: AC-004
- depends_on: TASK-005
- done_when: a @Variable is declared once and resolved through the hierarchy on load, never copied
  into children (INV-004)
- done: 2026-08-24, `src/service/workspace/variables.py`. INV-004 is met by **resolving on read and
  copying nothing**: a parent's change reaches every inheriting descendant in the same operation because
  there is no second copy to update, not because an update walks the tree. The version that walks the
  tree is the one that misses a branch.
### TASK-008 - Override and inheritance state
- satisfies: AC-005
- depends_on: TASK-007
- done_when: changing a parent value changes every inheriting descendant in one operation and leaves
  overriding descendants untouched, with the state visible per variable
- done: 2026-08-24. An inherited variable is **read-only in the child** and `detach` is the only way
  out - XC-117's correction in code. The earlier model let a child type a new value and detach silently:
  the user changes one number to try something, and three months later the parent no longer drives that
  child and nothing on screen said so.
  Detaching takes the current value as its starting point and records when it stopped following
  (AC-044). A descendant of a detached case follows **that** case, not the workspace, which falls out of
  resolving outwards rather than needing a rule.
### TASK-009 - Child-only variables
- satisfies: AC-006
- depends_on: TASK-007
- done_when: a variable added to a child does not appear on the parent, and deleting an inherited
  variable from a child is refused naming the ancestor that defines it (AC-007)
- done: 2026-08-24, and it needed a schema correction to be possible at all: a variable had nowhere
  to record which case it was declared on, so any resolution written against the old shape would have
  shown a child's variable on its parent. `declaredOn` is that field (CT-001's correction of the same
  date).
  Deleting an inherited variable from a child is refused **naming where it is defined** - the ancestor
  case, or the workspace - because "cannot delete" without the location is something a user cannot act
  on.
### TASK-010 - Unresolved variables are reported
- satisfies: AC-008
- depends_on: TASK-007
- done_when: a referenced variable with no value in scope reports as unresolved and no value is
  substituted
- done: 2026-08-24. An unresolved variable comes back as a `Resolution` that says why and carries
  no value. Three ways to be unresolved, each with its own sentence: never declared, declared on a case
  this one cannot see, and declared with no value.
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
- done: 2026-08-24, `src/service/workspace/sources.py`. **Missing and changed are different states**,
  not one problem state: a user can restore a missing file, and a changed one they have to decide about,
  because the numbers in the workspace were computed from what it used to be.
  A changed file is detected and **not re-read**. Re-reading it silently would replace every figure in
  the workspace with figures from a different input, under a report someone already wrote. The
  description gives both sides - recorded size and time against current - because "changed" alone
  leaves the user nothing to decide with.
- note: what this cannot detect is written into a test rather than left to be discovered. CT-001 records
  a size and a modification time, not a checksum, so a file whose bytes changed while both stayed the
  same reads as unchanged. Saying so is cheaper than a promise the contract cannot keep.
### TASK-014 - Tags and filtering
- satisfies: AC-014
- depends_on: TASK-005
- done_when: filtering by tag shows matching cases and states how many are hidden, and the selected
  case stays visible marked as outside the filter (AC-015)
- done: 2026-08-24, `src/service/workspace/tags.py`. A filter states how many it hid, because a tree
  that quietly shrinks looks like a tree that lost cases and the user's next question is whether
  something was deleted.
  **The selected case stays visible and says it does not match** (AC-015) - hiding what somebody has open
  is how a filter loses their place: they came back to a case, filtered to find its siblings, and the
  thing they were reading vanished. An ancestor of a match is kept for the same reason and marked the
  same way: a tree with its middle removed is not a tree, and it is not what was asked for either.
  Whether every wanted tag is required or any one of them is a parameter with no default: the two give
  different answers on the same tree, and only the caller knows which the user asked for.
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
- done: 2026-08-24, `src/service/workspace/quantities.py`. Declared, read, computed, measured and
  reference-material quantities in one list, each with its origin and its unit or the undeclared marker.
  The order is by provenance then name, because a list whose order depends on a dictionary's iteration
  is a list two screenshots disagree about.
  A @Field is listed as a field - its extent, association and unit - rather than as one of its values.
  Showing one number would be a choice of which entry to show, and nothing at this layer has the
  standing to make it.
### TASK-018 - Computed quantities show their expression
- satisfies: AC-019
- depends_on: TASK-017
- done_when: a computed entry displays the expression that produced it
- done: 2026-08-24. The expression is part of the entry rather than a tooltip: "1.17" and
  "1.17 = allowable / maximum" are different claims, and only the second can be checked.
### TASK-019 - Unavailable rather than absent
- satisfies: AC-020
- depends_on: TASK-018
- done_when: a quantity that cannot be evaluated for a case is shown as unavailable for that case
- done: 2026-08-24. An entry that disappears reads as a quantity that does not apply; one marked
  unavailable reads as a quantity that does apply and could not be worked out, which is what happened.
  **Reference material is listed and supplies nothing** - XC-013 forbids it as a source of numbers, and
  omitting it would hide that the value the user is looking for exists in a document the product
  declines to read a number from.
  One distinction the task did not name: a variable declared on a case this one cannot see is **absent**
  rather than unavailable. It is not this case's quantity at all.
### TASK-020 - Significant digits from stored precision
- satisfies: AC-021
- depends_on: TASK-017
- done_when: a value's displayed digits are derived from its stored precision, in one shared component,
  asserted for both single and double precision fields (INV-014)
- done: 2026-08-24. The shared component is `domain_core/precision.py`, which already derived digits
  from a stored dtype; what was missing was the digits of a value a **person typed**, and its absence
  showed up immediately - a variable written as 1.17 displayed as 1.17000, which is exactly the padded
  expansion INV-014 calls "a claim the data cannot support".
  `digits_written` counts the digits of Python's shortest round-tripping form, capped at what the
  storage carries. What it cannot recover is written into its docstring: somebody who typed 12.00
  meaning four significant digits is indistinguishable from one who typed 12, because the distinction
  was lost when the text became a float.
### TASK-021 - Stable identifiers, references by identifier
- satisfies: AC-022
- depends_on: TASK-001
- done_when: every object carries an identifier that is never reused, and no stored reference contains
  a name
- done: 2026-08-24, `src/service/workspace/naming.py`. An identifier is a kind, a colon and an
  opaque suffix, so a reference read out of a file says **what** it referred to even when the object is
  gone: `case:7f3a` is a case somebody deleted, and `7f3a` is nothing anybody can act on.
  A retired identifier is remembered and never issued again - not after a delete, not after an undo. A
  reference held outside this workspace resolves to the object it meant or to nothing, and never to
  whatever took its place. A retired **name**, by contrast, is free again: the identifier is the thing
  that must not repeat.
### TASK-022 - Duplicate names refused
- satisfies: AC-023
- depends_on: TASK-021
- done_when: a colliding create or rename is refused with the holder named, for every kind
- done: 2026-08-24, with the holder named and no suffix appended. "baseline (2)" beside "baseline"
  is a pair of objects nobody can tell apart in a report, created by a product that decided not to
  bother the user. Two different kinds may share a name; renaming something to the name it already has
  is allowed, or a form that saves every field would refuse every save.
### TASK-023 - Lookup returns one or fails
- satisfies: AC-024
- depends_on: TASK-022
- done_when: name lookup never returns a collection, and a miss reports what was searched
- done: 2026-08-24. A miss reports what was searched among - "not found" alone leaves the user
  guessing whether they misspelled it or are looking in the wrong place. A duplicate is reported as a
  document edited outside this product, because creation refuses collisions and so it cannot have
  happened here.
  Never a list: returning one moves the choice to a caller with less information than this layer has,
  and every caller that takes the first element is a bug nobody will find.
### TASK-024 - Rename keeps references working
- satisfies: AC-025
- depends_on: TASK-021
- done_when: renaming an object leaves views, pipelines and expressions resolving to it
- done: 2026-08-24, and asserted as a property of the whole document rather than of one code path -
  `references_in` walks a document for identifier-shaped strings, so a test can say "nothing stored
  holds a name" about all of it at once.
  One thing the task did not anticipate: a document written by another version, or edited outside this
  product, may hold identifiers this build would not issue and names it would not have allowed.
  Refusing to load them would lose the user's work over a rule about how they were made, so they are
  adopted as they are and the checks apply to what happens next.
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
