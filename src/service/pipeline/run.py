"""Running a pipeline: what fails, what stops, and what is written down about it.

XC-095's rationale is the whole shape of this: a forty-case study where one file is truncated should
produce **thirty-nine results and one clear failure**, not zero results and one clear failure. But
continuing *within* a failed case would build a report on a state nobody checked, which is the
silent-wrong-answer failure this product exists to prevent. So a failure skips the rest of **that case**
and no more.

XC-094 governs the other direction. A destructive step is authorised **once, for a named scope**, and
its absence is a refusal rather than an assumption. Confirming per case is safer for one case and
unusable for forty, which is how people learn to click through confirmations.

Two things follow that are easy to get almost right.

**Nothing partial is written.** A report whose input failed is not exported with a gap - it is skipped,
and the skip is recorded with its reason. A document with a hole in it is a document somebody sends.

**A dry run changes nothing and says everything.** Including each loop's iteration count and each
condition's value, because both are fixed before the run starts (XC-100, XC-101) and a dry run that
omitted them would be describing a different execution from the one that follows.

Specification: XC-094, XC-095, XC-046, pipeline/AC-008 to AC-017, AC-024.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Any, Callable, Iterable

from service.pipeline.document import (
    ACT_ON_TARGETS,
    Kind,
    TargetSet,
    kind_of,
    reference_of,
    walk,
)

#: The kinds that destroy something. `clear` empties the target set; `export` writes over a path.
#: Written out because "destructive" is a judgement, and one made by pattern-matching on a name would
#: change the day somebody adds a kind called `cleanup`.
DESTRUCTIVE = frozenset({Kind.CLEAR, Kind.EXPORT})


class Outcome(str, Enum):
    """What happened to one unit for one case."""

    DONE = "done"
    SKIPPED_EMPTY = "skipped-empty"            # nothing in the target set (AC-007)
    SKIPPED_AFTER_FAILURE = "skipped-after"    # this case failed earlier (XC-095)
    SKIPPED_UNAUTHORISED = "skipped-unauthorised"  # a destructive unit nobody authorised (AC-010)
    FAILED = "failed"
    CANCELLED = "cancelled"


class OnFailure(str, Enum):
    """What a run does when a case fails. `CONTINUE` is the default and `STOP` is chosen, not assumed."""

    CONTINUE = "continue"
    STOP = "stop"


class RunError(Exception):
    """Raised when a run cannot start honestly."""


@dataclass(frozen=True, slots=True)
class Authorisation:
    """One user's yes to one destructive unit, for a stated number of cases (XC-094)."""

    unit_id: str
    case_count: int

    def covers(self, unit_id: str, cases: int) -> bool:
        """Whether this authorisation covers what is about to happen.

        The count must match. An authorisation given for three cases does not cover thirty: the number
        is what the user weighed, and a scope that grew after the yes is a yes to something else.
        """
        return self.unit_id == unit_id and self.case_count == cases


@dataclass(frozen=True, slots=True)
class Step:
    """One line of a dry run: a unit, what it would act on, and what it would write.

    `cases` is what the unit **acts on**, and it is empty for a unit that only changes the target set.
    The size of the set afterwards is `set_size`, kept apart from it because the two answer different
    questions: an addCases unit that reported three cases under `cases` would claim to have done work on
    them, and the run then records no such work - a dry run and a run that disagree is worse than no dry
    run, because the authorisation was given for the first one.
    """

    unit_id: str
    kind: Kind
    cases: tuple[str, ...]
    #: How many cases the target set holds once this unit has run.
    set_size: int = 0
    writes: tuple[str, ...] = dataclass_field(default_factory=tuple)
    iterations: int | None = None
    condition_value: bool | None = None
    destructive: bool = False

    def describe(self) -> str:
        if self.kind is Kind.ADD_CASES:
            line = f"{self.unit_id}（{self.kind.value}）：対象集合は {self.set_size} 件になります"
        else:
            line = f"{self.unit_id}（{self.kind.value}）：対象 {len(self.cases)} 件"
        if self.iterations is not None:
            # AC-024: fixed before the run, so a dry run that omitted it would be describing a
            # different execution from the one that follows.
            line += f"・繰り返し {self.iterations} 回"
        if self.condition_value is not None:
            line += f"・条件は {'真' if self.condition_value else '偽'}"
        if self.writes:
            line += f"・書き出し {len(self.writes)} 件"
        if self.destructive:
            line += "・**破壊的**"
        return line


@dataclass(frozen=True, slots=True)
class DryRun:
    """What a run would do, having done none of it (AC-008)."""

    steps: tuple[Step, ...]

    @property
    def destructive_steps(self) -> tuple[Step, ...]:
        return tuple(step for step in self.steps if step.destructive)

    def describe(self) -> str:
        lines = [step.describe() for step in self.steps]
        if self.destructive_steps:
            named = "、".join(
                f"{step.unit_id}（{len(step.cases)} 件）" for step in self.destructive_steps
            )
            lines.append(f"実行には破壊的ユニットの承認が要ります：{named}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class UnitResult:
    """What happened to one unit for one case, for the record."""

    unit_id: str
    case_id: str | None
    outcome: Outcome
    target_size: int
    detail: str | None = None


@dataclass(slots=True)
class RunRecord:
    """The record a run is (REQ-005), rather than the side effects it had."""

    pipeline_id: str
    pipeline_revision: int
    resolved_cases: tuple[str, ...] = dataclass_field(default_factory=tuple)
    results: list[UnitResult] = dataclass_field(default_factory=list)
    #: Cases this run produced, each with the unit that produced it (AC-017), so a result's origin is
    #: answerable from the case itself rather than by reading the pipeline back.
    produced: dict[str, str] = dataclass_field(default_factory=dict)
    stopped_at: str | None = None
    written: list[str] = dataclass_field(default_factory=list)

    @property
    def failed_cases(self) -> tuple[str, ...]:
        return tuple(
            sorted({r.case_id for r in self.results if r.outcome is Outcome.FAILED and r.case_id})
        )

    def describe(self) -> str:
        done = sum(1 for r in self.results if r.outcome is Outcome.DONE)
        lines = [
            f"{self.pipeline_id} 第 {self.pipeline_revision} 版：ケース {len(self.resolved_cases)} 件、"
            f"完了 {done} 件、失敗ケース {len(self.failed_cases)} 件"
        ]
        if self.failed_cases:
            lines.append(
                f"失敗：{'、'.join(self.failed_cases)}。"
                "そのケースの残りの工程だけを飛ばしています — "
                "壊れた状態の上に続きを積むのは、静かに誤った答えを作ることです（XC-095）"
            )
        if self.stopped_at:
            lines.append(f"{self.stopped_at} で停止しました。ここまでに書き出したものは残っています")
        return "\n".join(lines)


def dry_run(
    pipeline: dict[str, Any],
    *,
    cases: Iterable[str],
    iterations: dict[str, int] | None = None,
    conditions: dict[str, bool] | None = None,
) -> DryRun:
    """What the run would do, changing nothing (AC-008, AC-024)."""
    iterations = iterations or {}
    conditions = conditions or {}
    targets = TargetSet()
    steps: list[Step] = []

    for unit, _ in walk(pipeline.get("units", [])):
        unit_id = str(unit.get("id", ""))
        kind = kind_of(unit)
        if kind is Kind.ADD_CASES:
            targets.add(unit_id, unit.get("caseIds") or list(cases))
            # It acts on nothing; it changes what everything below acts on.
            acting: tuple[str, ...] = ()
        elif kind is Kind.CLEAR:
            acting = tuple(targets.cases)
            targets.clear(unit_id)
        else:
            acting = tuple(targets.cases)
        steps.append(
            Step(
                unit_id=unit_id,
                kind=kind,
                cases=acting,
                set_size=len(targets.cases),
                writes=tuple(f"{unit_id}/{case}" for case in acting) if kind in ACT_ON_TARGETS else (),
                iterations=iterations.get(unit_id) if kind is Kind.LOOP else None,
                condition_value=conditions.get(unit_id) if kind is Kind.CONDITION else None,
                destructive=kind in DESTRUCTIVE,
            )
        )
    return DryRun(tuple(steps))


def run(
    pipeline: dict[str, Any],
    *,
    cases: Iterable[str],
    revision: int = 1,
    act: Callable[[dict[str, Any], str], None] | None = None,
    authorisations: Iterable[Authorisation] = (),
    on_failure: OnFailure = OnFailure.CONTINUE,
    cancel_after: str | None = None,
) -> RunRecord:
    """Run a pipeline, isolating failures to their case and writing down what happened.

    `act` performs one unit for one case and raises to fail it. Injected rather than dispatched here, so
    this module holds the rules about failure and authorisation and nothing about views or exports.

    `cancel_after` names the unit to stop after, which is how a cancellation arrives at this layer: at a
    **unit boundary**, keeping what completed (AC-014).
    """
    record = RunRecord(str(pipeline.get("id", "")), revision, tuple(cases))
    targets = TargetSet()
    granted = list(authorisations)
    failed: set[str] = set()
    stopped = False

    for unit, _ in walk(pipeline.get("units", [])):
        if stopped:
            break
        unit_id = str(unit.get("id", ""))
        kind = kind_of(unit)

        if kind is Kind.ADD_CASES:
            targets.add(unit_id, unit.get("caseIds") or record.resolved_cases)
            record.results.append(UnitResult(unit_id, None, Outcome.DONE, len(targets.cases)))
            continue
        if kind is Kind.CLEAR:
            size = len(targets.cases)
            if not _authorised(granted, unit_id, size):
                record.results.append(
                    UnitResult(unit_id, None, Outcome.SKIPPED_UNAUTHORISED, size,
                               "破壊的ユニットの承認がありません")
                )
                continue
            targets.clear(unit_id)
            record.results.append(UnitResult(unit_id, None, Outcome.DONE, 0))
            continue

        acting = targets.acted_on(unit_id)
        if not acting:
            record.results.append(UnitResult(unit_id, None, Outcome.SKIPPED_EMPTY, 0))
            continue
        if kind in DESTRUCTIVE and not _authorised(granted, unit_id, len(acting)):
            # AC-010: the run continues and the destructive unit is reported as not authorised, rather
            # than the whole run being refused for one step somebody declined.
            record.results.append(
                UnitResult(unit_id, None, Outcome.SKIPPED_UNAUTHORISED, len(acting),
                           f"{len(acting)} 件を対象とする承認がありません")
            )
            continue

        for case in acting:
            if case in failed:
                # XC-095: the rest of *this* case is skipped. Continuing within a failed case would
                # build on a state nobody checked.
                record.results.append(
                    UnitResult(unit_id, case, Outcome.SKIPPED_AFTER_FAILURE, len(acting),
                               "このケースは先の工程で失敗しています")
                )
                continue
            try:
                if act is not None:
                    act(unit, case)
            except Exception as error:  # noqa: BLE001 - a unit may fail in any way it likes
                failed.add(case)
                record.results.append(
                    UnitResult(unit_id, case, Outcome.FAILED, len(acting), str(error)[:200])
                )
                if on_failure is OnFailure.STOP:
                    record.stopped_at = unit_id
                    stopped = True
                    break
                continue
            record.results.append(UnitResult(unit_id, case, Outcome.DONE, len(acting)))
            if kind in ACT_ON_TARGETS:
                record.written.append(f"{unit_id}/{case}")

        if cancel_after is not None and unit_id == cancel_after:
            record.stopped_at = unit_id
            stopped = True

    return record


def _authorised(granted: list[Authorisation], unit_id: str, cases: int) -> bool:
    return any(item.covers(unit_id, cases) for item in granted)


def required_authorisations(plan: DryRun) -> tuple[Authorisation, ...]:
    """What a user would have to authorise for this run, one per destructive unit (XC-094).

    Produced from the dry run so that the figures a user authorises are the figures they were shown.
    Building them separately would let the two drift, and the drift would be invisible.
    """
    return tuple(
        Authorisation(step.unit_id, len(step.cases)) for step in plan.destructive_steps
    )


def export_skipped_because(record: RunRecord, case: str) -> str | None:
    """Why an export for one case was not written, or None if it was.

    A report whose input failed is not written with a gap. A document with a hole in it is a document
    somebody sends.
    """
    for result in record.results:
        if result.case_id == case and result.outcome is Outcome.FAILED:
            return f"入力の工程 '{result.unit_id}' が失敗したため、部分的な文書は書き出しません"
    return None


def unresolved_references_block(pipeline: dict[str, Any]) -> tuple[str, ...]:
    """Units whose reference cannot even be read. A malformed pin is not a missing one."""
    broken: list[str] = []
    for unit, _ in walk(pipeline.get("units", [])):
        try:
            reference_of(unit)
        except Exception as error:  # noqa: BLE001
            broken.append(f"{unit.get('id')}：{error}")
    return tuple(broken)
