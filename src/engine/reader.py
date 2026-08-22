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

# Metres, Z up. A file that declares something else is converted on load; a file that declares nothing
# is assumed to be in these already, and the assumption is recorded rather than hidden (AC-028).
CANONICAL_UP = "Z"
CANONICAL_SCALE = 1.0


class UnsupportedFormatError(Exception):
    """Raised for a file this build has no reader for. Names the format rather than failing vaguely."""


class UnreadableFileError(Exception):
    """Raised when a supported format cannot be read: truncated, damaged, or empty of geometry."""


@dataclass(frozen=True, slots=True)
class ReaderChoice:
    """Which reader will run, and what this product promises about it (XC-049)."""

    suffix: str
    factory: type
    support_level: str  # "Verified" | "Offered"
    known_gaps: str = ""


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

    fields = _fields(data)
    surface = _as_surface(data)
    points = vtk_to_numpy(surface.GetPoints().GetData()).astype(np.float64, copy=True)

    return Dataset(
        points_m=points * CANONICAL_SCALE,
        cells=_cells_as_indices(surface),
        fields=fields,
        source=SourceFrame(
            up_axis=CANONICAL_UP,
            scale_to_metres=CANONICAL_SCALE,
            reader=choice.factory.__name__,
        ),
    )


def support_level(path: str | Path) -> tuple[str, str]:
    """The level this product promises for a file's format, and the reader's known gaps (AC-032)."""
    choice = _READERS.get(Path(path).suffix.lower())
    if choice is None:
        return "Absent", "no reader for this format in this build"
    return choice.support_level, choice.known_gaps


def is_unstructured(data: vtkDataSet) -> bool:
    return isinstance(data, vtkUnstructuredGrid)
