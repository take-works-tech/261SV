"""A printed deliverable keeps its pages (report/AC-037, XC-296; #267).

A report is still handed round on paper. The exported document is printed here through the same
browsers a reader prints from - Edge and Chrome, headless, to PDF - and what the pages hold is read
back from the PDF: a short document is one page, a page-break block starts a new one, a figure
travels whole, and the two browsers agree. Where no browser is installed the test says so; the
measurement it stands on is E-219, which also records what a page count cannot show and was looked
at instead.
"""

from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

from domain_core.recorded_time import record  # noqa: E402
from engine.report.document import Block, BlockKind, Document, Figure, Legend, Provenance, SourceFile, ValueRow, ViewForm  # noqa: E402
from engine.report.html import Capability, render, write  # noqa: E402
from domain_core.reported_value import Provenance as Origin, ReportedValue  # noqa: E402
from test_exported_document_opens import browsers, version_of  # noqa: E402
from test_report_end_to_end import a_font  # noqa: E402

#: Where a run keeps the PDFs it printed, for a person to look at; unset, they go with tmp_path.
KEEP = os.environ.get("SOLVIA_KEEP_PDF_DIR")


def a_png(width: int, height: int) -> bytes:
    """A PNG of the stated size with a gradient in it: enough for a browser to lay out and print."""
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows += bytes((x * 255 // max(width - 1, 1), y * 255 // max(height - 1, 1), 96))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(rows), 6))
        + chunk(b"IEND", b"")
    )


def a_value(number: float) -> ReportedValue:
    return ReportedValue(value=number, unit="MPa", digits=4, provenance=Origin.COMPUTED, formula="max(stress)")


def a_figure_block(title: str, width: int = 1200, height: int = 900) -> Block:
    figure = Figure(
        png=a_png(width, height), width=width, height=height,
        legend=Legend(field_name="stress", unit="MPa", minimum=0.0, maximum=241.7, digits=4, colour_map="viridis", uniform=True),
        description="全体外観",
    )
    return Block(BlockKind.VIEW, title, rows=(ValueRow("最大応力", a_value(241.7)),), form=ViewForm.STILL, figure=figure)


def a_table_block(title: str, rows: int = 3) -> Block:
    return Block(BlockKind.VALUE_TABLE, title, rows=tuple(ValueRow(f"値 {index + 1}", a_value(100.0 + index)) for index in range(rows)))


def a_text_block(title: str, paragraphs: int = 1, sentences: int = 12) -> Block:
    return Block(BlockKind.TEXT, title, text="\n\n".join("梁の基本ケースについての所見。" * sentences for _ in range(paragraphs)))


def a_document(blocks: tuple[Block, ...], where: Path) -> Path:
    source = where / "run12.vtu"
    source.write_bytes(b"not read: the provenance names it")
    document = Document(
        title="Run 12 の最大応力",
        blocks=blocks,
        provenance=Provenance(
            workspace_id="workspace:001",
            case_ids=("Run 12",),
            sources=(SourceFile(str(source), record(datetime.fromtimestamp(source.stat().st_mtime, tz=timezone.utc))),),
            declared_units={"stress": "MPa"},
            product_version="0.1.0",
        ),
    )
    target = where / "document.html"
    # The stand-in font of the end-to-end test covers every character, so the limitations section
    # holds no list of glyphs and the pages measured are the document's own; the browser lays the
    # text out in its own faces, which is what a reader's machine does (AC-015).
    write(document, target, capability=Capability(font=a_font(render(document))))
    return target


def printed(executable: str, url: str, name: str) -> bytes:
    """The document as the browser prints it: a PDF with no header or footer of the browser's own."""
    profile = tempfile.mkdtemp(prefix="solvia-browser-")
    out = Path(profile) / "printed.pdf"
    command = [
        executable, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
        f"--user-data-dir={profile}", "--no-pdf-header-footer", f"--print-to-pdf={out}", url,
    ]
    if sys.platform != "win32":
        command.insert(1, "--no-sandbox")
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        assert done.returncode == 0, f"{executable} exited {done.returncode}: {done.stderr[-500:]}"
        data = out.read_bytes()
    finally:
        if KEEP and out.exists():
            Path(KEEP).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(out, Path(KEEP) / name)
        shutil.rmtree(profile, ignore_errors=True)
    assert data.startswith(b"%PDF"), "not a PDF"
    return data


def page_size(pdf: bytes) -> tuple[float, float]:
    """The first page's box in points: A4 is 595 x 842, US Letter 612 x 792."""
    box = re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
    assert box, "no page box in the PDF"
    return float(box.group(3)) - float(box.group(1)), float(box.group(4)) - float(box.group(2))


def page_count(pdf: bytes) -> int:
    """The page tree's own count. Chromium writes one `/Type /Pages` node with `/Count`; where a
    tree has several, the root's is the largest."""
    counts = [int(one) for one in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", pdf, re.S)]
    assert counts, "no page tree in the PDF"
    return max(counts)


@pytest.fixture(scope="module")
def present() -> list[tuple[str, str]]:
    found = browsers()
    if not found:
        pytest.skip("no Chromium browser is installed here; the measurement is E-219, taken with Edge and Chrome")
    for name, executable in found:
        print(f"{name} {version_of(executable)} at {executable}")
    return found


def pages_in_each(present: list[tuple[str, str]], target: Path, label: str) -> dict[str, int]:
    return {name: page_count(printed(executable, target.resolve().as_uri(), f"{label}-{name}.pdf")) for name, executable in present}


class TestThePagesOfAPrintedDocument:
    def test_a_short_document_is_one_a4_page(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        target = a_document((a_text_block("所見", sentences=3), a_table_block("応力", rows=2)), tmp_path)
        for name, executable in present:
            pdf = printed(executable, target.resolve().as_uri(), f"short-{name}.pdf")
            assert page_count(pdf) == 1, name
            width, height = page_size(pdf)
            assert (round(width), round(height)) == (595, 842), f"{name}: the sheet is {width} x {height} pt, not A4 (XC-296)"

    def test_a_page_break_block_starts_a_new_page(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        (tmp_path / "one").mkdir()
        (tmp_path / "two").mkdir()
        one = a_document((a_text_block("前半"), Block(BlockKind.PAGE_BREAK), a_text_block("後半")), tmp_path / "one")
        two = a_document((a_text_block("一"), Block(BlockKind.PAGE_BREAK), a_text_block("二"), Block(BlockKind.PAGE_BREAK), a_text_block("三")), tmp_path / "two")
        assert set(pages_in_each(present, one, "one-break").values()) == {2}
        assert set(pages_in_each(present, two, "two-breaks").values()) == {3}

    def test_a_figure_at_page_width_keeps_its_page_and_the_trust_content_follows(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        """A figure is laid out at the width of the page whatever its pixels, so with its legend, its
        value and the limitations it fills the first sheet, and the provenance - a section that is not
        split - opens the second (E-219). Two sheets, the same in both browsers."""
        target = a_document((a_figure_block("全体外観", 800, 600),), tmp_path)
        assert set(pages_in_each(present, target, "figure").values()) == {2}

    def test_a_figure_after_a_long_text_travels_whole_to_the_next_page(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        """A page count cannot tell a figure split across two pages from one moved whole to the second;
        E-219 records what the pages looked like. What the count does show is that the figure did not
        vanish and that the two browsers laid the document out alike."""
        target = a_document((a_text_block("所見", paragraphs=5), a_figure_block("全体外観"), a_table_block("応力", rows=6)), tmp_path)
        counts = pages_in_each(present, target, "text-then-figure")
        assert len(set(counts.values())) == 1 and min(counts.values()) >= 2, counts

    def test_both_browsers_agree_on_a_whole_report(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        blocks = (
            a_text_block("要約"), a_figure_block("全体外観"), a_table_block("主要値", rows=4),
            Block(BlockKind.PAGE_BREAK), a_figure_block("最大応力の近傍"), a_text_block("所見", paragraphs=3),
        )
        target = a_document(blocks, tmp_path)
        counts = pages_in_each(present, target, "whole")
        assert len(set(counts.values())) == 1, counts
        assert min(counts.values()) >= 2
