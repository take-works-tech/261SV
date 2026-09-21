"""The weights themselves, measured on a mesh whose elements differ by a factor of a thousand.

INV-017's `checked_by` asks for exactly this mesh: deliberately non-uniform element sizes, the two
reductions asserted different, each output carrying its weighting label. The labelling half is tested
without a toolkit in `test_summary.py`; this is the half where the volumes are real.

It is also where XC-245 earns its place. The two cubes here have sides 1.0 and 0.1, and 0.1 is not
exactly representable - which is precisely the case where single-precision coordinates put 4.5e-8 into
the volume and double precision puts nothing (E-142). A test written on cubes of side 1 and 2 would
agree in both precisions and prove nothing.

Needs VTK: the volumes are the toolkit's.

Verifies: INV-017, XC-245, graph/AC-022, graph/TASK-018.
"""

from __future__ import annotations

import numpy as np
import pytest
from conftest import VTK_HEXAHEDRON, requires_vtk

requires_vtk()

from domain_core.association import Association  # noqa: E402
from domain_core.dataset import Dataset, Field  # noqa: E402
from domain_core.mesh import Cells  # noqa: E402
from engine.analysis.summary import Reduction, Weighting, summarise  # noqa: E402
from engine.analysis.weights import WeightingError, cell_volumes, point_weights, toolkit_cell_volumes  # noqa: E402
from vtkmodules.vtkCommonDataModel import VTK_PYRAMID, VTK_TETRA, VTK_TRIANGLE, VTK_VOXEL, VTK_WEDGE  # noqa: E402


def two_cubes(big: float = 1.0, small: float = 0.1) -> Dataset:
    """One large cube and one small one, side by side and sharing no points.

    A thousand-to-one volume ratio, which is what makes the weighted and arithmetic means visibly
    different rather than differing in the last digits.
    """
    points: list[tuple[float, float, float]] = []
    connectivity: list[int] = []
    for origin, side in ((0.0, big), (2.0, small)):
        base = len(points)
        points += [
            (origin, 0.0, 0.0), (origin + side, 0.0, 0.0),
            (origin + side, side, 0.0), (origin, side, 0.0),
            (origin, 0.0, side), (origin + side, 0.0, side),
            (origin + side, side, side), (origin, side, side),
        ]
        connectivity += [base + index for index in range(8)]
    return Dataset(
        points_m=np.array(points, dtype=np.float64),
        cells=Cells(
            np.array([0, 8, 16], dtype=np.int64),
            np.array(connectivity, dtype=np.int64),
            np.full(2, VTK_HEXAHEDRON, dtype=np.uint8),
        ),
        fields={
            "stress": Field("stress", Association.CELL, np.array([10.0, 40.0]), unit="MPa"),
        },
    )


class TestTheVolumesAreTheToolkitsAndAreExact:
    def test_a_cube_measures_its_side_cubed(self) -> None:
        volumes = cell_volumes(two_cubes())

        assert volumes[0] == pytest.approx(1.0, rel=1e-15)
        assert volumes[1] == pytest.approx(1.0e-3, rel=1e-15)

    def test_the_small_cube_is_the_one_that_would_have_shown_the_error(self) -> None:
        """0.1 is not exactly representable. Single-precision coordinates put 4.5e-8 into this volume
        and double precision puts nothing (E-142), so the tolerance here is tighter than that gap on
        purpose - it is what would fail if the geometry stopped being float64."""
        volumes = cell_volumes(two_cubes())

        assert abs(volumes[1] - 1.0e-3) / 1.0e-3 < 1.0e-12

    def test_geometry_that_is_not_double_precision_is_refused_before_it_gets_here(self) -> None:
        """XC-245, at the one place that can enforce it."""
        with pytest.raises(ValueError) as refusal:
            Dataset(
                points_m=np.zeros((8, 3), dtype=np.float32),
                cells=two_cubes().cells,
            )
        assert "float64" in str(refusal.value)


class TestTheTwoReductionsDifferOnARealMesh:
    def test_the_weighted_mean_follows_the_volume(self) -> None:
        """INV-017's checked_by. The large cell holds 10 MPa and the small one 40 MPa, so a volume
        weighted mean sits near 10 and an arithmetic one sits at 25."""
        mesh = two_cubes()
        values = mesh.fields["stress"].values

        weighted = summarise(
            values, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=cell_volumes(mesh), unit="MPa",
        )
        arithmetic = summarise(
            values, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE, unit="MPa",
        )

        assert arithmetic.value == pytest.approx(25.0)
        assert weighted.value == pytest.approx(10.03, abs=0.01)
        assert weighted.value != arithmetic.value

    def test_each_output_carries_its_weighting_label(self) -> None:
        mesh = two_cubes()
        values = mesh.fields["stress"].values

        weighted = summarise(
            values, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=cell_volumes(mesh),
        )
        arithmetic = summarise(
            values, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert "体積加重" in weighted.describe()
        assert "重みなし" in arithmetic.describe()

    def test_the_gap_is_large_enough_to_change_a_verdict(self) -> None:
        """25 MPa against 10 MPa is not a rounding difference; it is the difference between a report
        that passes a limit and one that does not."""
        mesh = two_cubes()
        weighted = summarise(
            mesh.fields["stress"].values, reduction=Reduction.MEAN,
            association=Association.CELL, scope="全体", weights=cell_volumes(mesh),
        )

        assert abs((weighted.value or 0.0) - 25.0) > 14.0


class TestPointDataIsWeightedByTheVolumeAroundIt:
    def test_the_shares_sum_to_the_total_volume(self) -> None:
        mesh = two_cubes()

        shares = point_weights(mesh)

        assert float(np.sum(shares)) == pytest.approx(float(np.sum(cell_volumes(mesh))))

    def test_each_point_of_a_cube_gets_an_eighth_of_it(self) -> None:
        mesh = two_cubes()

        shares = point_weights(mesh)

        assert shares[0] == pytest.approx(1.0 / 8.0)
        assert shares[8] == pytest.approx(1.0e-3 / 8.0)

    def test_a_point_field_weighted_this_way_follows_the_large_cube(self) -> None:
        mesh = two_cubes()
        values = np.array([10.0] * 8 + [40.0] * 8)

        weighted = summarise(
            values, reduction=Reduction.MEAN, association=Association.POINT,
            scope="全体", weights=point_weights(mesh),
        )

        assert weighted.weighting is Weighting.DUAL_VOLUME
        assert weighted.value == pytest.approx(10.03, abs=0.01)


def test_the_hand_written_cell_type_is_the_toolkits_own() -> None:
    """The tests that build a mesh without VTK hold the code as a literal. This is where it is checked
    against the toolkit, so the copy cannot quietly stand for a different value."""
    from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON as FROM_TOOLKIT

    assert VTK_HEXAHEDRON == FROM_TOOLKIT


def one_cell(kind: int, corners: np.ndarray) -> Dataset:
    """One volume cell with a linear point field f = x, whose exact volume average is the centroid's x."""
    count = corners.shape[0]
    return Dataset(
        points_m=corners,
        cells=Cells(np.array([0, count]), np.arange(count), np.array([kind], dtype=np.uint8)),
        fields={"f": Field("f", Association.POINT, corners[:, 0].copy())},
    )


def volume_mean(dataset: Dataset) -> float:
    weights = point_weights(dataset)
    return float(np.sum(weights * dataset.fields["f"].values) / np.sum(weights))


BOX = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], dtype=np.float64)


class TestASharesIsTheIntegralOfItsShapeFunction:
    """XC-288, E-215: a point's share of a cell is the integral of its shape function, so the weighted
    mean of a linear field is the exact volume average on every linear cell - and the equal split it
    replaced was exact only on parallelepipeds and tetrahedra (E-214)."""

    def test_a_box_still_gives_each_corner_an_eighth(self) -> None:
        dataset = one_cell(VTK_HEXAHEDRON, BOX)

        assert point_weights(dataset) == pytest.approx(np.full(8, 0.125))
        assert cell_volumes(dataset) == pytest.approx([1.0])
        assert volume_mean(dataset) == pytest.approx(0.5)

    def test_a_skewed_hexahedron_reaches_the_interpolant_s_own_average_and_volume(self) -> None:
        """One corner pulled from (1,1,1) to (2,2,2). The equal split gave 0.625 and the toolkit's
        planar tetrahedra 0.75; the trilinear element's own average is 5/7 and its volume 7/4."""
        skewed = BOX.copy()
        skewed[6] = [2.0, 2.0, 2.0]
        dataset = one_cell(VTK_HEXAHEDRON, skewed)

        assert volume_mean(dataset) == pytest.approx(5.0 / 7.0)
        assert cell_volumes(dataset) == pytest.approx([1.75])
        assert float(np.sum(point_weights(dataset))) == pytest.approx(1.75)
        assert toolkit_cell_volumes(dataset) == pytest.approx([2.0]), "the reference this replaced, kept for the record"

    def test_a_cell_listed_the_other_way_round_has_the_same_volume(self) -> None:
        """A reversed corner order is a negative Jacobian; the toolkit's size filter reports a negative
        volume for it, and a weight is a volume."""
        flipped = BOX[[4, 5, 6, 7, 0, 1, 2, 3]]
        dataset = one_cell(VTK_HEXAHEDRON, flipped)

        assert cell_volumes(dataset) == pytest.approx([1.0])
        assert toolkit_cell_volumes(dataset) == pytest.approx([-1.0])
        assert volume_mean(dataset) == pytest.approx(0.5)

    def test_a_tetrahedron_gives_each_corner_a_quarter(self) -> None:
        dataset = one_cell(VTK_TETRA, np.array([[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4]], dtype=np.float64))

        assert point_weights(dataset) == pytest.approx(np.full(4, 1.0))
        assert cell_volumes(dataset) == pytest.approx([4.0])
        assert volume_mean(dataset) == pytest.approx(0.5)

    def test_a_wedge_gives_each_corner_a_sixth_and_keeps_its_volume_under_shear(self) -> None:
        right = np.array([[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4], [2, 0, 4], [0, 3, 4]], dtype=np.float64)
        sheared = right.copy()
        sheared[3:] += [1.0, 0.5, 0.0]

        assert point_weights(one_cell(VTK_WEDGE, right)) == pytest.approx(np.full(6, 2.0))
        assert volume_mean(one_cell(VTK_WEDGE, right)) == pytest.approx(2.0 / 3.0)
        assert cell_volumes(one_cell(VTK_WEDGE, sheared)) == pytest.approx([12.0])

    def test_a_pyramid_s_volume_is_exact_and_its_mean_is_its_centroid(self) -> None:
        pyramid = np.array([[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [1, 1, 3]], dtype=np.float64)
        dataset = one_cell(VTK_PYRAMID, pyramid)

        assert cell_volumes(dataset) == pytest.approx([4.0]), "base 2 x 2, height 3"
        assert float(np.sum(point_weights(dataset))) == pytest.approx(4.0)
        assert volume_mean(dataset) == pytest.approx(1.0)

    def test_a_cell_type_with_no_rule_is_refused_by_name(self) -> None:
        """A voxel is a hexahedron in another corner order; approximating it with the hexahedron's rule
        would be the wrong corners under the right formula."""
        with pytest.raises(WeightingError, match="vtkVoxel"):
            point_weights(one_cell(VTK_VOXEL, BOX))

    def test_a_surface_cell_in_a_volume_mesh_weighs_nothing_and_is_not_refused(self) -> None:
        corners = np.vstack([BOX, [[3.0, 0.0, 0.0], [4.0, 0.0, 0.0], [3.0, 1.0, 0.0]]])
        dataset = Dataset(
            points_m=corners,
            cells=Cells(np.array([0, 8, 11]), np.arange(11), np.array([VTK_HEXAHEDRON, VTK_TRIANGLE], dtype=np.uint8)),
            fields={"f": Field("f", Association.POINT, corners[:, 0].copy())},
        )

        assert cell_volumes(dataset) == pytest.approx([1.0, 0.0])
        assert point_weights(dataset)[8:] == pytest.approx([0.0, 0.0, 0.0])
