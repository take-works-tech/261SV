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
