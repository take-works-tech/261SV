"""A summary statistic that says how it was reduced, over what, and with which weighting.

INV-017 calls this "the single easiest way for this product to be confidently wrong", and the reason is
arithmetic rather than philosophical: the arithmetic mean of a field over an unstructured mesh weights a
millimetre-sized element the same as a metre-sized one. Both reductions are defensible and **they are
different numbers**, so a reported "average" that does not say which it is has not been reported.

Three rules follow.

**The default is weighted** - volume-weighted for cell data, dual-volume-weighted for point data - and
the weights are cell volumes computed on the canonical geometry. Which is why that geometry is double
precision: a single-precision volume carries about 5e-8 of relative error (E-142, XC-245), and this is
the multiplication that carries it into the answer.

**An unweighted reduction is labelled unweighted everywhere it appears** (AC-023), including in exports
and reports. Not as a footnote available on request: the label travels on the value, because the place
it goes missing is the place somebody reads the number.

**A scope with no valid entries is unavailable, not zero** (AC-024). Zero is a number a reader will
compare against a limit. "No entries" is not a small average.

Specification: INV-017, graph/AC-022 to AC-024, XC-245, E-142.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import numpy as np

from domain_core.association import Association


class Reduction(str, Enum):
    """What was done to the values. Each is a different question about the same field."""

    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    INTEGRAL = "integral"          # the sum of value x weight, which is not a mean
    STANDARD_DEVIATION = "standardDeviation"


class Weighting(str, Enum):
    """How the entries were weighted. `NONE` is a choice somebody makes, never a fallback."""

    VOLUME = "volume"              # cell data: each cell's own volume
    DUAL_VOLUME = "dualVolume"     # point data: the share of surrounding cell volume at each point
    AREA = "area"                  # a surface mesh has no volume to weight by
    NONE = "none"                  # arithmetic, and labelled as such wherever it appears


REDUCTION_WORD = {
    Reduction.MEAN: "平均",
    Reduction.MIN: "最小",
    Reduction.MAX: "最大",
    Reduction.SUM: "合計",
    Reduction.INTEGRAL: "積分",
    Reduction.STANDARD_DEVIATION: "標準偏差",
}

WEIGHTING_WORD = {
    Weighting.VOLUME: "体積加重",
    Weighting.DUAL_VOLUME: "双対体積加重",
    Weighting.AREA: "面積加重",
    Weighting.NONE: "**重みなし（算術）**",
}

#: What each association is weighted by unless somebody chooses otherwise (INV-017).
DEFAULT_WEIGHTING = {
    Association.CELL: Weighting.VOLUME,
    Association.POINT: Weighting.DUAL_VOLUME,
}

#: The reductions weighting changes. `min` and `max` pick an entry, and an entry does not become larger
#: for occupying more space - weighting them would be arithmetic nobody asked for.
WEIGHTABLE = frozenset(
    {Reduction.MEAN, Reduction.SUM, Reduction.INTEGRAL, Reduction.STANDARD_DEVIATION}
)


class SummaryError(Exception):
    """Raised where a reduction cannot be produced honestly."""


@dataclass(frozen=True, slots=True)
class Summary:
    """One reduced number, with everything needed to know what it is (INV-017).

    `value` of None means the reduction is **unavailable**, with `unavailable` saying why. There is no
    numeric stand-in, because a reader compares a number against a limit and "no entries" is not a small
    average.
    """

    reduction: Reduction
    weighting: Weighting
    scope: str
    value: float | None = None
    unit: str | None = None
    entries: int = 0
    skipped: int = 0
    unavailable: str | None = None

    def __post_init__(self) -> None:
        if self.value is None and not self.unavailable:
            raise SummaryError("値のない要約には、理由が要ります")
        if self.value is not None and self.unavailable:
            raise SummaryError("値と「求められない理由」は同時には持てません")

    @property
    def is_unweighted(self) -> bool:
        return self.weighting is Weighting.NONE

    def describe(self) -> str:
        """The line this number is shown as, wherever it is shown.

        The weighting is in the line rather than beside it, because the place a label goes missing is
        the place somebody reads the number (AC-023).
        """
        head = f"{REDUCTION_WORD[self.reduction]}（{WEIGHTING_WORD[self.weighting]}・{self.scope}）"
        if self.value is None:
            return f"{head}：求められません — {self.unavailable}"
        unit = f" {self.unit}" if self.unit else ""
        line = f"{head}：{self.value:g}{unit}（{self.entries} 件）"
        if self.skipped:
            line += f"・欠測 {self.skipped} 件は除外"
        return line


def summarise(
    values: Sequence[float] | np.ndarray,
    *,
    reduction: Reduction,
    association: Association,
    scope: str,
    weights: Sequence[float] | np.ndarray | None = None,
    weighting: Weighting | None = None,
    unit: str | None = None,
) -> Summary:
    """Reduce a field to one number, refusing the combinations that would mislead.

    `weighting` defaults to what the association implies (INV-017). Asking for a weighted reduction
    **without weights is refused**, not quietly downgraded to arithmetic: the downgrade produces a
    different number under the label of the one that was asked for, which is this invariant's whole
    subject.
    """
    chosen = weighting or DEFAULT_WEIGHTING.get(association, Weighting.NONE)
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise SummaryError(f"要約できるのは 1 次元の値です（{array.ndim} 次元が来ました）")

    present = ~np.isnan(array)
    skipped = int((~present).sum())
    kept = array[present]

    if kept.size == 0:
        # AC-024. Zero is a number a reader will compare against a limit.
        return Summary(
            reduction, chosen, scope, None, unit, 0, skipped,
            unavailable=(
                f"{scope} に有効な値がありません（欠測 {skipped} 件）。"
                "0 は返しません — 0 は読み手が上限と比べる数値で、「該当なし」は小さな平均ではありません"
            ),
        )

    if chosen is Weighting.NONE or reduction not in WEIGHTABLE:
        return Summary(
            reduction,
            chosen if reduction in WEIGHTABLE else Weighting.NONE,
            scope,
            _unweighted(reduction, kept),
            unit,
            int(kept.size),
            skipped,
        )

    if weights is None:
        raise SummaryError(
            f"{WEIGHTING_WORD[chosen]}の{REDUCTION_WORD[reduction]}が求められましたが、"
            "重みが渡されていません。重みなしに落とすことはしません — "
            "頼まれたものとは別の数値を、頼まれたものの名前で返すことになります（INV-017）"
        )
    weight_array = np.asarray(weights, dtype=np.float64)
    if weight_array.shape != array.shape:
        raise SummaryError(
            f"重みの数が値と合いません（値 {array.shape[0]} 件、重み {weight_array.shape[0]} 件）"
        )
    kept_weights = weight_array[present]
    if float(kept_weights.sum()) <= 0.0:
        return Summary(
            reduction, chosen, scope, None, unit, int(kept.size), skipped,
            unavailable=f"{scope} の重みの合計が 0 です。加重平均は定義できません",
        )

    return Summary(
        reduction, chosen, scope, _weighted(reduction, kept, kept_weights), unit,
        int(kept.size), skipped,
    )


def _unweighted(reduction: Reduction, values: np.ndarray) -> float:
    if reduction is Reduction.MEAN:
        return float(values.mean())
    if reduction is Reduction.MIN:
        return float(values.min())
    if reduction is Reduction.MAX:
        return float(values.max())
    if reduction in (Reduction.SUM, Reduction.INTEGRAL):
        return float(values.sum())
    if reduction is Reduction.STANDARD_DEVIATION:
        if values.size < 2:
            raise SummaryError("標準偏差には 2 件以上の値が要ります")
        return float(values.std(ddof=1))
    raise SummaryError(f"縮約 '{reduction}' の実装がありません")


def _weighted(reduction: Reduction, values: np.ndarray, weights: np.ndarray) -> float:
    total = float(weights.sum())
    if reduction is Reduction.MEAN:
        return float((values * weights).sum() / total)
    if reduction is Reduction.INTEGRAL:
        # Deliberately not a mean: the integral is what a weighted sum is, and calling it an average
        # would divide by a total nobody asked about.
        return float((values * weights).sum())
    if reduction is Reduction.SUM:
        return float((values * weights).sum())
    if reduction is Reduction.STANDARD_DEVIATION:
        if values.size < 2:
            raise SummaryError("標準偏差には 2 件以上の値が要ります")
        mean = (values * weights).sum() / total
        variance = float((weights * (values - mean) ** 2).sum() / total)
        return math.sqrt(variance)
    raise SummaryError(f"縮約 '{reduction}' に重みは使えません")


def dual_volumes(cell_volumes: Sequence[float], connectivity: Sequence[Sequence[int]], points: int) -> np.ndarray:
    """Each point's share of the volume around it, for weighting point data (INV-017).

    Each cell's volume is divided equally among the points it uses. That is the simplest rule that sums
    back to the total volume, which is the property a weighting has to have - a rule that did not would
    make the weighted mean depend on how the mesh was cut rather than on where the material is.

    A point no cell uses keeps a weight of zero, and a mean over a scope of only such points is
    unavailable rather than a division by zero.
    """
    shares = np.zeros(points, dtype=np.float64)
    for volume, cell in zip(cell_volumes, connectivity):
        if not len(cell):
            continue
        each = float(volume) / len(cell)
        for point in cell:
            shares[point] += each
    return shares
