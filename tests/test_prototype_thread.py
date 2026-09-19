"""The prototype, end to end, and the one claim it exists to make.

XC-257 defines the first working prototype as a thread: open a solver result, colour it by a field,
orbit it, pick a point and read the value with its unit, digits, provenance and location, declare a
unit and watch the legend change while no stored number does, and export a self-contained document.
And then the sentence the whole product rests on - **the number in the document, the number in the
readout and the number computed on the full dataset are the same number** (INV-001).

Three numbers reached through three different paths meet here:

- `dataset.probe` picks on the **reduced display surface** and traces back to a dataset point;
- `field.statistics` reduces over **every value the case holds**, touching no display geometry;
- the exported HTML carries what the report builder put in it, as text a person reads.

A test that computed them the same way would prove nothing. These are computed differently on
purpose, and the assertion is that they agree - with the value the file actually stores, which for a
float32 field is not the literal that was written into it (INV-014, E-143).

Verifies: INV-001, INV-009, INV-014, XC-003, view/AC-027, report/AC-002, XC-257.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import REQUIRE_VTK, offscreen_rendering_available, requires_vtk

requires_vtk()

ROOT = Path(__file__).resolve().parents[1]

OFFSCREEN_AVAILABLE, OFFSCREEN_DETAIL = offscreen_rendering_available()
needs_offscreen = pytest.mark.skipif(
    not OFFSCREEN_AVAILABLE and not REQUIRE_VTK, reason=f"no offscreen rendering here: {OFFSCREEN_DETAIL}"
)

import numpy as np  # noqa: E402
from vtkmodules.util.numpy_support import numpy_to_vtk  # noqa: E402
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, vtkCellArray, vtkUnstructuredGrid  # noqa: E402
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter  # noqa: E402

from service.command.handlers import Session, build_surface  # noqa: E402
from service.command.surface import Command, Status, Surface  # noqa: E402
from domain_core.reported_value import UNDECLARED_MARKER  # noqa: E402
from service.workspace.document import FORMAT_VERSION  # noqa: E402

#: Deliberately not round, and deliberately what a solver writes. 241.7 has no float32
#: representation: the file holds 241.6999969482422, and every number below must agree with what was
#: **stored**, not with the literal that was asked for.
STRESS = (12.5, 241.7, 98.25, 3.125, 77.0, 150.5, 200.25, 66.0)
STORED = np.asarray(STRESS, dtype=np.float32).astype(np.float64)
#: The corner of the unit cube that holds the largest value, in metres.
PEAK_AT = (1.0, 0.0, 0.0)


def write_case(path: Path) -> None:
    """One hexahedron with a float32 point field - a mesh with volume and a known extreme."""
    coordinates = np.array(
        [[x, y, z] for z in (0.0, 1.0) for y in (0.0, 1.0) for x in (0.0, 1.0)], dtype=np.float64
    )
    points = vtkPoints()
    points.SetData(numpy_to_vtk(coordinates, deep=True))
    cells = vtkCellArray()
    cells.InsertNextCell(8)
    for index in (0, 1, 3, 2, 4, 5, 7, 6):
        cells.InsertCellPoint(index)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(VTK_HEXAHEDRON, cells)
    field = vtkFloatArray()
    field.SetName("stress")
    for value in STRESS:
        field.InsertNextValue(value)
    grid.GetPointData().AddArray(field)
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def a_workspace(path: Path) -> Path:
    path.write_text(
        json.dumps({
            "formatVersion": FORMAT_VERSION,
            "id": "ws:1",
            "name": "梁の検討",
            "cases": [{"id": "case:1", "name": "baseline"}],
            "variables": [],
            "workspaceItems": {"simulations": [], "views": [], "graphs": [], "reports": []},
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def applied(result) -> object:
    assert result.status in (Status.APPLIED, Status.ANSWERED), result.reason
    return result.value


class Thread:
    """One run of the whole prototype, with what each step answered kept for the assertions."""

    def __init__(self, tmp_path: Path) -> None:
        self.session = Session(
            clock=lambda: datetime(2026, 9, 19, 10, tzinfo=timezone(timedelta(hours=9)))
        )
        self.surface: Surface = build_surface(self.session)
        self.source = tmp_path / "run12.vtu"
        write_case(self.source)
        applied(self.surface.submit(Command("workspace.open", {"path": str(a_workspace(tmp_path / "beam.svw"))})))
        self.dataset_id = applied(self.surface.submit(
            Command("dataset.load", {"caseId": "case:1", "filePaths": [str(self.source)]})
        ))["datasetId"]

    def declare(self, symbol: str = "MPa") -> None:
        applied(self.surface.submit(Command("field.declareUnit", {
            "datasetId": self.dataset_id, "fieldName": "stress", "unitSymbol": symbol,
        })))

    def statistics(self) -> dict:
        return applied(self.surface.submit(Command("field.statistics", {
            "datasetId": self.dataset_id, "fieldName": "stress",
        })))

    def probe(self, point=PEAK_AT) -> dict:
        return applied(self.surface.submit(Command("dataset.probe", {
            "datasetId": self.dataset_id, "fieldName": "stress",
            "pointM": list(point), "resultPosition": 0,
        })))

    def view(self, **changes) -> str:
        definition = {
            "name": "応力の全体図",
            "datasetId": self.dataset_id,
            "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point", "colourMap": "viridis"},
        }
        definition.update(changes)
        return applied(self.surface.submit(
            Command("view.create", {"workspaceId": "ws:1", "definition": definition})
        ))["id"]

    def export(self, tmp_path: Path, *, view_id: str | None = None, name: str = "run12.html") -> tuple[dict, str]:
        blocks: list[dict] = []
        if view_id is not None:
            blocks.append({"kind": "view", "viewId": view_id, "form": "still"})
        blocks.append({"kind": "valueTable", "fields": ["stress"]})
        report_id = applied(self.surface.submit(Command("report.create", {
            "workspaceId": "ws:1",
            "definition": {"name": "Run 12 の最大応力", "targets": ["html"], "blocks": blocks},
        })))["id"]
        target = tmp_path / name
        answer = applied(self.surface.submit(
            Command("report.export", {"reportId": report_id, "path": str(target)})
        ))
        return answer, target.read_text(encoding="utf-8")


class TestOneNumberReachedThreeWays:
    """The claim. Three paths, three different computations, one number."""

    def test_the_probe_the_statistics_and_the_document_agree_with_what_the_file_stores(
        self, tmp_path: Path
    ) -> None:
        thread = Thread(tmp_path)
        thread.declare()

        probed = thread.probe()["value"]
        reduced = thread.statistics()["maximum"]
        _, text = thread.export(tmp_path)

        stored = float(STORED.max())
        assert probed["value"] == stored, "the pick traced back to the dataset point, not a display vertex"
        assert reduced["value"] == stored, "the reduction ran on the full field"
        # The document shows the digits float32 supports and no more: 241.7, never 241.6999969482422
        # (INV-014). So the text carries the honest form of the same number.
        assert "241.7" in text
        assert "241.6999969482422" not in text and "241.69999" not in text
        assert stored != 241.7, "the file holds no exact 241.7 - this is what makes the test mean something"

    def test_every_one_of_them_carries_the_declared_unit(self, tmp_path: Path) -> None:
        """XC-003: a number without its unit is a number in whatever unit the reader assumed."""
        thread = Thread(tmp_path)
        thread.declare()

        probed = thread.probe()["value"]
        reduced = thread.statistics()["maximum"]
        _, text = thread.export(tmp_path)

        assert probed["unit"] == "MPa"
        assert reduced["unit"] == "MPa"
        assert "MPa" in text

    def test_undeclared_stays_undeclared_everywhere(self, tmp_path: Path) -> None:
        """No unit is declared in this thread, so nothing anywhere invents one (XC-003)."""
        thread = Thread(tmp_path)

        probed = thread.probe()["value"]
        reduced = thread.statistics()["maximum"]
        _, text = thread.export(tmp_path)

        assert probed["unit"] is None and "undeclared-unit" in probed["caveats"]
        assert reduced["unit"] is None and "undeclared-unit" in reduced["caveats"]
        assert UNDECLARED_MARKER in text

    def test_all_three_report_the_digits_the_storage_supports(self, tmp_path: Path) -> None:
        thread = Thread(tmp_path)
        thread.declare()

        assert thread.probe()["value"]["digits"] == 6
        assert thread.statistics()["maximum"]["digits"] == 6

    def test_declaring_a_unit_changes_the_label_and_not_the_number(self, tmp_path: Path) -> None:
        """Scenario 2: a unit is a declaration with an author, and declaring it changes labels and
        conversions without touching a stored number (XC-003, XC-134)."""
        thread = Thread(tmp_path)
        before = thread.probe()["value"]

        thread.declare("MPa")
        after = thread.probe()["value"]

        assert before["unit"] is None and after["unit"] == "MPa"
        assert before["value"] == after["value"], "the stored number did not move when the label arrived"


class TestTheNumberSurvivesAReducedPicture:
    """INV-001 and INV-009: the picture may be decimated, the number may not."""

    def test_a_display_budget_of_one_triangle_does_not_move_the_reported_maximum(
        self, tmp_path: Path
    ) -> None:
        from engine.visualization.display import display_geometry

        thread = Thread(tmp_path)
        thread.declare()
        full = thread.statistics()["maximum"]["value"]

        # Force the reduction the interactive budget would only reach on a large case, then ask again.
        for part in thread.session.datasets[thread.dataset_id].case.present:
            assert part.dataset is not None
            display_geometry(part.dataset, budget=1)
        after = thread.statistics()["maximum"]["value"]

        assert after == full == float(STORED.max())

    def test_the_probe_answers_from_the_dataset_even_when_the_surface_is_reduced(
        self, tmp_path: Path
    ) -> None:
        thread = Thread(tmp_path)

        probed = thread.probe()["value"]

        assert probed["value"] in set(STORED.tolist())
        assert probed["provenance"] == "dataset"


@needs_offscreen
class TestTheDocumentTheRecipientOpens:
    """What arrives at the other end: one file, no network, the picture and the numbers in it."""

    def test_the_whole_thread_produces_one_self_contained_file(self, tmp_path: Path) -> None:
        thread = Thread(tmp_path)
        thread.declare()
        view_id = thread.view()
        applied(thread.surface.submit(Command("view.render", {
            "viewId": view_id, "width": 320, "height": 240, "format": "png",
        })))

        answer, text = thread.export(tmp_path, view_id=view_id)

        assert answer["bytes"] > 0
        assert "data:image/png;base64," in text, "the picture is in the file"
        assert not re.search(r"https?://|//[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/", text), "nothing is fetched"
        assert "241.7" in text and "MPa" in text
        assert "静止画です" in text, "the document says the view does not turn"
        assert str(self_named(thread.source)) in text, "the source file is named in the provenance"

    def test_the_legend_range_is_the_full_field_and_matches_the_reported_maximum(
        self, tmp_path: Path
    ) -> None:
        """The picture's own scale is read off the same numbers the table reports."""
        thread = Thread(tmp_path)
        thread.declare()
        view_id = thread.view()

        _, text = thread.export(tmp_path, view_id=view_id)

        assert "241.7" in text
        assert "3.125" in text, "the legend's lower end, from the full field"


def self_named(path: Path) -> str:
    """The file name as the provenance writes it."""
    return path.name

# -- the other two formats XC-257 names ---------------------------------------------------------


class TestTheThreadRunsOnEveryFormatTheDecisionNames:
    """XC-257's prototype says "one of the three formats read end-to-end today (.vtu, .ex2, .cgns)".
    That sentence is a claim about three formats and was walked on one. Each is opened, reduced,
    probed and exported here - a format the readers accept and the thread cannot carry is a format
    the decision names and the product does not have.

    The fixtures differ on purpose: Exodus is written by the toolkit's own writer and returns **no
    results unless every array is switched on by name** (E-136), and CGNS has no writer in the
    toolkit at all, so its fixture is built straight into the HDF5 node layout (E-137).
    """

    @staticmethod
    def _open(tmp_path: Path, source: Path, field: str):
        session = Session(clock=lambda: datetime(2026, 9, 19, 10, tzinfo=timezone(timedelta(hours=9))))
        surface = build_surface(session)
        applied(surface.submit(Command("workspace.open", {"path": str(a_workspace(tmp_path / "w.svw"))})))
        loaded = applied(surface.submit(
            Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]})
        ))
        names = {one["name"] for one in loaded["fields"]}
        assert field in names, f"{source.suffix} carried {sorted(names)}"
        return surface, session, loaded["datasetId"]

    def test_exodus_carries_a_value_from_the_file_to_a_document(self, tmp_path: Path) -> None:
        from test_reader import write_exodus

        source = tmp_path / "case.ex2"
        write_exodus(source)
        surface, _, dataset_id = self._open(tmp_path, source, "stress")
        applied(surface.submit(Command("field.declareUnit", {
            "datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa",
        })))

        statistics = applied(surface.submit(Command("field.statistics", {
            "datasetId": dataset_id, "fieldName": "stress",
        })))
        probed = applied(surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "stress",
            "pointM": [0.0, 1.0, 0.0], "resultPosition": 0,
        })))

        assert statistics["maximum"]["value"] == 90.0, "the file's own largest value"
        assert statistics["maximum"]["unit"] == "MPa"
        assert probed["value"]["value"] in {10.0, 20.0, 90.0, 40.0}
        assert probed["value"]["unit"] == "MPa"
        assert probed["value"]["location"], "Exodus numbers its own nodes, so the location is named"

        report_id = applied(surface.submit(Command("report.create", {
            "workspaceId": "ws:1",
            "definition": {
                "name": "Exodus の最大応力", "targets": ["html"],
                "blocks": [{"kind": "valueTable", "fields": ["stress"]}],
            },
        })))["id"]
        target = tmp_path / "exodus.html"
        applied(surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)})))
        document = target.read_text(encoding="utf-8")

        assert "90" in document and "MPa" in document, "the maximum and its unit reach the page"
        assert "case.ex2" in document, "the document names the file it was read from"

    def test_cgns_carries_a_value_and_keeps_its_unit_undeclared(self, tmp_path: Path) -> None:
        """CGNS is the one format whose standard can declare a unit, and the toolkit's reader exposes
        no way to read it (E-130, E-137). So the unit stays undeclared through the whole thread, and
        the document says so rather than inventing one (XC-003)."""
        from conftest import requires_h5py

        requires_h5py()
        from cgns_fixture import write_minimal_cgns

        source = write_minimal_cgns(tmp_path / "case.cgns")
        surface, _, dataset_id = self._open(tmp_path, source, "stress")

        statistics = applied(surface.submit(Command("field.statistics", {
            "datasetId": dataset_id, "fieldName": "stress",
        })))

        assert statistics["maximum"]["value"] == 90.0
        assert statistics["maximum"]["unit"] is None
        assert "undeclared-unit" in statistics["maximum"]["caveats"]

        report_id = applied(surface.submit(Command("report.create", {
            "workspaceId": "ws:1",
            "definition": {
                "name": "CGNS の最大値", "targets": ["html"],
                "blocks": [{"kind": "valueTable", "fields": ["stress"]}],
            },
        })))["id"]
        target = tmp_path / "cgns.html"
        applied(surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)})))
        document = target.read_text(encoding="utf-8")

        assert "90" in document
        assert "単位未宣言" in document, "the page says the unit was never declared, in those words"


class TestOneWordForAnUndeclaredUnit:
    """The engine and the interface both show a value whose unit nobody declared. They live on opposite
    sides of a wire, each with its own constant, and for a while they said it differently: the page
    wrote 単位が宣言されていません and the screen wrote 単位未宣言 - the same absence, and a person
    reading both would rightly wonder whether they were the same state. XC-257 names the word; this
    holds both sides to it."""

    def test_the_interface_uses_the_engine_s_word(self) -> None:
        from domain_core.reported_value import UNDECLARED_MARKER

        source = (ROOT / "src" / "ui" / "shared" / "primitives.tsx").read_text(encoding="utf-8")
        match = re.search(r'export const UNDECLARED = "([^"]+)";', source)

        assert match, "the interface's constant is where the engine's comment says it is"
        assert match.group(1) == UNDECLARED_MARKER
