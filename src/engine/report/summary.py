"""The summary a report carries when no language model is configured, and always.

AC-013: with no model, a report is produced **with the mechanical summary only** and requires no
network. So the mechanical summary is not the degraded version of the generated one - it is the part
that is always there, and the generated commentary is what may be added to it.

The whole of it is counts, extremes with their labels and units, and the things a reader must know to
act on the numbers. There are no adjectives in it, and that is deliberate rather than terse:
`14_reporting_standards.md` lists the language an engineering audience rejects a report for, and it is
exactly the language a summariser reaches for - "good agreement", "significant", "roughly", "optimal".
A sentence produced here cannot contain them because nothing here composes one; it states quantities and
stops.

**A statement about a value this report does not carry is not made** (AC-012). That is trivial here
because the summary is derived from the document's own rows and can say nothing else - which is why it
is built from the document rather than from the dataset.

**It is marked as mechanical.** A reader who cannot tell which sentences a model wrote has to treat all
of them as if a model did (AC-011), and the marking is what keeps the generated commentary from
borrowing the mechanical summary's credibility.

Specification: report/AC-011 to AC-013, report/TASK-014, 14_reporting_standards.md, E-071.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum

from domain_core.reported_value import UNDECLARED_MARKER, Caveat
from engine.report.document import Document, ValueRow, missing, partial, undeclared


class Authorship(str, Enum):
    """Who wrote a passage. CT-006's two, and the marking AC-011 requires."""

    MECHANICAL = "mechanical"   # composed from the values by this product, with no model
    GENERATED = "generated"     # written by a language model, marked wherever it appears


AUTHORSHIP_WORD = {
    Authorship.MECHANICAL: "機械的な要約（言語モデルは使っていません）",
    Authorship.GENERATED: "生成された文章",
}


@dataclass(frozen=True, slots=True)
class Summary:
    """What a report says about itself without anybody writing prose.

    `lines` are statements of quantity. `concerns` are the things a reader must know to act on the
    numbers - missing values, undeclared units, partial coverage - kept apart from the statements
    because burying them in a list of figures is how they get skimmed past.
    """

    authorship: Authorship
    lines: tuple[str, ...] = dataclass_field(default_factory=tuple)
    concerns: tuple[str, ...] = dataclass_field(default_factory=tuple)
    derived_from: tuple[str, ...] = dataclass_field(default_factory=tuple)

    def as_text(self) -> str:
        parts = [f"## 要約（{AUTHORSHIP_WORD[self.authorship]}）", *self.lines]
        if self.concerns:
            parts.append("読む前に知っておくこと：")
            parts += [f"  - {one}" for one in self.concerns]
        return "\n".join(parts)


def _stated(row: ValueRow) -> str:
    unit = row.value.unit if row.value.unit is not None else UNDECLARED_MARKER
    return f"{row.label} {row.value.formatted()} {unit}".strip()


def summarise(document: Document) -> Summary:
    """The mechanical summary of a document (AC-013).

    Built from the document's own rows, so a statement about a value the report does not carry is not
    something this can produce (AC-012) rather than something it is asked not to do.

    The extremes are named **with their labels**, because "the maximum is 240 MPa" is a number without a
    subject and the reader has to go looking for which quantity it belonged to.
    """
    rows = document.values()
    present = [row for row in rows if row.value.value is not None]

    lines = [f"この文書は {len(rows)} 個の値を含みます。"]
    if present:
        largest = max(present, key=lambda row: float(row.value.value or 0.0))
        smallest = min(present, key=lambda row: float(row.value.value or 0.0))
        if largest is not smallest:
            lines.append(f"最大は {_stated(largest)}、最小は {_stated(smallest)} です。")
        else:
            lines.append(f"値は {_stated(largest)} の 1 件です。")
    lines.append(f"元ファイル {len(document.provenance.sources)} 件から作成しています。")

    concerns: list[str] = []
    absent = missing(document)
    if absent:
        concerns.append(f"値のない項目が {len(absent)} 件あります：{'、'.join(absent)}")
    without_units = undeclared(document)
    if without_units:
        concerns.append(
            f"単位が宣言されていない値が {len(without_units)} 件あります："
            f"{'、'.join(without_units)}"
        )
    incomplete = partial(document)
    if incomplete:
        concerns.append(
            f"データセットの一部から計算した値が {len(incomplete)} 件あります："
            f"{'、'.join(incomplete)}"
        )
    reduced = [block.reduced for block in document.blocks if block.reduced]
    if reduced:
        concerns.append(
            f"簡略化して表示している図が {len(reduced)} 件あります（数値は完全なデータで計算しています）"
        )
    for row in rows:
        if Caveat.FROM_REDUCED_GEOMETRY in row.value.caveats:
            concerns.append(f"{row.label} は縮退した表示形状から測った値です")

    return Summary(
        Authorship.MECHANICAL,
        tuple(lines),
        tuple(concerns),
        tuple(row.label for row in rows),
    )


def needs_a_model(summary: Summary) -> bool:
    """Whether producing this summary required a language model. Always False for a mechanical one.

    Exists to be asserted against: AC-013 is a statement about what a report can be produced without,
    and a function that answers it is cheaper to check than a promise in a docstring.
    """
    return summary.authorship is Authorship.GENERATED
