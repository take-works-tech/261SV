"""The picture is reduced and says so; the numbers are not (ingest/AC-030, AC-031, INV-001).

Needs VTK, because the point of these is that the toolkit's own filters behave as the specification
assumes - which is a thing to check rather than to believe.

Verifies: ingest/AC-030, AC-031, ingest/TASK-015, TASK-016, TASK-017.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

import numpy as np  # noqa: E402

from domain_core.dataset import Dataset  # noqa: E402
from engine import reader  # noqa: E402
from engine.visualization.display import display_geometry  # noqa: E402
from test_reader import write_block  # noqa: E402


@pytest.fixture
def block(tmp_path: Path) -> Dataset:
    """A 3x3x3 block of hexahedra: 27 points, 8 cells, 48 display triangles, one interior point."""
    write_block(tmp_path / "block.vtu")
    return reader.read(tmp_path / "block.vtu")


class TestTheReductionIsMarked:
    def test_a_surface_inside_the_budget_is_not_reduced(self, block: Dataset) -> None:
        display = display_geometry(block)

        assert display.is_reduced is False
        assert display.triangles.shape[0] == 48

    def test_a_surface_above_the_budget_is_cut_and_says_by_how_much(self, block: Dataset) -> None:
        display = display_geometry(block, budget=12)

        assert display.is_reduced is True
        assert display.triangles.shape[0] <= 12
        assert "48" in display.reduction.describe()
        assert "間引く前の全データ" in display.reduction.describe()

    def test_the_surviving_points_are_where_they_were(self, block: Dataset) -> None:
        """E-134: vtkDecimatePro removes vertices and moves none of the ones it keeps, which is what
        lets a reduced surface still answer a pick. vtkQuadricDecimation drops the map entirely."""
        display = display_geometry(block, budget=12)

        for index, source in enumerate(display.source_points.tolist()):
            assert display.points_m[index].tolist() == block.points_m[source].tolist()

    def test_a_triangle_spanning_cells_belongs_to_none_of_them(self, block: Dataset) -> None:
        """A decimated triangle can cross a cell boundary. Answering with one of the cells it partly
        covers would attach a cell value to a place that value is not true of, so it answers -1."""
        display = display_geometry(block, budget=12)

        assert set(display.source_cells.tolist()) <= set(range(block.cell_count)) | {-1}


class TestTheNumbersAreNotReduced:
    def test_the_maximum_on_a_reduced_view_is_the_full_data_maximum(self, block: Dataset) -> None:
        """AC-031 and INV-001, as a number: the largest value in this block is at its centre, and the
        centre is not on the surface at all - reduced or otherwise."""
        before = block.maximum("stress").value

        display_geometry(block, budget=12)

        assert block.maximum("stress").value == before == 260.0

    def test_reducing_does_not_touch_the_fields(self, block: Dataset) -> None:
        values = block.fields["stress"].values.copy()

        display_geometry(block, budget=12)
        display_geometry(block, budget=6)

        assert np.array_equal(block.fields["stress"].values, values)
        assert block.point_count == 27
        assert block.cell_count == 8


class TestItIsComputedOnce:
    def test_the_same_budget_returns_the_same_object(self, block: Dataset) -> None:
        """TASK-017. Decimating a 2.25-million-triangle surface to a tenth was measured at 22.3
        seconds (spike/results.json); a view redrawn is a view redrawn, not a case reloaded."""
        first = display_geometry(block, budget=12)

        assert display_geometry(block, budget=12) is first

    def test_two_budgets_are_two_entries(self, block: Dataset) -> None:
        """Two views of one @Case may have different budgets, and the second must not evict the first."""
        display_geometry(block, budget=12)
        display_geometry(block, budget=6)

        assert sorted(block.display_by_budget) == [6, 12]

    def test_nothing_is_computed_until_it_is_asked_for(self, block: Dataset) -> None:
        """Reading a file draws nothing. Producing display geometry is MOD-003's work, and a reader
        that did it anyway would pay for a picture nobody had asked to see."""
        assert block.display_by_budget == {}
