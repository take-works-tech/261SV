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
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkPolyData, vtkUnstructuredGrid
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkIOXML import (
    vtkXMLPolyDataReader,
    vtkXMLPUnstructuredGridReader,
    vtkXMLUnstructuredGridReader,
)

from domain_core.dataset import Association, Dataset, Field, SourceFrame
from domain_core.frame import (
    CANONICAL_SCALE,
    CANONICAL_UP,
    FORMATS_CARRYING_UNIT_INFORMATION,
    FrameDeclaration,
    resolve_frame,
)

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


def _as_surface(data: vtkDataSet) -> vtkPolyData:
    """Triangulated surface of a dataset, for display only - never for reported numbers (INV-001)."""
    surface = vtkDataSetSurfaceFilter()
    surface.SetInputData(data)
    triangles = vtkTriangleFilter()
    triangles.SetInputConnection(surface.GetOutputPort())
    triangles.Update()
    return triangles.GetOutput()


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


def _cells_as_indices(surface: vtkPolyData) -> np.ndarray:
    connectivity = vtk_to_numpy(surface.GetPolys().GetConnectivityArray())
    offsets = vtk_to_numpy(surface.GetPolys().GetOffsetsArray())
    sizes = np.diff(offsets)
    if sizes.size and not np.all(sizes == 3):
        raise UnreadableFileError("surface extraction produced cells that are not triangles")
    return connectivity.reshape(-1, 3).astype(np.int64, copy=False)


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

    up_axis, scale = resolve_frame(_declared_frame(location, data))

    fields = _fields(data)
    surface = _as_surface(data)
    points = vtk_to_numpy(surface.GetPoints().GetData()).astype(np.float64, copy=True)

    # One multiplication, at one point, and only when it changes the value. XC-230: a conversion happens
    # once at a stated place, and `* 1.0` on every coordinate of every dataset is an operation that can
    # only lose precision and never adds any.
    return Dataset(
        points_m=points if scale == CANONICAL_SCALE else points * scale,
        cells=_cells_as_indices(surface),
        fields=fields,
        source=SourceFrame(
            up_axis=up_axis,
            scale_to_metres=scale,
            reader=choice.factory.__name__,
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
