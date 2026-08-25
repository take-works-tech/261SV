"""Turning a graph definition into points, and what happens where a value is missing.

Every test here is about an absence. AC-013 wants a case that lacks the quantity drawn as no data and
**kept in the legend**, because dropping it makes the figure look complete - five cases plotted where
six were asked for, and nothing on the page saying which is gone. AC-007 wants an expression that fails
for one case to be that case's no-data rather than the series' deletion, because a vanished series takes
the other cases' answers with it.

AC-006 is the one about who computes: MOD-004 does, and the graph layer records what came back. A graph
that computed would be a second place where numbers are produced, and the two would disagree the day one
of them was fixed (XC-080, XC-088).

Verifies: graph/AC-005 to AC-007, AC-012, AC-013, graph/TASK-007 to TASK-011.
"""

from __future__ import annotations

from typing import Mapping

import pytest

from engine.analysis.expression import Value, quantity
from engine.graph.definition import GraphError, Provenance, Series, SourceKind
from engine.graph.series import (
    REPEAT_WORD,
    Figure,
    Quantity,
    Repeats,
    available_quantities,
    figure,
    missing_report,
    plot,
)

CASES = ["case:001", "case:002", "case:003"]

HELD: dict[str, dict[str, Value]] = {
    "case:001": {"peak": quantity(150.0, "MPa"), "yield_stress": quantity(250.0, "MPa")},
    "case:002": {"peak": quantity(240.0, "MPa"), "yield_stress": quantity(250.0, "MPa")},
    # case:003 was run with a different post-processing step and has no peak recorded.
    "case:003": {"yield_stress": quantity(250.0, "MPa")},
}


def quantities_of(case: str) -> Mapping[str, Value]:
    return HELD[case]


def peak() -> Series:
    return Series("最大応力", SourceKind.FIELD, Provenance.READ, unit="MPa", field_name="peak")


def margin() -> Series:
    return Series(
        "余裕", SourceKind.DERIVED, Provenance.COMPUTED,
        unit="MPa", expression="yield_stress - peak",
    )


class TestEveryQuantityIsOffered:
    def test_the_read_ones_come_from_the_cases(self) -> None:
        """AC-005."""
        offered = available_quantities(HELD)

        assert {q.name for q in offered} == {"peak", "yield_stress"}

    def test_a_quantity_only_some_cases_have_is_offered_once(self) -> None:
        """Offering it per case would put the same name on the list three times, and the cases that
        lack it become no-data points when it is plotted rather than a reason not to offer it."""
        assert sum(1 for q in available_quantities(HELD) if q.name == "peak") == 1

    def test_computed_and_reference_quantities_are_offered_beside_them(self) -> None:
        """A builder that offered only what came out of the solver would make the other two
        second-class, and they are the ones a comparison usually needs."""
        offered = available_quantities(
            HELD,
            computed=[Quantity("余裕", "MPa", Provenance.COMPUTED, "yield_stress - peak")],
            reference=[Quantity("規格値", "MPa", Provenance.REFERENCE)],
        )

        by_name = {q.name: q for q in offered}
        assert by_name["余裕"].provenance is Provenance.COMPUTED
        assert by_name["規格値"].provenance is Provenance.REFERENCE

    def test_each_offer_states_its_unit(self) -> None:
        offered = {q.name: q for q in available_quantities(HELD)}

        assert "MPa" in offered["peak"].describe()

    def test_an_undeclared_quantity_is_offered_with_the_marker(self) -> None:
        bare = {"case:009": {"ratio": Value(0.5)}}

        assert "宣言されていません" in available_quantities(bare)[0].describe()


class TestAMissingQuantityStaysVisible:
    def test_the_case_is_drawn_as_no_data(self) -> None:
        """AC-013."""
        drawn = plot(peak(), CASES, quantities_of)

        absent = next(point for point in drawn.points if point.case_id == "case:003")
        assert absent.missing
        assert "peak" in (absent.reason or "")

    def test_it_is_still_one_of_the_points(self) -> None:
        """Dropping it would make the figure look complete: two cases plotted where three were asked
        for, and nothing on the page saying which is gone."""
        drawn = plot(peak(), CASES, quantities_of)

        assert len(drawn.points) == len(CASES)

    def test_no_data_is_not_zero(self) -> None:
        """A missing value that arrives as zero is what XC-001 exists to prevent, so there is no numeric
        stand-in here to be mistaken for a measurement."""
        drawn = plot(peak(), CASES, quantities_of)

        assert next(p for p in drawn.points if p.case_id == "case:003").value is None

    def test_the_series_says_how_many_points_are_missing(self) -> None:
        assert "1 点はデータなし" in plot(peak(), CASES, quantities_of).describe()

    def test_a_series_with_nothing_plotted_still_appears_in_the_legend(self) -> None:
        nowhere = Series("見当たらない量", SourceKind.FIELD, Provenance.READ, field_name="absent")

        drawn = plot(nowhere, CASES, quantities_of)

        assert drawn.in_legend() == "見当たらない量（データなし）"

    def test_the_reason_names_what_the_case_does_have(self) -> None:
        """So somebody can see whether the quantity is misspelled or the case is."""
        drawn = plot(peak(), CASES, quantities_of)

        assert "yield_stress" in (drawn.points[2].reason or "")


class TestAnExpressionIsComputedElsewhere:
    def test_the_result_is_the_evaluators(self) -> None:
        """AC-006: computed in the analysis module, never in the graph layer."""
        drawn = plot(margin(), CASES, quantities_of)

        assert drawn.points[0].value == pytest.approx(1.0e8)  # 100 MPa in Pa
        assert drawn.points[1].value == pytest.approx(1.0e7)

    def test_the_expression_travels_with_the_series(self) -> None:
        """INV-013: a computed value carries the expression that produced it."""
        assert "yield_stress - peak" in margin().describe()

    def test_a_case_where_it_fails_is_that_cases_no_data(self) -> None:
        """AC-007. The series survives - one that vanished would take the other cases' answers with
        it."""
        drawn = plot(margin(), CASES, quantities_of)

        assert drawn.points[2].missing
        assert len(drawn.points) == 3
        assert drawn.points[0].value is not None

    def test_the_reason_is_the_evaluators_own(self) -> None:
        """Which is what tells somebody whether the expression is wrong or the case is."""
        drawn = plot(margin(), CASES, quantities_of)

        assert "peak" in (drawn.points[2].reason or "")

    def test_an_expression_whose_units_do_not_combine_fails_that_case_only(self) -> None:
        mixed = Series(
            "無理な計算", SourceKind.DERIVED, Provenance.COMPUTED,
            unit="MPa", expression="yield_stress + 1 s",
        )

        drawn = plot(mixed, CASES, quantities_of)

        assert drawn.missing_count == len(CASES)
        assert "INV-002" in (drawn.points[0].reason or "")

    def test_a_text_result_is_not_plotted_as_a_number(self) -> None:
        text = Series("文字", SourceKind.DERIVED, Provenance.COMPUTED, expression="'a'")

        assert plot(text, ["case:001"], quantities_of).points[0].missing


class TestRepeatsArePlottedDeliberately:
    def test_combining_keeps_every_repeats_points_under_one_label(self) -> None:
        """AC-012, and no averaging: an average is a number nobody asked for, and it would appear on the
        axis as though it had been measured."""
        drawn = figure(
            [peak()], CASES, quantities_of, repeats=Repeats.COMBINED,
            repeat_of=lambda case: "1 回目" if case != "case:003" else "2 回目",
        )

        assert len(drawn.series) == 1
        assert len(drawn.series[0].points) == 3

    def test_separating_gives_one_series_per_repeat(self) -> None:
        drawn = figure(
            [peak()], CASES, quantities_of, repeats=Repeats.PER_REPEAT,
            repeat_of=lambda case: "1 回目" if case != "case:003" else "2 回目",
        )

        assert [one.repeat for one in drawn.series] == ["1 回目", "2 回目"]
        assert [len(one.points) for one in drawn.series] == [2, 1]

    def test_which_was_used_is_stated(self) -> None:
        """Neither is a default applied silently. One drifting repeat is visible in the first and hidden
        in the second, and a product that picked would be choosing which of those somebody saw."""
        drawn = figure([peak()], CASES, quantities_of, repeats=Repeats.COMBINED)

        assert REPEAT_WORD[Repeats.COMBINED] in drawn.describe()
        assert drawn.repeats is Repeats.COMBINED

    def test_separating_without_a_rule_for_which_repeat_is_refused(self) -> None:
        """Grouping cases by similar names would be a grouping the user never stated."""
        with pytest.raises(GraphError):
            figure([peak()], CASES, quantities_of, repeats=Repeats.PER_REPEAT)

    def test_the_legend_order_is_stable(self) -> None:
        """Repeats appear in the order they first occur, so two runs of the same study produce the same
        legend."""
        order = lambda case: {"case:001": "b", "case:002": "a", "case:003": "b"}[case]  # noqa: E731

        drawn = figure([peak()], CASES, quantities_of, repeats=Repeats.PER_REPEAT, repeat_of=order)

        assert [one.repeat for one in drawn.series] == ["b", "a"]

    def test_a_missing_case_is_missing_in_whichever_mode(self) -> None:
        for mode, rule in (
            (Repeats.COMBINED, None),
            (Repeats.PER_REPEAT, lambda case: "1 回目"),
        ):
            drawn = figure([peak()], CASES, quantities_of, repeats=mode, repeat_of=rule)
            assert sum(one.missing_count for one in drawn.series) == 1


class TestWhatIsMissingIsAnswerableWithoutDrawing:
    def test_one_line_per_case_that_could_not_be_plotted(self) -> None:
        drawn = figure([peak(), margin()], CASES, quantities_of, repeats=Repeats.COMBINED)

        lines = missing_report(drawn)

        assert len(lines) == 2
        assert all("case:003" in line for line in lines)

    def test_a_complete_figure_reports_nothing(self) -> None:
        drawn = figure([peak()], CASES[:2], quantities_of, repeats=Repeats.COMBINED)

        assert missing_report(drawn) == ()

    def test_it_comes_from_the_figure_rather_than_from_the_drawing(self) -> None:
        """So a renderer that never ran still has the same answer about what is missing."""
        drawn = figure([peak()], CASES, quantities_of, repeats=Repeats.COMBINED)

        assert isinstance(drawn, Figure)
        assert missing_report(drawn) == missing_report(drawn)
