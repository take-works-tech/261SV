"""The weights a summary statistic is weighted by, measured on the canonical geometry.

Separate from `summary.py` on purpose: the rules about what a reduction is and how it is labelled hold
without a toolkit and are tested without one, while the geometry of a cell comes from the toolkit's own
shape functions. A module that mixed the two would make every test of the labelling rule need a mesh.

**A point's share of a cell is the integral of its shape function over the cell, and a cell's volume
is the integral of its Jacobian** (XC-288). Until 2026-09-21 the share was an equal split of the
toolkit's tetrahedron-split volume, which is the same number on parallelepipeds and tetrahedra and not
on a skewed hexahedron: there the volume average of a linear field came out 0.625 where the trilinear
interpolant's own average is 0.714 (E-214). The integrals are taken by Gauss quadrature on the
toolkit's parametric cell, with the toolkit's own interpolation functions, at an order that makes the
quadrature exact for the polynomial the linear cells are: two points per direction. So the weighted
mean of a point field is the exact volume average of the finite-element interpolant on hexahedra,
wedges and tetrahedra, and a cell's volume is the volume of the element the solver used - not of a
polyhedron with planar faces drawn through its corners.

Cells with no volume - triangles, quadrilaterals, lines, vertices - weigh nothing here, which is the
honest figure for a mesh that mixes them with volumes; a scope that is entirely surface comes back
with a zero total, and the refusal belongs to the caller (INV-017). A volumetric cell type this module
has no rule for is refused by name: a quadratic cell integrated with a linear rule is the kind of
approximation nobody would notice.

The coordinates are `Dataset.points_m`, float64 and refusing to be anything else (XC-245): this is
the multiplication that carries a coordinate's error into the reported average (E-142).

Specification: INV-017, XC-245, XC-288, graph/AC-022. Evidence: E-142 (T1), E-214 (T1), E-215 (T1).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import (
    VTK_HEXAHEDRON,
    VTK_PYRAMID,
    VTK_TETRA,
    VTK_WEDGE,
    vtkCellArray,
    vtkCellTypes,
    vtkHexahedron,
    vtkPyramid,
    vtkTetra,
    vtkUnstructuredGrid,
    vtkWedge,
)
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter

from domain_core.dataset import Dataset

#: The names the size filter writes. Set explicitly rather than left to the filter's defaults, so a
#: default that changes between toolkit versions is a build failure here rather than a missing array.
VOLUME_ARRAY = "Volume"
AREA_ARRAY = "Area"

#: How many cells are gathered at once. A million hexahedra's corners are 192 MB in float64; a chunk
#: bounds that whatever the case is (LIM-001).
CHUNK = 100_000


class WeightingError(Exception):
    """Raised where a weight cannot be computed honestly for what the mesh holds."""


@dataclass(frozen=True, slots=True)
class Rule:
    """One linear volume cell's quadrature: its node count, and at each point the toolkit's
    interpolation functions (n,), their parametric derivatives (3, n) and the point's weight."""

    name: str
    nodes: int
    functions: tuple[np.ndarray, ...]
    derivatives: tuple[np.ndarray, ...]
    weights: tuple[float, ...]


def _gauss_unit() -> tuple[tuple[float, float], ...]:
    """Two-point Gauss on [0, 1]: exact for cubics, which is the degree a shape function times the
    Jacobian of a trilinear map reaches in each parametric direction."""
    offset = 0.5 / math.sqrt(3.0)
    return ((0.5 - offset, 0.5), (0.5 + offset, 0.5))


def _triangle_points() -> tuple[tuple[float, float, float], ...]:
    """Dunavant's six-point rule of degree four on the parametric triangle {r, s >= 0, r + s <= 1}
    (weights sum to the triangle's area, one half): exact past the cubic a shape function times the
    Jacobian of a wedge reaches in the triangle's directions."""
    a, wa = 0.445948490915965, 0.223381589678011
    b, wb = 0.091576213509771, 0.109951743655322
    return (
        (a, a, wa / 2), (1 - 2 * a, a, wa / 2), (a, 1 - 2 * a, wa / 2),
        (b, b, wb / 2), (1 - 2 * b, b, wb / 2), (b, 1 - 2 * b, wb / 2),
    )


def _rule(cell, name: str, nodes: int, points: list[tuple[tuple[float, float, float], float]]) -> Rule:
    functions: list[np.ndarray] = []
    derivatives: list[np.ndarray] = []
    for parametric, _ in points:
        shape = [0.0] * nodes
        slope = [0.0] * (3 * nodes)
        cell.InterpolationFunctions(list(parametric), shape)
        cell.InterpolationDerivs(list(parametric), slope)
        functions.append(np.array(shape, dtype=np.float64))
        derivatives.append(np.array(slope, dtype=np.float64).reshape(3, nodes))
    return Rule(name, nodes, tuple(functions), tuple(derivatives), tuple(weight for _, weight in points))


def _rules() -> dict[int, Rule]:
    line = _gauss_unit()
    cube = [((r, s, t), wr * ws * wt) for r, wr in line for s, ws in line for t, wt in line]
    prism = [((r, s, t), w * wt) for r, s, w in _triangle_points() for t, wt in line]
    # A tetrahedron's shape functions are linear and its Jacobian constant: the centroid alone
    # integrates both exactly, with the parametric tetrahedron's volume of one sixth as the weight.
    tetrahedron = [((0.25, 0.25, 0.25), 1.0 / 6.0)]
    return {
        VTK_HEXAHEDRON: _rule(vtkHexahedron, "hexahedron", 8, cube),
        VTK_WEDGE: _rule(vtkWedge, "wedge", 6, prism),
        VTK_PYRAMID: _rule(vtkPyramid, "pyramid", 5, cube),
        VTK_TETRA: _rule(vtkTetra, "tetrahedron", 4, tetrahedron),
    }


RULES: dict[int, Rule] = _rules()

#: Cell types with no volume: they weigh nothing and are not refused (a surface in a volume mesh).
FLAT_TYPES = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9})


def _integrals(dataset: Dataset) -> tuple[np.ndarray, np.ndarray]:
    """Per cell, the integral of its Jacobian (its volume); per point, the integral of its shape
    functions over the cells that use it (its share). Both from one pass of one quadrature."""
    offsets = dataset.cells.offsets
    connectivity = dataset.cells.connectivity
    types = dataset.cells.types
    points = np.asarray(dataset.points_m, dtype=np.float64)
    volumes = np.zeros(dataset.cell_count, dtype=np.float64)
    shares = np.zeros(dataset.point_count, dtype=np.float64)
    for cell_type in np.unique(types):
        kind = int(cell_type)
        if kind in FLAT_TYPES:
            continue
        rule = RULES.get(kind)
        if rule is None:
            raise WeightingError(
                f"セル型 {vtkCellTypes.GetClassNameFromTypeId(kind)}（VTK type {kind}）の体積と節点の取り分を"
                "この版は求められません（線形の六面体・楔・角錐・四面体のみ）。"
                "線形の規則で近似して数を出すことはしません（XC-288）"
            )
        indices = np.flatnonzero(types == cell_type)
        for start in range(0, indices.size, CHUNK):
            chunk = indices[start:start + CHUNK]
            starts = offsets[chunk]
            corner_ids = starts[:, None] + np.arange(rule.nodes)[None, :]
            corner_ids = connectivity[corner_ids]  # (cells, nodes)
            corners = points[corner_ids]  # (cells, nodes, 3)
            volume = np.zeros(chunk.size, dtype=np.float64)
            share = np.zeros((chunk.size, rule.nodes), dtype=np.float64)
            for shape, slope, weight in zip(rule.functions, rule.derivatives, rule.weights):
                jacobian = np.einsum("kn,cnj->ckj", slope, corners)  # (cells, 3, 3)
                # The absolute value: a cell whose corners are listed the other way round has a
                # negative Jacobian and the same volume. A cell folded through itself has a Jacobian
                # of both signs, and no weighting is honest for it; that case is not detected here.
                measure = np.abs(np.linalg.det(jacobian)) * weight
                volume += measure
                share += measure[:, None] * shape[None, :]
            volumes[chunk] = volume
            np.add.at(shares, corner_ids.ravel(), share.ravel())
    return volumes, shares


def cell_volumes(dataset: Dataset) -> np.ndarray:
    """Each cell's volume in cubic metres, for weighting cell data (INV-017): the integral of the
    element's Jacobian, which for a skewed hexahedron is the element's volume and not that of a
    planar-faced polyhedron through its corners (E-215).

    A cell with no volume - a triangle, a line - contributes zero. That is the honest figure rather
    than an error: a mesh may hold both, and a volume-weighted mean over a scope that is entirely
    surface comes back unavailable through the caller, which is the right place for that refusal.
    """
    volumes, _ = _integrals(dataset)
    return volumes


def point_weights(dataset: Dataset) -> np.ndarray:
    """Each point's share of the volume around it (INV-017's dual-volume weighting): the integral of
    its shape function over every cell that uses it. The shares of a cell sum to the cell's volume,
    so the weights sum to the total - the property a weighting has to have, and the one an equal
    split also had; what the integral adds is that the weighted mean of a linear field is exact on
    every linear cell, skewed or not (XC-288).

    A point no cell uses keeps a weight of zero, and a mean over a scope of only such points is
    unavailable rather than a division by zero.
    """
    _, shares = _integrals(dataset)
    return shares


def _as_grid(dataset: Dataset) -> vtkUnstructuredGrid:
    points = vtkPoints()
    # float64 in, float64 stored. `vtkPoints` would otherwise hold single precision, which costs about
    # 5e-8 of relative error in a cell volume (E-142).
    points.SetData(numpy_to_vtk(np.ascontiguousarray(dataset.points_m), deep=True))
    cells = vtkCellArray()
    cells.SetData(
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.offsets), deep=True, array_type=12),
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.connectivity), deep=True, array_type=12),
    )
    grid = vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(
        numpy_to_vtk(np.ascontiguousarray(dataset.cells.types), deep=True, array_type=3), cells
    )
    return grid


def _sizes(dataset: Dataset) -> vtkUnstructuredGrid:
    sizes = vtkCellSizeFilter()
    sizes.SetInputData(_as_grid(dataset))
    sizes.ComputeVolumeOn()
    sizes.ComputeAreaOn()
    sizes.ComputeLengthOff()
    sizes.ComputeVertexCountOff()
    sizes.SetVolumeArrayName(VOLUME_ARRAY)
    sizes.SetAreaArrayName(AREA_ARRAY)
    sizes.Update()
    return sizes.GetOutput()


def toolkit_cell_volumes(dataset: Dataset) -> np.ndarray:
    """The toolkit's own cell volumes - a tetrahedron split through each cell's corners. Kept as the
    reference the integral is checked against (E-215): equal on every parallelepiped and tetrahedron,
    and not on a skewed hexahedron, where the split's planar faces are not the element's."""
    volumes = _sizes(dataset).GetCellData().GetArray(VOLUME_ARRAY)
    if volumes is None:
        raise RuntimeError(
            f"体積配列 '{VOLUME_ARRAY}' がツールキットから返りませんでした。"
            "名前を明示しているので、これは既定名の変更ではなくフィルタの失敗です"
        )
    return vtk_to_numpy(volumes).astype(np.float64, copy=True)


def cell_areas(dataset: Dataset) -> np.ndarray:
    """Each cell's area in square metres, for weighting a surface mesh that has no volume."""
    areas = _sizes(dataset).GetCellData().GetArray(AREA_ARRAY)
    if areas is None:
        raise RuntimeError(f"面積配列 '{AREA_ARRAY}' がツールキットから返りませんでした")
    return vtk_to_numpy(areas).astype(np.float64, copy=True)
