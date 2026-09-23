"""The regression set: every fixture this product's tests generate, in one table, with its format,
its kind and what it proves (XC-307; #203).

Generated at test time by the writers the tests already hold (XC-085), never committed: a file in
the repository is a file whose provenance has to be recorded, and a file the tests write is one
whose provenance is the test. The kinds are the ones a reader is held to - **normal** (a whole file
of the shape a solver writes), **partial** (a case with a part the reader cannot give), **broken**
(a file cut short, random bytes under a right extension, an empty file, an extension nothing
reads) and **large** (a grid of a million cells) - and the gate in test_regression_catalogue.py
holds every reader this build has to a normal fixture and a broken one, and reads every fixture
as its kind says it must read.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from conftest import requires_vtk

requires_vtk()

from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray  # noqa: E402
from vtkmodules.vtkCommonCore import vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, vtkCellArray, vtkUnstructuredGrid  # noqa: E402
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter  # noqa: E402

from demo_case import write_bar, write_cube, write_exodus, write_fields, write_holed, write_partial_case, write_transient_case  # noqa: E402
from engine import sample  # noqa: E402
from test_incomplete_files import write_partitioned, write_polydata  # noqa: E402
from test_reader import write_grid  # noqa: E402

Writer = Callable[[Path], object]

KINDS = ("normal", "partial", "broken", "large", "transient", "missing-values")
#: The kinds every regression set has to hold (#203's condition): whole, partly missing, broken, huge.
REQUIRED_KINDS = ("normal", "partial", "broken", "large")
#: XC-049's Verified tier names formats this build has no reader for yet: said here, held by a test,
#: and tracked as their own work rather than implied by the table.
VERIFIED_WITHOUT_READER = ("EnSight Gold", "VTKHDF")
#: Random bytes under a reader's own extension: what a wrong file, a download cut off or a disk
#: fault leaves. Seeded, so the bytes are the same on every run and a refusal is reproducible.
GARBAGE_SEED = 203
GARBAGE_BYTES = 4096
#: The large grid: hexahedra along each edge, so a million cells and 1,030,301 points.
LARGE_EDGE = 100


@dataclass(frozen=True)
class Fixture:
    """One generated file: where it comes from, what it is, and what a test built on it may claim."""

    id: str
    format: str
    kind: str
    write: Writer
    proves: tuple[str, ...]
    note: str
    #: What the writer needs beyond the toolkit; the gate skips - saying so - where it is absent.
    needs: str = ""

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"{self.id}: kind {self.kind!r} is not one of {KINDS}")
        if not self.format.startswith("."):
            raise ValueError(f"{self.id}: the format is the suffix, with its dot")


def garbage(path: Path) -> None:
    path.write_bytes(random.Random(GARBAGE_SEED).randbytes(GARBAGE_BYTES))


def empty(path: Path) -> None:
    path.write_bytes(b"")


def truncated(write: Writer, fraction: float) -> Writer:
    """The fixture `write` gives, cut to `fraction` of its bytes - what a solver still writing, or a
    copy that stopped, leaves (E-212)."""

    def cut(path: Path) -> None:
        write(path)
        body = path.read_bytes()
        path.write_bytes(body[: int(len(body) * fraction)])

    return cut


def renamed(write_into_directory: Callable[[Path], Path | None]) -> Writer:
    """A writer that chooses its own file name inside a directory, made to write at `path`."""

    def at(path: Path) -> object:
        written = write_into_directory(path.parent)
        if written is None:
            return None
        written.replace(path)
        return path

    return at


def sample_beam(path: Path) -> None:
    sample.write_cantilever(path, force_newton=100.0)


def large_hexahedra(path: Path) -> None:
    """`LARGE_EDGE`^3 hexahedra with one float32 point field, written whole by the toolkit's XML
    writer: 1,030,301 points and 1,000,000 cells, about 20 MB on disk (E-226)."""
    n = LARGE_EDGE
    xs = np.linspace(0.0, 1.0, n + 1)
    grid_x, grid_y, grid_z = np.meshgrid(xs, xs, xs, indexing="ij")
    coordinates = np.column_stack([grid_x.ravel(order="F"), grid_y.ravel(order="F"), grid_z.ravel(order="F")])
    i, j, k = np.meshgrid(np.arange(n), np.arange(n), np.arange(n), indexing="ij")
    i, j, k = i.ravel(order="F"), j.ravel(order="F"), k.ravel(order="F")

    def index(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        return a + (n + 1) * (b + (n + 1) * c)

    corners = np.column_stack([
        index(i, j, k), index(i + 1, j, k), index(i + 1, j + 1, k), index(i, j + 1, k),
        index(i, j, k + 1), index(i + 1, j, k + 1), index(i + 1, j + 1, k + 1), index(i, j + 1, k + 1),
    ]).astype(np.int64)
    connectivity = np.column_stack([np.full(len(corners), 8, dtype=np.int64), corners]).ravel()
    cells = vtkCellArray()
    cells.SetCells(len(corners), numpy_to_vtkIdTypeArray(connectivity, deep=True))
    points = vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(coordinates), deep=True))
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(VTK_HEXAHEDRON, cells)
    temperature = numpy_to_vtk((300.0 + 100.0 * coordinates[:, 0]).astype(np.float32), deep=True)
    temperature.SetName("temperature")
    grid.GetPointData().AddArray(temperature)
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    if not writer.Write():
        raise OSError(f"{path.name} を書けませんでした")


def cgns_minimal(path: Path) -> object:
    from cgns_fixture import write_minimal_cgns

    return write_minimal_cgns(path)


def cgns_transient(path: Path) -> object:
    from cgns_fixture import write_transient_cgns

    return write_transient_cgns(path)


FIXTURES: tuple[Fixture, ...] = (
    # ---- normal: a whole file of the shape a solver writes -------------------------------------
    Fixture("vtu/grid", ".vtu", "normal", write_grid, ("ingest/AC-020",), "two triangles, a point field and a cell field"),
    Fixture("vtu/cube", ".vtu", "normal", write_cube, ("ingest/AC-020", "operations/REQ-001"), "the demo cube with a temperature"),
    Fixture("vtu/fields", ".vtu", "normal", write_fields, ("INV-020",), "a displacement and a symmetric stress with hand-known derived answers"),
    Fixture("vtu/bar", ".vtu", "normal", write_bar, ("XC-292",), "the bar the second case loads"),
    Fixture("vtu/sample-beam", ".vtu", "normal", sample_beam, ("XC-298", "XC-299"), "the shipped cantilever under 100 N, from beam theory"),
    Fixture("pvtu/two-pieces", ".pvtu", "normal", write_partitioned, ("INV-010", "ingest/AC-022"), "a partitioned set of two pieces"),
    Fixture("vtp/sheet", ".vtp", "normal", lambda path: write_polydata(path, xml=True), ("ingest/AC-020",), "a triangle sheet as XML polydata"),
    Fixture("stl/sheet", ".stl", "normal", lambda path: write_polydata(path, xml=False), ("ingest/AC-020", "XC-049"), "the same sheet as STL: geometry only"),
    Fixture("ex2/case", ".ex2", "normal", write_exodus, ("ingest/AC-020", "E-136"), "an Exodus file whose every array is switched on by name"),
    Fixture("cgns/minimal", ".cgns", "normal", cgns_minimal, ("ingest/AC-034", "E-137"), "one base, one zone, one solution, a unit declaration the reader cannot read", needs="h5py"),
    # ---- partial: a case with a part the reader cannot give -----------------------------------
    Fixture("cgns/assembly-partial", ".cgns", "partial", renamed(write_partial_case), ("ingest/AC-027", "XC-272"), "one zone read and one the reader cannot: the case opens partial and says so", needs="h5py"),
    # ---- broken: cut, random, empty, or an extension nothing reads ------------------------------
    Fixture("vtu/cut", ".vtu", "broken", truncated(write_cube, 0.5), ("ingest/AC-022", "E-212"), "the cube cut at half its bytes"),
    Fixture("vtp/cut", ".vtp", "broken", truncated(lambda path: write_polydata(path, xml=True), 0.5), ("ingest/AC-022",), "the sheet cut at half"),
    Fixture("stl/cut", ".stl", "broken", truncated(lambda path: write_polydata(path, xml=False), 0.5), ("ingest/AC-022",), "the STL cut at half"),
    Fixture("ex2/cut", ".ex2", "broken", truncated(write_exodus, 0.5), ("ingest/AC-022", "E-212"), "the Exodus file cut at half: the reader would zero the rest silently"),
    Fixture("cgns/cut", ".cgns", "broken", truncated(cgns_minimal, 0.5), ("ingest/AC-022",), "the CGNS file cut at half", needs="h5py"),
    Fixture("vtu/garbage", ".vtu", "broken", garbage, ("ingest/AC-022",), "random bytes under .vtu"),
    Fixture("pvtu/garbage", ".pvtu", "broken", garbage, ("ingest/AC-022",), "random bytes under .pvtu"),
    Fixture("vtp/garbage", ".vtp", "broken", garbage, ("ingest/AC-022",), "random bytes under .vtp"),
    Fixture("stl/garbage", ".stl", "broken", garbage, ("ingest/AC-022", "E-226"), "random bytes under .stl: read as eighty triangles until the container was checked"),
    Fixture("cgns/garbage", ".cgns", "broken", garbage, ("ingest/AC-022",), "random bytes under .cgns"),
    Fixture("ex2/garbage", ".ex2", "broken", garbage, ("ingest/AC-022",), "random bytes under .ex2"),
    Fixture("vtu/empty", ".vtu", "broken", empty, ("ingest/AC-022",), "an empty file under .vtu"),
    Fixture("pvtu/empty", ".pvtu", "broken", empty, ("ingest/AC-022",), "an empty file under .pvtu"),
    Fixture("vtp/empty", ".vtp", "broken", empty, ("ingest/AC-022",), "an empty file under .vtp"),
    Fixture("stl/empty", ".stl", "broken", empty, ("ingest/AC-022",), "an empty file under .stl"),
    Fixture("cgns/empty", ".cgns", "broken", empty, ("ingest/AC-022",), "an empty file under .cgns"),
    Fixture("ex2/empty", ".ex2", "broken", empty, ("ingest/AC-022",), "an empty file under .ex2"),
    Fixture("sim/unsupported", ".sim", "broken", lambda path: path.write_bytes(b"not a mesh"), ("ingest/AC-021",), "an extension no reader in this build takes"),
    # ---- large ----------------------------------------------------------------------------------
    Fixture("vtu/large-hexahedra", ".vtu", "large", large_hexahedra, ("LIM-001", "E-226"), f"{LARGE_EDGE}^3 hexahedra: a million cells, 1,030,301 points"),
    # ---- the rest a reader is held to ------------------------------------------------------------
    Fixture("cgns/transient", ".cgns", "transient", cgns_transient, ("XC-240", "XC-283"), "two steps the file declares as 0.0 and 0.5", needs="h5py"),
    Fixture("vtu/holed", ".vtu", "missing-values", write_holed, ("XC-303",), "three missing points, one missing component, two missing cells"),
)


def by_kind(kind: str) -> tuple[Fixture, ...]:
    return tuple(one for one in FIXTURES if one.kind == kind)


def by_format(suffix: str) -> tuple[Fixture, ...]:
    return tuple(one for one in FIXTURES if one.format == suffix)


def write_all(directory: Path) -> dict[str, Path | None]:
    """Every fixture into `directory`, by id; None where its writer's need is not met here."""
    written: dict[str, Path | None] = {}
    for fixture in FIXTURES:
        path = directory / f"{fixture.id.replace('/', '-')}{fixture.format}"
        try:
            fixture.write(path)
        except ImportError:
            written[fixture.id] = None
            continue
        written[fixture.id] = path
    return written


__all__ = ["FIXTURES", "Fixture", "KINDS", "REQUIRED_KINDS", "VERIFIED_WITHOUT_READER", "by_format", "by_kind", "write_all"]

# The transient writer is in the table through `cgns_transient`; `write_transient_case` is kept
# importable for callers that want the demo's own name for it.
_ = write_transient_case
