"""What VTK's data object types are, and what a reader hands this product for each of them.

Run in a prepared spike environment (`pip install vtk==9.5.2 numpy`). Writes `object_types.json`.

Three questions this settles, all of which a compatibility specification needs answered from the
toolkit rather than from documentation:

1. which concrete data object types exist, and which of them a `vtkDataSet` reader can produce;
2. what surface extraction - the step between a read file and a drawn picture - does to point count
   and point order, because a field read from the file is indexed by the *original* points;
3. which cell types a dataset can hold, since a View object type that promises "a mesh" has to say
   which cells count as one.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints, vtkVersion
from vtkmodules.vtkCommonDataModel import (
    VTK_HEXAHEDRON,
    vtkDataObjectTypes,
    vtkPolyData,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

RESULT = Path(__file__).with_name("object_types.json")


def data_object_types() -> list[dict[str, object]]:
    """Every type id VTK knows, with the class name and whether it is a dataset, composite or neither."""
    found = []
    for type_id in range(0, 128):
        name = vtkDataObjectTypes.GetClassNameFromTypeId(type_id)
        if not name or name == "UnknownClass":
            continue
        try:
            instance = vtkDataObjectTypes.NewDataObject(name)
        except Exception:
            instance = None
        found.append(
            {
                "id": type_id,
                "class": name,
                "instantiable": instance is not None,
                "is_dataset": bool(instance and instance.IsA("vtkDataSet")),
                "is_composite": bool(instance and instance.IsA("vtkCompositeDataSet")),
                "is_pointset": bool(instance and instance.IsA("vtkPointSet")),
            }
        )
    return found


def block_of_hexahedra(n: int = 3) -> vtkUnstructuredGrid:
    """An n x n x n block of points meshed with hexahedra, with a point field equal to the index."""
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
                grid.InsertNextCell(
                    VTK_HEXAHEDRON,
                    8,
                    [
                        index[(i, j, k)],
                        index[(i + 1, j, k)],
                        index[(i + 1, j + 1, k)],
                        index[(i, j + 1, k)],
                        index[(i, j, k + 1)],
                        index[(i + 1, j, k + 1)],
                        index[(i + 1, j + 1, k + 1)],
                        index[(i, j + 1, k + 1)],
                    ],
                )

    values = np.arange(grid.GetNumberOfPoints(), dtype=np.float64) * 10.0
    array = numpy_to_vtk(values, deep=True)
    array.SetName("stress")
    grid.GetPointData().AddArray(array)
    return grid


def surface_of(grid: vtkUnstructuredGrid) -> vtkPolyData:
    """Exactly the two filters `engine.reader` runs between the file and the drawn geometry."""
    surface = vtkDataSetSurfaceFilter()
    surface.SetInputData(grid)
    triangles = vtkTriangleFilter()
    triangles.SetInputConnection(surface.GetOutputPort())
    triangles.Update()
    return triangles.GetOutput()


def surface_extraction() -> dict[str, object]:
    """What the display path does to the point set a field is indexed by."""
    grid = block_of_hexahedra()
    surface = surface_of(grid)

    volume_points = vtk_to_numpy(grid.GetPoints().GetData())
    surface_points = vtk_to_numpy(surface.GetPoints().GetData())
    field = vtk_to_numpy(grid.GetPointData().GetArray("stress"))

    # Where each surface point came from in the volume, matched by coordinate.
    lookup = {tuple(row): i for i, row in enumerate(volume_points)}
    origin = [lookup[tuple(row)] for row in surface_points]

    return {
        "volume_points": int(grid.GetNumberOfPoints()),
        "volume_cells": int(grid.GetNumberOfCells()),
        "surface_points": int(surface.GetNumberOfPoints()),
        "surface_triangles": int(surface.GetNumberOfCells()),
        "field_length": int(field.size),
        "length_matches_geometry": int(field.size) == int(surface.GetNumberOfPoints()),
        "surface_point_order_matches_volume_prefix": origin == list(range(len(origin))),
        "first_ten_origins": origin[:10],
        "carries_original_ids": bool(surface.GetPointData().GetArray("vtkOriginalPointIds")),
        "field_carried_through": bool(surface.GetPointData().GetArray("stress")),
    }


def surface_with_original_ids() -> dict[str, object]:
    """Whether the filter can be asked for the map back to the original points."""
    grid = block_of_hexahedra()
    surface = vtkDataSetSurfaceFilter()
    surface.SetInputData(grid)
    surface.PassThroughPointIdsOn()
    surface.PassThroughCellIdsOn()
    surface.Update()
    output = surface.GetOutput()
    ids = output.GetPointData().GetArray("vtkOriginalPointIds")
    return {
        "point_ids_available": ids is not None,
        "point_id_array": None if ids is None else ids.GetName(),
        "cell_ids_available": output.GetCellData().GetArray("vtkOriginalCellIds") is not None,
        "count": None if ids is None else int(ids.GetNumberOfTuples()),
    }


def cell_types() -> dict[str, object]:
    """The linear and quadratic cell types a dataset may hold, by dimension."""
    from vtkmodules.vtkCommonDataModel import vtkCellTypes

    by_dimension: dict[str, list[str]] = {"0": [], "1": [], "2": [], "3": [], "unknown": []}
    for type_id in range(0, 100):
        name = vtkCellTypes.GetClassNameFromTypeId(type_id)
        if not name or name == "UnknownClass":
            continue
        dimension = vtkCellTypes.GetDimension(type_id)
        key = str(dimension) if 0 <= dimension <= 3 else "unknown"
        by_dimension[key].append(name)
    return {"count": sum(len(v) for v in by_dimension.values()), "by_dimension": by_dimension}


def main() -> None:
    result = {
        "vtk_version": vtkVersion.GetVTKVersion(),
        "data_object_types": data_object_types(),
        "surface_extraction": surface_extraction(),
        "surface_with_original_ids": surface_with_original_ids(),
        "cell_types": cell_types(),
    }
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["surface_extraction"], indent=2))
    print(json.dumps(result["surface_with_original_ids"], indent=2))
    print("data object types:", len(result["data_object_types"]))
    print("datasets:", sum(1 for t in result["data_object_types"] if t["is_dataset"]))
    print("composites:", sum(1 for t in result["data_object_types"] if t["is_composite"]))
    print("cell types:", result["cell_types"]["count"])
    print(f"written to {RESULT}")


if __name__ == "__main__":
    main()
