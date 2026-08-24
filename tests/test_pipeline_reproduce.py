"""Two runs of the same pipeline, and the same pipeline run without an interface.

AC-016 allows exactly one difference between two runs on the same inputs - the recorded timestamps -
and requires everything else to match. That exception is the difficulty: "identical" needs a form to
compare and a name for the first place two runs part company, because a boolean answer to "were these
the same" is the least useful form of a correct one.

AC-022 asks for progress **and** outcome in a machine-readable form, and a non-zero exit when any case
failed. Progress reported only at the end is not progress: the run somebody needs to know about is the
one that was killed at case thirty of forty.

Verifies: pipeline/AC-016, AC-021, AC-022, pipeline/TASK-030, TASK-034, XC-012, XC-046.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from service.pipeline.document import (
    DefinitionRef,
    Kind,
    Source,
    add,
    add_cases_unit,
    artefact_unit,
)
from service.pipeline.headless import (
    EXIT_CASE_FAILED,
    EXIT_OK,
    EXIT_REFUSED,
    main,
    run_headless,
)
from service.pipeline.reproduce import (
    VOLATILE_FIELDS,
    artefact_differences,
    artefact_digests,
    canonical,
    differences,
    digest,
    identical,
)
from service.pipeline.run import Outcome, run

VIEW_REF = DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)
CASES = ["case:001", "case:002", "case:003"]


def a_pipeline() -> dict[str, Any]:
    document: dict[str, Any] = {"id": "pipeline:001", "units": []}
    add(document, add_cases_unit("unit:cases", CASES))
    add(document, artefact_unit("unit:view", Kind.VIEW, VIEW_REF))
    return document


def failing_on(case: str):
    def act(unit: dict[str, Any], acting: str) -> None:
        if acting == case:
            raise RuntimeError("入力ファイルが途中で切れています")
    return act


def at(hour: int):
    return lambda: datetime(2026, 8, 25, hour, tzinfo=timezone(timedelta(hours=9)))


class TestTheOnlyThingThatMayDifferIsTheTime:
    def test_two_runs_of_the_same_pipeline_agree(self) -> None:
        """AC-016."""
        first = run(a_pipeline(), cases=CASES, clock=at(9))
        second = run(a_pipeline(), cases=CASES, clock=at(17))

        assert differences(first, second) == ()
        assert identical(first, second)

    def test_the_timestamps_really_did_differ(self) -> None:
        """Otherwise the test above would pass on two runs that recorded no time at all."""
        first = run(a_pipeline(), cases=CASES, clock=at(9))
        second = run(a_pipeline(), cases=CASES, clock=at(17))

        assert first.started is not None and second.started is not None
        assert first.started.utc != second.started.utc

    def test_the_canonical_form_holds_no_time(self) -> None:
        record = run(a_pipeline(), cases=CASES, clock=at(9))

        assert not set(VOLATILE_FIELDS) & set(canonical(record))
        assert "2026-08-25" not in json.dumps(canonical(record), ensure_ascii=False)

    def test_the_volatile_fields_are_written_out_rather_than_matched_by_name(self) -> None:
        """"Anything that looks like a time" is a rule that would one day drop a field somebody
        needs."""
        assert VOLATILE_FIELDS == ("started", "finished")


class TestWhereTwoRunsPartCompanyIsNamed:
    def test_a_different_outcome_is_reported_with_its_unit(self) -> None:
        clean = run(a_pipeline(), cases=CASES, clock=at(9))
        broken = run(a_pipeline(), cases=CASES, act=failing_on("case:002"), clock=at(9))

        found = differences(clean, broken)

        assert found
        assert any("results[" in line and "failed" in line for line in found)

    def test_agreement_is_an_empty_tuple_rather_than_a_message(self) -> None:
        assert differences(run(a_pipeline(), cases=CASES), run(a_pipeline(), cases=CASES)) == ()

    def test_a_different_case_list_is_reported(self) -> None:
        first = run(a_pipeline(), cases=CASES)
        second = run(a_pipeline(), cases=CASES[:2])

        assert any("resolvedCases" in line for line in differences(first, second))

    def test_order_is_a_difference_rather_than_something_to_tidy_away(self) -> None:
        """Two runs that acted on the same cases in a different order are not the same run, and a
        canonical form that sorted them would report agreement where there is none."""
        forwards = run(a_pipeline(), cases=CASES)
        backwards = run(a_pipeline(), cases=list(reversed(CASES)))

        assert differences(forwards, backwards) != ()

    def test_the_digest_answers_whether_and_the_differences_answer_where(self) -> None:
        first = run(a_pipeline(), cases=CASES, clock=at(9))
        second = run(a_pipeline(), cases=CASES, act=failing_on("case:001"), clock=at(9))

        assert digest(first) != digest(second)
        assert len(differences(first, second)) >= 1


class TestArtefactsAreComparedByContent:
    def test_two_identical_files_agree(self, tmp_path: Path) -> None:
        one, other = tmp_path / "a", tmp_path / "b"
        one.mkdir()
        other.mkdir()
        (one / "report.html").write_bytes(b"<p>150 MPa</p>")
        (other / "report.html").write_bytes(b"<p>150 MPa</p>")

        assert artefact_differences(
            artefact_digests(one.iterdir()), artefact_digests(other.iterdir())
        ) == ()

    def test_a_changed_byte_is_reported_by_name(self, tmp_path: Path) -> None:
        one, other = tmp_path / "a", tmp_path / "b"
        one.mkdir()
        other.mkdir()
        (one / "report.html").write_bytes(b"<p>150 MPa</p>")
        (other / "report.html").write_bytes(b"<p>151 MPa</p>")

        found = artefact_differences(
            artefact_digests(one.iterdir()), artefact_digests(other.iterdir())
        )

        assert found == ("report.html：内容が違います",)

    def test_they_are_keyed_by_name_rather_than_by_path(self, tmp_path: Path) -> None:
        """Two runs write into two directories, and a comparison keyed by absolute path would report
        every artefact as missing from the other side."""
        one, other = tmp_path / "run-1", tmp_path / "run-2"
        one.mkdir()
        other.mkdir()
        (one / "report.html").write_bytes(b"same")
        (other / "report.html").write_bytes(b"same")

        assert list(artefact_digests(one.iterdir())) == ["report.html"]

    def test_a_missing_artefact_is_reported_rather_than_ignored(self, tmp_path: Path) -> None:
        one, other = tmp_path / "a", tmp_path / "b"
        one.mkdir()
        other.mkdir()
        (one / "report.html").write_bytes(b"x")

        assert artefact_differences(
            artefact_digests(one.iterdir()), artefact_digests(other.iterdir())
        ) == ("report.html：2 回目にありません",)


class TestTheHeadlessRunReportsWhileItRuns:
    def test_every_unit_result_is_a_line(self) -> None:
        """AC-022. Emitted as each unit finishes, so a run killed halfway has still said what it did."""
        stream = io.StringIO()

        code, record = run_headless(a_pipeline(), cases=CASES, stream=stream)

        events = [json.loads(line) for line in stream.getvalue().splitlines()]
        units = [event for event in events if event["event"] == "unit"]
        assert record is not None
        assert len(units) == len(record.results)
        assert code == EXIT_OK

    def test_every_line_is_its_own_json_object(self) -> None:
        stream = io.StringIO()
        run_headless(a_pipeline(), cases=CASES, stream=stream)

        for line in stream.getvalue().splitlines():
            assert isinstance(json.loads(line), dict)

    def test_the_plan_is_emitted_before_anything_runs(self) -> None:
        """What makes the log usable as an authorisation record: the destructive steps and their case
        counts are in it before the first unit, rather than reconstructed from what happened."""
        stream = io.StringIO()
        run_headless(a_pipeline(), cases=CASES, stream=stream)

        events = [json.loads(line)["event"] for line in stream.getvalue().splitlines()]
        assert events[0] == "plan"
        assert events.index("start") < events.index("unit")

    def test_the_last_line_summarises_the_run(self) -> None:
        stream = io.StringIO()
        run_headless(a_pipeline(), cases=CASES, stream=stream)

        last = json.loads(stream.getvalue().splitlines()[-1])
        assert last["event"] == "finished"
        assert last["failedCases"] == []
        assert last["startedUtc"] is not None


class TestTheExitCodeAnswersOneQuestion:
    def test_zero_when_nothing_failed(self) -> None:
        code, _ = run_headless(a_pipeline(), cases=CASES, stream=io.StringIO())

        assert code == EXIT_OK

    def test_one_when_a_case_failed(self) -> None:
        stream = io.StringIO()

        code, record = run_headless(
            a_pipeline(), cases=CASES, stream=stream, act=failing_on("case:002")
        )

        assert code == EXIT_CASE_FAILED
        assert json.loads(stream.getvalue().splitlines()[-1])["failedCases"] == ["case:002"]
        assert record is not None

    def test_the_other_cases_still_completed(self) -> None:
        """A non-zero exit reports that something failed, not that nothing was done."""
        _, record = run_headless(
            a_pipeline(), cases=CASES, stream=io.StringIO(), act=failing_on("case:002")
        )

        assert record is not None
        done = {r.case_id for r in record.results if r.outcome is Outcome.DONE and r.case_id}
        assert done == {"case:001", "case:003"}

    def test_two_when_the_run_was_refused_before_it_started(self) -> None:
        """Distinct from a failed case because nothing ran, which is a different fact to whatever is
        calling."""
        from service.pipeline.document import loop_unit
        from engine.limits import MAX_LOOP_ITERATIONS

        document = a_pipeline()
        add(document, loop_unit("unit:loop", count=MAX_LOOP_ITERATIONS + 1))
        stream = io.StringIO()

        code, record = run_headless(document, cases=CASES, stream=stream)

        assert code == EXIT_REFUSED
        assert record is None
        assert json.loads(stream.getvalue().splitlines()[-1])["event"] == "refused"

    def test_the_three_codes_are_three_different_numbers(self) -> None:
        assert len({EXIT_OK, EXIT_CASE_FAILED, EXIT_REFUSED}) == 3


class TestTheEntryPointReadsADocument:
    def test_it_runs_a_pipeline_from_a_file(self, tmp_path: Path) -> None:
        path = tmp_path / "pipeline.json"
        path.write_text(json.dumps(a_pipeline(), ensure_ascii=False), encoding="utf-8")
        stream = io.StringIO()

        code = main([str(path), *CASES], stream=stream)

        assert code == EXIT_OK
        last = json.loads(stream.getvalue().splitlines()[-1])
        assert last["event"] == "finished"
        assert last["failedCases"] == []

    def test_a_missing_file_is_refused_rather_than_raised(self, tmp_path: Path) -> None:
        stream = io.StringIO()

        code = main([str(tmp_path / "nowhere.json")], stream=stream)

        assert code == EXIT_REFUSED
        assert "読めません" in json.loads(stream.getvalue().splitlines()[-1])["reason"]

    def test_no_arguments_says_how_to_call_it(self) -> None:
        stream = io.StringIO()

        assert main([], stream=stream) == EXIT_REFUSED
        assert "使い方" in json.loads(stream.getvalue())["reason"]

    def test_it_holds_no_execution_of_its_own(self) -> None:
        """AC-021's identity. A second runner here would be a second answer to what a pipeline does,
        and the two would drift apart quietly."""
        import service.pipeline.headless as headless

        source = Path(headless.__file__).read_text(encoding="utf-8")
        assert "def _execute" not in source
        assert source.count("from service.pipeline.run import") == 1


@pytest.mark.parametrize("case", CASES)
def test_a_run_is_reproducible_whichever_case_fails(case: str) -> None:
    """The property has to hold for the failing runs too, or it only holds for the runs nobody needs to
    compare."""
    first = run(a_pipeline(), cases=CASES, act=failing_on(case), clock=at(9))
    second = run(a_pipeline(), cases=CASES, act=failing_on(case), clock=at(23))

    assert differences(first, second) == ()
