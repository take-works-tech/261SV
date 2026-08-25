"""The summary a report carries with no language model, and the coverage a partial value must state.

AC-013 makes the mechanical summary the part that is **always** there rather than the degraded version
of a generated one. So the test that matters most is the negative one: it composes no prose, contains
none of the language `14_reporting_standards.md` says an engineering audience rejects a report for, and
requires no network.

AC-004's rule is the same shape. A caveat saying "part of the dataset was missing" without saying which
part is a warning nobody can act on - the reader cannot tell whether one part of fifteen was absent or
twelve were - so a partial value with no coverage refuses to be put in a document at all.

Verifies: report/AC-004, AC-011 to AC-013, report/TASK-006, TASK-014, E-071.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain_core.recorded_time import record as record_time
from domain_core.reported_value import Caveat, Provenance, ReportedValue
from engine.report.document import (
    Block,
    BlockKind,
    Document,
    Provenance as Trust,
    ReportError,
    SourceFile,
    ValueRow,
    partial,
)
from engine.report.summary import Authorship, needs_a_model, summarise

WHEN = record_time(datetime(2026, 8, 25, 9, tzinfo=timezone(timedelta(hours=9))))

#: The language an engineering audience rejects a report for, enumerated by category (E-071). None of it
#: can appear here, because nothing here composes a sentence.
REJECTED = (
    "best", "worst", "optimal", "good agreement", "acceptable", "satisfactory",
    "significant", "considerable", "minimal", "slight", "roughly",
    "良好", "概ね", "ほぼ最適", "十分に",
)


def a_value(
    value: float | None = 150.0, unit: str | None = "MPa", *caveats: Caveat
) -> ReportedValue:
    marks = set(caveats)
    if unit is None:
        marks.add(Caveat.UNDECLARED_UNIT)
    return ReportedValue(
        value=value, unit=unit, digits=4, provenance=Provenance.DATASET,
        caveats=frozenset(marks),
        missing_because=None if value is not None else "この節点は読み込まれていません",
    )


def trust() -> Trust:
    return Trust(
        workspace_id="workspace:001",
        case_ids=("case:001",),
        sources=(SourceFile("runs/run12.vtu", WHEN),),
        declared_units={"stress": "MPa"},
        product_version="0.0.1",
        produced=WHEN,
    )


def a_document(rows: list[ValueRow], blocks: list[Block] | None = None) -> Document:
    return Document(
        title="週次の応力レポート",
        blocks=tuple(blocks or [Block(BlockKind.VIEW, "全体", rows=tuple(rows))]),
        provenance=trust(),
    )


TWO_VALUES = [ValueRow("上面の最大応力", a_value(240.0)), ValueRow("下面の最大応力", a_value(90.0))]


class TestTheMechanicalSummaryIsAlwaysThere:
    def test_it_needs_no_language_model(self) -> None:
        """AC-013. The mechanical summary is not the degraded version of a generated one."""
        found = summarise(a_document(TWO_VALUES))

        assert found.authorship is Authorship.MECHANICAL
        assert needs_a_model(found) is False

    def test_it_is_marked_as_mechanical_in_the_text(self) -> None:
        """A reader who cannot tell which sentences a model wrote has to treat all of them as if one
        did (AC-011)."""
        assert "言語モデルは使っていません" in summarise(a_document(TWO_VALUES)).as_text()

    def test_it_counts_the_values(self) -> None:
        assert "2 個の値" in summarise(a_document(TWO_VALUES)).as_text()

    def test_the_extremes_are_named_with_their_labels(self) -> None:
        """"The maximum is 240 MPa" is a number without a subject, and the reader has to go looking for
        which quantity it belonged to."""
        text = summarise(a_document(TWO_VALUES)).as_text()

        assert "最大は 上面の最大応力 240" in text
        assert "最小は 下面の最大応力 90" in text

    def test_a_single_value_is_not_described_as_both_extremes(self) -> None:
        text = summarise(a_document([ValueRow("最大応力", a_value())])).as_text()

        assert "最大は" not in text
        assert "1 件です" in text

    def test_it_says_how_many_files_it_came_from(self) -> None:
        assert "元ファイル 1 件" in summarise(a_document(TWO_VALUES)).as_text()

    def test_it_names_the_values_it_was_derived_from(self) -> None:
        """AC-011 asks a generated passage to name what it was derived from; the mechanical one carries
        the same thing, so the two can be compared rather than trusted differently."""
        assert summarise(a_document(TWO_VALUES)).derived_from == (
            "上面の最大応力", "下面の最大応力"
        )


class TestItContainsNoneOfTheLanguageThatIsRejected:
    def test_no_superlative_or_subjective_word_appears(self) -> None:
        """E-071's enumeration is exactly the language a summariser reaches for. Nothing here composes a
        sentence, so none of it can arrive."""
        text = summarise(a_document(TWO_VALUES)).as_text().lower()

        for word in REJECTED:
            assert word.lower() not in text

    def test_it_states_quantities_and_stops(self) -> None:
        """Every line ends in a figure or a count rather than an assessment of one."""
        lines = summarise(a_document(TWO_VALUES)).lines

        assert all(any(character.isdigit() for character in line) for line in lines)

    def test_it_cannot_state_a_value_the_report_does_not_carry(self) -> None:
        """AC-012, and it is true here by construction rather than by restraint: the summary is derived
        from the document's own rows and has nothing else to say."""
        found = summarise(a_document(TWO_VALUES))

        assert set(found.derived_from) <= {row.label for row in TWO_VALUES}


class TestWhatAReaderMustKnowIsKeptApart:
    def test_missing_values_are_a_concern_rather_than_a_line(self) -> None:
        """Burying them in a list of figures is how they get skimmed past."""
        found = summarise(a_document([ValueRow("最大応力", a_value(value=None))]))

        assert any("値のない項目" in one for one in found.concerns)
        assert not any("値のない項目" in one for one in found.lines)

    def test_undeclared_units_are_a_concern(self) -> None:
        found = summarise(a_document([ValueRow("比", a_value(unit=None))]))

        assert any("単位が宣言されていない" in one for one in found.concerns)

    def test_a_reduced_figure_is_a_concern_and_says_the_numbers_are_not(self) -> None:
        found = summarise(
            a_document([], [Block(BlockKind.VIEW, "全体", reduced="三角形を 10% に間引いています")])
        )

        assert any("完全なデータで計算" in one for one in found.concerns)

    def test_a_value_measured_on_reduced_geometry_is_named(self) -> None:
        """INV-001's own failure mode: a number measured on display geometry is wrong in a way that
        looks right."""
        found = summarise(
            a_document([ValueRow("寸法", a_value(1.0, "m", Caveat.FROM_REDUCED_GEOMETRY))])
        )

        assert any("縮退した表示形状" in one for one in found.concerns)

    def test_a_clean_report_has_nothing_to_warn_about(self) -> None:
        """And says nothing, rather than manufacturing a caution to look thorough."""
        assert summarise(a_document(TWO_VALUES)).concerns == ()


class TestAPartialValueStatesWhatItCovered:
    def test_it_is_refused_without_the_coverage(self) -> None:
        """AC-004. A caveat with no figures behind it is a warning nobody can act on: the reader cannot
        tell whether one part of fifteen was absent or twelve were."""
        with pytest.raises(ReportError) as refusal:
            ValueRow("最大応力", a_value(240.0, "MPa", Caveat.PARTIAL_DATASET))

        assert "対象範囲" in str(refusal.value)

    def test_with_the_coverage_it_appears_in_the_text(self) -> None:
        row = ValueRow(
            "最大応力", a_value(240.0, "MPa", Caveat.PARTIAL_DATASET),
            coverage="15 パート中 12 パート",
        )

        assert "15 パート中 12 パート" in row.as_text()

    def test_which_values_are_partial_is_answerable(self) -> None:
        document = a_document([
            ValueRow(
                "最大応力", a_value(240.0, "MPa", Caveat.PARTIAL_DATASET),
                coverage="15 パート中 12 パート",
            ),
            ValueRow("下面の最大応力", a_value(90.0)),
        ])

        assert partial(document) == ("最大応力：15 パート中 12 パート",)

    def test_the_summary_carries_it_as_a_concern(self) -> None:
        document = a_document([
            ValueRow(
                "最大応力", a_value(240.0, "MPa", Caveat.PARTIAL_DATASET),
                coverage="15 パート中 12 パート",
            )
        ])

        assert any("15 パート中 12 パート" in one for one in summarise(document).concerns)

    def test_a_value_that_is_not_partial_needs_no_coverage(self) -> None:
        """The requirement is attached to the caveat, not to every value."""
        assert ValueRow("最大応力", a_value(240.0)).coverage is None


class TestTheSummaryNeedsNoNetwork:
    def test_the_module_reaches_nothing_outside_this_machine(self) -> None:
        """AC-013's second half, INV-007. Structural: a module that imported a client could make a
        request, whatever it currently does."""
        from pathlib import Path

        import engine.report.summary as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for door in ("requests", "urllib", "httpx", "socket", "http.client"):
            assert door not in source

    def test_nor_does_the_document_module(self) -> None:
        from pathlib import Path

        import engine.report.document as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for door in ("requests", "urllib", "httpx", "socket"):
            assert door not in source
