"""Comparing two cases whose meshes differ, and saying what that cost.

XC-038 permits it and attaches a price: the user names the basis, and four things travel with every
number - direction, outside-point count and proportion, round-trip error on the same scale, and the
fact that the visible difference is physical difference **plus** discretisation **plus** interpolation.
Its fifth rule is the one the tasks do not name: where the difference is the same order as the
round-trip error, the region is undetermined rather than coloured.

Needs VTK: the resampling is the toolkit's, and the trap this guards against is its default behaviour.

Verifies: diff/AC-005 to AC-008, diff/TASK-007 to TASK-010.
"""

from __future__ import annotations

import numpy as np
import pytest
from conftest import requires_vtk

requires_vtk()

from domain_core.association import Association  # noqa: E402
from domain_core.dataset import Dataset, Field  # noqa: E402
from domain_core.mesh import Cells  # noqa: E402
from engine.analysis.difference import DiffError, cross_mesh_difference  # noqa: E402
from engine.analysis.resample import (  # noqa: E402
    VALID_POINT_MASK,
    ResampleError,
    resample,
    round_trip_error,
)


def strip(xs: list[float], values: list[float], unit: str | None = "MPa") -> Dataset:
    """A ribbon of triangles along x, with one value per point, duplicated on the y=1 row."""
    count = len(xs)
    points = np.array([[x, 0.0, 0.0] for x in xs] + [[x, 1.0, 0.0] for x in xs])
    offsets = [0]
    connectivity: list[int] = []
    for index in range(count - 1):
        connectivity += [index, index + 1, count + index]
        offsets.append(offsets[-1] + 3)
        connectivity += [index + 1, count + index + 1, count + index]
        offsets.append(offsets[-1] + 3)
    cells = Cells(
        np.array(offsets, np.int64),
        np.array(connectivity, np.int64),
        np.full(len(offsets) - 1, 5, np.uint8),
    )
    return Dataset(
        points_m=points,
        cells=cells,
        fields={
            "stress": Field("stress", Association.POINT, np.array(values + values), unit=unit)
        },
    )


COARSE = strip([0.0, 1.0, 2.0, 3.0], [0.0, 10.0, 20.0, 30.0])
FINE = strip([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0], [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0])


class TestOutsidePointsAreMissingRatherThanZero:
    def test_the_toolkit_writes_zero_there(self) -> None:
        """Not a test of this product - the measurement this module exists for. `vtkResampleWithDataSet`
        marks the point invalid **and writes 0.0 into the field**, and zero in a difference reads as
        "these agree"."""
        from vtkmodules.util.numpy_support import vtk_to_numpy
        from vtkmodules.vtkFiltersCore import vtkResampleWithDataSet

        from engine.analysis.resample import _as_grid

        reaching_out = strip([0.5, 1.5, 9.0], [0.0, 0.0, 0.0])
        filter_ = vtkResampleWithDataSet()
        filter_.SetInputData(_as_grid(reaching_out))
        filter_.SetSourceData(_as_grid(COARSE, COARSE.field("stress")))
        filter_.Update()
        data = filter_.GetOutput().GetPointData()

        mask = vtk_to_numpy(data.GetArray(VALID_POINT_MASK)).astype(bool)
        raw = vtk_to_numpy(data.GetArray("stress"))
        assert (raw[~mask] == 0.0).all()

    def test_this_product_replaces_them_with_missing(self) -> None:
        """AC-007: reported as missing, never extrapolated."""
        reaching_out = strip([0.5, 1.5, 9.0], [0.0, 0.0, 0.0])

        carried = resample(COARSE, reaching_out, "stress", from_case="coarse", onto="out")

        assert np.isnan(carried.values[~carried.inside]).all()
        assert carried.outside_count == 2  # the far point on each row

    def test_the_count_and_proportion_are_reported(self) -> None:
        reaching_out = strip([0.5, 1.5, 9.0], [0.0, 0.0, 0.0])

        carried = resample(COARSE, reaching_out, "stress", from_case="coarse", onto="out")

        assert carried.outside_fraction == pytest.approx(2 / 6)
        assert "外挿はしません" in carried.describe()

    def test_a_fully_covered_target_says_there_were_none(self) -> None:
        carried = resample(COARSE, FINE, "stress", from_case="coarse", onto="fine")

        assert carried.outside_count == 0
        assert "範囲外の点はありません" in carried.describe()

    def test_the_interpolation_itself_is_linear_and_correct(self) -> None:
        carried = resample(COARSE, FINE, "stress", from_case="coarse", onto="fine")

        assert carried.values[1] == pytest.approx(5.0)

    def test_cell_data_is_refused_rather_than_treated_as_points(self) -> None:
        """Treating a cell value as a point value asserts it was at the centroid, which nothing said."""
        cells_only = Dataset(
            points_m=COARSE.points_m, cells=COARSE.cells,
            fields={
                "stress": Field(
                    "stress", Association.CELL, np.zeros(COARSE.cell_count), unit="MPa"
                )
            },
        )

        with pytest.raises(ResampleError):
            resample(cells_only, FINE, "stress", from_case="a", onto="b")


class TestTheRoundTripErrorIsMeasured:
    def test_a_linear_field_survives_a_round_trip_almost_exactly(self) -> None:
        """Linear interpolation of a linear field is exact, so this is the floor rather than a typical
        figure - and a method whose floor is not zero would be worth knowing about."""
        largest, _ = round_trip_error(COARSE, FINE, "stress")

        assert largest == pytest.approx(0.0, abs=1e-9)

    def test_a_curved_field_does_not(self) -> None:
        """Whatever the interpolation cost, it cost at least this."""
        curved = strip([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 4.0, 9.0])
        coarser = strip([0.0, 3.0], [0.0, 9.0])

        largest, _ = round_trip_error(curved, coarser, "stress")

        assert largest > 1.0


class TestTheDirectionIsNamedByTheCaller:
    def test_a_basis_that_is_neither_case_is_refused(self) -> None:
        """AC-005. The two directions give different numbers, and picking one is an engineering
        decision made on the user's behalf."""
        with pytest.raises(DiffError) as refusal:
            cross_mesh_difference(
                COARSE, FINE, "stress", left_case="coarse", right_case="fine", onto="somewhere"
            )
        assert "利用者に代わって下した技術判断" in str(refusal.value)

    def test_the_result_says_which_mesh_it_sits_on(self) -> None:
        result = cross_mesh_difference(
            COARSE, FINE, "stress", left_case="coarse", right_case="fine", onto="fine"
        )

        assert result.onto == "fine"
        assert "fine 上に再サンプリング" in result.provenance

    def test_the_difference_is_left_minus_right_whichever_mesh_it_sits_on(self) -> None:
        higher = strip([0.0, 1.0, 2.0, 3.0], [1.0, 11.0, 21.0, 31.0])

        onto_left = cross_mesh_difference(
            higher, FINE, "stress", left_case="high", right_case="fine", onto="high"
        )
        onto_right = cross_mesh_difference(
            higher, FINE, "stress", left_case="high", right_case="fine", onto="fine"
        )

        assert np.nanmean(onto_left.field.values) > 0
        assert np.nanmean(onto_right.field.values) > 0

    def test_differing_units_are_refused_before_resampling(self) -> None:
        in_pascals = strip([0.0, 1.0, 2.0, 3.0], [0.0, 10.0, 20.0, 30.0], unit="Pa")

        with pytest.raises(DiffError):
            cross_mesh_difference(
                COARSE, in_pascals, "stress", left_case="a", right_case="b", onto="a"
            )


class TestWhatTravelsWithTheNumber:
    def test_the_disclosure_carries_all_four_things(self) -> None:
        """AC-008, and XC-038 lists them: direction, outside count and proportion, round-trip error,
        and the statement that three contributions are in the number."""
        result = cross_mesh_difference(
            COARSE, FINE, "stress", left_case="coarse", right_case="fine", onto="fine"
        )

        line = result.disclosure()
        assert "fine 上に再サンプリング" in line
        assert "範囲外" in line and "%" in line
        assert "往復補間誤差" in line
        assert "物理的な差・離散化・補間" in line

    def test_a_difference_no_larger_than_the_round_trip_error_is_undetermined(self) -> None:
        """XC-038's fifth rule, which the tasks do not name. A difference smaller than the
        interpolation that produced it is not a small difference - it is a number the method cannot
        resolve, and shading it faintly says "almost no change here" when the honest statement is "this
        method cannot tell"."""
        curved = strip([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 4.0, 9.0])
        nearly_the_same = strip([0.0, 1.5, 3.0], [0.0, 2.3, 9.0])

        result = cross_mesh_difference(
            curved, nearly_the_same, "stress", left_case="a", right_case="b", onto="a"
        )

        assert result.round_trip_error > 0
        assert result.undetermined_count > 0
        assert "判定できない領域" in result.disclosure()

    def test_the_undetermined_mask_lines_up_with_the_field(self) -> None:
        result = cross_mesh_difference(
            COARSE, FINE, "stress", left_case="coarse", right_case="fine", onto="fine"
        )

        assert result.undetermined.shape == result.field.values.shape

    def test_the_result_is_a_field_with_the_source_unit(self) -> None:
        result = cross_mesh_difference(
            COARSE, FINE, "stress", left_case="coarse", right_case="fine", onto="fine"
        )

        assert result.field.unit == "MPa"
        assert result.field.name == "Δstress"
