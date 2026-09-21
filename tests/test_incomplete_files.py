"""A file that is not all there is not a result (ingest/AC-022, AC-046, XC-284; #263).

A solver writing into a watched folder produces, for minutes at a time, a file that is a valid
prefix of a result. What each reader does with such a file was measured here (E-212): most refuse
it, the XML readers accept one cut inside its closing tag with every value intact - and the Exodus
reader accepts one cut anywhere in its last ten per cent, returning every point, cell and field name
with the values zeroed, silently. So the check is of the container's own statement of its length,
before the read; and a file that does not hold still while it is read, or has changed since it was
loaded, is refused rather than read as a mixture.

The fixtures are written by this test code (XC-085) and cut by it, so the measurement is repeated on
every run rather than remembered.
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import pytest
from conftest import requires_h5py, requires_vtk

requires_vtk()

import numpy as np  # noqa: E402
from vtkmodules.util.numpy_support import numpy_to_vtk  # noqa: E402
from vtkmodules.vtkCommonCore import vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE, vtkCellArray, vtkPolyData, vtkUnstructuredGrid  # noqa: E402
from vtkmodules.vtkIOGeometry import vtkSTLWriter  # noqa: E402
from vtkmodules.vtkIOParallelXML import vtkXMLPUnstructuredGridWriter  # noqa: E402
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter, vtkXMLUnstructuredGridReader  # noqa: E402

from engine import reader  # noqa: E402
from engine.completeness import FileIncomplete, ResultsLost, check_file_is_whole, netcdf_declared_length  # noqa: E402
from demo_case import write_cube  # noqa: E402
from test_reader import write_exodus, write_grid  # noqa: E402

CUTS = (0.5, 0.8, 0.9, 0.95, 0.99, 0.999)


def write_polydata(path: Path, *, xml: bool) -> None:
    """A 20 x 20 sheet of triangles, as `.vtp` or binary `.stl`: big enough to cut anywhere."""
    points = vtkPoints()
    for x in range(20):
        for y in range(20):
            points.InsertNextPoint(float(x), float(y), 0.0)
    cells = vtkCellArray()
    for x in range(19):
        for y in range(19):
            corner = x * 20 + y
            for triangle in ((corner, corner + 20, corner + 1), (corner + 1, corner + 20, corner + 21)):
                cells.InsertNextCell(3)
                for index in triangle:
                    cells.InsertCellPoint(index)
    sheet = vtkPolyData()
    sheet.SetPoints(points)
    sheet.SetPolys(cells)
    writer = vtkXMLPolyDataWriter() if xml else vtkSTLWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(sheet)
    writer.Write()


def write_partitioned(path: Path) -> None:
    """A `.pvtu` of two pieces, written by the toolkit's own parallel writer."""
    grid = vtkUnstructuredGrid()
    points = vtkPoints()
    for x, y in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)):
        points.InsertNextPoint(x, y, 0.0)
    grid.SetPoints(points)
    for triangle in ([0, 1, 2], [1, 3, 2]):
        grid.InsertNextCell(VTK_TRIANGLE, 3, triangle)
    stress = numpy_to_vtk(np.array([10.0, 20.0, 90.0, 40.0]), deep=True)
    stress.SetName("stress")
    grid.GetPointData().AddArray(stress)
    writer = vtkXMLPUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetNumberOfPieces(2)
    writer.SetStartPiece(0)
    writer.SetEndPiece(1)
    writer.SetInputData(grid)
    writer.Write()


def write_cgns(path: Path) -> None:
    requires_h5py()
    from cgns_fixture import write_minimal_cgns

    write_minimal_cgns(path)


FORMATS = {
    "vtu": ("grid.vtu", write_grid),
    "vtu-hexahedra": ("cube.vtu", write_cube),
    "vtp": ("sheet.vtp", lambda path: write_polydata(path, xml=True)),
    "stl": ("sheet.stl", lambda path: write_polydata(path, xml=False)),
    "ex2": ("case.ex2", write_exodus),
    "cgns": ("case.cgns", write_cgns),
}

#: What a cut file may do: be refused by one of these, or read as the complete file. Nothing else.
REFUSALS = (reader.UnreadableFileError, ResultsLost, FileIncomplete)


def arrays_of(case) -> dict[str, np.ndarray]:
    found: dict[str, np.ndarray] = {}
    for index, part in enumerate(one for one in case.present if one.dataset is not None):
        found[f"{index}/points"] = np.asarray(part.dataset.points_m)
        for name, field in part.dataset.fields.items():
            found[f"{index}/{name}"] = np.asarray(field.values)
    return found


def assert_refused_or_complete(cut: Path, complete) -> str:
    """The one outcome a cut file may not have: reading as something other than the complete file."""
    try:
        case = reader.read_case(cut)
    except REFUSALS as refusal:
        return f"refused: {type(refusal).__name__}"
    whole, partial = arrays_of(complete), arrays_of(case)
    assert set(whole) == set(partial), f"{cut.name} read with other arrays: {sorted(partial)} vs {sorted(whole)}"
    for key in whole:
        assert whole[key].shape == partial[key].shape, f"{cut.name}: {key} has another shape"
        assert np.array_equal(whole[key], partial[key], equal_nan=True), f"{cut.name}: {key} read with other values"
    return "read, identical to the complete file"


@pytest.mark.parametrize("format_name", sorted(FORMATS))
def test_a_file_cut_short_is_refused_or_reads_as_the_complete_file(tmp_path: Path, format_name: str) -> None:
    """AC-022 for every format this build reads: at six cuts and at one byte short, the reader either
    refuses or answers exactly what the complete file holds. Before XC-284 the Exodus reader answered
    zeros at every cut from 90 per cent on (E-212)."""
    name, write = FORMATS[format_name]
    full = tmp_path / name
    write(full)
    body = full.read_bytes()
    complete = reader.read_case(full)
    outcomes = []
    for fraction in CUTS:
        cut = tmp_path / f"cut_{int(fraction * 1000)}{full.suffix}"
        cut.write_bytes(body[: int(len(body) * fraction)])
        outcomes.append(assert_refused_or_complete(cut, complete))
    short = tmp_path / f"short{full.suffix}"
    short.write_bytes(body[:-1])
    outcomes.append(assert_refused_or_complete(short, complete))
    assert any(one.startswith("refused") for one in outcomes), outcomes


def test_a_partitioned_set_with_a_piece_cut_short_is_refused_or_reads_whole(tmp_path: Path) -> None:
    manifest = tmp_path / "run.pvtu"
    write_partitioned(manifest)
    complete = reader.read_case(manifest)
    piece = next(tmp_path.rglob("run_1.vtu"))
    body = piece.read_bytes()
    for fraction in (0.5, 0.9, 0.99):
        piece.write_bytes(body[: int(len(body) * fraction)])
        assert_refused_or_complete(manifest, complete)
    piece.write_bytes(body)
    text = manifest.read_bytes()
    manifest.write_bytes(text[: len(text) // 2])
    with pytest.raises(REFUSALS):
        reader.read_case(manifest)


class TestTheContainerSaysHowLongItIs:
    """E-212: the Exodus reader zero-fills a cut file and says nothing, so the NetCDF classic header
    is read first, and a file shorter than the header declares is refused before the read."""

    def test_a_complete_file_is_exactly_as_long_as_its_header_declares(self, tmp_path: Path) -> None:
        write_exodus(tmp_path / "case.ex2")
        body = (tmp_path / "case.ex2").read_bytes()

        assert netcdf_declared_length(body) == len(body)
        check_file_is_whole(tmp_path / "case.ex2")

    @pytest.mark.parametrize("fraction", (0.9, 0.95, 0.99, 0.999))
    def test_a_cut_the_reader_would_zero_fill_is_refused_with_both_lengths(self, tmp_path: Path, fraction: float) -> None:
        write_exodus(tmp_path / "case.ex2")
        body = (tmp_path / "case.ex2").read_bytes()
        cut = tmp_path / "cut.ex2"
        cut.write_bytes(body[: int(len(body) * fraction)])

        with pytest.raises(FileIncomplete) as refusal:
            reader.read_case(cut)

        assert f"{len(body)} バイト" in str(refusal.value) and f"{cut.stat().st_size} バイト" in str(refusal.value)
        assert "0 で埋めて" in str(refusal.value)

    def test_a_header_that_does_not_say_is_not_a_statement_that_the_file_is_whole(self, tmp_path: Path) -> None:
        write_exodus(tmp_path / "case.ex2")
        body = bytearray((tmp_path / "case.ex2").read_bytes())

        assert netcdf_declared_length(b"\x89HDF\r\n\x1a\n" + bytes(32)) is None, "HDF5 checks itself"
        assert netcdf_declared_length(b"") is None
        assert netcdf_declared_length(body[:40]) is None, "a header cut short says nothing"
        body[4:8] = b"\xff\xff\xff\xff"  # the streaming marker: the record count is not in the header
        assert netcdf_declared_length(bytes(body)) is None


class Growing(vtkXMLUnstructuredGridReader):
    """A reader whose file grows under it: what a solver writing into the folder looks like."""

    def Update(self) -> None:  # noqa: N802 - the toolkit's own name
        with open(self.GetFileName(), "ab") as handle:
            handle.write(b"\n")
        super().Update()


class TestAFileMustHoldStill:
    """AC-046: the fingerprint - size and modification time of every file involved - is taken before
    the read and after it, and a difference is a refusal that names what moved."""

    def test_a_file_that_changes_while_it_is_read_is_refused_by_name(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        path = tmp_path / "case.vtu"
        write_grid(path)
        choice = reader._READERS[".vtu"]
        monkeypatch.setitem(reader._READERS, ".vtu", dataclasses.replace(choice, factory=Growing))

        with pytest.raises(reader.FileChanged) as refusal:
            reader.read_case(path)

        assert "読んでいる間に変わりました" in str(refusal.value)
        assert "case.vtu" in str(refusal.value) and "バイト" in str(refusal.value)
        with pytest.raises(reader.UnreadableFileError):
            reader.read(path)

    def test_a_file_that_changed_since_it_was_loaded_is_not_read_again(self, tmp_path: Path) -> None:
        path = tmp_path / "case.vtu"
        write_grid(path)
        loaded = reader.snapshot(path)
        reader.read_case(path, expected=loaded)
        with open(path, "ab") as handle:
            handle.write(b"\n")
        os.utime(path, ns=(loaded["case.vtu"][1] + 2_000_000_000, loaded["case.vtu"][1] + 2_000_000_000))

        with pytest.raises(reader.FileChanged) as refusal:
            reader.read_case(path, expected=loaded)

        assert "読み込んだあとに変わりました" in str(refusal.value)
        assert f"{loaded['case.vtu'][0]}→{path.stat().st_size} バイト" in str(refusal.value)

    def test_a_partitioned_set_s_fingerprint_covers_its_pieces(self, tmp_path: Path) -> None:
        manifest = tmp_path / "run.pvtu"
        write_partitioned(manifest)

        fingerprint = reader.snapshot(manifest)

        assert set(fingerprint) == {"run.pvtu", "run_0.vtu", "run_1.vtu"}
        # The toolkit's parallel reader concatenates the pieces itself: two of four points each.
        assert reader.read_case(manifest, expected=fingerprint).present[0].dataset.point_count == 8
