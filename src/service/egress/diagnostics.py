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

import json
import os
import zipfile
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from pathlib import Path

from domain_core.os_paths import for_people
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Sequence

from domain_core.recorded_time import RecordedTime, from_stored, record as record_time


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
        line = f"{self.at.describe_where_recorded()} {self.level.value} {self.event}"
        if self.context:
            line += "｜" + "、".join(f"{k}={v}" for k, v in sorted(self.context.items()))
        return line

    def as_json(self) -> dict[str, Any]:
        """The line as it is written to the file: when (UTC and the offset it was recorded in), the
        level, the event, and the context - which the constructor already refused a value into."""
        return {
            "at": self.at.as_stored(),
            "level": self.level.value,
            "event": self.event,
            **self.context,
        }


def line_from_stored(stored: Mapping[str, Any]) -> Line:
    """One line as `as_json` wrote it, read back: the time as the pair, the level, the event, and
    everything else as the context it was."""
    context = {key: value for key, value in stored.items() if key not in ("at", "level", "event")}
    return Line(from_stored(stored["at"]), Level(str(stored["level"])), str(stored["event"]), context)


@dataclass(frozen=True, slots=True)
class Reading:
    """What a read of the log answered: the lines, and what was left out - by the limit, and by
    not being readable at all."""

    lines: tuple[Line, ...]
    omitted: int = 0
    unreadable: int = 0


#: The file the log is written to, in the directory the shell names (XC-263).
LOG_FILE = "solvia.log"

#: One file at most this size before it is rotated; this many rotated files kept; rotated files
#: older than this many days removed at open. Five megabytes is a week of a busy session at a few
#: hundred bytes a line; five of them is what a support bundle can carry (XC-126) without becoming
#: the largest thing in it. "Seven days" is what the settings page has promised since the design
#: (直近7日); the code now keeps the promise.
MAX_LOG_BYTES = 5_000_000
KEEP_ROTATED = 5
RETAIN_DAYS = 7

#: In memory, whatever the file says: what a screen may read back without opening files.
KEEP_IN_MEMORY = 1_000

LEVEL_ORDER = (Level.DEBUG, Level.INFO, Level.WARNING, Level.ERROR)


class Log:
    """The local log. Written here, read here, and sent by nothing (XC-126).

    With a `directory` it is also a file: one JSON object per line, rotated at `MAX_LOG_BYTES`, at
    most `KEEP_ROTATED` rotated files kept, rotated files older than `RETAIN_DAYS` removed when the
    log is opened (#312, XC-263). Lines below `level` are not written anywhere. Without a directory
    it is memory only, which is what a test wants and what a development run gets unless it asks.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        directory: Path | str | None = None,
        level: Level = Level.INFO,
    ) -> None:
        self._lines: list[Line] = []
        self._clock = clock or (lambda: datetime.now().astimezone())
        self.level = level
        self.directory = Path(directory) if directory is not None else None
        self.written_bytes = 0
        if self.directory is not None:
            self.directory.mkdir(parents=True, exist_ok=True)
            self._sweep()
            self.written_bytes = self.path.stat().st_size if self.path.exists() else 0

    @property
    def path(self) -> Path:
        assert self.directory is not None
        return self.directory / LOG_FILE

    def _sweep(self) -> None:
        """Rotated files past the retention period go; the live file stays whatever its age."""
        assert self.directory is not None
        cutoff = self._clock().timestamp() - RETAIN_DAYS * 86_400
        for old in self.directory.glob(LOG_FILE + ".*"):
            try:
                if old.stat().st_mtime < cutoff:
                    old.unlink()
            except OSError:
                continue

    def _rotate(self) -> None:
        assert self.directory is not None
        oldest = self.directory / f"{LOG_FILE}.{KEEP_ROTATED}"
        if oldest.exists():
            oldest.unlink()
        for index in range(KEEP_ROTATED - 1, 0, -1):
            source = self.directory / f"{LOG_FILE}.{index}"
            if source.exists():
                os.replace(source, self.directory / f"{LOG_FILE}.{index + 1}")
        if self.path.exists():
            os.replace(self.path, self.directory / f"{LOG_FILE}.1")
        self.written_bytes = 0

    def enabled(self, level: Level) -> bool:
        return LEVEL_ORDER.index(level) >= LEVEL_ORDER.index(self.level)

    def record(self, level: Level, event: str, **context: Any) -> Line | None:
        """One line, if the level allows it. The context is checked before anything is written."""
        if not self.enabled(level):
            return None
        line = Line(record_time(self._clock()), level, event, dict(context))
        self._lines.append(line)
        if len(self._lines) > KEEP_IN_MEMORY:
            del self._lines[: len(self._lines) - KEEP_IN_MEMORY]
        if self.directory is not None:
            encoded = (json.dumps(line.as_json(), ensure_ascii=False) + "\n").encode("utf-8")
            if self.written_bytes + len(encoded) > MAX_LOG_BYTES:
                self._rotate()
            with self.path.open("ab") as handle:
                handle.write(encoded)
            self.written_bytes += len(encoded)
        return line

    def lines(self) -> tuple[Line, ...]:
        return tuple(self._lines)

    @property
    def source(self) -> str:
        """Where a read comes from: `file` outlives the process, `memory` ends with it (XC-286)."""
        return "file" if self.directory is not None else "memory"

    def _files_oldest_first(self) -> list[Path]:
        assert self.directory is not None
        rotated = [self.directory / f"{LOG_FILE}.{index}" for index in range(KEEP_ROTATED, 0, -1)]
        return [one for one in [*rotated, self.path] if one.exists()]

    def read(self, *, level: Level = Level.DEBUG, since: str | None = None, limit: int = 500) -> "Reading":
        """The log as a person reads it back: the newest `limit` lines at `level` or above, from
        `since` (a UTC instant) on, and what was left out said in numbers (XC-286).

        From the files where there are files - the rotated ones oldest first, then the live one - so
        a session started after the last one closed reads what that one wrote; from memory where
        the log is memory only, which the answer says. A line the parser cannot read (a write cut
        short by a crash) is counted, never guessed at.
        """
        found: list[Line] = []
        unreadable = 0
        if self.directory is None:
            found = list(self._lines)
        else:
            for one in self._files_oldest_first():
                try:
                    raw = one.read_text(encoding="utf-8").splitlines()
                except OSError:
                    unreadable += 1
                    continue
                for text in raw:
                    if not text.strip():
                        continue
                    try:
                        found.append(line_from_stored(json.loads(text)))
                    except (ValueError, KeyError, TypeError, DiagnosticsError):
                        unreadable += 1
        floor = LEVEL_ORDER.index(level)
        kept = [
            one for one in found
            if LEVEL_ORDER.index(one.level) >= floor and (since is None or one.at.utc >= since)
        ]
        omitted = max(0, len(kept) - limit)
        return Reading(tuple(kept[len(kept) - limit:] if omitted else kept), omitted=omitted, unreadable=unreadable)

    def as_text(self) -> str:
        return "\n".join(one.describe() for one in self._lines)

    def describe_location(self) -> dict[str, Any]:
        """Where the log is and how it is kept - what a settings page shows (#312: reachable)."""
        files = sorted(self.directory.glob(LOG_FILE + "*")) if self.directory is not None else []
        return {
            "logDirectory": str(for_people(self.directory)) if self.directory is not None else None,
            "level": self.level.value,
            "maxBytes": MAX_LOG_BYTES,
            "keepFiles": KEEP_ROTATED,
            "retainDays": RETAIN_DAYS,
            "files": len(files),
            "bytes": sum(one.stat().st_size for one in files if one.exists()),
        }


@dataclass(frozen=True, slots=True)
class Item:
    """One thing a bundle would contain, in the words the user is shown."""

    kind: str      # log, shell, product, environment, workspace, case, file
    name: str
    detail: str = ""

    @property
    def customer(self) -> bool:
        """A case name or a file path is the customer's information (XC-126, XC-302)."""
        return self.kind in ("case", "file")

    def describe(self) -> str:
        return f"{self.kind}：{self.name}" + (f"（{self.detail}）" if self.detail else "")


@dataclass(frozen=True, slots=True)
class Include:
    """What the person chose to include of their own information (XC-302). Both default to no."""

    case_names: bool = False
    file_paths: bool = False

    @property
    def free_text(self) -> bool:
        """Whether the log's free text - a refusal's reason, a warning's sentence - goes in as it is.
        Either can carry a case name or a path, and nothing here guesses which words are which, so
        the text goes in only when both were included and is replaced otherwise (XC-302, #419)."""
        return self.case_names and self.file_paths

    def as_answer(self) -> dict[str, bool]:
        return {"caseNames": self.case_names, "filePaths": self.file_paths}


#: What stands in for a log line's free text when it is not included (XC-302).
REDACTED = "（伏せました：ケース名やパスを含みうるため）"
#: The context keys that hold free text: a refusal's reason and a warning's sentence (handlers.log_entry).
FREE_TEXT_KEYS = ("reason", "text")
#: Every line the files hold goes in; this is the ceiling the read is asked for - above what the
#: rotated files can hold at a hundred bytes a line, so nothing is left out by it.
BUNDLE_LINE_LIMIT = 1_000_000
#: The shell's own notes, beside the engine's log (XC-263); free text throughout, so it goes in
#: only when the log's free text does.
SHELL_LOG_FILE = "shell.log"


@dataclass(frozen=True, slots=True)
class Manifest:
    """Everything a bundle would contain, shown **before** it exists (AC-008).

    Case names and file paths are listed individually rather than counted. "3 files" is a number
    somebody accepts without reading; a customer's part name in the list is the thing they would have
    objected to, and they can only object to what they can see.
    """

    items: tuple[Item, ...]
    produced: RecordedTime | None = None
    #: What the person chose to include (XC-302); None where the caller decided by what it passed.
    include: Include | None = None

    @property
    def case_names(self) -> tuple[str, ...]:
        return tuple(one.name for one in self.items if one.kind == "case")

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(one.name for one in self.items if one.kind == "file")

    @property
    def free_text_kept(self) -> bool:
        return self.include.free_text if self.include is not None else True

    @property
    def fixed_items(self) -> tuple[Item, ...]:
        """The items that do not move with the log: what must still hold when the bundle is made."""
        return tuple(one for one in self.items if one.kind not in ("log", "shell"))

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

    def as_answer(self) -> dict[str, Any]:
        """The list as the interface shows it (CT-003 `system.supportManifest`)."""
        return {
            "items": [
                {"kind": one.kind, "name": one.name, "detail": one.detail, "customer": one.customer}
                for one in self.items
            ],
            "text": self.describe(),
            "customerItems": len(self.case_names) + len(self.paths),
            "producedAt": self.produced.as_stored() if self.produced is not None else None,
            "freeTextKept": self.free_text_kept,
        }


def manifest_for(
    log: Log,
    *,
    workspace_id: str | None = None,
    case_names: Iterable[str] = (),
    paths: Iterable[str] = (),
    clock: Callable[[], datetime] | None = None,
    include: Include | None = None,
    product_version: str | None = None,
    environment: Mapping[str, Any] | None = None,
    shell_lines: int | None = None,
) -> Manifest:
    """What a bundle would contain, assembled without creating one.

    The log is always in it, counted as the bundle would carry it, and its line says whether its
    free text goes in as it is (XC-302). The product's version and the environment are in it when
    given - never a path and never a user name. Case names and file paths are listed as given: the
    caller passes what the person chose, and the manifest lists what it was passed.
    """
    free_text = include.free_text if include is not None else True
    reading = log.read(level=Level.DEBUG, limit=BUNDLE_LINE_LIMIT)
    detail = f"{len(reading.lines)} 行" + (
        "・拒否理由と警告文はそのまま" if free_text else "・拒否理由と警告文は伏せます（ケース名やパスを含みうるため）"
    )
    if reading.unreadable:
        detail += f"・読めない行 {reading.unreadable}"
    items = [Item("log", "診断ログ", detail)]
    if shell_lines is not None:
        items.append(Item("shell", "シェルの記録", f"{shell_lines} 行"))
    if product_version is not None:
        items.append(Item("product", "製品の版", product_version))
    if environment is not None:
        items.append(Item("environment", "環境", "OS・Python・VTK の版と機械クラス。パスも利用者名も含みません"))
    if workspace_id:
        items.append(Item("workspace", workspace_id))
    items += [Item("case", name) for name in case_names]
    items += [Item("file", path) for path in paths]
    at = record_time((clock or (lambda: datetime.now().astimezone()))())
    return Manifest(tuple(items), at, include)


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


@dataclass(frozen=True, slots=True)
class Written:
    """An archive on disk, whole: where, how big, and what is in it."""

    path: Path
    bytes: int
    entries: tuple[str, ...]


def bundle_lines(log: Log, *, free_text: bool) -> tuple[list[dict[str, Any]], int]:
    """Every line the log holds, oldest first, as the bundle carries it: the free text as it is, or
    replaced by `REDACTED` where it was not included (XC-302). The count left unreadable comes too."""
    reading = log.read(level=Level.DEBUG, limit=BUNDLE_LINE_LIMIT)
    carried: list[dict[str, Any]] = []
    for one in reading.lines:
        stored = one.as_json()
        if not free_text:
            for key in FREE_TEXT_KEYS:
                if stored.get(key):
                    stored[key] = REDACTED
        carried.append(stored)
    return carried, reading.unreadable


def write_bundle(
    bundle: Bundle,
    *,
    path: Path,
    log: Log,
    product_version: str,
    environment: Mapping[str, Any],
    cases: Sequence[Mapping[str, Any]] = (),
    sources: Sequence[Mapping[str, Any]] = (),
    shell_log: Path | None = None,
) -> Written:
    """The archive, from a bundle whose manifest was accepted: written beside its target and moved
    into place, so it is whole or absent (XC-262), and never over a file that is there.

    What goes in is what the manifest lists and nothing else: the log's lines with their free text
    kept only where the manifest says so, the shell's notes where listed, the product and the
    environment, and the case names and recorded paths **only where the manifest lists them** - the
    caller may pass more, and the manifest decides, because what was accepted is what is written
    (AC-008).
    """
    if path.exists():
        raise DiagnosticsError(f"{path.name} はすでにあります。上書きしません — 別の場所を指定してください")
    manifest = bundle.manifest
    kinds = {one.kind for one in manifest.items}
    lines, unreadable = bundle_lines(log, free_text=manifest.free_text_kept)
    entries: list[str] = []
    temporary = path.with_name(path.name + ".writing")

    def put(archive: zipfile.ZipFile, name: str, text: str) -> None:
        archive.writestr(name, text)
        entries.append(name)

    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            put(archive, "manifest.txt", manifest.describe() + "\n")
            put(archive, "manifest.json", json.dumps({
                "items": manifest.as_answer()["items"],
                "producedAt": manifest.produced.as_stored() if manifest.produced is not None else None,
                "include": manifest.include.as_answer() if manifest.include is not None else None,
                "freeTextKept": manifest.free_text_kept,
                "logLinesWritten": len(lines),
                "logLinesUnreadable": unreadable,
                "productVersion": product_version,
            }, ensure_ascii=False, indent=2) + "\n")
            put(archive, "environment.json", json.dumps({"productVersion": product_version, **dict(environment)}, ensure_ascii=False, indent=2) + "\n")
            put(archive, "log/solvia.jsonl", "".join(json.dumps(one, ensure_ascii=False) + "\n" for one in lines))
            if "shell" in kinds and shell_log is not None and shell_log.exists():
                put(archive, "log/shell.log", shell_log.read_text(encoding="utf-8", errors="replace"))
            if "case" in kinds:
                put(archive, "cases.json", json.dumps(list(cases), ensure_ascii=False, indent=2) + "\n")
            if "file" in kinds:
                put(archive, "sources.json", json.dumps(list(sources), ensure_ascii=False, indent=2) + "\n")
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return Written(path, path.stat().st_size, tuple(entries))
