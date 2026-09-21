"""This product's numbers against the toolkit's own filters - the kernels ParaView runs - on the same
files, the same quantities, the same units (#321, XC-287).

The claim the product makes is trustworthy numbers, and the one way to check a claim from outside is
another implementation of the same arithmetic on the same input. ParaView is not installed on the
machine this ran on; its filters are these VTK classes (`vtkIntegrateAttributes` is Integrate
Variables, `vtkCellDataToPointData` is Cell Data to Point Data, `vtkTensorPrincipalInvariants` is
Principal Invariants, `vtkArrayCalculator` is the Calculator), so what is compared is the kernel and
not the application's presentation of it. That is stated as the limit of this measurement.

Every comparison is one of three kinds, and the record says which: **agrees** exactly; **differs**,
with the reason written beside it; or **has no reference**, because the toolkit does not compute the
quantity at all (the spread at an averaged peak, INV-033).

Run in the engine environment (VTK 9.5.2, numpy): `python spike/measure_cross_check.py`.
Writes `spike/cross_check.json`. `tests/test_cross_check.py` repeats the measurement on every run.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for one in (ROOT / "src", ROOT / "tests"):
    if str(one) not in sys.path:
        sys.path.insert(0, str(one))

import numpy as np  # noqa: E402
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy  # noqa: E402
from vtkmodules.vtkCommonCore import vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, vtkUnstructuredGrid  # noqa: E402
from vtkmodules.vtkFiltersCore import vtkAppendDataSets, vtkArrayCalculator, vtkCellDataToPointData  # noqa: E402
from vtkmodules.vtkFiltersParallel import vtkIntegrateAttributes  # noqa: E402
from vtkmodules.vtkFiltersTensor import vtkTensorPrincipalInvariants  # noqa: E402
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader  # noqa: E402

from domain_core.association import Association  # noqa: E402
from domain_core.dataset import Dataset, Field  # noqa: E402
from domain_core.mesh import Cells  # noqa: E402
from engine import reader  # noqa: E402
from engine.analysis import derived, nodal  # noqa: E402
from engine.analysis.summary import Reduction, Weighting, summarise  # noqa: E402
from engine.analysis.weights import point_weights  # noqa: E402

OUTPUT = HERE / "cross_check.json"


# ---- the toolkit's kernels, each named for the ParaView filter it is ------------------------------

def read_grid(path: Path) -> vtkUnstructuredGrid:
    read = vtkXMLUnstructuredGridReader()
    read.SetFileName(str(path))
    read.Update()
    return read.GetOutput()


def integrate_variables(grid: vtkUnstructuredGrid, name: str) -> tuple[float, float, str]:
    """ParaView's Integrate Variables: the integral of the field and the measure it was taken over."""
    kernel = vtkIntegrateAttributes()
    kernel.SetInputData(grid)
    kernel.Update()
    out = kernel.GetOutput()
    volume = out.GetCellData().GetArray("Volume")
    area = out.GetCellData().GetArray("Area")
    measure = float(volume.GetValue(0)) if volume else float(area.GetValue(0)) if area else math.nan
    array = out.GetPointData().GetArray(name) or out.GetCellData().GetArray(name)
    return (float(array.GetValue(0)) if array else math.nan), measure, ("Volume" if volume else "Area")


def cell_data_to_point_data(grid: vtkUnstructuredGrid, name: str) -> np.ndarray:
    """ParaView's Cell Data to Point Data: the unweighted average of the cells sharing each point."""
    kernel = vtkCellDataToPointData()
    kernel.SetInputData(grid)
    kernel.Update()
    return vtk_to_numpy(kernel.GetOutput().GetPointData().GetArray(name)).astype(np.float64)


def calculator_magnitude(grid: vtkUnstructuredGrid, name: str) -> np.ndarray:
    """ParaView's Calculator with `mag(name)`."""
    kernel = vtkArrayCalculator()
    kernel.SetInputData(grid)
    kernel.SetAttributeTypeToPointData()
    kernel.AddVectorArrayName(name)
    kernel.SetFunction(f"mag({name})")
    kernel.SetResultArrayName("magnitude")
    kernel.Update()
    return vtk_to_numpy(kernel.GetOutput().GetPointData().GetArray("magnitude")).astype(np.float64)


def principal_invariants(grid: vtkUnstructuredGrid, name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ParaView's Principal Invariants: the three principal values of a symmetric tensor field."""
    kernel = vtkTensorPrincipalInvariants()
    kernel.SetInputData(grid)
    kernel.SetInputArrayToProcess(0, 0, 0, 0, name)
    kernel.Update()
    data = kernel.GetOutput().GetPointData()
    return tuple(vtk_to_numpy(data.GetArray(f"{name} - Sigma {rank}")).astype(np.float64) for rank in (1, 2, 3))  # type: ignore[return-value]


def merge_blocks(*grids: vtkUnstructuredGrid) -> vtkUnstructuredGrid:
    """ParaView's Merge Blocks: the parts as one dataset, coincident points merged."""
    kernel = vtkAppendDataSets()
    kernel.SetMergePoints(True)
    for grid in grids:
        kernel.AddInputData(grid)
    kernel.Update()
    return kernel.GetOutput()


# ---- fixtures built in memory, beside the ones the tests write --------------------------------------

def hexahedra(first: int, count: int, values: list[float] | None) -> tuple[Dataset, vtkUnstructuredGrid]:
    """A row of unit hexahedra from x = first, as this product's dataset and as the toolkit's grid."""
    corners = np.array(
        [[float(index), y, z] for index in range(first, first + count + 1) for y in (0.0, 1.0) for z in (0.0, 1.0)],
        dtype=np.float64,
    )

    def node(index: int, y: int, z: int) -> int:
        return index * 4 + y * 2 + z

    connectivity: list[int] = []
    for index in range(count):
        connectivity += [
            node(index, 0, 0), node(index + 1, 0, 0), node(index + 1, 1, 0), node(index, 1, 0),
            node(index, 0, 1), node(index + 1, 0, 1), node(index + 1, 1, 1), node(index, 1, 1),
        ]
    fields: dict[str, Field] = {}
    if values is not None:
        fields["stress"] = Field("stress", Association.CELL, np.array(values, dtype=np.float64))
    dataset = Dataset(
        points_m=corners,
        cells=Cells(np.arange(0, 8 * count + 1, 8), np.array(connectivity), np.full(count, VTK_HEXAHEDRON, dtype=np.uint8)),
        fields=fields,
    )
    grid = vtkUnstructuredGrid()
    points = vtkPoints()
    points.SetData(numpy_to_vtk(corners, deep=True))
    grid.SetPoints(points)
    for index in range(count):
        grid.InsertNextCell(VTK_HEXAHEDRON, 8, connectivity[8 * index: 8 * index + 8])
    if values is not None:
        array = numpy_to_vtk(np.array(values, dtype=np.float64), deep=True)
        array.SetName("stress")
        grid.GetCellData().AddArray(array)
    return dataset, grid


def one_hexahedron(corners: np.ndarray, values: np.ndarray) -> tuple[Dataset, vtkUnstructuredGrid]:
    """One hexahedron whose eight corners are given in the toolkit's own order, with a point field."""
    dataset = Dataset(
        points_m=corners,
        cells=Cells(np.array([0, 8]), np.arange(8), np.array([VTK_HEXAHEDRON], dtype=np.uint8)),
        fields={"f": Field("f", Association.POINT, values)},
    )
    grid = vtkUnstructuredGrid()
    points = vtkPoints()
    points.SetData(numpy_to_vtk(corners, deep=True))
    grid.SetPoints(points)
    grid.InsertNextCell(VTK_HEXAHEDRON, 8, list(range(8)))
    array = numpy_to_vtk(values, deep=True)
    array.SetName("f")
    grid.GetPointData().AddArray(array)
    return dataset, grid


def trilinear_mean(corners: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    """The volume average of the trilinear interpolant over the hexahedron, and its volume, by 2 x 2 x 2
    Gauss quadrature - exact here, because the Jacobian is at most quadratic in each coordinate."""
    gauss = (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0))
    numerator = denominator = 0.0
    for a in gauss:
        for b in gauss:
            for c in gauss:
                shape = np.array([
                    (1 - a) * (1 - b) * (1 - c), (1 + a) * (1 - b) * (1 - c), (1 + a) * (1 + b) * (1 - c), (1 - a) * (1 + b) * (1 - c),
                    (1 - a) * (1 - b) * (1 + c), (1 + a) * (1 - b) * (1 + c), (1 + a) * (1 + b) * (1 + c), (1 - a) * (1 + b) * (1 + c),
                ]) / 8.0
                gradient = np.array([
                    [-(1 - b) * (1 - c), (1 - b) * (1 - c), (1 + b) * (1 - c), -(1 + b) * (1 - c), -(1 - b) * (1 + c), (1 - b) * (1 + c), (1 + b) * (1 + c), -(1 + b) * (1 + c)],
                    [-(1 - a) * (1 - c), -(1 + a) * (1 - c), (1 + a) * (1 - c), (1 - a) * (1 - c), -(1 - a) * (1 + c), -(1 + a) * (1 + c), (1 + a) * (1 + c), (1 - a) * (1 + c)],
                    [-(1 - a) * (1 - b), -(1 + a) * (1 - b), -(1 + a) * (1 + b), -(1 - a) * (1 + b), (1 - a) * (1 - b), (1 + a) * (1 - b), (1 + a) * (1 + b), (1 - a) * (1 + b)],
                ]) / 8.0
                jacobian = float(np.linalg.det(gradient @ corners))
                numerator += jacobian * float(shape @ values)
                denominator += jacobian
    return numerator / denominator, denominator


def dual_volume_mean(dataset: Dataset, values: np.ndarray) -> tuple[float, float]:
    weights = point_weights(dataset)
    return float(np.sum(weights * values) / np.sum(weights)), float(np.sum(weights))


# ---- the measurement ----------------------------------------------------------------------------------

def _row(case: str, quantity: str, ours: float | None, reference: float | None, reference_by: str, note: str = "") -> dict[str, Any]:
    agrees = (
        ours is not None and reference is not None
        and math.isfinite(ours) and math.isfinite(reference)
        and math.isclose(ours, reference, rel_tol=1e-12, abs_tol=1e-12)
    )
    verdict = "agrees" if agrees else ("no reference" if reference is None else "differs")
    return {"case": case, "quantity": quantity, "ours": ours, "reference": reference, "referenceBy": reference_by, "verdict": verdict, "note": note}


def measure(directory: Path) -> dict[str, Any]:
    """Every comparison, on fixtures written into `directory` by the tests' own writers (XC-085)."""
    from demo_case import write_bar, write_cube, write_fields
    from test_reader import write_grid

    rows: list[dict[str, Any]] = []

    # cube: one hexahedron, temperature 1..8 at the nodes (a trilinear field on a box)
    cube = directory / "cube.vtu"
    write_cube(cube)
    grid = read_grid(cube)
    dataset = reader.read_case(cube).present[0].dataset
    assert dataset is not None
    temperature = dataset.fields["temperature"]
    values = np.asarray(temperature.values, dtype=np.float64)
    integral, volume, measure_kind = integrate_variables(grid, "temperature")
    ours_mean, ours_volume = dual_volume_mean(dataset, values)
    rows.append(_row("cube", "max(temperature)", float(dataset.maximum("temperature").value or math.nan), float(values.max()), "GetRange"))
    rows.append(_row("cube", "mean(temperature), dual-volume weights", ours_mean, integral / volume, f"IntegrateAttributes ({measure_kind})",
                     "a box: each node's share is exactly V/8, and the integrator's tetrahedra give the same"))
    rows.append(_row("cube", "volume", ours_volume, volume, "IntegrateAttributes Volume"))

    # bar: five hexahedra with element values 10, 20, 200, 20, 10 (E-144)
    bar = directory / "bar.vtu"
    write_bar(bar)
    grid = read_grid(bar)
    dataset = reader.read_case(bar).present[0].dataset
    assert dataset is not None
    stress = dataset.fields["stress"]
    cells = np.asarray(stress.values, dtype=np.float64)
    integral, volume, _ = integrate_variables(grid, "stress")
    summary = summarise(cells, reduction=Reduction.MEAN, association=Association.CELL, scope="bar", weighting=Weighting.VOLUME, unit=None,
                        weights=dual_volume_weights_for_cells(dataset))
    at_nodes = nodal.to_nodes(dataset, stress)
    averaged = cell_data_to_point_data(grid, "stress")
    rows.append(_row("bar", "max(stress) unaveraged", float(dataset.maximum("stress").value or math.nan), float(cells.max()), "GetRange"))
    rows.append(_row("bar", "mean(stress), volume weights", float(summary.value), integral / volume, "IntegrateAttributes (Volume)"))
    rows.append(_row("bar", "max(nodal average of stress)", float(np.nanmax(at_nodes.values)), float(averaged.max()), "CellDataToPointData"))
    rows.append(_row("bar", "min(nodal average of stress)", float(np.nanmin(at_nodes.values)), float(averaged.min()), "CellDataToPointData"))
    rows.append(_row("bar", "every nodal average", float(np.max(np.abs(at_nodes.values - averaged))), 0.0, "CellDataToPointData, largest absolute difference over all nodes"))
    rows.append(_row("bar", "spread at the averaged maximum", float(at_nodes.spread[int(np.nanargmax(at_nodes.values))]), None, "-",
                     "the toolkit computes no spread; INV-033's indicator has no reference here"))

    # fields: a vector and a symmetric tensor with answers known by hand (tests/test_derived.py)
    fields = directory / "fields.vtu"
    write_fields(fields)
    grid = read_grid(fields)
    dataset = reader.read_case(fields).present[0].dataset
    assert dataset is not None
    magnitude = derived.derive(dataset.fields["displacement"], derived.Quantity.MAGNITUDE)[0].values
    rows.append(_row("fields", "every |displacement|", float(np.max(np.abs(magnitude - calculator_magnitude(grid, "displacement")))), 0.0,
                     "ArrayCalculator mag(), largest absolute difference over all points"))
    sigma = principal_invariants(grid, "stress6")
    principal = [one.values for one in derived.derive(dataset.fields["stress6"], derived.Quantity.PRINCIPAL)]
    for rank in range(3):
        rows.append(_row("fields", f"every principal value {rank + 1}", float(np.max(np.abs(principal[rank] - sigma[rank]))), 0.0,
                         f"TensorPrincipalInvariants Sigma {rank + 1}, largest absolute difference over all points"))
    von_mises = derived.derive(dataset.fields["stress6"], derived.Quantity.VON_MISES)[0].values
    from_principal = np.sqrt(((sigma[0] - sigma[1]) ** 2 + (sigma[1] - sigma[2]) ** 2 + (sigma[2] - sigma[0]) ** 2) / 2.0)
    rows.append(_row("fields", "every von Mises", float(np.max(np.abs(von_mises - from_principal))), 0.0,
                     "from the toolkit's principal values, largest absolute difference - the component formula against the eigenvalue route"))
    shear = derived.derive(dataset.fields["stress6"], derived.Quantity.MAXIMUM_SHEAR)[0].values
    rows.append(_row("fields", "every maximum shear", float(np.max(np.abs(shear - (sigma[0] - sigma[2]) / 2.0))), 0.0,
                     "from the toolkit's principal values, largest absolute difference"))

    # grid: two triangles - a surface, where this product refuses the mean and the integrator integrates
    surface = directory / "grid.vtu"
    write_grid(surface)
    grid = read_grid(surface)
    dataset = reader.read_case(surface).present[0].dataset
    assert dataset is not None
    integral, area, measure_kind = integrate_variables(grid, "stress")
    weights = point_weights(dataset)
    refused = summarise(np.asarray(dataset.fields["stress"].values, dtype=np.float64), reduction=Reduction.MEAN, association=Association.POINT,
                        scope="grid", weighting=Weighting.DUAL_VOLUME, unit=None, weights=weights)
    rows.append(_row("grid", "mean(stress) on a surface mesh", None if refused.value is None else float(refused.value), integral / area,
                     f"IntegrateAttributes ({measure_kind})",
                     "this product refuses: a surface has no volume and area weighting is not built (INV-017); the integrator averages over area"))

    # two parts sharing a face: the averaging stops at the part (INV-022) and the merged average does not
    part_a, grid_a = hexahedra(0, 3, [10.0, 20.0, 200.0])
    part_b, grid_b = hexahedra(3, 2, [20.0, 10.0])
    ours_a = float(np.nanmax(nodal.to_nodes(part_a, part_a.fields["stress"]).values))
    ours_b = float(np.nanmax(nodal.to_nodes(part_b, part_b.fields["stress"]).values))
    rows.append(_row("two parts", "max(nodal average) in the part holding the concentration", ours_a, float(cell_data_to_point_data(grid_a, "stress").max()),
                     "CellDataToPointData on that block alone"))
    rows.append(_row("two parts", "max(nodal average) in the other part", ours_b, float(cell_data_to_point_data(grid_b, "stress").max()),
                     "CellDataToPointData on that block alone"))
    merged = float(cell_data_to_point_data(merge_blocks(grid_a, grid_b), "stress").max())
    rows.append(_row("two parts", "max(nodal average) across the shared face", ours_a, merged, "Merge Blocks, then CellDataToPointData",
                     "this product averages within a part and never across one (INV-022, E-074); the merged average halves the peak at the face"))

    # a skewed hexahedron with a linear field: where V/8 per node stops being exact
    box = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], dtype=np.float64)
    skewed = box.copy()
    skewed[6] = [2.0, 2.0, 2.0]
    for label, corners in (("box", box), ("skewed hexahedron", skewed)):
        values = corners[:, 0].copy()  # f = x, linear
        dataset, grid = one_hexahedron(corners, values)
        integral, volume, _ = integrate_variables(grid, "f")
        ours_mean, ours_volume = dual_volume_mean(dataset, values)
        exact_mean, exact_volume = trilinear_mean(corners, values)
        rows.append(_row(label, "mean(f = x), dual-volume weights, against the integrator", ours_mean, integral / volume, "IntegrateAttributes (Volume)",
                         "" if label == "box" else "the integrator splits the cell into planar tetrahedra, and their volume average of a linear field is not the element's (E-215)"))
        rows.append(_row(label, "mean(f = x), dual-volume weights, against the trilinear interpolant", ours_mean, exact_mean, "2x2x2 Gauss quadrature of the trilinear interpolant",
                         "" if label == "box" else "the exact volume average of the trilinear interpolant, which the shape-function shares reach (XC-288)"))
        rows.append(_row(label, "volume", ours_volume, volume, "IntegrateAttributes Volume",
                         "" if label == "box" else f"this product integrates the element's Jacobian ({exact_volume:.6f}); the integrator's planar tetrahedra enclose more"))

    return {
        "measured_on": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "reference": "VTK filters, the kernels ParaView's filters are; ParaView itself was not run",
        "rows": rows,
        "agrees": sum(1 for row in rows if row["verdict"] == "agrees"),
        "differs": sum(1 for row in rows if row["verdict"] == "differs"),
        "no_reference": sum(1 for row in rows if row["verdict"] == "no reference"),
    }


def dual_volume_weights_for_cells(dataset: Dataset) -> np.ndarray:
    """Cell volumes, the weights of a cell field's mean (INV-017)."""
    from engine.analysis.weights import cell_volumes

    return cell_volumes(dataset)


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="solvia-cross-check-") as directory:
        record = measure(Path(directory))
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for row in record["rows"]:
        print(f"{row['verdict']:12} {row['case']:18} {row['quantity']:60} ours={row['ours']!r} ref={row['reference']!r} [{row['referenceBy']}]")
    print(f"agrees {record['agrees']}, differs {record['differs']}, no reference {record['no_reference']} -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
