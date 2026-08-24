"""The one entry point that turns a file into a @Dataset.

Nothing above this module knows which reader ran. What it returns is always in the canonical frame -
right-handed, Z up, metres - with fields that remember their association and units that are declared
or absent.

Three of the toolkit's defaults are overridden here, and each override is the reason this module
exists rather than a call site using the toolkit directly:

* a field arrives with the association the file gave it, and is not promoted to points (INV-003)
* a value that could not be read is missing, never zero (INV-011)
* no unit is inferred from a field name, a magnitude or a format (XC-003)

Specification: ingest/REQ-010, REQ-011, REQ-013, ingest/TASK-001, TASK-002.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObject,
    vtkDataSet,
    vtkMultiBlockDataSet,
    vtkPartitionedDataSet,
    vtkPartitionedDataSetCollection,
    vtkPolyData,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkIOXML import (
    vtkXMLPolyDataReader,
    vtkXMLPUnstructuredGridReader,
    vtkXMLUnstructuredGridReader,
)

from domain_core.case_contents import AxisKind, CaseContents, ResultAxis
from domain_core.dataset import Association, Dataset, Field, SourceFrame
from domain_core.frame import (
    CANONICAL_SCALE,
    FORMATS_CARRYING_UNIT_INFORMATION,
    FrameDeclaration,
    resolve_frame,
)
from domain_core.conversion import ConversionRecord
from domain_core.mesh import Cells
from domain_core.object_compatibility import Disposition, handling
from domain_core.partitions import Partitioning
from domain_core.parts import LoadedCase, Part
from engine.conversion import to_unstructured

class UnsupportedFormatError(Exception):
    """Raised for a file this build has no reader for. Names the format rather than failing vaguely."""


class UnreadableFileError(Exception):
    """Raised when a supported format cannot be read: truncated, damaged, or empty of geometry."""


def _declared_frame(path: Path, data: vtkDataSet | None) -> FrameDeclaration:
    """What this file declares about its frame.

    Every format this build reads declares **nothing**: the VTK XML formats carry no frame or unit
    field, and STL carries geometry alone (E-130). So this returns an empty declaration today, and the
    assumption that the file is already canonical is what gets recorded (AC-028). It exists as a step
    rather than as a comment so that a format which does declare - CGNS, with its `LengthUnits`
    enumeration - is read here and validated by the same rule, instead of at whatever call site adds it.
    """
    return FrameDeclaration()


@dataclass(frozen=True, slots=True)
class ReaderChoice:
    """Which reader will run, and what this product promises about it (XC-049)."""

    suffix: str
    factory: type
    support_level: str  # "Verified" | "Offered"
    known_gaps: str = ""
    # What unit information the file may carry that this reader does not read. Empty means the format
    # carries none - which is the measured case for every format in this build (E-130) - not that the
    # question was skipped.
    unread_unit_information: str = ""

    def __post_init__(self) -> None:
        carried = FORMATS_CARRYING_UNIT_INFORMATION.get(self.suffix)
        if carried and not self.unread_unit_information:
            raise ValueError(
                f"{self.suffix} files carry {carried}; a reader for them must either read it or say "
                f"that it does not (ingest/AC-034)"
            )


_READERS: dict[str, ReaderChoice] = {
    ".vtu": ReaderChoice(".vtu", vtkXMLUnstructuredGridReader, "Verified"),
    ".pvtu": ReaderChoice(".pvtu", vtkXMLPUnstructuredGridReader, "Verified",
                          "pieces are concatenated; points on partition boundaries appear more than once"),
    ".vtp": ReaderChoice(".vtp", vtkXMLPolyDataReader, "Verified"),
    ".stl": ReaderChoice(".stl", vtkSTLReader, "Verified", "carries geometry only; no fields"),
}


def supported_suffixes() -> list[str]:
    return sorted(_READERS)


def _canonical_cells(data: vtkDataSet) -> Cells:
    """The connectivity the file declared, in the toolkit's own layout and with nothing tessellated.

    An unstructured grid hands over its three arrays directly. Anything else - an image, a rectilinear
    or structured grid - has implicit connectivity rather than stored connectivity, and this build has
    no reader for one, so the case is refused by name instead of being approximated by its surface.
    """
    if isinstance(data, vtkUnstructuredGrid):
        cells = data.GetCells()
        return Cells(
            offsets=vtk_to_numpy(cells.GetOffsetsArray()).astype(np.int64, copy=True),
            connectivity=vtk_to_numpy(cells.GetConnectivityArray()).astype(np.int64, copy=True),
            types=vtk_to_numpy(data.GetCellTypesArray()).astype(np.uint8, copy=True),
        )
    if isinstance(data, vtkPolyData):
        # A surface file is already the thing it draws. Its four cell arrays are read in the order VTK
        # stores them so that a cell index means the same here as it does in the file.
        offsets = [np.zeros(1, np.int64)]
        connectivity: list[np.ndarray] = []
        types: list[np.ndarray] = []
        base = 0
        for array, cell_type in (
            (data.GetVerts(), 1), (data.GetLines(), 4), (data.GetPolys(), 7), (data.GetStrips(), 6),
        ):
            if array.GetNumberOfCells() == 0:
                continue
            piece = vtk_to_numpy(array.GetOffsetsArray()).astype(np.int64, copy=True)
            offsets.append(piece[1:] + base)
            entries = vtk_to_numpy(array.GetConnectivityArray()).astype(np.int64, copy=True)
            connectivity.append(entries)
            types.append(np.full(array.GetNumberOfCells(), cell_type, np.uint8))
            base += entries.size
        return Cells(
            offsets=np.concatenate(offsets),
            connectivity=np.concatenate(connectivity) if connectivity else np.zeros(0, np.int64),
            types=np.concatenate(types) if types else np.zeros(0, np.uint8),
        )
    raise UnreadableFileError(
        f"{type(data).__name__} stores no explicit connectivity; this build reads only the two types "
        "that do, and approximating the rest by its surface would put display geometry where the "
        "canonical geometry belongs (INV-001)"
    )


def _fields(data: vtkDataSet) -> dict[str, Field]:
    """Every array on the dataset, with the association the file gave it and no declared unit."""
    found: dict[str, Field] = {}
    for association, container in (
        (Association.POINT, data.GetPointData()),
        (Association.CELL, data.GetCellData()),
    ):
        for index in range(container.GetNumberOfArrays()):
            array = container.GetArray(index)
            if array is None:
                continue
            values = vtk_to_numpy(array).astype(np.float64, copy=True)
            name = array.GetName() or f"{association.value}_array_{index}"
            found[name] = Field(name=name, association=association, values=values, unit=None)
    return found


# CT-012's dispositions, as the reader applies them. A composite is taken apart into the parts of one
# @Case; a dataset is read; anything else names itself and stops.
_PARTITION_CONTAINERS = (vtkPartitionedDataSet,)


def _block_name(parent: vtkCompositeDataSet, index: int, fallback: str) -> str:
    """The name the file gave a block, or a generated one that says it was generated."""
    metadata = parent.GetMetaData(index)
    if metadata is not None and metadata.Has(vtkMultiBlockDataSet.NAME()):
        name = metadata.Get(vtkMultiBlockDataSet.NAME())
        if name:
            return str(name)
    return fallback


def _walk(node: vtkDataObject, path: tuple[str, ...], found: list[Part], absent: list[str],
          partitions: list[int]) -> None:
    """Collect the leaves of a composite as parts, keeping absent ones as absences.

    An empty leaf is a named `None` (E-133's measurement companion): the file said there was a part
    there and there is not, which is exactly what AC-027 asks be reported rather than skipped.
    """
    if isinstance(node, _PARTITION_CONTAINERS):
        # Partitions of one part: they recombine, so this is one part with a piece count (XC-234).
        pieces = [node.GetPartition(i) for i in range(node.GetNumberOfPartitions())]
        present = [piece for piece in pieces if piece is not None]
        partitions.append(max(len(present), 1))
        if not present:
            absent.append(" / ".join(path) or "unnamed partitioned dataset")
            return
        found.append(Part(name=path[-1], path=path, dataset=_combine(present)))
        return

    if isinstance(node, vtkCompositeDataSet):
        count = (
            node.GetNumberOfPartitionedDataSets()
            if isinstance(node, vtkPartitionedDataSetCollection)
            else node.GetNumberOfBlocks()
        )
        for index in range(count):
            child = (
                node.GetPartitionedDataSet(index)
                if isinstance(node, vtkPartitionedDataSetCollection)
                else node.GetBlock(index)
            )
            name = _block_name(node, index, f"block {index}")
            if child is None:
                absent.append(" / ".join(path + (name,)))
                continue
            _walk(child, path + (name,), found, absent, partitions)
        return

    # From here on the disposition is CT-012's, read from the contract rather than restated.
    where = " / ".join(path) or "the root object"
    row = handling(node.GetClassName())

    if row.disposition is Disposition.READ and isinstance(node, vtkDataSet):
        found.append(Part(name=path[-1], path=path, dataset=_as_dataset(node)))
        return

    if row.disposition is Disposition.CONVERT:
        converted, record = to_unstructured(node)
        found.append(Part(name=path[-1], path=path, dataset=_as_dataset(converted, conversion=record)))
        return

    raise UnsupportedFormatError(
        f"{where} is a {node.GetClassName()}, which this product does not read. {row.reason or ''} "
        "(CT-012). Naming it is the point: a generic read failure sends a user looking for a corrupt "
        "file that does not exist"
    )


def read(path: str | Path) -> Dataset:
    """Read a result file into a @Dataset in the canonical frame.

    Raises UnsupportedFormatError for a format with no reader here, and UnreadableFileError when a
    supported file yields no geometry - never a partial dataset, and never an empty one presented as
    a result (ingest/AC-021, AC-022).
    """
    location = Path(path)
    choice = _READERS.get(location.suffix.lower())
    if choice is None:
        raise UnsupportedFormatError(
            f"'{location.suffix}' is not a format this build reads; it reads {supported_suffixes()}"
        )
    if not location.exists():
        raise UnreadableFileError(f"{location} does not exist")

    reader = choice.factory()
    reader.SetFileName(str(location))
    reader.Update()
    data = reader.GetOutput()

    if data is None or data.GetNumberOfPoints() == 0:
        raise UnreadableFileError(f"{location.name} was read by {choice.factory.__name__} but contains no points")

    return _as_dataset(data, source=SourceFrame(
        *resolve_frame(_declared_frame(location, data)), reader=choice.factory.__name__
    ))


def _as_dataset(
    data: vtkDataSet, *, source: SourceFrame | None = None,
    conversion: ConversionRecord | None = None,
) -> Dataset:
    """One `vtkDataSet` as a @Dataset in the canonical frame, with nothing drawn.

    Shared by the single-file path and the composite walk so that a part of an assembly and a file on
    its own go through the same conversion - a second path here is a second set of rounding.
    """
    if data.GetNumberOfPoints() == 0:
        raise UnreadableFileError(f"a {type(data).__name__} was read and contains no points")
    scale = source.scale_to_metres if source is not None else CANONICAL_SCALE
    points = vtk_to_numpy(data.GetPoints().GetData()).astype(np.float64, copy=True)
    # One multiplication, at one point, and only when it changes the value. XC-230: a conversion happens
    # once at a stated place, and `* 1.0` on every coordinate of every dataset is an operation that can
    # only lose precision and never adds any.
    return Dataset(
        points_m=points if scale == CANONICAL_SCALE else points * scale,
        cells=_canonical_cells(data),
        fields=_fields(data),
        source=source,
        conversion=conversion,
    )


def _combine(pieces: list[vtkDataSet]) -> Dataset:
    """The partitions of one part, as the one mesh they were cut from.

    They are concatenated and **not merged**: the reader performs no point merging (E-039), so the
    interface points arrive twice and stay twice. Which is right - INV-010 governs them from there, and
    welding them here would need a tolerance (XC-232).
    """
    if len(pieces) == 1:
        return _as_dataset(pieces[0])
    datasets = [_as_dataset(piece) for piece in pieces]
    offset = 0
    points, offsets, connectivity, types = [], [np.zeros(1, np.int64)], [], []
    base = 0
    for dataset in datasets:
        points.append(dataset.points_m)
        offsets.append(dataset.cells.offsets[1:] + base)
        connectivity.append(dataset.cells.connectivity + offset)
        types.append(dataset.cells.types)
        base += dataset.cells.connectivity.size
        offset += dataset.point_count
    fields: dict[str, Field] = {}
    shared = set.intersection(*(set(dataset.fields) for dataset in datasets)) if datasets else set()
    for name in sorted(shared):
        first = datasets[0].fields[name]
        fields[name] = Field(
            name=name,
            association=first.association,
            values=np.concatenate([dataset.fields[name].values for dataset in datasets]),
            unit=first.unit,
        )
    return Dataset(
        points_m=np.concatenate(points),
        cells=Cells(np.concatenate(offsets), np.concatenate(connectivity), np.concatenate(types)),
        fields=fields,
        partitioning=Partitioning(partitions=len(pieces)),
    )


def read_case(path: str | Path) -> LoadedCase:
    """Read a file as one @Case, however many parts it turns out to hold (ingest/AC-026, AC-027).

    A composite is taken apart into named parts; a single dataset is one part named after its file.
    Either way what comes back states how many parts were found, how many pieces they were cut into,
    and which named parts were not there.
    """
    location = Path(path)
    choice = _READERS.get(location.suffix.lower())
    if choice is None:
        raise UnsupportedFormatError(
            f"'{location.suffix}' is not a format this build reads; it reads {supported_suffixes()}"
        )
    if not location.exists():
        raise UnreadableFileError(f"{location} does not exist")

    reader = choice.factory()
    reader.SetFileName(str(location))
    reader.Update()
    data = reader.GetOutputDataObject(0)
    if data is None:
        raise UnreadableFileError(f"{location.name} was read by {choice.factory.__name__} and is empty")

    found: list[Part] = []
    absent: list[str] = []
    partitions: list[int] = []
    _walk(data, (location.stem,), found, absent, partitions)

    if not found:
        raise UnreadableFileError(
            f"{location.name} named {len(absent)} part(s) and none of them is there"
            if absent
            else f"{location.name} holds no part this build can read"
        )
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


def support_level(path: str | Path) -> tuple[str, str]:
    """The level this product promises for a file's format, and the reader's known gaps (AC-032).

    An unread unit declaration is one of those gaps (AC-034): the unit stays undeclared either way, and
    the difference between "this file said nothing" and "this file said something we did not read" is
    the user's to know, because only one of the two can be fixed by asking the solver.
    """
    choice = _READERS.get(Path(path).suffix.lower())
    if choice is None:
        return "Absent", "no reader for this format in this build"
    gaps = [gap for gap in (choice.known_gaps, choice.unread_unit_information) if gap]
    return choice.support_level, "; ".join(gaps)


def is_unstructured(data: vtkDataSet) -> bool:
    return isinstance(data, vtkUnstructuredGrid)
