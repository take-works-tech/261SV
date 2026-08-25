---
status: draft
updated: 2026-08-25
---

# Technology

What this is built on, and why each piece was chosen over the alternatives. Selection order, applied
in this sequence and not by preference:

1. **An existing system that can be reused** rather than rebuilt
2. **Broad adoption in production inside companies**
3. **A credible support horizon** - release cadence, maintainers, governance, long-term support
4. **Fit for the requirement**

**Novelty is not a criterion.** Being new is a reason to wait: the failure modes have not been found
yet, and the path away from it does not exist.

### XC-040 - Stack
- language: Python for the engine, TypeScript for the interface
- framework: Electron shell over a local Python core process; React in the renderer
- data store: files on disk. No database ships with the desktop product
- build and packaging: electron-builder for the shell, a pinned Python environment for the engine
- reused rather than built: VTK provides the readers, the data model and the offscreen rendering that
  would otherwise be the entire first year of work
- decidedness: Fixed
- basis: E-002 (T1), E-024 (T1)

### XC-041 - VTK is embedded, and its default build carries obligations of its own
- statement: the product ships the published VTK wheel (XC-034). The optional modules IO/MySQL,
  IO/FFMPEG, IO/OCCT, IO/LAS and IO/PDAL are absent from it and stay absent; the gl2ps obligation is
  discharged by publication rather than by disabling the module; readers with open advisories are
  never invoked rather than removed (XC-047). The notices file is generated from the actual shipped
  files, not from VTK's install tree
- rationale: embedding is permitted, but "BSD-3 and nothing else" was wrong. Reading the 9.7.0 source
  release shows 27 core modules under the Sandia variant, whose notice must appear on **all copies**;
  and the default-on Rendering group pulls in a **modified** gl2ps, which obliges the distributor to
  publish the modified source. Turning off one export module removes that obligation entirely, which
  looked like the cheapest compliance decision - until the wheel showed it is not available without
  building VTK ourselves (XC-034)
- decidedness: Fixed
- basis: E-002 (T1), E-004 (T1), E-045 (T1), E-046 (T1), E-051 (T1)
- correction: the earlier version of this decision said copyleft entered only through modules that are
  off by default. That was false: gl2ps arrives through the default-on path. A guard written against
  the wrong list would have passed every build while the obligation stood

Obligations that the default closure creates, none of which are discharged by a copyright line:

| Component | What is required |
|---|---|
| VTK core (Sandia variant, 27 modules) | the notice and statement of authorship reproduced on all copies |
| gl2ps, as modified by VTK | the modified source made available - or the module disabled, which is this project's choice |
| FreeType | a statement in the product documentation crediting the FreeType Team |
| libjpeg-turbo | the Independent JPEG Group statement, required even when statically linked |
| Eigen (MPL-2.0) | recipients told how to obtain the source |
| scnlib (Apache-2.0, mandatory path) | the full licence text delivered |

**Measured here: the published wheel contains it.** A default `pip install vtk` lands
`vtkgl2ps`, `vtkIOExportGL2PS` and `vtkRenderingGL2PSOpenGL2` on disk, in a 393.8 MB install. So
"disable the module" is not a build flag we can pass to a wheel - it requires building VTK from source,
or accepting the modified-source obligation and publishing VTK's gl2ps patches. That cost is now an
open decision rather than an assumption (OPEN-011).

**Upstream's own practice is not the model.** The official VTK wheel ships VTK's copyright file alone,
with none of the vendored libraries' notices, and its install tree omits Eigen's MPL-2.0 text. Copying
what Kitware does would leave several of the rows above undischarged.

### XC-042 - Omniverse is not a shipped dependency
- statement: no Omniverse binary is redistributed; the photorealistic path is USD interchange, using
  the Apache-2.0 OpenUSD Exchange SDK where a higher-level writer helps
- rationale: section 8.15 licenses execution only on systems with NVIDIA GPUs or CPUs, so a required
  dependency would refuse to run for every AMD, Intel and CPU-only seat. Redistribution itself is
  expressly permitted (E-041), so this is a reach decision, not a legal one
- decidedness: Fixed
- basis: E-009 (T1), E-041 (T1)
- correction: an earlier version of this decision said redistribution was blocked by fees. That was
  wrong - section 1.1.2.2 grants distribution as part of a customer product, and the public release
  needs no subscription. The decision is unchanged; the reason is not, and a reason that does not hold
  gets a decision reversed for the wrong cause later

### XC-043 - Gaussian splatting uses a commercially licensed implementation, if it ships at all
- statement: if splat display ships, it uses gsplat (Apache-2.0) for training and Spark (MIT) or an
  equally licensed renderer for display; the Inria and MPII reference implementation is never used
- rationale: that reference implementation forbids commercial use outright, and it is the one almost
  every tutorial starts from - which is exactly how it ends up in a product by accident
- decidedness: Fixed
- basis: E-014 (T1), E-015 (T1)

### XC-044 - WebGL2 ships, WebGPU is opt-in
- statement: the in-application 3D view renders through vtk.js on WebGL2 by default; WebGPU is
  selectable and marked experimental
- rationale: vtk.js shares VTK's data model and vendor, so a scientific renderer does not have to be
  rebuilt on a general-purpose 3D engine; but the WebGPU backends of both vtk.js and native VTK are
  documented as experimental, with volume mappers and textures unimplemented. Shipping the
  experimental path by default would make every rendering bug ours to explain
- decidedness: Fixed
- basis: E-016 (T1), E-017 (T1), E-018 (T1), E-019 (T1)

### XC-044b - Three pieces added after this file was first written
- statement: the **expression evaluator** (XC-101) is this product's own and runs without a Python
  interpreter, so a formula evaluates identically whether or not scripting is enabled; the **scripting
  sandbox** (XC-102) runs user or agent Python in a separate process under the capability limits of
  XC-089; and **egress** (MOD-014) is the only module that opens a connection, which is what makes
  "what leaves this machine" a directory rather than a search
- rationale: each of the three was decided in a feature discussion and none of them was a technology
  choice recorded here, which is how a stack description silently stops describing the stack
- decidedness: Fixed
- basis: E-065 (T1)

### XC-045 - The engine is a local process, not a library in the shell
- statement: the Python engine runs as a separate process bound to the loopback interface; the
  interface talks to it over the same protocol whether it is local or remote
- rationale: it keeps the desktop and web products one codebase (XC-032), it contains a reader crash
  to a process the interface can restart, and it avoids passing gigabyte arrays through the shell's
  IPC, which copies. JupyterLab Desktop is the same shape and demonstrates the packaging is possible
- decidedness: Fixed
- basis: E-024 (T1)

### XC-046 - The command log is the reproducible artefact, not the model
- statement: every operation is recorded as a replayable command sequence; language models produce
  commands, never results, and reproducibility is a property of the log
- rationale: providers state that determinism is not guaranteed even with a fixed seed, and the
  current Model Context Protocol states that tool annotations are hints that must not be relied on for
  safety. A product whose reproducibility depends on a model has no reproducibility. Recording
  operations as a replayable script is what ParaView already does
- decidedness: Fixed
- basis: E-030 (T1), E-031 (T1), E-032 (T1)

### XC-047 - The reader surface is treated as hostile input
- statement: files are parsed in the engine process with no network access and limited filesystem
  reach; formats whose readers carry unfixed advisories are disabled by default and named in the
  release notes
- rationale: four heap-overflow and use-after-free advisories at CVSS 7.5 affect the VTK glTF loader
  with no fixed version indicated. The product's users open files sent to them by customers, which is
  the definition of untrusted input, and waiting for upstream is not a strategy
- decidedness: Fixed
- basis: E-033 (T1)

### XC-048 - USD is written by this product, not by VTK's exporter
- statement: the export path writes UsdGeomMesh with point data as vertex-interpolated primvars and
  cell data as uniform primvars, states `metersPerUnit` and `upAxis` explicitly in every file, and
  emits float32 for values Blender cannot read as double or int64
- rationale: VTK's own USD exporter writes neither the unit nor the axis and bakes scalars into vertex
  colour, which destroys exactly the thing this product exists to preserve. And USD's defaults are
  centimetres and Y-up, so a file that omits them does not mean "unspecified" - it means centimetres
- decidedness: Fixed
- basis: E-040 (T1)

## Material architecture

CT-011 MaterialX is the canonical rendering-material graph. The engine pins MaterialX 1.39.5, loads
the official 1.39 standard libraries and authors new PBR surfaces against OpenPBR Surface 1.1.1. The
official Python bindings own document creation, parsing, validation and upgrade into a new immutable
revision; `mxvalidate` and target shader generation run in CI. Received `.mtlx` bytes and dependencies
are retained and content-hashed separately from the parsed graph, because reserialising XML is not an
identity operation (XC-174, XC-178).

MaterialX values and connections are never translated into a second persistent VTK-property model.
MOD-003 derives a per-backend Material IR and capability report at runtime. Native VTK and vtk.js are
separate targets and every required feature is `exact`, `baked` or `unsupported`; no lowest-common-
denominator schema erases richer source. Result inputs are resolved before shader generation into
validity-bearing display attributes and standard geometry-property access. Imported shader source code
is data, not executable authority (XC-175, XC-178).

USD remains transport rather than the material source of truth. Its `mtlx` render context points at the
packaged source by `sourceAsset` and `subIdentifier`; a universal UsdPreviewSurface graph is a declared
exact/baked fallback, and SOLVIA identity is written independently of UsdMtlx conversion. The tested
compatibility matrix records the full OpenUSD, MaterialX, standard-library and consumer versions. The
first Omniverse target row is Kit 110's documented OpenUSD 25.11/MaterialX 1.39.3 tuple; it does not
change the engine's canonical version and any generated MDL stays derived (E-110, E-113).

### XC-049 - Every reader ParaView has, offered from the first release; the guarantee is staged
- statement: the product ships the VTK build whole, so **everything ParaView can open, this product
  opens** - 184 reader classes, measured on the shipped wheel. What is staged is not whether a file
  opens but what is promised about it: **Verified** formats carry regression tests in this product and
  their defects are ours to fix; **Offered** formats open through the same reader ParaView uses, with
  the reader's own known gaps named at load time; **Absent** formats have no reader anywhere and are
  named so nobody waits for one
- rationale: reader parity is nearly free because it is the same code, and refusing to open a file the
  underlying library can read would be an invented limitation. But a promise is not free: the vendor of
  those readers classifies several as minimal support and scopes its own paid maintenance by a format
  list. Offering everything while promising selectively is the only combination that is both useful and
  true
- decidedness: Fixed
- basis: E-034 (T1), E-035 (T1), E-060 (T1)

| Level | First release | What it means |
|---|---|---|
| **Verified** | CGNS, EnSight Gold, Exodus/IOSS, VTK XML and VTKHDF, STL | a regression test in this product opens a real file and asserts values; a defect here is a defect of ours |
| **Offered** | everything else the shipped VTK build reads - OpenFOAM (serial and parallel), Fluent (`.cas` and CFF), LS-DYNA, Tecplot, Plot3D, CONVERGE, GAMBIT, MFIX, SLAC, NetCDF family, Xdmf, H5Part, and the rest of the 184 | opens through the reader ParaView uses; where that reader is documented as minimal, the gaps are named in the interface at load rather than discovered later |
| **Absent** | Abaqus ODB, MED/Salome | no reader exists in VTK or ParaView; the user converts outside the product, and the specification says so rather than implying a future release |

**Two gaps between "ParaView opens it" and "VTK opens it"** are worth stating precisely, because parity
claims usually hide them. First, ParaView ships readers of its own that are not in VTK - its Nastran
BDF reader is one, and it interprets five keywords. Matching those means porting them, one at a time,
and each becomes ours to maintain. Second, a few ParaView capabilities are application-level rather
than library-level - plot-over-line is a ParaView filter, not a VTK class - so they are rebuilt rather
than inherited. Neither is a reason to narrow the promise; both are reasons to write the promise about
VTK's readers rather than about ParaView's menu.

**What may be embedded is decided by the licence on the part, not by the name on the box** (XC-250).
"Omniverse" is not one thing: **PhysX, the MDL SDK and Warp are BSD-3 or Apache-2.0 with no hardware,
field-of-use or competing-products restriction** (E-148, E-149, E-150), while the **Kit SDK and
everything requiring it - the RTX and IndeX paths, and `kit-cae` - may not be distributed at all**, must
be published through NVIDIA's own channels, and carry a prohibition on developing competing products
(E-151, E-152). `kit-cae` is the case worth knowing: NVIDIA publishes OpenUSD file-format plugins for
CGNS, EnSight, VTK and OpenFOAM that compose result files **without converting them** - this product's
subject exactly - on a runtime this product cannot ship. What is takeable from it is the idea.

**That is a maintenance decision and it was being read as a legal one.** ParaView is BSD-3-Clause
(E-147), so its readers and filters may be embedded here on the same terms as VTK. XC-248 settles what
to do with that: a **reader** ParaView has and VTK does not is worth copying in with its notice when a
customer's format needs it, because a format is a fixed target and the cost ends; an application-level
**filter** is rebuilt rather than copied, because it is behaviour this product will change, and a copied
implementation diverges on the first change and then carries somebody else's structure forever.

## Analysis capability, in stages

The same principle applies to what can be computed: the filters are present in the shipped build - 23
of the 24 common families - so the staging is about what is exposed, verified and reported honestly.

| Stage | Capability |
|---|---|
| First release | contour, clip, slice, threshold, glyph, calculator, cell-to-point and point-to-cell conversion, integrate variables with Gaussian quadrature (INV-009), resample between meshes with disclosure (XC-038), temporal statistics |
| Next | stream tracing, connectivity, decimation controls exposed to the user, gradient and derived-quantity fields |
| Later | anything requiring a filter this product would have to write rather than configure |

Every capability in the first-release row needs a verification entry before it is exposed, because a
filter that produces a number is a filter that can produce a wrong one.

## Dependencies

Every row carries a licence, evidence of adoption, and a support horizon. A blank cell is the question
nobody asked before taking on the dependency (check 20).

| Dependency | Purpose | Licence | Adoption evidence | Support horizon | Alternative rejected |
|---|---|---|---|---|---|
| VTK | readers, data model, offscreen rendering | BSD-3-Clause (E-002) | ParaView, 3D Slicer, PyVista build on it; 3.66 M PyPI downloads in 30 days | Kitware maintains it commercially; 9.7.0 released 2026-08-15 | writing readers for 100+ formats, which is the product's whole first year |
| NumPy | the array type every field value is held and computed in, and the boundary VTK's own `numpy_support` hands data across | BSD-3-Clause, **and the published wheel additionally declares 0BSD, MIT, Zlib and CC0-1.0** for code it vendors (E-118) | pinned at 2.3.4 and imported by `src/engine/reader.py`; VTK ships `vtkmodules.util.numpy_support` against it | six releases in the three months to 2026-08-09; SPEC 0 drops support for a core dependency 2 years after its release (E-119) | Python lists and `array`: no typed n-dimensional buffer, so every field would be copied element by element across the VTK boundary |
| vtk.js | in-browser scientific rendering | BSD-3-Clause (E-016) | declared dependency of OHIF Viewers, cornerstone3D, MONAILabel, VolView (E-017) | 211 commits from 18 accounts in six months, same vendor as VTK | three.js and Babylon.js: general 3D engines with no cell arrays, point/cell association or lookup tables - the scientific data model would be ours to rebuild |
| Electron | desktop shell | MIT | JupyterLab Desktop, VS Code and others ship Python or servers inside it (E-024) | 8-week major cadence, latest three majors supported | Tauri: the size advantage disappears once VTK is bundled, and its Linux WebKitGTK path documents white windows and lost WebGL contexts - unacceptable when 3D is the product |
| React | interface | MIT | ubiquitous in commercial desktop and web products | Meta-maintained, long deprecation cycles | - |
| MaterialX 1.39.5 | canonical rendering-material graph, validation and shader generation | Apache-2.0 (E-115) | ASWF standard with Python/JavaScript bindings and DCC/renderer integrations (E-108) | ASWF governance; exact version and standard library pinned together | VTK properties: runtime-only and not interchange; opaque custom shaders: no portable graph or dependency contract |
| OpenPBR Surface 1.1.1 | default PBR surface definition for newly authored MaterialX | Apache-2.0 (E-115) | ASWF reference model included by MaterialX 1.39.5 (E-109) | ASWF governance; version recorded per Asset | UsdPreviewSurface alone: broader preview subset but insufficient as the rich canonical graph |
| OpenUSD | export interchange | TOST 1.0, Apache-2.0 except trademarks (E-005) | the interchange format Blender, Omniverse and DCC tools read | Academy Software Foundation governance | glTF: no volumetric or simulation-field story |
| OpenVDB | volumetric export | Apache-2.0 (E-006) | Academy Software Foundation project, used across VFX | ASWF governance | - |
| OpenUSD Exchange SDK | higher-level USD writing | Apache-2.0 (E-007) | NVIDIA-published, redistributable | NVIDIA; optional, replaceable by OpenUSD directly | writing USD by hand for every schema |
| NVIDIA MDL SDK | translating this product's MaterialX graph into what NVIDIA's renderers consume | BSD-3-Clause (E-149) | NVIDIA's own SDK, open-sourced 2018 and maintained since | NVIDIA; version pinned when adopted | writing an MDL emitter here: the language is NVIDIA's and the SDK is the reference |
| NVIDIA Warp | GPU data-processing kernels from Python, if adopted | Apache-2.0 (E-150) | NVIDIA's own; `kit-cae` uses it for CAE visualisation algorithms (E-152) | NVIDIA | hand-written CUDA, which is a second language in the build |
| NVIDIA PhysX | not used today; listed because it is available on the same terms | BSD-3-Clause (E-148) | NVIDIA's own, GPU kernels included since 2025 | NVIDIA | - |
| gsplat | Gaussian splat training, if shipped (OPEN-016) | Apache-2.0 (E-015) | 654 commits from 25 contributors in six months | active, with a migration guide from the non-commercial implementation | the Inria reference implementation: non-commercial only (E-014) |
| electron-builder | packaging, signing, updates | MIT | the default packaging path for Electron products | active | hand-rolled installers per platform |

**Adoption evidence must be checkable** - a named product whose manifest declares the dependency, or a
release history. A vendor claiming wide adoption is tier T3 and cannot justify a Fixed choice.

## Licences

- distribution model: a signed desktop installer, and later a hosted service; both are binary
  distribution, so copyleft obligations attach to what is linked, not to what is read
- licences not acceptable here: GPL and LGPL in anything linked into the product. LGPL is excluded not
  because it is impossible but because satisfying it in a single-file desktop bundle requires relinking
  provisions that a one-person vendor will get wrong
- attribution: generated from the dependency manifest into a file shipped beside the executable and
  shown in the application (XC-025)

## Development environment

- required tool versions: pinned in a lock file per language, and checked by a script the build runs
- build: one command produces the platform installer; the same command runs in CI
- run: the shell and the engine start together in development, and the engine is startable alone for
  headless work (assistant/REQ-004)
- test: unit and integration in the engine, end-to-end through the shell
- environment variables: none required for normal operation. A product that needs environment
  variables to start cannot be installed by its intended user
