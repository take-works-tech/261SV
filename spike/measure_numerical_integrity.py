"""Two ways a post-processor reports a wrong number while doing arithmetic correctly.

Neither is exotic. Both are the ordinary shape of CAE data meeting the ordinary way of reducing it.

**Accumulation.** A field of ten million values varying by a thousandth about 300 - a temperature field,
or a stress field about a preload - summed the obvious ways. The question is what the mean loses.

**Averaging.** A stress concentration inside a body, held as element values. Averaging them onto the
shared nodes is what makes a smooth contour, and it is also what changes the maximum a report states.

Run in a prepared spike environment (`pip install vtk==9.5.2 numpy`). Writes `numerical_integrity.json`.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import VTK_DOUBLE, vtkPoints
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, vtkUnstructuredGrid
from vtkmodules.vtkFiltersCore import vtkCellDataToPointData

#: Ten million entries, which is a mesh this product's own limits allow several times over (LIM-001).
COUNT = 10_000_000
#: The offset and the variation. A field that varies in its fourth significant digit about a large
#: value is not a contrived case: it is a temperature in kelvin, or a stress about a preload.
OFFSET = 300.0
VARIATION = 1.0e-3
SEED = 20260825


def accumulation() -> dict[str, float]:
    """What the sum of a large field costs, by the precision it is accumulated in."""
    values = OFFSET + np.random.default_rng(SEED).normal(0.0, VARIATION, COUNT)
    single = values.astype(np.float32)
    exact = math.fsum(values.tolist())

    def error(total: float) -> float:
        return abs(total - exact) / abs(exact)

    measured = {
        "float64_pairwise": error(float(values.sum())),
        "float64_sequential": error(float(sum(values.tolist()))),
        "float32_accumulated_in_float32": error(float(single.sum())),
        "float32_accumulated_in_float64": error(float(single.sum(dtype=np.float64))),
        "mean_exact": exact / COUNT,
        "mean_float32_in_float32": float(single.sum()) / COUNT,
        "mean_float32_in_float64": float(single.sum(dtype=np.float64)) / COUNT,
    }
    measured["mean_error_float32_in_float32"] = abs(
        measured["mean_float32_in_float32"] - measured["mean_exact"]
    )
    return measured


def cancellation() -> dict[str, object]:
    """What a difference between two near-equal values costs, and what it does not.

    The first version of this measured `float32(300.0000001) - float32(300.0)` and reported 0.0 as a
    loss in the **subtraction**. It is not: both literals round to the same float32 before anything is
    subtracted, and the distinction was gone in storage. Subtraction of two float values within a factor
    of two is exact - checked below over a hundred thousand random pairs, which is the measurement that
    corrects the earlier reading.

    What a near-equal difference does lose is **significance**: operands carrying ten digits produce a
    difference carrying one, and the result's storage type says nothing about that.
    """
    rounding = np.float32(300.0000001) == np.float32(300.0)

    rng = np.random.default_rng(1)
    left = rng.uniform(1.0, 1000.0, 100_000).astype(np.float32)
    right = (left * rng.uniform(0.5, 2.0, 100_000)).astype(np.float32)
    in_single = (left - right).astype(np.float64)
    in_double = left.astype(np.float64) - right.astype(np.float64)

    a, b = 300.0000001, 300.0000000
    return {
        "two_close_literals_round_to_the_same_float32": bool(rounding),
        "float32_subtraction_differs_from_float64_anywhere": bool((in_single != in_double).any()),
        "pairs_checked": int(left.size),
        "operand_magnitude": a,
        "difference": a - b,
        "significant_digits_left": math.log10(abs(a) / abs(a - b)),
    }


def _bar(cell_values: list[float]) -> np.ndarray:
    """A row of hexahedra sharing faces, with one value per element, averaged onto the nodes."""
    count = len(cell_values)
    coordinates = [
        (float(i), y, z)
        for i in range(count + 1)
        for y in (0.0, 1.0)
        for z in (0.0, 1.0)
    ]

    def node(index: int, y: int, z: int) -> int:
        return index * 4 + y * 2 + z

    points = vtkPoints()
    points.SetDataType(VTK_DOUBLE)
    for coordinate in coordinates:
        points.InsertNextPoint(*coordinate)
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    for index in range(count):
        grid.InsertNextCell(
            VTK_HEXAHEDRON,
            8,
            [
                node(index, 0, 0), node(index + 1, 0, 0),
                node(index + 1, 1, 0), node(index, 1, 0),
                node(index, 0, 1), node(index + 1, 0, 1),
                node(index + 1, 1, 1), node(index, 1, 1),
            ],
        )
    array = numpy_to_vtk(np.asarray(cell_values, dtype=np.float64), deep=True)
    array.SetName("stress")
    grid.GetCellData().AddArray(array)

    to_points = vtkCellDataToPointData()
    to_points.SetInputData(grid)
    to_points.Update()
    return vtk_to_numpy(to_points.GetOutput().GetPointData().GetArray("stress"))


def averaging() -> dict[str, object]:
    """What averaging element values onto shared nodes does to the reported maximum.

    The concentration is **inside** the bar on purpose. At the end face a node belongs to one element
    and averaging changes nothing, so a check placed there reports that averaging is harmless.
    """
    cell_values = [10.0, 20.0, 200.0, 20.0, 10.0]
    at_points = _bar(cell_values)
    unaveraged = max(cell_values)
    averaged = float(at_points.max())
    at_end = _bar([10.0, 20.0, 60.0, 200.0])
    return {
        "cell_values": cell_values,
        "unaveraged_maximum": unaveraged,
        "averaged_maximum": averaged,
        "averaged_as_fraction_of_unaveraged": averaged / unaveraged,
        "under_report": unaveraged - averaged,
        "nodal_difference_at_the_peak": unaveraged - 20.0,
        "concentration_at_the_end_face_unaveraged": 200.0,
        "concentration_at_the_end_face_averaged": float(at_end.max()),
    }


def main() -> None:
    measured = {
        "count": COUNT,
        "accumulation": accumulation(),
        "cancellation": cancellation(),
        "averaging": averaging(),
    }
    Path(__file__).with_name("numerical_integrity.json").write_text(
        json.dumps(measured, indent=2), encoding="utf-8"
    )

    sums = measured["accumulation"]
    print(f"{COUNT:,} values of {OFFSET} +/- {VARIATION}")
    for name in (
        "float64_pairwise", "float64_sequential",
        "float32_accumulated_in_float32", "float32_accumulated_in_float64",
    ):
        print(f"  {name:34} relative error {sums[name]:.3e}")
    print(f"  exact mean {sums['mean_exact']:.12f}")
    print(f"  float32 accumulated in float32 {sums['mean_float32_in_float32']:.12f}")
    print(f"  float32 accumulated in float64 {sums['mean_float32_in_float64']:.12f}")

    gap = measured["cancellation"]
    print(
        f"float32 subtraction differs from float64 over {gap['pairs_checked']:,} pairs: "
        f"{gap['float32_subtraction_differs_from_float64_anywhere']}"
    )
    print(
        f"two literals 1e-7 apart round to the same float32: "
        f"{gap['two_close_literals_round_to_the_same_float32']}; "
        f"digits lost by the near-equal difference: {gap['significant_digits_left']:.1f}"
    )

    spread = measured["averaging"]
    print(f"maximum unaveraged {spread['unaveraged_maximum']}, "
          f"averaged {spread['averaged_maximum']} "
          f"({100 * spread['averaged_as_fraction_of_unaveraged']:.1f}% of it)")
    print(f"at an end face instead: unaveraged 200.0, "
          f"averaged {spread['concentration_at_the_end_face_averaged']}")


if __name__ == "__main__":
    main()
