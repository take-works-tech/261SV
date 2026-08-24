"""A @Dataset holds the geometry it was read from and the geometry it is drawn as, and knows which.

INV-001 is a statement about two point sets. Until this existed the product kept one of them - the
drawn one - and hung the fields off it, so every index into a field named a different place than the
same index into the geometry (E-132).

No VTK: the shapes are numpy and the rule is arithmetic.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.association import Association
from domain_core.dataset import Dataset, Field
from domain_core.mesh import TRIANGLE_CELL, Cells, DisplayGeometry

# One hexahedron: eight corners, one cell, VTK type 12.
HEX = Cells(
    offsets=np.array([0, 8], np.int64),
    connectivity=np.arange(8, dtype=np.int64),
    types=np.array([12], np.uint8),
)
CORNERS = np.array(
    [[0.0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]
)


class TestConnectivityKeepsItsOwnShape:
    """A mesh of one cell type and a mesh of seven are the same shape in the toolkit's layout, which
    is the reason for using it: a product storing triangles as (n, 3) has to decide what to do the
    first time it meets a hexahedron, and it usually decides to triangulate."""

    def test_a_mixed_mesh_needs_no_special_case(self) -> None:
        mixed = Cells(
            offsets=np.array([0, 4, 12, 15], np.int64),   # tetra, hexahedron, triangle
            connectivity=np.arange(15, dtype=np.int64),
            types=np.array([10, 12, 5], np.uint8),
        )

        assert mixed.count == 3
        assert mixed.points_of(1).tolist() == list(range(4, 12))

    def test_a_type_per_cell_is_required(self) -> None:
        with pytest.raises(ValueError) as refusal:
            Cells(np.array([0, 3, 6], np.int64), np.arange(6, dtype=np.int64), np.array([5], np.uint8))
        assert "wrong number of corners" in str(refusal.value)

    def test_offsets_that_overrun_the_connectivity_are_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            Cells(np.array([0, 3, 9], np.int64), np.arange(6, dtype=np.int64), np.array([5, 5], np.uint8))
        assert "read past their own end" in str(refusal.value)

    def test_a_dataset_with_no_cells_is_allowed(self) -> None:
        cloud = Dataset(points_m=np.zeros((5, 3)), cells=Cells.empty())

        assert cloud.cell_count == 0
        assert cloud.point_count == 5


class TestAFieldBelongsToOneGeometry:
    """The check that turns a whole class of silent wrongness into a refusal at construction."""

    def test_a_point_field_of_the_wrong_length_is_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            Dataset(
                points_m=CORNERS,
                cells=HEX,
                fields={"s": Field("s", Association.POINT, np.arange(7.0), unit="MPa")},
            )
        assert "different geometry" in str(refusal.value)
        assert "real values from the wrong places" in str(refusal.value)

    def test_a_cell_field_is_checked_against_the_cells(self) -> None:
        with pytest.raises(ValueError):
            Dataset(
                points_m=CORNERS,
                cells=HEX,
                fields={"s": Field("s", Association.CELL, np.arange(8.0), unit="MPa")},
            )

    def test_the_lengths_that_do_correspond_are_accepted(self) -> None:
        dataset = Dataset(
            points_m=CORNERS,
            cells=HEX,
            fields={
                "point": Field("point", Association.POINT, np.arange(8.0), unit="MPa"),
                "cell": Field("cell", Association.CELL, np.arange(1.0), unit="MPa"),
            },
        )

        assert dataset.point_count == 8
        assert dataset.cell_count == 1


class TestDisplayGeometryKnowsWhatItCameFrom:
    def test_it_carries_the_map_back_to_the_dataset(self) -> None:
        """Surface extraction neither preserves the count nor the order - a 27-point block of hexahedra
        extracts to 26 surface points beginning 0, 1, 10, 9, 3 (E-132) - so a picked vertex has to be
        resolved through the map rather than by its own index."""
        display = DisplayGeometry(
            points_m=CORNERS[:4],
            triangles=np.array([[0, 1, 2], [0, 2, 3]], np.int64),
            source_points=np.array([0, 1, 10, 9], np.int64),
            source_cells=np.array([4, 4], np.int64),
        )

        assert display.source_points[2] == 10
        assert display.source_cells.tolist() == [4, 4]

    def test_display_points_without_a_map_are_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            DisplayGeometry(
                points_m=CORNERS[:4],
                triangles=np.array([[0, 1, 2]], np.int64),
                source_points=np.array([0, 1], np.int64),
                source_cells=np.array([0], np.int64),
            )
        assert "the map is not a map" in str(refusal.value)

    def test_display_geometry_is_triangles_only(self) -> None:
        """A renderer handed a polygon tessellates it itself, at a moment nothing records."""
        with pytest.raises(ValueError) as refusal:
            DisplayGeometry(
                points_m=CORNERS,
                triangles=np.array([[0, 1, 2, 3]], np.int64),
                source_points=np.arange(8, dtype=np.int64),
                source_cells=np.array([0], np.int64),
            )
        assert "tessellates it itself" in str(refusal.value)

    def test_a_dataset_may_have_none_yet(self) -> None:
        """Nothing has been drawn. That is different from having been drawn as itself."""
        assert Dataset(points_m=CORNERS, cells=HEX).display is None

    def test_the_triangle_type_is_the_toolkit_s(self) -> None:
        assert TRIANGLE_CELL == 5
