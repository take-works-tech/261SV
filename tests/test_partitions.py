"""A partitioned dataset gives the same numbers as the same dataset in one piece (INV-010).

The reader merges nothing, so every point on a partition interface arrives once per piece touching it.
The over-count is small enough to look plausible and large enough to be wrong, which is the whole
reason this is an invariant rather than a nicety.

These run with no VTK: the ghost array is a byte per entry and the arithmetic is numpy.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.association import Association
from domain_core.case_contents import AxisKind, CaseContents, ResultAxis
from domain_core.dataset import Dataset, Field
from domain_core.partitions import (
    GHOST_ARRAY_NAME,
    Aggregate,
    CellGhost,
    Partitioning,
    PointGhost,
    counted,
)
from domain_core.reported_value import Provenance

# A bar of four cells along x, as one piece: five points, values rising along it.
WHOLE_VALUES = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

# The same bar cut between cell 1 and cell 2. The point at x=2 is on the interface and arrives in both
# pieces, so the concatenation has six points where the mesh has five. The second copy is the one the
# writer marks.
SPLIT_VALUES = np.array([10.0, 20.0, 30.0, 30.0, 40.0, 50.0])
SPLIT_GHOSTS = np.array([0, 0, 0, PointGhost.DUPLICATE, 0, 0], dtype=np.uint8)


def bar(
    values: np.ndarray,
    *,
    ghosts: np.ndarray | None = None,
    parts: int = 1,
    ghost_level: int = 0,
    unit: str | None = "MPa",
) -> Dataset:
    count = values.size
    return Dataset(
        points_m=np.array([[float(i), 0.0, 0.0] for i in range(count)]),
        cells=np.array([[i, i + 1] for i in range(count - 1)]),
        fields={"stress": Field("stress", Association.POINT, values, unit=unit)},
        ghosts={} if ghosts is None else {Association.POINT: ghosts},
        partitioning=Partitioning(parts=parts, ghost_level=ghost_level),
    )


class TestTheNumberIsTheSameEitherWay:
    """The check INV-010 names: the number reported over the pieces equals the number over the whole."""

    @pytest.mark.parametrize("aggregate", ["total", "mean", "maximum"])
    def test_a_partitioned_dataset_reports_what_the_whole_one_does(self, aggregate: str) -> None:
        whole = getattr(bar(WHOLE_VALUES), aggregate)("stress")
        split = getattr(bar(SPLIT_VALUES, ghosts=SPLIT_GHOSTS, parts=2), aggregate)("stress")

        assert split.value == whole.value

    def test_ignoring_the_mark_is_what_gets_it_wrong(self) -> None:
        """Not a test of this product - a demonstration that the mark is load-bearing. Summing the
        pieces as they arrive over-counts by exactly one interface point."""
        assert SPLIT_VALUES.sum() == WHOLE_VALUES.sum() + 30.0

    def test_the_count_of_entries_excludes_the_duplicate(self) -> None:
        split = bar(SPLIT_VALUES, ghosts=SPLIT_GHOSTS, parts=2)

        assert split.counted_entries("stress").value == 5.0
        assert split.point_count == 6


class TestWhatIsRefusedWhenNothingIsMarked:
    """A `.pvtu` at the default GhostLevel="0" carries no ghost array, so the duplicates cannot be
    identified. Merging by coordinate would need a tolerance, and a tolerance welds a crack face shut -
    it turns a visible over-count into an invisible change of geometry."""

    def test_a_sum_over_unmarked_pieces_is_refused_with_a_reason(self) -> None:
        total = bar(SPLIT_VALUES, parts=2).total("stress")

        assert total.is_missing
        assert GHOST_ARRAY_NAME in (total.missing_because or "")
        assert "INV-010" in (total.missing_because or "")

    def test_a_mean_over_unmarked_pieces_is_refused(self) -> None:
        assert bar(SPLIT_VALUES, parts=2).mean("stress").is_missing

    def test_the_extremum_is_still_reported(self) -> None:
        """The largest of a set is the largest of that set with part of it written twice. Refusing it
        would cost the number an engineer actually reports, for no gain in correctness."""
        assert bar(SPLIT_VALUES, parts=2).maximum("stress").value == 50.0

    def test_one_piece_refuses_nothing(self) -> None:
        assert bar(WHOLE_VALUES).total("stress").value == 150.0

    def test_cells_are_refused_only_once_ghost_layers_exist(self) -> None:
        """At ghost level 0 each cell belongs to exactly one piece, so a cell quantity is already
        exact; an interface repeats points, not cells."""
        flat = Partitioning(parts=8, ghost_level=0)
        layered = Partitioning(parts=8, ghost_level=1)

        assert flat.refusal(Aggregate.TOTAL, Association.CELL, marked=False) is None
        assert layered.refusal(Aggregate.TOTAL, Association.CELL, marked=False) is not None
        assert flat.refusal(Aggregate.TOTAL, Association.POINT, marked=False) is not None


class TestTheTwoVocabulariesDoNotMix:
    """Bit 2 is HIDDENPOINT for a point and HIGHCONNECTIVITYCELL for a cell, and both arrays are named
    vtkGhostType. A mask built without the association drops every high-connectivity cell from an
    integral - a wrong number that looks right."""

    def test_bit_two_hides_a_point_and_keeps_a_cell(self) -> None:
        byte = np.array([2], dtype=np.uint8)

        assert not counted(byte, Association.POINT)[0]  # the point is hidden
        assert counted(byte, Association.CELL)[0]  # the cell is merely well connected

    def test_the_excluded_cell_bits_are_the_ones_the_integrator_skips(self) -> None:
        """E-131: vtkIntegrateAttributes skips DUPLICATECELL and HIDDENCELL and consults no other bit.
        The remaining bits describe a cell; they do not disqualify it."""
        described = np.array(
            [
                CellGhost.HIGH_CONNECTIVITY,
                CellGhost.LOW_CONNECTIVITY,
                CellGhost.REFINED,
                CellGhost.EXTERIOR,
            ],
            dtype=np.uint8,
        )

        assert counted(described, Association.CELL).all()
        assert not counted(
            np.array([CellGhost.DUPLICATE, CellGhost.HIDDEN], dtype=np.uint8), Association.CELL
        ).any()

    def test_a_wider_ghost_array_is_refused_rather_than_reinterpreted(self) -> None:
        with pytest.raises(ValueError) as refusal:
            counted(np.array([0, 1], dtype=np.int32), Association.CELL)
        assert "unsigned bytes of flags" in str(refusal.value)

    def test_a_mask_that_does_not_line_up_is_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            bar(WHOLE_VALUES, ghosts=np.zeros(3, dtype=np.uint8))
        assert "excludes the wrong ones" in str(refusal.value)


class TestTheSurveyIsTheAuthorityOnTheParts:
    def test_the_partitioning_comes_from_what_was_counted(self) -> None:
        """A caller restating the part count could restate it wrongly, and the count decides which
        numbers get refused."""
        dataset = Dataset(
            points_m=np.zeros((2, 3)),
            cells=np.array([[0, 1]]),
            contents=CaseContents(steps=1, parts=4, axis=ResultAxis(AxisKind.NONE), ghost_level=2),
            partitioning=Partitioning(parts=1),
        )

        assert dataset.partitioning == Partitioning(parts=4, ghost_level=2)


class TestARefusalIsNotAnAbsentValue:
    def test_a_refused_number_says_why_and_carries_its_formula(self) -> None:
        total = bar(SPLIT_VALUES, parts=2).total("stress")

        assert total.provenance is Provenance.COMPUTED
        assert total.formula == "total(stress)"
        assert total.missing_because

    def test_a_field_with_a_missing_entry_refuses_rather_than_averaging_the_rest(self) -> None:
        """INV-011 and XC-001. A mean over the entries that happened to be there is read as the mean of
        the field, and nothing in the digits says otherwise."""
        holed = bar(np.array([10.0, np.nan, 30.0]))

        assert holed.mean("stress").is_missing
        assert "3 件のうち 1 件が欠損" in (holed.mean("stress").missing_because or "")

    def test_a_count_is_dimensionless_even_when_the_field_has_no_unit(self) -> None:
        undeclared = bar(WHOLE_VALUES, unit=None)

        assert undeclared.counted_entries("stress").unit == "1"
        assert undeclared.maximum("stress").unit is None
