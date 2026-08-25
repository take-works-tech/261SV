"""The document a report becomes, and the three things it refuses to be produced without.

REQ-001's own note is the reason AC-002 exists: the free export path produced 34.4 MB in 21.4 seconds
for a 1.13 million point surface, and **the text annotation and point label were absent from the
exported file with no warning** while the scalar bar survived. A document whose values live only inside
the 3D content stops being readable the moment the viewer fails - and that measurement is what a silent
omission looks like from the outside.

So every number is text, the trust content is mandatory and blocks the export when it cannot be
produced, and a field with no declared unit carries the marker rather than a guess.

Verifies: report/AC-002 to AC-004, AC-007, AC-008, report/TASK-001 to TASK-003, XC-003, INV-013.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from domain_core.recorded_time import record as record_time
from domain_core.reported_value import UNDECLARED_MARKER, Caveat, Provenance, ReportedValue
from engine.report.document import (
    EXTERNAL,
    Block,
    BlockKind,
    Document,
    Provenance as Trust,
    ReportError,
    SourceFile,
    ValueRow,
    build,
    external_references,
    missing,
    undeclared,
)

WHEN = record_time(datetime(2026, 8, 25, 9, tzinfo=timezone(timedelta(hours=9))))


def a_value(unit: str | None = "MPa", value: float | None = 150.0) -> ReportedValue:
    caveats = frozenset({Caveat.UNDECLARED_UNIT}) if unit is None else frozenset()
    return ReportedValue(
        value=value, unit=unit, digits=4, provenance=Provenance.DATASET, caveats=caveats,
        location="GlobalNodeId 1003" if value is not None else None,
        missing_because=None if value is not None else "この節点は部分読み込みに含まれていません",
    )


def trust(**changed: Any) -> Trust:
    fields: dict[str, Any] = {
        "workspace_id": "workspace:001",
        "case_ids": ("case:001",),
        "sources": (SourceFile("runs/run12.vtu", WHEN),),
        "declared_units": {"stress": "MPa"},
        "product_version": "0.0.1",
        "produced": WHEN,
    }
    fields.update(changed)
    return Trust(**fields)


def a_definition() -> dict[str, Any]:
    return {
        "id": "report:001",
        "name": "週次の応力レポート",
        "locale": "ja",
        "blocks": [
            {"kind": "view", "viewId": "view:001", "title": "全体"},
            {"kind": "text", "text": "所見はまだありません。"},
            {"kind": "pageBreak"},
        ],
    }


def a_document() -> Document:
    return build(
        a_definition(),
        rows_for={"view:001": [ValueRow("最大応力", a_value())]},
        provenance=trust(),
    )


class TestEveryNumberIsText:
    def test_the_value_appears_in_the_document_text(self) -> None:
        """AC-002. A document whose values live only inside the 3D content stops being readable the
        moment the viewer fails."""
        text = a_document().as_text()

        assert "最大応力" in text
        assert "150" in text

    def test_it_carries_its_unit(self) -> None:
        assert "MPa" in a_document().as_text()

    def test_it_carries_its_provenance(self) -> None:
        """INV-013: a quantity is never shown without where it came from."""
        assert "dataset" in a_document().as_text()

    def test_it_carries_where_it_is_in_the_sources_own_words(self) -> None:
        """Never an array index - an index is a number a reader takes to the solver and fails to
        find."""
        assert "GlobalNodeId 1003" in a_document().as_text()

    def test_a_value_that_is_absent_says_why_rather_than_leaving_a_blank(self) -> None:
        """XC-001. A blank cell is a value the reader supplies an explanation for, usually a wrong
        one."""
        document = build(
            a_definition(),
            rows_for={"view:001": [ValueRow("最大応力", a_value(value=None))]},
            provenance=trust(),
        )

        assert "部分読み込み" in document.as_text()
        assert missing(document) == ("最大応力：この節点は部分読み込みに含まれていません",)

    def test_a_caveat_travels_into_the_text(self) -> None:
        value = a_value().with_caveat(Caveat.FROM_REDUCED_GEOMETRY)
        document = build(
            a_definition(), rows_for={"view:001": [ValueRow("最大応力", value)]},
            provenance=trust(),
        )

        assert "縮退した表示形状" in document.as_text()

    def test_the_values_are_answerable_without_reading_the_text(self) -> None:
        assert [row.label for row in a_document().values()] == ["最大応力"]


class TestTheTrustContentIsMandatory:
    def test_it_records_the_workspace_the_cases_and_the_version(self) -> None:
        """AC-007."""
        text = a_document().as_text()

        assert "workspace:001" in text
        assert "case:001" in text
        assert "0.0.1" in text

    def test_it_records_the_source_files_with_their_modification_times(self) -> None:
        """The time is what lets a reader tell a delivered document from one whose inputs have moved
        since (INV-027). Without it the block says which files, which is the easier half."""
        text = a_document().as_text()

        assert "runs/run12.vtu" in text
        assert "2026-08-25T00:00:00Z" in text

    def test_it_records_the_declared_units(self) -> None:
        assert "stress：MPa" in a_document().as_text()

    def test_a_report_with_no_workspace_blocks_the_export(self) -> None:
        """Rather than writing a document with a gap where its provenance should be - that is a document
        somebody sends."""
        with pytest.raises(ReportError) as refusal:
            trust(workspace_id="")
        assert "書き出しは行いません" in str(refusal.value)

    def test_a_report_with_no_product_version_blocks_it_too(self) -> None:
        with pytest.raises(ReportError):
            trust(product_version="")

    def test_a_report_with_no_cases_blocks_it(self) -> None:
        with pytest.raises(ReportError):
            trust(case_ids=())

    def test_having_no_source_files_is_stated_rather_than_omitted(self) -> None:
        """An empty list and an absent list read the same on a page, and only one of them means "this
        report drew on no file"."""
        document = build(a_definition(), provenance=trust(sources=()))

        assert "元ファイル：ありません" in document.as_text()

    def test_the_version_is_handed_in_rather_than_discovered(self) -> None:
        """Nothing here can know which build produced the document, so nothing here guesses."""
        import inspect

        assert "product_version" in inspect.signature(Trust).parameters


class TestAnUndeclaredUnitIsMarkedNeverGuessed:
    def test_the_marker_appears_where_the_unit_would(self) -> None:
        """AC-008, XC-003."""
        document = build(
            a_definition(),
            rows_for={"view:001": [ValueRow("比", a_value(unit=None))]},
            provenance=trust(),
        )

        assert UNDECLARED_MARKER in document.as_text()

    def test_which_values_are_undeclared_is_answerable(self) -> None:
        document = build(
            a_definition(),
            rows_for={"view:001": [ValueRow("比", a_value(unit=None)), ValueRow("応力", a_value())]},
            provenance=trust(),
        )

        assert undeclared(document) == ("比",)

    def test_the_marker_has_one_spelling_across_the_product(self) -> None:
        """The axis label, the table cell and the report line cannot disagree about the same absence."""
        from engine.graph.definition import UNDECLARED_MARKER as ON_AN_AXIS

        assert ON_AN_AXIS is UNDECLARED_MARKER

    def test_it_is_not_said_twice_for_the_same_value(self) -> None:
        """The unit column already says it; repeating it as a caveat reads as two problems."""
        document = build(
            a_definition(),
            rows_for={"view:001": [ValueRow("比", a_value(unit=None))]},
            provenance=trust(),
        )

        line = next(
            one for one in document.as_text().splitlines() if one.startswith("比：")
        )
        assert line.count(UNDECLARED_MARKER) == 1


class TestTheDocumentOpensWithTheNetworkDisabled:
    def test_nothing_in_it_needs_the_network(self) -> None:
        """AC-001, INV-007. Checked on the document rather than trusted of the writers: a report opens
        on a machine that may have no network at all."""
        assert external_references(a_document()) == ()

    def test_an_external_reference_would_be_found(self) -> None:
        """Otherwise the check above passes by being unable to fail."""
        document = build(
            {**a_definition(), "blocks": [{"kind": "text", "text": "https://example.com/logo.png を参照"}]},
            provenance=trust(),
        )

        assert external_references(document) == ("https://",)

    def test_a_protocol_relative_reference_is_found_too(self) -> None:
        assert EXTERNAL.search("//cdn.example.com/style.css") is not None


class TestTheBlocksAreTheContractsBlocks:
    def test_a_kind_the_contract_does_not_list_is_refused(self) -> None:
        with pytest.raises(ReportError):
            build({**a_definition(), "blocks": [{"kind": "carousel"}]}, provenance=trust())

    def test_the_five_kinds(self) -> None:
        assert {kind.value for kind in BlockKind} == {
            "view", "graph", "valueTable", "text", "pageBreak"
        }

    def test_a_reduced_view_says_so_in_the_document(self) -> None:
        """AC-003: marked in the document, not only on screen - and the numbers still come from the full
        data."""
        block = Block(BlockKind.VIEW, "全体", reduced="三角形を 10% に間引いています")

        assert "簡略化されています" in block.as_text()
        assert "完全なデータで計算" in block.as_text()

    def test_a_value_from_a_partial_dataset_states_its_coverage(self) -> None:
        """AC-004."""
        block = Block(BlockKind.VIEW, "全体", coverage="12 パート中 9 パート")

        assert "12 パート中 9 パート" in block.as_text()

    def test_a_page_break_is_a_break_and_not_an_empty_section(self) -> None:
        assert Block(BlockKind.PAGE_BREAK).as_text() == "---"


class TestNothingHereProducesANumber:
    def test_the_rows_are_handed_in(self) -> None:
        """MOD-004 produces numbers and this module arranges them. A report layer that computed would be
        a second place where a value comes from (INV-001)."""
        import inspect

        assert "rows_for" in inspect.signature(build).parameters

    def test_the_module_does_not_reach_the_analysis_layer(self) -> None:
        from pathlib import Path

        import engine.report.document as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "engine.analysis" not in source
