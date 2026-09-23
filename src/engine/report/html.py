"""The one file a recipient opens with nothing installed.

This is the product's claim, and until now `src/` contained no line that wrote it: `document.py` builds
the model and says of itself that nothing there writes HTML. This module is the writer.

**It says what it cannot carry before it writes, rather than omitting it silently** (AC-014). The reason
is measured rather than principled: the free export path produced 34.4 MB for a 1.13 million point
surface and **the text annotation and the point label were absent from the file with no warning** while
the scalar bar survived (spike/results.json). A writer that drops what it cannot represent produces a
document that looks complete and is not, and the reader has no way to know. So `unrepresentable()` is
answerable before anything is written, `write()` refuses until that list has been accepted, and the
statement then travels **into the document** so the recipient reads it too - refusing and then writing
a file that keeps the omission to itself would only move the silence one step along.

**Nothing in the file reaches the network** (AC-001, INV-007). Not asserted of the writer but checked of
the output: the produced text is searched for an external reference and the file is refused if one is
there. A document that renders differently on a machine with no network is the failure this exists to
prevent, and a machine with no network is the ordinary case for a customer opening a deliverable.

**Every number is text** (AC-002). The rows carry the value, its unit or the undeclared marker, its
provenance and its caveats, so the document is readable with the 3D content broken, old, or printed.

**A missing value is a stated absence** (XC-001). Never a blank cell: a blank reads as zero to some
readers and as "not applicable" to others, and it is neither.

**What this build cannot do yet is named, not implied.** `Capability` holds what the writer can put in
the file, and a view block is named by **the form it asked for**: a still is written when a picture was
drawn for it, while the rotatable @View of AC-001 still needs the vtk.js bundle and a video needs a
camera path and a codec. Neither is quietly given a still instead - a reader who asked to rotate the
model and got a photograph was answered with something else under the same name. The embedded font
subset of AC-015 is absent for the same kind of reason, needing a font whose licence permits it. Until
each arrives, a document using it is refused unless the caller accepts a list that names it.

**A still carries its legend as text, not in the picture.** Measured: the toolkit's embedded faces
draw a Japanese title as nothing at all - no glyph, no box, no warning (E-192) - and 単位未宣言 is the
word a picture of an undeclared field must carry. So the image holds the colour ramp and its tick
digits, and the field, the unit and the range are typeset here, in the document's own font.

**A deliverable has a weight limit** (LIM-006). An embedded picture makes that a real question rather
than a theoretical one, so the size is measured before the file exists and an oversized document is
refused with the figure named rather than written and bounced by a mail system.

**The font is required of every report, not only of reports containing Japanese.** Found by the check
rather than assumed: a document whose content is entirely Latin still fails, because this product's own
labels are Japanese - the provenance block says `ワークスペース`, `元ファイル`, `宣言された単位`. So a
build with no embedded font produces empty boxes on any machine without a Japanese font installed, for
every document it writes. Which font that is remains open (OPEN-032); that it is not optional is settled.

Specification: CT-006, report/AC-001, AC-002, AC-003, AC-004, AC-007, AC-008, AC-014, AC-016, AC-031,
INV-007, INV-013, XC-001, XC-003.
"""

from __future__ import annotations

import base64
import os
import html as html_escape
import unicodedata
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path

from domain_core.precision import format_value
from domain_core.reported_value import Caveat, caveat_text, UNDECLARED_MARKER
from engine.report.document import (
    EXTERNAL,
    Block,
    BlockKind,
    Document,
    Figure,
    ReportError,
    ValueRow,
    ViewForm,
)
from engine.report_limits import MAX_REPORT_BYTES

#: Block kinds this writer can put into a static document. `VIEW` is here from 2026-09-18 and is the
#: **conditional** one: a view block is writable when it asked for a still and a picture was drawn for
#: it, and not otherwise. AC-001's rotatable view still needs the vtk.js bundle of 09_technology.md and
#: a video still needs a camera path and a codec; neither is written as a still in its place, because a
#: reader who asked to rotate the model and got a photograph was answered with something else under the
#: same name (XC-254). Which of the three a block asked for is `Block.form` (CT-006 2.1.0).
STATIC_KINDS = frozenset({
    BlockKind.VALUE_TABLE, BlockKind.TEXT, BlockKind.PAGE_BREAK, BlockKind.GRAPH, BlockKind.VIEW,
})

#: What a view block that cannot be written says, by the form it asked for. Written out per form
#: because "this view cannot be included" is a message nobody can act on: one of these is fixed by
#: rendering the view first, one by a build that bundles the viewer, and one by a build that encodes
#: video.
VIEW_FORM_REASONS: dict[ViewForm | None, str] = {
    ViewForm.INTERACTIVE: "回転できる 3D 表示には vtk.js の同梱が要ります（AC-001）",
    ViewForm.VIDEO: "動画にはカメラパスと動画コーデックが要ります（この版にはありません）",
    ViewForm.STILL: "静止画が描かれていません：先にビューを描画してから書き出してください",
    None: "どの形（still / video / interactive）か書かれていません。"
    "書ける形を選んで入れることはしません（CT-006 2.1.0）",
}

#: Characters every font has. Anything outside it needs either an embedded font or a statement that the
#: document depends on what the reader's machine has (AC-015, AC-016).
BASIC_LATIN = frozenset(chr(code) for code in range(0x20, 0x7F)) | frozenset("\n\r\t")


#: The browsers the gate opened and printed this document form in (`tests/test_exported_document_opens.py`,
#: `tests/test_exported_document_prints.py`), each with the oldest major version measured on any
#: machine that ran the gate (XC-309, E-228). Named in the document's own footer, so a reader knows
#: what was verified; a browser not here was not measured and is not claimed. The gate fails where
#: a browser it measured is older than the version claimed here.
VERIFIED_BROWSERS: tuple[tuple[str, int], ...] = (("Microsoft Edge", 152), ("Google Chrome", 152), ("Mozilla Firefox", 155))


@dataclass(frozen=True, slots=True)
class EmbeddedFont:
    """A font subset carried inside the document (AC-015).

    `covers` is what it can actually render, not what it is named after. A font declared to cover
    Japanese and missing one character produces an empty box, and an empty box is the outcome AC-016
    exists to prevent - so coverage is stated as characters and checked against the document.
    """

    name: str
    licence: str
    data: bytes
    covers: frozenset[str]

    def __post_init__(self) -> None:
        if not self.licence:
            raise ReportError(
                f"フォント '{self.name}' の使用条件が記録されていません。"
                "再配布の可否が分からないものは文書に埋め込みません"
            )
        if not self.data:
            raise ReportError(f"フォント '{self.name}' に中身がありません")


@dataclass(frozen=True, slots=True)
class Capability:
    """What this build can put into an exported document.

    Held as data rather than read from what happens to import, so a document can be checked against a
    build other than the one running - and so the answer to "why is this refused" is a value somebody
    can print.
    """

    kinds: frozenset[BlockKind] = STATIC_KINDS
    font: EmbeddedFont | None = None
    #: Colour maps this build knows to be perceptually uniform (AC-038, XC-111). Empty means it knows of
    #: none, which is reported as not knowing rather than as the map being fine.
    uniform_colour_maps: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class Unrepresentable:
    """One thing this build cannot put in the file, and where it is."""

    what: str
    where: str

    def describe(self) -> str:
        return f"{self.what}（{self.where}）"


def unrepresentable(
    document: Document, capability: Capability | None = None
) -> tuple[Unrepresentable, ...]:
    """Everything this build cannot carry, named, before anything is written (AC-014, AC-016).

    Answerable without writing, because AC-014's requirement is that the omission is stated **before**
    the file exists. A list produced alongside the file would be a list somebody found afterwards.
    """
    build = capability or Capability()
    found: list[Unrepresentable] = []

    for index, block in enumerate(document.blocks):
        where = block.title or f"{index + 1} 番目のブロック"
        if block.kind not in build.kinds:
            found.append(Unrepresentable(f"{block.kind.value} ブロック", where))
            continue
        if block.kind is BlockKind.VIEW and block.figure is None:
            # The one conditional kind: writable as a still with a picture, and named by the form it
            # asked for otherwise, so the reader is told which thing is missing.
            found.append(
                Unrepresentable(f"view ブロック：{VIEW_FORM_REASONS[block.form]}", where)
            )

    found += _uncovered_characters(document, build.font)
    return tuple(found)


def _uncovered_characters(document: Document, font: EmbeddedFont | None) -> list[Unrepresentable]:
    """Which characters cannot be guaranteed, and in which element (AC-016).

    Named by character and by element rather than counted: "12 characters may not render" is a warning
    nobody can act on, and the two questions a reader has are which ones and where.
    """
    found: list[Unrepresentable] = []
    for where, text in _elements(document):
        outside = sorted({one for one in text if one not in BASIC_LATIN})
        if not outside:
            continue
        if font is None:
            found.append(
                Unrepresentable(
                    "基本ラテン文字の外の文字："
                    + _name_characters(outside)
                    + "。埋め込みフォントがないので、読み手の機械にある書体次第になります（AC-015）",
                    where,
                )
            )
            continue
        missing = [one for one in outside if one not in font.covers]
        if missing:
            found.append(
                Unrepresentable(
                    f"埋め込みフォント '{font.name}' が持たない文字：" + _name_characters(missing),
                    where,
                )
            )
    return found


def _name_characters(characters: list[str]) -> str:
    """The characters themselves, with their Unicode names - a code point alone is not readable."""
    shown = characters[:8]
    named = "、".join(
        f"{one} (U+{ord(one):04X} {unicodedata.name(one, '名前なし')})" for one in shown
    )
    if len(characters) > len(shown):
        named += f" ほか {len(characters) - len(shown)} 字"
    return named


def _elements(document: Document) -> list[tuple[str, str]]:
    """Every piece of text in the document, with the element it belongs to."""
    found = [("表題", document.title)]
    for index, block in enumerate(document.blocks):
        where = block.title or f"{index + 1} 番目のブロック"
        if block.title:
            found.append((f"{where}・見出し", block.title))
        if block.text:
            found.append((f"{where}・本文", block.text))
        if block.figure is not None:
            # The legend's words are in the document rather than in the picture (E-192), so they are
            # the document's to render - and 単位未宣言 is exactly the string a build with no font
            # would turn into empty boxes on the reader's machine. The **same** strings the writer
            # emits, not a second phrasing of them: a coverage check against text the file does not
            # contain reports characters nobody will see and misses the ones they will.
            found.append((f"{where}・凡例", "".join(_legend_parts(block.figure))))
        for row in block.rows:
            found.append((f"{where}・{row.label}", row.label + (row.value.unit or "")))
    found.append(("来歴", document.provenance.as_text()))
    return found


@dataclass(frozen=True, slots=True)
class Export:
    """What one export produced, and what it had to say about itself."""

    path: Path
    bytes: int
    stated: tuple[str, ...] = dataclass_field(default_factory=tuple)

    def describe(self) -> str:
        line = f"{self.path.name}（{self.bytes} バイト）"
        if self.stated:
            line += "。文書に次を明記しました：" + "、".join(self.stated)
        return line


def write(
    document: Document,
    path: Path | str,
    *,
    capability: Capability | None = None,
    accepted: bool = False,
) -> Export:
    """Write the document as one self-contained HTML file (AC-001).

    Refuses while anything is unrepresentable and `accepted` is false, so the caller has seen the list
    before the file exists (AC-014). Once accepted, the same list is written **into** the document:
    refusing and then producing a file that kept the omission to itself would move the silence one step
    along rather than ending it.
    """
    build = capability or Capability()
    cannot = unrepresentable(document, build)
    if cannot and not accepted:
        raise ReportError(
            "この文書には、この版が表現できない要素があります。書き出しは行いません：\n"
            + "\n".join(f"  - {one.describe()}" for one in cannot)
            + "\n黙って省くより、書く前に申し上げます（AC-014）"
        )

    text = render(document, build, stated=cannot)
    outside = sorted(set(EXTERNAL.findall(text)))
    if outside:
        # Checked of the output rather than trusted of the writer. A deliverable is opened on a machine
        # that may have no network at all, and one that renders differently there is the failure.
        raise ReportError(
            f"書き出そうとした文書が外部を参照しています：{outside}。"
            "ネットワークのない機械で開かれる前提の成果物なので、書き出しません（AC-001、INV-007）"
        )

    destination = Path(path)
    # Written as the bytes that were measured, never through a text stream: on Windows `write_text`
    # turns every "\n" into "\r\n", so the file was 25 bytes larger than the size this returned and
    # differed from the same document written elsewhere. A deliverable's stated size is its size
    # (LIM-006), and the same document is the same bytes on every platform (XC-046).
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        # LIM-006: a deliverable an engineer emails has to stay under what a mail system accepts.
        # Refused **before the file exists** rather than written oversized, and the caller is told by
        # how much, because what it does about it - a smaller picture, fewer views - is its choice.
        raise ReportError(
            f"この文書は {len(encoded):,} バイトで、上限 {MAX_REPORT_BYTES:,} バイトを超えます"
            f"（LIM-006）。書き出しは行いません — 図を小さくするか、図の数を減らしてください。"
            "黙って送れない大きさのファイルを作るより、ここで申し上げます"
        )
    # Whole or absent: written beside the target and moved into place, so a process that dies
    # mid-write leaves a `.writing` file and never a deliverable that opens and is short (#313,
    # XC-262). A `.writing` left by an earlier death is overwritten, not kept.
    temporary = destination.with_name(destination.name + ".writing")
    with temporary.open("wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return Export(
        destination,
        len(encoded),
        tuple(one.describe() for one in cannot),
    )


def render(
    document: Document,
    capability: Capability | None = None,
    *,
    stated: tuple[Unrepresentable, ...] = (),
) -> str:
    """The document as HTML text, without writing it anywhere.

    Separate from `write` so what would be written can be examined - by a test, by the caller, and by
    the external-reference check above, which has to read the output rather than trust its author.
    """
    build = capability or Capability()
    parts = [
        "<!doctype html>",
        f'<html lang="{_attribute(document.language)}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_text(document.title)}</title>",
        f"<style>{_stylesheet(build.font)}</style>",
        "</head>",
        "<body>",
        f"<h1>{_text(document.title)}</h1>",
    ]
    parts += [_block(block, index) for index, block in enumerate(document.blocks)]
    parts.append(_limitations(document, stated))
    parts.append(_provenance(document))
    parts.append(_verified())
    parts += ["</body>", "</html>", ""]
    return "\n".join(parts)


def _block(block: Block, index: int) -> str:
    if block.kind is BlockKind.PAGE_BREAK:
        return '<hr class="page-break">'
    parts = [f'<section class="block {_attribute(block.kind.value)}">']
    if block.title:
        parts.append(f"<h2>{_text(block.title)}</h2>")
    if block.text:
        parts.append(f"<p>{_text(block.text)}</p>")
    if block.figure is not None:
        parts.append(_figure(block.figure))
    if block.reduced:
        # AC-003: the reduction is in the document, not only on the screen it happened on.
        parts.append(
            f'<p class="note">表示は簡略化されています：{_text(block.reduced)}。'
            "数値は完全なデータで計算しています</p>"
        )
    if block.coverage:
        parts.append(f'<p class="note">この値の対象範囲：{_text(block.coverage)}</p>')
    if block.rows:
        parts.append(_table(block.rows))
    parts.append("</section>")
    return "\n".join(parts)


#: What a still says about itself, beyond its legend. Held here so the coverage check and the writer
#: read from one list: a note the file carries and the check does not know about is a note that
#: becomes empty boxes on a machine without the font.
STILL_NOTE = "この図は静止画です。回転はできません（report/AC-001）"
NOT_UNIFORM_NOTE = (
    "このカラーマップは知覚均等ではありません："
    "色の変化の速さが値の変化の速さと一致しないため、勾配の見え方は当てになりません（XC-111）"
)


def _legend_parts(figure: Figure) -> tuple[str, ...]:
    """Every string the figure puts in the document, in the order it puts them."""
    legend = figure.legend
    parts = [
        figure.description or f"{legend.field_name} の表示",
        legend.field_name,
        legend.unit_text,
        format_value(legend.minimum, legend.digits),
        format_value(legend.maximum, legend.digits),
        legend.colour_map,
    ]
    if not legend.uniform:
        parts.append(NOT_UNIFORM_NOTE)
    parts.append(STILL_NOTE)
    return tuple(parts)


def _figure(figure: Figure) -> str:
    """The picture, embedded, with its legend as text beside it (E-192) and its form stated.

    The bytes travel as a `data:` URI because the file is self-contained: a picture fetched from
    somewhere is a picture the recipient may not get (AC-001, INV-007). The legend is typeset here
    rather than drawn into the image, and the document says the view is a still - a reader who cannot
    turn it should be told it does not turn, not left to discover it.
    """
    encoded = base64.b64encode(figure.png).decode("ascii")
    legend = figure.legend
    low = format_value(legend.minimum, legend.digits)
    high = format_value(legend.maximum, legend.digits)
    parts = [
        '<figure class="view">',
        f'<img src="data:image/png;base64,{encoded}" width="{figure.width}" height="{figure.height}"'
        f' alt="{_text(figure.description or legend.field_name + " の表示")}">',
        '<figcaption>',
        f'<span class="legend-field">{_text(legend.field_name)}</span>'
        f'<span class="legend-unit">{_text(legend.unit_text)}</span>'
        f'<span class="legend-range">{_text(low)} – {_text(high)}</span>'
        f'<span class="legend-map">{_text(legend.colour_map)}</span>',
    ]
    if not legend.uniform:
        parts.append(f'<p class="note">{_text(NOT_UNIFORM_NOTE)}</p>')
    parts.append(f'<p class="note">{_text(STILL_NOTE)}</p>')
    parts += ["</figcaption>", "</figure>"]
    return "\n".join(parts)


def _table(rows: tuple[ValueRow, ...]) -> str:
    """Every number as text (AC-002), with the columns a reader needs to judge it."""
    parts = [
        '<table class="values">',
        "<thead><tr><th>項目</th><th>値</th><th>単位</th><th>来歴</th><th>注記</th></tr></thead>",
        "<tbody>",
    ]
    for row in rows:
        parts.append(f"<tr>{_row(row)}</tr>")
    parts += ["</tbody>", "</table>"]
    return "\n".join(parts)


def _row(row: ValueRow) -> str:
    if row.value.value is None:
        # XC-001: never a blank cell. A blank reads as zero to some readers and as "not applicable" to
        # others, and it is neither.
        because = row.value.missing_because or "理由が記録されていません"
        return (
            f"<th scope=\"row\">{_text(row.label)}</th>"
            f'<td class="missing" colspan="4">値なし（{_text(because)}）</td>'
        )
    undeclared = row.value.unit is None
    unit = f'<td class="undeclared">{_text(UNDECLARED_MARKER)}</td>' if undeclared else (
        f"<td>{_text(row.value.unit or '')}</td>"
    )
    notes = [
        caveat_text(caveat, row.value)
        for caveat in sorted(row.value.caveats, key=lambda one: one.value)
        # Already said by the unit column; saying it twice reads as two problems.
        if caveat is not Caveat.UNDECLARED_UNIT
    ]
    if row.coverage:
        notes.append(f"対象範囲：{row.coverage}")
    if row.value.formula:
        notes.append(f"式：{row.value.formula}")
    if row.value.location:
        notes.append(f"位置：{row.value.location}")
    return (
        f'<th scope="row">{_text(row.label)}</th>'
        f'<td class="value">{_text(row.value.formatted())}</td>'
        f"{unit}"
        f"<td>{_text(row.value.provenance.value)}</td>"
        f"<td>{_text('・'.join(notes))}</td>"
    )


def _limitations(document: Document, stated: tuple[Unrepresentable, ...]) -> str:
    """The limitations section, present even where it has one sentence to say (AC-031).

    Mandatory because its absence is the reading a recipient takes from it: a report with no limitations
    section is one that claims none, and no result of a discretised solve has none.
    """
    from engine.report.document import missing, partial, undeclared

    lines: list[str] = []
    for one in stated:
        lines.append(f"この版で表現できなかったもの：{one.describe()}")
    lines += [f"単位が宣言されていない値：{label}" for label in undeclared(document)]
    lines += [f"データの一部から計算された値：{one}" for one in partial(document)]
    lines += [f"値のない項目：{one}" for one in missing(document)]
    body = (
        "<ul>" + "".join(f"<li>{_text(one)}</li>" for one in lines) + "</ul>"
        if lines
        else "<p>この文書について、書き出しの時点で記録された制約はありません。"
        "解析結果そのものの妥当性を述べるものではありません</p>"
    )
    return f'<section class="limitations"><h2>制約</h2>{body}</section>'


def _provenance(document: Document) -> str:
    """The trust content, as the document model already composes it (AC-007, INV-027)."""
    lines = document.provenance.as_text().split("\n")
    parts: list[str] = []
    items: list[str] = []

    def flush() -> None:
        if items:
            parts.append("<ul>" + "".join(items) + "</ul>")
            items.clear()

    for line in lines[1:]:
        if line.startswith("  - "):
            # The items the model indents are one list, and a list item belongs in a list.
            items.append(f"<li>{_text(line.strip().lstrip('- '))}</li>")
        else:
            flush()
            parts.append(f"<p>{_text(line)}</p>")
    flush()
    return f'<section class="provenance"><h2>来歴</h2>{"".join(parts)}</section>'


def _verified() -> str:
    """The browsers this document form was opened and printed in by the gate, named with the version
    measured (XC-309). A recipient's browser is not chosen by the author, so the document says what
    was verified rather than promising what was not."""
    named = "、".join(f"{name} {major}" for name, major in VERIFIED_BROWSERS)
    return (
        '<footer class="verified"><p>この文書の表示と印刷は次のブラウザで確認しています: '
        f"{_text(named)}（確認した版。それより古い版や、ここにないブラウザでの表示は確認していません）</p></footer>"
    )


def _stylesheet(font: EmbeddedFont | None) -> str:
    """Inline, and with no external reference of any kind (AC-001).

    A font is embedded as a `data:` URI when there is one. The fallback list names generic families
    rather than a hosted face: a stylesheet asking for a web font is a document that renders one way
    online and another way offline.
    """
    face = ""
    stack = "system-ui, sans-serif"
    if font is not None:
        import base64

        encoded = base64.b64encode(font.data).decode("ascii")
        face = (
            "@font-face{font-family:'" + font.name + "';"
            "src:url(data:font/woff2;base64," + encoded + ") format('woff2');"
            "font-display:block}"
        )
        stack = f"'{font.name}', system-ui, sans-serif"
    return (
        face
        + ":root{color-scheme:light dark}"
        + f"body{{font-family:{stack};margin:2rem auto;max-width:52rem;line-height:1.7;padding:0 1rem}}"
        + "h1{font-size:1.6rem}h2{font-size:1.15rem;margin-top:2rem}"
        + "table.values{border-collapse:collapse;width:100%;margin:1rem 0}"
        + "table.values th,table.values td{border:1px solid currentColor;padding:.35rem .6rem;"
        + "text-align:left;vertical-align:top}"
        + "td.value{text-align:right;font-variant-numeric:tabular-nums}"
        + "td.undeclared,td.missing{font-style:italic}"
        + "p.note{font-size:.9rem;opacity:.85}"
        # A still and its legend. The picture scales to the page and never past its own pixels, so a
        # printed report does not enlarge it into softness; the legend reads as one line of facts.
        + "figure.view{margin:1rem 0}"
        + "figure.view img{max-width:100%;height:auto;display:block}"
        + "figure.view figcaption{font-size:.9rem;margin-top:.4rem}"
        + "figure.view figcaption span{margin-right:.9rem}"
        + ".legend-field{font-weight:600}"
        + ".legend-range{font-variant-numeric:tabular-nums}"
        + ".legend-map{opacity:.85}"
        + "hr.page-break{border:0;border-top:1px solid currentColor;margin:2rem 0}"
        + "section.limitations,section.provenance{margin-top:2.5rem;font-size:.95rem}"
        + "footer.verified{margin-top:2.5rem;font-size:.85rem;opacity:.85}"
        # On paper (XC-296, E-219): A4, because that is the sheet a Japanese office prints on and a
        # document printed on two sheet sizes is two layouts; a page-break block is a page break; a
        # figure, a table row and each trust section stay whole, and a heading stays with what it
        # heads, because a picture cut in two or a value parted from its unit is a different document;
        # a long table repeats its header on every page. The screen's width limit is lifted so the page
        # margins alone decide the measure.
        + "@media print{"
        + "@page{size:A4;margin:18mm 20mm}"
        + "body{max-width:none;margin:0;padding:0}"
        + "hr.page-break{break-after:page;border:0;margin:0}"
        + "figure.view,table.values tr,section.limitations,section.provenance,footer.verified{break-inside:avoid}"
        # One line of small print, close under the provenance: on paper it earns no sheet of its own.
        + "footer.verified{margin-top:1rem;font-size:.75rem}"
        + "h1,h2,figure.view figcaption{break-after:avoid}"
        + "table.values thead{display:table-header-group}"
        + "}"
    )


def _text(value: str) -> str:
    """Escaped for text content. A case name holding a `<` is a name, not markup."""
    return html_escape.escape(str(value), quote=False)


def _attribute(value: str) -> str:
    return html_escape.escape(str(value), quote=True)
