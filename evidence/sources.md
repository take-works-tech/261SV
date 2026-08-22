---
status: draft
updated: 2026-08-22
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
