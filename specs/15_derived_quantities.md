---
status: draft
updated: 2026-08-20
---

# Derived quantities, components and frames

A result file carries components; an engineer asks about von Mises stress, the radial displacement, or
the first principal value. Between the two sits arithmetic that is easy to get subtly wrong and
impossible to notice afterwards, because every wrong answer is the right shape and a plausible size.

This file fixes the catalogue: what may be derived, by which formula, in which frame, and under whose
convention. **The conventions are not this product's** - they are the ones the field already uses
(E-073), because a value labelled by a different rule is a value nobody can compare.

## Component order and naming

A symmetric tensor of six components is ordered and named **XX, YY, ZZ, XY, YZ, XZ**; in two dimensions
it is three components, **XX, YY, XY** (E-073). A vector is **X, Y, Z** in the frame it is reported in.
A nine-component tensor has no standard naming, so this product **requires the symmetric form** for
derived quantities and reports the full form as components only.

## The catalogue

Every entry is computed in the analysis module from canonical data (INV-001), carries its formula in the
value's @Provenance, and propagates units (INV-002). Nothing outside this table is derived silently:
an expression a user writes is still an @Expression, and it is shown.

| Quantity | Applies to | Definition |
|---|---|---|
| component | vector, tensor | one named component in a stated @Component frame |
| magnitude | vector | the Euclidean norm |
| von Mises | symmetric tensor | `sqrt( ((XX-YY)^2 + (YY-ZZ)^2 + (ZZ-XX)^2 + 6*(XY^2 + YZ^2 + XZ^2)) / 2 )` |
| principal values | symmetric tensor | the eigenvalues, **ordered largest to smallest** (E-073), reported as three quantities |
| principal directions | symmetric tensor | the eigenvectors paired with the values above, in the same order |
| maximum shear | symmetric tensor | `(σ1 - σ3) / 2`, from the ordered principal values |
| trace | symmetric tensor | `XX + YY + ZZ` |
| deviatoric part | symmetric tensor | the tensor minus one third of its trace on the diagonal |
| invariants | symmetric tensor | I1, I2, I3 of the characteristic polynomial |
| amplitude | complex result | `sqrt(real^2 + imaginary^2)`, the convention the established tool uses (E-076) |
| value at a phase | complex result | `real * cos(phase) - imaginary * sin(phase)` |
| phase angle | complex result | `atan2(imaginary, real)`, reported with its range stated |

**Ordering is a convention, not a fact about the material.** Largest-to-smallest is what the reference
implementation produces, so it is what this product produces; a report states the ordering rule beside
the values rather than assuming the reader shares it.

## The result axis

A @Case is indexed by a @Result axis, and it is not always time (XC-131):

| Kind | Indexed by | Notes |
|---|---|---|
| steady | nothing | one result |
| transient | time | the ordinary case |
| modal | mode number | each mode carries its eigenfrequency |
| harmonic | frequency **and** phase angle | complex results; the two are swept one at a time (E-076) |

For a harmonic result, **one axis is fixed while the other advances** - frequency at a chosen phase, or
phase at a chosen frequency - and which is which is stated on anything produced from it. Animating a
harmonic response over phase is what "over time" means for that kind of result.

**A mode index is not a time.** A graph that places mode 3 and t = 3 s on one axis has said something
false about the physics, so a @Graph or @Report combining results of different axes must state that it
is doing so.

## Component frames

A component without a frame is not a quantity. "Radial stress" means nothing until an axis exists, and
a product that assumes the global Z axis will be right most of the time and wrong silently the rest.

- the default frame is **global Cartesian**, and it is named on every component
- **cylindrical, spherical and local Cartesian frames** are defined on the @Workspace with an origin and
  an orientation, given a name, and referenced by that name
- a component requested without a frame that can be resolved is **refused**, naming what is missing -
  the same discipline as an undeclared unit (XC-003)
- a frame is geometry, not appearance: changing it changes reported numbers, so it is recorded with any
  value derived through it

## Where a value lives, and what may not be done to it

The reference implementation converts cell values to point values by **averaging every cell that uses a
point**, with the restricting options selecting by cell dimension rather than by material (E-074). At
the interface between two materials that averages values belonging to different physics into one number,
and the output does not record that it happened.

This product does not inherit that default:

- **no conversion happens unless it is asked for** (INV-003)
- when averaging is asked for, it is **never across a @Part boundary or a material boundary**; each side
  keeps its own value and the boundary is reported as such
- an averaged value is **labelled averaged** wherever it appears, and a report says so
- values that a solver wrote at integration points are read as the solver wrote them. This product does
  not extrapolate them to nodes on its own, because the extrapolation depends on the element formulation
  and the file does not carry it. Where a solver has already done it, the value is what the solver wrote

## Identifiers

Points and cells carry the identifiers the source file gave them, using the domain's existing types
(E-075):

- a **global identifier** - numeric, one per point or cell, unique in the dataset - is preserved and is
  what "the maximum is at node 12345" refers to, and what matches the same location between two cases on
  the same mesh
- a **pedigree identifier** may be non-numeric and need not be unique; it is carried through as
  provenance
- where a file carries neither, this product says so. **An array position is not an identifier** and is
  never presented as one: it changes when the file is written differently, and a report citing it would
  be citing nothing
