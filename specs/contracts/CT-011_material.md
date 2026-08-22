---
status: draft
updated: 2026-08-22
---

# Contract: Material Asset definition

### CT-011 - Material Asset definition
- purpose: the renderer-independent, reproducible definition carried by a CT-008 `material` entry:
  one qualified root MaterialX material, its typed inputs, resources, SOLVIA result dependencies,
  provenance, traceability and conversion requirements
- schema: schema/CT-011.json
- version: 1.0.0
- strictness: unknown fields, unknown MaterialX elements and imported source bytes are **preserved**.
  A reader may report an unsupported requirement, but may not rewrite or discard it while moving,
  copying or saving the Asset
- compatibility: a reader supports the contract only when it validates the declared MaterialX document,
  resolves every required input and resource, and can classify every feature used by the selected
  backend as `exact`, `baked` or `unsupported`. Partial success is not an appearance match
- migration: older MaterialX documents may be upgraded only into a new immutable Asset revision; the
  received byte sequence and its hash remain attached as import provenance
- decidedness: Fixed
- basis: E-108 (T1), E-109 (T1), E-110 (T1), E-111 (T1), E-112 (T1), E-113 (T1), E-114 (T1), E-001 (T1)

## One material model, described by its interface

There is no PBR-material kind, result-material kind or composite-material kind. The root MaterialX
graph and its `requirements` say what the material is capable of and what it needs. The interface may
require no SOLVIA data, one result or several results alongside textures and referenced material
graphs. `data-independent`, `解析データ依存` and `composite` are derived descriptions for search and UI;
they are not stored type choices and never override the graph (XC-174).

One CT-011 definition identifies exactly one qualified root MaterialX material element. If an imported
document contains several materials, import creates one immutable CT-008/CT-011 entry per material
element while allowing them to share the same content-addressed original document and resources.
MaterialX Looks, Collections, assignments, variants, surface, volume and displacement terminals remain
in the preserved source inventory. Scene assignment is CT-004/USD state, not Asset identity.

MaterialX owns shader values, nodes and connections. CT-011 does not repeat base colour, metallic,
roughness or another shader value in JSON. CT-011 owns facts MaterialX does not make authoritative for
SOLVIA: Asset identity, exact source hashes, data requirements, unit and association constraints,
licence, provenance, preview fixture, traceability and backend conversion history.

## SOLVIA backlink inside MaterialX

The shipped, versioned `solvia_defs.mtlx` library declares custom attributes restricted to a
`surfacematerial`: `solvia_asset_id` (string), `solvia_asset_revision` (integer), `solvia_contract`
(string), `solvia_contract_version` (string) and `solvia_manifest_uri` (string). A generated or imported
SOLVIA revision writes those attributes on its root material. `solvia_manifest_uri` uses the logical
form `solvia:asset/<id>?revision=<revision>` and resolves only through the current package/library
index; it is not a network scheme.

The backlink is a locator, not the authoritative manifest. On load, the CT-008 identifier and revision,
CT-011 contract version and MaterialX attributes must agree. A mismatch leaves both originals intact,
does not link them and reports the reference unresolved. A standalone `.mtlx` remains valid MaterialX
when the manifest is absent, but its SOLVIA metadata is unresolved and never guessed. CT-011 hashes the
raw MaterialX document and every dependency; MaterialX does not hash CT-011, avoiding a cyclic digest.

UsdMtlx ignores `attributedef`, so USD export independently writes the same identity into
`assetInfo` and namespaced `customData`. Those USD values are another backlink, not a second source of
truth (E-110).

## Result inputs are ordinary typed material requirements

A `solviaResult` requirement declares a MaterialX input name and value type, whether it is required,
allowed point/cell association, optional unit dimension and every visible channel it can affect. A
CT-004 Material Instance binds that requirement to field identifier, component, association, result
position and declared unit. The binding never copies the canonical result array into the View.

Before shader generation MOD-003 resolves the binding from the canonical Dataset into derived display
data: a native VTK array, GPU attribute or USD primvar, plus an explicit validity attribute. The
MaterialX graph reads it through `geompropvalue`. A trusted SOLVIA convenience node may express the
same requirement while authoring, but lowering replaces it with standard geometry-property access;
shader code never opens a Dataset, file, database or network connection (XC-175).

Each result input declares its visible effects. Any result that affects colour and is presented with
an authoritative legend names the exact transfer-function element and `legendOutput`. A graph whose
arbitrary mixing prevents that relationship from being validated may still be preserved and used as
unverified appearance, but `traceability.reportable` is false and presentable result export is refused.
Probe, extrema, table and report numbers continue to use canonical data, never shader-interpolated
attributes or pixels (INV-001, INV-002).

## Required input and material failure

Resolution checks the Asset revision, MaterialX validity, required inputs, field/component,
association, result position, declared-unit compatibility, texture/resource hashes, geometry
properties and selected-backend capability. A missing required item produces CT-010 reason data and a
failed Material Instance. The entire affected target renders with the reserved diagnostic magenta
material, the ordinary result legend is suppressed, the sidebar names every missing requirement and no
last-successful pixels or implicit value remains. Missing values inside an otherwise valid field use
the validity attribute and mark only their affected elements. An optional input may use only the
fallback declared in this Asset revision (XC-001, XC-175).

A failed material is a useful editable state and remains stored so a transferred View can be repaired.
It is not a successful deliverable: image, video, USD and Report export refuse it unless the operation
is explicitly a diagnostic export, in which case the failure report travels with the magenta geometry.

## Assignment and composition

CT-004 assigns Material Instances to a whole View object, a part or an explicit element set. A whole
object default may be overridden by mutually non-overlapping subsets. Every surface element resolves
to one root MaterialX material; independently assigned roots never form an implicit ordered stack.
The root graph may explicitly reference and compose other immutable Material Asset revisions and any
number of result inputs. That graph is the inspectable composition rule and declares which inputs
affect each output (XC-176).

## Source, resources and mapping

`materialX.documentSha256` is computed over the exact imported/generated UTF-8 source bytes. Imported
bytes are retained even when a parsed document is upgraded or normalised in memory. Every XInclude,
texture, LUT, custom-node library, colour configuration and implementation source is inventoried with
logical URI, package path, SHA-256, byte length, MIME type, required/optional state and licence where
known. Images additionally state dimensions, channels, bit depth, colour space, alpha mode, normal-map
convention, sampler behaviour and complete UDIM tile inventory. Missing metadata remains explicitly
unknown; it is never filled from the filename.

SOLVIA-authored MaterialX uses MaterialX 1.39 through the pinned 1.39.5 implementation, OpenPBR Surface
1.1.1 for new PBR surfaces, `lin_rec709_scene` as the explicit working space, `srgb_texture` for colour
textures and `raw` for data, mask, ORM and normal textures. Generated tangent-space normals use the
OpenGL positive-Y convention and the standard primary UV name is `st`. Imports retain their declared
spaces and conventions; conversion records the OCIO configuration identifier/hash and never assumes
sRGB for an unknown source (XC-178).

Mapping requirements name coordinate source, UV set, projection, scale, units, normal/tangent spaces
and tangent generator when one is needed. Generated coordinates and tangents are derived display
caches; CT-004 stores the choice and generator identity, while the canonical Dataset remains unchanged
(XC-167).

## Code management and validation

SOLVIA-authored `.mtlx` documents and `solvia_defs.mtlx` are code-managed sources. The engine uses the
official MaterialX Python API to create/edit documents, load the standard libraries, upgrade into a new
revision and call `Document.validate`; CI also runs `mxvalidate` and semantic graph fixtures. Tests
compare graph meaning and generated target interfaces rather than relying on XML attribute order.
Imported raw source is never regenerated merely to make it resemble SOLVIA formatting (E-114).

MaterialX node graphs may be arbitrarily rich in preserved source, but execution is bounded to the
declared SOLVIA profile. External source-code implementations are recorded but not executed. XInclude
and asset resolution accepts package-contained normalised paths only, rejects traversal and symlink
escape, performs no network request offline and enforces the measured XML depth, dependency-count,
byte and image limits in 05_limits.md. Unknown nodes and attributes cause `unsupported`, never deletion
or a plausible replacement.

## Renderer and interchange adapters

Native VTK and vtk.js have separate, versioned capability manifests. Each required node, terminal,
texture channel, colour transform and geometry property is classified `exact`, `baked` or
`unsupported`. `baked` requires an explicit operation and records source graph hash, tool/version,
resolution, colour space and every approximation; the original graph remains canonical.

USD export creates a `UsdShadeMaterial` with an `mtlx` render context referring to the packaged `.mtlx`
by `sourceAsset` and `subIdentifier`. A universal UsdPreviewSurface context is emitted only from exact
or explicitly baked mappings. Material assignments use `UsdShadeMaterialBindingAPI` and non-overlapping
`materialBind` GeomSubsets. Result display arrays are typed primvars with their validity data; canonical
result values and their units/provenance remain separate. A conversion manifest lists every exact,
baked and unsupported feature (E-110, E-111).

Omniverse is a consumer of that USD package, never a required backend or source of truth. Compatibility
tests pin the OpenUSD/MaterialX/Omniverse tuple under test. MaterialX-to-MDL output is derivative and may
be discarded and regenerated (XC-178).

## Preview and non-rendering material data

Every Material Asset revision owns one transparent-background rendered thumbnail and a reproducible
preview recipe: test geometry, renderer/version, lighting environment/hash, camera, colour configuration
and generated time. A data-dependent Material may bind the versioned synthetic scalar fixture for its
library thumbnail and labels it `サンプルデータ`. A selected object's live preview uses real bindings;
an unresolved requirement produces diagnostic magenta. A thumbnail is never material truth.

Appearance classification names and tags are descriptive only. Density, elastic modulus, Poisson
ratio, yield strength, temperature dependence and other engineering properties are excluded from
CT-011 and belong to a separately unit- and provenance-bearing engineering-material contract. A
material named `steel` supplies no analysis property (XC-179).
