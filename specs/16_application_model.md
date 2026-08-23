---
status: draft
updated: 2026-08-22
---

# The application model

The complete product, not the first release. [11_ui.md](11_ui.md) inventories the screens r1 ships and
is written against that scope; this file describes the shell those screens are a subset of, the areas
the complete product adds, the objects behind all of them, and the paths a user takes through them.

Written because the r1 inventory answers "what does the user see" and cannot answer "where does the
next surface go". A product that grows a table, a diff, a node graph and a log without a grammar for
where a surface lives grows four bespoke screens, and the shared components of 11_ui.md gain a second
implementation each time. The grammar is the point; the catalogue below is its first population.

**Nothing here changes r1.** Where this file describes a member a contract does not carry yet, the
contract gains it with the code that implements it, not before - the rule of spec model 6.5. What this
file fixes now is the shape those additions must take, so that two of them do not arrive as two shapes.

## 1. What was measured

Two products were read on this machine rather than described from memory. Both are installed here, both
were enumerated from the running program, and both entries in the evidence record name the command that
produced the numbers (E-120, E-121).

| | Blender 5.0.1 | ParaView 6.2.0 |
|---|---|---|
| What it is here for | the **shell**: how a window is divided, where a panel lives, how a command is bound | the **object model**: how a visualisation, a chart, a table and an output are described as data |
| Structure | Window - Screen - Area - Region; 19 editors, 16 region kinds | proxies with typed properties, grouped and named; 1143 definitions in 78 groups |
| Where the complexity sits | Properties editor `data` context 129 panels, `render` 89; `View3DOverlay` 95 properties | a geometry representation 222 properties, `RenderView` 159, `XYChartView` 130 |
| Command surface | 2442 operators in 77 modules, bound through 105 area-scoped keymaps | every proxy property is scriptable; the GUI writes Python for what it did |
| What it separates | display state from data: 135 shading and overlay properties, none of them on the mesh | the colour map from the thing coloured: one lookup-table proxy, referenced |
| What this product must not copy | name uniqueness by numeric suffix (XC-103); Python bypassing undo (XC-102); the dark theme (XC-144) | the pipeline browser as primary navigation (XC-195); a colour map re-chosen per representation |

Neither is a competitor and neither is a target to match feature for feature. They are read because both
have already answered, over decades, the questions this product is about to answer badly by inventing.

## 2. The shell grammar

Four nested things, fixed by XC-190.

```
Application
└── Window                  one open Workspace document, one OS window
    └── Screen              a named, saveable layout; six built-in presets
        └── AreaNode        binary split tree: Split{axis, ratio, first, second} | Leaf{areaId}
            └── Area        exactly one editor kind; the unit of split, join, maximise
                └── Region  a sub-surface from one fixed vocabulary
```

- **Window.** One open @Workspace. A second window on the same workspace is a second view of one
  document, sharing selection and undo; a second window on another workspace is a second document.
- **Screen.** A layout with a name. Switching Screen changes the tool, never the subject: the open
  @Workspace, the selected @Case and the current position on the @Result axis survive the switch. A
  Screen is workspace UI state (XC-149) and never enters a definition.
- **Area.** Hosts one editor kind. Splitting an Area produces two Areas of the same kind, which the
  user then retypes; joining discards the layout of the one absorbed, never its subject.
- **Region.** Optional, collapsible, and drawn from the vocabulary below. An Area declares which
  regions it may show; a region it does not declare cannot be summoned into it.

**The three-column shell of 11_ui.md is the default Screen preset.** It is `Leaf(navigator) | Leaf(main
editor) | Leaf(properties)` with the shelf and composer regions of the centre Area shown. Saying it that
way is what lets Diff arrive as a second `main` Area rather than as a fourth column.

## 3. Region vocabulary

Eight kinds. Fewer than the sixteen measured in E-120, because six of those exist for editors this
product does not have, and because a region kind that appears in one Area only is a panel, not a kind.

| Region | What it is for | Where the toggle lives | Measured analogue |
|---|---|---|---|
| `main` | the Area's own canvas or document | not toggleable; an Area always has one | Blender `WINDOW`, ParaView view widget |
| `header` | the Area's own tools and its subject selector | always visible | Blender `HEADER` / `TOOL_HEADER` |
| `navigator` | the Area's tree or list of subjects | outer edge of the Screen | Blender `CHANNELS`, ParaView Pipeline Browser |
| `properties` | icon rail plus one section, editing the current item or selection | outer edge of the Screen | Blender `UI` with `bl_context` rail | - |
| `shelf` | horizontal resource strip docked below `main` | its own title bar (XC-149) | Blender `ASSET_SHELF` |
| `composer` | the instruction bar: one conversation, compact form (XC-150) | absent while the drawer owns the composer | - |
| `overlay` | transient surfaces over `main`: result axis, gizmo, probe, conversation drawer | each owns its own dismissal | Blender `HUD` and gizmos, ParaView 3D widgets |
| `footer` | what this Area is currently showing, and why it may be incomplete | always visible when the Area declares it | Blender `FOOTER` |

Rules that hold for every region:

- **one control, one region.** A control that appears in two regions is a defect, not a convenience.
  The panel toggles live at the outer ends of the work toolbar and never inside the panel they open.
- **a region never scrolls the application.** Expanding `shelf` shrinks `main`; it never grows the
  window or introduces application-level scrolling (XC-149).
- **`overlay` never reserves space.** A result axis with nothing to scrub is absent, not disabled
  (XC-160).
- **`properties` edits the current thing and never browses reusable ones.** Browsing is `shelf`, and
  the full organiser is the Library Area (XC-149).

## 4. Area catalogue

Twenty editor kinds. The `r1` column says which exist in the first release and in what form, and the
last column names the screen the design catalogue carries for it, so the difference between "designed"
and "shipped" is readable from one place - and checkable: `tests/test_application_model.py` compares
that column against `mockups/ui/lib/screen-catalog.json` in both directions.

| Area | Edits | Regions it declares | r1 | r1 screen |
|---|---|---|---|---|
| `workspaces` | the list of @Workspace: search, tag filter, grid or list, open, create | main, header | yes | `home` |
| `viewport` | one pane of a @View: geometry, fields, materials, guides | main, header, properties, shelf, composer, overlay, footer | yes | `view` |
| `outliner` | the @Dataset structure and the @View object list, with visibility and selection | main, header | yes, as a region of the View Screen | - |
| `properties` | the current item or selection, through an icon rail | main, header | yes, as a region | - |
| `chart` | one @Graph: series, axes, style, output | main, header, properties, shelf, composer, footer | yes | `graph` |
| `table` | one saved table of values with unit, digits and @Provenance | main, header, properties, composer, footer | **no** (XC-191) | - |
| `report` | one @Report: blocks, layout, trust content, commentary | main, header, properties, shelf, composer, footer | yes | `report` |
| `pipeline` | one @Pipeline: units, bounded zones, target counts, runs | main, header, properties, composer, footer | yes | `pipeline` |
| `nodes` | a typed graph: MaterialX for a @Material, or an @Expression graph | main, header, properties, footer | partly, as a dialogue over the centre | - |
| `timeline` | the @Result axis, camera paths and animation cues over the current item | main, header, footer | a canvas overlay and a property tab; the docked editor is future | - |
| `diff` | a @Diff between two @Case: the field, the method, and what it cost | main, header, properties, composer, footer | **no** - the feature is specified, the surface is not | - |
| `information` | what the loaded @Dataset actually contains: fields, associations, ranges, counts, frames | main, header, footer | **no** | - |
| `find` | a data selection built as a query, and what it resolved to | main, header, footer | **no** | - |
| `library` | the Asset organiser: import, metadata, revisions, scope, bulk management | main, header, navigator, properties, footer | named as future in 11_ui.md | - |
| `script` | the Python surface of [13_scripting.md](13_scripting.md): editor, console, and the log of what was just done | main, header, footer | a copyable popover only | - |
| `log` | notifications, run records and the communication audit, kept after dismissal | main, header, footer | popovers only | - |
| `chat` | the full-height rendering of the one conversation (XC-150) | main, header, navigator | yes | `chat` |
| `simulation` | one @Simulation flow: conditions for external solver executions | main, header, properties, composer, footer | yes, definition only (XC-091) | `simulation` |
| `settings` | application and workspace preferences, and the command list | main, header, navigator | yes, as a page | `settings` |
| `network` | what may leave the machine and what has (XC-106) | main, header, properties, footer | yes | `network` |

Nine of the twenty are not editors in r1. Four are absent outright - `table`, `diff`, `information`
and `find` - and five exist only as something smaller: `nodes` as a dialogue, `timeline` as a canvas
overlay plus a property tab, `script` and `log` as popovers, `library` as the shelf plus a note that the organiser is
future. Four of the nine are gaps rather than deferrals - a specified capability with no surface:

- **`diff`.** [features/diff/spec.md](features/diff/spec.md) fixes how a @Diff is computed, what it
  must disclose across meshes, and that it is a quantity like any other. No screen state in 11_ui.md
  shows one, so nothing says where the resampling direction, the outside-target count and the
  round-trip error are read.
- **`information`.** The product's claim is trustworthy numbers, and no surface says what the file
  actually contains. Format support, field associations, declared units and coordinate frames appear
  once, inside the import dialogue, and then never again.
- **`find`.** [contracts/CT-007_selection.md](contracts/CT-007_selection.md) is *case* selection. There
  is no way to select points or cells by a condition, which is what a probe, a @Derived quantity, a
  threshold and a @Diff over a region all need.
- **`table`.** Discussed in XC-191.

The remaining five are deliberate reductions already named in 11_ui.md, 13_scripting.md and XC-160:
each has a smaller form that is right for r1 and a full form the complete product needs. `nodes` is the
clearest: a graph edited in a sidebar-width miniature is the case XC-177 already refuses, and the
dialogue r1 opens over the centre is the interim shape.

## 5. Screen presets

Six built-in Screens, plus two application pages. A preset is a starting layout, not a lock: the user
may split, retype and save, and their saved Screens sit beside the built-ins.

| Preset | Areas | Why this shape |
|---|---|---|
| Simulation | navigator, `simulation`, properties | one flow at a time; nothing to compare |
| View | navigator, `viewport` (1-4 panes), `outliner` above properties | the @Outliner sits above the rail because selection drives it (view/AC-068) |
| Graph | navigator, `chart`, properties | a chart's subject is its series, which the rail owns |
| Report | navigator, `report`, properties | the document is the canvas |
| Automation | navigator, `pipeline`, properties | the palette is in the rail, the flow in the centre |
| Chat | conversation history, `chat` | the sidebar is history, not cases (XC-150) |
| Settings | `settings` full width | no workspace sidebars (XC-165) |
| Network and audit | `network`, properties | no case tree; the permission is workspace-wide |

Layouts the complete product ships as additional presets, each a split of an existing one:

| Preset | Areas | For |
|---|---|---|
| Compare | two `viewport` Areas, camera-synchronised, plus `diff` below | the job the product exists for |
| Inspect | `viewport`, `table`, `information` | checking a figure against the file it came from |
| Author material | `viewport`, `nodes`, properties | a MaterialX graph needs a canvas, not a sidebar miniature |
| Automate | `pipeline`, `log`, `script` | writing a run, watching it, and reading what it did |

## 6. Transitions

Three transition classes, separated by one rule: **switching area changes the tool; switching subject
changes what every area shows; switching workspace changes the document.**

```
                    ┌──────────────────────── application ─────────────────────────┐
   [no workspace] ──▶ Workspace list ──open──▶ Workspace ──▶ Screen preset ──▶ Area
        ▲                   │                     │  ▲            │
        │                   │ new                 │  │ close      │ split / retype / save
        └────── close ──────┴─────────────────────┘  └────────────┘
```

**Class 1 - tool changes.** Screen switch, Area split, region show or hide, property section change.
These preserve the open @Workspace, the selected @Case, the open item per Area, the position on the
@Result axis, the conversation with its draft, and the selection. They enter no undo history because
they change no document.

**Class 2 - subject changes.** Selecting a @Case, opening another @View, moving the result position.
Every Area that follows context re-renders; an Area pinned to an item does not. A workspace item that
binds its own cases is the authority, and the tree cannot override it by clicking (11_ui.md).

**Class 3 - document changes.** Opening a workspace, importing, closing. The only transitions that may
discard in-memory state, and each states what it will discard before it does.

Transitions that are refused rather than performed, each with the reason on screen:

| Attempted | Refused when | Reason shown |
|---|---|---|
| edit any workspace item | a @Pipeline run is in progress over this workspace | the run's subject would move underneath it (pipeline/AC-040) |
| start an export | an export to that target is already running | XC-060 |
| apply a @Template | required fields, cases or assets are unresolved | the unresolved list, before anything is drawn (XC-063) |
| run a @Pipeline holding a destructive unit | that unit's scope is unauthorised | the unit, and how many cases it covers (XC-094) |
| convert a unit | the @Declared unit is absent | nothing is inferred (XC-003) |
| reach the network | the workspace permission is absent | the exact request, and that it was not sent (XC-106) |

## 7. Element inventory

What each Area needs to contain. Read with [11_ui.md](11_ui.md), which fixes the r1 subset and the
naming; this adds the complete-version elements and says what each is bound to, because a control with
no binding is decoration and a binding with no control is a value nobody can set.

Every table below uses one convention for the last column: **unresolved** is what the element shows
when what it needs is missing. It is a column rather than a paragraph because it is the state the
product is judged on, and the one every design review forgets.

### 7.1 `viewport`

Whole-View group of the property rail.

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| 全体 | name and description; pane count 1-4 and arrangement; per-pane @Case and camera binding; camera synchronisation off/orbit/all; guides - world axes, ground grid, orientation gizmo, scale bar, selection outline; unit display | `View.layout`, `View.guides` | a pane whose @Case has no @Dataset names that, and draws nothing |
| カメラ | the named camera list with add, duplicate, rename, delete and set-active; for the selected camera - pose explicit or framed on a target, projection, focal length or parallel scale, sensor, near and far clipping, shift, focus target, depth of field, navigation | `View.cameras[]`, `View.activeCameraId` | a camera whose pose rule cannot resolve names the missing quantity and leaves the camera where it was (XC-197) |
| 出力（再生プリセット） | the named @Timeline list - each six values: start and end saved positions, stride, speed, frame rate and loop - beside the saved result position list it draws from. A video names one timeline **and one camera**; the timeline carries no camera of its own (XC-200) | `View.timelines[]`, `View.resultBookmarks[]` | a timeline whose start or end cannot resolve names the missing quantity and refuses the export |
| 描画 | @Renderer backend and its availability; one 照明 group - source studio, background environment or unlit, strength, shadow, ambient occlusion, key light when studio; one 現像 group - preset, exposure, contrast, tone mapping, white balance, image treatments the backend supports; transparency method; sample count | `View.environment.lighting`, `View.grade`, `View.renderer` | an unavailable backend or treatment names which and what still runs (XC-004, XC-198) |
| 背景 | kind solid, gradient, image or environment; colours; environment @Asset, rotation, visible-to-camera, display strength | `View.environment.background` | an environment asset that cannot be resolved says so; the background does not silently fall back |
| スライス | plane, box, sphere, cylinder, annulus or frustum; interactive handle plus exact numeric origin and normal; cut style smooth or cell-preserving; invert; show the cutting surface | `View.widgets[]` | a widget outside the data bounds says so rather than showing an empty result |
| 計測 | distance between two picked positions; angle between three; the value with its @Declared unit, @Significant digits and @Provenance; keep as a @Variable | `View.widgets[]`, `Workspace.variables` | an unpicked end shows no number, never zero |
| 凡例 | which colour map object; orientation and placement; title and component; label format and precision; range annotations; out-of-range and missing-value swatches | `Workspace.colourMaps[]`, `View.guides.legends[]` | a legend for an unresolved field names the field and shows no scale |
| 出力 | kind image, video or interactive; format; resolution; transparent background; **one named camera** for either and **one named timeline** for a video, both chosen here; destination pattern; no-overwrite policy; preflight | `View.output[]`, `View.timelines[]` | a video naming no timeline, or one whose positions do not resolve, is blocked and the preflight names which |

Active-object group. The @View object taxonomy is fixed in 11_ui.md; what each type needs is here,
because "the Object section is type-specific" is a rule and this is the content it ranges over.

| Type | Object section holds | Materials | テキスト | Refuses to guess |
|---|---|---|---|---|
| 解析メッシュ | source role, source element, 表示形式 surface / surface with edges / wireframe, visibility, 表示不透明度, edge colour, width and opacity when edges are shown | yes | no | a display opacity never edits a @Material Asset |
| 参照メッシュ | the same, plus that its role is reference and it carries no solver results | yes | no | it is a display role of the Mesh family, not a second file format |
| スカラー場 | field, association, component, colour map object, range rule, legend, contour or isosurface values | yes | no | an absent field is named; no neighbouring field is substituted |
| ベクトル場 | field, @Component frame, glyph shape, scale mode and factor, density or masking, colour source | no | no | an automatic scale states what it derived the factor from |
| 流線・軌跡 | source vector field, seed set, integrator and step size, maximum length and steps, line or tube presentation, time range for pathlines | no | no | no geometry is generated until field and seeds both resolve (INV-025) |
| 点群 | source, point size, size-by-quantity, colour binding, gaussian or sprite rendering | no | no | point attributes stay distinguishable from a continuous mesh |
| テキスト・注釈 | kind text, dimension or point label, anchor in screen or world space, leader, @Provenance | no | **yes** | a dimension's measured value and unit come from canonical data and are not editable text |
| エフェクト | kind highlight, glow or particles, target, strength, and that it is display-only | no | no | it never invents an analysis value, and says so on the object |

Canvas overlays: orientation gizmo (upper right, below the representation row - XC-145); result-axis
overlay on hover (XC-160); probe readout; @Deformation scale stamp drawn into the picture (INV-024);
reduced-representation marker (INV-001); selection highlight; widget handles; the conversation drawer
(XC-151).

### 7.2 `outliner`

| Region | Elements | Bound to | Unresolved |
|---|---|---|---|
| header | title; substring search; filter menu - by type, by visibility state, by whether a field resolves; restriction-column switches, each independent | `Outliner.filters` | a filter that matches nothing says which filter emptied it |
| main | one row per source element: disclosure only where there are children, taxonomy type icon, the exact authored name, a right-edge visibility toggle | `Dataset.hierarchy`, `View.objects[].presentation.visible` | an unreadable branch names what could not be read and shows only confirmed nodes |

`Shift` applies visibility to descendants and `Ctrl` isolates the branch, with the affected rows
previewed before a large recursive change. Selection is shared with the viewport in both directions
(view/AC-068), and the row is the same object the property rail edits. r1 does not rename, reparent or
delete source elements here.

The complete product adds a second display mode, chosen in the header the way E-120's seven modes are:
**source structure** (the @Dataset as authored) and **View objects** (what this @View draws, including
derived objects that have no source row - a scalar field, a trajectory, an annotation). One tree cannot
be both without inventing parentage, which the @Dataset mode may never do.

### 7.3 `chart`

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| 全体 | name; title; subtitle; caption; legend on/off, position, symbol width | `Graph.title`, `Graph.legend` | - |
| 種類 | 2D - line, scatter, bar, histogram, box/quartile, parallel coordinates, plot matrix, heatmap; 3D - surface, scatter, contour; projection and view direction for 3D | `Graph.kind` | a kind the selected quantities cannot support names why |
| 軸 | one entry per used axis of bottom, left, top, right: title, @Declared unit, range auto or explicit, log scale, tick label notation and precision, custom labels, grid | `Graph.axes` | an axis whose series have no declared unit carries the undeclared marker, never an assumed label (XC-003) |
| 系列 | list with add, remove, reorder; per series - label, X source (@Result axis, a parameter, index), Y quantity or @Expression, @Declared unit, @Provenance, missing-value policy, target axis corner, colour, line style, thickness, marker style and size, opacity | `Graph.series[]` | a series with no quantity is listed and drawn as no data, never dropped from the legend |
| スタイル | style @Asset; palette chosen for discriminability; background; grid weights; typography | `Graph.style` | - |
| 詳細 | case selection (CT-007) - selected, saved, declarative condition, or Python; iteration handling; reduction method and its weighting quantity; @Reference material | `Graph.caseSelection`, `Graph.reduction` | a selection that resolves to nothing says which condition emptied it (CT-007) |
| 出力 | image, vector, tabular data or animation; format; size; provenance columns for tabular; result-axis mapping for animation; destination and no-overwrite | `Graph.output[]` | preflight blocks on unresolved series and names each |

The chart canvas has no global 適用 button (XC-153): edits are property edits and undo as one step.
Hovering a point shows its value, unit and the @Case it came from; clicking it selects that case.

### 7.4 `table`

The Area XC-191 adds. Its purpose is that a number on screen can be checked without leaving the product.

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| 全体 | name; association - point, cell, integration point, field, case or variable; the @Case selection it reads | `Table.source` | an association the @Dataset does not carry is named, and the table stays empty |
| 列 | column list with add, remove, reorder; per column - quantity or attribute, header text, @Display unit, @Significant digits, provenance column shown or not, numeric format, width | `Table.columns[]` | a column whose quantity is missing in one @Case shows the missing marker in those rows, never zero (XC-001) |
| 絞り込み | rule list: value range, equals, text match, selection-only, valid-only; each rule enabled independently | `Table.rowFilter[]` | a rule that empties the table says which |
| 並び替え | column and direction; stable across paging | `Table.sort` | - |
| 出力 | CSV, Excel or Markdown; provenance and unit columns; machine-readable numbers do not follow the interface language (XC-110) | `Table.output[]` | - |

Rows are virtualised in blocks and the block size is a stated limit, not a silent truncation. Selecting
a row selects that element in the viewport; selecting in the viewport scrolls the table to it.

### 7.5 `report`

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| 全体 | name; document title; language; source @Template and its revision; the mandatory trust content - @Provenance, @Declared unit, limitations, product version - each shown as present and not removable | `Report.identity`, `Report.trustContent` | a mandatory item that cannot be produced blocks export and names itself |
| レイアウト | page size, orientation, margins, columns; header, footer, page numbers; figure width | `Report.layout` | - |
| スタイル | @Art style asset; palette including a monochrome print variant; table rules; figure treatment | `Report.artStyleId` | - |
| テキスト | body and heading typeface, sizes, embedding scope | `Report.typography` | a glyph the chosen face cannot draw is named with the element that used it, never exported as an empty box |
| 詳細 | which @Workspace and which @Case; @Reference material; the ordered block list with per-block reference and, for a @View block, still, video or interactive; commentary direction, depth, model, and whether a search may be made | `Report.blocks[]`, `Report.commentary` | a block whose referenced item was deleted is listed as unresolved and is not silently dropped |
| 出力 | interactive HTML, PowerPoint, Word, Excel, CSV, image, video, plain text, Markdown; per-format 3D handling; offline completeness; font embedding; destination and no-overwrite; preflight | `Report.targets[]` | a format that cannot carry an included block states the substitution in the document itself |

Generated commentary is reviewed before it enters the document: each passage carries which of the four
kinds it is and its source, and the omissions the standard produced are listed with their reason
(XC-104).

### 7.6 `pipeline`

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| main | the ordered unit list; a bounded zone around a loop, condition or simulation unit; a drop-position line previewed before the drop; the accumulated @Target set count on every unit; the start and end boundaries | `Pipeline.units[]` | a unit whose reference was deleted shows unresolved and blocks the run |
| ユニット | the palette: simulation, case, view, graph, report, table, export, tag, clear, loop, variable, formula, condition | `Pipeline.units[]` | - |
| 設定 | per selected unit: name, kind, its own references pinned by identifier and revision, its @Expression where it has one, failure policy | `Pipeline.units[].settings` | a pinned revision that no longer exists is named; the unit does not fall forward to the latest |
| 履歴 | run records; per run the outcome table of case against unit - applied, skipped, failed, refused, with the value a false condition evaluated to; the files each run wrote | `Pipeline.runRecords[]` | a run interrupted at a unit boundary says which unit it stopped before |

A destructive unit states its scope - which unit, how many @Case - and is authorised once for the run
(XC-094). Editing the workspace under a run is blocked with the reason (pipeline/AC-040).

### 7.7 `nodes`

| Region | Elements | Bound to | Unresolved |
|---|---|---|---|
| header | which graph is open - a @Material Asset revision, or an @Expression; save state; validation state | `Material.materialX` | - |
| main | typed nodes with named input and output sockets; connections that only join compatible types; add, delete, duplicate, reroute; frame and comment; navigation by zoom, pan and fit | the MaterialX document | a node whose implementation is absent is drawn and named, never dropped |
| properties | the selected node's inputs; the graph's declared @Material Binding requirements - expected type, association and unit dimension per `solviaResult` input | `Material.requirements[]` | an unbound required input is listed, and its target renders diagnostic magenta (XC-175) |

Editing here and editing in 基本 edit one document. Nodes that 基本 cannot represent are retained, never
flattened. Imported implementations are never executed.

### 7.8 `timeline`

The dockable form of the result-axis overlay, for work the overlay cannot hold.

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| main | the @Result axis drawn to scale - time in seconds, mode index with eigenfrequency, or frequency at a held phase; the available positions as ticks; the current position; a range selection for export | `Case.resultAxis`, `View.resultPosition` | a steady @Case shows the axis as absent, not as a disabled bar (XC-160) |
| カメラパス | named paths; keyframes of camera pose against axis position; interpolation; preview | `View.cameraPaths[]` | a path with one keyframe cannot produce a video, and the preflight says so |
| キュー | what else varies over the axis: @Deformation scale, a colour-map range, visibility | `View.animationCues[]` | a cue over a quantity the @Case lacks is listed and does not run |

A position that does not exist on the axis is named and refused, never rounded to the nearest
(view/AC-033).

### 7.9 `diff`

The surface [features/diff/spec.md](features/diff/spec.md) needs and 11_ui.md does not have.

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| 対象 | @Case A and @Case B, named in that order; the quantity; the @Component frame both are read in; @Absolute or difference | `Diff.left`, `Diff.right`, `Diff.quantity` | a quantity present in one @Case only is named, and no difference is computed |
| 方法 | shared mesh or resampled; when resampled, which dataset is the target - chosen by the user, never by the product; the matching basis, @Source identifier or array position | `Diff.method` | different declared units refuse the diff and name both (INV-002) |
| 開示 | the resampling direction; how many points fell outside the target; the round-trip error; all three carried with the result wherever it appears | `Diff.disclosure` | a missing location is missing in the result, never zero (INV-011) |
| 表示 | the difference as a field in a `viewport`, as a series in a `chart`, or as a column in a `table` - it is a quantity like any other | `Workspace.variables`, any item that references it | - |

### 7.10 `information`

Read-only, and the answer to "is the number I am looking at supported by the file".

| Section | Elements | Bound to |
|---|---|---|
| ファイル | source paths; reader and its version; format support level with the named gaps for a Limited reader; import time; checksum |
| 構造 | element and point counts; cell types present; bounds in the @Canonical frame; blocks or parts and their sizes |
| フィールド | one row per @Field: authored name, association, component count and authored component names, @Declared unit or the undeclared marker, measured range at the current result position, missing-value count |
| 座標 | the @Component frame declared for this @Dataset, and whether it resolved |
| 結果軸 | axis kind and its positions; for a @Complex result, that real and imaginary parts are held together |

Nothing here is editable, and nothing is inferred: a field with no declared unit says undeclared, and a
frame that did not resolve says so rather than defaulting to global Cartesian.

### 7.11 `find`

The data-selection surface CT-007 does not cover.

| Section | Elements | Bound to | Unresolved |
|---|---|---|---|
| 対象 | @Case; @Dataset; association point, cell or block | `Selection.target` | - |
| 条件 | query over field values with the @Expression editor - names in scope, unit checking, the error at its position; or ids; or a picked region; or a block selector; or a threshold on one field | `Selection.spec` | an unresolvable name is named at its character position, and nothing is selected |
| 結果 | how many elements matched; the first rows in a `table`; highlight in the viewport; keep as a named selection | `Selection.resolved`, `Workspace.selections[]` | a query matching nothing says so and leaves the previous selection untouched |

A named selection is a document object, so a @Graph, a `table`, a @Diff and a @Pipeline unit can all
refer to the same one rather than each carrying a copy of the condition.

### 7.12 `library`, `script`, `log`

| Area | Elements |
|---|---|
| `library` | navigator of scopes - sample, workspace original, shared original (@Library scope) - and categories; per @Asset: rendered thumbnail or a named missing-thumbnail state, name, kind, revision list, dependencies, tags, licence, origin, import and export; bulk operations; where used |
| `script` | a Python editor over `sv.data`, `sv.context`, `sv.ops`, `sv.pipeline`, `sv.units`; a console; the log of what the interface just did, as the same commands, copyable; run, and run selection; one script is one undo step (XC-102) |
| `log` | notifications kept after dismissal, with severity, area, subject and the action that dismissed them; @Pipeline run records; the communication audit of XC-106 with its export |

### 7.13 `chat`, `simulation`, `settings`, `network`

These are fixed in 11_ui.md and are listed here only for the completeness of the catalogue. The
complete product changes one thing in each: `chat` gains the conversation settings as document state
rather than per-surface state (XC-150); `simulation` gains execution when it exists (XC-091); `network`
gains a per-host allow-list rather than a single switch (XC-106); and `settings` gains an editor for
the command list rather than a printed copy of it.

| Settings section | Elements | Bound to | Unresolved |
|---|---|---|---|
| ショートカット | the command list generated from the registry, grouped by the keymap scope; per command its label, its resolved key, and the area the binding belongs to; search by command name or by key; rebind, restore one, restore all; import and export a scheme | `Application.keymaps` | a command marked destructive shows キーなし with the confirmation it is reached through, and refuses a binding (XC-193) |
| コマンド衝突 | two bindings of one key inside one scope; one command bound to different keys in two scopes | derived from the registry | listed at startup and in this section; neither is silently resolved by order |

## 8. The object model

Four layers, separated by what each one survives. The separation is the design: a value in the wrong
layer is how a workspace becomes unopenable on another machine, or how deleting a @View changes a
number.

| Layer | Survives | Held where | Examples |
|---|---|---|---|
| Application | reinstall, if exported | user profile | preferences, keymap, shared @Library scope registry, recent workspaces |
| Window | this session | memory | Screens, Areas, region sizes, which Area is maximised |
| Session | until the workspace closes | memory, journalled | selection, active object, resolved caches, notifications, the conversation, run progress |
| Document | forever, and on another machine | the @Workspace file (CT-001) | cases, items, variables, templates, pipelines, declared units, colour maps |

Two rules decide every placement dispute. **A value another engineer must see to reproduce the result
is Document.** **A value that describes how this person is looking at it today is Window or Session**
(XC-149, XC-192).

### 8.1 Application

```
Application {
  preferences: Preferences
  keymaps:     Keymap[]                 // one 'global', one per Area kind
  libraries:   LibraryScopeRef[]        // shared scopes this install can reach
  recent:      WorkspaceRef[]
  install:     { productVersion, buildId, rendererCapabilities }
}

Preferences {
  general:       { language, startupBehaviour, autosaveInterval }
  display:       { theme: 'system'|'light'|'dark', contrast, density, numberFont }
  units:         { displayUnitByQuantityKind: Map<QuantityKind, Unit> }   // never applied to a file
  frames:        { defaultComponentFrame: FrameRef }
  renderers:     { preferred: RendererId, fallbackPolicy: 'name-and-stop' }
  artStyle:      { defaultArtStyleId }
  assistant:     { modelId | null, effort, searchPolicy: 'off'|'ask'|'allow' }
  library:       { defaultSaveScope: 'workspace'|'shared', offlineResolution: 'package-only' }
  network:       { defaultDecision: 'refuse', hostAllowList: Host[] }     // per workspace overrides
  diagnostics:   { logLevel, supportBundleContents }
}
```

`Preferences.units` is a *display* preference. It never becomes a @Declared unit: a quantity read
without one stays undeclared however the preference is set (XC-003, XC-134).

### 8.2 Window

```
Window {
  id
  workspaceId
  screens:      Screen[]
  activeScreenId
}

Screen {
  id, name, builtin: boolean
  layout:       AreaNode
  areas:        Area[]
}

AreaNode =
  | { kind: 'split', axis: 'horizontal'|'vertical', ratio: number, first: AreaNode, second: AreaNode }
  | { kind: 'leaf',  areaId: Id<Area> }

Area {
  id
  kind:         AreaKind                 // the nineteen of section 4
  regions:      Map<RegionKind, RegionState>
  subject:      SubjectBinding
  maximised:    boolean
}

RegionState { visible: boolean, size: number, activeSection: string, scroll: number }

SubjectBinding =
  | { mode: 'follow-context' }                       // re-renders when the selected Case changes
  | { mode: 'pinned', itemId: Id<WorkspaceItem> }    // ignores context, like a pinned Properties tab
```

`SubjectBinding` is what makes a Compare Screen possible without a second selection model: two
`viewport` Areas, one following context and one pinned, show two cases side by side while one tree
selection still means one thing.

### 8.3 Session

```
Session {
  workspaceId
  selection:      SelectionState
  resultPosition: Map<Id<Case>, ResultPosition>   // where each case is on its own axis
  caches:         { renderCache, fieldRangeCache, decimationCache }   // derived, never saved
  notifications:  Notification[]
  conversation:   Conversation                    // one, shared by composer and chat (XC-150)
  runs:           RunState[]                      // pipelines in progress
  locks:          { editingBlockedBy: Id<Run> | null }
  journal:        JournalEntry[]                  // the undo history of this session
}

SelectionState {
  cases:          Id<Case>[]                      // tree selection; the last is active
  viewObjects:    Id<ViewObject>[]                // the last is active and drives Object/Materials/Text
  data:           Selection | null                // point, cell or block selection (section 10)
  pipelineUnit:   Id<PipelineUnit> | null
  reportBlock:    Id<ReportBlock> | null
}
```

Caches are listed because they are the layer that most often leaks upward. A decimated mesh, a computed
field range and a rendered frame are all derived from Document plus a resolved input; none of them may
be stored, cited, or measured for a reported value (INV-001, INV-009).

### 8.4 Document

The @Workspace, extending CT-001. Members marked **new** are additions the complete product needs and
the contract gains with the code that implements them.

```
WorkspaceDocument {
  formatVersion, id, name, createdBy, createdIso
  cases:            Case[]
  datasets:         Dataset[]                 // new: referenced by Case, so two cases may share one
  variables:        Variable[]
  referenceMaterial: ReferenceDocument[]
  workspaceItems:   WorkspaceItem[]           // view | graph | report | table | simulation
  pipelines:        Pipeline[]
  templates:        TemplateRef[]
  colourMaps:       ColourMap[]               // new (XC-194)
  selections:       NamedSelection[]          // new (section 10)
  displayUnits:     Map<QuantityKind, Unit>
  componentFrames:  Frame[]
  permissions:      { network: NetworkPermission }
}
```

#### Case, Dataset, Field

```
Case {
  id, name, parentId: Id<Case> | null
  tags:        string[]
  state:       CaseState                       // GL: imported | computed | failed | ...
  datasetIds:  Id<Dataset>[]
  resultAxis:  ResultAxis
  variables:   VariableBinding[]               // declared here, inherited by children
  provenance:  { sourceFiles: FileRef[], importedIso, readerId, readerVersion }
}

Dataset {
  id
  nameAsAuthored: string
  hierarchy:      DatasetNode[]                // exactly as the file carries it; never inferred
  fields:         Field[]
  geometry:       { pointCount, cellCount, bounds: Box, cellTypes: string[] }
  coordinateFrame: FrameRef | 'unresolved'
  support:        { level: 'verified'|'limited'|'unsupported', gaps: string[] }
}

DatasetNode { id, nameAsAuthored: string | null, kind, childIds: Id<DatasetNode>[] }

Field {
  id
  nameAsAuthored:  string
  association:     'point' | 'cell' | 'integrationPoint' | 'field'
  components:      { count: number, namesAsAuthored: string[] }
  declaredUnit:    Unit | null                 // null is undeclared, and stays undeclared (XC-003)
  storedPrecision: 'float32' | 'float64' | ...  // decides Significant digits (INV-014)
  provenance:      Provenance
}

ResultAxis =
  | { kind: 'steady' }
  | { kind: 'time',      unit: 's',  positions: number[] }
  | { kind: 'mode',      positions: { index: number, eigenfrequency: Quantity | null }[] }
  | { kind: 'frequency', unit: 'Hz', positions: number[], sweep: { held: 'phase'|'frequency', value: Quantity } }

ResultPosition = { axisKind, index: number }   // an index into positions, never an interpolated value
```

`ResultPosition` is an index rather than a value on purpose: a position that does not exist is then not
representable, which is what makes view/AC-033 a type error rather than a runtime rounding.

#### Quantities, variables and provenance

```
Quantity { value: number | null, unit: Unit | null, digits: number, provenance: Provenance }

Provenance =
  | { kind: 'declared',  by: string, atIso: string }
  | { kind: 'dataset',   datasetId, fieldId, association, resultPosition }
  | { kind: 'computed',  expression: string, inputs: Ref[], engineVersion }
  | { kind: 'reference', documentId, locator: string }          // never a numerical basis
  | { kind: 'measured',  method: 'probe'|'distance'|'angle'|'integral', target: Ref, resultPosition }

Variable {
  id, name
  scope:  { caseId: Id<Case> | null }          // null is workspace-wide
  value:  Quantity | Expression
  inheritedBy: 'descendants' | 'none'
}
```

A @Variable that a descendant overrides keeps both values reachable, because changing the parent must
be visibly different from changing the child (XC-062 confirms the second).

#### Workspace items

```
WorkspaceItem = { id, name, kind, revision, createdFrom: TemplateOrigin | null, definition }

TemplateOrigin { templateId, revision, unresolvedAtCreation: UnresolvedEntry[] }   // XC-063

ViewDefinition {                                    // CT-004, complete form
  layout:      { panes: Pane[], cameraSync: 'off'|'orbit'|'all' }
  objects:     ViewObject[]
  materialBindings: MaterialBinding[]               // CT-004 3.0
  objectPresentations, textureMappings              // CT-004 3.1 / 2.1
  environment: { background: Background, lighting: Lighting, worldRotationDeg: number }
  cameras:     Camera[]                             // new (XC-199); a pane names the one it looks through
  timelines:   Timeline[]                           // new (XC-199); an output names the one it plays
  resultBookmarks: ResultBookmark[]                 // new (XC-197), referenced by timelines
  grade:       Grade                                // new (XC-198)
  guides:      { grid, worldAxes, orientationGizmo, scaleBar, selectionOutline, legends: LegendRef[] }
  widgets:     Widget[]                             // new: slices, clips, measurements
  resultPosition: ResultPosition
  deformation: { scale: number, appliedTo: Id<ViewObject>[] }    // 1.0 default, drawn in (INV-024)
  componentFrame: FrameRef
  rendererBackend: RendererId | null
  output:      OutputSpec[]
}

Pane { id, caseBinding: 'context' | Id<Case>, camera: Camera, viewportKind: '3d'|'slice'|'ortho' }

ViewObject {
  id, name
  kind: 'analysisMesh'|'referenceMesh'|'scalarField'|'vectorField'|'trajectory'|'pointCloud'|'annotation'|'effect'
  source: { datasetNodeId } | { derivedFrom: Ref, method: DerivationSpec }
  presentation: { visible, representation: 'surface'|'surfaceWithEdges'|'wireframe'|'points',
                  displayOpacity: number, edges?: { colour, widthPx, opacity } }
  kindSettings: AnalysisMeshSettings | ScalarFieldSettings | VectorFieldSettings | ...
}

ScalarFieldSettings {
  fieldId, component, association, colourMapId: Id<ColourMap>, rangeRule: RangeRule, legendId | null
}

Widget =
  | { kind: 'slice'|'clip', shape: 'plane'|'box'|'sphere'|'cylinder'|'annulus'|'frustum',
      placement: ImplicitPlacement, cutStyle: 'smooth'|'cellPreserving', invert: boolean, showSurface: boolean }
  | { kind: 'distance'|'angle', points: Position[], result: Quantity }

CameraPath { id, name, keyframes: { at: ResultPosition | number, camera: Camera }[], interpolation }
AnimationCue { id, target: 'deformation'|'colourRange'|'visibility', keyframes: Keyframe[] }
```

#### Saved result positions, and what resolves them

XC-197. A saved position answers *when*, the same way a camera answers *where from*: explicit, or a rule
that resolves per @Case.

```
FocusTarget =
  | { kind: 'object',    viewObjectId }
  | { kind: 'selection', selectionId }
  | { kind: 'position',  point: Position }
  | { kind: 'extremum',  quantity: Ref, statistic: 'max'|'min'|'absMax',
                         over: 'currentPosition'|'allPositions'|'selection' }

ResultBookmark {
  id, name
  position: { kind: 'explicit',  index: number }
          | { kind: 'extremum',  quantity: Ref, statistic: 'max'|'min'|'absMax', scope }
          | { kind: 'crossing',  quantity: Ref, threshold: Quantity, direction: 'rising'|'falling'|'either' }
          | { kind: 'relative',  of: 'first'|'last' }
  resolution?: Resolution
}

Resolution =
  | { state: 'resolved',   caseId, index: number, at: Quantity, snapped: boolean }
  | { state: 'unresolved', caseId, reason: string, missing: Ref }
```

Three properties, each of which is the difference between this being useful and being a trap:

- **`Resolution` is derived.** It is recomputed for the @Case in scope and never written into the
  definition. A four-pane comparison therefore shows each pane its own critical position, which is the
  whole point of naming a bookmark `最大応力時` rather than typing `12.0 s`.
- **`snapped` is reported.** An extremum that falls between stored positions resolves to a position that
  exists and says it did (view/AC-033, XC-160). It is never interpolated.
- **An unresolved entry changes nothing.** The camera stays where it was and the position stays where it
  was; the entry names the quantity it could not find. Moving to the origin, or to the first position,
  is the plausible default XC-001 forbids in its own domain and this borrows the rule from.

`crossing` uses a @Declared unit for its threshold, so a bookmark reading `235 MPa` refuses to resolve
against an undeclared quantity rather than comparing bare numbers (XC-003).

#### Cameras and timelines, the two lists a @View holds several of

XC-199. A camera is one object, not a pose beside a lens; a timeline is one object, not export settings
beside a scrubber. Both resolve per @Case wherever they hold a rule (XC-197).

```
ViewDefinition {
  cameras:        Camera[]
  activeCameraId: Id<Camera>
  timelines:      Timeline[]
  activeTimelineId: Id<Timeline>
  resultBookmarks: ResultBookmark[]        // referenced by timelines, not owned by them
  layout: { panes: Pane[], cameraSync: 'off'|'orbit'|'all' }
}

Pane { id, caseBinding: 'context' | Id<Case>, cameraId: Id<Camera>, viewportKind }

Camera {
  id, name
  pose:       { kind: 'explicit', position: Position, focalPoint: Position, viewUp: [number,number,number] }
            | { kind: 'framed',   target: FocusTarget, direction: Direction, marginFraction: number }
  projection: 'perspective' | 'orthographic'
  lens:       { focalLengthMm?, parallelScale?, sensorWidthMm?, shift: [number, number] }
  clipping:   { near: number, far: number }
  focus?:     FocusTarget                  // also the depth-of-field focus
  depthOfField: { enabled, source: 'focusTarget'|'distance', distanceM?, fStop, blades }
  navigation: { orbitCentre: 'selection'|'bounds'|'focalPoint', zoomToCursor: boolean }
  resolution?: Resolution                  // derived per Case, never stored as a choice
}

Timeline {                                 // six values and nothing else (XC-200)
  id, name
  from:       BookmarkRef | 'first'
  to:         BookmarkRef | 'last'
  stride:     number                       // every Nth stored position
  speed:      number
  frameRate:  number
  loop:       boolean
  resolution?: { state, from: number, to: number, frameCount: number, caseId }
}

Comparison {                               // the second kind of View item (XC-202, GL-050)
  id, name
  baseViewId: Id<View>                     // live reference: objects, materials, lighting, guides
  axis:       { kind: 'case' | 'resultPosition' | 'camera' }
            | { kind: 'property', path: string }   // one published property of the base View
  members:    Ref[] | Value[]              // ordered, two or more
  arrangement: { kind: 'grid', rows: number, columns: number } | { kind: 'overlay' }
  labelling:  { template: string }                    // never optional
  colourMap:  { shared: true, colourMapId, range: RangeRule }
            | { shared: false, statedPerPane: true }  // XC-203
}

BookmarkRef = Id<ResultBookmark>
```

Three consequences, and the third is the reason for the first two:

- **A pane names its camera.** A four-pane comparison is four panes, four cases and four cameras, which
  is one binding per pane rather than a mode. `cameraSync` then means *apply my orbit delta to the other
  panes' cameras too*, and two panes naming one camera move together by construction.
- **An output names a camera or a timeline.** A still renders from a camera; a video plays a timeline.
  Motion is not a property of the file (XC-196's correction).
- **A @Timeline answers when and a camera answers from where, and an output names one of each**
  (XC-200). Both may be rules, so one timeline played from one camera over forty cases reaches each
  case's own critical moment from its own distance. Keeping them apart is what lets the same timeline
  be replayed from a different camera, and what makes camera a usable axis of @Comparison.

#### Grade, the group XC-198 adds

```
Grade {
  preset:      'measurement'|'standard'|'technicalDocument'|'presentation'|'photoreal'
  exposureEv:  number                               // 0 in measurement
  contrast:    number
  toneMapping: 'none'|'neutral'|'filmic'|'aces'
  whiteBalance:{ temperatureK, tint }
  treatments:  { antialiasing, ambientOcclusion, shadows, samplesPerPixel, denoise, bloom }
  legendPolicy:'gradedWithImage'|'recordedInExport'  // one of the two must hold when a grade is active
}
```

`measurement` sets tone mapping to `none`, exposure to zero and every treatment that alters colour off.
It is the default, and it is what an image cited as evidence is produced with.

#### Colour map, the object XC-194 promotes

```
ColourMap {
  id, name, revision
  colourPoints:  { position: number, colour: sRGB }[]        // two immutable endpoints plus interior
  opacityPoints: { position: number, opacity: number }[]
  interpolation: 'linearRgb'|'diverging'|'constant'
  domain:        RangeRule
  outOfRange:    { below: 'transparent'|sRGB, above: 'transparent'|sRGB }
  missingColour: sRGB                                        // the one missing-data treatment (XC-001)
  discretise:    { enabled: boolean, steps: number }
  themed:        false                                       // never; a value looks the same in both themes
}

RangeRule =
  | { kind: 'explicit', min: Quantity, max: Quantity }
  | { kind: 'dataRange', over: 'currentPosition'|'allPositions'|'selection', updatedIso }
  | { kind: 'symmetric', around: number, over: ... }

Legend { id, colourMapId, title, component, placement, orientation, labelFormat, precision,
         showRangeAnnotations, showOutOfRange, showMissing }
```

Storing `RangeRule` rather than two numbers is the same rule CT-004 already states for colour range:
the definition records the rule that produced a number, never numbers pretending to be a choice.

**This is the one place the design supersedes a contract rather than extending it.** CT-004 3.0 holds
the colour choice inside each Material Binding, and for r1 - one View, one binding - that is right and
shipped. The promotion of XC-194 changes where the map lives, so it is a contract version rather than
an added member, and the two forms must not both be written: opening a 3.x definition resolves each
embedded map to a workspace object on first save of the newer format, and never writes both.

#### Graph, table, report, pipeline

```
GraphDefinition {                                   // CT-005, complete form
  kind: GraphKind                                   // line|scatter|bar|histogram|quartile|parallel|matrix|heatmap|surface3d|scatter3d|contour3d
  axes: { bottom: Axis, left: Axis, top?: Axis, right?: Axis }
  series: Series[]
  caseSelection: CaseSelection                      // CT-007
  reduction: { method: 'none'|'weighted'|'unweighted', weightQuantity?: Ref }
  legend: { show, location, position, symbolWidth, fontSize }
  tooltip: { format, notation, precision }
  style: { artStyleId, palette, background, gridWeights, typography }
  resultAxisNote: string | null                     // set when series come from different axes (XC-131)
  output: OutputSpec[]
}

Axis { title, unit: Unit | null, declaredUnit: boolean, range: RangeRule, logScale: boolean,
       labelNotation: 'auto'|'fixed'|'scientific', labelPrecision: number, customLabels?: number[], grid: boolean }

Series { id, label,
         x: { kind: 'resultAxis' } | { kind: 'quantity', ref: Ref } | { kind: 'index' },
         y: { kind: 'quantity', ref: Ref } | { kind: 'expression', expression: Expression },
         unit: Unit | null, provenance: Provenance,
         missingPolicy: 'gap',                      // the only value; never interpolate or drop (XC-001)
         plotCorner: 'bottomLeft'|'bottomRight'|'topLeft'|'topRight',
         style: { colour, lineStyle, thicknessPx, marker, markerSizePx, opacity } }

TableDefinition {                                   // new (XC-191)
  source: { caseSelection: CaseSelection, association: 'point'|'cell'|'integrationPoint'|'field'|'case'|'variable',
            selectionId?: Id<NamedSelection> }
  columns: Column[]
  rowFilters: RowFilter[]
  sort: { columnId, direction: 'asc'|'desc' } | null
  paging: { blockSize: number }
  output: OutputSpec[]
}

Column { id, source: Ref | AttributeRef, header, displayUnit: Unit | null, digits: number | 'stored',
         showProvenance: boolean, format: 'decimal'|'scientific'|'engineering', widthPx }

RowFilter = { id, enabled, columnId,
              test: { kind: 'range', min, max } | { kind: 'equals', value } | { kind: 'contains', text }
                  | { kind: 'valid' } | { kind: 'inSelection' } }

ReportDefinition {                                  // CT-006, complete form
  identity:   { title, subtitle?, locale, authors: string[], documentDate }
  trustContent: { provenance: true, declaredUnits: true, limitations: true, productVersion: true }
  layout:     { pageSize, orientation, margins, columns, header, footer, pageNumbers, figureWidth }
  artStyleId
  typography: { bodyFace, headingFace, bodySizePt, noteSizePt, embedScope: 'usedGlyphs' }
  scope:      { workspaceIds: Id<Workspace>[], caseSelection: CaseSelection, referenceDocumentIds }
  blocks:     ReportBlock[]
  commentary: { mode: 'mechanical'|'generated', direction?, depth?, modelId?, searchPolicy: 'off'|'ask' }
  targets:    OutputSpec[]
  producedFrom: { itemRevisions: Ref[], engineVersion, producedIso }   // written at export
}

ReportBlock =
  | { kind: 'view',      itemId, form: 'still'|'video'|'interactive', caption? }
  | { kind: 'graph',     itemId, caption? }
  | { kind: 'table',     itemId, caption? }
  | { kind: 'text',      body, author: 'person'|'generated', derivedFrom?: Ref[], statementKind? }
  | { kind: 'reference', documentIds }
  | { kind: 'pageBreak' }

PipelineDefinition {                                // CT-009, complete form
  onFailure:  'continueOtherCases'|'stop'
  units:      PipelineUnit[]
  runRecords: RunRecord[]
}

PipelineUnit {
  id, name
  kind: 'simulation'|'case'|'view'|'graph'|'report'|'table'|'export'|'tag'|'clear'|'loop'|'variable'|'formula'|'condition'
  reference?:  { itemId, revision }                  // pinned; a later edit does not change the run
  expression?: Expression                            // condition and formula units
  children?:   PipelineUnit[]                        // loop, condition and simulation are bounded zones
  addsCases?:  CaseSelection                         // case units only
  destructive: boolean                               // clear units; authorised per run (XC-094)
}

RunRecord {
  id, startedIso, finishedIso?, issuer, authorisedUnits: Id<PipelineUnit>[]
  outcomes: { caseId, unitId, outcome: 'applied'|'skipped'|'failed'|'refused',
              note?: string, conditionValue?: boolean }[]
  filesWritten: { path, bytes, atIso }[]
  stoppedBefore?: Id<PipelineUnit>                   // cancellation is at a unit boundary
}
```

#### Primitives

The small types the structures above lean on. They are listed because each of them is somewhere a
plausible default would otherwise appear.

```
Unit      = { symbol: string, dimension: Dimension }          // declared, never inferred (XC-003)
Quantity  = { value: number | null, unit: Unit | null, digits, provenance }
Ref       = { kind: 'case'|'dataset'|'field'|'variable'|'item'|'asset'|'selection', id, revision? }
FrameRef  = { frameId } | 'canonical' | 'unresolved'          // never silently global Cartesian
Camera    = { position, focalPoint, viewUp, projection: 'perspective'|'orthographic',
              viewAngleDeg?, parallelScale? }
Background = { kind: 'solid'|'gradient'|'image'|'environment', colours?, assetId?, rotationDeg?,
               visibleToCamera: boolean, displayStrength: number }
Lighting   = { source: 'studio'|'backgroundEnvironment'|'unlit', strength, shadows, ambientOcclusion,
               keyLight? }                                     // one group, in 描画 (XC-184)
Expression = { text: string, scope: Ref[], checkedUnits: Dimension | 'undeclared',
               error?: { position: number, length: number, message } }
Position   = { point: [number, number, number], frame: FrameRef }
Box        = { min: Position, max: Position }
LocalisedText = Map<Locale, string>
```

#### Output, one shape for every area that produces a file

```
OutputSpec {
  id
  kind:        'image'|'video'|'vector'|'table'|'document'|'interactive'
  format:      string                                // png, jpeg, tiff, mp4, webm, svg, pdf, csv, xlsx, html, pptx, docx, md
  resolution?: { width, height } | 'viewport'
  transparentBackground?: boolean
  cameraPathId?: Id<CameraPath>                      // required for a video from a viewport
  axisRange?:   { from: ResultPosition, to: ResultPosition, stride: number }
  frameRate?:   number
  includeProvenanceColumns?: boolean                 // tabular
  destination:  { patternTemplate: string, onExisting: 'refuse' }    // never overwrite (XC-060)
  preflight:    PreflightResult | null
}

PreflightResult { checks: { label, detail, status: 'pass'|'warning'|'blocked' }[], checkedIso }
```

One `OutputSpec` shape across viewport, chart, table and report is what makes an export unit in a
@Pipeline a single implementation rather than four. The differences between kinds are optional members,
not separate types, so an area that gains a format does not gain an export path.

## 9. The command model

Everything that changes state is a command (CT-002). The complete product adds a **descriptor** beside
the command, because four things the interface needs - a label, a keyboard binding, a confirmation and
a dry run - are all properties of the operation rather than of the button that happens to call it.

```
CommandDescriptor {
  name:            string                    // 'view.apply_template'; never repurposed once shipped
  module:          string
  label:           LocalisedText
  description:     LocalisedText
  parameters:      ParameterSpec[]
  changesState:    boolean
  destructive:     boolean                   // deletes, overwrites, or releases loaded data
  needsConfirmation: boolean                 // XC-062: names what changes and in how many places
  undoable:        boolean                   // false only where the effect left the document (files)
  dryRunnable:     boolean
  effectSummary:   (parameters) => LocalisedText
  areaContext:     AreaKind[] | 'any'
  bindable:        boolean                   // derived: false whenever destructive is true (XC-193)
}

Keymap { id, scope: AreaKind | 'global', bindings: KeyBinding[] }

KeyBinding {
  id, command: CommandName, parameters?: object
  key: { code: KeyCode, event: 'press'|'release'|'clickDrag'|'doubleClick',
         modifiers: { ctrl, shift, alt, meta }, secondKey?: KeyCode }
  active: boolean
  userModified: boolean
}
```

Three properties follow, and each is checkable rather than asserted:

- **`bindable` is derived, not authored.** A destructive command cannot be given a key by an author who
  did not read the rule; registration refuses it (XC-193).
- **the same action has the same key in every area.** Two keymaps binding one command to different keys
  is a defect the registry reports at startup, not a preference.
- **every command appears in the command list.** The settings command list is generated from the
  registry, so a command with no entry is a command the registry does not have.

The four callers of CT-002 - interface, assistant, @Script and @Pipeline - all produce the same
`Command`, so the journal below has one shape whatever issued it.

## 10. The selection model

Two selections, deliberately distinct, and one active item within each.

```
CaseSelection = CT-007                     // which cases an item reads: declarative, saved, or Python

Selection {                                 // new: which elements inside a case
  id, name?                                 // named selections are Document; unnamed are Session
  target:      { caseId, datasetId }
  association: 'point'|'cell'|'block'
  spec:
    | { kind: 'ids',       ids: number[], basis: 'sourceIdentifier'|'arrayIndex' }
    | { kind: 'query',     expression: Expression }
    | { kind: 'threshold', fieldId, component, range: RangeRule }
    | { kind: 'block',     selectors: string[] }
    | { kind: 'picked',    frustum: Position[], throughSurface: boolean }
  resolved?:   { count: number, resolvedIso, atResultPosition: ResultPosition }
}
```

Rules:

- **`basis: 'sourceIdentifier'` is preferred and stated.** Matching by array position across two
  @Case is only valid where the meshes are identical, and INV-023 already requires the identifier where
  one exists; the selection records which it used, because a diff computed the other way is a different
  number.
- **A selection resolves at a result position and says so.** A threshold selection is not the same set
  at every time step, and a saved selection that is replayed elsewhere reports the position it was
  resolved at.
- **The active element drives the property rail.** With several selected, the most recently selected is
  active and the others remain selected, producing no aggregate form (view/AC-068).
- **Selection is Session unless named.** Naming it makes it a Document object that a @Graph, a table, a
  @Diff and a @Pipeline unit can share.

## 11. Undo, the journal and run records

One log, four readers. Undo, the run record, reproducibility and the dry run are all built on the
command log (13_scripting.md), so there is exactly one place an action is recorded.

```
JournalEntry {
  id, sequence, atIso
  issuer:   { kind: 'interface'|'assistant'|'script'|'pipeline', identity?: string }
  groupId:  string                          // one instruction is one undo step (XC-061)
  commands: Command[]
  result:   { status: 'applied'|'refused'|'failed', changed: Ref[], reason?: string }
  documentRevisionBefore, documentRevisionAfter
  filesWritten: { path, bytes, atIso }[]    // not undone; offered for deletion by name (XC-061)
}
```

- **The undo boundary is the @Workspace document.** Files already written are outside it: undo restores
  the document and the run record offers to delete what it produced, naming each file.
- **One instruction is one step**, including a multi-part instruction from the assistant and an entire
  @Script.
- **A refused command is journalled.** A record that holds only successes cannot answer "why did nothing
  happen", which is the question a user asks after a refusal they did not see.
- **A run record is a journal slice.** The outcome table of case against unit is derived from the
  entries that ran under that run's group, so the table and the history cannot disagree.

## 12. Notifications and where a failure appears

A failure appears **where it happened** - on the unit, the case, the pane, the field - and is also kept
in the `log` Area. Neither replaces the other: the inline one is how it is noticed, the log is how it is
found again after looking away.

```
Notification {
  id, atIso
  severity:  'info'|'warning'|'error'|'refusal'
  origin:    { areaKind, subject: Ref }
  title, detail
  actions:   { label, command: Command }[]        // 'open the unit', 'show the file', 'permit once'
  dismissedIso?: string                            // dismissal hides it; it stays in the log
}
```

Four notification kinds have fixed content because getting them wrong is the product's central risk:

| Kind | Must name |
|---|---|
| unreadable input | the file, what could not be read, and that the original is untouched (XC-007) |
| missing value | that it is missing; never a zero, a previous value or an interpolated neighbour (XC-001) |
| undeclared unit | the quantity, and that no conversion happened (XC-003) |
| refused network request | the host, the exact request, and that nothing was sent (XC-106) |

## 13. What this model deliberately does not take

| Not taken | From | Why |
|---|---|---|
| the pipeline browser as primary navigation | ParaView | the subject here is the @Case the user named, not a chain of filters (XC-195) |
| a colour map chosen per representation | ParaView | two panes of one study must not drift apart (XC-194) |
| name uniqueness by numeric suffix | Blender | a script asking for `Cube` must not silently get `Cube.002` (XC-103) |
| Python bypassing the undo stack | Blender | forty generated reports must be revocable in one step (XC-102) |
| the dark theme | Blender | the shell is light neutral; the deliverable's @Art style is separate (XC-144, GL-013) |
| modifier stacks and geometry authoring | Blender | r1 inspects source geometry; it does not author it |
| a per-property "advanced" toggle | ParaView | a property that must be hidden to be usable is a property in the wrong section |

## 14. What r1 would have to gain

Collected so the difference between this design and the shipped product is one list rather than a
reading exercise. Each row is a surface or a structure that exists in this file and not in r1.

| Addition | Why it is not cosmetic |
|---|---|
| the Screen and Area grammar | every new surface below needs somewhere to live (XC-190) |
| `table` Area and `TableDefinition` | a number on screen cannot currently be checked at full precision (XC-191) |
| `diff` Area | a specified feature with acceptance criteria and no surface |
| `information` Area | nothing says what the file actually contains after import |
| `find` Area and `Selection` | no way to select points or cells by a condition |
| `timeline` Area, `CameraPath`, `AnimationCue` | a video output requires a named camera path that nothing can author |
| `ColourMap` as a document object | comparison panes and the report each hold their own copy today (XC-194) |
| `CommandDescriptor` and area keymaps | the destructive-key prohibition is a convention, not a check (XC-193) |
| `JournalEntry` with `filesWritten` | undo's boundary is stated in prose and stored nowhere |
| named `Selection` objects | a condition is retyped in each place that needs it |
| `library` and `script` Areas | both are specified capabilities reachable today only through a popover |
