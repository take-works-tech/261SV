"""The shipped sample, generated rather than collected (XC-129, XC-085, XC-298).

A cantilever beam of rectangular section, meshed with hexahedra and carrying the fields a structural
result carries - a stress, a displacement, an element stress - with values from Euler-Bernoulli beam
theory rather than from a solver: the bending stress `sigma = F (L - x) (y - h/2) / I` and the
deflection `w = F x^2 (3L - x) / (6 E I)`, with `I = b h^3 / 12`. Every number in the file follows
from the five constants below, so what the product reports about it can be checked by hand - the
maximum stress at the clamped end's surface is `F L (h/2) / I`, exactly - which is what a sample is
for. The file carries no unit, as a solver's would not (XC-003); the sample workspace declares them
as its author.

Written by the toolkit's own XML writer, so the file is a `.vtu` the product reads through the same
door as any other, and stored as float32 like a solver's output, so the digits the product shows are
the digits such a file supports (INV-014). Geometry is float64 (XC-245).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, vtkCellArray, vtkUnstructuredGrid
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter

from domain_core.os_paths import for_os

#: The beam: a metre long, a tenth of a metre high, a twentieth wide, and steel-like.
LENGTH_M = 1.0
HEIGHT_M = 0.1
WIDTH_M = 0.05
YOUNG_PA = 200.0e9
#: Hexahedra along, up and across: enough for a contour to read as one, few enough to open at once.
DIVISIONS = (40, 4, 2)

SECOND_MOMENT_M4 = WIDTH_M * HEIGHT_M**3 / 12.0


@dataclass(frozen=True, slots=True)
class SampleFacts:
    """What the written file holds, from the formulas, for a test or a reader to check against."""

    force_newton: float
    points: int
    cells: int
    #: The bending stress at the clamped end's top surface: `F L (h/2) / I`.
    maximum_stress_pa: float
    #: The deflection at the free end: `F L^3 / (3 E I)`.
    tip_deflection_m: float


def bending_stress_pa(x: np.ndarray, y: np.ndarray, force_newton: float) -> np.ndarray:
    return force_newton * (LENGTH_M - x) * (y - HEIGHT_M / 2.0) / SECOND_MOMENT_M4


def deflection_m(x: np.ndarray, force_newton: float) -> np.ndarray:
    return force_newton * x**2 * (3.0 * LENGTH_M - x) / (6.0 * YOUNG_PA * SECOND_MOMENT_M4)


def write_cantilever(path: str | Path, *, force_newton: float) -> SampleFacts:
    """Write the beam under a tip load of `force_newton` as a `.vtu`, and say what it holds."""
    nx, ny, nz = DIVISIONS
    xs = np.linspace(0.0, LENGTH_M, nx + 1)
    ys = np.linspace(0.0, HEIGHT_M, ny + 1)
    zs = np.linspace(0.0, WIDTH_M, nz + 1)
    # Point index = i + (nx + 1) * (j + (ny + 1) * k), so a hexahedron's corners are known by arithmetic.
    grid_x, grid_y, grid_z = np.meshgrid(xs, ys, zs, indexing="ij")
    coordinates = np.column_stack([grid_x.ravel(order="F"), grid_y.ravel(order="F"), grid_z.ravel(order="F")])

    def index(i: int, j: int, k: int) -> int:
        return i + (nx + 1) * (j + (ny + 1) * k)

    cells = vtkCellArray()
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                cells.InsertNextCell(8)
                # The toolkit's hexahedron order: the four corners of the lower face counter-clockwise,
                # then the four above them (E-215's fixture is built the same way).
                for corner in (
                    index(i, j, k), index(i + 1, j, k), index(i + 1, j + 1, k), index(i, j + 1, k),
                    index(i, j, k + 1), index(i + 1, j, k + 1), index(i + 1, j + 1, k + 1), index(i, j + 1, k + 1),
                ):
                    cells.InsertCellPoint(corner)

    points = vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(coordinates, dtype=np.float64), deep=True))
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(VTK_HEXAHEDRON, cells)

    x = coordinates[:, 0]
    y = coordinates[:, 1]
    stress = numpy_to_vtk(bending_stress_pa(x, y, force_newton).astype(np.float32), deep=True)
    stress.SetName("stress")
    grid.GetPointData().AddArray(stress)
    displacement = np.zeros((len(x), 3), dtype=np.float64)
    displacement[:, 1] = -deflection_m(x, force_newton)
    moved = numpy_to_vtk(np.ascontiguousarray(displacement.astype(np.float32)), deep=True)
    moved.SetName("displacement")
    grid.GetPointData().AddArray(moved)

    # Cell index = i + nx * (j + ny * k), the order the cells were inserted in above.
    centres_x = np.tile((xs[:-1] + xs[1:]) / 2.0, ny * nz)
    centres_y = np.tile(np.repeat((ys[:-1] + ys[1:]) / 2.0, nx), nz)
    element_stress = numpy_to_vtk(bending_stress_pa(centres_x, centres_y, force_newton).astype(np.float32), deep=True)
    element_stress.SetName("element_stress")
    grid.GetCellData().AddArray(element_stress)

    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(for_os(path)))
    writer.SetInputData(grid)
    if not writer.Write():
        raise OSError(f"{Path(path).name} を書けませんでした")
    return SampleFacts(
        force_newton=force_newton,
        points=(nx + 1) * (ny + 1) * (nz + 1),
        cells=nx * ny * nz,
        maximum_stress_pa=force_newton * LENGTH_M * (HEIGHT_M / 2.0) / SECOND_MOMENT_M4,
        tip_deflection_m=force_newton * LENGTH_M**3 / (3.0 * YOUNG_PA * SECOND_MOMENT_M4),
    )
