"""Display geometry: the triangulated, possibly reduced surface a picture is drawn from.

This is MOD-003's work and not the reader's, which is why it takes a @Dataset rather than a toolkit
object. A boundary that only holds because the reader hands the renderer something extra is not a
boundary; if this cannot be done from a @Dataset alone then the @Dataset is not the product's model of
a result.

Three guarantees live here, and they are the three tasks this module closes:

* **the reduction is marked, with its size** (ingest/AC-030). The surface says how many triangles it
  drew out of how many there were, not merely that it is reduced;
* **nothing reported comes from it** (ingest/AC-031, INV-001). Reported numbers read `Dataset.fields`,
  which this module never touches - structurally, rather than by each call site remembering;
* **it is computed once** (ingest/TASK-017). Decimating a million-triangle surface costs seconds, and a
  view redrawn is a view redrawn, not a case reloaded.

**The decimator is `vtkDecimatePro` and the reason is correctness, not quality.** Measured on a 977,200
triangle sphere reduced to a tenth: `vtkDecimatePro` carries `vtkOriginalPointIds` through and moves no
surviving point, while `vtkQuadricDecimation` **drops the array entirely** (E-134). A reduced surface
built with the second one cannot answer a pick at all, because nothing remains that says which dataset
point a vertex was.

Specification: MOD-003, INV-001, LIM-002, ingest/AC-030, AC-031. Evidence: E-132 (T1), E-134 (T1).
"""

from __future__ import annotations

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkUnstructuredGrid
from vtkmodules.vtkFiltersCore import vtkDecimatePro, vtkTriangleFilter
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

from domain_core.dataset import Dataset
from domain_core.mesh import DisplayGeometry
from domain_core.reduction import ReductionPlan, plan_reduction
from engine.limits import MAX_INTERACTIVE_TRIANGLES

ORIGINAL_POINT_IDS = "vtkOriginalPointIds"
ORIGINAL_CELL_IDS = "vtkOriginalCellIds"


def _as_grid(dataset: Dataset) -> vtkUnstructuredGrid:
    """The @Dataset back in the toolkit's own shape, with no value changed.

    The three connectivity arrays go across as they are, which is the whole reason `Cells` uses the
    toolkit's layout: this is a copy rather than a conversion, and a conversion here would be one nobody
    asked for on a path that runs every time a view opens.
    """
    points = vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(dataset.points_m), deep=True))

    cells = vtkCellArray()
    cells.SetData(
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.offsets), deep=True, array_type=12),
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.connectivity), deep=True, array_type=12),
    )

    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(numpy_to_vtk(np.ascontiguousarray(dataset.cells.types), deep=True, array_type=3), cells)
    return grid


def _surface(grid: vtkUnstructuredGrid) -> vtkPolyData:
    """The triangulated boundary, carrying the map back to the points and cells it came from."""
    surface = vtkDataSetSurfaceFilter()
    surface.SetInputData(grid)
    surface.PassThroughPointIdsOn()
    surface.PassThroughCellIdsOn()
    triangles = vtkTriangleFilter()
    triangles.SetInputConnection(surface.GetOutputPort())
    triangles.Update()
    return triangles.GetOutput()


def _decimate(surface: vtkPolyData, plan: ReductionPlan) -> vtkPolyData:
    """Remove triangles until the plan is met, without moving the ones that remain.

    `PreserveTopology` and `BoundaryVertexDeletion` off keep the silhouette and the holes: a reduced
    picture that closed a hole would be showing a different part.
    """
    decimator = vtkDecimatePro()
    decimator.SetInputData(surface)
    decimator.SetTargetReduction(plan.fraction_removed)
    decimator.PreserveTopologyOn()
    decimator.SetSplitting(False)
    decimator.SetBoundaryVertexDeletion(False)
    decimator.Update()
    return decimator.GetOutput()


def _triangles(surface: vtkPolyData) -> np.ndarray:
    connectivity = vtk_to_numpy(surface.GetPolys().GetConnectivityArray())
    offsets = vtk_to_numpy(surface.GetPolys().GetOffsetsArray())
    sizes = np.diff(offsets)
    if sizes.size and not np.all(sizes == 3):
        raise ValueError("display geometry is triangles; something in this path stopped triangulating")
    return connectivity.reshape(-1, 3).astype(np.int64, copy=False)


def _map_back(surface: vtkPolyData, name: str, container: str, expected: int) -> np.ndarray:
    data = surface.GetPointData() if container == "point" else surface.GetCellData()
    array = data.GetArray(name)
    if array is None:
        raise ValueError(
            f"the display surface lost '{name}', so nothing says which dataset {container} each of its "
            f"own {container}s was. A picked vertex would answer with a real value from the wrong place "
            "(INV-001, E-134)"
        )
    values = vtk_to_numpy(array).astype(np.int64, copy=True)
    if values.size != expected:
        raise ValueError(f"'{name}' has {values.size} entries for {expected} {container}s")
    return values


def display_geometry(
    dataset: Dataset, *, budget: int = MAX_INTERACTIVE_TRIANGLES
) -> DisplayGeometry:
    """The surface this @Dataset is drawn as, reduced to the budget, computed once and kept.

    Reported numbers are not affected by any of this: they are read from `Dataset.fields`, which nothing
    here touches (INV-001).
    """
    cached = dataset.display_by_budget.get(budget)
    if cached is not None:
        return cached

    surface = _surface(_as_grid(dataset))
    plan = plan_reduction(surface.GetNumberOfCells(), budget=budget)
    if plan.needed:
        # The cell ids do not survive decimation - a decimated triangle is not one of the originals -
        # so the surviving triangles are traced back through their own points instead.
        surface = _decimate(surface, plan)

    points = vtk_to_numpy(surface.GetPoints().GetData()).astype(np.float64, copy=True)
    triangles = _triangles(surface)
    source_points = _map_back(surface, ORIGINAL_POINT_IDS, "point", points.shape[0])
    if plan.needed:
        # Every triangle of a decimated surface spans points that were in the original, so the cell it
        # belongs to is recovered from them rather than claimed. A triangle whose three points came from
        # different cells belongs to none of them, and says so with -1 rather than picking one.
        source_cells = _cells_from_points(dataset, source_points, triangles)
    else:
        source_cells = _map_back(surface, ORIGINAL_CELL_IDS, "cell", triangles.shape[0])

    geometry = DisplayGeometry(
        points_m=points,
        triangles=triangles,
        source_points=source_points,
        source_cells=source_cells,
        reduction=plan,
    )
    dataset.display_by_budget[budget] = geometry
    return geometry


def _cells_from_points(
    dataset: Dataset, source_points: np.ndarray, triangles: np.ndarray
) -> np.ndarray:
    """Which dataset cell each decimated triangle lies in, or -1 where no single cell holds all three.

    -1 rather than a nearest guess: a decimated triangle can span a cell boundary, and answering with
    one of the cells it partly covers would attach a cell value to a place that value is not true of.
    """
    holders: dict[int, set[int]] = {}
    for cell in range(dataset.cells.count):
        for point in dataset.cells.points_of(cell):
            holders.setdefault(int(point), set()).add(cell)

    found = np.full(triangles.shape[0], -1, np.int64)
    for index, corners in enumerate(triangles):
        shared: set[int] | None = None
        for corner in corners:
            owners = holders.get(int(source_points[corner]), set())
            shared = owners if shared is None else (shared & owners)
            if not shared:
                break
        if shared:
            found[index] = min(shared)
    return found
