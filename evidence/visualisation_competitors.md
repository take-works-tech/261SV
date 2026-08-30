---
status: draft
updated: 2026-08-30
---

# What already turns engineering data into pictures, and what it costs

A survey taken on 2026-08-30 of the products and alternatives a customer would weigh against a
"faithful visualisation and imaging" product - the direction the owner described as the original
idea: convert CAD/CAE data into 3D, render it realistically or as contoured figures, and produce
images and video for reports and promotion, displacing spend on 3D artists.

Prices are quoted from the vendor's own page where published. Where a vendor publishes none, that is
recorded rather than estimated.

## The paid field

| Product | What it is | Published price | Reads analysis data? |
|---|---|---|---|
| **KeyShot Professional** | CAD product rendering, the category leader | **JPY 207,048 / user / year** (JPY 17,254/mo; JPY 621,144 for 3 years) | **No** - "34+ CAD Format Support" |
| **KeyShot Business** | + seat management, network rendering | **JPY 254,865 / user / year** | No |
| KeyShot Enterprise | + VR, SSO, CSM | custom | No |
| **Lumion Pro** | real-time architectural rendering | **EUR 999 / year** (Studio EUR 1,299) | No |
| **Enscape Solo** | real-time, CAD/BIM plug-in | **USD 574.80 / year** (Premium 634.80) | No |
| **Twinmotion** | real-time, Epic | **free below USD 1M annual revenue**, otherwise **USD 445 / seat / year** | No |
| Tecplot 360 | CFD post-processing | USD 3,330/yr or USD 7,860 perpetual | Yes |
| VCollab · POSTFLOW | 3D CAE reports | not published | Yes |

## The free field

| Tool | What it is | Cost |
|---|---|---|
| **Blender** | full 3D suite, renderer, animation | free (GPL) |
| **STEPper / import_step** (Blender add-ons) | STEP import into Blender via OpenCASCADE / FreeCAD | free, open source |
| **ParaView / PyVista / VTK** | analysis post-processing | free |
| **BVtkNodes** | VTK pipelines inside Blender | free (GPL-3), 153 stars, last push 2024-08-04 |
| **Twinmotion** | real-time rendering | free below the revenue threshold |

## E-165 - What product rendering costs when it is bought as software
- tier: T1
- url: https://www.keyshot.com/pricing/ and https://www.lumion.com, https://enscape3d.com, twinmotion pricing
- verified: 2026-08-30
- says: KeyShot publishes JPY 207,048 per user per year (Professional) and JPY 254,865 (Business),
  with "34+ CAD Format Support with Native Plugins" on every edition. Lumion Pro is EUR 999 a year,
  Enscape Solo USD 574.80. **Twinmotion is free for companies below USD 1M in annual gross revenue**
  and USD 445 per seat above it
- justifies: XC-070, XC-071
- note: the band between free and JPY 207,048 is populated here, unlike the CAE post-processing band
  (E-160). Product rendering is a **served** market, and the free tier at the bottom is not a
  hobbyist tool - Twinmotion is Epic's, and it is free to exactly the customer a first release would
  reach

## E-166 - None of the rendering products reads analysis results
- tier: T1
- url: https://www.keyshot.com/pricing/ and the Datasmith supported-formats page
- verified: 2026-08-30
- says: KeyShot's format claim is "34+ CAD Format Support". Unreal's Datasmith lists eight CAD
  formats (ACIS, 3DXML, IFC, IGES, JT, Parasolid, PLM XML, STEP) and **no simulation or analysis
  result format** - no VTK, CGNS, Exodus, and no per-node or per-cell field data
- justifies: OPEN-037
- note: this is the measured gap. Geometry is served by many products; **field data on geometry is
  served by none of them**, and the products that read field data (ParaView, Tecplot) are the ones
  that render least attractively

## E-167 - The reader coverage already installed, by domain
- tier: T1
- url: measured here on 2026-08-30 against the pinned VTK 9.5.2 wheel
- verified: 2026-08-30
- says: the pinned build carries **43 IO modules and 181 reader classes**. By domain: CAE 30
  (Exodus, CGNS, EnSight, PLOT3D, Nek5000, CONVERGE, ERF, IOSS, Avmesh), general 3D 11 (OBJ, STL,
  PLY, glTF, X3D, BYU), point clouds 8 (PLY, PTS, SimplePoints), geospatial 6 (CityGML,
  Cesium 3D Tiles, GeoJSON, DEM, SEG-Y), medical 6 (DICOM, NIFTI, MINC, Nrrd), climate 8 (NetCDF
  family, MPAS), chemistry 4 (PDB, CML, Gaussian Cube). **No CAD kernel format is present** - no
  STEP, IGES or Parasolid reader exists in the build
- justifies: OPEN-037, OPEN-012
- note: the marginal cost of a domain is what decides its priority. Point clouds, general 3D,
  geospatial, medical and climate are **already readable at zero additional cost**; CAD is the one
  direction that needs a new dependency, a licence review and a kernel - and it is also the one with
  the most competition

## E-168 - Free tools already bridge CAD into the rendering world
- tier: T2
- url: https://github.com/postsilver/import_step and https://www.cadsketcher.com/
- verified: 2026-08-30
- says: STEPper (from the CAD Sketcher project) is a free and open-source STEP importer for Blender;
  a second add-on converts STEP to STL through FreeCAD's OpenCASCADE kernel. Blender cannot parse
  STEP natively, and these fill that gap at no cost
- justifies: OPEN-037
- note: recorded at T2 because the claims come from the projects' own pages and a community forum
  rather than from a tested build here. The point stands regardless of the details: **"get CAD into
  a renderer" is a solved and free problem**, and a product whose value is that conversion is
  competing with free

## E-169 - Difference-on-geometry with a colour scale is already free, and already scriptable
- tier: T1
- url: https://www.cloudcompare.org/doc/wiki/index.php/Cloud-to-Mesh_Distance and .../Command_line_mode
- verified: 2026-08-30
- says: CloudCompare computes cloud-to-mesh and cloud-to-cloud distance, stores the result as a
  scalar field, displays it with an editable colour scale, converts that scalar field to RGB for
  export, and **runs from the command line**. It is free and open source
- justifies: OPEN-037
- note: **this is the single most important competitive fact for a "faithful difference viewer".**
  The operation at the centre of ICT as-built management - overlay a point cloud on design geometry,
  show the deviation as a heat map - is not a gap. It is a free, mature, scriptable tool. What is not
  free is everything around it: the ministry's delivery specification, the forms, the tolerance
  judgement, the traceable record

## E-170 - What a paid inspection product costs, and what it is built on
- tier: T2
- url: https://www.artec3d.com/3d-software/geomagic-control-x and reseller listings
- verified: 2026-08-30
- says: Geomagic Control X is 3D inspection and metrology software for model-to-scan comparison and
  reporting, "built on a CAD kernel", integrating with scanners and PCMMs. Reseller listings give a
  perpetual licence with first-year maintenance from **USD 7,249 to USD 21,745** depending on tier
- justifies: XC-070, XC-071
- note: recorded at T2 - the price comes from resellers rather than from the vendor's own page.
  The band it implies is the same shape as everywhere else in this survey: **free at the bottom
  (CloudCompare), nothing published in the middle, five figures at the top**

## E-174 - Adjacent product-data domains, priced
- tier: T2
- url: CLO and Browzwear listings on SaaS directories; robodk.com/pricing; Isaac Sim license FAQ;
  gazebosim.org
- verified: 2026-08-30
- says: **apparel 3D** - CLO 3D is quoted at USD 50/month or USD 450/year; Browzwear VStitcher from
  USD 75/month, USD 750/year (Freelancer) to USD 3,950/year (Teams), enterprise by quote.
  **Robot simulation** - Gazebo is Apache-2.0 and free; **Isaac Sim is free for internal R&D**, source
  under Apache-2.0 with no per-seat limit, with Omniverse Enterprise quoted around USD 4,500 per
  GPU/year for commercial production; **RoboDK publishes no price** and raised it in April 2024
- justifies: XC-070, OPEN-037
- note: recorded T2 - the apparel prices come from software directories rather than the vendors' own
  pages, and the Isaac Sim enterprise figure from a forum thread. Two patterns hold regardless of the
  decimals: **apparel is an order of magnitude cheaper per seat than engineering software**, and
  **robot simulation has been made free at the point of use by its largest vendors** - NVIDIA and Open
  Robotics both give the simulator away, which removes the pricing floor from that domain entirely

## E-175 - The technical-illustration pipeline is already in the pinned build
- tier: T1
- url: measured here on 2026-08-30 against the pinned VTK 9.5.2 wheel
- verified: 2026-08-30
- says: the build carries `vtkHiddenLineRemovalPass`, `vtkFeatureEdges`, `vtkPolyDataSilhouette`,
  `vtkExplodeDataSet`, and vector exporters - `vtkSVGExporter`, `vtkPDFExporter` and
  `vtkGL2PSExporter` (PostScript/EPS). Fourteen outline filters and twenty-one exporters are present
- justifies: OPEN-037
- note: **the parts of a technical illustrator are already installed.** Hidden-line removal, feature
  edges, silhouettes, exploded views, and SVG/PDF/EPS output at zero additional cost. What is not
  present is a CAD kernel: these operate on meshes, so the line work is mesh-derived rather than
  B-rep-exact. For an assembly instruction from mesh or scan data that is enough; for a
  drawing-grade illustration from STEP it is not

## E-176 - What a technical illustrator costs, and what the simple-simulation floor is
- tier: T2
- url: novedge.com listing for Creo Illustrate Professional; simscale.com/product/pricing;
  autodesk.com Fusion pricing and Simulation Extension pages; freecad.org FEM workbench docs
- verified: 2026-08-30
- says: **Creo Illustrate Professional is listed at USD 14,500 a year** (concurrent user, maintenance
  included, about USD 1,341/month if split); Cortona3D RapidAuthor publishes no price.
  **SimScale**: a Community tier that is free ("10 unrestricted simulations", "up to 3000 core
  hours"), and Mechanical / Professional / Enterprise all **"Request pricing"**.
  **Fusion**: JPY 35,640 a year (JPY 4,320/month), and **static stress is not in the base
  subscription** - it needs the paid Simulation Extension.
  **FreeCAD's FEM workbench** is free on Windows, macOS and Linux, bundles **CalculiX** for static
  structural and modal analysis, and offers Elmer, Z88 and Mystran alongside, with Gmsh/Netgen
  meshing and **VTK-based post-processing**
- justifies: XC-070, OPEN-037
- note: recorded T2 - Creo's figure is a reseller's, and the Fusion extension boundary comes from
  Autodesk's marketing pages rather than a licence document. Two conclusions hold anyway.
  **Technical illustration is priced two orders of magnitude above a USD 49-149/month idea**, and
  **the simple-simulation floor is not empty**: FreeCAD plus CalculiX is a free, cross-platform,
  GUI-equipped static and modal solver whose post-processing is already VTK

## E-177 - Simplygon is free, with two stated limits
- tier: T1
- url: https://contents.simplygon.com/eulas/Simplygon_Free_License_Terms.pdf
- verified: 2026-08-30
- says: the Simplygon Free licence terms (Microsoft) state "You may install and use **any number of
  copies** of the software to develop and test your applications, and **solely for use on Windows**"
  and "The software requires an internet connection. **You may not use the software in an offline
  environment**"
- justifies: OPEN-037
- note: recorded because a mesh-optimisation product was proposed on the premise that Simplygon is
  enterprise-priced and out of reach. It is not. What remains unserved by the free tier is
  **non-Windows** and **offline** use - neither of which is a pain somebody pays a monthly fee for

## E-180 - Video: the outsourced price, and the floor generative models put under it
- tier: T2
- url: Japanese production-agency cost pages (tebiki, locus-inc, douga-kanji, atsoho); AI video API
  pricing comparisons (modelslab, buildmvpfast, vo3ai)
- verified: 2026-08-30
- says: **outsourced manual/instruction video** in Japan is quoted at JPY 100,000-2,000,000 in total,
  broken down as planning and script JPY 50,000-300,000, shooting JPY 100,000-1,000,000 (live action
  JPY 100,000-300,000 per shooting day), editing JPY 100,000-500,000, direction JPY 50,000-200,000.
  3DCG video was quoted separately at **JPY 1,000,000-1,400,000 per minute** (E-165 context).
  **Generative video** is quoted at **USD 0.09-0.14 per second** (Kling 3.0), USD 0.10/sec (Sora 2),
  USD 0.40-0.75/sec (Veo 3.1), with subscriptions from **USD 7.99-12 a month**
- justifies: XC-070, OPEN-037
- note: recorded T2 throughout - agency marketing pages and third-party API-pricing round-ups, not
  vendor contracts. The arithmetic is what matters. **A minute of generative video costs about USD 6
  at Kling's rate; a minute of outsourced 3DCG costs about JPY 1.2 million.** That is a gap of roughly
  four orders of magnitude, and it is closing from below every quarter. A product whose value is
  "cheaper than the agency" is entering the same race generative video is already winning

---

## What the survey says about the direction

**The rendering market is served, priced, and has a free tier from Epic.** KeyShot at JPY 207,048 a
year sits above Lumion, Enscape and a free Twinmotion, and every one of them reads CAD and none reads
analysis results.

**The gap is the intersection, and only the intersection.** Faithful geometry plus field data plus an
attractive render is served by nothing measured here. Each pair is served: geometry+render by
KeyShot's field, geometry+field by ParaView's, and the third pair does not exist without the first.

**The cheapest domains to add are the ones already installed** (E-167), and CAD - the domain the
original idea starts from - is the only one that is neither installed nor unserved.

## What this survey cannot settle

Whether anyone buys the intersection. The measured demand signal for the closest existing attempt is
weak (BVtkNodes, 153 stars, dormant two years), and it measures a hard tool rather than the need. The
outsourcing prices in `market_survey.md` (JPY 50,000 per still, JPY 50,000 per added angle) are what a
buyer pays today for the geometry half alone; nothing here says what they would pay for the
intersection.
