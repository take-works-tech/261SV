"""The one surface through which anything changes.

INV-006's claim is that the interface, the assistant, a script and a pipeline all act through the same
set of operations, and that none of them has a private path. That claim is what makes undo, the run
record, the dry run and the log each need to be built once instead of four times - so this module is
where all four are built, and a second dispatcher anywhere else would quietly undo the argument.

Four rules, each ruling out something plausible.

**Refusal beats assumption** (CT-002). An unknown operation, an unknown parameter, or an operation that
needs authorisation it was not given is refused with a named reason and **changes nothing**. CT-002 is
explicit about why this differs from CT-001, which preserves unknown fields: a document outlives the
program that wrote it and dropping a field destroys somebody's work, while a command is executed
immediately and an unrecognised parameter means the caller believes something is happening that is not.

**A read is not a write.** A read never enters the undo history and never needs confirmation. Which of
the two an operation is comes from the contract's own table, not from a guess at the name: `writes()`
raises on an operation it does not know rather than defaulting, because defaulting to read lets a write
escape undo and defaulting to write puts a question in front of an answer somebody just asked for.

**One instruction, one undo.** Commands sharing a `group_id` undo together, in reverse, and a script is
one group - deliberately unlike the reference application, where operators called from Python skip the
undo stack by default (XC-102). There, scripts mostly run before anyone is watching; here the customer
asks an agent to build forty reports and must be able to take it back.

**A dry run is the same command.** Resolved, reported, and applied to nothing. Not a second code path
that describes what the first one would do - two paths is how a dry run comes to describe an execution
that never happens.

Specification: CT-002, CT-003, INV-006, XC-061, XC-102, XC-128, operations/REQ-004.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Sequence

from domain_core.recorded_time import RecordedTime, record as record_time
from service.command.catalogue import OPERATIONS, PARAMETERS, RESULT_FIELDS, writes


class Origin(str, Enum):
    """Who issued a command. Recorded on every one of them (CT-002, XC-128).

    An autonomous agent is a caller like any other, which is only true if the record says which caller
    it was: "who changed this" is unanswerable afterwards from a log that treats them all alike.
    """

    INTERFACE = "interface"
    ASSISTANT = "assistant"
    SCRIPT = "script"
    PIPELINE = "pipeline"


class Status(str, Enum):
    """CT-003's four. `ANSWERED` is what a read returns - it applied nothing."""

    APPLIED = "applied"
    ANSWERED = "answered"
    REFUSED = "refused"
    FAILED = "failed"


class Permission(str, Enum):
    """Classes of operation that are refused headless unless explicitly allowed (CT-002)."""

    DESTRUCTIVE = "allowDestructive"
    OVERWRITE = "allowOverwrite"
    NETWORK = "allowNetwork"


@dataclass(frozen=True, slots=True)
class Command:
    """One request. The envelope of CT-002, and nothing beyond it."""

    operation: str
    parameters: Mapping[str, Any] = dataclass_field(default_factory=dict)
    origin: Origin = Origin.INTERFACE
    targets: tuple[str, ...] = ()
    group_id: str | None = None
    allowed: frozenset[Permission] = frozenset()
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class Result:
    """One response (CT-003). A refusal always carries a reason and changed nothing."""

    status: Status
    changed: tuple[str, ...] = ()
    effect_summary: str | None = None
    reason: str | None = None
    undo_id: str | None = None
    value: Any = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status in (Status.REFUSED, Status.FAILED) and not self.reason:
            raise ValueError("拒否と失敗には理由が要ります（CT-003）")
        if self.status is Status.REFUSED and self.changed:
            raise ValueError("拒否は何も変えません。changed があるなら拒否ではありません（CT-002）")


@dataclass(frozen=True, slots=True)
class Effect:
    """What a handler did, or would do. The handler's whole vocabulary.

    A handler returns this and never a `Result`: composing the response - the status, the undo id, the
    log line - is the surface's job, and a handler that could compose its own could compose one that
    says applied while the surface refused it.
    """

    summary: str
    changed: tuple[str, ...] = ()
    value: Any = None
    warnings: tuple[str, ...] = ()
    #: How to put this back. Required of a write, absent from a read, and checked at registration.
    undo: Callable[[], None] | None = None


@dataclass(frozen=True, slots=True)
class Handler:
    """One operation's implementation.

    `parameters` and `required` are **not** declared here any more: they come from CT-003 (`catalogue.
    PARAMETERS`). A handler that declared its own would be a second answer to what an operation takes,
    and the enforcement would hold against the copy rather than against the contract - which is what
    OPEN-028 recorded until the contract became machine-readable on 2026-08-25.
    """

    operation: str
    perform: Callable[[Mapping[str, Any], tuple[str, ...]], Effect]
    needs: frozenset[Permission] = frozenset()

    @property
    def parameters(self) -> frozenset[str]:
        return PARAMETERS[self.operation][0]

    @property
    def required(self) -> frozenset[str]:
        return PARAMETERS[self.operation][1]

    @property
    def answers(self) -> frozenset[str]:
        """The fields this operation's result may carry, from CT-003."""
        return RESULT_FIELDS[self.operation][0]

    @property
    def answers_required(self) -> frozenset[str]:
        """The fields it must carry. Where a number is among them, so is its unit (XC-003)."""
        return RESULT_FIELDS[self.operation][1]


@dataclass(frozen=True, slots=True)
class LogEntry:
    """One line of the log `history.list` reads back: what, who, when, and how it went."""

    operation: str
    origin: Origin
    at: RecordedTime
    status: Status
    reason: str | None = None
    undo_id: str | None = None
    group_id: str | None = None
    dry_run: bool = False

    def describe(self) -> str:
        line = f"{self.at.utc} {self.origin.value} {self.operation} → {self.status.value}"
        if self.dry_run:
            line += "（試算）"
        if self.reason:
            line += f"：{self.reason}"
        return line


class Surface:
    """The command surface: a registry, a dispatcher, an undo history and a log."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._handlers: dict[str, Handler] = {}
        self._log: list[LogEntry] = []
        #: undo id -> the undo callables of that group, in the order they were applied.
        self._undo: dict[str, list[Callable[[], None]]] = {}
        self._next = 0
        self._clock = clock or (lambda: datetime.now(timezone.utc).astimezone())

    # -- registration ------------------------------------------------------------------------

    def register(self, handler: Handler) -> None:
        """Add an implementation for one catalogue operation.

        Refuses an operation the contract does not list, and refuses a second implementation of one
        already registered. Both are the same mistake seen from two sides: the catalogue is the set,
        and a surface that quietly accepted an extra name or a replacement would make INV-006 a
        statement about the contract rather than about the product.
        """
        if handler.operation not in OPERATIONS:
            raise KeyError(
                f"'{handler.operation}' は CT-003 のカタログにありません。"
                "操作の集合は閉じています — 追加は契約の側に書いてから生成します"
            )
        if handler.operation in self._handlers:
            raise KeyError(f"'{handler.operation}' の実装はすでに登録されています")
        self._handlers[handler.operation] = handler

    def registered(self) -> tuple[str, ...]:
        return tuple(name for name in OPERATIONS if name in self._handlers)

    def unimplemented(self) -> tuple[str, ...]:
        """Catalogue operations this build has no handler for. Reported, never hidden."""
        return tuple(name for name in OPERATIONS if name not in self._handlers)

    # -- dispatch ----------------------------------------------------------------------------

    def submit(self, command: Command) -> Result:
        """Run one command, or refuse it with a reason. Never raises for a bad command.

        A refusal is a result rather than an exception because the caller is often a loop over forty
        cases, and one refused command is a line in a record, not the end of the study.
        """
        refusal = self._refusal(command)
        if refusal is not None:
            return self._record(command, refusal)

        handler = self._handlers[command.operation]
        is_write = writes(command.operation)

        if command.dry_run:
            effect = self._attempt(handler, command)
            if isinstance(effect, Result):
                return self._record(command, effect)
            # Nothing is kept: no undo entry, no changed list. The same command, resolved and reported.
            return self._record(
                command,
                Result(
                    Status.ANSWERED,
                    effect_summary=effect.summary,
                    value=effect.value,
                    warnings=effect.warnings,
                ),
            )

        effect = self._attempt(handler, command)
        if isinstance(effect, Result):
            return self._record(command, effect)

        if not is_write:
            return self._record(
                command,
                Result(
                    Status.ANSWERED,
                    effect_summary=effect.summary,
                    value=effect.value,
                    warnings=effect.warnings,
                ),
            )

        undo_id = self._keep(command, effect)
        return self._record(
            command,
            Result(
                Status.APPLIED,
                changed=effect.changed,
                effect_summary=effect.summary,
                undo_id=undo_id,
                value=effect.value,
                warnings=effect.warnings,
            ),
        )

    def submit_group(self, commands: Sequence[Command], *, group_id: str) -> tuple[Result, ...]:
        """Submit several commands as one undo step (assistant/AC-002, XC-061).

        One script is one undo step. The group is not abandoned when one command is refused: the caller
        asked for several things, and undoing what did happen is exactly what the group id is for.
        """
        return tuple(
            self.submit(
                Command(
                    command.operation,
                    command.parameters,
                    command.origin,
                    command.targets,
                    group_id,
                    command.allowed,
                    command.dry_run,
                )
            )
            for command in commands
        )

    def _refusal(self, command: Command) -> Result | None:
        if command.operation not in OPERATIONS:
            return Result(
                Status.REFUSED,
                reason=(
                    f"'{command.operation}' はこの製品の操作ではありません（CT-002）。"
                    "綴りの誤りを黙って通すと、呼び出し側は起きていないことが起きたと信じます"
                ),
            )
        handler = self._handlers.get(command.operation)
        if handler is None:
            return Result(
                Status.REFUSED,
                reason=(
                    f"'{command.operation}' はカタログにありますが、このビルドに実装がありません。"
                    "未知の操作とは別の事実として報告します"
                ),
            )
        unknown = sorted(set(command.parameters) - handler.parameters)
        if unknown:
            return Result(
                Status.REFUSED,
                reason=(
                    f"'{command.operation}' が受け付けない引数 {unknown} があります（CT-002）。"
                    f"受け付けるのは {sorted(handler.parameters)} です"
                ),
            )
        absent = sorted(handler.required - set(command.parameters))
        if absent:
            return Result(
                Status.REFUSED, reason=f"'{command.operation}' には {absent} が要ります"
            )
        withheld = sorted(
            permission.value for permission in handler.needs - command.allowed
        )
        if withheld:
            return Result(
                Status.REFUSED,
                reason=(
                    f"'{command.operation}' には {withheld} の承認が要ります。"
                    "承認がないことは拒否であって、仮定ではありません（CT-002）"
                ),
            )
        return None

    def _attempt(self, handler: Handler, command: Command) -> Effect | Result:
        try:
            effect = handler.perform(command.parameters, command.targets)
        except Exception as error:  # noqa: BLE001 - a handler may fail in any way it likes
            return Result(Status.FAILED, reason=str(error)[:400])
        if writes(command.operation) and not command.dry_run and effect.undo is None:
            return Result(
                Status.FAILED,
                reason=(
                    f"'{command.operation}' は状態を変える操作なのに、元に戻す方法を返していません。"
                    "取り消せない変更を履歴に載せるより、適用しないほうが安全です（XC-061）"
                ),
            )
        mismatch = self._answer_mismatch(handler, effect, dry_run=command.dry_run)
        if mismatch is not None:
            return Result(Status.FAILED, reason=mismatch)
        return effect

    @staticmethod
    def _answer_mismatch(handler: Handler, effect: Effect, *, dry_run: bool) -> str | None:
        """Why this effect is not the answer CT-003 states, or None.

        The mirror of the parameter check, pointed the other way: a caller is refused for sending a
        field the contract does not declare, and a **build** fails for returning one. It is `FAILED`
        rather than `REFUSED` because the caller did nothing wrong - the defect is here.

        A dry run is held to the field names and not to the required ones: it applies nothing, so it
        cannot produce the identifier or the revision that applying would have created, and requiring
        those of it would make every dry run of a write fail (CT-002).
        """
        declared, required = handler.answers, handler.answers_required
        value = effect.value
        if value is None:
            absent = sorted(required)
            if absent and not dry_run:
                return (
                    f"'{handler.operation}' は {absent} を返すと契約に書かれていますが、"
                    "何も返していません（CT-003）"
                )
            return None
        if not isinstance(value, Mapping):
            if not declared:
                return (
                    f"'{handler.operation}' は値を返さない操作ですが、"
                    f"{type(value).__name__} を返しています（CT-003）"
                )
            return (
                f"'{handler.operation}' の結果はオブジェクトです。"
                f"{type(value).__name__} では呼び出し側に型がありません（CT-003）"
            )
        unknown = sorted(set(value) - declared)
        if unknown:
            return (
                f"'{handler.operation}' が契約にない項目 {unknown} を返しています（CT-003）。"
                f"返せるのは {sorted(declared)} です — 契約にない項目は、呼び出し側の型に無い項目です"
            )
        absent = sorted(required - set(value))
        if absent and not dry_run:
            return (
                f"'{handler.operation}' の結果に {absent} がありません（CT-003）。"
                "単位や来歴が必須なのは、それが無い数値は読み手が仮定した単位の数値だからです（XC-003）"
            )
        return None

    def _keep(self, command: Command, effect: Effect) -> str:
        undo_id = command.group_id or self._identifier()
        if effect.undo is not None:
            self._undo.setdefault(undo_id, []).append(effect.undo)
        return undo_id

    def _identifier(self) -> str:
        self._next += 1
        return f"undo:{self._next:04d}"

    def _record(self, command: Command, result: Result) -> Result:
        self._log.append(
            LogEntry(
                operation=command.operation,
                origin=command.origin,
                at=record_time(self._clock()),
                status=result.status,
                reason=result.reason,
                undo_id=result.undo_id,
                group_id=command.group_id,
                dry_run=command.dry_run,
            )
        )
        return result

    # -- undo and log ------------------------------------------------------------------------

    def undo(self, undo_id: str) -> Result:
        """Put back everything applied under one undo id, in reverse order.

        Reverse because the commands were applied in order and each undo assumes the ones after it have
        already gone; forwards would put an earlier state back underneath a later one.
        """
        steps = self._undo.pop(undo_id, None)
        if steps is None:
            return Result(Status.REFUSED, reason=f"取り消し '{undo_id}' は履歴にありません")
        for step in reversed(steps):
            step()
        return Result(
            Status.APPLIED,
            effect_summary=f"{undo_id} の {len(steps)} 件を元に戻しました",
            undo_id=undo_id,
        )

    def history(self) -> tuple[LogEntry, ...]:
        """Every command, in order, with its origin, time and outcome (`history.list`)."""
        return tuple(self._log)

    def undoable(self) -> tuple[str, ...]:
        return tuple(self._undo)


def only_reads(commands: Iterable[Command]) -> bool:
    """Whether a sequence changes nothing - so a caller can tell before submitting any of it."""
    return all(not writes(command.operation) for command in commands)
