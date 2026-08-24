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
from typing import Any, Callable, Iterable, Mapping

from engine.analysis.expression import ExpressionError, Value, evaluate, quantity
from engine.limits import MAX_LOOP_ITERATIONS
from service.pipeline.document import (
    ACT_ON_TARGETS,
    CONTAINERS,
    COUNT_FROM_VARIABLE,
    COUNT_LITERAL,
    COUNT_PER_CASE,
    DEFAULT_INDEX_NAME,
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
    SKIPPED_CONDITION = "skipped-condition"    # an enclosing condition was false (AC-034)
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
    #: Which of XC-100's three sources gave the iteration count, where this step is a loop. AC-026
    #: requires the run to state it: two loops that ran three times for different reasons behave
    #: differently the next time a case is added.
    count_source: str | None = None
    #: Why the plan could not settle this step, where it could not. A dry run that quietly dropped a
    #: unit it could not resolve would read as a unit with nothing to say.
    unresolved: str | None = None

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
        if self.unresolved:
            line += f"・実行前には確定しません（{self.unresolved}）"
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


@dataclass(frozen=True, slots=True)
class LoopCount:
    """How many times a loop runs, and **which of the three sources said so** (AC-026).

    Recording the source matters as much as the number: a loop that ran three times because the target
    set held three cases and a loop that ran three times because somebody typed 3 behave differently the
    next time a case is added, and afterwards the record is the only place the difference survives.
    """

    unit_id: str
    count: int
    source: str
    detail: str = ""

    def describe(self) -> str:
        named = {
            COUNT_LITERAL: "回数の直接指定",
            COUNT_FROM_VARIABLE: f"変数 '{self.detail}' の値の個数",
            COUNT_PER_CASE: "対象ケース 1 件につき 1 回",
        }[self.source]
        return f"{self.unit_id}：{self.count} 回（{named}）"


def _sequence_of(unit: dict[str, Any]) -> tuple[Value, ...]:
    symbol = unit.get("unit")
    declaration = {"kind": unit["quantityKind"]} if "quantityKind" in unit else None
    return tuple(
        quantity(float(item), symbol, declaration=declaration) for item in unit.get("values", [])
    )


def _resolve_count(
    unit: dict[str, Any],
    *,
    sequences: dict[str, tuple[Value, ...]],
    target_size: int,
) -> LoopCount:
    """The iteration count, fixed before the loop begins (XC-100).

    Refuses rather than guesses in both directions: a source this build cannot resolve, and a count
    above LIM-008. The ceiling is checked here rather than while looping, because AC-028 requires the
    refusal **before the run starts** - a formula yielding a million iterations should stop at edit
    time, not after a night of running.
    """
    unit_id = str(unit.get("id", ""))
    if COUNT_LITERAL in unit:
        resolved = LoopCount(unit_id, int(unit[COUNT_LITERAL]), COUNT_LITERAL)
    elif COUNT_FROM_VARIABLE in unit:
        name = str(unit[COUNT_FROM_VARIABLE])
        if name not in sequences:
            raise RunError(
                f"ループ '{unit_id}' は変数 '{name}' の値の個数で回りますが、"
                "その位置に複数値の変数がありません"
            )
        resolved = LoopCount(unit_id, len(sequences[name]), COUNT_FROM_VARIABLE, name)
    elif unit.get(COUNT_PER_CASE):
        resolved = LoopCount(unit_id, target_size, COUNT_PER_CASE)
    else:
        raise RunError(
            f"ループ '{unit_id}' に回数の指定がありません"
            f"（{COUNT_LITERAL}／{COUNT_FROM_VARIABLE}／{COUNT_PER_CASE}）"
        )
    if resolved.count > MAX_LOOP_ITERATIONS:
        raise RunError(
            f"ループ '{unit_id}' の回数が {resolved.count} 回に解決され、"
            f"上限 {MAX_LOOP_ITERATIONS} 回を超えます（LIM-008）。実行は始めません — "
            "回数は開始前に確定するので、一晩走らせてから気づく類の誤りではありません（AC-028）"
        )
    return resolved


def _bind(unit: dict[str, Any], bindings: Mapping[str, Value]) -> Value:
    """Evaluate a unit's expression against what is bound here, and return the result."""
    try:
        return evaluate(str(unit.get("expression", "")), bindings)
    except ExpressionError as error:
        raise RunError(f"ユニット '{unit.get('id')}' の式：{error}") from None


def _declare(
    unit: dict[str, Any],
    bindings: dict[str, Value],
    sequences: dict[str, tuple[Value, ...]],
) -> None:
    """Bind a variable unit's name for the units below it (AC-029).

    A several-valued variable is **not** bound as a value: it is what a loop counts over, and outside
    that loop there is no single value the name could mean.
    """
    name = str(unit.get("name", ""))
    if "values" in unit:
        sequences[name] = _sequence_of(unit)
        return
    # `quantityKind`, never the unit's own `kind`: a unit's kind is `variable`, and a reader of
    # INV-028's absolute-or-difference handed the whole unit reads that word as a temperature scale.
    declaration = {"kind": unit["quantityKind"]} if "quantityKind" in unit else None
    bindings[name] = quantity(
        float(unit.get("value", 0.0)), unit.get("unit"), declaration=declaration
    )


def _peek(unit: dict[str, Any], bindings: Mapping[str, Value]) -> bool | None:
    """A condition's value where the bindings at plan time settle it, and None where they cannot.

    None is an honest answer rather than a missing one: a condition inside a per-case loop has a value
    per iteration, and one number in its place would describe an execution that never happens.
    """
    try:
        result = evaluate(str(unit.get("expression", "")), bindings)
    except ExpressionError:
        return None
    return result.magnitude if isinstance(result.magnitude, bool) else None


def dry_run(
    pipeline: dict[str, Any],
    *,
    cases: Iterable[str],
    variables: Mapping[str, Value] | None = None,
) -> DryRun:
    """What the run would do, changing nothing (AC-008, AC-024).

    Loop counts and condition values are **resolved from the document** where the bindings at that point
    allow it, and left undetermined where they do not. There is no parameter to supply either: a count
    the caller passed in would be a second answer to a question XC-100 already says the document
    settles, and the two would disagree the day somebody edited only one of them.

    A loop's contents are listed **once**, with the count on the loop. Listing a thousand repetitions of
    the same three steps is a dry run nobody reads, which is the same as not having one.
    """
    targets = TargetSet()
    bindings: dict[str, Value] = dict(variables or {})
    sequences: dict[str, tuple[Value, ...]] = {}
    steps: list[Step] = []

    def describe_units(units: list[dict[str, Any]], scope: dict[str, Value]) -> None:
        for unit in units:
            unit_id = str(unit.get("id", ""))
            kind = kind_of(unit)
            acting: tuple[str, ...] = ()
            count: LoopCount | None = None
            value: bool | None = None
            unresolved: str | None = None

            if kind is Kind.ADD_CASES:
                targets.add(unit_id, unit.get("caseIds") or list(cases))
            elif kind is Kind.CLEAR:
                acting = tuple(targets.cases)
                targets.clear(unit_id)
            elif kind is Kind.VARIABLE:
                _declare(unit, bindings, sequences)
            elif kind is Kind.FORMULA:
                # A formula inside a per-case loop reads quantities of the case in scope, and at plan
                # time there is no case in scope. Left undetermined and **said so** rather than either
                # guessed at or dropped: the run refuses it if it is genuinely wrong.
                try:
                    bindings[str(unit.get("name", ""))] = _bind(unit, {**bindings, **scope})
                except RunError as error:
                    unresolved = str(error)
            elif kind is Kind.LOOP:
                count = _resolve_count(unit, sequences=sequences, target_size=len(targets.cases))
            elif kind is Kind.CONDITION:
                value = _peek(unit, {**bindings, **scope})
                if value is None:
                    unresolved = "この位置では条件の値が反復ごとに変わります"
            else:
                acting = tuple(targets.cases)

            steps.append(
                Step(
                    unit_id=unit_id,
                    kind=kind,
                    cases=acting,
                    set_size=len(targets.cases),
                    writes=tuple(f"{unit_id}/{case}" for case in acting)
                    if kind in ACT_ON_TARGETS
                    else (),
                    iterations=count.count if count else None,
                    condition_value=value,
                    destructive=kind in DESTRUCTIVE,
                    count_source=count.source if count else None,
                    unresolved=unresolved,
                )
            )
            if kind in CONTAINERS:
                # A loop binds **nothing** for its contents here, and that is the decision rather than
                # an omission. Binding the index to its first value would let a formula and a condition
                # inside the loop resolve - to the answer for iteration zero, stated as though it were
                # the answer for all of them. A condition reading `i > 0` would be planned as false and
                # run as true twice out of three times, and the plan is what somebody authorises a
                # destructive step against. Undetermined, with the reason, and the run settles it.
                describe_units(unit.get("units") or [], dict(scope))

    describe_units(pipeline.get("units", []), {})
    return DryRun(tuple(steps))


@dataclass(slots=True)
class _State:
    """What one run carries through its units.

    Held in one object so the recursion threads one parameter rather than eight, and so a nested call
    cannot quietly forget one of them.
    """

    record: RunRecord
    targets: TargetSet
    granted: list[Authorisation]
    act: Callable[[dict[str, Any], str], None] | None
    quantities_of: Callable[[str], Mapping[str, Value]] | None
    on_failure: OnFailure
    cancel_after: str | None
    failed: set[str] = dataclass_field(default_factory=set)
    sequences: dict[str, tuple[Value, ...]] = dataclass_field(default_factory=dict)
    stopped: bool = False


def run(
    pipeline: dict[str, Any],
    *,
    cases: Iterable[str],
    revision: int = 1,
    act: Callable[[dict[str, Any], str], None] | None = None,
    variables: Mapping[str, Value] | None = None,
    quantities_of: Callable[[str], Mapping[str, Value]] | None = None,
    authorisations: Iterable[Authorisation] = (),
    on_failure: OnFailure = OnFailure.CONTINUE,
    cancel_after: str | None = None,
) -> RunRecord:
    """Run a pipeline, isolating failures to their case and writing down what happened.

    `act` performs one unit for one case and raises to fail it. Injected rather than dispatched here, so
    this module holds the rules about failure and authorisation and nothing about views or exports.
    `quantities_of` supplies the recorded quantities of a case, which is what "the case in scope" means
    to an expression inside a per-case loop.

    `cancel_after` names the unit to stop after, which is how a cancellation arrives at this layer: at a
    **unit boundary**, keeping what completed (AC-014).
    """
    record = RunRecord(str(pipeline.get("id", "")), revision, tuple(cases))
    bindings: dict[str, Value] = dict(variables or {})

    # AC-028: every loop count is resolved before anything runs, and one above LIM-008 refuses the run
    # rather than being discovered a night later. The dry run is what resolves them, so the check and
    # the plan cannot disagree - a second resolver here would be a second answer to the same question.
    dry_run(pipeline, cases=record.resolved_cases, variables=bindings)

    state = _State(
        record=record,
        targets=TargetSet(),
        granted=list(authorisations),
        act=act,
        quantities_of=quantities_of,
        on_failure=on_failure,
        cancel_after=cancel_after,
    )
    _execute(pipeline.get("units", []), state, bindings, {})
    return record


def _execute(
    units: list[dict[str, Any]],
    state: _State,
    bindings: dict[str, Value],
    scope: Mapping[str, Value],
) -> None:
    """Run one level of a pipeline.

    Recursive, because a loop and a condition contain their own level: a flat walk would run their
    contents once whatever the loop count said and whatever the condition evaluated to.
    """
    record = state.record
    for unit in units:
        if state.stopped:
            return
        unit_id = str(unit.get("id", ""))
        kind = kind_of(unit)

        if kind is Kind.ADD_CASES:
            state.targets.add(unit_id, unit.get("caseIds") or record.resolved_cases)
            record.results.append(UnitResult(unit_id, None, Outcome.DONE, len(state.targets.cases)))
        elif kind is Kind.CLEAR:
            _clear(unit_id, state)
        elif kind is Kind.VARIABLE:
            _declare(unit, bindings, state.sequences)
            detail = "ワークスペースの変数も更新します" if unit.get("toWorkspace") else None
            record.results.append(
                UnitResult(unit_id, None, Outcome.DONE, len(state.targets.cases), detail)
            )
        elif kind is Kind.FORMULA:
            result = _bind(unit, {**bindings, **scope})
            bindings[str(unit.get("name", ""))] = result
            record.results.append(
                UnitResult(unit_id, None, Outcome.DONE, len(state.targets.cases), result.describe())
            )
        elif kind is Kind.CONDITION:
            _condition(unit, state, bindings, scope)
        elif kind is Kind.LOOP:
            _loop(unit, state, bindings, scope)
        else:
            _act_on_targets(unit, kind, state)
            if kind in CONTAINERS:
                _execute(unit.get("units") or [], state, bindings, scope)

        if state.cancel_after is not None and unit_id == state.cancel_after:
            record.stopped_at = unit_id
            state.stopped = True


def _clear(unit_id: str, state: _State) -> None:
    size = len(state.targets.cases)
    if not _authorised(state.granted, unit_id, size):
        state.record.results.append(
            UnitResult(unit_id, None, Outcome.SKIPPED_UNAUTHORISED, size,
                       "破壊的ユニットの承認がありません")
        )
        return
    state.targets.clear(unit_id)
    state.record.results.append(UnitResult(unit_id, None, Outcome.DONE, 0))


def _condition(
    unit: dict[str, Any],
    state: _State,
    bindings: dict[str, Value],
    scope: Mapping[str, Value],
) -> None:
    """Run the contents when the expression is true; record them when it is false (AC-033, AC-034).

    Recorded **with the value the expression evaluated to**, so that a report never written is
    distinguishable from one never asked for. Leaving the contents out of the record would make the two
    look identical, and the second is fine while the first needs somebody to look.
    """
    unit_id = str(unit.get("id", ""))
    result = _bind(unit, {**bindings, **scope})
    if not isinstance(result.magnitude, bool):
        raise RunError(f"条件ユニット '{unit_id}' の式が真偽値になりません（{result.describe()}）")
    state.record.results.append(
        UnitResult(unit_id, None, Outcome.DONE, len(state.targets.cases),
                   f"条件は {'真' if result.magnitude else '偽'}")
    )
    if result.magnitude:
        _execute(unit.get("units") or [], state, bindings, scope)
        return
    for skipped, _ in walk(unit.get("units") or []):
        state.record.results.append(
            UnitResult(
                str(skipped.get("id", "")), None, Outcome.SKIPPED_CONDITION,
                len(state.targets.cases),
                f"条件 '{unit.get('expression')}' が偽（{unit_id}）のため実行していません",
            )
        )


def _loop(
    unit: dict[str, Any],
    state: _State,
    bindings: dict[str, Value],
    scope: Mapping[str, Value],
) -> None:
    """Repeat the contents the resolved number of times, binding the index under the declared name."""
    resolved = _resolve_count(unit, sequences=state.sequences, target_size=len(state.targets.cases))
    index_name = str(unit.get("indexName") or DEFAULT_INDEX_NAME)
    state.record.results.append(
        UnitResult(
            str(unit.get("id", "")), None, Outcome.DONE, len(state.targets.cases),
            resolved.describe(),
        )
    )
    values = state.sequences.get(str(unit.get(COUNT_FROM_VARIABLE, "")), ())
    for iteration in range(resolved.count):
        if state.stopped:
            return
        inner: dict[str, Value] = {**scope, index_name: Value(float(iteration))}
        if resolved.source == COUNT_FROM_VARIABLE:
            inner[str(unit[COUNT_FROM_VARIABLE])] = values[iteration]
        if resolved.source == COUNT_PER_CASE and state.quantities_of is not None:
            inner.update(state.quantities_of(state.targets.cases[iteration]))
        _execute(unit.get("units") or [], state, bindings, inner)


def _act_on_targets(unit: dict[str, Any], kind: Kind, state: _State) -> None:
    """The per-case half: one attempt per case, with a failure confined to its own case (XC-095)."""
    record = state.record
    unit_id = str(unit.get("id", ""))
    acting = state.targets.acted_on(unit_id)
    if not acting:
        record.results.append(UnitResult(unit_id, None, Outcome.SKIPPED_EMPTY, 0))
        return
    if kind in DESTRUCTIVE and not _authorised(state.granted, unit_id, len(acting)):
        # AC-010: the run continues and the destructive unit is reported as not authorised, rather than
        # the whole run being refused for one step somebody declined.
        record.results.append(
            UnitResult(unit_id, None, Outcome.SKIPPED_UNAUTHORISED, len(acting),
                       f"{len(acting)} 件を対象とする承認がありません")
        )
        return

    for case in acting:
        if case in state.failed:
            # XC-095: the rest of *this* case is skipped. Continuing within a failed case would build on
            # a state nobody checked.
            record.results.append(
                UnitResult(unit_id, case, Outcome.SKIPPED_AFTER_FAILURE, len(acting),
                           "このケースは先の工程で失敗しています")
            )
            continue
        try:
            if state.act is not None:
                state.act(unit, case)
        except Exception as error:  # noqa: BLE001 - a unit may fail in any way it likes
            state.failed.add(case)
            record.results.append(
                UnitResult(unit_id, case, Outcome.FAILED, len(acting), str(error)[:200])
            )
            if state.on_failure is OnFailure.STOP:
                record.stopped_at = unit_id
                state.stopped = True
                return
            continue
        record.results.append(UnitResult(unit_id, case, Outcome.DONE, len(acting)))
        if kind in ACT_ON_TARGETS:
            record.written.append(f"{unit_id}/{case}")


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
