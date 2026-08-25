"""The one file a recipient opens with nothing installed.

Every rule here is a refusal to produce a document that looks complete and is not. The measurement
behind them is in spike/results.json: the free export path wrote 34.4 MB for a 1.13 million point
surface and **left the text annotation and the point label out of the file with no warning** while the
scalar bar survived. A reader of that file has no way to know something is missing, which is why the
statement has to come before the file exists and then travel inside it.

Verifies: report/AC-001, AC-002, AC-003, AC-004, AC-007, AC-008, AC-014, AC-016, AC-031, INV-007,
XC-001, XC-003.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from domain_core.recorded_time import RecordedTime
from domain_core.reported_value import Caveat, Provenance as Origin, ReportedValue
from engine.report.document import (
    Block,
    BlockKind,
    Document,
    Provenance,
    ReportError,
    SourceFile,
    ValueRow,
)
from engine.report.html import (
    BASIC_LATIN,
    STATIC_KINDS,
    Capability,
    EmbeddedFont,
    render,
    unrepresentable,
    write,
)

WHEN = RecordedTime("2026-08-26T00:00:00Z", 540)


def a_provenance() -> Provenance:
    return Provenance(
        workspace_id="workspace:001",
        case_ids=("Run 12",),
        sources=(SourceFile("D:/studies/run12.vtu", WHEN),),
        declared_units={"stress": "MPa"},
        product_version="0.1.0",
        produced=WHEN,
    )


def a_value(**over: object) -> ReportedValue:
    fields: dict[str, object] = {
        "value": 241.7,
        "unit": "MPa",
        "digits": 4,
        "provenance": Origin.COMPUTED,
        # A computed value carries the formula that produced it (GL-032): without it the number cannot
        # be checked, which is the whole reason the column exists.
        "formula": "max(von Mises)",
    }
    fields.update(over)
    return ReportedValue(**fields)  # type: ignore[arg-type]


def a_document(*blocks: Block, title: str = "Run 12 の応力") -> Document:
    return Document(
        title=title,
        blocks=blocks or (Block(BlockKind.VALUE_TABLE, "最大応力", (ValueRow("最大", a_value()),)),),
        provenance=a_provenance(),
    )


class TestNothingInTheFileReachesTheNetwork:
    def test_a_produced_document_holds_no_external_reference(self) -> None:
        """AC-001, INV-007. A deliverable is opened on a machine that may have no network at all."""
        text = render(a_document())

        assert "http://" not in text and "https://" not in text

    def test_the_stylesheet_is_inline(self) -> None:
        text = render(a_document())

        assert "<style>" in text
        assert "<link" not in text

    def test_a_document_whose_text_reaches_out_is_refused(self, tmp_path: Path) -> None:
        """Checked of the output rather than trusted of the writer: the text came from somebody else."""
        document = a_document(
            Block(BlockKind.TEXT, "出典", text="詳しくは https://example.test/notes を参照")
        )

        with pytest.raises(ReportError) as refusal:
            write(document, tmp_path / "report.html", accepted=True)

        assert "外部を参照" in str(refusal.value)
        assert not (tmp_path / "report.html").exists()

    def test_an_embedded_font_is_a_data_uri_and_not_a_hosted_one(self) -> None:
        font = EmbeddedFont("Test Sans", "OFL-1.1", b"\x00\x01font", frozenset("応力最大"))

        text = render(a_document(), Capability(font=font))

        assert "data:font/woff2;base64," in text
        assert "fonts.googleapis" not in text


class TestEveryNumberIsText:
    def test_the_value_its_unit_and_its_provenance_are_in_the_document(self) -> None:
        """AC-002. Readable with the 3D content broken, old, or printed."""
        text = render(a_document())

        assert "241.7" in text
        assert "MPa" in text
        assert "computed" in text

    def test_a_value_with_no_declared_unit_carries_the_marker(self) -> None:
        """AC-008, XC-003. Never a guess, and never an empty column."""
        document = a_document(
            Block(BlockKind.VALUE_TABLE, "最大", (ValueRow("最大", a_value(unit=None, caveats=frozenset({Caveat.UNDECLARED_UNIT}))),))
        )

        text = render(document)

        assert "単位が宣言されていません" in text

    def test_a_missing_value_says_why_rather_than_leaving_a_blank(self) -> None:
        """XC-001. A blank reads as zero to some readers and as "not applicable" to others."""
        document = a_document(
            Block(
                BlockKind.VALUE_TABLE,
                "最大",
                (ValueRow("最大", a_value(value=None, missing_because="この時刻に出力がありません")),),
            )
        )

        text = render(document)

        assert "値なし" in text
        assert "この時刻に出力がありません" in text
        assert "<td></td>" not in text

    def test_a_partial_value_carries_the_range_it_covered(self) -> None:
        """AC-004. "part of the dataset was missing" without saying which part is unactionable."""
        document = a_document(
            Block(
                BlockKind.VALUE_TABLE,
                "最大",
                (
                    ValueRow(
                        "最大",
                        a_value(caveats=frozenset({Caveat.PARTIAL_DATASET})),
                        coverage="15 パート中 14",
                    ),
                ),
            )
        )

        text = render(document)

        assert "15 パート中 14" in text

    def test_a_reduced_display_says_so_in_the_document(self) -> None:
        """AC-003. In the file, not only on the screen the reduction happened on."""
        document = a_document(
            Block(BlockKind.GRAPH, "傾向", (ValueRow("最大", a_value()),), reduced="点を 1/10 に間引き")
        )

        text = render(document)

        assert "点を 1/10 に間引き" in text
        assert "数値は完全なデータで計算しています" in text


class TestItSaysWhatItCannotCarryBeforeItWrites:
    def test_a_rotatable_view_is_named_as_unsupported(self) -> None:
        """AC-001's second half needs the vtk.js bundle. A still picture would satisfy the sentence and
        not the requirement, so the kind is refused and named rather than quietly downgraded."""
        document = a_document(Block(BlockKind.VIEW, "全体図"))

        found = unrepresentable(document)

        assert any("vtk.js" in one.what for one in found)
        assert any(one.where == "全体図" for one in found)

    def test_writing_is_refused_until_the_list_is_accepted(self, tmp_path: Path) -> None:
        """AC-014: said **before** the file exists. A list produced alongside it is one somebody found
        afterwards."""
        document = a_document(Block(BlockKind.VIEW, "全体図"))

        with pytest.raises(ReportError) as refusal:
            write(document, tmp_path / "report.html")

        assert "書き出しは行いません" in str(refusal.value)
        assert not (tmp_path / "report.html").exists()

    def test_accepting_it_writes_the_statement_into_the_document(self, tmp_path: Path) -> None:
        """Refusing and then writing a file that kept the omission to itself would move the silence one
        step along rather than ending it."""
        document = a_document(Block(BlockKind.VIEW, "全体図"))

        export = write(document, tmp_path / "report.html", accepted=True)

        assert export.path.exists()
        assert any("vtk.js" in one for one in export.stated)
        assert "vtk.js" in export.path.read_text(encoding="utf-8")

    def test_a_document_this_build_can_carry_needs_no_acceptance(self, tmp_path: Path) -> None:
        font = EmbeddedFont("Test Sans", "OFL-1.1", b"\x00font", frozenset(_all_characters()))

        export = write(a_document(), tmp_path / "report.html", capability=Capability(font=font))

        assert export.bytes > 0
        assert export.stated == ()

    def test_the_static_kinds_are_written_down(self) -> None:
        assert BlockKind.VIEW not in STATIC_KINDS
        assert BlockKind.VALUE_TABLE in STATIC_KINDS


class TestCharactersAreNamedRatherThanCounted:
    def test_without_a_font_the_characters_outside_basic_latin_are_named(self) -> None:
        """AC-015, AC-016. "12 characters may not render" is a warning nobody can act on."""
        found = unrepresentable(a_document())

        assert any("U+" in one.what for one in found)

    def test_it_says_in_which_element(self) -> None:
        found = unrepresentable(a_document())

        assert any("表題" in one.where for one in found)

    def test_a_font_missing_one_character_is_reported_by_that_character(self, ) -> None:
        """A font named for a language and missing one character produces an empty box, which is the
        outcome AC-016 exists to prevent - so coverage is characters, not a name."""
        covered = set(_all_characters()) - {"応"}
        font = EmbeddedFont("Test Sans", "OFL-1.1", b"\x00font", frozenset(covered))

        found = unrepresentable(a_document(), Capability(font=font))

        assert any("応" in one.what for one in found)

    def test_even_a_latin_only_report_needs_the_font(self) -> None:
        """Written expecting the opposite, and the check said otherwise.

        The product's own labels are Japanese - the provenance block says `ワークスペース`,
        `元ファイル`, `宣言された単位` - so a report whose content is entirely Latin still
        carries characters outside it. The embedded font of AC-015 is therefore not a provision for
        reports that happen to contain Japanese: **every report this product writes needs it**, and a
        build without one produces empty boxes on a machine with no Japanese font installed.
        """
        document = Document(
            title="Run 12",
            blocks=(Block(BlockKind.VALUE_TABLE, "Maximum", (ValueRow("Max", a_value()),)),),
            provenance=Provenance(
                workspace_id="w", case_ids=("Run 12",), sources=(),
                declared_units={}, product_version="0.1.0",
            ),
        )

        found = unrepresentable(document)

        assert [one.where for one in found] == ["来歴"]

    def test_content_with_no_font_needed_is_reported_as_such(self) -> None:
        """The element-by-element answer, so the statement is about the element and not the document."""
        document = a_document()

        where = {one.where for one in unrepresentable(document)}

        assert "表題" in where

    def test_basic_latin_is_what_it_says_it_is(self) -> None:
        assert "A" in BASIC_LATIN and " " in BASIC_LATIN
        assert "応" not in BASIC_LATIN

    def test_a_font_with_no_licence_is_refused(self) -> None:
        """Redistribution is the whole question with a font, and a file with no recorded terms cannot be
        answered for."""
        with pytest.raises(ReportError):
            EmbeddedFont("Test Sans", "", b"\x00font", frozenset())


class TestTheTrustContentIsInTheFile:
    def test_the_provenance_block_is_written(self) -> None:
        """AC-007. The workspace, the cases, the sources with their times, the units, the version."""
        text = render(a_document())

        for expected in ("workspace:001", "Run 12", "run12.vtu", "2026-08-26T00:00:00Z", "0.1.0"):
            assert expected in text

    def test_a_limitations_section_is_always_present(self) -> None:
        """AC-031. Its absence is the reading a recipient takes from it: a report with no limitations
        section is one claiming none, and no result of a discretised solve has none."""
        text = render(a_document())

        assert "制約" in text

    def test_the_limitations_name_the_values_with_no_unit(self) -> None:
        document = a_document(
            Block(BlockKind.VALUE_TABLE, "最大", (ValueRow("せん断", a_value(unit=None, caveats=frozenset({Caveat.UNDECLARED_UNIT}))),))
        )

        text = render(document)

        assert text.count("せん断") >= 2  # once in the table, once in the limitations


class TestTextIsEscaped:
    def test_a_name_holding_a_bracket_stays_a_name(self) -> None:
        """A case called "<script>" is a case name, not markup - and a writer that let it through would
        be one somebody could hand a file to."""
        document = a_document(title="<script>alert(1)</script>")

        text = render(document)

        assert "<script>alert" not in text
        assert "&lt;script&gt;" in text

    def test_the_language_attribute_is_quoted(self) -> None:
        text = render(a_document())

        assert '<html lang="ja">' in text


def _all_characters() -> set[str]:
    """Every character a test document holds, so a font can be declared to cover it."""
    return set(render(a_document()))
