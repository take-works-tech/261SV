"""What a cell volume costs when the coordinates are single precision.

`vtkPoints` stores its coordinates in **float** by default. This product holds geometry in metres in a
canonical frame and multiplies field values by cell volumes to produce a volume-weighted mean (INV-017),
so the question is not academic: whatever error is in the coordinates arrives in the reported number.

Run in a prepared spike environment (`pip install vtk==9.5.2 numpy`). Writes `point_precision.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import VTK_DOUBLE, VTK_FLOAT, vtkPoints
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, vtkUnstructuredGrid
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter


def cube_volume(side: float, data_type: int) -> float:
    """One axis-aligned cube of the given side, measured by the toolkit's own filter."""
    corners = [
        (0, 0, 0), (side, 0, 0), (side, side, 0), (0, side, 0),
        (0, 0, side), (side, 0, side), (side, side, side), (0, side, side),
    ]
    points = vtkPoints()
    points.SetDataType(data_type)
    for corner in corners:
        points.InsertNextPoint(*corner)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.InsertNextCell(VTK_HEXAHEDRON, 8, list(range(8)))

    sizes = vtkCellSizeFilter()
    sizes.SetInputData(grid)
    sizes.ComputeVolumeOn()
    sizes.ComputeAreaOff()
    sizes.ComputeLengthOff()
    sizes.ComputeVertexCountOff()
    sizes.SetVolumeArrayName("Volume")
    sizes.Update()
    return float(vtk_to_numpy(sizes.GetOutput().GetCellData().GetArray("Volume"))[0])


def main() -> None:
    measured: dict[str, object] = {
        "default_vtkPoints_data_type": vtkPoints().GetDataType(),
        "VTK_FLOAT": VTK_FLOAT,
        "VTK_DOUBLE": VTK_DOUBLE,
        "cubes": {},
    }
    for side in (1.0, 2.0, 0.1, 0.01):
        exact = side ** 3
        single = cube_volume(side, VTK_FLOAT)
        double = cube_volume(side, VTK_DOUBLE)
        measured["cubes"][str(side)] = {  # type: ignore[index]
            "exact": exact,
            "float32": single,
            "float32_relative_error": abs(single - exact) / exact,
            "float64": double,
            "float64_relative_error": abs(double - exact) / exact,
        }
        print(
            f"side {side}: float32 rel err {abs(single - exact) / exact:.2e}, "
            f"float64 rel err {abs(double - exact) / exact:.2e}"
        )

    Path(__file__).with_name("point_precision.json").write_text(
        json.dumps(measured, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
