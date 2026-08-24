"""A number carries where it came from and what is qualified about it, everywhere it goes.

ingest/AC-027 asks that a missing part mark the @Dataset partial and that **every derived number carry
the mark**. That is a property of the value type rather than a rule each call site remembers - which is
the difference between a guarantee and a habit.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.case_contents import AxisKind, CaseContents, ResultAxis
from domain_core.dataset import Association, Dataset, Field
from domain_core.mesh import Cells
from domain_core.reported_value import (
    DIMENSIONLESS,
    Caveat,
    Provenance,
    ReportedValue,
    caveat_notes,
)


# One triangle over the three points. VTK type 5 is VTK_TRIANGLE.
TRIANGLE = Cells(np.array([0, 3], np.int64), np.arange(3, dtype=np.int64), np.array([5], np.uint8))


def partial_dataset() -> Dataset:
    """A dataset whose manifest named three parts and whose third was not there."""
    return Dataset(
        points_m=np.zeros((3, 3)),
        cells=TRIANGLE,
        fields={"stress": Field("stress", Association.POINT, np.array([1.0, 2.0, np.nan]))},
        contents=CaseContents(
            steps=1, parts=2, axis=ResultAxis(AxisKind.NONE), missing_parts=("run_2.vtu",),
        ),
    )


class TestTheMarkTravels:
    def test_a_value_read_from_a_partial_dataset_carries_the_mark(self) -> None:
        value = partial_dataset().value("stress", 0)

        assert Caveat.PARTIAL_DATASET in value.caveats
        assert "データセットの一部が欠落しています" in caveat_notes(value)

    def test_a_value_derived_from_it_still_carries_the_mark(self) -> None:
        """The one AC-027 is about. A ratio of a partial maximum to a declared allowable is still about
        a partial dataset, and the ratio is what somebody reads."""
        maximum = partial_dataset().value("stress", 1)
        allowable = ReportedValue(235.0, "MPa", 4, Provenance.DECLARED)

        safety = allowable.derive(
            235.0 / 2.0, formula="allowable / maximum", unit=DIMENSIONLESS, others=[maximum],
        )

        assert Caveat.PARTIAL_DATASET in safety.caveats

    def test_a_complete_dataset_adds_no_mark(self) -> None:
        complete = Dataset(
            points_m=np.zeros((3, 3)),
            cells=TRIANGLE,
            fields={"stress": Field("stress", Association.POINT, np.array([1.0, 2.0, 3.0]), unit="MPa")},
            contents=CaseContents(steps=1, parts=3, axis=ResultAxis(AxisKind.NONE)),
        )

        assert complete.is_partial is False
        assert complete.value("stress", 0).caveats == frozenset()

    def test_a_dataset_that_was_never_surveyed_claims_nothing(self) -> None:
        """Absent contents is not a claim of completeness - it is the absence of a survey, and it adds
        no caveat rather than asserting there is none to add."""
        unsurveyed = Dataset(points_m=np.zeros((1, 3)), cells=Cells.empty())

        assert unsurveyed.is_partial is False
        assert unsurveyed.caveats() == frozenset()


class TestWhatAValueRefusesToBe:
    def test_a_missing_value_stays_missing(self) -> None:
        """XC-001: no substituted zero, no previous value, no interpolated neighbour."""
        value = partial_dataset().value("stress", 2)

        assert value.is_missing
        assert value.value is None
        assert value.formatted() == "—"

    def test_an_undeclared_unit_is_marked_rather_than_left_blank(self) -> None:
        value = partial_dataset().value("stress", 0)

        assert value.unit is None
        assert Caveat.UNDECLARED_UNIT in value.caveats

    def test_a_value_with_no_unit_and_no_mark_is_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            ReportedValue(1.0, None, 4, Provenance.DATASET)
        assert "reads as a unit nobody needed" in str(refusal.value)

    def test_dimensionless_is_not_undeclared(self) -> None:
        """A safety factor has no unit because it has none; a stress with no unit has one nobody
        declared. Conflating them makes every ratio look like a defect."""
        ratio = ReportedValue(1.17, DIMENSIONLESS, 3, Provenance.COMPUTED, formula="a / b")

        assert ratio.unit == DIMENSIONLESS
        assert Caveat.UNDECLARED_UNIT not in ratio.caveats

    def test_a_computed_value_carries_its_formula(self) -> None:
        with pytest.raises(ValueError) as refusal:
            ReportedValue(1.0, "MPa", 4, Provenance.COMPUTED)
        assert "cannot be checked or reproduced" in str(refusal.value)


class TestPrecisionDoesNotGrow:
    def test_a_derived_value_is_no_more_precise_than_its_inputs(self) -> None:
        """XC-230: the result of a computation does not acquire digits its inputs never had."""
        coarse = ReportedValue(1.0, "MPa", 3, Provenance.DATASET)
        fine = ReportedValue(2.0, "MPa", 7, Provenance.DATASET)

        assert coarse.derive(0.5, formula="a / b", unit=DIMENSIONLESS, others=[fine]).digits == 3

    def test_a_value_carries_at_least_one_digit(self) -> None:
        with pytest.raises(ValueError):
            ReportedValue(1.0, "MPa", 0, Provenance.DATASET)

    def test_the_notes_are_in_a_fixed_order(self) -> None:
        """Two reports of the same value say the same thing in the same order."""
        value = ReportedValue(
            1.0, None, 3, Provenance.DATASET,
            frozenset({Caveat.UNDECLARED_UNIT, Caveat.PARTIAL_DATASET, Caveat.AVERAGED}),
        )

        assert caveat_notes(value) == [
            "データセットの一部が欠落しています",
            "セル間で平均した値です",
            "単位が宣言されていません",
        ]


class TestTheTwoSourcesOfIncompleteness:
    """Dataset already carried `partial`/`partial_reason` from the initial import - a flag whose
    docstring promised that "every derived number can say so" and which nothing read. The survey adds a
    second, structured source. One property answers the question, so no path can be incomplete in a way
    the other source does not see."""

    def test_a_recorded_incompleteness_marks_it_too(self) -> None:
        dataset = Dataset(points_m=np.zeros((1, 3)), cells=Cells.empty(),
                          fields={"s": Field("s", Association.POINT, np.array([1.0]), unit="MPa")})
        dataset.mark_partial("読み込み中に打ち切られました")

        assert dataset.is_partial
        assert dataset.incompleteness == "読み込み中に打ち切られました"
        assert Caveat.PARTIAL_DATASET in dataset.value("s", 0).caveats

    def test_a_surveyed_incompleteness_describes_the_parts(self) -> None:
        assert "run_2.vtu" in (partial_dataset().incompleteness or "")

    def test_a_complete_dataset_has_nothing_to_say(self) -> None:
        dataset = Dataset(points_m=np.zeros((1, 3)), cells=Cells.empty())

        assert dataset.incompleteness is None
