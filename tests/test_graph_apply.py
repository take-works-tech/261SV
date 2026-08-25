"""Applying a graph template to a different study, and what it says about what did not come across.

XC-090: a template applies as far as it resolves and names what it could not. The property that makes
this honest rather than convenient is that an unresolved series **stays** - removing it would make the
applied graph look complete and quietly smaller than the one it came from, and the series module already
draws a quantity it cannot find as no data with a reason.

AC-017 asks for the scope to be shown. A template that resolved from the shared library and one that
resolved from this workspace behave identically and travel differently, and only the scope says which.

Verifies: graph/AC-017 to AC-019, graph/TASK-012, TASK-013, XC-090, XC-109, CT-008.
"""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from engine.analysis.expression import Value, quantity
from engine.graph.apply import (
    SCOPE_WORD,
    STYLEABLE,
    Scope,
    accept,
    apply_template,
    series_requirements,
    unresolved_of,
)
from engine.graph.definition import (
    GraphError,
    Provenance,
    Series,
    SourceKind,
    add_series,
    new_graph,
)
from engine.graph.series import Repeats, figure, missing_report


def a_template() -> dict[str, Any]:
    graph = new_graph("template:001", "毎回の応力比較", "line")
    add_series(
        graph,
        Series("上面の最大応力", SourceKind.FIELD, Provenance.DATASET, unit="MPa", field_name="peak_top"),
    )
    add_series(
        graph,
        Series(
            "下面の最大応力", SourceKind.FIELD, Provenance.DATASET, unit="MPa", field_name="peak_bottom"
        ),
    )
    return graph


HELD: dict[str, dict[str, Value]] = {
    "case:001": {"peak_top": quantity(150.0, "MPa")},
    "case:002": {"peak_top": quantity(180.0, "MPa")},
}


def quantities_of(case: str) -> Mapping[str, Value]:
    return HELD[case]


class TestRequirementsComeFromTheDefinition:
    def test_the_quantities_a_graph_needs_are_read_from_its_series(self) -> None:
        """A promise written by hand beside the thing it describes is one that stops matching after the
        third edit."""
        assert series_requirements(a_template()) == ("peak_top", "peak_bottom")

    def test_a_computed_series_is_not_counted_as_a_field_requirement(self) -> None:
        """An expression's names are the evaluator's business, and a second parser here would be a
        second answer."""
        graph = new_graph("template:002", "余裕", "line")
        add_series(
            graph,
            Series(
                "余裕", SourceKind.DERIVED, Provenance.COMPUTED,
                unit="MPa", expression="yield_stress - peak",
            ),
        )

        assert series_requirements(graph) == ()


class TestATemplateAppliesAsFarAsItResolves:
    def test_the_resolved_series_come_across(self) -> None:
        """AC-018."""
        applied = apply_template(
            a_template(), available=["peak_top"], scope=Scope.SHARED
        )

        assert applied.resolved == ("上面の最大応力",)

    def test_the_unresolved_one_is_named_with_what_it_wanted(self) -> None:
        """AC-019: listed, by name and by what was missing."""
        applied = apply_template(
            a_template(), available=["peak_top"], scope=Scope.SHARED
        )

        assert len(applied.missing) == 1
        assert applied.missing[0].label == "下面の最大応力"
        assert applied.missing[0].needed == "peak_bottom"

    def test_the_unresolved_series_stays_in_the_definition(self) -> None:
        """Removing it would make the applied graph look complete and quietly smaller than the one it
        came from, which is the failure XC-090 exists to prevent."""
        applied = apply_template(
            a_template(), available=["peak_top"], scope=Scope.SHARED
        )

        assert len(applied.definition["series"]) == 2

    def test_and_is_therefore_drawn_as_no_data(self) -> None:
        """AC-019's second half, which needs nothing extra: the series module already draws a quantity
        it cannot find as no data with a reason."""
        from engine.graph.definition import read_series

        applied = apply_template(a_template(), available=["peak_top"], scope=Scope.SHARED)

        drawn = figure(
            read_series(applied.definition), list(HELD), quantities_of, repeats=Repeats.COMBINED
        )

        assert all("peak_bottom" in line for line in missing_report(drawn))
        assert len(missing_report(drawn)) == len(HELD)

    def test_everything_resolving_says_so(self) -> None:
        applied = apply_template(
            a_template(), available=["peak_top", "peak_bottom"], scope=Scope.WORKSPACE
        )

        assert applied.resolves_completely
        assert "すべてが解決" in applied.describe()

    def test_the_definition_is_a_copy(self) -> None:
        """XC-109: a shared structure would make a later edit to the template reach into a graph
        somebody already sent."""
        template = a_template()

        applied = apply_template(template, available=["peak_top"], scope=Scope.SHARED)
        applied.definition["series"][0]["label"] = "書き換えました"

        assert template["series"][0]["label"] == "上面の最大応力"


class TestTheScopeIsShown:
    def test_it_is_in_the_line_the_user_reads(self) -> None:
        """AC-017. A template from the shared library and one from this workspace behave identically and
        travel differently."""
        applied = apply_template(a_template(), available=[], scope=Scope.SHARED)

        assert SCOPE_WORD[Scope.SHARED] in applied.describe()

    def test_it_is_recorded_on_the_graph_that_was_made(self) -> None:
        """Somebody opening this graph next month reads the graph, not the dialogue that made it."""
        applied = apply_template(a_template(), available=["peak_top"], scope=Scope.SAMPLE)

        made = accept(applied, "graph:001", "今週の比較")

        assert made["appliedFromScope"] == "sample"

    def test_the_three_scopes_are_the_contracts_three(self) -> None:
        assert {scope.value for scope in Scope} == {"sample", "workspace", "shared"}

    def test_a_preview_from_the_workspace_carries_its_scope_too(self) -> None:
        """The generic machinery in MOD-007 shows the same thing for any kind of template."""
        from service.workspace.items import preview_application

        document: dict[str, Any] = {
            "templates": {
                "graphs": [
                    {
                        "id": "template:001", "revision": 2, "scope": "shared",
                        "definition": {}, "requirements": [{"kind": "field", "name": "peak_top"}],
                    }
                ]
            }
        }

        preview = preview_application(document, "graphs", "template:001", available=["peak_top"])

        assert preview.scope == "shared"
        assert "shared" in preview.describe()


class TestStyleResolvesSeparatelyFromStructure:
    def test_a_style_key_the_target_can_honour_is_applied(self) -> None:
        applied = apply_template(
            a_template(), available=["peak_top", "peak_bottom"], scope=Scope.SHARED,
            style={"axes": {"y": {"label": "応力"}}},
        )

        assert applied.definition["axes"] == {"y": {"label": "応力"}}

    def test_one_it_cannot_is_named_rather_than_ignored(self) -> None:
        """A style key nobody honours is a difference between two figures that neither of them shows."""
        applied = apply_template(
            a_template(), available=["peak_top", "peak_bottom"], scope=Scope.SHARED,
            style={"axes": {}, "glowIntensity": 3},
        )

        assert applied.style_dropped == ("glowIntensity",)
        assert "glowIntensity" in applied.describe()

    def test_a_style_may_not_change_which_numbers_are_plotted(self) -> None:
        """A style that could set the series is not a style."""
        assert "series" not in STYLEABLE

        applied = apply_template(
            a_template(), available=["peak_top", "peak_bottom"], scope=Scope.SHARED,
            style={"series": []},
        )

        assert len(applied.definition["series"]) == 2
        assert applied.style_dropped == ("series",)

    def test_a_partly_applied_style_still_applies_the_rest(self) -> None:
        """AC-017: partially where they resolve."""
        applied = apply_template(
            a_template(), available=["peak_top", "peak_bottom"], scope=Scope.SHARED,
            style={"kind": "scatter", "glowIntensity": 3},
        )

        assert applied.definition["kind"] == "scatter"
        assert applied.style_dropped == ("glowIntensity",)


class TestAcceptanceMakesSomethingIndependent:
    def test_the_gaps_were_on_screen_before_the_thing_was_made(self) -> None:
        """`accept` takes the resolution rather than the template, so a graph cannot be created without
        a resolution result having existed."""
        import inspect

        assert list(inspect.signature(accept).parameters)[0] == "applied"

    def test_what_was_unresolved_is_recorded_on_the_artefact(self) -> None:
        applied = apply_template(a_template(), available=["peak_top"], scope=Scope.SHARED)

        made = accept(applied, "graph:001", "今週の比較")

        assert unresolved_of(made)[0].needed == "peak_bottom"

    def test_a_graph_that_fully_resolved_records_nothing_to_explain(self) -> None:
        applied = apply_template(
            a_template(), available=["peak_top", "peak_bottom"], scope=Scope.SHARED
        )

        assert unresolved_of(accept(applied, "graph:001", "今週の比較")) == ()

    def test_a_template_with_no_series_makes_nothing(self) -> None:
        """An empty figure is indistinguishable from one that failed to resolve."""
        empty = new_graph("template:003", "空", "line")

        with pytest.raises(GraphError):
            accept(apply_template(empty, available=[], scope=Scope.SHARED), "graph:001", "空")

    def test_the_new_graph_carries_its_own_identity(self) -> None:
        applied = apply_template(a_template(), available=["peak_top"], scope=Scope.SHARED)

        made = accept(applied, "graph:001", "今週の比較")

        assert made["id"] == "graph:001"
        assert made["name"] == "今週の比較"
