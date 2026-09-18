"""A value at a picked point, read from the full dataset through the surface that was picked.

XC-257's step 4. The pick lands where the person pointed - on the reduced display surface, because
that is what they see - and the value comes from nowhere near it: the display vertex is traced back
through `source_points` to the dataset point it came from, and the number is that point's own,
at its own digits, with its own name in the source's words (view/AC-027, INV-001, INV-023).

Three things a pick may honestly be, and each is answered as itself (AC-028, AC-029):

- **a point value**, the dataset point nearest the pick, never an interpolation between vertices
  (INV-003: interpolating changes the number and must be asked for);
- **a cell value**, when the field lives on cells - the value of the cell the pick fell in, said to
  be a cell's, never smoothed onto a point;
- **nothing**, when the point is off the model or the entry is missing - reported as missing,
  never as zero (INV-011) and never as the nearest value that does exist.

Specification: view/AC-027, AC-028, AC-029, INV-001, INV-003, INV-011, INV-023.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np
from vtkmodules.vtkCommonCore import reference
from vtkmodules.vtkCommonDataModel import vtkStaticCellLocator

from domain_core.association import Association
from domain_core.dataset import Dataset
from domain_core.identifiers import location_of
from domain_core.reported_value import Provenance, ReportedValue
from engine.limits import MAX_INTERACTIVE_TRIANGLES
from engine.visualization.display import as_polydata, display_geometry

#: How far from the surface a pick may land and still be on the model, as a fraction of the model's
#: bounding diagonal. Farther than this and the pick has no value (AC-029), rather than the nearest
#: value there is - a reading taken from a point that is not on the part is a reading of nothing.
ON_SURFACE_FRACTION = 0.01


class PickError(Exception):
    """Raised where the question itself cannot be asked - an unknown field, a bad point."""


@dataclass(frozen=True, slots=True)
class Pick:
    """What a pick found: the value, whose it is, and how far the asked point was from the surface."""

    value: ReportedValue
    association: Association
    distance_m: float
    #: Which display triangle the pick fell in, or -1 when it fell on nothing.
    triangle: int = -1


def probe(
    dataset: Dataset,
    field_name: str,
    point_m: Sequence[float],
    *,
    budget: int = MAX_INTERACTIVE_TRIANGLES,
) -> Pick:
    """The value of `field_name` at the model point nearest `point_m`, or a stated absence."""
    field = dataset.fields.get(field_name)
    if field is None:
        raise PickError(f"'{field_name}' というフィールドはありません（{sorted(dataset.fields)}）")
    if field.association is Association.INTEGRATION_POINT:
        raise PickError(
            f"'{field_name}' は積分点の値で、一つの点や要素の値として答えられません。"
            "要素内の分布を潰した値を出すことはしません（XC-123）"
        )
    if len(point_m) != 3 or not all(math.isfinite(float(one)) for one in point_m):
        raise PickError(f"点は正準フレームの 3 つの有限な座標です（{list(point_m)} が渡されました）")

    geometry = display_geometry(dataset, budget=budget)
    surface = as_polydata(geometry)
    locator = vtkStaticCellLocator()
    locator.SetDataSet(surface)
    locator.BuildLocator()
    closest = [0.0, 0.0, 0.0]
    cell_id, sub_id, squared = reference(0), reference(0), reference(0.0)
    locator.FindClosestPoint([float(one) for one in point_m], closest, cell_id, sub_id, squared)
    triangle = int(cell_id.get())
    distance = math.sqrt(max(float(squared.get()), 0.0))

    extent = geometry.points_m.max(axis=0) - geometry.points_m.min(axis=0)
    diagonal = float(np.linalg.norm(extent))
    if triangle < 0 or distance > ON_SURFACE_FRACTION * max(diagonal, np.finfo(float).tiny):
        return Pick(
            value=ReportedValue.unavailable(
                f"点はモデルの外です（表面から {distance:.4g} m）。近くの値を代わりに出すことはしません（AC-029）",
                unit=field.unit, digits=field.significant_digits, provenance=Provenance.DATASET,
            ),
            association=field.association,
            distance_m=distance,
        )

    if field.association is Association.POINT:
        corners = geometry.triangles[triangle]
        # The display vertex nearest the landing point, then the dataset point it came from. Not an
        # interpolation across the triangle: that would be a number no point of the mesh holds.
        offsets = geometry.points_m[corners] - np.asarray(closest, dtype=np.float64)
        vertex = int(corners[int(np.argmin(np.einsum("ij,ij->i", offsets, offsets)))])
        source = int(geometry.source_points[vertex])
        value = dataset.value(field_name, source)
        location = location_of(dataset.identifiers.get(Association.POINT), source)
        return Pick(replace(value, location=location), Association.POINT, distance, triangle)

    source_cell = int(geometry.source_cells[triangle])
    if source_cell < 0:
        # A decimated triangle spanning a cell boundary belongs to no cell; naming one of the cells it
        # partly covers would attach a value to a place the value is not true of.
        return Pick(
            value=ReportedValue.unavailable(
                "間引かれた表示の三角形が複数の要素にまたがっていて、どの要素の値かを言えません。"
                "表示予算を上げるか、要素の値は統計で読んでください",
                unit=field.unit, digits=field.significant_digits, provenance=Provenance.DATASET,
            ),
            association=Association.CELL,
            distance_m=distance,
            triangle=triangle,
        )
    value = dataset.value(field_name, source_cell)
    location = location_of(dataset.identifiers.get(Association.CELL), source_cell)
    return Pick(replace(value, location=location), Association.CELL, distance, triangle)
