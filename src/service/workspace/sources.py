"""Whether a @Case's input files are still the ones it was built from.

CT-001 records a reference to each result file - a relative path, a size and a modification time - and
never the file's contents. workspace/AC-012 says what to do when one of those no longer matches: **open
the workspace, mark that case unresolved, and delete or rewrite nothing.**

Three things follow, and the third is the one worth stating.

A missing file and a changed file are **different states**, not one "problem" state. A user can restore
a missing file; a changed one they have to decide about, because the numbers in the workspace were
computed from what it used to be.

A changed file is detected and **not re-read**. Silently re-reading it would replace every figure in the
workspace with figures from a different input, under a report someone already wrote.

And the check is of the **recorded** size and time against the current ones. It is not a checksum: a
file whose bytes changed while its size and mtime did not is not detected here, and the contract does
not claim otherwise. Saying which is which is cheaper than a promise this cannot keep.

Specification: CT-001, workspace/AC-012.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from domain_core.recorded_time import record_instant


class SourceState(str, Enum):
    """What became of one file a @Case was built from."""

    PRESENT = "present"    # there, and the same size and time as recorded
    MISSING = "missing"    # not there
    CHANGED = "changed"    # there, and no longer what was recorded


@dataclass(frozen=True, slots=True)
class SourceStatus:
    """One recorded source, and what is true of it now."""

    path_relative: str
    state: SourceState
    recorded_size: int
    recorded_modified: str
    current_size: int | None = None
    current_modified: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.state is SourceState.PRESENT

    def describe(self) -> str:
        if self.state is SourceState.PRESENT:
            return f"{self.path_relative}：記録どおりです"
        if self.state is SourceState.MISSING:
            return f"{self.path_relative}：ファイルがありません。読み込みも書き換えもしていません"
        return (
            f"{self.path_relative}：記録時と異なります"
            f"（記録 {self.recorded_size} バイト {self.recorded_modified}、"
            f"現在 {self.current_size} バイト {self.current_modified}）。"
            "読み直していません — このワークスペースの数値は記録時のファイルから計算されています"
        )


def _modified_utc(path: Path) -> str:
    """The file's modification time, to the second and in UTC - the instant half of a recorded time.

    To the second because that is the resolution a recorded ISO string carries across the filesystems
    this product meets; comparing finer would report a change every time a file is copied.
    """
    stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return stamp.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record(path: Path, *, relative_to: Path, where: datetime) -> dict[str, Any]:
    """The reference CT-001 stores for a file: where it is, how big, and when it changed - the time
    as `{utc, offsetMinutes}`, the offset being that of whoever is recording (`where`, an aware
    moment from the recorder's clock; XC-266)."""
    return {
        "pathRelative": path.relative_to(relative_to).as_posix(),
        "sizeBytes": path.stat().st_size,
        "modified": record_instant(
            datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc), where=where,
        ).as_stored(),
    }


def status_of(source: dict[str, Any], *, relative_to: Path) -> SourceStatus:
    """What is true now of one recorded source. Reads the file's metadata and never its contents."""
    relative = str(source.get("pathRelative", ""))
    recorded_size = int(source.get("sizeBytes", -1))
    recorded = source.get("modified")
    recorded_modified = str(recorded.get("utc", "")) if isinstance(recorded, dict) else ""
    location = relative_to / relative

    if not location.exists():
        return SourceStatus(relative, SourceState.MISSING, recorded_size, recorded_modified)

    current_size = location.stat().st_size
    current_modified = _modified_utc(location)
    if current_size == recorded_size and current_modified == recorded_modified:
        return SourceStatus(
            relative, SourceState.PRESENT, recorded_size, recorded_modified,
            current_size, current_modified,
        )
    return SourceStatus(
        relative, SourceState.CHANGED, recorded_size, recorded_modified,
        current_size, current_modified,
    )


@dataclass(frozen=True, slots=True)
class CaseResolution:
    """Whether a @Case's inputs are all still there, and which are not."""

    case_id: str
    sources: tuple[SourceStatus, ...]

    @property
    def is_resolved(self) -> bool:
        return all(source.is_resolved for source in self.sources)

    @property
    def unresolved(self) -> tuple[SourceStatus, ...]:
        return tuple(source for source in self.sources if not source.is_resolved)

    def describe(self) -> str:
        if self.is_resolved:
            return f"ケース '{self.case_id}'：入力 {len(self.sources)} 件はすべて記録どおりです"
        missing = sum(1 for s in self.unresolved if s.state is SourceState.MISSING)
        changed = sum(1 for s in self.unresolved if s.state is SourceState.CHANGED)
        parts = []
        if missing:
            parts.append(f"不明 {missing} 件")
        if changed:
            parts.append(f"変更 {changed} 件")
        return (
            f"ケース '{self.case_id}' は未解決です（{'・'.join(parts)}）。"
            "ワークスペースは開いており、何も削除も書き換えもしていません"
        )


def resolve_case(case: dict[str, Any], *, relative_to: Path) -> CaseResolution:
    """Check every source a case records, without opening any of them."""
    return CaseResolution(
        case_id=str(case.get("id", "")),
        sources=tuple(
            status_of(source, relative_to=relative_to) for source in case.get("sources", [])
        ),
    )


# ---- what a person declared about a source's fields (CT-001 `declaredUnits`, XC-003) ------------

def _same_file(candidate: Path, path: Path) -> bool:
    try:
        return candidate.resolve() == path.resolve()
    except OSError:
        return False


def find_source(case: dict[str, Any], path: Path, *, relative_to: Path) -> dict[str, Any] | None:
    """The case's entry for this file, by its relative or its absolute path, or None."""
    for source in case.get("sources") or []:
        relative = source.get("pathRelative")
        if relative and _same_file(relative_to / str(relative), path):
            return source
        absolute = source.get("pathAbsolute")
        if absolute and _same_file(Path(str(absolute)), path):
            return source
    return None


def ensure_source(
    case: dict[str, Any], path: Path, *, relative_to: Path, where: datetime,
) -> tuple[dict[str, Any], bool]:
    """The case's entry for this file, created from the file itself when the case had none.

    Returns the entry and whether it was created. A file outside the workspace's directory gets the
    nearest relative path the platform allows and its absolute path beside it (CT-001 keeps both);
    on another drive, where no relative path exists, the absolute path stands in and says so by
    being absolute.
    """
    found = find_source(case, path, relative_to=relative_to)
    if found is not None:
        found.setdefault("declaredUnits", {})
        return found, False
    try:
        source = record(path, relative_to=relative_to, where=where)
    except ValueError:
        source = record(path, relative_to=path.parent, where=where)
        try:
            source["pathRelative"] = Path(os.path.relpath(path.resolve(), relative_to.resolve())).as_posix()
        except ValueError:
            source["pathRelative"] = path.resolve().as_posix()
    source["pathAbsolute"] = str(path.resolve())
    source["declaredUnits"] = {}
    case.setdefault("sources", []).append(source)
    return source, True


def declared_units(source: dict[str, Any]) -> dict[str, str]:
    """Field name to unit symbol, as declared; empty where nothing was. Never a guess (XC-003)."""
    units = source.get("declaredUnits")
    if not isinstance(units, dict):
        return {}
    return {str(name): symbol for name, symbol in units.items() if isinstance(symbol, str)}


def record_unit(source: dict[str, Any], field_name: str, symbol: str) -> str | None:
    """Write one declaration into the entry; returns what it replaced, if anything."""
    units = source.setdefault("declaredUnits", {})
    previous = units.get(field_name)
    units[field_name] = symbol
    return previous if isinstance(previous, str) else None


def forget_unit(source: dict[str, Any], field_name: str, previous: str | None) -> None:
    """Undo `record_unit`: put back what was there, or remove what was not."""
    units = source.setdefault("declaredUnits", {})
    if previous is None:
        units.pop(field_name, None)
    else:
        units[field_name] = previous
