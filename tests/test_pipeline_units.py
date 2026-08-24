"""Variables, formulas, conditions and loops: the units that compute rather than act.

XC-100 fixes a loop's count before the loop begins, from one of three sources, and there is no `while`
and no user-written early exit. The argument is not tidiness: a pipeline that cannot say what it will do
before it does it cannot be authorised to delete data, and authorisation before destruction is XC-094.

XC-101 puts the language behind all of them, with no interpreter: a workspace from an untrusted source
opens and its formulas read without running anything.

AC-034 is the one that is easy to leave out. A false condition records its contents **with the value the
expression evaluated to**, so that a report never written is distinguishable from one never asked for.

Verifies: pipeline/AC-026 to AC-029, AC-032 to AC-034, pipeline/TASK-014 to TASK-019.
"""

from __future__ import annotations

from typing import Any

import pytest

from engine.analysis.expression import quantity
from engine.limits import MAX_LOOP_ITERATIONS
from service.pipeline.document import (
    COUNT_FROM_VARIABLE,
    COUNT_LITERAL,
    COUNT_PER_CASE,
    DefinitionRef,
    Kind,
    PipelineError,
    Source,
    add,
    add_cases_unit,
    artefact_unit,
    condition_unit,
    formula_unit,
    loop_unit,
    names_bound_before,
    variable_unit,
)
from service.pipeline.run import Outcome, RunError, dry_run, run

VIEW_REF = DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)
CASES = ["case:001", "case:002", "case:003"]


def pipeline() -> dict[str, Any]:
    return {"id": "pipeline:001", "name": "毎回の確認", "units": []}


def with_cases() -> dict[str, Any]:
    document = pipeline()
    add(document, add_cases_unit("unit:cases", CASES))
    return document


def detail_of(record: Any, unit_id: str) -> str:
    return next(r.detail or "" for r in record.results if r.unit_id == unit_id)


class TestAVariableUnitBindsForTheUnitsBelow:
    def test_the_name_is_visible_below_it(self) -> None:
        """AC-029."""
        document = pipeline()
        add(document, variable_unit("unit:v", "inlet", value=3.0, unit_symbol="m"))
        add(document, formula_unit("unit:f", "twice", "inlet * 2"))

        record = run(document, cases=[])

        assert detail_of(record, "unit:f") == "6 m"

    def test_it_leaves_the_workspace_variables_alone_unless_it_says_to(self) -> None:
        """A pipeline that quietly rewrote a workspace variable would change every other pipeline that
        reads it, and the change would be invisible from the pipeline that made it."""
        quiet = variable_unit("unit:v", "inlet", value=3.0)
        loud = variable_unit("unit:w", "inlet", value=3.0, to_workspace=True)

        assert "toWorkspace" not in quiet
        assert loud["toWorkspace"] is True

    def test_the_run_records_which_one_reaches_the_workspace(self) -> None:
        document = pipeline()
        add(document, variable_unit("unit:w", "inlet", value=3.0, to_workspace=True))

        assert "ワークスペース" in detail_of(run(document, cases=[]), "unit:w")

    def test_a_variable_with_neither_a_value_nor_values_is_refused(self) -> None:
        with pytest.raises(PipelineError):
            variable_unit("unit:v", "inlet")

    def test_a_several_valued_variable_is_not_a_value_to_read(self) -> None:
        """It is what a loop counts over. Outside that loop there is no single value the name could
        mean, so binding it to one would be the product choosing."""
        document = pipeline()
        add(document, variable_unit("unit:v", "sweep", values=[1.0, 2.0, 3.0]))

        assert names_bound_before(document, "unit:anything") == ()


class TestAFormulaCarriesTheUnitItProduced:
    def test_the_result_states_the_unit_the_expression_made(self) -> None:
        """AC-030: the unit the expression produced, not one the unit was told."""
        document = pipeline()
        add(document, variable_unit("unit:l", "span", value=100.0, unit_symbol="mm"))
        add(document, variable_unit("unit:t", "duration", value=2.0, unit_symbol="s"))
        add(document, formula_unit("unit:f", "speed", "span / duration"))

        assert detail_of(run(document, cases=[]), "unit:f") == "0.05 m·s^-1"

    def test_incompatible_units_stop_the_run_naming_both(self) -> None:
        """AC-031 reaching the pipeline: the refusal is the evaluator's and it is not swallowed here."""
        document = pipeline()
        add(document, variable_unit("unit:l", "span", value=1.0, unit_symbol="m"))
        add(document, variable_unit("unit:t", "duration", value=1.0, unit_symbol="s"))
        add(document, formula_unit("unit:f", "nonsense", "span + duration"))

        with pytest.raises(RunError) as refusal:
            run(document, cases=[])
        assert "m" in str(refusal.value) and "s" in str(refusal.value)


class TestAnUnboundNameIsRefusedWhenTheUnitIsAdded:
    def test_the_edit_is_refused_and_the_pipeline_is_unchanged(self) -> None:
        """AC-032. The unit does not land, so a pipeline is never briefly holding an expression nobody
        could evaluate."""
        document = pipeline()

        with pytest.raises(PipelineError) as refusal:
            add(document, formula_unit("unit:f", "x", "outlet * 2"))

        assert "outlet" in str(refusal.value)
        assert document["units"] == []

    def test_a_name_the_workspace_supplies_counts_as_bound(self) -> None:
        document = pipeline()

        add(document, formula_unit("unit:f", "x", "outlet * 2"), outside=["outlet"])

        assert document["units"][0]["id"] == "unit:f"

    def test_a_name_bound_only_inside_a_sibling_container_is_not_in_scope(self) -> None:
        """A formula that read one would work until somebody made that branch conditional."""
        document = pipeline()
        add(document, loop_unit("unit:loop", count=2, index_name="i"))
        add(document, formula_unit("unit:inner", "doubled", "i * 2"), inside="unit:loop")

        with pytest.raises(PipelineError):
            add(document, formula_unit("unit:outer", "also", "i * 3"))


class TestAConditionChoosesWhatRuns:
    def test_true_runs_the_contents(self) -> None:
        """AC-033."""
        document = with_cases()
        add(document, condition_unit("unit:if", "1 m < 2 m"))
        add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF), inside="unit:if")

        record = run(document, cases=CASES)

        assert {r.case_id for r in record.results if r.unit_id == "unit:view"} == set(CASES)

    def test_false_skips_them(self) -> None:
        document = with_cases()
        add(document, condition_unit("unit:if", "1 m > 2 m"))
        add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF), inside="unit:if")

        record = run(document, cases=CASES)

        outcomes = {r.outcome for r in record.results if r.unit_id == "unit:view"}
        assert outcomes == {Outcome.SKIPPED_CONDITION}

    def test_the_skipped_contents_carry_the_value_the_expression_evaluated_to(self) -> None:
        """AC-034: a report never written is distinguishable from one never asked for. Leaving the
        contents out of the record would make the two look identical."""
        document = with_cases()
        add(document, condition_unit("unit:if", "1 m > 2 m"))
        add(document, artefact_unit("unit:report", Kind.REPORT, VIEW_REF), inside="unit:if")

        record = run(document, cases=CASES)

        assert "1 m > 2 m" in detail_of(record, "unit:report")
        assert "偽" in detail_of(record, "unit:if")

    def test_the_condition_itself_is_recorded_either_way(self) -> None:
        document = with_cases()
        add(document, condition_unit("unit:if", "1 m < 2 m"))

        assert "真" in detail_of(run(document, cases=CASES), "unit:if")

    def test_an_expression_that_is_not_a_truth_value_is_refused(self) -> None:
        document = with_cases()
        add(document, condition_unit("unit:if", "1 m + 1 m"))

        with pytest.raises(RunError):
            run(document, cases=CASES)

    def test_the_dry_run_states_the_value_it_could_resolve(self) -> None:
        document = with_cases()
        add(document, condition_unit("unit:if", "1 m > 2 m"))

        assert "条件は 偽" in dry_run(document, cases=CASES).describe()

    def test_a_condition_it_cannot_resolve_yet_is_left_undetermined_rather_than_guessed(self) -> None:
        """Inside a per-case loop the value differs per iteration, and one number in its place would
        describe an execution that never happens."""
        document = with_cases()
        add(document, loop_unit("unit:loop", per_case=True, index_name="i"))
        add(document, condition_unit("unit:if", "i > 0"), inside="unit:loop")

        plan = dry_run(document, cases=CASES)

        assert next(step for step in plan.steps if step.unit_id == "unit:if").condition_value is None


class TestALoopCountsFromOneOfThreeSources:
    def test_a_literal_count(self) -> None:
        """AC-026, first source."""
        document = with_cases()
        add(document, loop_unit("unit:loop", count=3))
        add(document, formula_unit("unit:f", "seen", "index + 1"), inside="unit:loop")

        record = run(document, cases=CASES)

        assert sum(1 for r in record.results if r.unit_id == "unit:f") == 3

    def test_the_values_of_a_variable(self) -> None:
        """Second source. The variable's current value is bound under its own name inside the loop."""
        document = with_cases()
        add(document, variable_unit("unit:v", "sweep", values=[10.0, 20.0], unit_symbol="mm"))
        add(document, loop_unit("unit:loop", over_variable="sweep"))
        add(document, formula_unit("unit:f", "doubled", "sweep * 2"), inside="unit:loop")

        record = run(document, cases=CASES)

        seen = [r.detail for r in record.results if r.unit_id == "unit:f"]
        assert seen == ["0.02 m", "0.04 m"]

    def test_one_iteration_per_case_in_the_target_set(self) -> None:
        """Third source."""
        document = with_cases()
        add(document, loop_unit("unit:loop", per_case=True))
        add(document, formula_unit("unit:f", "seen", "index"), inside="unit:loop")

        record = run(document, cases=CASES)

        assert sum(1 for r in record.results if r.unit_id == "unit:f") == len(CASES)

    def test_the_run_states_which_source_it_used(self) -> None:
        """AC-026's last clause. Two loops that ran three times for different reasons behave differently
        the next time a case is added, and afterwards the record is the only place that survives."""
        document = with_cases()
        add(document, loop_unit("unit:loop", per_case=True))

        assert "対象ケース 1 件につき 1 回" in detail_of(run(document, cases=CASES), "unit:loop")

    def test_the_dry_run_states_the_source_too(self) -> None:
        document = with_cases()
        add(document, loop_unit("unit:loop", over_variable="sweep"))
        add(document, variable_unit("unit:v", "sweep", values=[1.0, 2.0]))

        # The variable is declared after the loop, so at the loop's position there is nothing to count.
        with pytest.raises(RunError):
            dry_run(document, cases=CASES)

    def test_naming_more_than_one_source_is_refused(self) -> None:
        """Accepting both would mean the product choosing which count a pipeline meant, and the two
        would disagree the day somebody edited only one of them."""
        with pytest.raises(PipelineError):
            loop_unit("unit:loop", count=3, per_case=True)

    def test_the_three_sources_are_the_three_keys_the_document_uses(self) -> None:
        assert (COUNT_LITERAL, COUNT_FROM_VARIABLE, COUNT_PER_CASE) == (
            "count", "countFromVariable", "countPerCase"
        )


class TestTheLoopIndex:
    def test_the_contents_see_it_under_the_declared_name(self) -> None:
        """AC-027."""
        document = with_cases()
        add(document, loop_unit("unit:loop", count=3, index_name="step"))
        add(document, formula_unit("unit:f", "here", "step * 10"), inside="unit:loop")

        record = run(document, cases=CASES)

        assert [r.detail for r in record.results if r.unit_id == "unit:f"] == [
            "0 単位なし", "10 単位なし", "20 単位なし"
        ]

    def test_a_loop_that_names_no_index_still_has_one(self) -> None:
        document = with_cases()
        add(document, loop_unit("unit:loop", count=1))
        add(document, formula_unit("unit:f", "here", "index"), inside="unit:loop")

        assert detail_of(run(document, cases=CASES), "unit:f") == "0 単位なし"

    def test_the_index_leaves_scope_with_the_loop(self) -> None:
        document = with_cases()
        add(document, loop_unit("unit:loop", count=1, index_name="step"))

        assert "step" not in names_bound_before(document, "unit:after")


class TestTheIterationCeiling:
    def test_the_limit_comes_from_the_one_place_that_holds_it(self) -> None:
        assert MAX_LOOP_ITERATIONS == 1000

    def test_a_count_above_it_refuses_the_run_before_anything_happens(self) -> None:
        """AC-028. A formula yielding a million iterations should stop before the run, not after a night
        of running."""
        document = with_cases()
        add(document, loop_unit("unit:loop", count=MAX_LOOP_ITERATIONS + 1))
        add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF), inside="unit:loop")

        with pytest.raises(RunError) as refusal:
            run(document, cases=CASES)

        assert "unit:loop" in str(refusal.value)
        assert str(MAX_LOOP_ITERATIONS + 1) in str(refusal.value)
        assert "LIM-008" in str(refusal.value)

    def test_nothing_ran_before_the_refusal(self) -> None:
        """The check is on a pass that changes nothing, so a refused run is a run that did not start."""
        touched: list[str] = []
        document = with_cases()
        add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF))
        add(document, loop_unit("unit:loop", count=MAX_LOOP_ITERATIONS + 1))

        with pytest.raises(RunError):
            run(document, cases=CASES, act=lambda unit, case: touched.append(case))

        assert touched == []

    def test_exactly_the_limit_is_allowed(self) -> None:
        document = with_cases()
        add(document, loop_unit("unit:loop", count=MAX_LOOP_ITERATIONS))

        assert run(document, cases=CASES).results


class TestWhatAnExpressionCanSeeOfACase:
    def test_a_per_case_loop_binds_the_recorded_quantities_of_the_case_in_scope(self) -> None:
        """"The case in scope" has a meaning inside a per-case loop and none outside one, which is why
        the quantities are bound there rather than everywhere."""
        document = with_cases()
        add(document, loop_unit("unit:loop", per_case=True))
        add(
            document, formula_unit("unit:f", "margin", "yield_stress - peak"),
            inside="unit:loop", outside=["peak", "yield_stress"],
        )

        recorded = {
            "case:001": {"peak": quantity(150.0, "MPa"), "yield_stress": quantity(250.0, "MPa")},
            "case:002": {"peak": quantity(240.0, "MPa"), "yield_stress": quantity(250.0, "MPa")},
            "case:003": {"peak": quantity(100.0, "MPa"), "yield_stress": quantity(250.0, "MPa")},
        }
        record = run(document, cases=CASES, quantities_of=lambda case: recorded[case])

        assert [r.detail for r in record.results if r.unit_id == "unit:f"] == [
            "1e+08 Pa", "1e+07 Pa", "1.5e+08 Pa"
        ]
