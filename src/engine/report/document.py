"""The document a report becomes: every number as text, and the block that says where they came from.

Two measurements shaped this, and both are recorded against REQ-001 rather than being general good
practice. The free export path produced 34.4 MB in 21.4 seconds for a 1.13 million point surface, and
**the text annotation and point label added to that scene were absent from the exported file with no
warning** while the scalar bar survived.

So: **every number appears as text** (AC-002). A document whose values live only inside the 3D content
is a document that stops being readable the moment the viewer fails, the browser is old, or the reader
prints it - and the measurement above is what an export silently dropping content looks like.

**The trust content is mandatory and refuses to be absent** (AC-007). A report states the workspace, the
cases, the source files with their modification times, the declared units and the product version. None
of it is knowable here, so all of it is handed in - and a document that cannot produce one of them
**blocks the export and names what is missing**, rather than writing a document with a gap where its
provenance should be.

**A field with no declared unit carries the marker, never a guess** (AC-008, XC-003). That is already
refused at construction by `ReportedValue`, and this module's job is not to undo it: the marker travels
into the text.

Nothing here writes HTML. The document model is what the writers agree on, so the same values reach the
interactive document and the office formats (AC-005) without either of them being the definition of what
a report contains.

Specification: CT-006, report/AC-002, AC-004, AC-007, AC-008, INV-013, INV-027, XC-003.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Any, Iterable, Sequence

from domain_core.recorded_time import RecordedTime
from domain_core.reported_value import CAVEAT_TEXT, UNDECLARED_MARKER, Caveat, ReportedValue

#: Anything matching this in a produced document would need the network to render (AC-001).
EXTERNAL = re.compile(r"https?://|//[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/")


class BlockKind(str, Enum):
    """CT-006's five. Closed: a sixth is a contract change, not a new string."""

    VIEW = "view"
    GRAPH = "graph"
    VALUE_TABLE = "valueTable"
    TEXT = "text"
    PAGE_BREAK = "pageBreak"


class ReportError(Exception):
    """Raised where a document cannot be produced honestly - which blocks the export (AC-007)."""


@dataclass(frozen=True, slots=True)
class SourceFile:
    """One file a report drew on, with when it was last changed.

    The modification time is what lets a reader tell a delivered document from one whose inputs have
    moved since (INV-027). Without it the provenance block says which files, which is the easier half.
    """

    path: str
    modified: RecordedTime

    def describe(self) -> str:
        return f"{self.path}（更新 {self.modified.utc}）"


@dataclass(frozen=True, slots=True)
class Provenance:
    """The trust content of a report. Mandatory, and refused rather than partly filled (AC-007)."""

    workspace_id: str
    case_ids: tuple[str, ...]
    sources: tuple[SourceFile, ...]
    declared_units: dict[str, str]
    product_version: str
    produced: RecordedTime | None = None

    def __post_init__(self) -> None:
        missing = [
            name for name, value in (
                ("ワークスペース", self.workspace_id),
                ("ケース", self.case_ids),
                ("製品の版", self.product_version),
            ) if not value
        ]
        if missing:
            raise ReportError(
                f"来歴に {'、'.join(missing)} がありません。書き出しは行いません — "
                "来歴の欠けたところに空白のある文書は、誰かが送ってしまう文書です（AC-007）"
            )

    def as_text(self) -> str:
        lines = [
            "## 来歴",
            f"ワークスペース：{self.workspace_id}",
            f"ケース：{'、'.join(self.case_ids)}",
            f"製品の版：{self.product_version}",
        ]
        if self.produced:
            lines.append(f"作成：{self.produced.utc}")
        if self.sources:
            lines.append("元ファイル：")
            lines += [f"  - {one.describe()}" for one in self.sources]
        else:
            # Said rather than omitted: an empty list and an absent list read the same on a page, and
            # only one of them means "this report drew on no file".
            lines.append("元ファイル：ありません（このレポートはファイルを読んでいません）")
        if self.declared_units:
            lines.append("宣言された単位：")
            lines += [
                f"  - {name}：{unit}" for name, unit in sorted(self.declared_units.items())
            ]
        else:
            lines.append(f"宣言された単位：ありません（{UNDECLARED_MARKER}）")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class ValueRow:
    """One number as it appears in the document's text (AC-002, INV-013).

    `coverage` is what this value was computed over, and it is **required** where the value carries
    `PARTIAL_DATASET` (AC-004). A caveat saying "part of the dataset was missing" without saying which
    part is a warning nobody can act on: the reader cannot tell whether one part of fifteen was absent
    or twelve were.
    """

    label: str
    value: ReportedValue
    coverage: str | None = None

    def __post_init__(self) -> None:
        if Caveat.PARTIAL_DATASET in self.value.caveats and not self.coverage:
            raise ReportError(
                f"'{self.label}' は部分的なデータセットから計算された値ですが、"
                "その対象範囲が書かれていません。範囲のない「一部が欠けています」は、"
                "読み手が対処できない警告です（AC-004）"
            )

    def unit_text(self) -> str:
        if self.value.unit is not None:
            return self.value.unit
        return UNDECLARED_MARKER

    def as_text(self) -> str:
        if self.value.value is None:
            because = self.value.missing_because or "理由が記録されていません"
            return f"{self.label}：値なし（{because}）"
        shown = self.value.formatted()
        line = f"{self.label}：{shown} {self.unit_text()}".rstrip()
        line += f"（{self.value.provenance.value}）"
        if self.value.location:
            line += f"・位置 {self.value.location}"
        for caveat in sorted(self.value.caveats, key=lambda one: one.value):
            if caveat is Caveat.UNDECLARED_UNIT:
                continue  # already said by the unit column; saying it twice reads as two problems
            line += f"・{CAVEAT_TEXT[caveat]}"
        if self.coverage:
            line += f"（対象範囲：{self.coverage}）"
        return line


@dataclass(frozen=True, slots=True)
class Block:
    """One block of the document, and the text that stands for it.

    A view block and a graph block each carry their values as rows: the picture is the convenience and
    the text is the document. That order is the whole of AC-002.
    """

    kind: BlockKind
    title: str = ""
    rows: tuple[ValueRow, ...] = dataclass_field(default_factory=tuple)
    text: str = ""
    reduced: str | None = None
    coverage: str | None = None

    def as_text(self) -> str:
        if self.kind is BlockKind.PAGE_BREAK:
            return "---"
        lines: list[str] = []
        if self.title:
            lines.append(f"## {self.title}")
        if self.text:
            lines.append(self.text)
        if self.reduced:
            # AC-003: a reduced representation says so in the document, not only on screen.
            lines.append(f"※ 表示は簡略化されています：{self.reduced}。数値は完全なデータで計算しています")
        if self.coverage:
            # AC-004: a number computed over part of a dataset states what it covered.
            lines.append(f"※ この値の対象範囲：{self.coverage}")
        lines += [row.as_text() for row in self.rows]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class Document:
    """A report as a structure, before any format writes it.

    Held apart from the writers so the same values reach the interactive document and the office
    formats (AC-005) without either being the definition of what a report contains.
    """

    title: str
    blocks: tuple[Block, ...]
    provenance: Provenance
    language: str = "ja"

    def as_text(self) -> str:
        return "\n\n".join(
            [f"# {self.title}", *(block.as_text() for block in self.blocks), self.provenance.as_text()]
        )

    def values(self) -> tuple[ValueRow, ...]:
        return tuple(row for block in self.blocks for row in block.rows)


def build(
    definition: dict[str, Any],
    *,
    rows_for: dict[str, Sequence[ValueRow]] | None = None,
    provenance: Provenance,
) -> Document:
    """Turn a CT-006 definition into a document (AC-002).

    `rows_for` maps a block's identifier to the values it shows. Supplied rather than computed here:
    MOD-004 produces numbers and this module arranges them, and a report layer that computed would be a
    second place where a value comes from (INV-001).
    """
    supplied = rows_for or {}
    blocks: list[Block] = []
    for index, stated in enumerate(definition.get("blocks", []) or []):
        kind = _kind_of(stated)
        key = str(stated.get("viewId") or stated.get("graphId") or index)
        blocks.append(
            Block(
                kind,
                title=str(stated.get("title", "")),
                rows=tuple(supplied.get(key, ())),
                text=str(stated.get("text", "")),
                reduced=stated.get("reduced"),
                coverage=stated.get("coverage"),
            )
        )
    return Document(
        title=str(definition.get("name", "")),
        blocks=tuple(blocks),
        provenance=provenance,
        language=str(definition.get("locale", "ja")),
    )


def _kind_of(block: dict[str, Any]) -> BlockKind:
    stated = str(block.get("kind", ""))
    try:
        return BlockKind(stated)
    except ValueError:
        raise ReportError(
            f"ブロックの種類 '{stated}' は CT-006 の一覧にありません"
            f"（{[k.value for k in BlockKind]}）"
        ) from None


def external_references(document: Document) -> tuple[str, ...]:
    """Anything in the text that would need the network to render (AC-001, INV-007).

    Checked on the document rather than trusted of the writers: a report opens on a machine that may
    have no network at all, and one that quietly renders differently there is the failure this is for.
    """
    return tuple(sorted(set(EXTERNAL.findall(document.as_text()))))


def undeclared(document: Document) -> tuple[str, ...]:
    """Which values appear with the undeclared marker (AC-008).

    Answerable from the document, so "does this report contain a value with no unit" needs no reading.
    """
    return tuple(
        row.label for row in document.values() if row.value.unit is None
    )


def partial(document: Document) -> tuple[str, ...]:
    """Which values were computed over part of the data, with what they covered (AC-004)."""
    return tuple(
        f"{row.label}：{row.coverage}"
        for row in document.values()
        if Caveat.PARTIAL_DATASET in row.value.caveats
    )


def missing(document: Document) -> tuple[str, ...]:
    """Which values are absent, with their reasons - never rendered as a blank cell (XC-001)."""
    return tuple(
        f"{row.label}：{row.value.missing_because}"
        for row in document.values()
        if row.value.value is None
    )


def blocks_needing(document: Document, kinds: Iterable[BlockKind]) -> tuple[Block, ...]:
    wanted = set(kinds)
    return tuple(block for block in document.blocks if block.kind in wanted)
