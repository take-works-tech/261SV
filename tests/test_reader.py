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


class TestUnreadUnitInformation:
    """ingest/AC-034, at the reader table. The rule is enforced when the table is built, so a reader
    added for a format that carries units cannot be added silently.

    The other half of AC-034 - the unit staying undeclared whatever the file carried - is
    `test_no_unit_is_declared_on_load` above, which already asserts it for AC-023. One assertion rather
    than two: a duplicate passes while the original is deleted.
    """

    def test_a_reader_for_a_format_carrying_units_must_state_the_gap(self) -> None:
        from engine.reader import ReaderChoice

        with pytest.raises(ValueError) as refusal:
            ReaderChoice(".cgns", object, "Verified")
        assert "LengthUnits" in str(refusal.value)
        assert "AC-034" in str(refusal.value)

    def test_stating_the_gap_is_enough_to_add_one(self) -> None:
        from engine.reader import ReaderChoice

        choice = ReaderChoice(".cgns", object, "Verified",
                              unread_unit_information="the file declares LengthUnits; this reader does not read it")
        assert "LengthUnits" in choice.unread_unit_information

    def test_the_gap_reaches_the_surface_that_reports_gaps(self, tmp_path: Path) -> None:
        """It is reported through support_level, beside the other known gaps, rather than in a place of
        its own that an interface would have to know to ask about (AC-032)."""
        import engine.reader as reader_module

        choice = reader_module.ReaderChoice(
            ".cgns", object, "Verified", known_gaps="one gap",
            unread_unit_information="the file declares LengthUnits; this reader does not read it")
        original = dict(reader_module._READERS)
        reader_module._READERS[".cgns"] = choice
        try:
            level, gaps = reader_module.support_level(tmp_path / "case.cgns")
        finally:
            reader_module._READERS.clear()
            reader_module._READERS.update(original)

        assert level == "Verified"
        assert "one gap" in gaps and "LengthUnits" in gaps


def write_block(path: Path, n: int = 3) -> np.ndarray:
    """An n x n x n block of points meshed with hexahedra, with a point field equal to the index.

    A volume mesh, unlike the two-triangle grid above, has points that are not on its surface - which
    is the case the reader was silently wrong about.
    """
    from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON

    points = vtkPoints()
    index: dict[tuple[int, int, int], int] = {}
    for k in range(n):
        for j in range(n):
            for i in range(n):
                index[(i, j, k)] = points.GetNumberOfPoints()
                points.InsertNextPoint(float(i), float(j), float(k))

    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    for k in range(n - 1):
        for j in range(n - 1):
            for i in range(n - 1):
                grid.InsertNextCell(VTK_HEXAHEDRON, 8, [
                    index[(i, j, k)], index[(i + 1, j, k)], index[(i + 1, j + 1, k)], index[(i, j + 1, k)],
                    index[(i, j, k + 1)], index[(i + 1, j, k + 1)], index[(i + 1, j + 1, k + 1)],
                    index[(i, j + 1, k + 1)],
                ])

    values = np.arange(grid.GetNumberOfPoints(), dtype=np.float64) * 10.0
    array = numpy_to_vtk(values, deep=True)
    array.SetName("stress")
    grid.GetPointData().AddArray(array)

    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()
    return values


class TestTheGeometryAFieldBelongsTo:
    """INV-001 is a statement about two point sets. Until `Cells` and `DisplayGeometry` existed the
    reader kept only the drawn one and hung the fields off it, so a field index and a geometry index
    named different places (E-132). The two-triangle grid above could never show it: its surface is
    itself."""

    def test_the_dataset_keeps_the_points_the_file_declared(self, tmp_path: Path) -> None:
        values = write_block(tmp_path / "block.vtu")

        dataset = reader.read(tmp_path / "block.vtu")

        assert dataset.point_count == values.size == 27
        assert dataset.cell_count == 8

    def test_a_field_index_and_a_geometry_index_name_the_same_point(self, tmp_path: Path) -> None:
        """The centre of the block is point 13 at (1, 1, 1) and its value is 130. Before the fix,
        `points_m[13]` was a surface point and `stress[13]` was this one."""
        write_block(tmp_path / "block.vtu")

        dataset = reader.read(tmp_path / "block.vtu")

        assert dataset.points_m[13].tolist() == [1.0, 1.0, 1.0]
        assert dataset.fields["stress"].values[13] == 130.0

    def test_reading_draws_nothing(self, tmp_path: Path) -> None:
        """Display geometry is MOD-003's work and is produced when a view asks for it. What the reader
        returns is the file, in the canonical frame - see tests/test_display.py for the rest."""
        write_block(tmp_path / "block.vtu")

        assert reader.read(tmp_path / "block.vtu").display_by_budget == {}

    def test_the_cells_are_the_hexahedra_and_not_their_triangles(self, tmp_path: Path) -> None:
        write_block(tmp_path / "block.vtu")

        dataset = reader.read(tmp_path / "block.vtu")

        assert set(dataset.cells.types.tolist()) == {12}  # VTK_HEXAHEDRON
        assert dataset.cells.points_of(0).size == 8

    def test_the_maximum_is_the_interior_point_the_picture_never_shows(self, tmp_path: Path) -> None:
        """INV-001, stated as a number: the largest value in this block is at its centre."""
        write_block(tmp_path / "block.vtu")

        assert reader.read(tmp_path / "block.vtu").maximum("stress").value == 260.0


def triangle(offset: float, first: float):
    """One triangle carrying a point field, for building composites out of."""
    from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE as TRI

    points = vtkPoints()
    for x, y in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)):
        points.InsertNextPoint(x + offset, y, 0.0)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.InsertNextCell(TRI, 3, [0, 1, 2])
    array = numpy_to_vtk(np.array([first, first + 1.0, first + 2.0]), deep=True)
    array.SetName("stress")
    grid.GetPointData().AddArray(array)
    return grid


class TestACompositeIsOneCaseOfManyParts:
    """19 of the 40 CAE readers in the pinned build return a `vtkMultiBlockDataSet` and 6 a
    `vtkPartitionedDataSetCollection`, against 4 that return an unstructured grid (E-133). An assembly
    arrives as an assembly, and this is the path that meets it."""

    def nested_assembly(self):
        from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

        inner = vtkMultiBlockDataSet()
        inner.SetNumberOfBlocks(2)
        inner.SetBlock(0, triangle(0.0, 10.0))
        inner.GetMetaData(0).Set(vtkMultiBlockDataSet.NAME(), "flange")
        inner.SetBlock(1, triangle(2.0, 90.0))
        inner.GetMetaData(1).Set(vtkMultiBlockDataSet.NAME(), "gasket")

        root = vtkMultiBlockDataSet()
        root.SetNumberOfBlocks(3)
        root.SetBlock(0, inner)
        root.GetMetaData(0).Set(vtkMultiBlockDataSet.NAME(), "assembly")
        root.SetBlock(1, triangle(5.0, 40.0))
        root.GetMetaData(1).Set(vtkMultiBlockDataSet.NAME(), "bolt")
        root.SetBlock(2, None)
        root.GetMetaData(2).Set(vtkMultiBlockDataSet.NAME(), "washer")
        return root

    def walk(self, node):
        from domain_core.case_contents import AxisKind, CaseContents, ResultAxis
        from domain_core.parts import LoadedCase

        found, absent, partitions = [], [], []
        reader._walk(node, ("asm",), found, absent, partitions)
        return LoadedCase(
            parts=tuple(found),
            contents=CaseContents(
                steps=1,
                parts=len(found),
                axis=ResultAxis(AxisKind.NONE),
                missing_parts=tuple(absent),
                partitions=max(partitions or [1]),
            ),
        )

    def test_nested_blocks_become_parts_with_their_hierarchy(self) -> None:
        case = self.walk(self.nested_assembly())

        assert [part.label for part in case.present] == [
            "asm / assembly / flange", "asm / assembly / gasket", "asm / bolt"
        ]

    def test_an_empty_block_is_a_named_part_that_is_missing(self) -> None:
        """AC-027: the file said there was a part there. A block with a name and no data is exactly
        that, and skipping it would leave an assembly nobody knows is incomplete."""
        case = self.walk(self.nested_assembly())

        assert case.is_partial is True
        assert case.contents.missing_parts == ("asm / washer",)

    def test_the_case_wide_maximum_carries_the_missing_part(self) -> None:
        value = self.walk(self.nested_assembly()).maximum("stress")

        assert value.value == 92.0
        assert "partial-dataset" in [caveat.value for caveat in value.caveats]

    def test_partitions_of_one_dataset_are_one_part(self) -> None:
        """XC-234: they recombine into the mesh they were cut from, so the case has one part and a
        partition count - not three parts."""
        from vtkmodules.vtkCommonDataModel import vtkPartitionedDataSet, vtkPartitionedDataSetCollection

        pieces = vtkPartitionedDataSet()
        pieces.SetNumberOfPartitions(3)
        for index in range(3):
            pieces.SetPartition(index, triangle(index * 3.0, 100.0 + index))
        collection = vtkPartitionedDataSetCollection()
        collection.SetNumberOfPartitionedDataSets(1)
        collection.SetPartitionedDataSet(0, pieces)
        collection.GetMetaData(0).Set(vtkPartitionedDataSetCollection.NAME(), "rotor")

        case = self.walk(collection)

        assert len(case.present) == 1
        assert case.contents.parts == 1
        assert case.contents.partitions == 3
        assert case.part("rotor").dataset.point_count == 9

    def test_the_recombined_part_refuses_the_numbers_partitioning_invalidates(self) -> None:
        """The partition count reaches the @Dataset, so INV-010 applies without anyone re-stating it."""
        from vtkmodules.vtkCommonDataModel import vtkPartitionedDataSet, vtkPartitionedDataSetCollection

        pieces = vtkPartitionedDataSet()
        pieces.SetNumberOfPartitions(2)
        for index in range(2):
            pieces.SetPartition(index, triangle(index * 3.0, 100.0 + index))
        collection = vtkPartitionedDataSetCollection()
        collection.SetNumberOfPartitionedDataSets(1)
        collection.SetPartitionedDataSet(0, pieces)
        collection.GetMetaData(0).Set(vtkPartitionedDataSetCollection.NAME(), "rotor")

        dataset = self.walk(collection).part("rotor").dataset

        assert dataset.partitioning.partitions == 2
        assert dataset.maximum("stress").value == 103.0
        assert dataset.total("stress").is_missing
        assert "パーティション境界" in (dataset.total("stress").missing_because or "")

    def test_a_type_the_contract_refuses_names_itself(self) -> None:
        """TASK-030's rule, met here for the composite path: a generic read failure sends a user
        looking for a corrupt file that does not exist."""
        from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkTable

        root = vtkMultiBlockDataSet()
        root.SetNumberOfBlocks(1)
        root.SetBlock(0, vtkTable())
        root.GetMetaData(0).Set(vtkMultiBlockDataSet.NAME(), "history")

        with pytest.raises(reader.UnsupportedFormatError) as refusal:
            self.walk(root)
        assert "vtkTable" in str(refusal.value)
        assert "asm / history" in str(refusal.value)


class TestReadCaseOnASingleFile:
    def test_one_file_is_one_case_of_one_part(self, tmp_path: Path) -> None:
        write_grid(tmp_path / "one.vtu")

        case = reader.read_case(tmp_path / "one.vtu")

        assert case.contents.parts == 1
        assert case.contents.partitions == 1
        assert case.part("one").dataset.point_count == 4

    def test_an_unreadable_format_is_named(self, tmp_path: Path) -> None:
        with pytest.raises(reader.UnsupportedFormatError) as refusal:
            reader.read_case(tmp_path / "nothing.xyz")
        assert ".xyz" in str(refusal.value)


def write_identified(path: Path, *, with_ids: bool) -> None:
    """A two-triangle grid, optionally carrying the identifiers the solver wrote."""
    from vtkmodules.vtkCommonCore import vtkIdTypeArray

    points = vtkPoints()
    for x, y in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)):
        points.InsertNextPoint(x, y, 0.0)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    for triangle in ([0, 1, 2], [1, 3, 2]):
        grid.InsertNextCell(VTK_TRIANGLE, 3, triangle)

    stress = numpy_to_vtk(np.array([10.0, 20.0, 90.0, 40.0]), deep=True)
    stress.SetName("stress")
    grid.GetPointData().AddArray(stress)

    if with_ids:
        nodes = vtkIdTypeArray()
        nodes.SetName("GlobalNodeId")
        for value in (1001, 1002, 1003, 1004):
            nodes.InsertNextValue(value)
        grid.GetPointData().SetGlobalIds(nodes)
        elements = vtkIdTypeArray()
        elements.SetName("GlobalElementId")
        for value in (5001, 5002):
            elements.InsertNextValue(value)
        grid.GetCellData().SetGlobalIds(elements)

    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    writer.Write()


class TestIdentifiersSurviveReading:
    """INV-023. `<PointData GlobalIds="GlobalNodeId">` is in the file, so the attribute role is read
    rather than guessed from the array's name (E-135)."""

    def test_the_identifiers_the_solver_wrote_come_back(self, tmp_path: Path) -> None:
        write_identified(tmp_path / "ids.vtu", with_ids=True)

        dataset = reader.read(tmp_path / "ids.vtu")

        point_ids = dataset.identifiers[Association.POINT]
        assert point_ids.global_name == "GlobalNodeId"
        assert point_ids.global_ids.tolist() == [1001, 1002, 1003, 1004]
        assert dataset.identifiers[Association.CELL].global_ids.tolist() == [5001, 5002]

    def test_they_are_not_offered_as_variables(self, tmp_path: Path) -> None:
        """Before this, `GlobalNodeId` arrived as a @Field with no declared unit - a physical quantity
        as far as anything downstream could tell, castable to float and plottable against itself."""
        write_identified(tmp_path / "ids.vtu", with_ids=True)

        assert sorted(reader.read(tmp_path / "ids.vtu").fields) == ["stress"]

    def test_they_stay_integers(self, tmp_path: Path) -> None:
        write_identified(tmp_path / "ids.vtu", with_ids=True)

        ids = reader.read(tmp_path / "ids.vtu").identifiers[Association.POINT].global_ids
        assert np.issubdtype(ids.dtype, np.integer)

    def test_the_maximum_is_reported_against_the_identifier(self, tmp_path: Path) -> None:
        write_identified(tmp_path / "ids.vtu", with_ids=True)

        assert reader.read(tmp_path / "ids.vtu").maximum("stress").location == "GlobalNodeId 1003"

    def test_a_file_with_none_says_so_rather_than_giving_an_index(self, tmp_path: Path) -> None:
        write_identified(tmp_path / "plain.vtu", with_ids=False)

        value = reader.read(tmp_path / "plain.vtu").maximum("stress")

        assert value.value == 90.0
        assert "識別子" in (value.location or "")
        assert reader.read(tmp_path / "plain.vtu").identifiers == {}
