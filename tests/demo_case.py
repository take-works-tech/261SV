"""The smallest case the prototype thread can be walked on, written where a caller asks.

One hexahedron with a float32 point field 1..8 (a mesh with volume, so dual weights exist), and a
workspace with one case that names it. Used three ways, from one definition:

  - `tests/test_handlers.py` and the tests that import from it, in-process;
  - `python tests/demo_case.py <directory>`, from the interface's own test, which runs under Node and
    needs the files on disk before it starts a real engine against them;
  - by hand, to have something to open in a development build.

A second copy of `write_cube` for the interface's side would be a second answer to what the demo
case is, and the two would drift the day one of them was edited.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, VTK_TRIANGLE, vtkCellArray, vtkUnstructuredGrid
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from service.workspace.document import FORMAT_VERSION  # noqa: E402


def write_cube(path: Path) -> None:
    """One hexahedron, a float32 point field 1..8 - a mesh with volume, so dual weights exist."""
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
    field.SetName("temperature")
    for value in range(1, 9):
        field.InsertNextValue(float(value))
    grid.GetPointData().AddArray(field)
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def write_exodus(path: Path, *, results: bool = True) -> None:
    """A two-triangle Exodus file, written by the toolkit's own writer (XC-085). The writer takes
    the path as a narrow string on Windows: at a path with Japanese in it, outside the UTF-8 code
    page, it creates nothing (E-216) - write where it can and copy."""
    from vtkmodules.vtkIOExodus import vtkExodusIIWriter

    points = vtkPoints()
    for x, y in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)):
        points.InsertNextPoint(x, y, 0.0)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    for triangle in ([0, 1, 2], [1, 3, 2]):
        grid.InsertNextCell(VTK_TRIANGLE, 3, triangle)

    if results:
        for name, values in (("stress", [10.0, 20.0, 90.0, 40.0]), ("temp", [1.0, 2.0, 3.0, 4.0])):
            array = numpy_to_vtk(np.array(values), deep=True)
            array.SetName(name)
            grid.GetPointData().AddArray(array)
        cells = numpy_to_vtk(np.array([7.0, 8.0]), deep=True)
        cells.SetName("elem_stress")
        grid.GetCellData().AddArray(cells)

    writer = vtkExodusIIWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.WriteAllTimeStepsOn()
    writer.Write()


def write_fields(path: Path) -> None:
    """`fields.vtu`: the two-triangle grid carrying a three-component displacement and a six-component
    symmetric stress, each row with a derived answer known by hand (15_derived_quantities): magnitudes
    5, 0, 3, 7; von Mises 100, 86.60, 0, 173.2; principal values 100/0/0, 50/0/-50, 10/10/10, 200/100/0."""
    coordinates = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
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
    displacement = vtkFloatArray()
    displacement.SetName("displacement")
    displacement.SetNumberOfComponents(3)
    for row in ((3.0, 4.0, 0.0), (0.0, 0.0, 0.0), (1.0, 2.0, 2.0), (2.0, 3.0, 6.0)):
        displacement.InsertNextTuple3(*row)
    grid.GetPointData().AddArray(displacement)
    stress = vtkFloatArray()
    stress.SetName("stress6")
    stress.SetNumberOfComponents(6)
    for row in (
        (100.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 50.0, 0.0, 0.0),
        (10.0, 10.0, 10.0, 0.0, 0.0, 0.0), (200.0, 100.0, 0.0, 0.0, 0.0, 0.0),
    ):
        stress.InsertNextTuple6(*row)
    grid.GetPointData().AddArray(stress)
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def write_bar(path: Path) -> None:
    """E-144's measurement as a file: five hexahedra in a row carrying element values 10, 20, 200,
    20, 10 - a concentration inside the body. Averaged onto the shared nodes its maximum is 110
    against 200, and the spread at that node is 180 (INV-032)."""
    cell_values = (10.0, 20.0, 200.0, 20.0, 10.0)
    count = len(cell_values)
    coordinates = np.array(
        [[float(index), y, z] for index in range(count + 1) for y in (0.0, 1.0) for z in (0.0, 1.0)],
        dtype=np.float64,
    )
    points = vtkPoints()
    points.SetData(numpy_to_vtk(coordinates, deep=True))

    def node(index: int, y: int, z: int) -> int:
        return index * 4 + y * 2 + z

    cells = vtkCellArray()
    for index in range(count):
        cells.InsertNextCell(8)
        for corner in (
            node(index, 0, 0), node(index + 1, 0, 0), node(index + 1, 1, 0), node(index, 1, 0),
            node(index, 0, 1), node(index + 1, 0, 1), node(index + 1, 1, 1), node(index, 1, 1),
        ):
            cells.InsertCellPoint(corner)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(VTK_HEXAHEDRON, cells)
    field = vtkFloatArray()
    field.SetName("stress")
    for value in cell_values:
        field.InsertNextValue(value)
    grid.GetCellData().AddArray(field)
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def write_two_blocks(path: Path) -> None:
    """Two triangles and a quad in an Exodus file: the toolkit's writer puts each cell type in its
    own element block, and the reader returns them as two parts under `Element Blocks` - a case
    with a hierarchy and two parts to show or hide (INV-019). Measured here on 2026-09-20 rather
    than assumed; the block names are the writer's, and a test reads them back rather than
    spelling them."""
    from vtkmodules.vtkCommonDataModel import VTK_QUAD, VTK_TRIANGLE
    from vtkmodules.vtkIOExodus import vtkExodusIIWriter

    points = vtkPoints()
    for x, y in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0), (2.0, 0.0), (2.0, 1.0)):
        points.InsertNextPoint(x, y, 0.0)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    for triangle in ([0, 1, 2], [1, 3, 2]):
        grid.InsertNextCell(VTK_TRIANGLE, 3, triangle)
    grid.InsertNextCell(VTK_QUAD, 4, [1, 4, 5, 3])
    field = numpy_to_vtk(np.array([10.0, 20.0, 90.0, 40.0, 50.0, 60.0]), deep=True)
    field.SetName("stress")
    grid.GetPointData().AddArray(field)
    writer = vtkExodusIIWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def write_workspace(path: Path) -> Path:
    """A workspace document with one case and nothing in it yet."""
    path.write_text(
        json.dumps(
            {
                "formatVersion": FORMAT_VERSION,
                "id": "ws:1",
                "name": "梁の検討",
                "cases": [{"id": "case:1", "name": "baseline"}],
                "variables": [],
                "workspaceItems": {"simulations": [], "views": [], "graphs": [], "reports": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def write_demo_case(directory: Path) -> tuple[Path, Path]:
    """`beam.svw` and `cube.vtu` in the directory; returns both paths."""
    directory.mkdir(parents=True, exist_ok=True)
    workspace = write_workspace(directory / "beam.svw")
    cube = directory / "cube.vtu"
    write_cube(cube)
    return workspace, cube


def write_partial_case(directory: Path) -> Path | None:
    """`assembly.cgns`: one zone the reader reads and one it cannot - a case the product opens as
    partial and says so (AC-027, XC-272). None where h5py, which writes the fixture, is not here.
    """
    try:
        import h5py
        from cgns_fixture import node, text, write_minimal_cgns
    except ImportError:
        return None
    path = write_minimal_cgns(directory / "assembly.cgns")
    with h5py.File(path, "a") as handle:
        ghost = node(handle["Base"], "Ghost", "Zone_t", np.array([[4, 2, 0]], dtype=np.int32), "I4")
        node(ghost, "ZoneType", "ZoneType_t", text("Unstructured"), "C1")
    return path


def write_transient_case(directory: Path) -> Path | None:
    """`transient.cgns`: the transient fixture of `tests/cgns_fixture.py` - two steps the file declares
    as `0.0` and `0.5` without saying what they are, `stress` one higher at the second (XC-240,
    XC-283). None where h5py, which writes the fixture, is not here.
    """
    try:
        from cgns_fixture import write_transient_cgns
    except ImportError:
        return None
    return write_transient_cgns(directory / "transient.cgns")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python tests/demo_case.py <directory>", file=sys.stderr)
        return 2
    workspace, cube = write_demo_case(Path(argv[0]))
    partial = write_partial_case(Path(argv[0]))
    bar = Path(argv[0]) / "bar.vtu"
    write_bar(bar)
    fields = Path(argv[0]) / "fields.vtu"
    write_fields(fields)
    transient = write_transient_case(Path(argv[0]))
    print(json.dumps({
        "workspace": str(workspace), "cube": str(cube), "partial": str(partial) if partial else None,
        "bar": str(bar), "fields": str(fields), "transient": str(transient) if transient else None,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
