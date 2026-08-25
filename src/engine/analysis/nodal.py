"""A value at a shared node is several values, and the spread between them is a measurement.

Where a solver writes one value per element, a node used by six elements carries six values. Averaging
them is what makes a smooth contour and it is also what changes the number a report states: measured
here, the averaged maximum of a stress concentration inside a body is **110 MPa against an element
maximum of 200 MPa** - 55 per cent of it (E-144, INV-032).

Neither figure is wrong. They answer different questions, and a report that gives one without saying
which has answered neither. So both are produced, each carries its label, and an averaged figure carries
the **spread** it was averaged from.

The spread is not a defect to hide. It is the only discretisation indicator a post-processor can compute
from a single solve, and the reference product publishes the same quantity as Nodal Difference, stating
that a large one means the mesh needs refining there (E-145). The combination that misleads is precisely
the smoothed peak shown alone: it looks converged (INV-033).

**Nothing here averages across a part or material boundary** (INV-022). The toolkit's own conversion
averages across every cell attached to a point with no notion of material (E-074), which is the default
this refuses to inherit rather than the behaviour it copies.

Specification: INV-022, INV-031, INV-032, INV-033, XC-247, E-143, E-144, E-145.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from domain_core.association import Association
from domain_core.dataset import Dataset, Field


class Averaging(str, Enum):
    """Which of the two numbers this is. Stated on the value, never a display option.

    Treating it as a display option is how a figure and a table on the same page come to disagree.
    """

    AVERAGED = "averaged"
    UNAVERAGED = "unaveraged"


AVERAGING_WORD = {
    Averaging.AVERAGED: "節点平均",
    Averaging.UNAVERAGED: "要素値（平均なし）",
}


class NodalError(Exception):
    """Raised where the two numbers cannot be produced honestly."""


@dataclass(frozen=True, slots=True)
class AtNodes:
    """Element values brought to the nodes, with what was lost on the way.

    `spread` is the largest contributing value minus the smallest, per node. `fraction` is that spread
    over the average, which is the dimensionless form - a 2 MPa spread means one thing on a 4 MPa
    average and another on a 400 MPa one.
    """

    values: np.ndarray
    spread: np.ndarray
    contributors: np.ndarray
    unit: str | None = None

    @property
    def fraction(self) -> np.ndarray:
        """Spread over average, with nothing where the average is zero.

        Not "spread over average or zero": a fraction of an average of zero is undefined, and returning
        zero there would read as perfect agreement at exactly the nodes where the value cancels.
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            found = np.abs(self.spread) / np.abs(self.values)
        found[~np.isfinite(found)] = np.nan
        return found

    @property
    def worst_node(self) -> int | None:
        """Where the elements disagree most, or None where nothing does."""
        if self.spread.size == 0 or not np.isfinite(self.spread).any():
            return None
        return int(np.nanargmax(self.spread))


@dataclass(frozen=True, slots=True)
class Extremum:
    """One reported peak, saying which of the two numbers it is (INV-032)."""

    value: float
    averaging: Averaging
    at: int
    unit: str | None = None
    spread: float | None = None
    fraction: float | None = None

    def describe(self) -> str:
        unit = f" {self.unit}" if self.unit else ""
        line = f"{self.value:g}{unit}（{AVERAGING_WORD[self.averaging]}）"
        if self.averaging is Averaging.AVERAGED and self.spread is not None:
            line += f"・その節点での要素間のばらつき {self.spread:g}{unit}"
            if self.fraction is not None and np.isfinite(self.fraction):
                line += f"（平均比 {self.fraction:.0%}）"
            line += " — メッシュ細分の目安であって、精度の保証ではありません"
        return line


def to_nodes(dataset: Dataset, field: Field) -> AtNodes:
    """Average a cell field onto the points, keeping the spread it was averaged from.

    Built from this product's own connectivity rather than from the toolkit's filter, because the
    filter returns the average and discards the spread - and the spread is half of what INV-032
    requires. Doing it here also keeps the material rule visible: this averages the cells that use each
    point, and it is the caller's job to hand it one part at a time (INV-022).
    """
    if field.association is not Association.CELL:
        raise NodalError(
            f"'{field.name}' は要素値ではありません（{field.association.value}）。"
            "節点平均は要素値にしか意味がありません"
        )
    if field.values.shape[0] != dataset.cell_count:
        raise NodalError(
            f"'{field.name}' の要素数が形状と合いません"
            f"（{field.values.shape[0]} と {dataset.cell_count}）"
        )

    points = dataset.point_count
    # float64 throughout, whatever the field is stored in (INV-031). The accumulation below is a sum
    # over every cell attached to a point, and in float32 it loses the variation it exists to carry.
    values = np.asarray(field.values, dtype=np.float64)
    total = np.zeros(points, dtype=np.float64)
    count = np.zeros(points, dtype=np.int64)
    largest = np.full(points, -np.inf, dtype=np.float64)
    smallest = np.full(points, np.inf, dtype=np.float64)

    offsets = dataset.cells.offsets
    connectivity = dataset.cells.connectivity
    for cell in range(len(offsets) - 1):
        value = values[cell]
        if np.isnan(value):
            # A cell with no value contributes nothing and is not counted, rather than contributing a
            # zero that would pull the average down (INV-011).
            continue
        for point in connectivity[offsets[cell]: offsets[cell + 1]]:
            total[point] += value
            count[point] += 1
            largest[point] = max(largest[point], value)
            smallest[point] = min(smallest[point], value)

    with np.errstate(invalid="ignore"):
        averaged = np.where(count > 0, total / np.maximum(count, 1), np.nan)
    spread = np.where(count > 0, largest - smallest, np.nan)
    return AtNodes(averaged, spread, count, field.unit)


def extremum(
    dataset: Dataset,
    field: Field,
    *,
    averaging: Averaging,
    largest: bool = True,
) -> Extremum:
    """The maximum or minimum, said as one of the two numbers it can be (INV-032, XC-247).

    `averaging` has no default. The two differ by 45 per cent on the measured case (E-144), and a
    product that picked would be choosing which of them somebody read.
    """
    if averaging is Averaging.UNAVERAGED:
        values = np.asarray(field.values, dtype=np.float64)
        if not np.isfinite(values).any():
            raise NodalError(f"'{field.name}' に有効な値がありません")
        at = int(np.nanargmax(values) if largest else np.nanargmin(values))
        return Extremum(float(values[at]), averaging, at, field.unit)

    at_nodes = to_nodes(dataset, field)
    if not np.isfinite(at_nodes.values).any():
        raise NodalError(f"'{field.name}' を節点に持ってきた結果に有効な値がありません")
    at = int(np.nanargmax(at_nodes.values) if largest else np.nanargmin(at_nodes.values))
    return Extremum(
        float(at_nodes.values[at]),
        averaging,
        at,
        field.unit,
        spread=float(at_nodes.spread[at]),
        fraction=float(at_nodes.fraction[at]),
    )


def both(dataset: Dataset, field: Field, *, largest: bool = True) -> tuple[Extremum, Extremum]:
    """Both numbers, in the order a report should show them.

    Unaveraged first, because it is the value the solver produced, and averaged second with its spread.
    A caller that wants only one has to say which; a caller that shows both cannot present either as
    the number.
    """
    return (
        extremum(dataset, field, averaging=Averaging.UNAVERAGED, largest=largest),
        extremum(dataset, field, averaging=Averaging.AVERAGED, largest=largest),
    )


def disagreement(first: Extremum, second: Extremum) -> str:
    """What has to be said where the two figures are shown together, or where one is chosen."""
    if first.unit != second.unit:
        raise NodalError("単位の違う二つの極値は並べられません")
    unit = f" {first.unit}" if first.unit else ""
    gap = abs(first.value - second.value)
    if gap == 0.0:
        return (
            "節点平均と要素値の最大が一致しています。"
            "その節点に接する要素が 1 つだけの場合にも起きます — "
            "境界上の集中は平均しても変わりません（E-144）"
        )
    larger = max(abs(first.value), abs(second.value))
    return (
        f"節点平均と要素値で {gap:g}{unit} 違います"
        f"（大きいほうの {gap / larger:.0%}）。"
        "どちらも正しく、答えている問いが違います"
    )
