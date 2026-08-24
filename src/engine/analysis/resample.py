"""Comparing two cases whose meshes differ, and saying what that cost.

XC-038 permits this and attaches a price to it: the user chooses the basis, and the comparison reports
**four things beside every number** - the direction, the count and proportion of points that fell
outside the source, the round-trip interpolation error on the same scale as the difference, and the
fact that the visible difference is physical difference **plus** discretisation **plus** interpolation.
And a fifth rule the tasks do not name: where the difference is the same order as the round-trip error,
the region is **undetermined rather than coloured**.

**The measured trap.** `vtkResampleWithDataSet` marks points outside the source in `vtkValidPointMask`
and writes **0.0** into the field at those points (E-140). A product that took the field as returned
would hand an engineer a page of zeros in the region where its mesh did not reach - and zero in a
difference reads as "these agree". So the mask is applied and those points become missing, which is
what E-056 records the reference tools doing right and Tecplot doing without.

**The round-trip error is measured, not estimated.** Resample onto the target and back again, and
compare with what was there before. Whatever the interpolation cost, it cost at least that, and it is
in the same unit as the difference so the two can be compared at all.

Specification: XC-038, GL-011, INV-011, diff/AC-005 to AC-008. Evidence: E-056 (T1), E-140 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkUnstructuredGrid
from vtkmodules.vtkFiltersCore import vtkResampleWithDataSet

from domain_core.association import Association
from domain_core.dataset import Dataset, Field

#: The mask the filter writes, and the reason this module exists in the shape it does. Points outside
#: the source are 0 here and **0.0 in the field**, which is a measured value as far as anything
#: downstream can tell (E-140).
VALID_POINT_MASK = "vtkValidPointMask"


class ResampleError(Exception):
    """Raised when a cross-mesh comparison cannot be made honestly."""


@dataclass(frozen=True, slots=True)
class Resampled:
    """One field carried onto another mesh, with what that cost."""

    values: np.ndarray
    #: True where the target point was inside the source. False points are **missing** in `values`,
    #: never zero and never extrapolated (AC-007).
    inside: np.ndarray
    onto: str
    from_case: str

    @property
    def outside_count(self) -> int:
        return int((~self.inside).sum())

    @property
    def outside_fraction(self) -> float:
        return float(self.outside_count / self.inside.size) if self.inside.size else 0.0

    def describe(self) -> str:
        if not self.outside_count:
            return f"{self.from_case} を {self.onto} 上に再サンプリングしました（範囲外の点はありません）"
        return (
            f"{self.from_case} を {self.onto} 上に再サンプリングしました。"
            f"{self.outside_count} 点（{self.outside_fraction * 100:.1f}%）が元メッシュの外にあり、"
            "欠測としています — 外挿はしません"
        )


def _as_grid(dataset: Dataset, field: Field | None = None) -> vtkUnstructuredGrid:
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
    if field is not None:
        array = numpy_to_vtk(np.ascontiguousarray(field.values.astype(np.float64)), deep=True)
        array.SetName(field.name)
        grid.GetPointData().AddArray(array)
    return grid


def resample(
    source: Dataset,
    target: Dataset,
    name: str,
    *,
    from_case: str,
    onto: str,
) -> Resampled:
    """Carry one field from a source mesh onto a target mesh, marking what fell outside.

    `onto` is named by the caller and never chosen here (AC-005): the two directions give different
    numbers, and a product that picks one has made an engineering decision on the user's behalf.
    """
    field = source.field(name)
    if field.association is not Association.POINT:
        raise ResampleError(
            f"'{name}' は {field.association.value} データです。"
            "セル値の再サンプリングはセル中心の扱いを決めてからにします — "
            "点として扱うと、セルの値がその重心にあったことにしてしまいます"
        )

    filter_ = vtkResampleWithDataSet()
    filter_.SetInputData(_as_grid(target))
    filter_.SetSourceData(_as_grid(source, field))
    filter_.Update()
    output = filter_.GetOutput().GetPointData()

    mask_array = output.GetArray(VALID_POINT_MASK)
    values_array = output.GetArray(name)
    if mask_array is None or values_array is None:
        raise ResampleError(
            f"再サンプリングの結果に {VALID_POINT_MASK} または '{name}' がありません。"
            "どの点が範囲外かを言えないまま値を返すことはしません"
        )

    inside = vtk_to_numpy(mask_array).astype(bool)
    values = vtk_to_numpy(values_array).astype(np.float64, copy=True)
    # The measured trap (E-140): the filter writes 0.0 outside the source, and zero in a difference
    # reads as "these agree". Replaced with missing, which is what the field actually holds there.
    values[~inside] = np.nan

    return Resampled(values=values, inside=inside, onto=onto, from_case=from_case)


def round_trip_error(source: Dataset, target: Dataset, name: str) -> tuple[float, np.ndarray]:
    """How much the interpolation itself moved the numbers, in the field's own unit.

    Measured rather than estimated: carry the field onto the target and back again, and compare with
    what was there before. Whatever the interpolation cost, it cost at least this - and it is in the
    same unit as the difference, which is what lets XC-038's last rule compare the two at all.

    Returns the largest error and the per-point errors, both over points that survived both hops.
    """
    forward = resample(source, target, name, from_case="source", onto="target")
    carried = Dataset(
        points_m=target.points_m,
        cells=target.cells,
        fields={name: Field(name, Association.POINT, forward.values, unit=source.field(name).unit)},
    )
    back = resample(carried, source, name, from_case="target", onto="source")

    original = source.field(name).values.astype(np.float64)
    error = np.abs(back.values - original)
    # A point that fell outside on either hop has no round-trip to measure. Excluded rather than
    # counted as zero error, which would make a mesh that barely overlaps look like a perfect one.
    error[~back.inside] = np.nan
    finite = error[np.isfinite(error)]
    return (float(finite.max()) if finite.size else float("nan")), error
