"""Sending a workspace to somebody who has neither the product's library nor your disk.

XC-140's shape, and each clause is there because the obvious version fails somewhere.

**The size is stated before the pack is written** (AC-048). A user asking for a workspace with its data
is asking for something that may be forty gigabytes, and finding that out from a full disk is finding
it out too late.

**Everything that could not go in is named** (AC-049) - a linked folder outside the workspace, an asset
whose licence forbids redistribution. Not counted: named. "3 items omitted" tells the recipient that
something is missing and not which thing, and the recipient is the person who cannot ask.

**A pack without data opens with every case unresolved** (AC-050), not with cases that look fine until
somebody clicks one. XC-136 already has the state for it, which is the whole reason it is a state
rather than a flag on a loader.

This module builds the manifest and states the cost; it does not write the archive. What goes in is a
decision about the user's disk and their licences, and it is made before a single byte is copied.

Specification: XC-140, XC-136, XC-085, workspace/AC-048, AC-049, AC-050.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from service.workspace.case_state import CaseState
from service.workspace.hierarchy import walk


class Omission(str, Enum):
    """Why something the workspace refers to is not in the pack."""

    OUTSIDE = "outside"            # a linked folder the workspace only points at
    NOT_REDISTRIBUTABLE = "licence"  # an asset whose terms forbid it travelling (XC-025, XC-085)
    NOT_FOUND = "missing"          # referenced and not on this disk
    NOT_REQUESTED = "not-requested"  # input data the user chose to leave out


_OMISSION_WORD = {
    Omission.OUTSIDE: "ワークスペースの外にあるリンク先",
    Omission.NOT_REDISTRIBUTABLE: "ライセンス上再配布できない素材",
    Omission.NOT_FOUND: "参照されていますが見つかりません",
    Omission.NOT_REQUESTED: "入力データ（同梱しない選択）",
}


@dataclass(frozen=True, slots=True)
class Omitted:
    """One thing the pack could not or would not take, named rather than counted."""

    name: str
    why: Omission

    def describe(self) -> str:
        return f"{self.name}（{_OMISSION_WORD[self.why]}）"


@dataclass(frozen=True, slots=True)
class Plan:
    """What a pack would contain and cost, before anything is written."""

    document_bytes: int
    included: tuple[tuple[str, int], ...] = dataclass_field(default_factory=tuple)
    omitted: tuple[Omitted, ...] = dataclass_field(default_factory=tuple)
    with_data: bool = False

    @property
    def total_bytes(self) -> int:
        return self.document_bytes + sum(size for _, size in self.included)

    def describe(self) -> str:
        """The line a user reads **before** deciding, which is the only time it is useful."""
        size = _human(self.total_bytes)
        line = f"パックの大きさは約 {size}（文書 + {len(self.included)} 件）です"
        if not self.with_data:
            line += "。入力データは含みません"
        if self.omitted:
            names = "、".join(item.describe() for item in self.omitted)
            line += f"。持って行けないもの {len(self.omitted)} 件：{names}"
        return line


def _human(size: int) -> str:
    for unit, step in (("GB", 1 << 30), ("MB", 1 << 20), ("kB", 1 << 10)):
        if size >= step:
            return f"{size / step:.1f} {unit}"
    return f"{size} B"


def plan(
    document: dict[str, Any],
    *,
    root: Path,
    document_bytes: int,
    with_data: bool,
    assets: dict[str, Path] | None = None,
    redistributable: Iterable[str] = (),
) -> Plan:
    """What packing this workspace would take, and what it would leave behind.

    Reads sizes and nothing else. The decision about the user's disk and their licences is made here,
    before a single byte is copied.
    """
    assets = assets or {}
    allowed = set(redistributable)
    included: list[tuple[str, int]] = []
    omitted: list[Omitted] = []

    for name, path in sorted(assets.items()):
        if name not in allowed:
            # Named rather than dropped. An asset whose terms forbid redistribution is the recipient's
            # problem if it travels, and their missing font if it does not - and they can only act on
            # the second if they are told which one.
            omitted.append(Omitted(name, Omission.NOT_REDISTRIBUTABLE))
        elif not path.exists():
            omitted.append(Omitted(name, Omission.NOT_FOUND))
        else:
            included.append((name, path.stat().st_size))

    for case, _ in walk(document.get("cases", [])):
        for source in case.get("sources", []):
            relative = str(source.get("pathRelative", ""))
            if not with_data:
                omitted.append(Omitted(relative, Omission.NOT_REQUESTED))
                continue
            location = root / relative
            if ".." in Path(relative).parts or Path(relative).is_absolute():
                # A workspace may point at a folder it does not contain. Following it would put files
                # from outside the project into a pack the user believes holds their project.
                omitted.append(Omitted(relative, Omission.OUTSIDE))
            elif not location.exists():
                omitted.append(Omitted(relative, Omission.NOT_FOUND))
            else:
                included.append((relative, location.stat().st_size))

    return Plan(
        document_bytes=document_bytes,
        included=tuple(included),
        omitted=tuple(omitted),
        with_data=with_data,
    )


def opened_without_data(document: dict[str, Any]) -> tuple[str, ...]:
    """Put every case that has inputs into unresolved, and return which (AC-050).

    A pack without data must not open into cases that look fine until somebody clicks one. XC-136
    already has the state for exactly this, which is the whole reason it is a state rather than a flag
    on a loader.

    A case with no inputs is left alone: it has nothing missing, and marking it unresolved would be the
    product reporting a problem it invented.
    """
    moved: list[str] = []
    for case, _ in walk(document.get("cases", [])):
        if not case.get("sources"):
            continue
        case["state"] = CaseState.UNRESOLVED.value
        case["stateReason"] = (
            "データを含まないパックから開きました。入力ファイルを同じ場所に置くと解決します"
        )
        moved.append(str(case.get("id", "")))
    return tuple(moved)
