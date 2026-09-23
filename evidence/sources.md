---
status: draft
updated: 2026-09-23
---

# Sources

Every Fixed value cites an entry here. Tier T3 may never justify a Fixed value, and the linter enforces
it - so a number with no traceable source cannot reach the spec, whoever wrote it.

| Tier | What qualifies |
|---|---|
| T1 | Licence texts, vendor *documentation*, standards, public filings and statistics, published datasets, a measurement taken here, and the product owner's own stated decisions |
| T2 | Analysis that names its method and its underlying source, and can be traced back to T1 |
| T3 | Vendor marketing, press releases, unattributed figures, blog summaries with no source, AI-generated summaries |

### E-001 - Product brief from the owner
- tier: T1
- url: evidence/source-notes/prior-research.txt and evidence/source-notes/product-brief.txt in this repository, plus the owner's clarifications of 2026-08-19
- verified: 2026-08-19
- says: the product definition, the Workspace/Case/Variable hierarchy, the four work areas, the
  delivery model (desktop first, web second), the LLM operation requirement, and the decisions that
  VTK and Omniverse are embedded in the product while Blender is reached one-way by exporting USD
- justifies: CT-003, CT-004, CT-005, CT-006, CT-007, CT-008, CT-009, GL-016, GL-022, GL-017, GL-018, GL-019, XC-088, GL-001, GL-002, GL-003, GL-004, GL-005, GL-006, GL-007, GL-008, GL-010, GL-012, GL-013, GL-014, GL-015, GL-020, MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, MOD-007, MOD-008, MOD-009, MOD-010, CT-001, CT-002, XC-001, XC-002, XC-003, XC-004, XC-005, XC-007, XC-010, XC-011, XC-012, XC-013, XC-014, XC-015, XC-030, XC-031, XC-032, XC-060, XC-061, XC-062, INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, GL-021, GL-009

An estimate stays an estimate however often it is cited: re-citing a labelled estimate does not promote
it to T2. Record the method, the inputs and the assumptions next to the number, and mark it as an
estimate. If available sources cannot settle a question, that is a finding to report, not a gap to fill
with a plausible number.

## Licences

### E-002 - VTK licence text
- tier: T1
- url: https://github.com/Kitware/VTK/blob/master/Copyright.txt
- verified: 2026-08-19
- says: VTK is BSD 3-Clause. Binary redistribution requires reproducing the copyright notice, the
  conditions and the disclaimer; there is no source-disclosure or copyleft obligation. Only using the
  authors' names to endorse a product is forbidden
- justifies: EXT-001, XC-040, XC-041

### E-003 - ParaView licence page and repository copyright
- tier: T1
- url: https://www.paraview.org/license/
- verified: 2026-08-19
- says: ParaView is BSD-3-Clause, chosen so that the widest audience including commercial
  organisations can use it royalty-free, and its third-party dependencies are stated to be permissive
  and BSD-3-compatible
- justifies: EXT-001

### E-004 - VTK optional modules with copyleft dependencies
- tier: T1
- url: https://api.github.com/repos/Kitware/VTK/contents/IO?ref=master
- verified: 2026-08-19
- says: VTK carries IO/MySQL, IO/FFMPEG, IO/OCCT, IO/LAS and IO/PDAL, all off by default; IO/MySQL
  depends on the GPL MySQL client library, so enabling it would impose GPL obligations on a closed
  product
- justifies: XC-041

### E-005 - OpenUSD licence
- tier: T1
- url: https://raw.githubusercontent.com/PixarAnimationStudios/OpenUSD/release/LICENSE.txt
- verified: 2026-08-19
- says: OpenUSD is under the Tomorrow Open Source Technology License 1.0, which states it differs from
  Apache License 2.0 only in section 6, Trademarks, and is otherwise identical including the patent grant
- justifies: EXT-002

### E-006 - OpenVDB licence
- tier: T1
- url: https://raw.githubusercontent.com/AcademySoftwareFoundation/openvdb/master/LICENSE
- verified: 2026-08-19
- says: OpenVDB is Apache License 2.0, moved from MPL 2.0 in 2020
- justifies: EXT-002

### E-007 - NVIDIA OpenUSD Exchange SDK licence
- tier: T1
- url: https://docs.omniverse.nvidia.com/usd/code-docs/usd-exchange-sdk/latest/docs/licenses.html
- verified: 2026-08-19
- says: the OpenUSD Exchange SDK is Apache 2.0 and none of its third-party dependencies are GPL or
  LGPL, so it may be redistributed inside a commercial product
- justifies: EXT-002, XC-042

### E-008 - NVIDIA Omniverse licensing documentation
- tier: T1
- url: https://docs.omniverse.nvidia.com/ov/latest/common/NVIDIA_Omniverse_License_Agreement.html
- verified: 2026-08-19
- says: as of May 2026 the documentation states Omniverse is freely available for development and
  production use with no NVIDIA AI Enterprise subscription required
- justifies: XC-042

### E-009 - NVIDIA Product Specific Terms for AI Products
- tier: T1
- url: https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/
- verified: 2026-08-19
- says: the binding terms last modified 2026-04-15 include Omniverse with Kit under NVIDIA AI
  Enterprise, still condition the licence grant on payment of applicable fees, and in section 8.15
  licence the proprietary components solely to run on systems with NVIDIA Platforms; 8.12 forbids use
  in developing competing products and 8.9 forbids publishing benchmark or performance data
- justifies: XC-042

### E-010 - Blender licence and integration FAQ
- tier: T1
- url: https://www.blender.org/support/faq/
- verified: 2026-08-19
- says: Blender binaries are distributed under GPL v3 or later and the Python API is stated to be an
  integral part of the software. Licensing your own product freely is permitted only if all four
  conditions hold: it operates outside Blender, uses no Blender source code or API including the
  Python API, generates data for Blender, and runs Blender to process it
- justifies: XC-031, EXT-003

### E-011 - bpy package licence
- tier: T1
- url: https://pypi.org/pypi/bpy/json
- verified: 2026-08-19
- says: the bpy package, Blender as a Python module, declares GPL-3.0
- justifies: XC-031

### E-012 - CGNS library licence
- tier: T1
- url: https://raw.githubusercontent.com/CGNS/CGNS/develop/license.txt
- verified: 2026-08-19
- says: the CGNS library is under a zlib/libpng-style licence permitting use, modification and
  redistribution for any purpose including commercial applications, subject only to not
  misrepresenting the origin, marking modified versions, and keeping the notice
- justifies: EXT-004

### E-013 - OpenFOAM licence and trade mark policy
- tier: T1
- url: https://openfoam.org/licence/
- verified: 2026-08-19
- says: OpenFOAM is GPL and distributing binaries built from its source obliges the distributor to
  make source available; the OpenCFD trade mark policy requires a disclaimer when a product not from
  OpenCFD refers to OPENFOAM
- justifies: EXT-004

### E-014 - Gaussian splatting reference implementation licence
- tier: T1
- url: https://github.com/graphdeco-inria/gaussian-splatting/blob/main/LICENSE.md
- verified: 2026-08-19
- says: the Inria and MPII reference implementation forbids commercial use, exploitation and
  distribution without prior written consent
- justifies: XC-043

### E-015 - Commercially usable Gaussian splatting implementations
- tier: T1
- url: https://github.com/nerfstudio-project/gsplat
- verified: 2026-08-19
- says: gsplat is Apache-2.0 with 654 commits from 25 contributors in the last six months and carries
  a migration guide from the Inria implementation; Spark, a three.js splat renderer, is MIT with 146
  commits from 11 contributors in the same period
- justifies: XC-043

## Rendering and platform

### E-016 - Scientific web renderer, release and maintenance record
- tier: T1
- url: https://api.github.com/repos/Kitware/vtk-js
- verified: 2026-08-19
- says: vtk.js is BSD-3-Clause, released v36.8.3 on 2026-08-18, with 211 commits from 18 accounts in
  the last six months, maintained by Kitware - the same vendor as native VTK
- justifies: XC-044

### E-017 - vtk.js production adopters
- tier: T1
- url: https://github.com/OHIF/Viewers
- verified: 2026-08-19
- says: vtk.js appears as a declared dependency of OHIF Viewers, cornerstone3D, MONAILabel, VolView
  and itk-vtk-viewer - checkable adoption rather than a vendor claim
- justifies: XC-044

### E-018 - WebGPU implementation status and default limits
- tier: T1
- url: https://github.com/gpuweb/gpuweb/wiki/Implementation-Status
- verified: 2026-08-19
- says: WebGPU is on by default in Chrome on Mac, Windows and ChromeOS since v113, on Linux only for
  Intel Gen12+ from v144 and NVIDIA Wayland from v147, and in Firefox on Windows from v141; default
  limits include a 128 MiB maximum storage-buffer binding and a 256 MiB maximum buffer size
- justifies: LIM-003, XC-044

### E-019 - WebGPU backends are experimental in both VTK layers
- tier: T1
- url: https://docs.vtk.org/en/latest/modules/vtk-modules/Rendering/WebGPU/README.html
- verified: 2026-08-19
- says: the native VTK WebGPU rendering module is documented as highly experimental, with volume
  mappers and textures listed as not implemented
- justifies: XC-044

### E-020 - Browser-scale visualisation measurement
- tier: T2
- url: https://www.sci.utah.edu/~will/papers/teraweb-ldav20.pdf
- verified: 2026-08-19
- says: a peer-reviewed measurement, IEEE LDAV 2020, computed a 137.5 million triangle isosurface in a
  browser via WebGPU on an RTX 2070 in 526 ms and rendered it at 1280x720 and 30 frames per second
- justifies: LIM-002

## Packaging and distribution

### E-021 - Runtime and dependency sizes, measured
- tier: T1
- url: https://pypi.org/project/vtk/#files
- verified: 2026-08-19
- says: Electron v43.4.1 win32-x64 is 143.2 MB, the VTK 9.7.0 Python wheel for Windows amd64 is
  80.4 MB, and the ParaView 6.0.1 Windows MSI is 495.5 MB by HTTP content length
- justifies: LIM-004, XC-050

### E-022 - Windows signing requirements and reputation
- tier: T1
- url: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation
- verified: 2026-08-19
- says: unsigned and self-signed applications raise the SmartScreen warning, extended-validation
  certificates no longer bypass SmartScreen, reputation accrues over several weeks and hundreds of
  clean installations, and Smart App Control blocks unknown unsigned applications by default
- justifies: XC-051

### E-023 - Code-signing options available to an individual in Japan
- tier: T1
- url: https://learn.microsoft.com/en-us/azure/artifact-signing/faq
- verified: 2026-08-19
- says: Azure Artifact Signing public-trust certificates are available to individuals only in the
  United States and Canada while organisations in a list including Japan qualify; SSL.com individual
  validation certificates are USD 129 per year with eSigner cloud signing from USD 180 per year; the
  Apple Developer Program is USD 99 per year
- justifies: XC-051

### E-024 - Precedent for shipping Python inside an Electron application
- tier: T1
- url: https://api.github.com/repos/jupyterlab/jupyterlab-desktop/releases/latest
- verified: 2026-08-19
- says: JupyterLab Desktop ships an Electron shell with a Python environment, and its 2026-07-22
  installers are the measurable artefact of that architecture
- justifies: XC-045, XC-050

## Market and pricing

### E-025 - Pure-play CAE vendor revenue from filings
- tier: T1
- url: https://data.sec.gov/api/xbrl/companyconcept/CIK0001013462/us-gaap/Revenues.json
- verified: 2026-08-19
- says: Ansys FY2024 revenue was USD 2.545 billion with Japan at 7.3 per cent; Altair FY2024 revenue
  was USD 665.8 million across more than 13,000 customers with Japan at 6.4 per cent
- justifies: XC-070

### E-026 - Upper bound on the pre- and post-processing category
- tier: T1
- url: https://www.sec.gov/Archives/edgar/data/813672/000081367225000024/cdns-20241231.htm
- verified: 2026-08-19
- says: Cadence reports BETA CAE, the largest CAE pre- and post-processing vendor, as under 2 per cent
  of FY2024 consolidated revenue for the seven months from acquisition, annualising to under USD 159
  million
- justifies: XC-070

### E-027 - Published prices in this category
- tier: T2
- url: https://www.cts.com.au/Tecplot%20Prices.pdf
- verified: 2026-08-19
- says: Tecplot 360 lists a single-user annual licence at USD 3,330, a perpetual licence at USD 7,860
  and maintenance renewal at USD 1,820 per year, while EnSight, Ansys Discovery, SimScale paid tiers
  and Ceetron publish no prices at all
- justifies: XC-071

### E-028 - The report capability already exists free
- tier: T1
- url: https://www.kitware.com/exporting-paraview-scenes-to-paraview-glance/
- verified: 2026-08-19
- says: ParaView has exported scenes into a standalone ParaView Glance HTML file since 5.7.0 in 2019,
  and 6.0.0 released 2025-08-01 can generate a standalone viewer with network access disabled
- justifies: XC-072

### E-029 - Japanese CAE engineer population
- tier: T1
- url: https://www.jsme.or.jp/cee/uploads/sites/3/2026/05/date2_1_kotai2025.pdf
- verified: 2026-08-19
- says: cumulative passes of the JSME computational mechanics engineer certification from 2003 to 2025
  total 14,128 across three fields
- justifies: XC-070

## Assistant and control surface

### E-030 - Model Context Protocol, current specification
- tier: T1
- url: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- verified: 2026-08-19
- says: the 2026-07-28 revision removed protocol-level sessions and the initialize handshake, and the
  tools specification states that all properties in tool annotations are hints which must not be
  relied on for safety decisions when the server is not trusted
- justifies: XC-046

### E-031 - Language models cannot provide determinism
- tier: T1
- url: https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter
- verified: 2026-08-19
- says: with a fixed seed the system makes a best effort to sample deterministically and determinism
  is explicitly not guaranteed
- justifies: XC-046

### E-032 - Recording operations as a replayable script is established practice
- tier: T1
- url: https://docs.paraview.org/en/latest/Tutorials/SelfDirectedTutorial/batchPythonScripting.html
- verified: 2026-08-19
- says: ParaView records interface operations as a Python script through its Python Trace feature,
  which can then be replayed in batch
- justifies: XC-046

### E-033 - Vulnerabilities in the reader surface
- tier: T1
- url: https://osv.dev/list?ecosystem=&q=vtk
- verified: 2026-08-19
- says: four heap-overflow and use-after-free advisories at CVSS 7.5 affect the VTK glTF loader up to
  and including 9.5.0, and as of the 2026-08-12 update no fixed version is indicated
- justifies: XC-047

## Corrections from adversarial verification (2026-08-19)

These entries exist because an independent check refuted or narrowed an earlier conclusion. They are
kept separate so that the correction, not just the corrected text, is on the record.

### E-041 - Omniverse redistribution is expressly permitted
- tier: T1
- url: https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/
- verified: 2026-08-19
- says: section 1.1.2.2 of the Product Specific Terms expressly grants the right to sublicense and
  distribute the software as part of a Customer Product, subject to the attribution in 1.7.1, the
  usage reporting in 1.7.2 and flow-down to end users; the NVIDIA Software License Agreement of
  2026-05-07 classes the public Omniverse release as a Free SDK / Community Product needing no
  subscription. The surviving restriction is 8.15, which licenses execution only on systems with
  NVIDIA GPUs or CPUs
- justifies: XC-042, EXT-005

### E-042 - A narrower primary source for BETA CAE revenue
- tier: T1
- url: https://www.sec.gov/Archives/edgar/data/813672/000081367224000037/0000813672-24-000037-index.htm
- verified: 2026-08-19
- says: Cadence's CFO commentary of 2024-07-22 states approximately USD 40 million of FY2024 revenue
  from BETA CAE at the midpoint - about 0.86 per cent of the year, annualising to roughly USD 69
  million, which is a far narrower figure than the under-2-per-cent internal-controls scoping
  statement that annualises to USD 159 million
- justifies: XC-070

### E-043 - Independent visualisation vendors are small
- tier: T1
- url: https://www.proff.no/selskap/ceetron-as/trondheim/
- verified: 2026-08-19
- says: Ceetron AS and Ceetron Solutions AS, the independent 3D CAE visualisation component vendors,
  report FY2025 revenue of NOK 26.8 million and NOK 23.3 million respectively - together about USD 5
  million
- justifies: XC-070

### E-044 - What a support contract actually promises
- tier: T1
- url: https://www.kitware.com/support/
- verified: 2026-08-19
- says: Kitware's support agreement disclaims any warranty as to results attained and fitness for
  purpose, caps liability at the lesser of fees paid and USD 10,000, defines an issue as a
  reproducible deviation from documented behaviour, and counts notifying the customer that an issue is
  a known unresolved problem as resolving it
- justifies: XC-072

### E-045 - What a default VTK build actually contains
- tier: T1
- url: https://vtk.org/files/release/9.7/VTK-9.7.0.tar.gz
- verified: 2026-08-19
- says: reading the 284 module definitions in the 9.7.0 source release shows the default build is not
  uniformly BSD-3-Clause: 27 core modules carry the Sandia variant, whose notice must be reproduced on
  **all copies** rather than in documentation, three carry a LANL variant, and DICOMParser is
  BSD-4-Clause. The default-on Rendering group pulls in gl2ps through IO/ExportGL2PS, and VTK ships a
  **modified** gl2ps - symbols mangled, using VTK's own zlib, png and glad - which under the GL2PS
  licence obliges the distributor to make the modified source available
- justifies: XC-041

### E-046 - Notice obligations beyond reproducing a copyright line
- tier: T1
- url: https://gitlab.kitware.com/vtk/vtk/-/tree/master/ThirdParty
- verified: 2026-08-19
- says: in the default closure, FreeType's licence requires a statement in the distribution
  documentation that the software is based in part on the work of the FreeType Team; libjpeg-turbo
  requires the equivalent Independent JPEG Group statement when statically linked; Eigen is MPL-2.0
  across 301 files, requiring recipients to be told how to obtain source; and scnlib, on the mandatory
  CommonCore path, is Apache-2.0, requiring the full licence text
- justifies: XC-041, XC-025

### E-047 - Upstream practice is not a compliance model
- tier: T1
- url: https://pypi.org/project/vtk/#files
- verified: 2026-08-19
- says: the official VTK wheel ships only VTK's own BSD copyright file and no third-party notices,
  and its metadata records the licence simply as BSD - so the vendored libraries' obligations are not
  discharged by copying what upstream does, and VTK's own install tree omits the MPL-2.0 text for Eigen
- justifies: XC-025

### E-048 - What the free HTML export path drops, measured
- tier: T1
- url: https://github.com/Kitware/vtk-js/issues , https://kitware.github.io/paraview-glance/
- verified: 2026-08-19
- says: a measured export of a 1,128,448-point surface produced a 35.5 MB scene file and a 48.5 MB
  standalone HTML in about 19 seconds; vtk.js does not serialise text actors or point labels, and
  VTK's JSON scene exporter writes only props that are vtkActor, silently discarding vtkActor2D -
  scalar bars, text and legends - without a warning; Glance's own documentation scopes it to small to
  medium data, and ParaView's standalone-HTML option is disabled when exporting time series
- justifies: XC-072, report/REQ-001

### E-049 - The paid alternatives are not licence-free for the recipient
- tier: T1
- url: https://ansyshelp.ansys.com/
- verified: 2026-08-19
- says: Ansys Dynamic Reporting requires a legally licensed Ansys product; the Siemens STAR-CCM+ web
  viewer is a hosted viewer requiring a STAR-CCM+ licence and its own format; VCollab requires a Pro
  licence and a server - none of them is a single file a recipient opens with nothing installed
- justifies: XC-072

### E-050 - Why public buyers say they pay
- tier: T1
- url: https://sam.gov/
- verified: 2026-08-19
- says: United States federal sole-source justifications record the Air Force citing Tecplot for best
  capability and interoperability with existing investment, and NASA citing FieldView as having no
  other known product performing the same functionality - organisations with free ParaView available
  renewing commercial post-processing licences on capability grounds
- justifies: XC-072

### E-052 - How the GL2PS obligation is discharged
- tier: T1
- url: https://raw.githubusercontent.com/Kitware/VTK/master/ThirdParty/gl2ps/vtkgl2ps/COPYING.GL2PS
- verified: 2026-08-19
- says: the GL2PS licence requires that modifications be licensed on the same terms and that their
  source be made available "either on the same media as you distribute any executable or other form of
  this software, or via a mechanism generally accepted in the software development community for the
  electronic transfer of data" - a published source archive for the exact version satisfies the second
  branch, and VTK's modified gl2ps is already published by Kitware
- justifies: XC-034

## Formats, units and numerical fidelity

### E-034 - Kitware's own format support levels
- tier: T1
- url: https://www.kitware.com/terms/PVCoveredFileFormats.pdf
- verified: 2026-08-19
- says: Kitware classifies OpenFOAM, Fluent Case, Fluent CFF, NASTRAN, Nastran BDF and all Tecplot
  formats as minimal support - features unimplemented and not sufficiently tested - in its own
  published support-level document
- justifies: EXT-004, ingest/REQ-015

### E-035 - Readers that do not exist
- tier: T1
- url: https://github.com/Kitware/VTK/tree/master/IO
- verified: 2026-08-19
- says: of 202 reader headers under VTK IO, none reads Abaqus ODB, MED/Salome or Nastran natively;
  the ParaView Nastran BDF reader interprets five keywords and counts everything else as unsupported
- justifies: EXT-004

### E-036 - Units are absent from the file by design
- tier: T1
- url: https://cgns.org/standard/SIDS/array.html
- verified: 2026-08-19
- says: CGNS is the only common CAE format whose standard can fully specify units, through DataClass,
  DimensionalUnits, DimensionalExponents and DataConversion, and all of them are optional; VTK's CGNS
  reader reads none of them, reading only ReferenceState
- justifies: GL-020, XC-003

### E-037 - High-order elements survive reading but not display
- tier: T1
- url: https://raw.githubusercontent.com/Kitware/VTK/master/IO/CGNS/vtkCGNSReaderInternal.cxx
- verified: 2026-08-19
- says: the CGNS reader maps TRI_6, QUAD_9, TETRA_10, HEXA_20 and HEXA_27 onto VTK's quadratic cells
  and arbitrary order onto Lagrange cells, so nothing is lost on read
- justifies: INV-009

### E-038 - Display and derived quantities run on linear approximations
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkDataSetSurfaceFilter.html
- verified: 2026-08-19
- says: surface extraction subdivides non-linear cells at level 1 by default; contour and clip on
  high-order cells always split into linear sub-cells first; ParaView's integration defaults to a
  linear strategy and Gaussian quadrature must be selected explicitly, falling back to linear for
  cells it cannot handle
- justifies: INV-009, XC-010

### E-039 - Partitioned files duplicate points at the boundaries
- tier: T1
- url: https://raw.githubusercontent.com/Kitware/VTK/master/IO/XML/vtkXMLPUnstructuredDataReader.cxx
- verified: 2026-08-19
- says: the parallel XML reader performs no point merging between pieces - it propagates ghost levels
  only - so points on a partition boundary appear more than once, and integration excludes cells
  marked duplicate or hidden through the ghost array
- justifies: INV-009, ingest/REQ-012

### E-040 - USD defaults disagree with engineering conventions
- tier: T1
- url: https://openusd.org/release/api/group___usd_geom_up_axis__group.html
- verified: 2026-08-19
- says: USD defaults to metersPerUnit 0.01, that is centimetres, and an up axis of Y, while CAE and
  Blender work in Z-up; VTK's own USD exporter writes neither metersPerUnit nor upAxis and bakes
  scalars into vertex colour
- justifies: GL-021, XC-048

### E-051 - Measured here, on the target class of machine
- tier: T1
- url: spike/measure_export.py and spike/results.json in this repository
- verified: 2026-08-19
- says: for a surface of 1,127,844 points and 2,251,442 triangles carrying one float field, the free
  PyVista HTML export produced 34,398,358 bytes in 21.4 seconds; a text annotation and a point label
  added to the scene **did not appear in the exported file and no warning was raised**, while the
  scalar bar did. The same geometry as positions, indices and the field compressed to 16,149,246 bytes,
  so the export costs about 2.1 times the compressed floor. Decimating to 10 per cent produced 113,106
  points at 1,579,984 bytes but took 22 seconds. The installed VTK 9.5.2 wheel occupies 393.8 MB and
  contains vtkgl2ps, vtkIOExportGL2PS and vtkRenderingGL2PSOpenGL2
- justifies: LIM-002, LIM-004, LIM-006, XC-041, report/REQ-001

### E-053 - Dataset memory per point, measured here
- tier: T1
- url: spike/measure_capacity.py and spike/capacity.json in this repository
- verified: 2026-08-19
- says: a triangulated surface with one float field occupies 103.3, 103.7 and 103.8 bytes per point at
  40 thousand, 250 thousand and 810 thousand points - a stable ratio across the range, reported by VTK
  itself rather than inferred from process memory. An 8 GB budget therefore corresponds to roughly 77
  million points of this shape
- justifies: LIM-001

## Comparison, licensing and generated content

### E-054 - VTK fills points it could not sample with zero
- tier: T1
- url: https://raw.githubusercontent.com/Kitware/VTK/master/Filters/Core/vtkProbeFilter.cxx
- verified: 2026-08-19
- says: `vtkProbeFilter` initialises output arrays with `Fill(0)` and leaves that value in place for
  points that fall outside every source cell; the only indication is the separate `vtkValidPointMask`
  array. Point data is interpolated with the cell's own shape functions - linear barycentric for
  tetrahedra, trilinear for hexahedra with an iterative inverse mapping - while **cell data is not
  interpolated at all**: the containing cell's value is copied and becomes point data
- justifies: INV-011, XC-038

### E-055 - Round-trip interpolation error is a published protocol
- tier: T2
- url: https://onlinelibrary.wiley.com/doi/10.1002/nme.2951
- verified: 2026-08-19
- says: Alauzet and Mehrenberger use forward and round-trip interpolation error as an explicit
  evaluation protocol and state that interpolation error accumulates through a computation; Farrell and
  Maddison name the failings of consistent interpolation as suboptimality, non-conservation and
  unsuitability for discontinuous fields, proposing Galerkin projection instead
- justifies: XC-038

### E-056 - How comparable products handle mesh-mismatched comparison
- tier: T1
- url: https://www.ansys.com/products/fluids/ansys-ensight
- verified: 2026-08-19
- says: FieldView requires an explicit Dataset Sampling step before comparing across different meshes,
  returns non-finite values at unmatched vertices and reports matched and unmatched vertex counts;
  EnSight's case mapping warns that target nodes must lie inside the source geometry and makes the user
  choose what happens when they do not; Tecplot offers only "do not change" or "constant" for outside
  points, with no validity mask
- justifies: XC-038

### E-057 - Offline licensing patterns in comparable products
- tier: T1
- url: https://docs.cryptlex.com/
- verified: 2026-08-19
- says: engineering vendors split between a licence server (Altair units cannot be node-locked; Ansys
  binds increment lines to a server host id) and a signed offline licence file (Tecplot offers an
  activation code or a licence file; RLM embeds a public key in the application and signs licences).
  Clock-rollback detection produces false positives in practice - one vendor widened its threshold to
  about an hour for daylight saving. Single-developer products of comparable size bind per user rather
  than per machine and distribute keys offline
- justifies: XC-039

### E-058 - Sandboxing generated code is not a solved problem
- tier: T1
- url: https://restrictedpython.readthedocs.io/en/latest/
- verified: 2026-08-19
- says: RestrictedPython states in its own documentation that it is not a sandbox system or a secured
  environment; the author of pysandbox withdrew it as broken by design, arguing that Python should be
  run inside a sandbox rather than the reverse; and declarative grammars are not automatically safe -
  Vega's expression language compiles to JavaScript through the Function constructor and has a history
  of published sandbox-escape advisories
- justifies: XC-080

### E-059 - Functional Source License terms
- tier: T1
- url: https://raw.githubusercontent.com/getsentry/fsl.software/main/FSL-1.1-MIT.template.md
- verified: 2026-08-19
- says: the licence permits any purpose other than a competing use, naming internal use,
  non-commercial education and research, and professional services for compliant licensees. A
  competing use is making the software available commercially as a substitute for it, for another
  product the licensor offers using it, or with substantially similar functionality. Each released
  version converts to MIT on the second anniversary of its release
- justifies: XC-082

### E-060 - What the shipped VTK build can actually open, enumerated here
- tier: T1
- url: spike/enumerate_readers.py in this repository
- verified: 2026-08-19
- says: the installed VTK 9.5.2 wheel exposes 184 reader classes, including CGNS (with its file-series
  reader), every EnSight variant, OpenFOAM serial and parallel, both Fluent readers, Exodus serial and
  parallel, LS-DYNA serial and parallel, Tecplot binary and table, Plot3D, IOSS, CONVERGE, GAMBIT,
  MFIX, SLAC, the NetCDF family, HDF and VTKHDF, and Xdmf. Twenty-three of twenty-four common analysis
  filter families are present; the exception, plot-over-line, is a ParaView-level filter rather than a
  VTK one
- justifies: XC-049, EXT-004

### E-061 - Which formats the product can generate for itself
- tier: T1
- url: spike/enumerate_readers.py in this repository
- verified: 2026-08-19
- says: the shipped VTK build provides 102 writer classes. It can write EnSight, Exodus serial and
  parallel, IOSS, VTKHDF, the whole VTK XML family including partitioned forms, STL, PLY and OBJ. It
  has **no writer** for CGNS, Tecplot, LS-DYNA, OpenFOAM or Plot3D
- justifies: XC-085

### E-062 - Public CAE data mostly lacks a redistribution licence
- tier: T1
- url: https://cgns.org/current/examples.html
- verified: 2026-08-19
- says: the CGNS example files are described as submitted by users as is and certified by nobody but
  the sender, with no licence stated; the VTK data repository declares no licence through the platform
  API; and the NASA turbulence modelling resource states no usage terms on its landing page. None of
  them can be assumed redistributable inside a product or its repository
- justifies: XC-085

### E-063 - Interactive render cost, measured with proof of rendering
- tier: T1
- url: spike/measure_render.py and spike/render.json in this repository
- verified: 2026-08-19
- says: on integrated graphics at 1280x720, with every frame hashed and all twelve frames confirmed
  distinct, frame time including a per-frame framebuffer readback was 26 ms at 320 thousand triangles,
  34 ms at 1.6 million, 31 ms at 5.1 million and 49 ms at 11.5 million. The readback dominates: a
  36-fold increase in geometry raised frame time by less than double, and the intermediate points are
  not monotonic, so this establishes a floor rather than a curve. Subtracting the readback baseline,
  11.5 million triangles cost roughly 23 ms of rendering, about 43 frames a second
- justifies: LIM-002

### E-079 - Blender Outliner hierarchy and restriction controls
- tier: T1
- url: https://docs.blender.org/manual/en/4.2/editors/outliner/introduction.html
- verified: 2026-08-21
- says: Blender's Outliner represents stored scene data as a tree whose rows are data-blocks. A
  disclosure triangle expands contained data, each row carries a type icon and name, selection can be
  synchronized with the viewport, and restriction columns control visibility and selectability. Its
  header provides search and filtering; Shift applies a restriction toggle through descendants and
  Ctrl isolates a collection
- justifies: GL-042, XC-143, view/REQ-012

### E-080 - Owner-selected SOLVIA mockup shell
- tier: T1
- url: cae-saa-s/components/workspace/top-bar.tsx, cae-saa-s/components/workspace/library-view.tsx, cae-saa-s/components/workspace/viewport.tsx and cae-saa-s/components/workspace/scene.tsx in this repository
- verified: 2026-08-21
- says: the retained SOLVIA mockup establishes the product's light neutral panel palette, a two-row
  application header with File/Edit/View/Filter/Tools/Help menus, workspace versus library switching,
  panel toggles at the outer ends of the second toolbar, and a searchable card-based library whose
  preview viewport is 4:3 with cover-filled images from `cae-saa-s/public/thumbnails`. The owner
  clarified that its `Case list` label is wrong: the cards represent workspaces and the destination is
  `Workspace list`; the owner also selected those retained thumbnail fixtures for the design mockup,
  removed duplicate sidebar-local panel controls, and assigned new-workspace creation to Workspace list
  rather than a plus-button title row inside the open workspace. At browser-default desktop scale, the
  owner selected a four-card row for the Workspace list, and removed generic mode-assets headings from
  the right sidebars. The owner selected the retained viewport as the interaction reference for a
  temporary Three.js display in the UI mockup; product rendering remains governed separately by
  XC-044. The owner removed the static Dataset label from the Outliner header and the decorative frame
  and duplicate status footer around the mock 3D Canvas. The owner then requested more readable
  Outliner type and background separation, and removed the persistent `Shift`/`Ctrl` shortcut footer
  from its visible area. For Template sections, the owner selected one composition shared by View,
  Graph and Report: horizontal Sample/Original sources, text search and tag filtering, then an
  icon-labelled empty/result region; the owner clarified that Simulation has no right-sidebar
  Template tab and requested that tag search follow a conventional suggestion pattern. The owner
  subsequently requested that the upper-right XYZ gizmo enlarge both its letters and circular axis
  heads while retaining separation from the representation controls. The owner then requested a sort
  button in the shared Template panel, then extended the same Sample/Original, search, Tag and sort
  composition to View's Asset, Material, Background and Font; Graph's Style and Font; and Report's
  Layout, Style and Font sections. After separating working artefacts from reusable templates, the
  owner removed the persistent Template and Save-as-template buttons from the View, Graph and Report
  work-area headers and replaced them with one `+ New` action. The owner then separated reusable-resource
  browsing from current-state editing: Sample/Original, search, Tag, sort and thumbnails move to a
  centre-bottom material library above the instruction bar; the right rail retains its sections as
  properties, renaming Template to Overall; the shelf is collapsible, resizable and a narrow-width
  bottom drawer. Its bar remains labelled only `Material library` whether open or closed, shares the
  open row with category tabs, and toggles from the bar surface without intercepting those controls.
  The owner then replaced corner resize handles with the full shared boundary: the left sidebar's right
  edge, the right sidebar's left edge and the open material library's top edge. Dock orientation assigns
  horizontal resizing to sidebars and vertical resizing to the bottom shelf, whose width continues to
  follow the centre column. The owner also removed the adjacent one-row/multi-row icon as a redundant
  and unclear control, then required shelf dragging to track the pointer like sidebar dragging rather
  than jumping to a much larger height. The owner further required shelf expansion to stay inside the
  application viewport without creating application-level vertical scrolling, and replaced generic
  `New` with the explicit View, Graph or Report object name in each creation action. The owner then
  requested that the material-library dropdown indicator be placed near the material-library title.
  The owner fixed the centre-bottom natural-language instruction bar and full-height Chat mode as two
  UI positions for one feature, sharing the same conversation and history rather than separate chats.
  The owner required the library indicator to remain visible in both open and closed states, placed
  directly after its title, and placed Report Output last in its ordinary property-tab sequence. The owner
  then added Output last in Graph's sequence and clarified that neither tab is detached at the physical
  rail bottom. The owner removed the persistent Apply button from the central Graph display while keeping
  the material library's explicit non-drag Apply path distinct. The owner then added the explicit
  `New simulation` action to the Simulation work-area header alongside the existing named View, Graph and
  Report creation actions. The owner defined a Simulation as one saved flow grouping the conditions for
  one or more solver executions, required each Workspace to own multiple such flows, and kept Pipeline as
  the broader result-processing orchestration that may invoke a saved Simulation
- justifies: XC-143, XC-144, XC-147, XC-148, XC-149, XC-150, XC-152, XC-153, XC-154, GL-043, workspace/REQ-017, workspace/REQ-018, view/REQ-009, view/REQ-012, graph/REQ-010, assistant/REQ-013

### E-081 - Blender navigation gizmo placement
- tier: T1
- url: https://docs.blender.org/manual/en/latest/editors/3dview/navigate/introduction.html
- verified: 2026-08-21
- says: Blender places the navigation gizmo at the top right of the 3D Viewport; its orbit control
  reports orientation and the zoom, pan, camera and projection controls form a vertical navigation
  group beneath it
- justifies: XC-145

### E-082 - Maya ViewCube placement
- tier: T1
- url: https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-C1861E55-85FA-47F9-B4D2-71366875E56D
- verified: 2026-08-21
- says: Maya places its interactive ViewCube in the upper-right corner of the scene view, where it
  reports current camera orientation and provides direct access to standard and intermediate views
- justifies: XC-145

### E-083 - Blender Properties Editor navigation bar
- tier: T1
- url: https://docs.blender.org/manual/en/4.5/editors/properties_editor.html
- verified: 2026-08-21
- says: Blender groups context-sensitive properties into tabs shown as a vertical list of icons in a
  dedicated navigation-bar region. The bar can be placed on either side and tabs can be hidden for a
  workflow without changing the property content model
- justifies: XC-146

### E-084 - Windows adaptive navigation guidance
- tier: T1
- url: https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/navigationview
- verified: 2026-08-21
- says: Microsoft recommends top navigation for five or fewer peer categories and left navigation for
  five to ten. Its compact left mode keeps every category visible as an icon, but only when the
  categories can be represented clearly; expanded labels remain the alternative when icons are not
  self-explanatory
- justifies: XC-146

### E-085 - Fluent 2 Tag picker guidance
- tier: T1
- url: https://fluent2.microsoft.design/components/web/react/core/tagpicker/usage
- verified: 2026-08-21
- says: a Tag picker combines a text input and suggestion dropdown; typing filters system-provided
  options, choosing one inserts a visible tag, tags wrap when necessary, and deletion plus accessible
  input naming are part of the interaction
- justifies: XC-147

### E-086 - Carbon filterable multiselect and Tag guidance
- tier: T1
- url: https://carbondesignsystem.com/components/dropdown/usage/ and https://carbondesignsystem.com/components/tag/usage/
- verified: 2026-08-21
- says: a filterable multiselect is the pattern for choosing several predefined filtering values;
  typing narrows the menu, selections stay visible and clearable, and selectable or dismissible tags
  may represent active content filters
- justifies: XC-147

### E-087 - WAI-ARIA combobox with list autocomplete pattern
- tier: T1
- url: https://www.w3.org/WAI/ARIA/apg/patterns/combobox/
- verified: 2026-08-21
- says: an editable combobox exposes a popup list of suggestions filtered by input while retaining
  focus in the text field, with expanded state, active option, arrow-key navigation, selection and
  Escape behavior communicated through the combobox/listbox semantics
- justifies: XC-147

### E-088 - Working artefacts are distinct from reusable templates
- tier: T1
- url: https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-templates ; https://help.tableau.com/current/pro/desktop/en-gb/environ_workbooksandsheets.htm ; https://support.microsoft.com/en-us/word/save-a-word-document-as-a-template
- verified: 2026-08-21
- says: Power BI describes a report template as a starting point that creates a report, Word creates a
  separate document from a template, and Tableau stores multiple worksheets, dashboards and stories as
  concrete sheets inside one workbook. After reviewing those conventions, the product owner selected
  the same user-facing distinction for SOLVIA: a workspace owns multiple concrete Views, Graphs and
  Reports, while a Template is a reusable blueprint in workspace or shared scope. Applying a template
  creates an independent workspace item by default; later template edits do not silently alter it
- justifies: GL-008, GL-010, GL-015, GL-017, XC-090, XC-109, CT-001, CT-008, CT-009,
  workspace/REQ-010, workspace/REQ-012

### E-089 - Substance 3D Painter separates Assets from Properties
- tier: T1
- url: https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/interface/assets/assets ; https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/interface/properties ; https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/interface/interface
- verified: 2026-08-21
- says: Painter exposes Starter and user resources through an Assets window with filtering and an asset
  list, while its context-sensitive Properties window edits tool, brush and layer parameters. Interface
  panels can be resized, moved, hidden or docked rather than assigning both roles to one fixed sidebar
- justifies: XC-149

### E-090 - Blender Asset Shelf is contextual, bottom-integrated and row-snapped
- tier: T1
- url: https://developer.blender.org/docs/features/asset_system/user_interface/asset_shelf/
- verified: 2026-08-21
- says: Blender's Asset Shelf provides fast context-specific asset access inside an editor, usually at
  its bottom. Its main region shows thumbnail assets and snaps height to complete rows; its footer owns
  catalogues, filters and display options. Click and drag activation can be specialised by asset type
- justifies: XC-149

### E-091 - Blender reserves the full Asset Browser for organisation
- tier: T1
- url: https://docs.blender.org/manual/en/4.4/editors/asset_browser.html
- verified: 2026-08-21
- says: Blender's full Asset Browser is a distinct editor: the centre lists thumbnail assets, the left
  selects libraries and catalogues, and the right shows metadata for the active asset. Search filters
  names and tags, separating full organisation from the lighter embedded Asset Shelf
- justifies: XC-149

### E-092 - Blender resizes areas from their borders
- tier: T1
- url: https://docs.blender.org/manual/en/5.0/interface/window_system/areas.html
- verified: 2026-08-21
- says: Blender resizes an area by dragging the border between areas. It reserves corners for area
  docking, splitting and joining, so an ordinary size adjustment does not require a corner handle
- justifies: XC-149

### E-093 - WAI-ARIA Window Splitter pattern
- tier: T1
- url: https://www.w3.org/WAI/ARIA/apg/patterns/windowsplitter/
- verified: 2026-08-21
- says: A movable boundary between panes uses the separator role, an accessible label, the controlled
  pane, current/minimum/maximum values and directional arrow keys appropriate to its orientation
- justifies: XC-149

### E-094 - Contextual assistants use a compact entry and a right-side conversation surface
- tier: T1
- url: https://code.visualstudio.com/docs/agents/run/chat-view ; https://code.visualstudio.com/docs/chat/inline-chat ; https://help.autodesk.com/view/fusion360/ENU/?contextId=LEARNINGPANEL
- verified: 2026-08-21
- says: VS Code distinguishes quick contextual chat from its longer Chat view and supports placing Chat
  in the secondary sidebar, while Autodesk Fusion docks its assistant to the right of the canvas. After
  reviewing these current contextual-work patterns, the product owner selected three presentations for
  one SOLVIA conversation: a compact centre-bottom entry, a right overlay drawer during CAE work and
  full-height Chat for extended conversation. The drawer sits inside the centre surface so the existing
  right properties editor remains available, and only one composer is active at a time
- justifies: XC-151, assistant/REQ-013

### E-095 - Blender distinguishes working Objects from reusable Assets
- tier: T1
- url: https://docs.blender.org/manual/en/latest/scene_layout/object/introduction.html ; https://developer.blender.org/docs/features/asset_system/fundamentals/
- verified: 2026-08-22
- says: Blender describes geometry as Objects composed from object-level state and Object Data, with
  Object Data shareable between Objects. Its asset-system fundamentals separately describe Assets as
  entities packaged for organised sharing and reuse. After reviewing that distinction, the product
  owner selected the analogous SOLVIA boundary: Object names an instantiated selectable entity in a
  View, while Asset names a reusable library resource; Dataset remains source analysis data
- justifies: GL-018, GL-044, XC-159, XC-166, CT-008, view/REQ-020, workspace/REQ-017

### E-096 - OpenUSD face-varying primvars represent UV seams without changing mesh point identity
- tier: T1
- url: https://openusd.org/release/user_guides/primvars.html ; https://openusd.org/release/spec_usdpreviewsurface.html
- verified: 2026-08-22
- says: OpenUSD primvars carry surface-varying inputs such as texture coordinates. `faceVarying`
  interpolation supplies one value per face-vertex, supports indexed values and can represent a UV
  discontinuity at an edge without changing the Mesh point array; UsdPreviewSurface consumes texture
  coordinates through a primvar reader
- justifies: XC-167, view/REQ-021, CT-004

### E-097 - VTK generates projection coordinates as display-pipeline data
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkTextureMapToSphere.html
- verified: 2026-08-22
- says: VTK's texture-coordinate filters derive two-dimensional coordinates from input geometry
  through explicit sphere, plane or cylinder projections, with seam behaviour and model-coordinate
  dependence stated by the selected projection. The coordinates are filter output used for rendering,
  not source analysis values
- justifies: XC-167, view/REQ-021

### E-098 - Automatic atlasing is charting, parameterisation and packing, with seam cost
- tier: T1
- url: https://github.com/jpcy/xatlas
- verified: 2026-08-22
- says: xatlas generates unique texture coordinates by segmenting a mesh into charts,
  parameterising the charts and packing them into an atlas. Its primary documentation states that the
  output mesh may contain more vertices because UV seams duplicate vertices while retaining the same
  number of indices. This is materially different from mapping every input triangle to one identical
  right-triangle template
- justifies: XC-167, view/REQ-021

### E-099 - Fixed peer tabs and segmented choices normally use equal widths
- tier: T1
- url: https://m2.material.io/components/tabs/android ; https://developer.apple.com/design/human-interface-guidelines/segmented-controls
- verified: 2026-08-22
- says: Material Design defines fixed tabs as simultaneously visible peers of equal width, calculated
  from the available width or widest label, and uses content-width scrolling tabs when the set does not
  fit. Apple's Human Interface Guidelines likewise state that segments in one segmented control are
  usually equal in width and recommend consistent segment size, while limiting the number of segments
  that must be parsed in a wide interface
- justifies: XC-168, workspace/REQ-017

### E-100 - DCC applications assign materials to explicit objects or face sets
- tier: T1
- url: https://docs.blender.org/manual/en/latest/render/materials/assignment.html ; https://help.autodesk.com/cloudhelp/2023/ENU/Maya-LightingShading/files/GUID-D41AF807-F7CB-447E-BACC-7F0867C14E8D.htm
- verified: 2026-08-22
- says: Blender material slots bind a material to an object or selected faces and directs smooth
  material mixing to an explicit shader network; Maya likewise assigns a material to the selected
  objects or polygon faces from the viewport, Hypershade or Outliner. Neither treats dropping an
  arbitrary second material on the whole object as an unlabelled overlay. Blender presents an object's
  slots and active material in a compact List View with adjacent Add Material Slot and Remove Material
  Slot controls, and explicitly permits several slots for different object parts
- justifies: XC-169, XC-170, XC-177, view/REQ-022, view/REQ-023

### E-101 - Painter layers compose one texture-set material while selection remains explicit
- tier: T1
- url: https://helpx.adobe.com/substance-3d-painter/using/layer-stack.html ; https://helpx.adobe.com/substance-3d-painter/using/interface-overview.html ; https://helpx.adobe.com/substance-3d-viewer/interface/appearance-workspace.html
- verified: 2026-08-22
- says: Substance 3D Painter creates one Texture Set and layer stack for each imported material ID;
  masks, per-channel opacity and blend modes compose that stack into the final surface material.
  Substance 3D Viewer filters the Appearance panel by a part selected in the viewport and lets a
  material preset be dragged to a specific model part. The pattern separates target selection from
  material composition instead of making the current sidebar context ambiguous
- justifies: XC-169, XC-170, view/REQ-022, view/REQ-023

### E-102 - Material viewers use switchable neutral test geometry
- tier: T1
- url: https://help.autodesk.com/cloudhelp/2026/ENU/Maya-LightingShading/files/GUID-FAB13FA2-7068-4169-8D27-016B13E5C930.htm ; https://helpx.adobe.com/substance-3d-player/the-user-interface/panes.html
- verified: 2026-08-22
- says: Maya's live Material Viewer offers several swatch shapes including a sphere, while Substance
  Player previews a Substance on built-in primitive geometry including spheres and boxes and can also
  open arbitrary models. A neutral primitive is therefore a material-inspection surface, not evidence
  of the selected analysis object's geometry or values
- justifies: XC-170, view/REQ-022, view/REQ-023

### E-103 - Scientific pseudocolour and PBR material are distinct colour authorities
- tier: T1
- url: https://docs.paraview.org/en/latest/ReferenceManual/colorMapping.html ; https://docs.paraview.org/en/latest/ReferenceManual/advancedRendering.html
- verified: 2026-08-22
- says: ParaView maps a selected data array through a colour transfer function and exposes a legend
  that states the value-to-colour relationship. Its imported rendering materials are a separate
  surface-display path beyond standard solid or pseudocolour display; selecting no material leaves the
  standard colouring path in control. This supports keeping result colour and PBR base colour as
  separately named authorities rather than alpha-blending them without a declared rule
- justifies: XC-169, view/REQ-023

### E-104 - Blender uses one last-selected active object as the property context
- tier: T1
- url: https://docs.blender.org/manual/en/5.2/scene_layout/object/selecting.html ; https://docs.blender.org/manual/en/4.5/editors/properties_editor.html
- verified: 2026-08-22
- says: Blender distinguishes any number of selected objects from at most one active object. The last
  selected object is active, reselecting with Shift makes it active, and the Properties editor displays
  context-sensitive settings for that active object and its material. This provides a known
  multi-selection convention without introducing a second target selection inside each property tab
- justifies: XC-171, view/REQ-022, view/REQ-023

### E-105 - Blender material properties begin with a simple-scene preview and switchable shapes
- tier: T1
- url: https://docs.blender.org/manual/en/5.2/render/materials/preview.html
- verified: 2026-08-22
- says: Blender's Material Preview panel gives a quick view of the active material in a simple scene
  and switches the inspection object among named test shapes including plane, sphere and cube. This
  supports keeping a compact shape switcher adjacent to the preview instead of mixing it into the
  material parameter form
- justifies: XC-171, view/REQ-023

### E-106 - Substance material assets use generated transparent thumbnails
- tier: T1
- url: https://helpx.adobe.com/substance-3d-community-assets/guidelines/creating-thumbnails.html ; https://helpx.adobe.com/substance-3d-community-assets/desktop/the-different-asset-types-on-substance-3d-community-assets/substance-materials.html
- verified: 2026-08-22
- says: Adobe's Substance 3D asset guidance requires square static PNG thumbnails with transparent
  backgrounds for published resource previews and states that material thumbnails are generated
  automatically from the material render. Painter-created Shelf resources likewise carry their
  generated thumbnail. The thumbnail therefore communicates the surface appearance directly rather
  than representing every material with the same palette glyph
- justifies: XC-172, view/REQ-023

### E-107 - Blender names material regions by their purpose
- tier: T1
- url: https://docs.blender.org/manual/en/5.2/render/materials/index.html ; https://docs.blender.org/manual/en/5.2/render/materials/preview.html ; https://docs.blender.org/manual/en/5.2/render/materials/settings.html
- verified: 2026-08-22
- says: Blender's Material Properties documentation names concrete regions by purpose, including
  Preview, Surface and Settings, and reserves Material Slots for assigning materials to an object or
  faces. This supports purpose-specific labels inside an already named Materials tab and does not
  support adding a second generic appearance-slots heading around unrelated surface and result-colour
  controls
- justifies: XC-173, view/REQ-023

### E-108 - MaterialX is a typed material graph with geometry properties and preservable extensions
- tier: T1
- url: https://github.com/AcademySoftwareFoundation/MaterialX/blob/main/documents/Specification/MaterialX.Specification.md
- verified: 2026-08-22
- says: MaterialX 1.39 defines strongly typed nodes, inputs, outputs, node graphs, materials, variants,
  custom nodes and custom attributes. Its geometric properties are functionally equivalent to USD
  primvars, including user-defined varying properties read through `geompropvalue`. Applications that
  do not understand a custom attribute should preserve and re-output it, which permits a namespaced
  SOLVIA identity backlink without making that backlink shader data
- justifies: XC-174, XC-175, XC-177, CT-011, view/REQ-023, view/REQ-024

### E-109 - MaterialX 1.39.5 carries OpenPBR Surface 1.1.1 and its explicit opacity input
- tier: T1
- url: https://github.com/AcademySoftwareFoundation/MaterialX/releases/tag/v1.39.5 ; https://github.com/AcademySoftwareFoundation/OpenPBR ; https://github.com/AcademySoftwareFoundation/OpenPBR/blob/main/parametrization.md.html
- verified: 2026-08-22
- says: the current MaterialX release is 1.39.5 and updates its OpenPBR Surface definition to 1.1.1.
  OpenPBR supplies the portable surface model and defines `geometry_opacity` as a float in `[0, 1]`
  with default `1`. Exchange-framework concerns such as object-instance display opacity, mesh-edge
  overlays, texture association, geometry data and normal conventions remain outside that model and
  must be stated by the containing contract
- justifies: XC-174, XC-178, XC-180, CT-004, CT-011

### E-110 - OpenUSD can consume MaterialX but does not preserve every MaterialX feature
- tier: T1
- url: https://openusd.org/dev/api/usd_mtlx_page_front.html ; https://openusd.org/dev/api/class_usd_shade_node_def_a_p_i.html
- verified: 2026-08-22
- says: UsdMtlx maps MaterialX materials and graphs into UsdShade and supports shader source assets
  identified by `sourceAsset` and `subIdentifier`, but ignores or incompletely handles features including
  `attributedef`, geometry expressions, several geometry/property elements, general filename
  substitutions and locally source-code-implemented custom nodes. A valid MaterialX document may
  therefore load through UsdMtlx while losing unsupported semantics unless the original is retained
- justifies: XC-178, CT-011, view/REQ-008, view/REQ-024

### E-111 - USD resolves one material per surface or non-overlapping face subset
- tier: T1
- url: https://openusd.org/release/api/class_usd_shade_material_binding_a_p_i.html ; https://openusd.org/release/api/class_usd_geom_subset.html
- verified: 2026-08-22
- says: USD binds one resolved Material to a renderable primitive and uses `materialBind`
  `UsdGeomSubset` children for different face materials. The material-binding subset family is
  non-overlapping or a partition and must not be unrestricted, because one face cannot resolve to
  several independently bound materials
- justifies: XC-176, CT-004, view/REQ-023

### E-112 - Native VTK and vtk.js expose different PBR capability surfaces
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkProperty.html ; https://kitware.github.io/vtk-js/api/Rendering_Core_Property.html
- verified: 2026-08-22
- says: native VTK PBR accepts base-colour, ORM, normal, emissive, anisotropy and coat-normal textures
  with stated colour-space and tangent requirements, while vtk.js exposes a smaller property surface.
  Neither property model is a complete MaterialX interchange contract, so each is a versioned runtime
  adapter with its own exact, baked and unsupported capability report
- justifies: XC-178, CT-011, view/REQ-002, view/REQ-024

### E-113 - Omniverse consumes a version-paired OpenUSD and MaterialX stack
- tier: T1
- url: https://docs.omniverse.nvidia.com/dev-guide/latest/release-notes/110_0_highlights.html ; https://docs.omniverse.nvidia.com/materials-and-rendering/latest/templates/OpenPBR.html
- verified: 2026-08-22
- says: Kit 110 pairs OpenUSD 25.11 with MaterialX 1.39.3 and supports the
  `sourceAsset`/`subIdentifier` pattern. Its RTX paths translate MaterialX OpenPBR through MDL and
  document renderer-specific limitations, so Omniverse compatibility is tested as a version tuple and
  MDL output is a downstream derivative rather than SOLVIA's material source of truth
- justifies: XC-178, CT-011, view/REQ-008, view/REQ-024

### E-114 - MaterialX supplies Python document APIs, validation and shader generation
- tier: T1
- url: https://materialx.org/docs/api/class_document.html ; https://materialx.org/docs/api/_xml_io_8h.html ; https://materialx.org/Tools.html
- verified: 2026-08-22
- says: the official MaterialX library exposes document creation, validation, version upgrade and XML
  input/output through C++ and Python bindings, while ShaderGen generates target shader source from a
  graph and its upstream dependencies. This supports code-managed `.mtlx` sources and semantic tests;
  imported source bytes still need independent retention for lossless preservation
- justifies: XC-174, XC-178, CT-011, view/REQ-024

### E-115 - MaterialX and OpenPBR use Apache-2.0
- tier: T1
- url: https://github.com/AcademySoftwareFoundation/MaterialX/blob/main/LICENSE ; https://github.com/AcademySoftwareFoundation/OpenPBR/blob/main/LICENSE
- verified: 2026-08-22
- says: the upstream MaterialX and OpenPBR repositories each publish the Apache License 2.0, permitting
  use and redistribution subject to its notice and licence obligations
- justifies: XC-178, 09_technology.md

### E-116 - MaterialX's reference editor combines typed nodes, properties and a render view
- tier: T1
- url: https://github.com/AcademySoftwareFoundation/MaterialX/blob/main/documents/DeveloperGuide/GraphEditor.md
- verified: 2026-08-22
- says: the official MaterialX Graph Editor visualises, creates, loads and saves MaterialX graphs; its
  typed input and output pins permit only matching connections, a selected-node property editor changes
  values, and its render view updates from the edited graph. The graph, properties and render are views
  of the same MaterialX document rather than independent material copies
- justifies: XC-177, view/REQ-023

### E-117 - Transfer-function editors separate colour and opacity control points
- tier: T1
- url: https://docs.paraview.org/en/latest/ReferenceManual/colorMapping.html ; https://www.paraview.org/paraview-docs/latest/cxx/md__builds_gitlab-kitware-sciviz-ci_Documentation_release_ParaView-5_811_80.html ; https://docs.blender.org/manual/en/latest/interface/controls/templates/color_ramp.html ; https://vtk.org/doc/nightly/html/classvtkColorTransferFunction.html
- verified: 2026-08-22
- says: ParaView's official colour-map editor associates a transfer function with a selected array and
  component, presents independent colour and opacity control points, supports precise point values,
  range rescaling, interpolation and presets, and places opacity vertically over the scalar domain.
  Its 2D editor uses two scalar fields and editable coloured/opaque regions over a 2D histogram. Blender's
  official colour-ramp control independently confirms the stop pattern: add, remove, move, set exact
  position, colour, alpha and interpolation. VTK represents the colour mapping as ordered RGB control
  points, leaving SOLVIA to state its explicit alpha-zero behaviour outside the authored domain
- justifies: XC-177, view/REQ-023

### E-118 - NumPy licence, and what the published wheel actually carries
- tier: T1
- url: https://raw.githubusercontent.com/numpy/numpy/main/LICENSE.txt and https://pypi.org/pypi/numpy/json
- verified: 2026-08-22
- says: the repository licence file is BSD 3-Clause ("Copyright (c) 2005-2025, NumPy Developers"),
  requiring the notice, the conditions and the disclaimer to be reproduced in binary redistribution and
  forbidding use of the NumPy Developers' or contributors' names for endorsement. The **published
  package declares more than that**: its `License-Expression` metadata reads
  `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`, so the shipped wheel carries vendored code under
  four further licences whose notices are separate obligations - the same shape of finding as VTK's
  bundled gl2ps, FreeType and libjpeg-turbo (E-045, E-046)
- justifies: XC-040, XC-025

### E-119 - NumPy release cadence and support horizon
- tier: T1
- url: https://api.github.com/repos/numpy/numpy/releases and https://scientific-python.org/specs/spec-0000/
- verified: 2026-08-22
- says: six releases in the three months to 2026-08-09 - 2.4.4, 2.4.5 (2026-05-15), 2.4.6 (2026-05-19),
  2.5.0 (2026-06-21), 2.5.1 (2026-07-04) and 2.5.2 (2026-08-09) - so the project ships patch releases
  on a scale of weeks and minor releases quarterly. SPEC 0, the Scientific Python ecosystem policy
  NumPy follows, states that support for core package dependencies is dropped **2 years** after their
  initial release and for Python versions **3 years** after theirs
- justifies: XC-040

## Reference application structure, measured on this machine

The two products this design borrows from are installed here, so their structure was read from the
installation rather than from documentation about it. Both entries are measurements: the numbers below
came out of the running program, and the commands that produced them are recorded so the measurement
can be repeated.

### E-120 - Blender 5.0.1 shell, panel and command structure, read from the installation
- tier: T1
- url: `D:\dev\Blender Foundation\Blender 5.0` (build a3db93c5b259, 2025-12-16), enumerated with
  `blender.exe --background --factory-startup --python` over `bpy.types` and `bpy.ops`
- verified: 2026-08-22
- says: the shell is Window -> Screen -> Area -> Region. **19 space types** exist
  (VIEW_3D, IMAGE_EDITOR, NODE_EDITOR, SEQUENCE_EDITOR, CLIP_EDITOR, DOPESHEET_EDITOR, GRAPH_EDITOR,
  NLA_EDITOR, TEXT_EDITOR, CONSOLE, INFO, TOPBAR, STATUSBAR, OUTLINER, PROPERTIES, FILE_BROWSER,
  SPREADSHEET, PREFERENCES, EMPTY) and **16 region types**
  (WINDOW, HEADER, CHANNELS, TEMPORARY, UI, TOOLS, TOOL_PROPS, ASSET_SHELF, ASSET_SHELF_HEADER,
  PREVIEW, HUD, NAVIGATION_BAR, EXECUTE, FOOTER, TOOL_HEADER, XR). A registered panel declares
  `bl_space_type`, `bl_region_type`, `bl_category` and `bl_context`, and those four fields alone
  partition the 121 measured panel groups: the Properties editor subdivides its WINDOW region by
  `bl_context` into a vertical icon rail (object 26 panels, material 31, data 129, render 89,
  view_layer 40, scene 16, output 16, collection 6), while the 3D viewport subdivides its UI region by
  `bl_category` into Item, Tool and View tabs. The Outliner carries **7 display modes**
  (SCENES, VIEW_LAYER, SEQUENCE, LIBRARIES, DATA_API, LIBRARY_OVERRIDES, ORPHAN_DATA) and 34 further
  properties, of which 22 are filters; its restriction columns are individually toggled
  (`show_restrict_column_select/hide/viewport/render/holdout/indirect_only/enable`) and
  `use_sync_select` is what couples the tree to viewport selection. Display state is separated from
  data: `View3DShading` has 40 properties and `View3DOverlay` has 95, none of which are on the mesh.
  A material slot is four fields only - `link`, `material`, `name`, `slot_index`. The command surface
  is **2442 operators across 77 modules** (object 249, node 167, mesh 161, wm 117, outliner 72,
  view3d 67), and a key binding is a `KeyMapItem` of `idname` plus `type`, `value`, `ctrl/shift/alt/
  oskey/hyper`, `key_modifier`, `map_type`, `properties`, `active` and `is_user_modified`, held in one
  of **105 keymaps** scoped by area - so the same key means different things in different areas by
  construction rather than by convention. Asset metadata is 8 fields
  (`author`, `catalog_id`, `copyright`, `description`, `license`, `tags`, `active_tag`,
  `catalog_simple_name`), and unit handling is 8 (`system`, `system_rotation`, `length_unit`,
  `mass_unit`, `temperature_unit`, `time_unit`, `scale_length`, `use_separate`)
- justifies: XC-190, XC-191, XC-192, XC-193

### E-121 - ParaView 6.2.0 proxy, view and state structure, read from the installation
- tier: T1
- url: `D:\Program Files\ParaView 6.2.0`, enumerated with `pvpython.exe` over the proxy definition
  manager, and a saved `.pvsm` state produced by `SaveState` after `Wavelet` -> `Show` -> `ColorBy`
- verified: 2026-08-22
- says: everything is a **proxy** with typed properties, and a saved state is those proxies plus named
  `ProxyCollection`s. **1143 proxy definitions in 78 groups**: filters 279, sources 254,
  representations 78, writers 45, 3d_widgets 23, exporters 22, misc 21, extract_writers 20,
  **views 18**, implicit_functions 15. The 18 view types are RenderView, RenderViewWithEDL,
  ComparativeRenderView, OrthographicSliceView, MultiSlice, SpreadSheetView, XYChartView,
  XYBarChartView, XYPointChartView, XYHistogramChartView, QuartileChartView, BoxChartView,
  ParallelCoordinatesChartView, PlotMatrixView, ImageChartView, PythonView, ComparativeXYChartView and
  ComparativeXYBarChartView - so a table and a chart are views beside the 3D one, not features inside
  it. Property counts show where the complexity actually sits: RenderView 159, a geometry
  representation 222, XYChartView 130, ScalarBarWidgetRepresentation 66, PVLookupTable 34,
  SpreadSheetView 17, TimeKeeper 7, AnimationScene 22, SaveScreenshot 12, SaveAnimation 15. XYChartView
  carries a full four-axis model - bottom, left, top and right each with title, colour, log scale,
  range, custom labels, label notation and precision, and independent title/label typography - while a
  chart representation carries per-series `SeriesVisibility`, `SeriesColor`, `SeriesLabel`,
  `SeriesLineStyle`, `SeriesLineThickness`, `SeriesMarkerStyle`, `SeriesMarkerSize`, `SeriesOpacity`
  and `SeriesPlotCorner`. The colour map is its own proxy referenced by representations, with
  `RGBPoints`, `ScalarOpacityFunction`, `NanColor`, `UseAboveRangeColor`/`BelowRangeColor`,
  `UseLogScale`, `Discretize`, `IndexedColors`, `Annotations` and `AutomaticRescaleRangeMode`; the
  scalar bar is a separate representation with 66 properties of its own. Time is one `TimeKeeper` proxy
  holding `TimestepValues`, `TimeRange`, `Time` and the views it drives, and animation is a separate
  `AnimationScene` with cues. The 3D widgets are plane, box, sphere, line, spline, polyline, handle,
  slider, distance, protractor, cone, cylinder, annulus, frustum, coordinate frame and light
- justifies: XC-190, XC-191, XC-194, XC-195

### E-122 - The design catalogue's own type usage, counted
- tier: T1
- url: `mockups/ui/app/globals.css` and `mockups/ui/components/ui/*.tsx` at commit time, counted with
  `grep -o "font-size: [^;]*;" | sort | uniq -c` and the equivalent for family, weight, line height and
  letter spacing
- verified: 2026-08-23
- says: **368 `font-size` declarations carrying 20 distinct values** - 8px used 156 times, 9px 80, 7px
  60, 10px 28, 6px 14, 11px 9, and one or two each of 5, 12, 13, 14, 15, 17, 18, 19, 22, 24 and 27px,
  plus two `!important` overrides. Sixteen sites set type at **5px or 6px**, all of them inside the
  material property panel, so that panel runs a different type system from the rail it sits in.
  Separately, the shadcn primitives in `components/ui` set their own size through Tailwind:
  `text-sm` (14px) on Button, Input and SelectItem, `text-xs` (12px) on Badge, TabsTrigger and the small
  button, and `text-[10px]` on DropdownMenuItem - so a button renders at **14px beside an 8px label**,
  which is the visible mismatch. Two monospace stacks are spelled differently for one purpose,
  `"Cascadia Mono", Consolas, monospace` five times and `ui-monospace, "Cascadia Mono", Consolas,
  monospace` three times; one `Georgia, serif` appears once, in the report preview. `font-variant-numeric:
  tabular-nums` is set at **two** of the many places a number is displayed. Weight uses four values
  (700 forty-five times, 800 ten, 400 twice, 500 once), line height nine (1, 1.4, 1.45, 1.5, 1.55, 1.6,
  1.7, 1.75, 1.8) and letter spacing six (.025, .04, .08, .1, .14 em and -.03em)
- justifies: XC-201

### E-123 - How ParaView separates an interactive layout from a saved comparison
- tier: T1
- url: `D:\Program Files\ParaView 6.2.0`, proxy properties read with `pvpython` for
  `views/ComparativeRenderView`, `views/ComparativeXYChartView`, `misc/ViewLayout`,
  `misc/SaveScreenshot` and `animation/ComparativeAnimationCue`
- verified: 2026-08-23
- says: the two are different objects. **`ViewLayout`** - the interactive split of the central area -
  carries **three properties only**: `PreviewMode`, `SeparatorColor`, `SeparatorWidth`. It holds no
  per-pane meaning at all; what each pane shows is a property of the view dropped into it. It can still
  be exported as one image, because `SaveScreenshot` and `SaveAnimation` each carry `SaveAllViews`,
  `Layout`, `SeparatorColor` and `SeparatorWidth` beside their `View`. **`ComparativeRenderView`** is a
  view type of its own with 88 properties, of which only **two** are about comparison: `Dimensions`,
  the grid, and **`OverlayAllComparisons`**, a boolean that draws every member into one picture instead
  of a grid - so grid and overlay are one switch on one object rather than two features. What varies
  across the grid is declared, not configured per pane: a `ComparativeAnimationCue` names
  `AnimatedProxy`, `AnimatedPropertyName`, `AnimatedElement` and `AnimatedDomainName`, one cue per swept
  parameter. `ComparativeXYChartView` exposes the same `Dimensions` and nothing else comparison-specific.
  The cue also carries **`UpdateWholeRange`, `UpdateXRange` and `UpdateYRange`** beside `UpdateValue`,
  so a swept parameter is distributed across the grid as a **range divided among the cells** as well as
  by per-cell values: an ordered axis does not have to be enumerated by hand
- justifies: XC-202, XC-203

### E-124 - What a mature chart view actually exposes, counted in ParaView 6.2.0
- tier: T1
- url: `D:\Program Files\ParaView 6.2.0intkRemotingApplication-pv6.2.dll`, whose compiled proxy
  XML was read directly and the `XYChartViewBase`, `XYChartViewBase4Axes`, `XYChartRepresentationBase`
  and `XYChartRepresentation` elements extracted with their `<PropertyGroup>` labels
- verified: 2026-08-23
- says: the Line Chart View carries **65 properties in 13 named panel groups** for two axes, and the
  four-axis variant adds **50 more in 10 groups** - **115 properties in 23 groups** for one chart.
  **Twenty of the 23 groups are one pattern repeated per axis**: `<Axis>`, `<Axis> Title Properties`,
  `<Axis> Range`, `<Axis> Labels`, `<Axis> Label Properties`, identical for Left, Bottom, Right and Top,
  25 properties each. Only three groups are chart-wide: `Legend Properties`, `Annotation`, `Tooltip`.
  Per-axis, the settings are title, grid visibility and colour, axis colour, title font family/file/
  size/bold/italic/colour, log scale, custom range with minimum and maximum, label visibility, label
  notation and precision, custom labels, and the label font set. **Series appearance is keyed to the
  series, not to the chart**: the representation carries `SeriesVisibility`, `SeriesLabel`,
  `SeriesColor`, `SeriesOpacity`, `SeriesPlotCorner` and, in `Series Parameters` groups,
  `SeriesLineStyle`, `SeriesLineThickness`, `SeriesMarkerStyle`, `SeriesMarkerSize` - one value per
  series, addressed by series name, with `SeriesPlotCorner` choosing which axis pair a series is drawn
  against
- justifies: XC-213

### E-125 - Where Microsoft Office puts the properties of a selected chart element
- tier: T1
- url: https://support.microsoft.com/en-us/office/format-elements-of-a-chart-b6c787d5-f90a-41d2-a901-9d3ed9f0dbf0
- verified: 2026-08-23
- says: there is **one Format task pane**, opened from the element itself - "select a chart element,
  right-click it, and click Format <chart element>" - and it is contextual: "The **Format** pane appears
  with options that are tailored for the selected chart element", and "If you click on a different chart
  element, you'll see that the task pane automatically updates to the new chart element." Its sections
  are reached by **small icons at the top of the pane**, and the pane can be moved or resized. So the
  tabs of the pane are the facets of the **selected element**, not of the whole document, and the
  selection - not a tab - is how a user reaches an axis or a series
- justifies: XC-213

### E-126 - How a shipped LLM authoring tool sequences generation and review
- tier: T1
- url: https://support.microsoft.com/en-us/powerpoint/copilot/create-a-new-presentation-with-copilot-in-powerpoint
- verified: 2026-08-23
- says: the flow is prompt, then clarifying questions the user may answer or skip, then an **outline
  produced before any slides**: "Once Copilot has generated your outline, you can continue to chat with
  Copilot to refine your outline. When you're ready, you can let Copilot know to generate your slides."
  Generation happens on the user's word, not automatically. The vendor states in its own limitations
  that "The output of the Create a presentation feature is AI-generated content and should be
  human-reviewed and edited accordingly"
- justifies: XC-214

### E-127 - Where Canva and Gamma put insertion, selection properties and document theme
- tier: T1
- url: https://www.canva.com/help/glow-up-variantb/, https://www.canva.com/help/editor-tabs-missing/ and
  https://help.gamma.app/en/articles/11969695-how-do-i-style-cards-and-adjust-layout-settings-in-my-gamma
- verified: 2026-08-23
- says: **Canva** separates inserting from editing. The left side panel holds what can be added -
  templates, elements, fonts, Brand Kit, Draw, Projects, Apps - and its documentation lists the tabs a
  user may hide, "to help keep your editor view tidy": Photos, Audio, Videos, Background, Charts, Logos,
  Bulk create, Design, Text, Apps, Projects. The properties of a selection are not in a persistent rail:
  a fixed quick-actions toolbar sits below the header and "Just select an element and it'll suggest
  relevant editing options", while an edit panel opens with features specific to that element.
  **Gamma** splits appearance in two levels: a document-wide **Theme**, and per-slide styling that is
  "per-block", reached from the slide's own corner rather than from a global tab, exposing accent image
  and its placement, overlay style, intensity and colour, slide colour, full-bleed and content alignment
- justifies: XC-213, XC-214

### E-128 - How the measured references present a choice that is about appearance
- tier: T1
- url: `D:\Program Files\ParaView 6.2.0in\pqComponents-pv6.2.dll` and
  `C:\Program Files\Blender Foundation\Blender 5.0.0\datafiles`, both read on this machine
- verified: 2026-08-23
- says: **neither reference asks a user to choose an appearance from a list of words.** ParaView's
  colour-map chooser is built from `pqPresetDialog`, `pqPresetDialogTableModel`,
  `pqPresetDialogReflowModel` and **`pqPresetToPixmap`** - the last of which exists to render each preset
  into an image, and the reflow model to lay those images out as a grid rather than a list. Blender
  ships the previews as files: `datafiles/studiolights` holds **28 matcap, 5 studio and 9 world** image
  files, and `datafiles/icons` holds 147 preview data files, all drawn into the pickers that select
  them. The names are still shown beside the pictures in both
- justifies: XC-215

### E-129 - What this repository's plan actually permits, measured against the API
- tier: T1
- url: `gh api` against `take-works-tech/261SV` on 2026-08-23, and the reference design at
  `D:\dev\claude-agent-env-design\specsutonomous-dev-env-spec.md`
- verified: 2026-08-23
- says: **the three mechanisms a normal auto-merge is built on are unavailable here.**
  `GET /repos/.../rulesets` and `GET /repos/.../branches/main/protection` both answer **403 "Upgrade to
  GitHub Pro or make this repository public to enable this feature"**, re-measuring what OPEN-020
  recorded on 2026-08-22 for the write endpoints. New here: `PATCH /repos/...` with
  `allow_auto_merge=true` is **accepted and has no effect**: a subsequent read still returns `allow_auto_merge: false`, so GitHub's own auto-merge
  cannot be turned on. The GraphQL `repository.mergeQueue` is **null**. `gh secret list` and
  `gh variable list` are **both empty**, so `claude.yml` and `claude-code-review.yml` - which read
  `secrets.CLAUDE_CODE_OAUTH_TOKEN` - cannot run as written. Repository settings that *are* in effect:
  default branch `main`, squash merge allowed, merge commit allowed, rebase merge disallowed, delete
  branch on merge enabled.
  The reference design reaches the opposite conclusion about scope from the same problem: it defines
  autonomy levels **A0 propose-only, A1 auto-implement and open a ready pull request, A2 auto-merge
  limited to an allowlist of low-risk domains, A3 broad automation**, adopts **A0 to A2 only**, states
  **"A3 is never adopted"**, and gives as its central principle **"separate the freedom to create a PR
  from the authority to change main"**. Its stated reasons are goal drift over long horizons, the
  vendor's own "the action is powerful and occasionally wrong", and that a scheduled run reporting green
  means the session ended, not that the task succeeded
- justifies: XC-218

### E-130 - Which of the formats this build reads declares a frame or a unit at all
- tier: T1
- url: `D:\Program Files\ParaView 6.2.0intkcgns-pv6.2.dll` and the sibling `vtk*.dll`, read on
  this machine 2026-08-24
- says: **of the formats in this stack, CGNS is the one that declares a length unit.** Its library
  carries `vtkcgns_LengthUnitsName` and the enumeration values `Meter`, `Centimeter`, `Millimeter`,
  `Foot`, `Inch`, alongside `DataClass_t` and `DimensionalExponents_t` - a file can therefore say what
  its coordinates mean. Probing the same libraries for `Length_Unit`, `UnitSystem`, `up_axis`, `ZUp` and
  `metersPerUnit` found none of them, and `CoordinateSystem` appears only in the VTK-m acceleration
  modules, where it names a mesh's coordinate array rather than a declared frame. **The VTK XML formats
  this build reads - `.vtu`, `.pvtu`, `.vtp` - and STL declare neither an up axis nor a length unit**,
  which is why a file in one of them is assumed canonical and the assumption is recorded (ingest/AC-028)
  rather than read
- verified: 2026-08-24
- justifies: XC-230

## Not verified here

Recorded so that nothing silently depends on them:

- the revenue of Siemens Simcenter and Dassault SIMULIA, neither of which is disclosed separately
- how long an engineer currently spends assembling a result report: no first-hand or method-stated
  measurement was found. The claim that this step is the bottleneck rests on paid products continuing
  to sell exactly that step, which is circumstantial rather than measured
- **interactive rendering on the workstation class**: only the integrated-graphics class has been
  measured (E-063). The workstation row of LIM-002 is unmeasured, and extrapolating from a different
  class of hardware would produce a number that looks measured and is not
- the earlier failed attempts at rendering measurement are kept in `spike/measure_capacity.py`, which
  refuses to report rather than repeating them

### E-131 - The ghost vocabulary, and which bits an integral excludes
- tier: T1
- url: https://raw.githubusercontent.com/Kitware/VTK/master/Common/DataModel/vtkDataSetAttributes.h
- verified: 2026-08-24
- says: read first-hand from the VTK sources on 2026-08-24, together with
  `Common/DataModel/vtkFieldData.h`, `Filters/Parallel/vtkIntegrateAttributes.cxx`,
  `IO/XML/vtkXMLPUnstructuredDataReader.cxx` and `IO/ParallelXML/vtkXMLPDataObjectWriter.cxx`.
  (1) The ghost array is named `vtkGhostType` (`vtkFieldData::GhostArrayName`, one static returning that
  literal) and it is unsigned bytes of flags; the same name is used on point data and on cell data.
  (2) `PointGhostTypes` is DUPLICATEPOINT=1, HIDDENPOINT=2. `CellGhostTypes` is DUPLICATECELL=1,
  HIGHCONNECTIVITYCELL=2, LOWCONNECTIVITYCELL=4, REFINEDCELL=8, EXTERIORCELL=16, HIDDENCELL=32 - so
  **bit 2 means HIDDEN for a point and HIGH_CONNECTIVITY for a cell**, and the two vocabularies are not
  interchangeable although the arrays share a name.
  (3) `vtkIntegrateAttributes` skips a cell whose ghost byte has `DUPLICATECELL | HIDDENCELL` set and
  tests no other bit; it reads `GetCellGhostArray()` only and never consults the point ghost array.
  (4) `vtkXMLPUnstructuredDataReader.cxx` contains no locator and no merge step - grepping it for
  merge/locator returns nothing - confirming E-039 from the reader side.
  (5) The `GhostLevel` attribute a `.pvtu` carries is the writer's `UPDATE_NUMBER_OF_GHOST_LEVELS`,
  and `vtkXMLPDataObjectWriter` initialises it to **0**. At 0 no cell belongs to two pieces; only the
  points on the interfaces are repeated.
- justifies: INV-010, XC-231, XC-232

### E-132 - VTK's data object types, and what surface extraction does to a point set
- tier: T1
- url: spike/measure_object_types.py
- verified: 2026-08-24
- says: measured first-hand on 2026-08-24 by running `spike/measure_object_types.py` against **VTK
  9.5.2**, the pinned version (XC-185); the record is `spike/object_types.json`.
  (1) `vtkDataObjectTypes` names **50** types in 9.5.2, of which **10** are `vtkDataSet` subclasses -
  `vtkPolyData`, `vtkStructuredPoints`, `vtkStructuredGrid`, `vtkRectilinearGrid`,
  `vtkUnstructuredGrid`, `vtkImageData`, `vtkPointSet`, `vtkUniformGrid`, `vtkPath`,
  `vtkExplicitStructuredGrid` - **8** are `vtkCompositeDataSet` subclasses, and **17** more are
  instantiable data objects that are **neither**, including `vtkTable`, `vtkHyperTreeGrid`,
  `vtkUniformHyperTreeGrid`, `vtkMolecule`, `vtkCellGrid` and `vtkSelection`. A reader may therefore
  return something no `vtkDataSet` code path can accept, and `vtkHyperTreeGrid` - an AMR type this
  product's users meet - is one of them.
  (2) `vtkCellTypes` knows **64** cell types: 3 zero-dimensional, 8 curves, 21 surfaces, 32 volumes.
  (3) **Surface extraction is a different point set, not a subset.** A 3x3x3 block of points meshed as
  8 hexahedra has 27 points; `vtkDataSetSurfaceFilter` followed by `vtkTriangleFilter` yields **26**
  points and 48 triangles, and the origin of the first ten surface points is
  `0, 1, 10, 9, 3, 4, 12, 2, 11, 5` - neither the same count nor the same order. The point fields are
  carried through and re-indexed to the surface, so a field read from the original grid and geometry
  read from the surface disagree at every index.
  (4) The map back exists but is off by default: `PassThroughPointIdsOn()` and `PassThroughCellIdsOn()`
  add `vtkOriginalPointIds` and `vtkOriginalCellIds`, and without them nothing recovers which dataset
  point a display vertex was.
- justifies: INV-001, XC-233

### E-133 - What each reader in the pinned build hands back
- tier: T1
- url: spike/reader_output_types.json
- verified: 2026-08-24
- says: measured on 2026-08-24 by instantiating every class whose name ends in `Reader` across the
  `vtkIO*` modules of **VTK 9.5.2** and reading `GetOutputDataObject(0)`'s class name. 181 readers were
  probed; the record is `spike/reader_output_types.json`.
  (1) The most common output is **`vtkMultiBlockDataSet` (33 readers)**, ahead of `vtkImageData` (25),
  `vtkPolyData` (21), `vtkPartitionedDataSetCollection` (13) and `vtkUnstructuredGrid` (13). 15 could
  not be instantiated without a file and 14 create their output only during execution.
  (2) Of the 40 CAE readers listed in `spike/readers.json`, **19 return `vtkMultiBlockDataSet` and 6
  return `vtkPartitionedDataSetCollection`** - CGNS, Exodus (serial and parallel), every EnSight
  variant, OpenFOAM (serial and parallel), LS-DYNA (serial and parallel), both Fluent readers, Tecplot,
  IOSS, Plot3D and SLAC. Only **4** return a `vtkUnstructuredGrid` directly - GAMBIT, MFIX, NetCDF-CAM
  and NetCDF-UGRID - and 1 returns a `vtkTable`.
  So more than half of the readers for the formats this product's users work in return a composite, and
  a read path whose signature is `vtkDataSet` accepts none of them.
- justifies: CT-012, XC-234
### E-134 - Which decimator keeps the map back to the dataset
- tier: T1
- url: spike/measure_object_types.py
- verified: 2026-08-24
- says: measured on 2026-08-24 against **VTK 9.5.2**. A sphere triangulated to 489,300 points and
  977,200 triangles was given a `vtkOriginalPointIds` array and reduced to a tenth by each candidate
  decimator, with `SetTargetReduction(0.9)`.
  **`vtkDecimatePro`** (with `PreserveTopologyOn`, splitting off, boundary-vertex deletion off) returned
  49,560 points and 97,720 triangles in **2.63 s**, **carried `vtkOriginalPointIds` through**, and moved
  **none** of the surviving points - every one was bit-identical to its original position.
  **`vtkQuadricDecimation`** returned 48,990 points and 97,719 triangles in 4.31 s and **dropped the id
  array entirely**, so nothing remains that says which dataset point a surviving vertex was.
  The two are therefore not interchangeable on quality grounds: only one of them leaves a reduced
  surface able to answer a pick at all.
  Scale, for the caching question: this 977,200-triangle reduction took 2.63 s here, while the export
  spike measured 22.34 s to reduce a 2,251,442-cell mesh by the same fraction with the same filter
  (`spike/results.json`, `decimated_10pct`). Both are far above a frame.
- justifies: XC-235, ingest/TASK-015, ingest/TASK-017

### E-135 - How a file says which array is an identifier, and what a pedigree identifier may hold
- tier: T1
- url: spike/measure_object_types.py
- verified: 2026-08-24
- says: measured on 2026-08-24 against **VTK 9.5.2**, writing a grid with identifiers and reading it
  back through the XML reader.
  (1) The attribute role is **written into the file**, not inferred from the array's name: a `.vtu`
  carrying global identifiers has `<PointData GlobalIds="GlobalNodeId">` and
  `<CellData GlobalIds="GlobalElementId">` in its header, and `GetGlobalIds()` returns the array after
  a round trip. So a reader reads the declared role; a data array a user happened to call
  `GlobalNodeId` is not an identifier, and an identifier a writer called something else still is one.
  (2) Both point and cell global identifiers survive the round trip.
  (3) **A pedigree identifier may be text.** `SetPedigreeIds` accepts a `vtkStringArray` and returns
  it as one, so no numeric array can hold a pedigree identifier and `vtk_to_numpy` cannot read it.
  (4) The identifier arrays appear in `GetNumberOfArrays()` alongside the data arrays, so a reader that
  takes every array takes the identifiers too - which is what this build did until 2026-08-24.
- justifies: INV-023, XC-236

### E-136 - The Exodus reader's default is to read no results at all
- tier: T1
- url: spike/measure_object_types.py
- verified: 2026-08-24
- says: measured on 2026-08-24 against **VTK 9.5.2**, writing an Exodus file with `vtkExodusIIWriter`
  and reading it back.
  (1) A file written with the point results `stress` and `temp` and the cell result `elem_stress` comes
  back, after `SetFileName` and `Update` alone, carrying geometry, one `ObjectId` cell array and
  **zero results**. `UpdateInformation()` reports all three under
  `GetNumberOfPointResultArrays` / `GetNumberOfElementResultArrays`, and every status is **0**. There is
  no error and no warning: a whole result file reads as an empty mesh.
  (2) `vtkExodusIIReader` exposes **27** array categories, counted from its `GetNumberOf*Arrays`
  methods. Twenty-six have a plain count/name/status triple; `Object` takes an object-type argument and
  is a view over the others. All start off.
  (3) With every category enabled and `SetGenerateGlobalNodeIdArray` /
  `SetGenerateGlobalElementIdArray` on, the leaf carries `stress`, `temp`, `GlobalNodeId` and
  `PedigreeNodeId` on its points and `elem_stress`, `ObjectId`, `GlobalElementId` and
  `PedigreeElementId` on its cells, with the GLOBALIDS and PEDIGREEIDS roles set.
  (4) The output is a `vtkMultiBlockDataSet` with a fixed eight-branch skeleton - Element Blocks, Face
  Blocks, Edge Blocks, Element Sets, Side Sets, Face Sets, Edge Sets, Node Sets - of which seven are
  empty for a simple file. An empty branch is a category the file has none of, not a missing part.
  (5) `ObjectId` is the element-block number written onto every cell. It carries **no** identifier
  attribute role, so nothing in the toolkit distinguishes it from a measurement.
- justifies: XC-237, ingest/REQ-015

### E-137 - What the CGNS reader gives, and what it does not
- tier: T1
- url: spike/write_cgns.py
- verified: 2026-08-24
- says: measured on 2026-08-24 against **VTK 9.5.2**, against a minimal single-zone unstructured
  CGNS/HDF5 file written for the purpose.
  (1) **The build ships no CGNS writer.** Sweeping every `vtkmodules` module for a class name containing
  `CGNS` returns three, all readers: `vtkCGNSReader`, `vtkCGNSFileSeriesReader`,
  `vtkCONVERGECFDCGNSReader`. XC-085's premise is correct.
  (2) **A CGNS file can nonetheless be generated**, which XC-085 did not anticipate. CGNS/HDF5 stores
  every node as an HDF5 group with `name`, `label`, `type` and `flags` attributes and an optional
  ` data` dataset, and h5py writes it directly. One trap: `C1` character data must be written as native
  chars (int8). Written with h5py's string dtype the reader **opens the file and misreads it** - the
  `ZoneType` node went unread, the zone was taken for structured, and 4 points came back as 8.
  (3) **`vtkCGNSReader` exposes no unit accessor.** Every method name was searched for `unit`,
  `dimension` and `dataclass`: **zero matches**. The file's `DimensionalUnits` declaration is
  unreachable through the reader, which is what ingest/AC-034 is for.
  (4) **It reads no results by default**, like Exodus and through a different API: three
  `vtkDataArraySelection` objects, and a file offering `stress` comes back with the array listed and its
  status **0**, giving a leaf with zero point arrays. Enabling them yields `stress`.
  (5) The output is a `vtkMultiBlockDataSet` nesting base then zone.
- justifies: XC-239, ingest/REQ-015, XC-085

### E-138 - How a result sequence reaches this product, and who guesses what it means
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkExodusIIReader.html
- verified: 2026-08-24
- says: measured on 2026-08-24 against **VTK 9.5.2**, with the reader's own documentation read from the
  wrapped docstring in the shipped build.
  (1) **The values are universal.** A reader with a sequence publishes it on the pipeline as
  `vtkStreamingDemandDrivenPipeline::TIME_STEPS`, whatever the format. A CGNS file carrying
  `BaseIterativeData_t/TimeValues` of `[0.0, 0.5]` came back as exactly that, with `TIME_RANGE` set too.
  So one key covers every format instead of one method per reader.
  (2) **`vtkExodusIIReader` guesses the kind, and documents the guess.** `SetHasModeShapes`: *"Set/Get
  whether the Exodus sequence number corresponds to time steps or mode shapes. By default,
  HasModeShapes is false unless two time values in the Exodus file are identical, in which case it is
  true."* And `SetModeShape(val)`: *"Convenience method to set the mode-shape which is same as
  this->SetTimeStep(val-1)."* The same index, relabelled from a coincidence: two equal values in a
  transient restart make a run modal.
  (3) **CGNS declares the kind and the reader does not expose it.** `SimulationType_t` distinguishes
  TimeAccurate from NonTimeAccurate; searching `vtkCGNSReader` for a method naming it returns only
  `UseUnsteadyPattern` and `UnsteadySolutionStartTimestep`, neither of which reports what the file said.
  The same shape of gap as the units (E-137).
  (4) **A single `[0.0]` is the reader's placeholder, not a declaration.** A CGNS file with no
  `BaseIterativeData_t` still publishes `TIME_STEPS = [0.0]`, while a plain `.vtu` publishes the key not
  at all. A product treating that 0.0 as a position would show a number the file never wrote.
- justifies: XC-240, GL-036, ingest/AC-043

### E-139 - What `os.kill(pid, 0)` reports on Windows, and why it is not a liveness probe
- tier: T1
- url: spike/measure_object_types.py
- verified: 2026-08-24
- says: measured on 2026-08-24 on Windows 11 with CPython 3.11. `os.kill(pid, 0)` returns without
  raising for a live process; for a pid that does not exist it raises **`OSError` with
  `winerror == 87`** (ERROR_INVALID_PARAMETER) and **not `ProcessLookupError`**, which is what the
  POSIX form of the same check catches; and for a protected process - pid 4, the System process - it
  raises **`SystemError`** wrapping an OSError.
  So a liveness check written against `ProcessLookupError` finds every process alive on this platform,
  and one that treats any exception as "gone" declares the System process dead. Neither error tells the
  two cases apart on its own.
- justifies: workspace/AC-029, XC-241

### E-140 - What the resampling filter puts at a point outside the source
- tier: T1
- url: spike/measure_object_types.py
- verified: 2026-08-24
- says: measured on 2026-08-24 against **VTK 9.5.2**. `vtkResampleWithDataSet` and `vtkProbeFilter`
  both write a `vtkValidPointMask` array marking each target point 1 inside the source and 0 outside -
  and at the points marked 0 they write **0.0 into the field itself**. Not NaN, not the field's range,
  not left untouched: zero.
  So a product that takes the returned array as the resampled field hands back a page of zeros wherever
  its mesh did not reach, and in a difference zero reads as "these agree". This is the behaviour E-056
  records Tecplot having - "only 'do not change' or 'constant' for outside points, with no validity
  mask" - arriving here as the toolkit's default with a mask available and unapplied.
  Interpolation at an interior point is linear and exact for a linear field: a target at 0.5 between
  source values 0 and 10 came back as 5.0.
- justifies: XC-038, diff/AC-007


### E-141 - What multiplication does to a unit that carries an offset
- tier: T1
- url: spike/measure_expression_units.py
- verified: 2026-08-25
- says: measured on 2026-08-25 against this product's own converter (`domain_core.units.convert`).
  Doubling a value and then converting it, versus converting it and then doubling, give the **same**
  number for every unit that is a pure scale factor and **different** numbers for every unit that
  carries an offset: mm at 20 and K at 293.15 agree exactly (gap 0.0), degC at 20 gives 313.15 K one way
  and 586.3 K the other (gap **273.15 K**), and degF at 68 gives 330.93 K against 586.3 K (gap
  **255.37 K**).
  The gap is the offset itself, which is the point: "twice this temperature" has no single answer, so
  any answer an evaluator produced would be one it invented. The same argument covers division, powers
  and every function that is not addition or comparison.
- justifies: XC-242, pipeline/AC-030, pipeline/AC-031

### E-142 - What single-precision coordinates cost a cell volume
- tier: T1
- url: spike/measure_point_precision.py
- verified: 2026-08-25
- says: measured on 2026-08-25 against **VTK 9.5.2**. `vtkPoints` stores coordinates in **float by
  default** (`GetDataType()` returns `VTK_FLOAT`), and `vtkCellSizeFilter` computing the volume of a
  unit-side cube reports a relative error of **4.5e-8 at side 0.1 and 6.7e-8 at side 0.01** from
  single-precision points, against **0.0 at both** from the same coordinates stored as double. Sides of
  1.0 and 2.0 agree to 1.1e-16 either way, because those coordinates are exactly representable in both
  - so a check written against a cube of side 1 would find nothing.
  The error is the coordinates', not the filter's: it is float32 epsilon carried into a product of three
  numbers. It matters here because a volume-weighted mean multiplies field values by these volumes
  (INV-017), so it does not stay in the geometry - it arrives in the reported number.
- justifies: INV-001, XC-245, graph/AC-022

### E-143 - What a reduction over a large field loses, by the precision it is accumulated in
- tier: T1
- url: spike/measure_numerical_integrity.py
- verified: 2026-08-25
- says: measured on 2026-08-25 with NumPy 2.x on ten million values of 300.0 varying by 1e-3 - the
  ordinary shape of a temperature field in kelvin or a stress field about a preload. Relative error of
  the sum against an exact one: **1.6e-16** accumulated pairwise in float64, **1.3e-13** accumulated
  sequentially in float64, **3.5e-10** for a float32 field accumulated in float32, and **2.2e-12** for
  the same float32 field accumulated in float64 - a factor of 160 for no cost but the accumulator's
  type.
  The mean is where it shows. The exact mean is **299.999999895342**; accumulated in float32 it is
  **300.000000000000** - the variation the field was written to carry is gone, and the number that
  remains is the offset, printed to full width.
- justifies: INV-031, XC-246
- correction: 2026-08-25, same day. This entry first carried a second claim: that two values 1e-7 apart
  "differ by exactly 0.0 in float32 and by 1.0000002e-07 in float64", offered as a loss in the
  **subtraction** and as an argument for subtracting in double. **It is wrong**, and it was wrong in a
  way that would have produced a rule doing nothing.
  What the 0.0 shows is that both literals round to the **same float32 before anything is subtracted** -
  the distinction was gone in storage, and no arithmetic can recover it. Subtraction itself loses
  nothing: measured over **100,000 random float32 pairs within a factor of two**, the float32 difference
  equals the float64 difference in every case, which is Sterbenz's lemma holding as it should.
  What a near-equal difference does lose is **significance**, not bits: operands of magnitude 300
  differing by 1e-7 carry ten digits each and produce a difference carrying **one** - 9.5 digits gone -
  and the result's storage type says nothing about that. That is INV-034's subject, and it is a
  reporting rule rather than an arithmetic one.

### E-144 - Averaging element values onto shared nodes halves a reported peak
- tier: T1
- url: spike/measure_numerical_integrity.py
- verified: 2026-08-25
- says: measured on 2026-08-25 against **VTK 9.5.2**. A row of five hexahedra carrying element values
  10, 20, **200**, 20, 10 MPa - a stress concentration inside the body. `vtkCellDataToPointData`
  averages them onto the shared nodes, and the maximum of the result is **110 MPa against the element
  maximum of 200 MPa: 55 per cent of it, an under-report of 90 MPa**.
  The same concentration placed at the **end face** gives 200 MPa either way, because that node belongs
  to one element. So a check written on a peak at a boundary reports that averaging is harmless, and a
  peak in the interior - which is where a concentration is - is where it is not.
  The spread at the peak node is 180 MPa, which is the quantity the reference product publishes as
  Nodal Difference (E-145).
- justifies: INV-032, XC-247

### E-145 - How the reference product names averaged results, and what it refuses to average
- tier: T1
- url: https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/wb_sim/ds_Unaveraged_Results.html
- verified: 2026-08-25
- says: the vendor's own documentation for its mechanical post-processor defines: **averaged contours**
  "distribute the average elemental nodal results across element and geometric discontinuities",
  averaging component values at shared nodes and computing principal values from the averages;
  **unaveraged contours** "vary discontinuously even across element boundaries" and are "determined by
  linear interpolation within each element and are unaffected by surrounding elements".
  It publishes the spread as first-class results: **Nodal Difference** is "the maximum difference
  between the unaveraged computed result ... for all elements that share a particular node",
  **Nodal Fraction** "the ratio of the nodal difference and the nodal average", with Elemental
  Difference and Elemental Fraction the same quantities per element. The documentation states these aid
  in determining mesh quality: large differences between elements attached to a shared node indicate
  that a refined mesh may be necessary in that region.
  On material boundaries it warns that where bodies have different material properties, "averaging
  across bodies at the interface is not recommended".
- justifies: INV-032, XC-247
- note: this is the vocabulary, not the default. The product documents both that it averages across
  element and geometric discontinuities and that averaging across dissimilar materials is inadvisable;
  INV-022 already refuses the second outright rather than advising against it.

### E-146 - The built-in sum() stopped being a naive accumulator in Python 3.12
- tier: T1
- url: https://docs.python.org/3/whatsnew/3.12.html
- verified: 2026-08-25
- says: the language's own release notes, under "Other Language Changes": "`sum()` now uses Neumaier
  summation to improve accuracy and commutativity when summing floats or mixed ints and floats."
  Observed here on both sides of that change: on Python 3.11, `sum([0.1] * 10 + [1e16, -1e16])` returns
  **0.0** where `math.fsum` returns **1.0**; on Python 3.12, running the same accumulation over ten
  million values, `sum()` matched `math.fsum` exactly while NumPy's pairwise sum differed by 4.8e-07 in
  the last bits.
- justifies: INV-031
- note: this is a fact about the interpreter, not about this product, and it is recorded because a test
  here used `sum()` as the thing to be more accurate than. That test passed on 3.11 and failed on CI's
  3.12: the reference point had moved and the assertion was measuring the interpreter. `pyproject.toml`
  requires 3.12 and `conftest.py` prints a warning when the suite runs on anything older, which is the
  warning that would have caught it.

### E-147 - ParaView's own licence, read directly
- tier: T1
- url: https://gitlab.kitware.com/paraview/paraview/-/raw/master/Copyright.txt
- verified: 2026-08-25
- says: ParaView is **BSD 3-Clause**, copyright Kitware Inc. Binary redistribution requires reproducing
  the copyright notice, the list of conditions and the disclaimer in the documentation or other
  materials supplied with the distribution; the only prohibition is using Kitware's name or a
  contributor's name to endorse a derived product without written permission. There is no
  source-disclosure or copyleft obligation, and the file states no different licence for any part of
  the repository.
  So ParaView's own code - the readers VTK does not have, the application-level filters such as
  plot-over-line - may be taken into a commercial product on the same terms as VTK itself (E-002),
  which is a **licence** answer and not a maintenance one.
- justifies: XC-248

### E-148 - NVIDIA PhysX, licence read directly
- tier: T1
- url: https://raw.githubusercontent.com/NVIDIA-Omniverse/PhysX/main/LICENSE.md
- verified: 2026-08-25
- says: **BSD 3-Clause**, copyright NVIDIA Corporation 2008-2025. Source and binary redistribution both
  permitted on the usual notice-and-disclaimer conditions; the only prohibition is endorsement using
  NVIDIA's name. **No hardware restriction, no field-of-use restriction, no competing-products
  restriction**, and no component of the repository under different terms. The GPU simulation kernels
  are included under the same licence.
- justifies: XC-250

### E-149 - NVIDIA MDL SDK, licence read directly
- tier: T1
- url: https://raw.githubusercontent.com/NVIDIA/MDL-SDK/master/LICENSE.md
- verified: 2026-08-25
- says: **BSD 3-Clause**, copyright NVIDIA Corporation 2018-2026, with the usual notice conditions and
  the endorsement prohibition. **No hardware, field-of-use or competing-products restriction** is
  stated, and no component carries separate terms.
- justifies: XC-250
- note: this matters to this product specifically. MaterialX is already the canonical material graph
  (XC-115 and the technology table), and MDL is the language NVIDIA's own renderers consume - so the
  SDK is the piece that would let a MaterialX graph reach a photorealistic path **without** the piece
  that cannot be redistributed.

### E-150 - NVIDIA Warp, licence read directly
- tier: T1
- url: https://raw.githubusercontent.com/NVIDIA/warp/main/LICENSE.md
- verified: 2026-08-25
- says: **Apache License 2.0**, copyright NVIDIA Corporation & Affiliates 2022. Commercial
  redistribution permitted on the usual attribution and licence-delivery conditions. No hardware,
  field-of-use or competing-products restriction is stated.
- justifies: XC-250

### E-151 - What the Omniverse License Agreement actually forbids
- tier: T1
- url: https://raw.githubusercontent.com/NVIDIA-Omniverse/kit-cae/main/LICENSE
- verified: 2026-08-25
- says: the agreement governing Omniverse Kit and everything built on it states three things this
  product cannot work around.
  **"you may not use the Omniverse Products for the purpose of developing competing products or
  technologies."**
  **The Kit itself may not be distributed** - only specific extensions, snippets of thirty lines or
  fewer, and derivative works meeting stated criteria.
  **Public distribution "must take place either through the Exchange or through a fork of the Omniverse
  GitHub Repository"**, and the terms a distributor imposes "must be at least as protective as the terms
  of this license".
  Attribution is required in the form "This software contains source code provided by NVIDIA
  Corporation".
- justifies: XC-250, OPEN-030
- note: this **confirms E-009 against a contradicting reading taken the same day**. A summarised fetch of
  the Product Specific Terms page reported that no competing-products clause and no benchmark clause
  were stated; the licence text above states the competing-products prohibition in as many words. The
  recorded evidence was right and the summary was not, which is the argument for reading licence texts
  rather than pages about them.

### E-152 - What `kit-cae` provides, and what it requires
- tier: T1
- url: https://github.com/NVIDIA-Omniverse/kit-cae
- verified: 2026-08-25
- says: NVIDIA publishes a Kit sample **for CAE** - OpenUSD schemas and file-format plugins that compose
  and lazily access scientific datasets **without conversion**, with reference implementations for
  **CGNS, EnSight, VTK and OpenFOAM**; Warp-based GPU data-processing and visualisation algorithms; RTX
  and IndeX rendering of surfaces, volumes and particles; and capture and WebRTC streaming skills.
  Its extensions **require the Omniverse Kit SDK**, and the repository states that development using
  the Kit SDK is subject to the Omniverse licensing terms (E-151).
- justifies: XC-250
- note: this is the closest published work to this product's own subject, and it is the clearest case of
  the distinction XC-250 draws: what it does is directly relevant, and what it runs on cannot be
  shipped inside somebody else's desktop application.

### E-153 - The published VTK wheel contains no ray-tracing back end
- tier: T1
- url: spike/measure_vtk_rendering_modules.py
- verified: 2026-08-25
- says: measured on 2026-08-25 against the pinned **VTK 9.5.2** wheel. It carries 163 modules, 27 of
  them rendering, and **none of OSPRay, RayTracing, ANARI, OptiX, OpenVKL or Embree is among them**.
  The 27 are the OpenGL2, volume, VR/OpenXR, LIC, label, annotation and vtk.js-export families.
  So the ray-traced path ParaView offers - which is OSPRay - is **absent from the build this product
  ships**, and reaching it means building VTK from source with the module enabled. This is a fact about
  the wheel, not about VTK: VTK's documentation describes what VTK can be built with.
- justifies: XC-034, XC-087, OPEN-031

### E-154 - The Intel rendering stack, licences read directly
- tier: T1
- url: https://raw.githubusercontent.com/RenderKit/ospray/master/LICENSE.txt
- verified: 2026-08-25
- says: **OSPRay**, **Embree** and **Open Image Denoise** each ship a LICENSE file containing the
  **plain Apache License 2.0 text with no additional clause** - no hardware restriction, no
  field-of-use restriction, no competing-products restriction, and no product-specific addendum of any
  kind. Copyright Intel; the projects are maintained under the `RenderKit` organisation.
  OSPRay is a ray tracing engine for high-fidelity visualisation that renders **surfaces** (meshes,
  subdivision surfaces, spheres, curves, boxes, planes), **volumes** (structured regular and spherical,
  AMR, **unstructured**, VDB and particle volumes) and **isosurfaces**. It runs on **CPUs** - Intel
  architecture and Aarch64/ARM64 - with a beta implementation for Intel GPUs. Its dependencies are
  Embree, Open VKL, Open Image Denoise, ISPC and TBB.
- justifies: XC-250, OPEN-031
- note: the CPU point is what makes this relevant here rather than merely available. XC-086 supports a
  business laptop with integrated graphics, and INV-007 makes offline a feature - a photorealistic path
  that needs neither a particular vendor's GPU nor a network is the only one that fits both.

### E-155 - ANARI: one interface, three vendors' renderers behind it
- tier: T1
- url: https://www.khronos.org/anari
- verified: 2026-08-25
- says: ANARI is a Khronos C99 API with C++ wrappers that builds an in-memory scene tree for one frame,
  sitting **above** the low-level graphics APIs. Khronos states it "significantly simplifies the
  development of applications in domains such as scientific visualization" and it names scientific and
  exploratory visualisation as its target domain explicitly.
  **Three vendors provide back ends**: AMD RadeonProRender, Intel OSPRay (CPU and GPU through the oneAPI
  Rendering Toolkit) and NVIDIA VisRTX (RTX-accelerated). Barney, Visionaray and Cycles are named as
  further implementations.
  ANARI 1.0 launched in August 2023 and 1.1 is in preview with a feature freeze of 2025-08-07. It is
  **not yet fully ratified**: implementations are "expected to be officially conformant when the ANARI
  1.0 Adopters Program is released".
- justifies: OPEN-031, XC-251

### E-156 - The ANARI implementations, licences read through the registry
- tier: T1
- url: https://api.github.com/repos/KhronosGroup/ANARI-SDK/license
- verified: 2026-08-25
- says: read on 2026-08-25 through GitHub's licence endpoint, which reports the SPDX identifier the
  repository's own licence file declares.
  **ANARI-SDK** (Khronos): Apache-2.0. It ships the API headers and front-end library, the `helium`
  utilities for building a device, **`helide` - a CPU reference ray tracer using Embree** - a debug
  validation device, a capability-analysis tool and a conformance suite.
  **NVIDIA VisRTX**: **BSD-3-Clause**, copyright NVIDIA 2019-2026, read from the licence text itself
  because the registry reports NOASSERTION - the file carries a trailing paragraph excepting the sample
  applications' own external libraries, which is what defeats the classifier. It is an OptiX-based
  ANARI device with an experimental OpenGL device beside it, and **nothing in it refers to Omniverse or
  the Kit SDK**.
  **AMD RadeonProRenderANARI**: Apache-2.0.
  **Intel `anari-ospray`**: Apache-2.0.
  **Intel OSPRay, Embree, Open Image Denoise, Open VKL**: Apache-2.0, all four.
  **VTK's own source tree carries `Rendering/ANARI` and `Rendering/RayTracing`** - so the bridge from
  this product's data model to ANARI is a module Kitware already maintains, absent only from the
  published wheel (E-153).
- justifies: XC-251, OPEN-031
- note: VisRTX's **source** is BSD-3; running it needs OptiX, which is NVIDIA's own licence and NVIDIA
  hardware. The permissive licence removes the redistribution problem, not the hardware one - which is
  the same shape as CUDA and a different shape from the Kit SDK, where redistribution itself is barred.

### E-157 - A marketplace for this shape of product exists, and the customer spends budget already held
- tier: T1
- url: https://www.siemens.com/en-us/partners/software/join-partner-program/build/advanced-partner-alliance/
- verified: 2026-08-26
- says: the Advanced Partner Alliance - the former Altair Partner Alliance, reached today by following
  altair.com's own redirect - distributes independent vendors' software to customers who access it
  "using the Altair Units licensing system, which allows customers to access multiple engineering tools
  using a shared pool of licenses". **The customer therefore spends units already bought rather than
  making a separate purchase.** The stated criteria are "high-quality, specialized technology that adds
  real value to the workflow", "relevance to the engineering and industrial software space" and "a
  professional, dedicated company committed to supporting customers". Partners "retain ownership of
  your intellectual property, define your product roadmap and manage your own technology and support
  strategy", and reach customers through the catalogue, marketing, events and the Siemens sales
  organisation. **Partner compensation and revenue share are not stated on the page**
- justifies: OPEN-035
- note: two ownership changes were found on the way to this page and both bear on a channel decision -
  altair.com redirects to siemens.com, and ansys.com redirects to ansys.synopsys.com

### E-158 - The Ansys Store accepts third-party applications, on terms this project could not read
- tier: T2
- url: https://developer.ansys.com/partner_home
- verified: 2026-08-26
- says: the store lists third-party applications under a curated verification process - partnership
  review, virus and code scan, quality assurance testing and a documentation review, with results
  communicated within 45 days, and the submitter supporting the app. **Recorded at T2 because the
  primary pages could not be read here**: developer.ansys.com now redirects to developer.synopsys.com,
  which returns HTTP 403, as does the partner guidelines PDF. The description above comes from search
  summaries of those pages rather than from the pages themselves, so it may not justify a Fixed value
- justifies: OPEN-035

### E-159 - The Functional Source License text, from its steward
- tier: T1
- url: https://raw.githubusercontent.com/getsentry/fsl.software/main/FSL-1.1-MIT.template.md
- verified: 2026-08-30
- says: FSL-1.1-MIT grants use, copying, modification, derivative works, public performance/display
  and redistribution for any Permitted Purpose - any purpose other than a Competing Use, defined as
  making the software available in a commercial product or service that substitutes for it or for a
  product the licensor offers with it. Each version becomes available under the MIT licence on the
  second anniversary of its release. The template's only variables are the year and the licensor
  name; LICENSE.md instantiates it verbatim with 2026 and take-works-tech (Take)
- justifies: XC-082, XC-186

### E-191 - The pinned VTK renders a colour-mapped surface with a legend offscreen, on this machine
- tier: T1
- url: spike/measure_offscreen_render.py (record: spike/offscreen_render.json; the frame itself is
  written to spike/artifacts/, which is not committed, and is regenerated by running the script)
- verified: 2026-09-18
- says: measured on 2026-09-18 against the pinned **VTK 9.5.2** wheel, Python 3.11.9, Windows 11,
  OpenGL vendor NVIDIA. A 39,602-point, 79,200-polygon sphere carrying a float32 field, coloured
  through a lookup table with a scalar bar titled with a unit, rendered to an **offscreen** 800x600
  window and written to PNG in memory: **81,338 bytes, then 76,222 bytes after a 45-degree azimuth
  and 20-degree elevation move, the two frames differing by hash, 0.263 s for the whole run** from
  building the scene to the second PNG. The harness fails if the two frames are identical, so a
  plausible byte count without a drawing cannot pass it
- justifies: XC-257, XC-087
- note: this is the image role XC-087 gives the native toolkit, shown to work with nothing built
  yet - no window, no display server, and none of the ray-tracing modules E-153 found absent. It is a
  measurement on one machine with a discrete GPU; a machine without one, or a CI runner, is not
  measured here, and the `vtkRenderingOpenGL2` path on such a machine is the next thing to measure
  before the renderer step of XC-257 is called done

### E-192 - The native scalar bar drops a Japanese title silently, and draws it from a font file
- tier: T1
- url: spike/measure_legend_text.py (record: spike/legend_text.json; frames under spike/artifacts/, not
  committed, regenerated by the script)
- verified: 2026-09-18
- says: measured on 2026-09-18 against the pinned **VTK 9.5.2** wheel, Python 3.11.9, Windows 11.
  A scalar bar titled 「応力 単位未宣言」 with the toolkit's embedded faces renders **exactly the same
  number of text pixels as an untitled bar (388 and 388)** - no glyph, no box, no warning - while a
  Latin title renders 531 against the same 388. The same Japanese title with `C:\Windows\Fonts\
  meiryo.ttc` as the font file renders 262 text pixels against 131 for an untitled bar in that face.
  The frame with the dropped title still **differs by hash** from the untitled frame, because the bar
  is laid out shorter to leave room for words that are not there
- justifies: XC-257, OPEN-032
- note: two things, and the second is about this record. **The legend's words cannot come from the
  toolkit's own fonts** in this product's language: the one string the prototype must show when no
  unit is declared - 単位未宣言 - is the one the embedded face cannot draw, and it fails by omission,
  which is the failure this product's whole discipline exists to refuse (XC-001). So XC-257's step 3
  is corrected: the native image carries the colour ramp and Latin tick digits; the title, the unit
  and 単位未宣言 are typeset by the surface that shows the image - the document, which already
  embeds a font and checks its coverage per character (report-15), and the interface. A shipped font
  for the toolkit (OPEN-032) would let the image carry them too, and is not needed for the prototype.
  **And the first two versions of this measurement were wrong in the way spike/measure_render.py
  warns about**: a hash difference was read as "drawn" (it was the layout), and then a pixel count
  against the wrong baseline was read as "not drawn" (the digits had changed font). Only a count
  against an untitled bar in the same face measures the words. Both wrong readings are kept in the
  script's comments

### E-193 - Viridis and plasma are released by their authors under CC0, and the tables are theirs
- tier: T1
- url: https://raw.githubusercontent.com/BIDS/colormap/master/colormaps.py
- verified: 2026-09-18
- says: the header of the authors' own file reads: "New matplotlib colormaps by Nathaniel J. Smith,
  Stefan van der Walt, and (in the case of viridis) Eric Firing. This file and the colormaps in it are
  released under the CC0 license / public domain dedication. We would appreciate credit if you use or
  redistribute these colormaps, but do not impose any legal restrictions." The file holds
  `_viridis_data` and `_plasma_data` as 256 rows of three floats; the first row of viridis is
  `[0.267004, 0.004874, 0.329415]` and its last `[0.993248, 0.906157, 0.143936]`, and the same rows
  in matplotlib's `lib/matplotlib/_cm_listed.py` at the commit read the same day are identical
- justifies: XC-111, XC-257
- note: `src/engine/visualization/colour_maps.py` is generated from this file (archive
  script, not shipped): the 256 rows rounded to sRGB hex, which puts viridis's ends at `#440154` and
  `#fde725` and plasma's at `#0d0887` and `#f0f921` - **exactly the two stops the interface's own
  tokens already used for its legend gradients**, so the picture and the chrome agree. The third map,
  `greys`, is generated as a straight sRGB line between the token's two stops and needs no licence.
  Credit is given in the module docstring as the authors ask; no restriction applies. Issue #275
  (カラーマップの出所とライセンス) is answered for these three; any map added later needs its own row

### E-194 - Without a display, the published toolkit wheel does not refuse to render: it segfaults
- tier: T1
- url: https://github.com/take-works-tech/261SV/actions/runs/35350960523/job/105618715764 (CI run of
  pull request #352, `tests` job, 2026-09-18)
- verified: 2026-09-18
- says: on `ubuntu-latest` with the pinned **VTK 9.5.2** wheel from PyPI and no display, the first
  call to `vtkRenderWindow.Render()` on an offscreen window ended the interpreter with
  "Fatal Python error: Segmentation fault" at `render.py:209` and "Process completed with exit
  code 139". No exception, no toolkit message: the process was gone. The same call on this Windows
  machine with a discrete GPU rendered in 0.26 s (E-191)
- justifies: XC-257, XC-045
- note: two consequences, both built the same day. **The engine must ask before it draws, and ask
  in a process it can afford to lose**: `render.probe_offscreen` renders an empty window in a child
  process and reports its exit status, `system.capabilities` reports that answer, and `view.render`
  refuses with the requirement named when the answer is no - a refusal where the alternative is the
  engine process disappearing under the interface, which is the reason XC-045 isolated the readers.
  And **CI provides a virtual display** (`xvfb-run` with Mesa's software OpenGL), because a renderer
  whose tests skip on the runner is a renderer nobody has seen work; the test suite fails the run
  rather than skipping when the probe says no under `SIM_VIEWER_REQUIRE_VTK=1`. E-191's closing
  sentence - that a machine without a discrete GPU or a CI runner was not measured - is now measured,
  and the answer was worse than a slow frame

### E-195 - Electron's `app` module: single-instance lock, userData, quit events
- tier: T1
- url: https://www.electronjs.org/docs/latest/api/app
- verified: 2026-09-19
- says: `app.requestSingleInstanceLock()` returns whether this instance obtained the lock - "If it
  failed to obtain the lock, you can assume that another instance of your application is already
  running with the lock" - and `second-instance` "will be emitted inside the primary instance of
  your application when a second instance has been executed"; `app.getPath('userData')` is "the
  directory for storing your app's configuration files"; `before-quit` and `will-quit` are emitted
  before the application terminates and `event.preventDefault()` holds it
- justifies: XC-259

### E-196 - Electron's `utilityProcess` runs Node.js scripts, not arbitrary executables
- tier: T1
- url: https://www.electronjs.org/docs/latest/api/utility-process
- verified: 2026-09-19
- says: `utilityProcess.fork(modulePath)` takes the "path to the script that should run as
  entrypoint in the child process" and "provides the equivalent of `child_process.fork` API from
  Node.js"; its `exit` event carries "the exit code for the process obtained from waitpid on POSIX,
  or GetExitCodeProcess on Windows". A Python engine executable is therefore started with
  `child_process.spawn`, not with this
- justifies: XC-259

### E-197 - The engine's warm start and what termination leaves behind, measured here
- tier: T1
- url: spike/measure_engine_startup.py
- verified: 2026-09-19
- says: three runs on Windows 11 (reported by the platform module as "Windows 10"), Python 3.11.9,
  VTK 9.5.2, warm cache: spawn to `connection.json` 0.357-0.365 s; first `/health` 2.2-28.9 ms;
  `terminate()` ends the process with exit code 1 and the connection file survives it in every
  run. Before the pid was added the file was indistinguishable from a live engine's. A packaged
  cold start on a machine that has never run the product was not measured
- justifies: XC-259

### E-198 - Electron's `protocol` module: privileged schemes and `protocol.handle`
- tier: T1
- url: https://www.electronjs.org/docs/latest/api/protocol
- verified: 2026-09-19
- says: `registerSchemesAsPrivileged` "can only be used before the `ready` event of the `app`
  module gets emitted and can be called only once", and registers a scheme "as standard, secure,
  bypasses content security policy for resources, allows registering ServiceWorker, supports fetch
  API, streaming video/audio, and V8 code cache" according to the privileges given; `standard`
  makes the scheme "adhere to what RFC 3986 calls generic URI syntax" so relative resources
  resolve; `protocol.handle(scheme, handler)` delegates "requests made to URLs with this scheme"
  to a handler returning "either a `Response` or a `Promise<Response>`"
- justifies: XC-260

### E-199 - Electron's security checklist
- tier: T1
- url: https://www.electronjs.org/docs/latest/tutorial/security
- verified: 2026-09-19
- says: item 2 "Do not enable Node.js integration for remote content"; item 3 "Enable context
  isolation in all renderers" (default since 12.0.0); item 4 "Enable process sandboxing" (default
  since 20.0.0); item 6 "Do not disable `webSecurity`"; item 18 "Avoid usage of the `file://`
  protocol and prefer usage of custom protocols"; item 20 shows `contextBridge.exposeInMainWorld`
  filtering what reaches the page rather than exposing `ipcRenderer.on` directly
- justifies: XC-260, MOD-018

### E-200 - Node's `child_process`: what 'exit' carries and what `kill()` sends
- tier: T1
- url: https://nodejs.org/api/child_process.html
- verified: 2026-09-19
- says: on 'exit', `code` is "the exit code if the child process exited on its own, or `null` if
  the child process terminated due to a signal" and `signal` is "the signal by which the child
  process was terminated, or `null`"; "one of the two will always be non-`null`"; 'close' is
  emitted "after a process has ended _and_ the stdio streams of a child process have been closed";
  `subprocess.kill()` with no argument sends `'SIGTERM'`
- justifies: XC-259

### E-201 - Electron's ESM notes: main process yes, sandboxed preload no
- tier: T1
- url: https://www.electronjs.org/docs/latest/tutorial/esm
- verified: 2026-09-19
- says: ESM in the main process "was added in `electron@28.0.0`" and is enabled when "the nearest
  parent package.json has `"type": "module"` set"; "preload scripts will ignore `"type": "module"`
  fields, so you _must_ use the `.mjs` file extension in your ESM preload scripts"; "sandboxed
  preload scripts are run as plain JavaScript without an ESM context"
- justifies: XC-260

### E-202 - The frozen engine and the unpacked package, measured here
- tier: T1
- url: packaging/freeze_engine.py (record: spike/results.json `packaged_start`)
- verified: 2026-09-19
- says: on this machine (Windows 11, Python 3.11.9, VTK 9.5.2, PyInstaller 6.22.3), the frozen
  engine is 297,218,704 bytes in 1,600 files and takes 22.2 s to freeze; started on its own it
  writes its connection file in 0.549 s and answers `/health` in 6.1 ms with protocol 2.5.0 and 16
  operations; walked over HTTP it loads the demo case, declares K, renders a 70,510-byte PNG, picks
  8 K at the frame's centre and exports 229,791 bytes that match the file on disk. The unpacked
  Windows application (electron-builder 26.15.3, Electron 44.4.3) is 655 MB; started with a PATH of
  only the system directories - no Python - its `--smoke` reports the engine running 483, 391 and
  412 ms after the shell's own start across three launches, detects a SIGKILL as an event, restarts
  with a different pid, and leaves no connection file. Not a cold start: the machine's file cache
  had seen every file during the build. A fourth launch after a rebuild took 724 ms. On a GitHub
  `ubuntu-latest` runner (CI run 35423145900, the same day) the packaged Linux application, started
  with `PATH=/usr/bin:/bin` under xvfb right after being built, reported the engine running after
  1,165 ms - a second machine, a first launch of that build, and still a warm file cache
- justifies: XC-261

### E-203 - PyInstaller's run-time information: frozen state, `sys.executable`, one-file extraction
- tier: T1
- url: https://pyinstaller.org/en/stable/runtime-information.html
- verified: 2026-09-19
- says: "when a bundled app starts up, the bootloader sets the `sys.frozen` attribute and stores the
  absolute path to the bundle folder in `sys._MEIPASS`"; "in a frozen app, `sys.executable` is also
  the path to the program that was executed, but that is not Python; it is the bootloader in either
  the one-file app or the executable in the one-folder app"; `sys._MEIPASS` is "the path to the
  `_internal` folder" for a one-folder bundle and "the path to the temporary folder created by the
  bootloader" for a one-file bundle
- justifies: XC-261

### E-204 - PyInstaller's licence: what shipping a frozen program obliges
- tier: T1
- url: https://pyinstaller.org/en/stable/license.html
- verified: 2026-09-19
- says: PyInstaller is under "the GPL 2.0 License, with an exception that allows you to use it to
  build commercial products" and the Apache License 2.0; "the executable bundles generated by
  PyInstaller from your source code can be shipped with whatever license you want, as long as it
  complies with the licenses of your dependencies"; "you do not need to include PyInstaller's
  license file with your application, nor do you have to provide any form of acknowledgements or
  credits to PyInstaller"; modifications to PyInstaller itself, if distributed, fall under the GPL.
  Read after a comment in pyproject.toml had claimed the bootloader's notice belonged in the notices
  file - it does not, and the comment was corrected the same hour
- justifies: XC-261

### E-205 - Microsoft on redistributing the Visual C++ runtime files
- tier: T1
- url: https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files
- verified: 2026-09-19
- says: "distribution of the Visual C++ Runtime Redistributable package, merge modules, and individual
  binaries is limited to licensed Visual Studio users and is subject to Microsoft Software License
  Terms"; the REDIST list is referenced from the Visual Studio licence terms; "it's also possible to
  directly install the Redistributable DLLs in the application local folder", which "for servicing
  reasons, we don't recommend". The runtime files in this product's closure (VCRUNTIME140,
  VCRUNTIME140_1, msvcp140, the api-ms-win forwarders) arrive inside the VTK wheel, placed there by
  delvewheel at Kitware's build
- justifies: XC-025

### E-206 - The OpenXR loader's licence, from Khronos's own copying statement
- tier: T1
- url: https://github.com/KhronosGroup/OpenXR-SDK/blob/main/COPYING.adoc
- verified: 2026-09-19
- says: "the main OpenXR headers, XML registry, and loader source are licensed under a dual license
  with the SPDX license identifier `Apache-2.0 OR MIT`"; the repository's LICENSES/MIT.txt and the
  copyright lines of src/loader/loader_core.cpp (Khronos Group 2017-2026, Valve 2017-2019) are
  vendored in packaging/notices/openxr-loader.txt with this provenance. The loader DLL is in the
  closure because delvewheel bundled it into the VTK wheel; it is not in VTK's ThirdParty tree
- justifies: XC-025

### E-207 - What VTK 9.5.2's module descriptions declare, read from the source release
- tier: T1
- url: https://vtk.org/files/release/9.5/VTK-9.5.2.tar.gz (SHA-256 cee64b98d270ff7302daf1ef13458dff5d5ac1ecb45d47723835f7f7d562c989)
- verified: 2026-09-19
- says: the release carries 271 `vtk.module` files, 233 with an `SPDX_LICENSE_IDENTIFIER`: 178
  BSD-3-Clause, 42 `LicenseRef-BSD-3-Clause-Sandia-USGov`, and one or two each of seven other
  variants (LANL, Triad, California, NVIDIA, BSD-4-Clause, BSD-3-Clause-Clear), each variant naming
  its text through `SPDX_CUSTOM_LICENSE_FILE`; 45 third parties under ThirdParty/, 41 of them
  reached by the modules whose libraries the wheel ships, 71 licence-named files among them plus
  three under other names (exodusII and ioss `COPYRIGHT`, viskores/LICENSE.txt) and one with none
  (sqlite, whose sqlite3.h disclaims copyright). **`VTK::scn` is a `TEST_DEPENDS` of CommonCore in
  this release**, not a `DEPENDS` or `PRIVATE_DEPENDS`, so no scnlib file ships and no Apache-2.0
  text is owed for it - which corrects E-046's reading, taken from the master branch on 2026-08-19,
  that scnlib was on CommonCore's mandatory path. The reading was true of what it read and is not
  true of 9.5.2; E-046 stands as the record of that reading. The freeze also pulled Tk, Tcl's 830
  data files and Pillow through VTK's GUI bindings until they were excluded, which the generator
  found by refusing to attribute them
- justifies: XC-025, XC-041

### E-208 - This product's own leftovers in the temporary folder, measured here
- tier: T1
- url: spike/results.json `transient_leftovers` (the listing was taken with `ls -d %TEMP%/solvia-*`)
- verified: 2026-09-19
- says: on the development machine, before #313 was addressed, the temporary folder held eighteen
  `solvia-*` directories totalling 6 MB: twelve `solvia-smoke-<pid>` from the shell's `--smoke` runs
  and six `solvia-start-*` from `spike/measure_engine_startup.py`, none removed by what created it.
  The shell's session directories under `userData/engine` were not among them because the shell had
  been started only through the smoke. A crash leaves the connection file too (E-197)
- justifies: XC-262

### E-209 - What a workspace document costs as it grows, measured here
- tier: T1
- url: spike/results.json `workspace_document`, produced by spike/measure_workspace_document.py
- verified: 2026-09-20
- says: on the development machine (Windows 11, Python 3.11.9, warm cache), a document of views,
  graphs and reports in equal parts, each with a realistic definition, costs per item about 950
  bytes on disk and 28 µs to save or to load. 1,000 items: 0.95 MB, 29 ms to save, 21 ms to load,
  6.8 MB parsed. 10,000: 9.5 MB, 285 ms, 274 ms, 68 MB, with the `items` answer of `workspace.open`
  at 0.59 MB and one more creation at 5 ms. 100,000: 95 MB, 2.9 s each way, 682 MB parsed, a 5.9 MB
  answer and 106 ms per creation. Creating one at a time from empty is quadratic in what is there:
  0.09 s for 1,000, 0.38 s for 2,000, 2.5 s for 5,000, 11.5 s for 10,000. Not measured: a cold
  first open, the interface rendering the lists it is sent, a document with hundreds of cases
  beside the items
- justifies: LIM-016, XC-265

### E-210 - What a CGNS zone the reader cannot read looks like from outside, measured here
- tier: T1
- url: tests/test_cgns.py::TestAZoneTheReaderCannotReadIsAnAbsence, from a probe run on the
  development machine on 2026-09-20 (VTK 9.5.2, h5py 3.16.0)
- verified: 2026-09-20
- says: a CGNS/HDF5 file with two zones under one base, the second carrying a name and a ZoneType
  and no GridCoordinates, is read by vtkCGNSReader into a multiblock with two leaves. The second
  leaf holds 4 points - the zone's declared size - and 0 cells, and the reader writes "Error while
  reading mesh coordinates node :H5Gopen:open of a node group failed" to the toolkit's output window
  and nowhere a product reads. Before XC-272 the case counted 2 parts and reported itself complete
- justifies: XC-272

### E-211 - What the toolkit does with a result position it was not given, measured here
- tier: T1
- url: tests/test_cgns.py::TestReadingAnotherStep, from a probe run on the development machine on
  2026-09-21 (VTK 9.5.2, h5py 3.16.0) against the transient CGNS fixture of tests/cgns_fixture.py
- verified: 2026-09-21
- says: on a CGNS/HDF5 file declaring `TimeValues` of 0.0, 0.5 and 2.0, `vtkCGNSReader.UpdateTimeStep(0.5)`
  hands over the second solution's values and `UpdateTimeStep(0.0)` the first again; the declared
  sequence is on the pipeline's `TIME_STEPS` key after `UpdateInformation()` alone, before any data is
  read. Asked for 0.25, a value the file did not declare, the reader delivers the values at 0.5; asked
  for 7.0 it delivers those at 2.0 and for -1.0 those at 0.0 - silently in every case. The delivered
  position is written on the output's `DATA_TIME_STEP` key by every `UpdateTimeStep`, and by the
  plain first `Update()` not at all. Not measured: the Exodus reader on a file of several steps, for
  which no fixture exists here; it publishes the same pipeline keys
- justifies: XC-283

### E-212 - What each reader does with a file cut short, measured here
- tier: T1
- url: tests/test_incomplete_files.py, from a probe run on the development machine on 2026-09-21
  (VTK 9.5.2, h5py 3.16.0) against fixtures written by the toolkit's own writers and cut at 50, 80,
  90, 95, 99 and 99.9 per cent and one byte short
- verified: 2026-09-21
- says: CGNS (HDF5): refused at every cut, including one byte short. `.vtu`, `.vtp`: refused at
  every cut inside the data, read with every value identical to the complete file when the cut is
  inside the closing tag (99 per cent and one byte short for a 1.8 kB `.vtu`; one byte short for a
  7.7 kB `.vtp`). Binary `.stl`: refused at every cut but one byte short, which reads whole. A
  `.pvtu` with a piece cut: refused at 50 and 90 per cent, whole at 99; with the manifest cut or a
  piece missing: refused. Exodus II (NetCDF classic, magic `CDF\x02`, 3,308 bytes): refused at 50
  and 80 per cent by the results-arrived check (`ResultsLost`); **at 90, 95 and 99 per cent read as
  4 points, 2 cells and all three fields with every value 0.0**, with nothing written to the
  toolkit's output window; at 99.9 per cent and one byte short read whole. The file's NetCDF header
  declares an extent of 3,308 bytes, equal to the complete file and greater than every cut, one byte
  short included. Not measured: an Exodus file in HDF5 form (the writer here makes NetCDF classic);
  a file cut while a reader holds it open
- justifies: XC-284

### E-213 - UNC paths, vanishing files and held files through the real handlers, measured here
- tier: T1
- url: tests/test_paths.py, from a probe run on the development machine on 2026-09-21 (Windows 11,
  VTK 9.5.2) through the administrative share `\\localhost\C$` of the drive holding the temporary
  directory
- verified: 2026-09-21
- says: through the UNC path, `reader.read_case` read the eight-point cube, `snapshot` fingerprinted
  it, `dataset.inspect` answered, `dataset.load` into a local workspace applied and recorded the
  source with `pathRelative` `//localhost/C$/.../cube.vtu` and `pathAbsolute` the same in platform
  form, `field.declareUnit` and `workspace.save` applied, and a second session reopened the document
  and reloaded the file with the saved declaration re-applied and no second source entry. A workspace
  opened by its UNC path took its lock (`beam.svw.lock` beside it on the share), loaded a UNC file
  with `pathRelative` `cube.vtu`, saved, and answered `output.list`. A file deleted by the reader
  during its own `Update()` was refused as "does not exist"; so was a re-read of a deleted file with
  the load's fingerprint; both before XC-285 named the disappearance. A file on which another handle
  held a mandatory byte-range lock (`msvcrt.locking`) was refused by `read_case` and `dataset.load`
  as "named 1 part(s) and none of them is there": the toolkit's reader returned an empty output and
  no error. Not measured: a share on another machine, a mapped drive letter, the desktop shell's
  file dialogs with a UNC path
- justifies: XC-285

### E-214 - This product's numbers against the toolkit's own filters, measured here
- tier: T1
- url: spike/measure_cross_check.py, its record spike/cross_check.json, and tests/test_cross_check.py
  which repeats it on every run; taken on the development machine on 2026-09-21 (VTK 9.5.2)
- verified: 2026-09-21
- says: on the same files, the same quantities and the same units, against `vtkIntegrateAttributes`
  (ParaView's Integrate Variables), `vtkCellDataToPointData` (Cell Data to Point Data),
  `vtkTensorPrincipalInvariants` (Principal Invariants) and `vtkArrayCalculator` (the Calculator):
  **agrees exactly** - the maximum and the dual-volume mean of a trilinear field on a box (4.5), the
  volume-weighted mean of element values on the bar of E-144 (52.0), the nodal average at every node
  of that bar and its extrema (110 and 10), the magnitude of a vector at every point, the three
  principal values, the von Mises stress and the maximum shear of a symmetric tensor at every point
  (the component formula against the toolkit's eigenvalue route, largest difference 0.0), and the
  nodal average of each of two parts taken alone. **Differs, with the reason**: a surface mesh's mean
  is refused here (no volume, no area weighting built, INV-017) and integrated over area there
  (23.33); the nodal average across two parts' shared face is 200 here and 110 after Merge Blocks
  (INV-022, E-074); and on a hexahedron with one corner pulled from (1,1,1) to (2,2,2) the volume
  average of the linear field f = x is **0.625** by this product's V/8 node shares, **0.75** by the
  integrator's tetrahedra and **0.714286** by 2 x 2 x 2 Gauss quadrature of the trilinear
  interpolant - the exact value, which neither reaches; on a box all three are 0.5. **No reference**:
  the spread at an averaged peak (180 on the bar), which the toolkit does not compute. Not measured:
  ParaView itself, which is not installed on this machine; its filters are the classes above
- justifies: XC-287
- correction: 2026-09-21, same day. The skewed-hexahedron rows were re-measured after XC-288 replaced
  the equal split with shape-function integrals (E-215): this product's volume average of f = x is now
  **0.714286**, agreeing with the trilinear interpolant, and its volume **1.75** against the
  integrator's 2.0 - the difference is the integrator's planar tetrahedra, and it is recorded as
  such. The other rows are unchanged; `spike/cross_check.json` is the current record

### E-215 - What shape-function shares change in a weighted mean, measured here
- tier: T1
- url: tests/test_summary_weights.py::TestASharesIsTheIntegralOfItsShapeFunction and
  spike/measure_cross_check.py, from a probe run on the development machine on 2026-09-21 (VTK 9.5.2,
  numpy) with the toolkit's own interpolation functions at two-point Gauss quadrature per direction
- verified: 2026-09-21
- says: on a unit box every corner's share is 0.125 and the mean of f = x is 0.5, as before - to one
  ulp, since the quadrature points are irrational (4.5 arrives as 4.499999999999999). On the
  hexahedron with one corner pulled to (2,2,2) the shares are 0.1667 to 0.2917 and sum to **1.75**, the
  element's own volume, where the toolkit's size filter and integrator report 2.0 from planar
  tetrahedra; the volume average of f = x is **0.714286** = 5/7, the trilinear interpolant's exact
  value, against 0.625 from the equal split and 0.75 from the integrator. A tetrahedron of edges 2, 3,
  4 gives each corner 1.0 (a quarter of 4); a right wedge of base 2 x 3 and height 4 gives each corner
  2.0 (a sixth of 12) and keeps 12 under shear; a pyramid of base 2 x 2 and height 3 has volume
  exactly 4 and its mean of f = x is its centroid's 1.0, so the toolkit's pyramid functions are
  polynomial and the two-point rule is exact for them too. A hexahedron listed the other way round
  has volume 1.0 here and **-1.0** from the toolkit's size filter. A voxel (VTK type 11) is refused
  by name. Cost: a million unit hexahedra take 2.8 s for the point shares and 3.4 s for the cell
  volumes, against 18.7 s for the toolkit's size filter, with the total volume and the mean exact
- justifies: XC-288

### E-216 - Paths outside ASCII through every reader, the document and the engine process, measured here
- tier: T1
- url: tests/test_non_ascii_paths.py, packaging/freeze_engine.py --check --thread, and a probe run on
  the development machine on 2026-09-21: Japanese Windows 11 (active code page 932), Python 3.11.9,
  VTK 9.5.2 with its bundled netCDF 4.9.2, under a directory named `解析 結果／ｒｕｎ－１ #1 (a&b) 📐`
- verified: 2026-09-21
- says: the VTK XML reader and writer, the CGNS reader over HDF5, the document with its lock and its
  previous version, the report export, the output listing, the engine process's connection and log
  directories, and the shell's and the interface's threads under such a directory all read and write
  there as at any path. The Exodus family does not: the toolkit's writer creates nothing there
  ("CreateNewExodusFile can't create"), and its reader, handed such a path, **ends the process with
  0xC0000409** - for a Japanese-only name and for one with an emoji alike, on the system volume and on
  a data volume - before Python sees an error. The 8.3 short name is no way round: on the system
  volume the short names keep the Japanese characters (the OEM code page allows them) and the read
  then fails as "no part"; the data volume has 8.3 names disabled. With `activeCodePage=UTF-8`
  embedded in the interpreter's manifest (mt.exe on a copy of python.exe; `GetACP()` answers 65001)
  the same reader reads the same file and the writer writes beside it, Japanese and emoji included.
  The frozen engine built with `packaging/engine.manifest` answers `--code-page-probe` with 65001
  and, walked over HTTP, loads `ケース.ex2` under `解析 結果 📐` with its three fields (freeze 31 s,
  277.5 MB, connection file 1.0 s after start)
- justifies: XC-293

### E-217 - Paths past 260 characters through every library, with the long-path policy off, measured here
- tier: T1
- url: tests/test_long_paths.py and a probe run on the development machine on 2026-09-21: Windows 11
  (10.0.26200) with `LongPathsEnabled` = 0 - the default - Python 3.11.9 whose interpreter declares
  `longPathAware`, VTK 9.5.2 with its bundled HDF5 and netCDF 4.9.2, Node 22, at a directory whose
  plain path is 302 characters. The 247-character bound below which a plain path is always safe is
  Microsoft's documented limit for CreateDirectoryW (MAX_PATH less 12), a T2 source
- verified: 2026-09-21
- says: with the policy off, the **plain** long path fails in Python (`FileNotFoundError`, WinError 3,
  for a directory that exists), in HDF5 (h5py cannot create there) and in the toolkit's Exodus writer
  ("can't create"); the toolkit's XML writer alone writes there, and every reader was refused by this
  product's own existence check before the toolkit saw the path. In the **extended-length** form
  (`\\?\C:\...`) every one of them works: Python creates, writes and reads; the XML writer and
  reader, the CGNS reader over HDF5 and the Exodus reader over netCDF read the same files and answer
  the same numbers as at a short path. Node creates and writes at the plain long path on its own.
  Python keeps the prefix through `resolve`, `parent` and `with_name`, and refuses to relate a
  prefixed path to a plain one (`relpath` and `relative_to` raise `ValueError` on the mixed pair),
  which is why the prefix is added at the operating-system boundary only and never enters a record
- justifies: XC-294

### E-218 - An exported document opened from a download mark and a share, measured here
- tier: T1
- url: tests/test_exported_document_opens.py, run on the development machine on 2026-09-21: Windows
  11 (10.0.26200), Microsoft Edge 153.0.4234.48 and Google Chrome 153.0.8010.52, headless
  (`--headless=new --dump-dom`, a fresh `--user-data-dir` each run), the administrative share
  `\\localhost\C$`
- verified: 2026-09-21
- says: a probe page with an inline classic script, an inline module script, inline style and a 1x1
  PNG as a data URI reports all four as run, applied and loaded in both browsers from a local file,
  from the same file after `Zone.Identifier` with `ZoneId=3` was written beside it - the mark a
  download and a saved mail attachment carry - and through the share; and the document this build
  exports (title, the value table with its unit, the limitations and provenance sections, no script)
  renders the identical DOM the three ways in both browsers. Started without a profile of its own,
  Edge with a window open handed the request to the running browser and exited with code 789986 and
  no output, which is why every run gets its own profile. Not measured, and said so: a mail client's
  own preview pane, SmartScreen, opening by double-click from a folder, and browsers other than these
  two - the browser range is #256's question
- justifies: XC-295

### E-219 - The exported document and the application screen printed to PDF, measured here
- tier: T1
- url: tests/test_exported_document_prints.py, run on the development machine on 2026-09-21:
  Microsoft Edge 153.0.4234.48 and Google Chrome 153.0.8010.52, headless
  (`--print-to-pdf --no-pdf-header-footer`, a fresh profile each run), the pages read back from
  the PDF's page tree and looked at as rendered pages
- verified: 2026-09-21
- says: with a stylesheet that says nothing about paper, both browsers print on US Letter (612 x
  792 pt); with `@page{size:A4}` both print 595 x 842 pt. Before the print rules, a heading was
  left alone at the foot of a sheet with its figure on the next, a six-row table split across two
  sheets with its header repeated, and the trust sections followed inline. With the rules, a
  page-break block adds exactly one sheet (two and three sheets for one and two breaks), a figure
  at the width of the page sits whole on one sheet with its heading, legend, note and value, the
  provenance section - not split - opens the next sheet when it would not fit, a table's rows stay
  whole, and the two browsers lay the same five documents out to the same sheets (1, 2, 3, 3 and
  4). A document without an embedded font carries, in its limitations section, one line per
  element naming the characters it could not carry - the state OPEN-032 leaves the deliverable in -
  and that list alone turned a one-sheet document into two. The application screen printed from
  the browser is one Letter sheet holding the whole dark workbench, the report preview squeezed to a
  column some 60 mm wide, sidebars and toolbars around it: nothing of it is a document. Not
  measured: a physical printer, the browser's own print dialogue (the same engine, with margins and
  scaling as the person sets them), and browsers other than these two
- justifies: XC-296

### E-220 - What the generated sample holds, checked against its own formulas, measured here
- tier: T1
- url: tests/test_sample.py, tests/test_handlers.py::TestTheSample and the connected thread in
  src/ui/state/engine.connected.test.ts, run on the development machine on 2026-09-21 (VTK 9.5.2)
- verified: 2026-09-21
- says: the beam written by `engine/sample.py` has 615 points and 320 hexahedra; read back through
  the product's own reader, the maximum of `stress` is 1.2e6 under 100 N and 1.8e6 under 150 N -
  `F L (h/2) / I` with L = 1 m, h = 0.1 m, b = 0.05 m - at float32's six digits, the minimum
  -1.2e6, the largest displacement 4.0e-5 m (`F L^3 / (3 E I)` with E = 200 GPa) to a part in a
  million, and every cell-centre stress is inside the surface values; the file carries no unit and
  the sample document declares Pa and m, which the load applies. Through the interface's store
  against a real engine, asking for the sample, writing it, opening it, loading the first case and
  drawing it took 128 ms (the connected test prints the figure each run) - a segment of a launch
  on this machine, not LIM-010's number, which needs a launch on the hardware class of E-063
- justifies: XC-298

### E-221 - The product's numbers on the sample beam against beam theory, through every reporting path, measured here
- tier: T1
- url: tests/test_known_solution.py, run on the development machine on 2026-09-21 (VTK 9.5.2), on
  the sample of XC-298 under 100 N: L = 1 m, h = 0.1 m, b = 0.05 m, E = 200 GPa, 40 x 4 x 2 hexahedra
- verified: 2026-09-21
- says: `field.statistics` on the point stress reports the maximum 1200000 and the minimum -1200000
  exactly (the formula's 1.2e6 reaches float64's last place and float32 holds it exactly), in
  pascal at six digits, with a dual-volume-weighted mean within a pascal of the analytic zero; on the
  cell stress it reports the unaveraged maximum 888750 - the formula at the cell centre nearest the
  clamped end's top - and the nodal-averaged maximum the same with a spread of zero, because the
  cells meeting at that node hold one value; `dataset.probe` at three surface nodes reads the
  formula's value at each (600000, -900000, 0), and a point inside the body is a stated absence;
  `view.pick` at the centre of a 400 x 300 frame looking down z reads a value the field takes at a
  node; the derived displacement magnitude has the tip deflection 4.0e-5 m as its maximum to a part in
  a million and a weighted mean of 1.50031e-5 m - the analytic 1.5e-5 plus the trapezoid rule's
  3.125e-9 on this grid, to a part in a hundred thousand, and not the analytic mean; `graph.data`
  over the two cases plots 1200000 and 1800000; the deliverable's value table prints `1.20000e+6` and
  not a seventh digit. The prediction the mean rests on was checked on the same grid without the
  product: the trapezoid rule over the nodes gives the predicted value to a part in a trillion
- justifies: XC-299

### E-222 - The launch of the desktop shell, measured here: window, interface, engine, and a drawn sample
- tier: T1
- url: spike/measure_launch.py (record: spike/results.json `launch`)
- verified: 2026-09-22
- says: on this machine (Windows 11, Python 3.11.9, VTK 9.5.2, Electron 44.4.3, PyInstaller 6.22.3,
  integrated graphics, warm file cache), in milliseconds after the shell process's own start: the
  development shell reaches a created window in 75-77, a loaded interface in 158-182 and a reachable
  engine in 627-710 across five launches, and 710 / 1027 / 1341 on the first launch after a build;
  the packaged application (frozen engine 277,499,737 bytes in 669 files, 19.2 s to freeze) reaches
  them in 77-79 / 161-176 / 498-542 across two launches after the first, and 292 / 405 / 919 on the
  first launch after packaging. Asking the engine for the sample, writing it, opening it, loading
  its first case and drawing it takes 128 ms on this machine from a running engine (the connected
  test's own line). Launch to a drawn sample is therefore about 0.63 s packaged and warm, 1.05 s on
  the first launch after packaging, as a sum of segments measured separately and not as one
  measurement. Not measured: a cold start on a machine that has never run the product - the
  hundreds of megabytes of the frozen engine read from a cold disk - and any machine but this one;
  the launch page (XC-304) is written for that case rather than from a number nobody has
- justifies: XC-304

### E-223 - Selection to reflected change, measured here
- tier: T1
- url: src/ui/state/engine.connected.test.ts (record: spike/results.json `selection`)
- verified: 2026-09-22
- says: on this machine (Windows 11, integrated graphics, Python 3.11.9, VTK 9.5.2), with the demo
  cube and the bar loaded into the two cases of one document, moving the tree between them six
  times and waiting for every area to settle - the View area's picture and numbers of the other
  dataset included - took 99 ms at least, 108 ms at the median and 110 ms at most. Both fixtures
  are small; a dataset near LIM-001 was not measured, nor any machine but this one
- justifies: LIM-011, XC-305

### E-224 - Nielsen's three response-time limits
- tier: T2
- url: https://www.nngroup.com/articles/response-times-3-important-limits/
- verified: 2026-09-22
- says: Jakob Nielsen, 1993, citing Miller 1968, Card et al. 1991 and Myers 1985: 0.1 second is
  "the limit for having the user feel that the system is reacting instantaneously", 1.0 second
  "the limit for the user's flow of thought to stay uninterrupted", and 10 seconds "the limit for
  keeping the user's attention focused on the dialogue". An analysis that names its sources; the
  budgets here are set against it and measured here, never taken from it alone
- justifies: LIM-010, LIM-011, XC-305

### E-225 - What a workspace document costs as its cases grow, measured here
- tier: T1
- url: spike/measure_workspace_cases.py (record: spike/results.json `workspace_cases`); src/ui/logic/subject.scale.test.ts for the tree
- verified: 2026-09-22
- says: on this machine (Windows 11, Python 3.11.9, warm cache), a document of cases in a two-level
  tree of sweeps, each case tagged and carrying one recorded source whose file is absent, costs per
  case about 445 bytes on disk and 230 bytes in the `cases` answer of `workspace.open`. 500 cases:
  223 KB, 8 ms to save, 5 ms to load, 18 ms to open through the command surface (each source
  resolved by one stat), a 115 KB answer, 0.1 ms to add one more. 1,000: 446 KB, 16 / 11 / 36 ms,
  230 KB. 5,000: 2.2 MB, 74 / 56 / 196 ms, 1.15 MB, 1.1 ms. 20,000: 8.9 MB, 297 / 293 / 824 ms,
  4.6 MB, 6.3 ms. Adding one at a time is linear per add and quadratic over the run: 2,000 adds in
  0.34 s, the last at 0.75 ms. The interface's tree builder took 2.1 ms for 500 cases, 24 ms for
  2,000, 152 ms for 5,000 and 2,409 ms for 20,000 - a filter over every case for every case - and
  after grouping children once takes 0.3, 1.3, 1.7 and 7.7 ms. Not measured: a first open from a
  cold disk; sources whose files are present; the interface drawing one row per case
- justifies: LIM-005, XC-306

### E-226 - The regression set's fixtures, measured here: a million-cell grid, and what each reader does with random bytes and an empty file
- tier: T1
- url: tests/regression_catalogue.py and tests/test_regression_catalogue.py; the probe of 2026-09-23 recorded in this entry
- verified: 2026-09-23
- says: on this machine (Windows 11, Python 3.11.9, VTK 9.5.2), a grid of 100^3 hexahedra -
  1,030,301 points, 1,000,000 cells, one float32 point field - is 21.2 MB as the toolkit's XML
  writer writes it and reads whole in 0.25 s; a 60^3 grid (226,981 points, 216,000 cells, 4.4 MB)
  writes in 0.44 s and reads in 0.06 s. Handed 4,096 random bytes under each reader's extension and
  an empty file, `.vtu`, `.pvtu`, `.vtp`, `.cgns` and `.ex2` refused both - an XML parse error, or
  "no part this build can read" - and **`.stl` read the random bytes as 80 triangles, 240 points,
  with no complaint**, refusing only the empty file. A binary STL's header states its triangle
  count, and 84 + 50 × count equals 4,096 for no count but 80; that agreement is what the reader
  now requires before it reads
- justifies: XC-307, ingest/AC-051

### E-227 - EnSight Gold and VTKHDF through the toolkit's readers, measured here: what a cut file does to the reader, what its writer produces, and what the checks cost
- tier: T1
- url: src/engine/ensight.py, tests/test_ensight_vtkhdf.py and the probes of 2026-09-23 recorded in this entry
- verified: 2026-09-23
- says: on this machine (Windows 11, Python 3.11.9, VTK 9.5.2), with files `vtkEnSightWriter` wrote
  (one part of two triangles: geometry 828 bytes, node variable 260, element variable 252, case 194;
  two parts over two steps: geometry 1,256 bytes), `vtkGenericEnSightReader` handed the geometry cut
  in half **ended the process with a segmentation fault**; handed the geometry cut at 90 or 99 per
  cent, **returned the part as whole with the cells silently gone**; handed a variable file cut in
  half, returned the part with the variable silently dropped; handed the case file cut in half,
  **did not return** and was killed; handed an ASCII geometry cut in half, returned it as whole. A
  Python observer on the toolkit's output window (`CallDataType` `string0`) ends the interpreter.
  The writer names every part "VTK Part", suffixes each variable `_n` or `_c`, writes a `BlockId`
  variable file the case file does not list, and splits parts by a `BlockId` cell array; given
  `SetBlockIDs` from Python it keeps a pointer to the freed temporary and appends a stub part with an
  uninitialised number to the geometry and to every variable file (992 bytes where 828 is whole;
  1,584 where 1,256 is). `GetCaseFileName` returns the name alone and `GetFilePath` the directory
  with its separator. With the checks in place, every cut above is refused in under ten
  milliseconds and the whole files read in two to three; a hand-written big-endian geometry is read
  by the toolkit's reader in its own byte order; a companion whose name holds a space cannot be
  named by a case file, which the format splits on whitespace. `vtkHDFWriter` writes a four-point
  grid as 1,254,648 bytes; that file cut in half fails the reader's `CanReadFile` with the library's
  "truncated file" diagnostic, random bytes and an empty file carry no HDF5 signature, and a file
  with a 512-byte user block before the signature reads. Both readers take a path outside ASCII as
  given, as E-216 found for CGNS
- justifies: XC-308, ingest/AC-052
