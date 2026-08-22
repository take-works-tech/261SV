"""Tests for the reader entry point.

Every test here corresponds to an acceptance criterion, and the fixtures are written by this test code
rather than collected, so they carry no third-party terms (XC-085).

Verifies: ingest/AC-020, AC-021, AC-022, AC-023, AC-028.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

import numpy as np  # noqa: E402

from domain_core.dataset import Association, AssociationError  # noqa: E402
from engine import reader  # noqa: E402
from vtkmodules.util.numpy_support import numpy_to_vtk  # noqa: E402
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkUnstructuredGrid, VTK_TRIANGLE  # noqa: E402
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter  # noqa: E402


def write_grid(path: Path, *, with_cell_field: bool = True) -> None:
    """A two-triangle grid carrying one point field and one cell field, written by the toolkit."""
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

    point_field = vtkFloatArray()
    point_field.SetName("stress")
    for value in (10.0, 20.0, 30.0, 40.0):
        point_field.InsertNextValue(value)
    grid.GetPointData().AddArray(point_field)

    if with_cell_field:
        cell_field = vtkFloatArray()
        cell_field.SetName("element_stress")
        for value in (100.0, 200.0):
            cell_field.InsertNextValue(value)
        grid.GetCellData().AddArray(cell_field)

    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


def test_reads_a_grid_and_lists_its_fields(tmp_path: Path) -> None:
    """ingest/AC-020: every field is listed with its association."""
    path = tmp_path / "case.vtu"
    write_grid(path)

    dataset = reader.read(path)

    assert dataset.point_count == 4
    assert dataset.cell_count == 2
    assert set(dataset.fields) == {"stress", "element_stress"}
    assert dataset.field("stress").association is Association.POINT
    assert dataset.field("element_stress").association is Association.CELL


def test_no_unit_is_declared_on_load(tmp_path: Path) -> None:
    """ingest/AC-023: units come from a person, never from the file or the field name."""
    path = tmp_path / "case.vtu"
    write_grid(path)

    dataset = reader.read(path)

    assert all(field.unit is None for field in dataset.fields.values())


def test_cell_data_is_not_promoted_to_points(tmp_path: Path) -> None:
    """INV-003: reading a cell field as point data changes values, so it raises instead."""
    path = tmp_path / "case.vtu"
    write_grid(path)

    dataset = reader.read(path)

    with pytest.raises(AssociationError):
        dataset.field("element_stress").as_point_data()
    assert dataset.field("element_stress").as_cell_data().tolist() == [100.0, 200.0]


def test_source_frame_is_recorded(tmp_path: Path) -> None:
    """ingest/AC-028: what was applied to reach the canonical frame is recorded, not assumed."""
    path = tmp_path / "case.vtu"
    write_grid(path)

    dataset = reader.read(path)

    assert dataset.source is not None
    assert dataset.source.up_axis == "Z"
    assert dataset.source.scale_to_metres == 1.0
    assert "Reader" in dataset.source.reader


def test_unsupported_format_names_itself(tmp_path: Path) -> None:
    """ingest/AC-021: an unsupported format is named, and no partial case is created."""
    path = tmp_path / "result.sim"
    path.write_bytes(b"not a mesh")

    with pytest.raises(reader.UnsupportedFormatError) as error:
        reader.read(path)
    assert ".sim" in str(error.value)


def test_truncated_file_is_reported(tmp_path: Path) -> None:
    """ingest/AC-022: a damaged file of a supported format reports rather than returning something."""
    path = tmp_path / "case.vtu"
    write_grid(path)
    body = path.read_bytes()
    path.write_bytes(body[: len(body) // 2])

    with pytest.raises(reader.UnreadableFileError):
        reader.read(path)


def test_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(reader.UnreadableFileError):
        reader.read(tmp_path / "absent.vtu")


def test_support_level_is_reported_per_format(tmp_path: Path) -> None:
    """ingest/AC-032: the level comes from the table, and an unknown format is Absent."""
    assert reader.support_level(tmp_path / "case.vtu")[0] == "Verified"
    assert reader.support_level(tmp_path / "case.sim")[0] == "Absent"


def test_partitioned_reader_declares_its_gap(tmp_path: Path) -> None:
    """ingest/AC-033: an Offered or caveated reader names its specific gap, not a generic warning."""
    level, gaps = reader.support_level(tmp_path / "case.pvtu")
    assert level == "Verified"
    assert "boundaries" in gaps or "more than once" in gaps


def test_geometry_is_float_and_three_dimensional(tmp_path: Path) -> None:
    path = tmp_path / "case.vtu"
    write_grid(path)

    dataset = reader.read(path)

    assert dataset.points_m.shape == (4, 3)
    assert np.isfinite(dataset.points_m).all()
