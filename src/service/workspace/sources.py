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
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


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


def _modified_iso(path: Path) -> str:
    """The file's modification time, to the second and in UTC.

    To the second because that is the resolution a recorded ISO string carries across the filesystems
    this product meets; comparing finer would report a change every time a file is copied.
    """
    stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return stamp.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record(path: Path, *, relative_to: Path) -> dict[str, Any]:
    """The reference CT-001 stores for a file: where it is, how big, and when it changed."""
    return {
        "pathRelative": path.relative_to(relative_to).as_posix(),
        "sizeBytes": path.stat().st_size,
        "modifiedIso": _modified_iso(path),
    }


def status_of(source: dict[str, Any], *, relative_to: Path) -> SourceStatus:
    """What is true now of one recorded source. Reads the file's metadata and never its contents."""
    relative = str(source.get("pathRelative", ""))
    recorded_size = int(source.get("sizeBytes", -1))
    recorded_modified = str(source.get("modifiedIso", ""))
    location = relative_to / relative

    if not location.exists():
        return SourceStatus(relative, SourceState.MISSING, recorded_size, recorded_modified)

    current_size = location.stat().st_size
    current_modified = _modified_iso(location)
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
