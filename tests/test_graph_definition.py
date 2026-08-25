"""A graph as a definition: what it plots, in what unit, from where - and what it refuses to draw.

AC-004 is the one the rest hangs on: a graph stores its **definition**, never its plotted values. A
figure that cached its numbers would still draw after the study changed, showing last week's answer
under this week's title, and it would look right.

INV-013 is the reason every series carries a provenance. The variable list deliberately mixes values a
person typed with values a solver produced (XC-088); mixing them invisibly would make every number in
the product unfalsifiable.

The refusal worth reading twice is the mixed one. A declared series and an undeclared one on one axis
reads as a comparison, and nothing ever said the undeclared series was in the same unit.

Verifies: graph/AC-001 to AC-004, graph/TASK-001 to TASK-003, INV-013, XC-003, XC-131.
"""

from __future__ import annotations

import json

import pytest

from domain_core.case_contents import AxisKind, ResultAxis
from engine.graph.definition import (
    PROJECTIONS,
    THREE_DIMENSIONAL,
    KINDS,
    UNDECLARED_MARKER,
    GraphError,
    Provenance,
    Series,
    SourceKind,
    add_series,
    axis_label,
    new_graph,
    note_result_axes,
    read_series,
    refusal_for,
    describe_projection,
    projection_of,
    stored_values,
)


def stress(label: str = "応力", unit: str | None = "MPa") -> Series:
    return Series(label, SourceKind.FIELD, Provenance.DATASET, unit=unit, field_name="stress")


class TestASeriesSaysWhatItIs:
    def test_it_records_the_quantity_the_unit_and_the_provenance(self) -> None:
        """AC-001, INV-013."""
        line = stress().describe()

        assert "応力" in line
        assert "MPa" in line
        assert "ファイル由来" in line

    def test_a_computed_series_carries_its_expression(self) -> None:
        """INV-013's last clause. A computed value without its expression is a number nobody can
        check."""
        computed = Series(
            "余裕", SourceKind.DERIVED, Provenance.COMPUTED,
            unit="MPa", expression="yield_stress - peak",
        )

        assert "yield_stress - peak" in computed.describe()

    def test_a_computed_series_without_one_is_refused(self) -> None:
        with pytest.raises(GraphError) as refusal:
            Series("余裕", SourceKind.DERIVED, Provenance.COMPUTED, unit="MPa")
        assert "INV-013" in str(refusal.value)

    def test_reference_material_names_where_it_came_from(self) -> None:
        with pytest.raises(GraphError):
            Series("規格値", SourceKind.REFERENCE_FILE, Provenance.REFERENCE, unit="MPa")

    def test_the_provenance_vocabulary_is_the_products_one_and_not_a_second(self) -> None:
        """GL-016's five, from `domain_core.reported_value`. The first version of this module defined
        its own four, calling the file origin `read` where the rest of the product calls it `dataset` -
        which would have made the same value look like two things depending on which module printed it.

        There is no member for "unknown": a value whose origin nobody recorded is not a kind of origin,
        it is a value this product should not be plotting, so there is nowhere to put it."""
        from domain_core.reported_value import Provenance as Canonical

        assert Provenance is Canonical
        assert {p.value for p in Provenance} == {
            "declared", "dataset", "computed", "measured", "reference"
        }

    def test_a_unit_this_product_does_not_know_is_refused_when_the_series_is_made(self) -> None:
        with pytest.raises(GraphError):
            stress(unit="furlong")

    def test_an_empty_unit_string_is_refused_rather_than_read_as_undeclared(self) -> None:
        """Two ways to say "no unit" is one too many, and the empty string reads as a unit that happens
        to print as nothing."""
        with pytest.raises(GraphError):
            stress(unit="")


class TestAnUndeclaredUnitIsMarkedRatherThanAssumed:
    def test_the_axis_carries_the_marker(self) -> None:
        """AC-002, XC-003."""
        assert axis_label([stress(unit=None)]) == UNDECLARED_MARKER

    def test_a_declared_axis_says_the_unit_the_numbers_are_in(self) -> None:
        """The internal unit of the quantity, not whichever symbol the first series happened to use -
        that would be a number shown in one unit and labelled with another."""
        assert axis_label([stress(unit="MPa")]) == "Pa"

    def test_an_empty_graph_has_no_unit_to_claim(self) -> None:
        assert axis_label([]) == UNDECLARED_MARKER

    def test_the_marker_has_one_spelling(self) -> None:
        """So a graph, a table and a report cannot disagree about how the same absence is written."""
        assert UNDECLARED_MARKER in stress(unit=None).describe()


class TestIncompatibleUnitsAreRefusedNamingBoth:
    def test_a_length_beside_a_time(self) -> None:
        """AC-003."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, Series("長さ", SourceKind.FIELD, Provenance.DATASET, unit="mm"))

        with pytest.raises(GraphError) as refusal:
            add_series(graph, Series("時間", SourceKind.FIELD, Provenance.DATASET, unit="s"))

        assert "mm" in str(refusal.value) and "s" in str(refusal.value)

    def test_the_same_quantity_in_two_units_is_allowed(self) -> None:
        """MPa and kPa are the same quantity, and the axis says what the numbers are in."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress("上面", "MPa"))
        add_series(graph, stress("下面", "kPa"))

        assert axis_label(read_series(graph)) == "Pa"

    def test_a_declared_series_beside_an_undeclared_one_is_refused(self) -> None:
        """The quiet one. The figure reads as a comparison, and nothing said the undeclared series was
        in the same unit."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress("上面", "MPa"))

        with pytest.raises(GraphError) as refusal:
            add_series(graph, stress("下面", None))

        assert "XC-003" in str(refusal.value)
        assert "下面" in str(refusal.value)

    def test_all_undeclared_together_is_allowed_and_marked(self) -> None:
        """AC-002 requires this to be possible: the axis says nobody declared a unit."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress("上面", None))
        add_series(graph, stress("下面", None))

        assert axis_label(read_series(graph)) == UNDECLARED_MARKER

    def test_one_series_has_nothing_to_disagree_with(self) -> None:
        assert refusal_for([stress()]) is None

    def test_a_refused_addition_leaves_the_definition_as_it_was(self) -> None:
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress("上面", "MPa"))

        with pytest.raises(GraphError):
            add_series(graph, Series("時間", SourceKind.FIELD, Provenance.DATASET, unit="s"))

        assert len(graph["series"]) == 1


class TestTheDefinitionIsWhatIsSaved:
    def test_no_plotted_value_is_stored(self) -> None:
        """AC-004. A figure that cached its numbers would still draw after the study changed."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress())
        add_series(
            graph,
            Series("余裕", SourceKind.DERIVED, Provenance.COMPUTED, unit="MPa", expression="a - b"),
        )

        assert stored_values(graph) == []

    def test_it_round_trips_through_json_unchanged(self) -> None:
        """A definition is a document, and a document that only survives in memory is not one."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress())

        assert json.loads(json.dumps(graph, ensure_ascii=False)) == graph

    def test_reading_it_back_gives_the_same_series(self) -> None:
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress())

        assert read_series(graph)[0].describe() == stress().describe()

    def test_a_stored_series_that_contradicts_itself_is_refused_on_the_way_out(self) -> None:
        """`unitDeclared: false` beside a unit. Which one is true is not something this can decide, so
        it says so rather than choosing."""
        graph = new_graph("graph:001", "比較", "line")
        add_series(graph, stress())
        graph["series"][0]["unitDeclared"] = False

        with pytest.raises(GraphError):
            read_series(graph)

    def test_a_kind_this_build_cannot_draw_is_refused_when_it_is_written(self) -> None:
        with pytest.raises(GraphError):
            new_graph("graph:001", "比較", "sankey")

    def test_the_kinds_are_the_nine_the_contract_lists(self) -> None:
        assert len(KINDS) == 9
        assert "overTime" in KINDS and "contour3d" in KINDS


class TestSeriesFromDifferentResultAxes:
    def test_a_mode_index_beside_a_time_is_stated(self) -> None:
        """XC-131. The horizontal position means a different thing in each series, and a chart that
        said nothing would look ordinary."""
        graph = new_graph("graph:001", "比較", "line")

        note = note_result_axes(
            graph, [ResultAxis(AxisKind.TIME), ResultAxis(AxisKind.MODE)]
        )

        assert note is not None
        assert graph["resultAxisNote"] == note

    def test_one_axis_needs_no_note_and_leaves_none_behind(self) -> None:
        graph = new_graph("graph:001", "比較", "line")
        note_result_axes(graph, [ResultAxis(AxisKind.TIME), ResultAxis(AxisKind.MODE)])

        assert note_result_axes(graph, [ResultAxis(AxisKind.TIME)]) is None
        assert "resultAxisNote" not in graph

    def test_the_wording_comes_from_one_place(self) -> None:
        """A display site that phrased this itself would be one more place for it to go missing."""
        from domain_core.case_contents import differing_axes

        graph = new_graph("graph:001", "比較", "line")
        axes = [ResultAxis(AxisKind.TIME), ResultAxis(AxisKind.FREQUENCY)]

        assert note_result_axes(graph, axes) == differing_axes(*axes)


class TestAThreeDimensionalGraphSaysHowItIsRead:
    """AC-025 and AC-026. A surface read from one angle is a different claim from another."""

    def test_the_three_kinds_over_two_variables_are_offered(self) -> None:
        assert THREE_DIMENSIONAL == {"surface3d", "scatter3d", "contour3d"}
        assert THREE_DIMENSIONAL <= KINDS

    def test_they_are_named_rather_than_matched_by_their_suffix(self) -> None:
        """A rule reading "ends in 3d" is a rule a kind called `volume` would escape."""
        assert "surface3d" in THREE_DIMENSIONAL
        assert all(not kind.endswith("3d") or kind in THREE_DIMENSIONAL for kind in KINDS)

    def test_one_without_a_projection_is_refused(self) -> None:
        """No default. A default view direction is an angle nobody chose."""
        with pytest.raises(GraphError) as refusal:
            projection_of(new_graph("graph:001", "面", "surface3d"))

        assert "AC-026" in str(refusal.value)

    def test_a_projection_this_product_does_not_know_is_refused(self) -> None:
        graph = new_graph("graph:001", "面", "surface3d")
        graph["projection"] = {"kind": "isometric", "viewDirection": [0, 0, 1]}

        with pytest.raises(GraphError):
            projection_of(graph)

    def test_a_projection_with_no_direction_is_refused(self) -> None:
        """A projection without a direction has not said which angle it was read from."""
        graph = new_graph("graph:001", "面", "surface3d")
        graph["projection"] = {"kind": "orthographic"}

        with pytest.raises(GraphError):
            projection_of(graph)

    def test_a_complete_one_is_stated_in_words(self) -> None:
        graph = new_graph("graph:001", "面", "surface3d")
        graph["projection"] = {"kind": "perspective", "viewDirection": [1, 0, 0]}

        assert describe_projection(graph) == "透視投影・視線方向 (1, 0, 0)"

    def test_a_flat_graph_has_no_projection_to_state(self) -> None:
        """Rather than an empty one, which would read as a projection nobody recorded."""
        assert describe_projection(new_graph("graph:001", "線", "line")) is None
        assert projection_of(new_graph("graph:001", "線", "line")) is None

    def test_the_two_projections_are_the_contracts(self) -> None:
        assert PROJECTIONS == {"orthographic", "perspective"}
