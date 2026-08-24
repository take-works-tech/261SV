---
status: draft
updated: 2026-08-24
---

# Object compatibility

What this product accepts, what it becomes, and what every combination it does not accept does instead.

### CT-012 - Object compatibility
- purpose: the closed set of dispositions for every VTK data object type, the closed set of View object
  types, and the total table of conversions between them - so that a shape arriving at a boundary is
  never met without a decision having been made about it
- schema: schema/CT-012.json
- version: 1.0.0
- strictness: the tables are **total**. A data object type with no disposition, a View object type CT-004
  declares and this contract does not, or an ordered pair of View object types absent from the
  conversion table is a defect in this contract and not a permission
- compatibility: a reader supports the contract when every class it accepts is marked `read` here, every
  conversion it performs is the one named here, and every refusal names the type rather than reporting a
  generic failure
- migration: a toolkit upgrade that adds a data object type makes this contract incomplete by definition;
  `validate/check_object_compatibility.py` compares it against the measured list and fails until the new
  type has a disposition
- decidedness: Fixed
- basis: E-132 (T1), E-133 (T1)

## Why the tables are total rather than long

A compatibility list that mentions what is supported is read as a list whose omissions are unsupported.
That reading is wrong in the one direction that matters: an omission is usually a type nobody thought
about, and the code path it reaches was not designed to refuse it. So the shape of this contract is a
**closed table with a default of refusal**, and a gate that fails when a row is missing.

The set being closed is what makes it checkable. There are 50 data object types in VTK 9.5.2, of which
10 are `vtkDataSet` subclasses, 8 are composites, and 17 more are instantiable data objects that are
**neither** - `vtkHyperTreeGrid`, `vtkTable`, `vtkCellGrid`, `vtkMolecule` among them (E-132). A reader
can hand back any of them, so a product whose reader signature says `vtkDataSet` has already excluded a
third of what it may be given, without saying so anywhere.

## A part and a partition are two things

The distinction runs through the whole contract and it is not a wording preference.

A **partition** is one dataset cut up for parallel input and output. Its pieces recombine into the mesh
they came from; the points on their interfaces are duplicates of each other, and INV-010 governs them.
`vtkPartitionedDataSet` and `vtkMultiPieceDataSet` are partitions.

A **part** is a distinct thing in the model - an element block, a side set, a material, a component.
Two parts do not recombine, their points are not duplicates, and summing across them is sometimes what
the user wants and sometimes meaningless. `vtkMultiBlockDataSet` is parts. `vtkPartitionedDataSetCollection`
is both at once, which is why it exists: a collection of parts, each of which may be partitioned.

Conflating them produces the two errors this product cannot make. Treating parts as partitions
deduplicates points that were never duplicates and quietly drops geometry. Treating partitions as parts
counts every interface twice.

**This matters more than the type list suggests, because it is the common case.** Of the 40 CAE readers
in the pinned build, 19 return `vtkMultiBlockDataSet` and 6 return `vtkPartitionedDataSetCollection`
(E-133): Exodus, EnSight, CGNS, OpenFOAM, LS-DYNA, Fluent, Tecplot and IOSS all hand back a composite.
Only 4 return a `vtkUnstructuredGrid` directly. **Every format this product's users actually work in
arrives as parts**, and a reader that expects one dataset meets none of them.

## What a conversion costs is stated before it runs

Eight data object types are accepted after one named conversion, and each row of the table says what
that conversion costs. Three of those costs are not obvious and none of them is a rounding error.

`vtkImageData` and its relatives store origin and spacing instead of points. After conversion the points
are explicit and the spacing is gone, and **the spacing is the one number in a voxel result that carries
a length**. It is recorded on the @Dataset at conversion time because nothing can recover it afterwards.

`vtkHyperTreeGrid` is a tree because the expansion is what the format exists to avoid. Converting it
produces one cell per leaf, and the memory is stated against LIM-002 **before** the conversion runs.

`vtkCellGrid` carries a discontinuous-Galerkin basis that the conversion does not preserve: it writes
linear sub-cells. INV-009 already forbids reporting a number from a linear approximation of a high-order
cell, so the converted form is offered for display and is not a source of numbers.

## The View object types, and what may become what

CT-004 declares eight: `analysisMesh`, `referenceMesh`, `scalarField`, `vectorField`, `trajectory`,
`pointCloud`, `annotation`, `effect`. This contract states, for each, what it requires and whether a
reported number may come from it - and the second of those is the reason `analysisMesh` and
`referenceMesh` are two types rather than one with a flag.

The conversion table has all 64 ordered pairs. Five are allowed. The other 59 each name one of six
reasons, and the reasons are worth more than the pairs:

| reason | what it protects |
|---|---|
| `identity` | a no-op cannot be mistaken for an accepted request |
| `differentKind` | one is geometry and the other is not; there is nothing to convert, only something to create |
| `derivedNotConverted` | a scalar field, a vector field and a trajectory are **produced from** an analysis mesh that goes on existing; they do not replace it |
| `inventsConnectivity` | the target needs cells the source has not got, and meshing them needs a tolerance |
| `inventsData` | the target needs a @Field the source has not got, and no default stands in for one (XC-001) |
| `wouldLaunder` | the source may not source reported numbers and the target may, so the conversion would turn a drawing into a measurement |

`wouldLaunder` is the one to read twice. `referenceMesh` to `analysisMesh` is refused not because it is
technically hard - the geometry is right there - but because the whole content of `referenceMesh` is the
promise that no number came from it, and a conversion that lifts the promise leaves nothing behind that
records it had been made.

## What is refused today, and what would change it

`vtkOverlappingAMR` is refused, and not for want of a filter. Its levels overlap by construction: a
refined region is present at every level above it, so a sum over the leaves counts it once per level.
That is INV-010 one level up, and the same answer applies - the number is not reported until the mask
that identifies the covered cells is read and applied.

The graph, molecule and selection families are refused because they are other domains or are not data:
each names itself in the refusal rather than producing a generic read failure, so that a user who opens
one is told what they opened.
