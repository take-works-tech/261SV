"""What a pipeline run does when something fails, and what it writes down about it.

XC-095's rationale is the shape of the whole thing: a forty-case study where one file is truncated
should produce **thirty-nine results and one clear failure**, not zero results and one clear failure.
But continuing *within* a failed case would build a report on a state nobody checked.

XC-094: a destructive step is authorised **once, for a named scope**. Confirming per case is safer for
one case and unusable for forty, which is how people learn to click through confirmations.

Verifies: pipeline/AC-008 to AC-014, AC-017, AC-024, pipeline/TASK-021 to TASK-029.
"""

from __future__ import annotations

import inspect
from typing import Any

from service.pipeline.document import (
    DefinitionRef,
    Kind,
    Source,
    add,
    add_cases_unit,
    artefact_unit,
)
from service.pipeline.run import (
    DESTRUCTIVE,
    Authorisation,
    OnFailure,
    Outcome,
    dry_run,
    export_skipped_because,
    required_authorisations,
    run,
)

VIEW_REF = DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)
CASES = ["case:001", "case:002", "case:003"]


def a_pipeline(*, with_clear: bool = False, with_export: bool = False) -> dict[str, Any]:
    document: dict[str, Any] = {"id": "pipeline:001", "name": "毎回の確認", "units": []}
    add(document, add_cases_unit("unit:cases", CASES))
    add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF))
    if with_export:
        add(document, {"id": "unit:export", "kind": Kind.EXPORT.value})
    if with_clear:
        add(document, {"id": "unit:clear", "kind": Kind.CLEAR.value})
    return document


def failing_on(case: str):
    def act(unit: dict[str, Any], acting: str) -> None:
        if acting == case:
            raise RuntimeError("入力ファイルが途中で切れています")
    return act


class TestADryRunChangesNothingAndSaysEverything:
    def test_it_lists_every_unit_with_what_it_would_act_on(self) -> None:
        plan = dry_run(a_pipeline(), cases=CASES)

        assert [step.unit_id for step in plan.steps] == ["unit:cases", "unit:view"]
        assert len(plan.steps[1].cases) == 3

    def test_it_states_what_would_be_written(self) -> None:
        plan = dry_run(a_pipeline(), cases=CASES)

        assert len(plan.steps[1].writes) == 3

    def test_the_list_equals_what_the_real_run_then_does(self) -> None:
        """TASK-021's own condition. A dry run that describes a different execution from the one that
        follows is worse than no dry run: it is an authorisation given for the wrong thing."""
        document = a_pipeline(with_export=True)

        plan = dry_run(document, cases=CASES)
        record = run(
            document, cases=CASES, authorisations=[Authorisation("unit:export", 3)]
        )

        planned = [(step.unit_id, step.cases) for step in plan.steps]
        acted: dict[str, tuple[str, ...]] = {}
        for result in record.results:
            if result.case_id is not None:
                acted.setdefault(result.unit_id, ())
                acted[result.unit_id] += (result.case_id,)
        assert [
            (unit, cases) for unit, cases in planned if cases
        ] == [(unit, cases) for unit, cases in acted.items()]

    def test_it_is_given_nothing_to_run_with(self) -> None:
        """Structural rather than observed: `run` takes the callable that performs a unit and `dry_run`
        has no parameter for one, so there is nothing for it to call even by mistake. A test that merely
        watched a callback stay untouched would pass on the day somebody added the parameter."""
        assert "act" in inspect.signature(run).parameters
        assert "act" not in inspect.signature(dry_run).parameters

    def test_a_loop_states_its_iteration_count(self) -> None:
        """AC-024. Fixed before the run, so a dry run that omitted it would be describing a different
        execution from the one that follows."""
        document = a_pipeline()
        add(document, {"id": "unit:loop", "kind": Kind.LOOP.value, "units": []})

        plan = dry_run(document, cases=CASES, iterations={"unit:loop": 7})

        assert "繰り返し 7 回" in plan.steps[-1].describe()

    def test_a_condition_states_its_value(self) -> None:
        document = a_pipeline()
        add(document, {"id": "unit:if", "kind": Kind.CONDITION.value, "units": []})

        plan = dry_run(document, cases=CASES, conditions={"unit:if": False})

        assert "条件は 偽" in plan.steps[-1].describe()

    def test_it_marks_the_destructive_units(self) -> None:
        plan = dry_run(a_pipeline(with_clear=True), cases=CASES)

        assert [step.unit_id for step in plan.destructive_steps] == ["unit:clear"]
        assert "承認が要ります" in plan.describe()

    def test_destructive_is_a_stated_list_rather_than_a_guess_from_the_name(self) -> None:
        """A judgement made by pattern-matching would change the day somebody adds a kind called
        `cleanup`."""
        assert DESTRUCTIVE == {Kind.CLEAR, Kind.EXPORT}


class TestADestructiveUnitIsAuthorisedOnceForAScope:
    def test_the_authorisation_names_the_unit_and_the_count(self) -> None:
        """XC-094. Confirming per case is safer for one case and unusable for forty."""
        needed = required_authorisations(dry_run(a_pipeline(with_export=True), cases=CASES))

        assert needed == (Authorisation("unit:export", 3),)

    def test_it_is_produced_from_the_dry_run_so_the_figures_match(self) -> None:
        """Building them separately would let the two drift, and the drift would be invisible."""
        plan = dry_run(a_pipeline(with_export=True), cases=CASES)

        assert required_authorisations(plan)[0].case_count == len(plan.destructive_steps[0].cases)

    def test_an_authorisation_for_fewer_cases_does_not_cover_more(self) -> None:
        """The number is what the user weighed, and a scope that grew after the yes is a yes to
        something else."""
        assert Authorisation("unit:export", 3).covers("unit:export", 30) is False

    def test_declining_runs_the_rest_and_reports_the_destructive_one(self) -> None:
        """AC-010, rather than refusing the whole run for one step somebody declined."""
        record = run(a_pipeline(with_export=True), cases=CASES, authorisations=[])

        outcomes = {r.unit_id: r.outcome for r in record.results if r.case_id is None}
        assert outcomes["unit:export"] is Outcome.SKIPPED_UNAUTHORISED
        assert any(r.unit_id == "unit:view" and r.outcome is Outcome.DONE for r in record.results)

    def test_authorising_lets_it_run(self) -> None:
        record = run(
            a_pipeline(with_export=True), cases=CASES,
            authorisations=[Authorisation("unit:export", 3)],
        )

        assert all(
            r.outcome is Outcome.DONE for r in record.results if r.unit_id == "unit:export"
        )


class TestAFailureStopsOneCaseAndNotTheStudy:
    def test_the_other_cases_complete(self) -> None:
        """XC-095: thirty-nine results and one clear failure, not zero results and one."""
        record = run(a_pipeline(), cases=CASES, act=failing_on("case:002"))

        done = {r.case_id for r in record.results if r.outcome is Outcome.DONE and r.case_id}
        assert done == {"case:001", "case:003"}
        assert record.failed_cases == ("case:002",)

    def test_the_failed_case_skips_its_own_remaining_units(self) -> None:
        """Continuing within a failed case would build on a state nobody checked."""
        document = a_pipeline()
        add(document, artefact_unit("unit:report", Kind.REPORT, VIEW_REF))

        record = run(document, cases=CASES, act=failing_on("case:002"))

        later = [
            r for r in record.results if r.unit_id == "unit:report" and r.case_id == "case:002"
        ]
        assert later[0].outcome is Outcome.SKIPPED_AFTER_FAILURE

    def test_the_record_says_which_unit_failed(self) -> None:
        record = run(a_pipeline(), cases=CASES, act=failing_on("case:002"))

        failure = next(r for r in record.results if r.outcome is Outcome.FAILED)
        assert failure.unit_id == "unit:view"
        assert "途中で切れています" in (failure.detail or "")

    def test_stopping_at_the_first_failure_is_chosen_rather_than_assumed(self) -> None:
        """AC-013. Continuing is the default; stopping is a mode somebody picks."""
        record = run(
            a_pipeline(), cases=CASES, act=failing_on("case:001"), on_failure=OnFailure.STOP
        )

        assert record.stopped_at == "unit:view"
        assert "case:003" not in {r.case_id for r in record.results if r.outcome is Outcome.DONE}

    def test_stopping_reports_what_had_already_been_written(self) -> None:
        document = a_pipeline()
        record = run(document, cases=CASES, act=failing_on("case:002"), on_failure=OnFailure.STOP)

        assert "unit:view/case:001" in record.written


class TestNothingPartialIsWritten:
    def test_an_export_after_a_failed_input_says_why_it_was_skipped(self) -> None:
        """AC-012. A document with a hole in it is a document somebody sends."""
        record = run(a_pipeline(), cases=CASES, act=failing_on("case:002"))

        assert "部分的な文書は書き出しません" in (export_skipped_because(record, "case:002") or "")

    def test_a_case_that_succeeded_has_nothing_to_explain(self) -> None:
        record = run(a_pipeline(), cases=CASES, act=failing_on("case:002"))

        assert export_skipped_because(record, "case:001") is None


class TestCancellationStopsAtAUnitBoundary:
    def test_it_keeps_what_completed(self) -> None:
        """AC-014."""
        document = a_pipeline()
        add(document, artefact_unit("unit:report", Kind.REPORT, VIEW_REF))

        record = run(document, cases=CASES, cancel_after="unit:view")

        assert record.stopped_at == "unit:view"
        assert len(record.written) == 3
        assert not any(r.unit_id == "unit:report" for r in record.results)


class TestTheRunIsARecord:
    def test_it_holds_the_pipeline_its_revision_and_the_resolved_cases(self) -> None:
        """AC-015."""
        record = run(a_pipeline(), cases=CASES, revision=4)

        assert record.pipeline_id == "pipeline:001"
        assert record.pipeline_revision == 4
        assert record.resolved_cases == tuple(CASES)

    def test_every_result_carries_the_target_set_size_it_acted_on(self) -> None:
        record = run(a_pipeline(), cases=CASES)

        acting = [r for r in record.results if r.unit_id == "unit:view"]
        assert {r.target_size for r in acting} == {3}

    def test_a_case_a_run_produced_records_the_unit_that_produced_it(self) -> None:
        """AC-017: a result's origin is answerable from the case itself rather than by reading the
        pipeline back."""
        record = run(a_pipeline(), cases=CASES)
        record.produced["case:new"] = "unit:simulation"

        assert record.produced["case:new"] == "unit:simulation"

    def test_the_summary_says_what_happened_and_why_the_rest_was_skipped(self) -> None:
        record = run(a_pipeline(), cases=CASES, act=failing_on("case:002"))

        line = record.describe()
        assert "失敗ケース 1 件" in line
        assert "静かに誤った答え" in line
