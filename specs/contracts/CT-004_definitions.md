---
status: draft
updated: 2026-08-22
---

# Contracts: view, graph and report definitions

These three are the definition payloads a @Workspace item stores, a @Template may snapshot, and the
assistant emits (XC-080, XC-109). They are grouped
because they share one property that decides their design: **a definition names things, it never
contains results.** A @View holds the identifier of a field and the name of a colour map; it does not
hold values, pixels, or a resolved colour scale. That is what makes a saved workspace reproducible
(INV-005) and what makes generated content safe - a schema of identifiers has nothing to evaluate.

### CT-004 - View definition
- purpose: the reproducible description of one @View - what is shown, from where, in what style
- schema: schema/CT-004.json
- version: 3.1.0
- strictness: unknown fields are **preserved**, because a view authored by a newer build must survive
  being opened and saved by an older one (CT-001)
- compatibility: a field added to the definition has a default that reproduces the previous appearance
- migration: on open, in memory; the file is rewritten only when the user saves
- decidedness: Fixed
- basis: E-001 (T1)

A view names: **the fields it requires** - not a dataset, because a view belongs to the @Workspace and
resolves against whichever @Case is in scope or its explicit case binding (XC-109) - and how they are displayed (colour map, range,
out-of-range treatment), the representation (surface, wireframe, points, contour), which @Part are
shown, the camera, the background, the material, the annotations, and the renderer backend if the user
chose one (GL-009).

Version 2.0.0 added what later decisions require a view to carry, each because leaving it out made a
picture that could not be reproduced or could be misread:

| Field | Why it is in the definition |
|---|---|
| `resultPosition` | a position on the @Result axis, which may be a time, a mode, or a frequency with a phase (XC-131) |
| `deformation` | the scale a body is drawn at. **1.0 is the default**, and the factor is drawn into every export (XC-132) |
| `componentFrame` | the named frame components are reported in; absent means global Cartesian (XC-122) |
| `derivedVisualisations` | seed, integrator, step size and limits for streamlines - change one and the picture changes (INV-025) |
| `partVisibility` | which named parts are shown (INV-019) |
| `panes`, `cameraSynchronised` | the split layout, recorded because an exported comparison must say whether the cameras were synchronised |

Version 2.1.0 adds `textureMappings`, a per-View-object list that records the reproducible mapping
choice without storing generated coordinates. A reference mesh uses `authoredUv` and names its
`sourceUvSet`; the importer preserves that set's values, indexing and interpolation. An analysis mesh
uses `none`, `objectTriplanar`, `planar`, `cylindrical`, `spherical` or `generatedAtlas`. Scale is stored
as `scale_m` in canonical metres. `generatedAtlas` records the generator name, version and parameters;
the display-topology identity remains a runtime cache key because it identifies derived geometry, not a
user choice. Generated coordinates, seam vertices and current generation status are cached rendering
results and never enter this definition or the source @Dataset (XC-167). If `textureMappings` is absent,
the Material Asset's declared mapping profile applies. A legacy Material Asset with no profile resolves
to `none`; absence never causes silent UV generation.

Version 2.2.0 adds `objectAppearances`, one entry per View-object identifier. Each entry records the
CAE object type, one optional `pbrMaterialId`, one optional `resultColouring` binding and the explicit
display mode. `analysis` gives the result transfer function exclusive ownership of base colour;
`appearance` shows the PBR material without a hidden result layer; and `analysisWithSurfaceDetail`
retains only non-colour normal and roughness detail. The list is not a layer stack and an object
identifier occurs at most once. Preview primitive and target-selection state are interface state and do
not enter the reproducible View definition (XC-169, XC-171). If `objectAppearances` is absent, the
legacy top-level `material` and `colouring` members retain their previous semantics; opening alone does
not rewrite them.

Version 3.0.0 supersedes that two-slot shape with `materialBindings`. Each entry has View-local
`bindingId`, object identifier, whole-object/part/element-set target, an immutable CT-008 Material Asset
`entryId` plus `revision`, optional MaterialX variant, and bindings for its published inputs. There is
one Material Asset kind under CT-011: a binding may have no analysis dependency, or may bind one or
several MaterialX inputs to `solviaResult` sources. `solviaResult` records field identifier, component,
point/cell association, result-position rule, declared unit and range rule; it never stores result
arrays. A MaterialX input may also bind a literal, geometry property or another immutable Material Asset
revision for explicit graph composition (XC-174, XC-175).

Several Material Bindings may name one View object. One whole-object default may coexist with mutually
non-overlapping part or element-set overrides; overlapping subset bindings are invalid, and every
surface element resolves to exactly one root MaterialX material. There is no implicit layer order.
Texture mapping remains separately reproducible in `textureMappings`; where several bindings on one
object need distinct mapping, its optional binding identity associates the mapping with the Material
Binding (XC-176).

Version 3.1.0 adds `objectPresentations`, with at most one entry per View-object identifier. It stores
visibility, representation and a dimensionless `displayOpacity` in `[0, 1]`. For
`surfaceWithEdges` and `wireframe`, the same object entry also stores one edge overlay with explicit
sRGB colour, output-pixel width and opacity. Edges describe displayed topology and never belong to a
Material Slot. The resolved surface alpha is `displayOpacity * MaterialX geometry_opacity`; an edge's
alpha is `displayOpacity * edgeSettings.opacity`. Analysis values, colour-map values and reported
numbers are unchanged. An absent `objectPresentations` member retains the legacy top-level
`representation` and existing visibility behaviour, so opening an older definition does not alter its
appearance. New saves write the per-object entry when the user edits any of these controls (XC-180).

Resolution state is derived and is not saved as if it were a user choice. An unresolved required input
retains the binding, reports CT-010 detail and renders that target diagnostic magenta until repaired.
Opening a 2.2 definition migrates `pbrMaterialId` and `resultColouring` in memory into an equivalent
Material Binding only when the referenced legacy assets and their exact revisions can be identified;
otherwise the old members remain preserved and unresolved. Opening alone does not rewrite them. Saving
after successful migration writes current `materialBindings`, never both representations (XC-175).

The colour range is stored either as explicit numbers or as the rule that produced them - never as
numbers that pretend to be a choice when they came from the data.

The definition payload deliberately has no workspace-item or template identity. CT-001 owns item
identity and revision; CT-008 owns template identity, scope and revision. Copying this payload between
those envelopes is how `Create from template` and `Save as template` reuse one schema without making
the two objects the same thing (XC-109).

### CT-005 - Graph definition
- purpose: the reproducible description of one @Graph - which values, over what, in what style
- schema: schema/CT-005.json
- version: 2.0.0
- strictness: unknown fields are preserved
- compatibility: as CT-004
- migration: as CT-004
- decidedness: Fixed
- basis: E-001 (T1)

A graph names its series, and each series names a source: a field on a dataset, a derived quantity
with the expression that produced it, or an external reference file. **Each series carries the unit it
is plotted in and whether that unit was declared**; a series whose unit is undeclared is drawn with the
undeclared marker on its axis rather than an assumed label (XC-003).

### CT-006 - Report definition
- purpose: the reproducible description of a deliverable - what goes in it, in what order, in what style
- schema: schema/CT-006.json
- version: 2.0.0
- strictness: unknown fields are preserved
- compatibility: as CT-004
- migration: as CT-004
- decidedness: Fixed
- basis: E-001 (T1)

A report is an ordered list of blocks - a view, a graph, a table of values, a text passage, a
page break - plus the output targets and the art style. A text block records whether it was written by
a person or generated, and a generated block records the values it was derived from (report/AC-011).

## Why definitions and results are kept apart

Three consequences follow from the separation, and each of them is a requirement elsewhere in this
specification rather than a design preference:

- **Reproducibility.** Opening a saved workspace re-runs the definitions against the same inputs and
  must produce the same output (INV-005). A definition holding a cached result would reproduce the
  cache, not the computation.
- **Safety.** The assistant emits definitions, and a definition made only of identifiers and
  enumerated values has no evaluator to escape from (XC-080).
- **Extension.** A new representation, colour map or block type is a new enumerated value plus one
  handler. Callers that store and pass definitions do not change - which is the property the extension
  seams in [../01_boundaries.md](../01_boundaries.md) depend on.
