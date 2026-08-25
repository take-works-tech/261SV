"""The weights a summary statistic is weighted by, measured on the canonical geometry.

Separate from `summary.py` on purpose: the rules about what a reduction is and how it is labelled hold
without a toolkit and are tested without one, while the volumes themselves come from VTK. A module that
mixed the two would make every test of the labelling rule need a mesh.

The volumes are computed on `Dataset.points_m`, which is float64 and refuses to be anything else
(XC-245). That is not incidental here - this is the multiplication that carries a coordinate's error
into the reported average (E-142).

Specification: INV-017, XC-245, graph/AC-022.
"""

from __future__ import annotations

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkUnstructuredGrid
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter

from domain_core.dataset import Dataset

#: The names the size filter writes. Set explicitly rather than left to the filter's defaults, so a
#: default that changes between toolkit versions is a build failure here rather than a missing array.
VOLUME_ARRAY = "Volume"
AREA_ARRAY = "Area"


def _as_grid(dataset: Dataset) -> vtkUnstructuredGrid:
    points = vtkPoints()
    # float64 in, float64 stored. `vtkPoints` would otherwise hold single precision, which costs about
    # 5e-8 of relative error in a cell volume (E-142).
    points.SetData(numpy_to_vtk(np.ascontiguousarray(dataset.points_m), deep=True))
    cells = vtkCellArray()
    cells.SetData(
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.offsets), deep=True, array_type=12),
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.connectivity), deep=True, array_type=12),
    )
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.types), deep=True, array_type=3), cells
    )
    return grid


def _sizes(dataset: Dataset) -> vtkUnstructuredGrid:
    sizes = vtkCellSizeFilter()
    sizes.SetInputData(_as_grid(dataset))
    sizes.ComputeVolumeOn()
    sizes.ComputeAreaOn()
    sizes.ComputeLengthOff()
    sizes.ComputeVertexCountOff()
    sizes.SetVolumeArrayName(VOLUME_ARRAY)
    sizes.SetAreaArrayName(AREA_ARRAY)
    sizes.Update()
    return sizes.GetOutput()


def cell_volumes(dataset: Dataset) -> np.ndarray:
    """Each cell's volume in cubic metres, for weighting cell data (INV-017).

    A cell with no volume - a triangle, a line - contributes zero. That is the honest figure rather than
    an error: a mesh may hold both, and a volume-weighted mean over a scope that is entirely surface
    comes back unavailable through `summarise`, which is the right place for that refusal.
    """
    volumes = _sizes(dataset).GetCellData().GetArray(VOLUME_ARRAY)
    if volumes is None:
        raise RuntimeError(
            f"体積配列 '{VOLUME_ARRAY}' がツールキットから返りませんでした。"
            "名前を明示しているので、これは既定名の変更ではなくフィルタの失敗です"
        )
    return vtk_to_numpy(volumes).astype(np.float64, copy=True)


def cell_areas(dataset: Dataset) -> np.ndarray:
    """Each cell's area in square metres, for weighting a surface mesh that has no volume."""
    areas = _sizes(dataset).GetCellData().GetArray(AREA_ARRAY)
    if areas is None:
        raise RuntimeError(f"面積配列 '{AREA_ARRAY}' がツールキットから返りませんでした")
    return vtk_to_numpy(areas).astype(np.float64, copy=True)


def point_weights(dataset: Dataset) -> np.ndarray:
    """Each point's share of the volume around it (INV-017's dual-volume weighting).

    Built from this product's own connectivity rather than from a toolkit filter, so the rule is
    visible: each cell's volume divided equally among the points it uses, which sums back to the total.
    A weighting that did not sum back would make the average depend on how the mesh was cut.
    """
    from engine.analysis.summary import dual_volumes

    volumes = cell_volumes(dataset)
    offsets = dataset.cells.offsets
    connectivity = dataset.cells.connectivity
    cells = [
        connectivity[offsets[index]: offsets[index + 1]] for index in range(len(offsets) - 1)
    ]
    return dual_volumes(volumes, cells, dataset.point_count)
