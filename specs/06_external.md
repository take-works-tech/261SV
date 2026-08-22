---
status: draft
updated: 2026-08-20
---

# External systems

Hardware, third-party libraries, services and the operating system - anything whose behaviour this
product does not control. A spec that describes only the happy path of an external system delegates
the hard half of the work to the implementer, who will invent an answer.

### EXT-001 - VTK, embedded
- interface: the C++ and Python libraries, linked into the product's engine process
- version: **9.5.2**, pinned per release; readers are the reason this dependency exists
- pinned_in: pyproject.toml#vtk
- owned_by: Kitware; documentation at docs.vtk.org, source at github.com/Kitware/VTK
- licence: BSD 3-Clause - embedding in a closed commercial product is permitted, with the notice
  reproduced in the distributed binary (XC-041)
- decidedness: Fixed
- basis: E-051 (T1), E-060 (T1), E-002 (T1), E-003 (T1)
- correction: this line read "VTK 9.7.x, pinned per release" while the code pinned 9.5.2 and **every
  measurement behind LIM-002, LIM-004 and XC-049 was taken on 9.5.2**. The version a specification
  declares is not an intention; it is the version the evidence describes, and the two had drifted apart
  with nothing able to see it - check 7 compares `SYMBOL = literal` in source files and a pin in a
  package manifest is invisible to it (XC-185). Moving to 9.7.x is tracked as OPEN-019 because it
  invalidates three measured values and the module licence set, not because it is undesirable

| Failure mode | How it is detected | Required response |
|---|---|---|
| reader returns no cells or no fields | count after load | report the file as unreadable by the named reader; create no partial @Case (ingest/AC-022) |
| reader crashes the process on a malformed file | engine process exits | the crash is contained to the engine process, the interface survives, and the file is named (XC-047) |
| a field arrives with an unexpected association | association check on load | refuse rather than convert silently (INV-003) |
| memory exhausted while reading | allocation failure | report the size that failed against LIM-001, keep the @Workspace intact |

### EXT-011 - NumPy, the array type every value passes through
- interface: the Python library, and `vtkmodules.util.numpy_support`, which is how a @Field crosses
  between VTK's arrays and this product's own types without being copied element by element
- version: 2.3.4
- pinned_in: pyproject.toml#numpy
- owned_by: the NumPy Developers, under Scientific Python ecosystem governance
- licence: BSD 3-Clause for the source, but the **published wheel declares
  `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`** for code it vendors, so the notices file of
  XC-025 takes four further entries beyond the one a reader of the repository would expect
- decidedness: Fixed
- basis: E-118 (T1), E-119 (T1)

| Failure mode | How it is detected | Required response |
|---|---|---|
| NaN arriving from the library where the product means "missing" | the missing-value marker is NaN by construction (`src/domain_core/dataset.py`) | a NaN produced by an arithmetic accident and a NaN meaning "never sampled" are indistinguishable once mixed, so a computation that can produce the first checks for it at the point it happens rather than reading the result later (XC-001, INV-011) |
| silent dtype promotion or downcast across an operation | the declared @Stored precision no longer matches the array | refuse rather than report; a value shown to more digits than its source supports is the defect INV-014 exists to prevent |
| integer overflow on a count or index | fixed-width integer types wrap without raising | counts and indices are integer types end to end and are range-checked at the boundary, never carried through a float (INV-015) |
| allocation failure on a large field | `MemoryError` | report the size that failed against LIM-001 and keep the @Workspace intact, as for any read that exceeds the budget |
| a behaviour change between minor versions | pinned version, compared against the specification by `validate/check_dependency_pins.py` | the pin moves in the same change as the specification, and any measured value taken on the old version is re-measured or marked (XC-185) |

### EXT-002 - OpenUSD and OpenVDB, embedded for export
- interface: the USD and VDB libraries, used to write the export path
- version: pinned per release
- owned_by: the Academy Software Foundation and the OpenUSD project; the NVIDIA OpenUSD Exchange SDK
  is available under Apache 2.0 if a higher-level writer is preferred
- licence: OpenUSD under the Tomorrow Open Source Technology License 1.0, which differs from Apache
  2.0 only in the trademarks section; OpenVDB under Apache 2.0; both redistributable
- decidedness: Fixed
- basis: E-005 (T1), E-006 (T1), E-007 (T1), E-110 (T1), E-111 (T1)

| Failure mode | How it is detected | Required response |
|---|---|---|
| a field cannot be represented in USD | writer rejects it | name the field and what was omitted; never write a silently reduced file |
| unit or up-axis metadata cannot be determined | declared unit missing | write the file with the axis and scale actually used and state that units were undeclared (XC-003) |
| MaterialX has features UsdMtlx cannot carry | per-feature conversion report | retain and package the original `.mtlx`; write only exact or approved-baked preview fallback; name every unsupported feature before writing |
| material assignments overlap | CT-004 target validation | refuse the USD material binding instead of relying on renderer precedence; valid assignments become non-overlapping `materialBind` subsets |
| the target application reads the file differently | out of our control | the exported file states the conventions it was written with, so a discrepancy is attributable |

### EXT-010 - MaterialX documents and dependencies, embedded as untrusted material input
- interface: the pinned official MaterialX 1.39.5 Python/C++ APIs, standard libraries, validator and
  shader generators; MaterialX files imported by the user are data, not executable extensions
- version: 1.39.5 implementation with 1.39 document contract and OpenPBR Surface 1.1.1 for newly
  authored PBR surfaces; every imported document states its own version
- owned_by: the Academy Software Foundation MaterialX and OpenPBR projects
- licence: Apache-2.0; shipped licence and notices generated from the actual package (E-115)
- decidedness: Fixed
- basis: E-108 (T1), E-109 (T1), E-114 (T1), E-115 (T1)

| Failure mode | How it is detected | Required response |
|---|---|---|
| document or included graph is invalid | official parser and `Document.validate` | preserve raw bytes and report `materialCompileFailed`; create no plausible graph |
| required texture/include/LUT is absent or changed | package index plus recorded SHA-256 | keep the binding failed and diagnostic magenta; name the exact URI/hash; never search elsewhere by basename |
| custom or future node is unknown to a backend | separate native VTK/vtk.js/USD capability manifests | classify `unsupported`, preserve it, and never replace it silently |
| URI, XInclude or symlink leaves the package | bounded resolver before parse/load | refuse the resource, attempt no network access and report the escaped logical URI without opening it |
| imported implementation contains target-language source | dependency inventory | preserve as inert source; never compile or execute it unless it is a shipped trusted implementation |

### EXT-003 - Blender, reached one way
- interface: none. The product writes USD; the user opens it in Blender
- version: not pinned - the product targets the USD format, not a Blender release
- owned_by: the Blender Foundation
- licence: Blender is GPL v3 or later and its Python API is stated to be an integral part of the
  software. The product therefore ships no Blender code, no `bpy`, and no script that calls it
- decidedness: Fixed
- basis: E-010 (T1), E-011 (T1)

**The reasoning rests on the GPL, not on Blender's FAQ.** The product copies no Blender code, links to
nothing of Blender's, and distributes no Blender binary or `bpy`; a licence is only needed for acts the
copyright holder controls, and writing a USD file is not one of them. The FAQ's four conditions are
often quoted as a safe harbour, but a product that only writes a file does not meet the fourth of them
- it never executes Blender - so quoting them would weaken the argument rather than support it.

Two consequences remain. **A convenience script that imports `bpy` must be distributed under a
GPL-compatible licence** if it is distributed at all; the obligation arises on distribution, not on
internal use. And bundling the Blender binary is permitted by the FAQ under GPL conditions, but it
would put the product in the position of a GPL redistributor with source-provision duties, so it is
declined for a different reason than the one first recorded: cost of compliance, not impossibility.

### EXT-009 - Solver, CAD and Blender applications, driven rather than embedded
- interface: each application's own Python API, SDK or command line, invoked as a separate process -
  **later release** (XC-091). The first release imports result files by drag and drop and nothing more
- version: every one of them changes its API between versions; the product pins nothing and reports what
  it found
- owned_by: the vendor of each application
- decidedness: Bounded
- open: OPEN-012

| Failure mode | How it is detected | Required response |
|---|---|---|
| the application is absent, or its licence is not available | invocation fails | say which application and which licence, and leave the @Workspace unchanged |
| the API changed between versions | call fails or returns an unexpected shape | report the version found and what was expected; never guess a compatible call |
| a run produces no result file | expected output missing after completion | the @Case is marked failed with what the application reported, and downstream units skip (XC-095) |
| CAD geometry imports with no units declared | no unit in the file | treated as undeclared, never assumed to be millimetres (XC-003) |

**This product never computes the analysis itself**, in this release or any later one. It drives
applications that do, and reads what they wrote.

One saved @Simulation may group the explicit conditions for one or more invocations of these external
applications (XC-154). The adapter, input references, parameter bindings, execution identity and produced
files remain distinguishable in provenance; grouping runs never turns the external solver into embedded
product logic.

### EXT-004 - Solver file formats
- interface: files written by solvers the product never runs
- version: format versions are recorded per reader in [09_technology.md](09_technology.md)
- owned_by: various; CGNS under a zlib-style licence, OpenFOAM under GPL
- decidedness: Fixed
- basis: E-012 (T1), E-013 (T1)

Reading a file written by GPL software creates no obligation - the obligation attaches to linking or
distributing that software's code, which this product does not do. **Naming OPENFOAM in product
material does carry an obligation**: the trade mark policy requires a disclaimer that the offering is
not approved or endorsed by OpenCFD.

### EXT-005 - NVIDIA Omniverse, optional
- interface: an optional rendering capability, reached through USD; not installed by default
- version: compatibility is pinned as an OpenUSD/MaterialX/Kit tuple; the first documented target is
  Kit 110 with OpenUSD 25.11 and MaterialX 1.39.3, while SOLVIA's canonical source remains MaterialX
  1.39 under its independently pinned implementation
- owned_by: NVIDIA
- decidedness: Fixed
- basis: E-009 (T1), E-041 (T1), E-113 (T1)

| Failure mode | How it is detected | Required response |
|---|---|---|
| no NVIDIA GPU or CPU present | capability probe at enable time | the option is offered but not enabled, and says which hardware it needs - never a failure at render time |
| the optional component is absent or damaged | load failure | the product runs complete without it, and says the optional path is unavailable (XC-004) |
| terms change | not detectable from inside | the notices file names the version and the terms it shipped under, so a change applies to future releases rather than retroactively |
| Omniverse cannot consume a canonical MaterialX feature | tuple compatibility test and USD conversion report | use only the exact/approved-baked UsdPreviewSurface fallback, or name the material unsupported; generated MDL never replaces canonical source |

**Redistribution is permitted, and the first reading of these terms here was wrong.** The documentation
had already said so (E-008); the earlier conclusion weighted an unreconciled fee clause over an express
grant, which is how a conservative reading becomes an incorrect one. Section 1.1.2.2
expressly grants the right to sublicense and distribute the software as part of a customer product, and
the public release is classed as a free community product needing no subscription. The obligations are
attribution, usage reporting on request, and flow-down of terms to the end user.

**The binding constraint is hardware, not money.** Section 8.15 licenses execution only on systems with
NVIDIA GPUs or CPUs. In a corporate CAE environment a large share of seats are AMD or Intel, and remote
sessions are often CPU-only, so a required Omniverse path would refuse to run for those customers -
which is why it stays optional. Two further clauses shape what may be said publicly: 8.9 forbids
publishing benchmark or performance data, and 8.12 forbids use in developing a competing product.

The photorealistic path therefore rests on USD interchange, which runs anywhere, with Omniverse as an
optional capability for the customers whose machines qualify. XC-037 records the owner's decision to
ship it on those terms: **absent by default, stated at install, and never required by any function.**

### EXT-006 - Language model providers
- interface: HTTPS APIs, or a local model, configured by the user
- version: provider APIs change without our consent; the product pins a request shape and adapts
- owned_by: the provider the user chooses
- decidedness: Bounded

| Failure mode | How it is detected | Required response |
|---|---|---|
| unreachable or rate-limited | request failure | report it; every non-model operation continues (assistant/AC-015) |
| returns a value not present in the data | grounding check against the @Dataset | omit the statement rather than publish it (report/AC-012) |
| returns unparseable output | schema validation | retry once, then report; never partially apply (assistant/AC-004) |
| provider changes model behaviour between runs | not detectable from inside | the product never depends on model output being reproducible; reproducibility comes from the recorded command log (XC-046) |

### EXT-007 - Graphics hardware and drivers
- interface: the GPU through the renderer backend in use
- version: a minimum is stated per backend in [09_technology.md](09_technology.md)
- owned_by: the user's machine
- decidedness: Bounded

| Failure mode | How it is detected | Required response |
|---|---|---|
| no hardware acceleration available | context creation fails | name the backend that failed and offer one that runs (XC-004) |
| driver crash or device loss | context lost event | restore the @View from its definition rather than losing work (XC-012) |
| GPU memory exhausted | allocation failure | fall back to a reduced representation, marked as reduced (ingest/AC-030) |

### EXT-008 - Web search, when permitted
- interface: an HTTPS search API, or a local documentation index, configured by the user; **off by
  default and permitted per @Workspace** (XC-106)
- version: search APIs change and results are not reproducible between calls; the product treats a
  result as a **retrieved document with a date**, never as a stable reference
- owned_by: the provider the user chooses; the product ships no default key
- decidedness: Bounded

| Failure mode | How it is detected | Required response |
|---|---|---|
| not permitted, or offline | permission state, request failure | say what could not be answered without a search and produce the report without it; never fail the operation |
| returns nothing relevant | zero results, or none retained after filtering | state that nothing was found for the query shown; do not fall back to the model's memory (XC-105) |
| returns a page that later changes or disappears | not detectable later | the retrieved text is stored with the citation, so the report stays readable when the page does not |
| provider logs or profiles the query | not detectable from inside | the query is shown before it is sent, carries no workspace value or name unless allowed, and every request is in the audit (XC-106) |
| result contradicts the loaded data | grounding check against the @Dataset | carry the data value and state the disagreement (XC-013) |
