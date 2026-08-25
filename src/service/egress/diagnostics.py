"""The log this product writes about itself, and the bundle somebody may choose to send.

XC-126: logs are written locally, carry **no field values**, and are never sent anywhere on their own.
A support bundle is assembled on request, **lists everything it contains before it is created** -
including any case name or file path - and leaves only through the egress gate with explicit consent.

The reason is one measurement away from ordinary: automatic crash reporting produces better diagnostics
and sends a customer's part names to a third party without anybody deciding to. Every rule here is a
refusal to do that by accident.

**A log line cannot carry a float** (AC-007). Names are strings, counts are integers (INV-015), and a
measured value is a float - so refusing floats catches the shape a field value arrives in. What it does
not catch is a float somebody formatted into a string first, and that is worth knowing rather than
pretending otherwise: the check makes the accident hard and does not make the deliberate act impossible.

**The manifest exists before the bundle does** (AC-008). Not a list produced alongside it - a list the
user reads and then accepts, which is why `create` takes the manifest rather than the ingredients. A
bundle that reported its contents afterwards would be a bundle somebody found out about.

Specification: XC-126, XC-106, operations/AC-007, AC-008, INV-015.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Sequence

from domain_core.recorded_time import RecordedTime, record as record_time


class Level(str, Enum):
    """How much attention a line asks for. Four, and none of them changes what may be in it."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosticsError(Exception):
    """Raised where a line or a bundle would carry something it may not."""


#: The types a log context may hold. A float is absent on purpose: names are strings, counts are
#: integers (INV-015), and a value measured from a dataset is a float.
ALLOWED_CONTEXT = (str, int, bool, type(None))


@dataclass(frozen=True, slots=True)
class Line:
    """One local log line: what happened, and the names and counts around it - never a value."""

    at: RecordedTime
    level: Level
    event: str
    context: Mapping[str, Any] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in self.context.items():
            # `bool` is in the allowed types and is also a subclass of `int`, so it passes either way.
            # The first version special-cased it the wrong way round and rejected every flag.
            if not isinstance(value, ALLOWED_CONTEXT):
                if isinstance(value, float):
                    raise DiagnosticsError(
                        f"ログの '{name}' が浮動小数点数です。ログにフィールド値は書きません"
                        "（XC-126）— 名前は文字列、件数は整数で、測った値だけが浮動小数点数です"
                    )
                raise DiagnosticsError(
                    f"ログの '{name}' は {type(value).__name__} です。"
                    f"書けるのは {[t.__name__ for t in ALLOWED_CONTEXT]} のみです"
                )

    def describe(self) -> str:
        line = f"{self.at.utc} {self.level.value} {self.event}"
        if self.context:
            line += "｜" + "、".join(f"{k}={v}" for k, v in sorted(self.context.items()))
        return line


class Log:
    """The local log. Written here, read here, and sent by nothing (XC-126)."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._lines: list[Line] = []
        self._clock = clock or (lambda: datetime.now().astimezone())

    def record(self, level: Level, event: str, **context: Any) -> Line:
        line = Line(record_time(self._clock()), level, event, dict(context))
        self._lines.append(line)
        return line

    def lines(self) -> tuple[Line, ...]:
        return tuple(self._lines)

    def as_text(self) -> str:
        return "\n".join(one.describe() for one in self._lines)


@dataclass(frozen=True, slots=True)
class Item:
    """One thing a bundle would contain, in the words the user is shown."""

    kind: str      # log, workspace, case, file
    name: str
    detail: str = ""

    def describe(self) -> str:
        return f"{self.kind}：{self.name}" + (f"（{self.detail}）" if self.detail else "")


@dataclass(frozen=True, slots=True)
class Manifest:
    """Everything a bundle would contain, shown **before** it exists (AC-008).

    Case names and file paths are listed individually rather than counted. "3 files" is a number
    somebody accepts without reading; a customer's part name in the list is the thing they would have
    objected to, and they can only object to what they can see.
    """

    items: tuple[Item, ...]
    produced: RecordedTime | None = None

    @property
    def case_names(self) -> tuple[str, ...]:
        return tuple(one.name for one in self.items if one.kind == "case")

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(one.name for one in self.items if one.kind == "file")

    def describe(self) -> str:
        if not self.items:
            return "この診断情報には何も含まれません"
        lines = [f"この診断情報には次の {len(self.items)} 件が含まれます："]
        lines += [f"  - {one.describe()}" for one in self.items]
        if self.case_names or self.paths:
            lines.append(
                "うちケース名 "
                f"{len(self.case_names)} 件とファイルパス {len(self.paths)} 件は、"
                "お客さまの情報です。送るかどうかはこの一覧を見てから決めてください（XC-126）"
            )
        return "\n".join(lines)


def manifest_for(
    log: Log,
    *,
    workspace_id: str | None = None,
    case_names: Iterable[str] = (),
    paths: Iterable[str] = (),
    clock: Callable[[], datetime] | None = None,
) -> Manifest:
    """What a bundle would contain, assembled without creating one."""
    items = [Item("log", "診断ログ", f"{len(log.lines())} 行")]
    if workspace_id:
        items.append(Item("workspace", workspace_id))
    items += [Item("case", name) for name in case_names]
    items += [Item("file", path) for path in paths]
    at = record_time((clock or (lambda: datetime.now().astimezone()))())
    return Manifest(tuple(items), at)


@dataclass(frozen=True, slots=True)
class Bundle:
    """A created bundle, and the manifest it was created from."""

    manifest: Manifest
    contents: tuple[str, ...]

    def describe(self) -> str:
        return f"診断情報を作成しました（{len(self.contents)} 件）"


def create(manifest: Manifest, *, accepted: bool) -> Bundle:
    """Create a bundle from a manifest the user accepted (AC-008, XC-126).

    Takes the manifest rather than the ingredients, so a bundle cannot exist without a list having been
    shown first - a bundle that reported its contents afterwards would be one somebody found out about.
    """
    if not accepted:
        raise DiagnosticsError(
            "一覧が承諾されていません。診断情報は、何が入るかを見たうえで作ります（AC-008）"
        )
    if not manifest.items:
        raise DiagnosticsError("何も含まない診断情報は作りません")
    return Bundle(manifest, tuple(one.describe() for one in manifest.items))


def contents_for_egress(bundle: Bundle) -> Sequence[str]:
    """What the egress gate records as having been sent (XC-126).

    The **manifest's own lines**, so what is audited is what the user accepted rather than a summary
    produced separately - two descriptions of one bundle is one description too many.
    """
    return bundle.contents
