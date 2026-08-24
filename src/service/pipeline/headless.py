"""The same pipeline, run without an interface, reporting to a machine.

REQ-008's requirement is identity: a headless run executes the identical units and produces identical
artefacts (AC-021). So this module contains no execution of its own. It reads a document, calls the
same `run`, and turns what comes back into lines - a second runner here would be a second answer to
the question of what a pipeline does, and the two would drift apart quietly.

**Progress is reported while the run happens, not after it** (AC-022). One JSON object per line, written
as each unit finishes. The alternative - a single JSON document at the end - is smaller and easier to
parse and reports nothing at all about a run that was killed at case thirty of forty, which is exactly
the run somebody needs to know about. Line-delimited output also survives being read by a program that
is only interested in the last line.

**The exit code answers one question**: did any case fail. Zero when none did, 1 when one or more did,
2 when the run was refused before it started. Two rather than one for the refusal because they mean
different things to whatever is calling: a failed case is a result, and a refusal is a run that never
happened.

Specification: pipeline/AC-021, AC-022, REQ-008, INV-006, XC-046.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, TextIO

from service.pipeline.run import (
    Authorisation,
    OnFailure,
    RunError,
    RunRecord,
    UnitResult,
    dry_run,
    run,
)

#: The run finished and no case failed.
EXIT_OK = 0
#: At least one case failed. The run happened and the record is complete.
EXIT_CASE_FAILED = 1
#: The run was refused before it started - an unresolved reference, a loop count over LIM-008, a budget
#: with no way to size a case. Distinct from a failure because nothing ran.
EXIT_REFUSED = 2


def emit(stream: TextIO, event: dict[str, Any]) -> None:
    """One JSON object, one line, flushed.

    Flushed on every line rather than at the end: a buffer is exactly the thing that loses the progress
    of a run that was killed, which is the case this output format exists for.
    """
    stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    stream.flush()


def as_event(result: UnitResult) -> dict[str, Any]:
    return {
        "event": "unit",
        "unit": result.unit_id,
        "case": result.case_id,
        "outcome": result.outcome.value,
        "targetSize": result.target_size,
        "detail": result.detail,
    }


def run_headless(
    pipeline: dict[str, Any],
    *,
    cases: Iterable[str],
    stream: TextIO,
    revision: int = 1,
    act: Callable[[dict[str, Any], str], None] | None = None,
    authorisations: Iterable[Authorisation] = (),
    on_failure: OnFailure = OnFailure.CONTINUE,
    plan_first: bool = True,
) -> tuple[int, RunRecord | None]:
    """Run a pipeline and report it as JSON Lines. Returns the exit code and the record.

    `plan_first` emits the dry run before anything happens, which is what makes the output usable as an
    authorisation record: the destructive steps and their case counts are in the log before the first
    unit runs, rather than being reconstructed afterwards from what happened.
    """
    listed = list(cases)
    try:
        if plan_first:
            plan = dry_run(pipeline, cases=listed)
            emit(stream, {
                "event": "plan",
                "steps": [
                    {
                        "unit": step.unit_id,
                        "kind": step.kind.value,
                        "cases": len(step.cases),
                        "iterations": step.iterations,
                        "countSource": step.count_source,
                        "conditionValue": step.condition_value,
                        "destructive": step.destructive,
                        "unresolved": step.unresolved,
                    }
                    for step in plan.steps
                ],
            })
        emit(stream, {
            "event": "start",
            "pipeline": str(pipeline.get("id", "")),
            "revision": revision,
            "cases": listed,
        })
        record = run(
            pipeline,
            cases=listed,
            revision=revision,
            act=act,
            authorisations=authorisations,
            on_failure=on_failure,
            on_result=lambda result: emit(stream, as_event(result)),
        )
    except RunError as refusal:
        # Nothing ran. Reported as its own event and its own exit code, because "the run was refused"
        # and "a case failed" are different facts to whatever is calling.
        emit(stream, {"event": "refused", "reason": str(refusal)})
        return EXIT_REFUSED, None

    failed = list(record.failed_cases)
    code = EXIT_CASE_FAILED if failed else EXIT_OK
    emit(stream, {
        "event": "finished",
        "pipeline": record.pipeline_id,
        "revision": record.pipeline_revision,
        "failedCases": failed,
        "written": list(record.written),
        "stoppedAt": record.stopped_at,
        "startedUtc": record.started.utc if record.started else None,
        "finishedUtc": record.finished.utc if record.finished else None,
        "exit": code,
    })
    return code, record


def main(argv: list[str] | None = None, *, stream: TextIO | None = None) -> int:
    """`python -m service.pipeline.headless <pipeline.json> [case ...]`.

    Deliberately small. The units themselves are performed by whatever the caller supplies, and this
    entry point exists to prove the same run is reachable without an interface - not to become a second
    place where a pipeline's behaviour is decided.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    out = stream or sys.stdout
    if not arguments:
        emit(out, {
            "event": "refused",
            "reason": "使い方：python -m service.pipeline.headless <pipeline.json> [ケースID ...]",
        })
        return EXIT_REFUSED

    document_path = Path(arguments[0])
    try:
        document = json.loads(document_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        emit(out, {"event": "refused", "reason": f"{document_path} を読めません：{error}"})
        return EXIT_REFUSED

    code, _ = run_headless(document, cases=arguments[1:], stream=out)
    return code


if __name__ == "__main__":  # pragma: no cover - the module is exercised through main()
    raise SystemExit(main())
