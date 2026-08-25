"""A result file to a deliverable, through every layer, with the number checked at the far end.

This is the product's claim made executable. A file is written, read into the canonical frame, reduced
to one number on the **full** dataset, put into a document with the unit somebody declared, and written
as one self-contained HTML file - and the number that comes out of the file is compared against the one
computed here from the dataset's own array.

The comparison is the point. INV-001 and INV-009 say the number and the picture come from different code
paths: display geometry is decimated, tessellated and scaled, and measuring it produces a number that is
wrong in a way that looks right. A test that asserted only "the file exists" would pass for a document
whose figure was computed from the decimated copy.

The unit is the second point. The `.vtu` written here carries **no unit** - CAE formats do not carry them
reliably - and `MPa` appears in the deliverable only because it was declared (XC-003). The test asserts
the file itself is silent on units, so the claim is about this product rather than about VTK.

Verifies: report/AC-001, AC-002, AC-007, AC-008, ingest/AC-020, INV-001, INV-009, INV-013, INV-027,
XC-003.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from conftest import requires_vtk

requires_vtk()

from vtkmodules.util.numpy_support import numpy_to_vtk  # noqa: E402
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import (  # noqa: E402
    VTK_TRIANGLE,
    vtkCellArray,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter  # noqa: E402

from domain_core.dataset import Association  # noqa: E402
from domain_core.recorded_time import record  # noqa: E402
from domain_core.reported_value import Provenance as Origin, ReportedValue  # noqa: E402
from engine import reader  # noqa: E402
from engine.analysis.summary import Reduction, summarise  # noqa: E402
from engine.report.document import (  # noqa: E402
    Block,
    BlockKind,
    Document,
    Provenance,
    SourceFile,
    ValueRow,
)
from engine.report.html import Capability, EmbeddedFont, write  # noqa: E402

#: Deliberately not round, and deliberately float32 - which is what a solver writes and what INV-031
#: says is stored rather than promoted. The reduction happens in float64 (E-143).
STRESS = (12.5, 241.7, 98.25, 3.125)


def write_case(path: Path) -> None:
    """A four-point surface with one field and **no unit anywhere in the file**."""
    coordinates = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64
    )
    points = vtkPoints()
    points.SetData(numpy_to_vtk(coordinates, deep=True))

    cells = vtkCellArray()
    for triangle in ([0, 1, 2], [0, 2, 3]):
        cells.InsertNextCell(3)
        for index in triangle:
            cells.InsertCellPoint(index)

    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(VTK_TRIANGLE, cells)

    field = vtkFloatArray()
    field.SetName("stress")
    for value in STRESS:
        field.InsertNextValue(value)
    grid.GetPointData().AddArray(field)

    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def a_font(text: str) -> EmbeddedFont:
    """A stand-in for the licensed subset of AC-015, covering exactly what this document holds.

    Not the real font: choosing one is a licence question and its own decision. What it stands in for
    is the capability, so this test exercises the path a shipped build takes rather than the refusal
    path a build without a font takes.
    """
    return EmbeddedFont("Test Sans", "test-only, not redistributed", b"\x00woff2", frozenset(text))


def a_deliverable(tmp_path: Path) -> tuple[Path, float, str]:
    """Run the whole thread and return the file, the number, and the file's own text."""
    source = tmp_path / "run12.vtu"
    write_case(source)

    dataset = reader.read(source)
    field = dataset.fields["stress"]

    # Computed on the full dataset in the canonical frame, never on display geometry (INV-001, INV-009).
    summary = summarise(
        field.values,
        reduction=Reduction.MAX,
        association=Association.POINT,
        scope="ケース全体（4 点）",
        unit="MPa",
    )
    assert summary.value is not None

    value = ReportedValue(
        value=summary.value,
        # Declared by a person, never taken from the file (XC-003).
        unit="MPa",
        digits=4,
        provenance=Origin.COMPUTED,
        formula="max(stress)",
    )
    document = Document(
        title="Run 12 の最大応力",
        blocks=(
            Block(
                BlockKind.VALUE_TABLE,
                "応力",
                (ValueRow("最大応力", value),),
            ),
        ),
        provenance=Provenance(
            workspace_id="workspace:001",
            case_ids=("Run 12",),
            sources=(
                SourceFile(
                    str(source),
                    record(datetime.fromtimestamp(source.stat().st_mtime, tz=timezone.utc)),
                ),
            ),
            declared_units={"stress": "MPa"},
            product_version="0.1.0",
        ),
    )

    destination = tmp_path / "run12.html"
    from engine.report.html import render

    covering = render(document)
    write(document, destination, capability=Capability(font=a_font(covering)))
    return destination, summary.value, destination.read_text(encoding="utf-8")


class TestTheNumberSurvivesTheWholeThread:
    def test_the_figure_in_the_file_is_the_one_computed_on_the_full_dataset(
        self, tmp_path: Path
    ) -> None:
        """The whole claim. A test asserting only that the file exists would pass for a document whose
        figure had been measured off the decimated display copy (INV-001, INV-009)."""
        path, computed, text = a_deliverable(tmp_path)

        # **Written expecting `max(STRESS)` and corrected by the run.** 241.7 has no float32
        # representation: what the file holds is 241.6999969482422, and the reduction is right to
        # report that rather than the literal somebody typed. The comparison has to be against what
        # was *stored* - which is the first of the four precision questions, and the one a test is
        # most likely to get wrong, because the literal is right there in the source.
        stored = np.asarray(STRESS, dtype=np.float32).astype(np.float64)
        expected = float(stored.max())

        assert expected != max(STRESS)  # the point of the correction, kept where it happened
        assert computed == expected
        assert path.stat().st_size > 0

    def test_the_document_shows_the_digits_the_source_supports_and_no_more(
        self, tmp_path: Path
    ) -> None:
        """INV-014, and the reason the previous test is not the whole story.

        The stored value is 241.6999969482422. Printing that would claim thirteen digits for a number
        the file carries seven of, and a reader comparing it against a limit would be comparing noise.
        The value was declared to carry four, so the document says 241.7 - which is the literal that
        was written, arrived at honestly rather than by having been kept.
        """
        _, _, text = a_deliverable(tmp_path)

        assert "241.7" in text
        assert "241.6999969482422" not in text
        assert "241.69999" not in text

    def test_the_reduction_ran_in_double_precision(self, tmp_path: Path) -> None:
        """INV-031, E-143: stored as the file gave it, computed in float64."""
        source = tmp_path / "run12.vtu"
        write_case(source)

        field = reader.read(source).fields["stress"]
        summary = summarise(
            field.values, reduction=Reduction.MAX,
            association=Association.POINT, scope="全体",
        )

        assert summary.value is not None
        # Computed in float64 over what the file **stored** in float32: the reduction does not invent
        # precision the source never had, and it does not fall back to the source's own type either.
        assert isinstance(summary.value, float)
        assert summary.value == float(np.asarray(STRESS, dtype=np.float32).astype(np.float64).max())
        assert summary.value != max(STRESS)


class TestTheUnitCameFromThePersonAndNotTheFile:
    def test_the_file_written_here_carries_no_unit(self, tmp_path: Path) -> None:
        """The premise of XC-003, asserted rather than assumed: if the `.vtu` held a unit somewhere,
        this test would be about VTK and not about this product."""
        source = tmp_path / "run12.vtu"
        write_case(source)

        assert "MPa" not in source.read_text(encoding="utf-8", errors="replace")

    def test_the_read_field_has_no_unit_until_one_is_declared(self, tmp_path: Path) -> None:
        source = tmp_path / "run12.vtu"
        write_case(source)

        assert reader.read(source).fields["stress"].unit is None

    def test_the_deliverable_shows_the_declared_unit(self, tmp_path: Path) -> None:
        _, _, text = a_deliverable(tmp_path)

        assert "MPa" in text


class TestTheDeliverableStandsAlone:
    def test_it_reaches_nothing(self, tmp_path: Path) -> None:
        """AC-001, INV-007. Opened on a machine that may have no network at all."""
        _, _, text = a_deliverable(tmp_path)

        assert "http://" not in text and "https://" not in text

    def test_it_names_the_source_file_and_when_it_last_changed(self, tmp_path: Path) -> None:
        """AC-007, INV-027. Which files is the easier half; the time is what lets a reader tell a
        delivered document from one whose inputs have moved since."""
        _, _, text = a_deliverable(tmp_path)

        assert "run12.vtu" in text
        assert "更新 20" in text

    def test_every_number_is_readable_as_text(self, tmp_path: Path) -> None:
        """AC-002. With the 3D content broken, old, or printed."""
        _, computed, text = a_deliverable(tmp_path)

        table = text[text.index("<table") : text.index("</table>")]

        assert f"{computed:g}" in table
        assert "MPa" in table

    def test_the_limitations_section_is_there(self, tmp_path: Path) -> None:
        _, _, text = a_deliverable(tmp_path)

        assert "制約" in text
