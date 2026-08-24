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

Specification: XC-141, XC-113, XC-046, LIM-012, workspace/AC-052, AC-053.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Iterable

from domain_core.locale_format import bytes_as_text
from engine.limits import MAX_OUTPUT_BYTES

#: What a run folder holds that must survive pruning: the record of how the run was made. Named here
#: rather than guessed at by extension, because "keep the record" is a promise and a promise kept by
#: pattern-matching stops being kept when somebody adds a file.
RECORD_NAMES = frozenset({"run.json", "record.json", "provenance.json"})


@dataclass(frozen=True, slots=True)
class Run:
    """One timestamped output folder, and what it holds."""

    identifier: str
    #: UTC, with the offset beside it (XC-142). Sorting by this is why a run folder is timestamped.
    at: str
    directory: Path

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
    ordered = sorted(runs, key=lambda run: (run.at, run.identifier))
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

    records = tuple(
        path
        for run in chosen
        for path in sorted(run.directory.glob("*"))
        if path.is_file() and path.name in RECORD_NAMES
    )
    return PrunePlan(tuple(chosen), tuple(files), freed, records)


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
