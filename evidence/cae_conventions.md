---
status: draft
updated: 2026-08-20
---

# Evidence: the conventions this domain already has

Compatibility is not a feature here, it is the condition of being used at all: an engineer who reads a
result in this product and the same result in the tool their organisation already runs must get the
same number, and must recognise the vocabulary. Where a convention exists, this product adopts it
rather than inventing a better one.

### E-073 - Tensor component order, and the ordering of principal values
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkDataSetAttributes.html and
  https://vtk.org/doc/nightly/html/classvtkTensorPrincipalInvariants.html and
  https://discourse.paraview.org/t/automatic-naming-of-tensor-components/8762
- verified: 2026-08-20
- says: a six-component symmetric tensor is ordered **XX, YY, ZZ, XY, YZ, XZ**, and components are named
  automatically with exactly those labels; a two-dimensional symmetric tensor is three components named
  XX, YY, XY. There is **no standard naming for a nine-component tensor**. Principal values computed by
  `vtkTensorPrincipalInvariants` are **ordered from largest to smallest**, with principal vectors
  produced alongside and an option to scale the vectors by their values
- justifies: XC-121, INV-020

### E-074 - Cell values become point values by unweighted averaging, with no notion of material
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkCellDataToPointData.html
- verified: 2026-08-20
- says: the standard conversion transforms cell data to point data by **averaging the values of all
  cells using each point**. The options that restrict which cells contribute - `Patch` and `DataSetMax` -
  select by **cell dimension**, not by material, block or part, and the documentation warns they cost
  "on the order of >10x" performance against the default of using every attached cell
- justifies: INV-022, XC-123
- note: this is the hazard, stated by the toolkit itself. At a boundary between two materials the
  default averages values that belong to different physics into one number, and nothing in the output
  records that it happened

### E-075 - The domain already has identifiers, and they are typed
- tier: T1
- url: https://vtk.org/doc/nightly/html/classvtkDataSetAttributes.html
- verified: 2026-08-20
- says: among the twelve attribute types are **GLOBALIDS** - a single-component numeric array whose
  values are unique across the dataset, used to identify corresponding points or cells between datasets
  and across distributed pieces - and **PEDIGREEIDS**, a single-component array that may hold non-numeric
  values such as strings, carrying identity through refinement and transformation without a uniqueness
  guarantee
- justifies: INV-023, XC-124

## What these settle, and what they do not

They settle the **vocabulary and the ordering**, which is what compatibility actually consists of: a
product that labels the shear component YZ where everything else labels it XZ produces numbers that are
right and unusable. They do not settle what this product should do at a material boundary - the
reference implementation's default is documented above and is precisely what INV-022 refuses to inherit.
Adopting a convention is not the same as adopting a default.
