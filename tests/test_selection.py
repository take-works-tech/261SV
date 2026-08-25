"""Which cases a selection chooses, and why it chose none.

CT-007's declarative form has no arithmetic and no function calls, because a selection that can compute
is an evaluator and the reason this form is declarative is that it must not be one (XC-080).

Three refusals carry the weight. An **unknown condition** is refused rather than ignored, because
ignoring an unrecognised key is how a filter quietly becomes "everything". A **comparison with no unit**
is refused, because its answer depends on what the file happened to be written in. And an **empty
result names the condition that emptied it**, because an empty graph with no explanation reads as
"no data" when it means "your filter excluded everything".

The composed-unit half is here too: CT-007's own example compares against `m/s`, and until 2026-08-25
this product could not read that symbol at all.

Verifies: CT-007, graph/AC-008, AC-009, graph/TASK-004, TASK-005, XC-003, XC-080, GL-039.
"""

from __future__ import annotations

import pytest

from domain_core.dimension import parse_symbol, symbol_for
from domain_core.selection import (
    CONDITIONS,
    STATES,
    CaseFacts,
    SelectionError,
    VariableValue,
    describe_condition,
    resolve,
    selected_cases,
)

CASES = [
    CaseFacts(
        "case:001", "run_a", frozenset({"converged"}), "loaded",
        {"inlet": VariableValue(12.0, "m/s"), "mesh": VariableValue("coarse")},
    ),
    CaseFacts(
        "case:002", "draft_b", frozenset({"converged"}), "failed",
        {"inlet": VariableValue(8.0, "m/s")},
    ),
    CaseFacts("case:003", "run_c", frozenset(), "partial", {}),
]

CONVERGED_FAST = {
    "all": [
        {"tag": "converged"},
        {"variable": {"name": "inlet", "unit": "m/s", "greaterThan": 10}},
        {"not": {"name": {"startsWith": "draft_"}}},
    ]
}


class TestAComposedUnitCanBeDeclared:
    def test_a_velocity_is_read(self) -> None:
        """CT-007's own example compares against `m/s`, and the unit registry holds simple symbols
        only, so until this existed the contract's example could not be evaluated."""
        composed = parse_symbol("m/s")

        assert composed.dimension == parse_symbol("m").dimension.over(parse_symbol("s").dimension)
        assert composed.to_internal == 1.0

    def test_the_prefixes_are_carried_through(self) -> None:
        """mm/ms is m/s exactly, and a parser that dropped the prefixes would be out by a factor of one
        thousand in each direction and right by accident here."""
        assert parse_symbol("mm/ms").to_internal == pytest.approx(1.0)
        assert parse_symbol("mm/s").to_internal == pytest.approx(1.0e-3)

    def test_a_power_is_read(self) -> None:
        assert symbol_for(parse_symbol("kg/m^3").dimension) == "kg·m^-3"

    def test_an_offset_unit_may_not_be_part_of_one(self) -> None:
        """`degC/s` has no answer that survives the arithmetic: the gap between scaling first and
        converting first is the offset (E-141). A temperature rate is `K/s`."""
        with pytest.raises(ValueError) as refusal:
            parse_symbol("degC/s")
        assert "K/s" in str(refusal.value)

    def test_an_empty_exponent_is_refused_rather_than_read_as_one(self) -> None:
        """`m^` read as `m` accepts a typo as though it were a unit."""
        with pytest.raises(ValueError):
            parse_symbol("m^/s")

    def test_a_component_this_product_does_not_know_is_refused(self) -> None:
        with pytest.raises(Exception):
            parse_symbol("furlong/fortnight")


class TestTheDeclarativeFormChooses:
    def test_the_contracts_own_example(self) -> None:
        found = resolve(CONVERGED_FAST, CASES)

        assert found.selected == ("case:001",)

    def test_a_tag_is_what_a_person_decided(self) -> None:
        assert resolve({"tag": "converged"}, CASES).selected == ("case:001", "case:002")

    def test_a_state_is_what_the_product_observed(self) -> None:
        """GL-039: kept apart from tags, so "every case that failed" is answerable without anyone
        having tagged them."""
        assert resolve({"state": ["failed", "partial"]}, CASES).selected == (
            "case:002", "case:003"
        )

    def test_names_are_matched_not_evaluated(self) -> None:
        assert resolve({"name": {"startsWith": "run_"}}, CASES).selected == (
            "case:001", "case:003"
        )

    def test_a_pattern_has_no_capture_and_no_evaluation(self) -> None:
        assert resolve({"name": {"matches": "^run_[ac]$"}}, CASES).selected == (
            "case:001", "case:003"
        )

    def test_the_connectives_compose(self) -> None:
        both = {"any": [{"tag": "converged"}, {"state": ["partial"]}]}

        assert len(resolve(both, CASES).selected) == 3

    def test_naming_identifiers_directly_works(self) -> None:
        assert resolve({"caseIds": ["case:003"]}, CASES).selected == ("case:003",)

    def test_a_variable_that_is_absent_can_be_asked_about(self) -> None:
        assert resolve({"variable": {"name": "mesh", "exists": True}}, CASES).selected == (
            "case:001",
        )

    def test_a_non_numeric_variable_compares_by_equality(self) -> None:
        assert resolve(
            {"variable": {"name": "mesh", "equals": "coarse"}}, CASES
        ).selected == ("case:001",)


class TestAnEmptyResultNamesWhatEmptiedIt:
    def test_the_condition_is_named(self) -> None:
        """graph/AC-009. An empty graph with no explanation reads as "no data" when it means "your
        filter excluded everything", and those are different problems with different fixes."""
        found = resolve(
            {"all": [{"tag": "converged"}, {"variable": {"name": "inlet", "unit": "m/s", "greaterThan": 100}}]},
            CASES,
        )

        assert found.selected == ()
        assert "inlet" in (found.emptied_by or "")
        assert "100" in found.describe()

    def test_it_is_the_condition_that_emptied_it_rather_than_the_whole_tree(self) -> None:
        """Narrowed one condition at a time, so the answer is the step that did it."""
        found = resolve({"all": [{"tag": "nothing-has-this"}, {"tag": "converged"}]}, CASES)

        assert "nothing-has-this" in (found.emptied_by or "")

    def test_a_single_condition_that_matches_nothing_names_itself(self) -> None:
        found = resolve({"tag": "absent"}, CASES)

        assert "absent" in (found.emptied_by or "")

    def test_the_count_considered_is_reported(self) -> None:
        assert resolve({"tag": "absent"}, CASES).considered == 3

    def test_no_selection_at_all_chooses_nothing_and_says_so(self) -> None:
        """"No selection" and "select all" are different intentions, and the expensive direction is the
        one where a study silently covers every case in the workspace."""
        found = resolve(None, CASES)

        assert found.selected == ()
        assert found.emptied_by is not None


class TestRefusalBeatsIgnoring:
    def test_a_condition_this_build_does_not_know_is_refused(self) -> None:
        """Ignoring an unrecognised key is how a filter quietly becomes "everything"."""
        with pytest.raises(SelectionError) as refusal:
            resolve({"colour": "red"}, CASES)
        assert "CT-007" in str(refusal.value)

    def test_two_conditions_in_one_object_are_refused(self) -> None:
        with pytest.raises(SelectionError):
            resolve({"tag": "converged", "state": ["loaded"]}, CASES)

    def test_a_state_this_product_does_not_have_is_refused(self) -> None:
        """Never matching looks like a selection that found nothing, which is the wrong diagnosis."""
        with pytest.raises(SelectionError):
            resolve({"state": ["exploded"]}, CASES)

    def test_an_empty_connective_is_refused(self) -> None:
        with pytest.raises(SelectionError):
            resolve({"all": []}, CASES)

    def test_a_name_test_outside_the_four_is_refused(self) -> None:
        with pytest.raises(SelectionError):
            resolve({"name": {"endsWith": "_a"}}, CASES)

    def test_the_condition_vocabulary_is_the_contracts(self) -> None:
        assert CONDITIONS == {
            "all", "any", "not", "tag", "name", "variable", "caseIds", "state", "code"
        }
        assert len(STATES) == 6

    def test_the_code_form_is_refused_rather_than_returning_nothing(self) -> None:
        """CT-007: a failure is a refusal, not an empty result. An empty graph with no explanation reads
        as "no data" when it means "this build cannot run that"."""
        with pytest.raises(SelectionError) as refusal:
            resolve({"code": {"language": "python", "source": "return []"}}, CASES)

        assert "XC-089" in str(refusal.value)

    def test_the_refusal_happens_before_any_case_is_examined(self) -> None:
        """A selection that refused only on the case that triggered it would work until the data
        changed."""
        with pytest.raises(SelectionError):
            resolve({"all": [{"tag": "converged"}, {"colour": "red"}]}, [])


class TestAComparisonNeedsUnitsOnBothSides:
    def test_a_condition_with_no_unit_is_refused(self) -> None:
        """XC-003. Its answer would depend on what the file happened to be written in."""
        with pytest.raises(SelectionError) as refusal:
            resolve({"variable": {"name": "inlet", "greaterThan": 10}}, CASES)

        assert "XC-003" in str(refusal.value)

    def test_an_undeclared_variable_is_refused_too(self) -> None:
        undeclared = [CaseFacts("case:009", variables={"inlet": VariableValue(12.0)})]

        with pytest.raises(SelectionError):
            resolve({"variable": {"name": "inlet", "unit": "m/s", "greaterThan": 10}}, undeclared)

    def test_units_that_do_not_combine_are_refused(self) -> None:
        with pytest.raises(SelectionError):
            resolve({"variable": {"name": "inlet", "unit": "MPa", "greaterThan": 10}}, CASES)

    def test_the_comparison_converts_rather_than_comparing_raw_numbers(self) -> None:
        """12 m/s is 12000 mm/s, and a comparison against 10000 mm/s must say yes."""
        found = resolve(
            {"variable": {"name": "inlet", "unit": "mm/s", "greaterThan": 10000}}, CASES
        )

        assert found.selected == ("case:001",)

    def test_a_unit_the_condition_names_wrongly_is_refused_when_it_is_read(self) -> None:
        with pytest.raises(SelectionError):
            resolve({"variable": {"name": "inlet", "unit": "furlong", "greaterThan": 1}}, CASES)


class TestTheFallbackIsStatedRatherThanSilent:
    def test_with_no_selection_the_selected_case_is_used(self) -> None:
        """graph/AC-008."""
        found = selected_cases(None, CASES, fallback=["case:002"])

        assert found.selected == ("case:002",)

    def test_and_the_result_says_that_is_what_happened(self) -> None:
        """A graph that plotted the selected case without saying so looks identical to one that was told
        to plot it."""
        found = selected_cases(None, CASES, fallback=["case:002"])

        assert found.stated is not None
        assert "選択が書かれていない" in found.describe()

    def test_a_written_selection_wins_over_the_fallback(self) -> None:
        found = selected_cases(CONVERGED_FAST, CASES, fallback=["case:002"])

        assert found.selected == ("case:001",)
        assert found.stated is None

    def test_no_selection_and_no_fallback_still_chooses_nothing(self) -> None:
        assert selected_cases(None, CASES).selected == ()


class TestAConditionCanBeReadBack:
    def test_each_kind_describes_itself(self) -> None:
        """The description is what an empty result and a refusal both quote, so it has to be readable
        by somebody who did not write the selection."""
        assert "converged" in describe_condition({"tag": "converged"})
        assert "draft_" in describe_condition({"name": {"startsWith": "draft_"}})
        assert "inlet" in describe_condition({"variable": {"name": "inlet", "exists": True}})
        assert "すべて" in describe_condition(CONVERGED_FAST)
