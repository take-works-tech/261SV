"""Run output grows without limit, so the product says how much and offers to prune by run.

Every @Pipeline run writes a new timestamped folder and never overwrites an earlier one (XC-113), which
is the right rule and means output grows for ever. XC-141 is what follows: report the space in use, and
offer pruning **by run, oldest first**.

Three refusals hold the shape.

**Nothing is deleted unnamed** (AC-053). A pruning that reports "freed 4.2 GB" has told the user a
number and not what it cost them. The plan lists every run it would remove before anything goes.

**Input data is never touched.** It is not this product's to delete: the user brought it, and an output
directory that also holds a source file is a directory nothing here removes items from by size.

**The run record survives its artefacts.** A deleted image stays reproducible because the record of how
it was made is still there (XC-046). Pruning removes what can be regenerated and keeps what cannot.

Across the wire the same three hold (XC-268): `output.list` says what is there, `output.plan` says
what would go for the runs a person chose, and `output.prune` deletes what the plan showed - the act
names the files it expects, and a folder that changed in between is refused rather than pruned.

Specification: XC-141, XC-113, XC-046, XC-268, LIM-012, workspace/AC-052, AC-053.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from domain_core.locale_format import bytes_as_text
from domain_core.recorded_time import RecordedTime, from_stored, record_instant
from engine.limits import MAX_OUTPUT_BYTES

#: What a run folder holds that must survive pruning: the record of how the run was made. Named here
#: rather than guessed at by extension, because "keep the record" is a promise and a promise kept by
#: pattern-matching stops being kept when somebody adds a file.
RECORD_NAMES = frozenset({"run.json", "record.json", "provenance.json"})

#: Where a workspace's output lives: under the document's own folder, as
#: `output/<pipeline or report name>/<run timestamp>/…` (XC-113).
OUTPUT_DIRECTORY = "output"


class OutputError(Exception):
    """Raised where a plan cannot be made honestly: a run that is not there, or one holding input data."""


@dataclass(frozen=True, slots=True)
class Run:
    """One timestamped output folder, and what it holds."""

    identifier: str
    #: When the run started: from its record where it has one, otherwise from the folder's own time
    #: with the recorder's offset - and `started_from` says which, because a time whose origin is not
    #: stated is a time nobody can check (XC-142, XC-266).
    at: RecordedTime
    directory: Path
    started_from: str = "record"

    def record_path(self) -> Path | None:
        """The record of how the run was made, where the folder has one."""
        for name in sorted(RECORD_NAMES):
            candidate = self.directory / name
            if candidate.is_file():
                return candidate
        return None

    def artefacts(self) -> tuple[Path, ...]:
        """Everything in the run that could be produced again. The record itself is not in here."""
        if not self.directory.exists():
            return ()
        return tuple(
            sorted(
                path for path in self.directory.rglob("*")
                if path.is_file() and path.name not in RECORD_NAMES
            )
        )

    def artefact_bytes(self) -> int:
        return sum(path.stat().st_size for path in self.artefacts())

    def as_stored(self) -> dict[str, Any]:
        """The wire form (CT-003 `output.list`): counted, sized, timed, and honest about the time."""
        files = self.artefacts()
        return {
            "id": self.identifier,
            "started": self.at.as_stored(),
            "startedFrom": self.started_from,
            "artefactFiles": len(files),
            "artefactBytes": sum(path.stat().st_size for path in files),
            "hasRecord": self.record_path() is not None,
        }


@dataclass(frozen=True, slots=True)
class OutputSize:
    """How much space a workspace's output occupies, and whether that is worth asking about."""

    total_bytes: int
    run_count: int
    limit_bytes: int = MAX_OUTPUT_BYTES

    @property
    def over_limit(self) -> bool:
        return self.total_bytes > self.limit_bytes

    def describe(self) -> str:
        line = f"出力は {bytes_as_text(self.total_bytes)}（{self.run_count} 実行分）です"
        if self.over_limit:
            line += (
                f"。上限 {bytes_as_text(self.limit_bytes)} を超えています。"
                "古い実行から順に整理できます — 拒否ではなく、確認のお願いです"
            )
        return line


@dataclass(frozen=True, slots=True)
class PrunePlan:
    """Which runs would be pruned, and exactly what would go."""

    runs: tuple[Run, ...] = dataclass_field(default_factory=tuple)
    files: tuple[Path, ...] = dataclass_field(default_factory=tuple)
    freed_bytes: int = 0
    kept_records: tuple[Path, ...] = dataclass_field(default_factory=tuple)

    def describe(self) -> str:
        """Every file, not a total. "Freed 4.2 GB" tells the user a number and not what it cost them."""
        if not self.runs:
            return "整理するものはありません"
        names = "、".join(run.identifier for run in self.runs)
        lines = [
            f"{len(self.runs)} 実行分（{names}）から {len(self.files)} ファイル、"
            f"{bytes_as_text(self.freed_bytes)} を削除します"
        ]
        lines += [f"  - {path.name}" for path in self.files]
        lines.append(
            f"実行の記録 {len(self.kept_records)} 件は残します — "
            "作り方の記録が残っていれば、消した成果物は作り直せます（XC-046）"
        )
        return "\n".join(lines)

    def as_stored(self, base: Path) -> dict[str, Any]:
        """The wire form (CT-003 `output.plan`): every file by its path under the output folder, so
        the list a person confirms and the list the act deletes can be compared word for word."""
        return {
            "runIds": [run.identifier for run in self.runs],
            "files": [_under(path, base) for path in self.files],
            "freedBytes": self.freed_bytes,
            "keptRecords": [_under(path, base) for path in self.kept_records],
        }


def _under(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def runs_of(output_directory: Path, *, where: datetime) -> list[Run]:
    """Every run under a workspace's output folder, laid out as `output/<name>/<run timestamp>/` (XC-113).

    A run's time comes from its record where one exists and carries `started`; otherwise from the
    folder's own modification time with the recorder's offset (`where`), and the run says which. A
    record that cannot be read is not a reason to hide the run: the folder's time stands, labelled.
    """
    if not output_directory.is_dir():
        return []
    runs: list[Run] = []
    for name_directory in sorted(one for one in output_directory.iterdir() if one.is_dir()):
        for run_directory in sorted(one for one in name_directory.iterdir() if one.is_dir()):
            started, origin = _started_of(run_directory, where)
            runs.append(Run(f"{name_directory.name}/{run_directory.name}", started, run_directory, origin))
    return runs


def _started_of(run_directory: Path, where: datetime) -> tuple[RecordedTime, str]:
    for name in sorted(RECORD_NAMES):
        record = run_directory / name
        if not record.is_file():
            continue
        try:
            parsed = json.loads(record.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and "started" in parsed:
                return from_stored(parsed["started"]), "record"
        except (ValueError, OSError):
            continue
    stamp = datetime.fromtimestamp(run_directory.stat().st_mtime, tz=timezone.utc)
    return record_instant(stamp, where=where), "folder"


def size_of(runs: Iterable[Run], *, limit_bytes: int = MAX_OUTPUT_BYTES) -> OutputSize:
    """How much a workspace's output occupies (AC-052)."""
    listed = list(runs)
    return OutputSize(
        total_bytes=sum(run.artefact_bytes() for run in listed),
        run_count=len(listed),
        limit_bytes=limit_bytes,
    )


def plan_pruning(
    runs: Iterable[Run], *, target_bytes: int | None = None, keep_newest: int = 1
) -> PrunePlan:
    """Which runs to prune, oldest first, to bring output under a target.

    `keep_newest` is not an optimisation. The newest run is what the user is most likely looking at, and
    a size-driven rule that removes it is a rule that deletes the thing somebody just made.
    """
    ordered = sorted(runs, key=lambda run: (run.at.utc, run.identifier))
    if len(ordered) <= keep_newest:
        return PrunePlan()

    target = MAX_OUTPUT_BYTES if target_bytes is None else target_bytes
    total = sum(run.artefact_bytes() for run in ordered)
    chosen: list[Run] = []
    files: list[Path] = []
    freed = 0

    for run in ordered[: len(ordered) - keep_newest]:
        if total - freed <= target:
            break
        chosen.append(run)
        for path in run.artefacts():
            files.append(path)
            freed += path.stat().st_size

    return PrunePlan(tuple(chosen), tuple(files), freed, _records_of(chosen))


def plan_for(runs: Iterable[Run], chosen_ids: Iterable[str], *, protected: Iterable[Path] = ()) -> PrunePlan:
    """The plan for the runs a person chose: every file that would go, and the records that stay.

    Refused, not narrowed, where it cannot be made honestly - a run that is not there, or one holding a
    file the workspace records as an input: input data is never this product's to delete, whatever
    folder it sits in (AC-053). A plan that quietly dropped that run would delete less than it said and
    say nothing.
    """
    by_id = {run.identifier: run for run in runs}
    chosen = list(dict.fromkeys(str(one) for one in chosen_ids))
    if not chosen:
        raise OutputError("取り除く実行が指定されていません")
    unknown = [one for one in chosen if one not in by_id]
    if unknown:
        raise OutputError(f"実行が見つかりません：{'、'.join(unknown)}。一覧を読み直してください")
    guarded = {_canonical(path) for path in protected}
    selected = [by_id[one] for one in chosen]
    files: list[Path] = []
    for run in selected:
        for path in run.artefacts():
            if _canonical(path) in guarded:
                raise OutputError(
                    f"実行 '{run.identifier}' には入力データ {path.name} が含まれています。"
                    "入力は消しません（AC-053）。この実行を外して選び直してください"
                )
            files.append(path)
    freed = sum(path.stat().st_size for path in files)
    return PrunePlan(tuple(selected), tuple(files), freed, _records_of(selected))


def _canonical(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _records_of(runs: Iterable[Run]) -> tuple[Path, ...]:
    return tuple(
        path
        for run in runs
        for path in sorted(run.directory.glob("*"))
        if path.is_file() and path.name in RECORD_NAMES
    )


def prune(plan: PrunePlan) -> int:
    """Delete exactly the files a plan named, and nothing else.

    Takes the plan rather than the runs, so what is deleted is what was shown. A function that
    recomputed the list would be free to delete something the user never saw.
    """
    removed = 0
    for path in plan.files:
        if path.exists():
            path.unlink()
            removed += 1
    return removed
