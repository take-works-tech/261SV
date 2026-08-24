"""The two geometries a @Dataset holds, and why they are two.

INV-001 says every reported number is computed on the dataset in the canonical frame and never from
display geometry, because display geometry is scaled, decimated and tessellated and measuring it
produces a number that is wrong in a way that looks right. That is a statement about **two point sets**,
and a product that keeps only one of them cannot honour it whichever one it keeps.

So `Cells` is the connectivity as the file declared it - every cell, of whatever type - and
`DisplayGeometry` is the triangulated surface, which knows it is a reduction and knows which original
point each of its own points came from.

**The layout is VTK's, not one invented here.** `offsets`, `connectivity` and `types` are the three
arrays `vtkCellArray` and `vtkUnstructuredGrid` already hold (E-132), so reading a file into this shape
copies rather than converts, and converting back is the same copy. A layout of this product's own would
add a conversion in each direction whose only purpose is to be different.

Specification: INV-001, INV-009, GL-005. Evidence: E-132 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from domain_core.reduction import ReductionPlan

# VTK 9.5.2 knows 64 cell types, of which 3 are zero-dimensional, 8 are curves, 21 are surfaces and 32
# are volumes (E-132). This product does not enumerate them: a cell type it has no opinion about is
# carried through unchanged, and only the ones a rule mentions are named anywhere.
VERTEX_CELL = 1  # VTK_VERTEX - the type a point cloud is made of
TRIANGLE_CELL = 5  # VTK_TRIANGLE - the only type display geometry is allowed to contain


@dataclass(frozen=True, slots=True)
class Cells:
    """Connectivity exactly as the file declared it, in the toolkit's own three-array layout.

    A mesh of one cell type and a mesh of seven are the same shape here, which is the reason for the
    layout: a product that stored triangles as `(n, 3)` has to decide what to do the first time it meets
    a hexahedron, and the decision it usually makes is to triangulate - which is the display path
    wearing the canonical path's name.
    """

    offsets: np.ndarray       # (count + 1,) where cell i occupies connectivity[offsets[i]:offsets[i+1]]
    connectivity: np.ndarray  # (offsets[-1],) point indices
    types: np.ndarray         # (count,) VTK cell type ids

    def __post_init__(self) -> None:
        if self.offsets.ndim != 1 or self.offsets.size < 1:
            raise ValueError("offsets is a one-dimensional array with at least the leading zero")
        if self.types.shape != (self.count,):
            raise ValueError(
                f"{self.types.size} cell types for {self.count} cells; one of the two was built wrongly, "
                "and a cell read as the wrong type is a cell with the wrong number of corners"
            )
        if self.offsets[0] != 0:
            raise ValueError("the first offset is 0; a non-zero start silently drops the leading cells")
        if self.connectivity.size != int(self.offsets[-1]):
            raise ValueError(
                f"the offsets describe {int(self.offsets[-1])} entries and the connectivity has "
                f"{self.connectivity.size}; the difference is cells that would read past their own end"
            )

    @property
    def count(self) -> int:
        return int(self.offsets.size - 1)

    def points_of(self, index: int) -> np.ndarray:
        """The point indices of one cell."""
        return self.connectivity[self.offsets[index] : self.offsets[index + 1]]

    @classmethod
    def empty(cls) -> "Cells":
        """A dataset with geometry and no cells - a point cloud before any is declared."""
        return cls(np.zeros(1, np.int64), np.zeros(0, np.int64), np.zeros(0, np.uint8))


@dataclass(frozen=True, slots=True)
class DisplayGeometry:
    """The triangulated surface a picture is drawn from, and the map back to what it was made of.

    It carries `source_points` because a picked triangle vertex has to answer with the value of the
    point it came from, and surface extraction neither preserves the count nor the order: a 27-point
    block of hexahedra extracts to 26 surface points whose origins begin 0, 1, 10, 9, 3 (E-132). Reading
    the field at the surface index would return a real value belonging to a different place - the worst
    shape a wrong number can have.
    """

    points_m: np.ndarray       # (n, 3) in the canonical frame, but decimated and tessellated
    triangles: np.ndarray      # (m, 3) point indices into points_m
    source_points: np.ndarray  # (n,) index into the @Dataset's own points, from vtkOriginalPointIds
    source_cells: np.ndarray   # (m,) index into the @Dataset's own cells, from vtkOriginalCellIds
    # How much of the surface is drawn. A plan rather than a flag, because "reduced" alone is not a
    # useful thing to tell someone: a view showing a tenth of its triangles and one showing 99% of them
    # are both reduced, and only one is worth looking at twice.
    reduction: ReductionPlan | None = None

    def __post_init__(self) -> None:
        if self.points_m.ndim != 2 or self.points_m.shape[1] != 3:
            raise ValueError("display points are an (n, 3) array")
        if self.triangles.ndim != 2 or (self.triangles.size and self.triangles.shape[1] != 3):
            raise ValueError(
                "display geometry is triangles; a renderer that receives a polygon tessellates it "
                "itself, at a moment nothing records"
            )
        if self.source_points.shape != (self.points_m.shape[0],):
            raise ValueError(
                "every display point says which dataset point it came from, or the map is not a map"
            )
        if self.source_cells.shape != (self.triangles.shape[0],):
            raise ValueError("every display triangle says which dataset cell it came from")

    @property
    def is_reduced(self) -> bool:
        return self.reduction is not None and self.reduction.needed
