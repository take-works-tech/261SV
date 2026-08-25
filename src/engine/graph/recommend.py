"""Figures this product can propose from the data alone, each naming the signal behind it.

**A proposal is a suggestion of a figure, never a statement about the physics** (AC-014). "These two are
correlated" is a measurement about a set of numbers; "this drives that" is a claim about a mechanism,
and nothing here is entitled to make one. The vocabulary the report standard bans is banned here for the
same reason it is banned there (E-071): a proposal that arrives phrased as a conclusion has skipped the
step where somebody decides whether it is one.

**Every proposal names its signal with the figures behind it** - `r = 0.93 over 12 cases, 2 without a
value` - rather than "these look related". A recommendation with no number attached cannot be judged and
cannot be wrong, which is the same thing.

**Nothing is applied.** Proposals are offered, and a rejected one does not come back in the same
session (AC-016). Repeating a suggestion somebody has already declined is how a helpful feature becomes
one people turn off.

The signals are deliberately few and deliberately conservative. Each has a **minimum** below which it is
not offered at all, because a correlation over two cases is 1.0 by construction and an interesting-
looking spread over three is not a distribution.

Specification: graph/AC-014, AC-016, XC-013, E-071, INV-013, INV-031.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Iterable, Mapping, Sequence

import numpy as np

from engine.analysis.expression import Value

#: Below this many cases a correlation says nothing: over two points it is 1.0 whatever the numbers are.
MINIMUM_FOR_CORRELATION = 5

#: Below this many cases a spread is a handful of values rather than a distribution.
MINIMUM_FOR_DISTRIBUTION = 8

#: Below this the correlation is not worth a figure. A judgement, not a measurement - it is the point
#: at which somebody would look, not a threshold anything physical crosses.
NOTABLE_CORRELATION = 0.7

#: A quantity whose values are all within this fraction of each other has nothing to plot a spread of.
FLAT_FRACTION = 1.0e-6


class Kind(str, Enum):
    """What the proposed figure would show. Three, matching AC-014's own list."""

    CORRELATION = "correlation"
    DISTRIBUTION = "distribution"
    OVER_TIME = "overTime"


KIND_WORD = {
    Kind.CORRELATION: "相関",
    Kind.DISTRIBUTION: "分布",
    Kind.OVER_TIME: "時間変化",
}


@dataclass(frozen=True, slots=True)
class Proposal:
    """One suggested figure, with the measurement that suggested it.

    `signal` is the sentence a person reads to decide whether to accept it, and it carries the figures.
    `identity` is what a rejection remembers - the same figure proposed again is the same proposal, and
    two proposals over the same quantities in the other order are not two proposals.
    """

    kind: Kind
    quantities: tuple[str, ...]
    signal: str
    strength: float

    @property
    def identity(self) -> tuple[str, ...]:
        return (self.kind.value, *sorted(self.quantities))

    def describe(self) -> str:
        return f"{KIND_WORD[self.kind]}：{'、'.join(self.quantities)} — {self.signal}"


@dataclass(slots=True)
class Session:
    """What has been declined, for as long as somebody is working.

    Held for the session and not stored: a proposal declined today because the study was half loaded is
    one worth making again next week, and a permanent refusal list would be a product that quietly
    stops suggesting things.
    """

    rejected: set[tuple[str, ...]] = dataclass_field(default_factory=set)

    def reject(self, proposal: Proposal) -> None:
        self.rejected.add(proposal.identity)

    def allows(self, proposal: Proposal) -> bool:
        return proposal.identity not in self.rejected


def _paired(
    per_case: Mapping[str, Mapping[str, Value]], left: str, right: str
) -> tuple[np.ndarray, np.ndarray, int]:
    """The cases where both quantities have a value, and how many were left out.

    Pairwise deletion, stated. A correlation computed over the cases that happen to have both is a
    correlation over a different set from the one somebody selected, and the count is what says so.
    """
    a: list[float] = []
    b: list[float] = []
    missing = 0
    for values in per_case.values():
        one, other = values.get(left), values.get(right)
        if one is None or other is None:
            missing += 1
            continue
        if isinstance(one.magnitude, (bool, str)) or isinstance(other.magnitude, (bool, str)):
            missing += 1
            continue
        if math.isnan(float(one.magnitude)) or math.isnan(float(other.magnitude)):
            missing += 1
            continue
        a.append(float(one.magnitude))
        b.append(float(other.magnitude))
    # float64 throughout, whatever the fields were stored in (INV-031).
    return np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64), missing


def correlation(a: np.ndarray, b: np.ndarray) -> float | None:
    """Pearson's r, or None where it is not defined.

    None rather than zero where either quantity does not vary: a constant has no correlation with
    anything, and zero would read as "measured, and unrelated".
    """
    if a.size < 2 or b.size < 2:
        return None
    if float(a.std()) == 0.0 or float(b.std()) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _values_of(per_case: Mapping[str, Mapping[str, Value]], name: str) -> np.ndarray:
    found = [
        float(values[name].magnitude)
        for values in per_case.values()
        if name in values and not isinstance(values[name].magnitude, (bool, str))
    ]
    array = np.asarray(found, dtype=np.float64)
    return array[~np.isnan(array)]


def propose(
    per_case: Mapping[str, Mapping[str, Value]],
    *,
    with_sequences: Iterable[str] = (),
    session: Session | None = None,
) -> tuple[Proposal, ...]:
    """Figures worth offering, from the data alone (AC-014).

    `with_sequences` names the quantities that have a result axis, which is the only thing an
    over-time proposal needs to know - **whether** a quantity varies along a sequence is a fact about
    the file, and this module does not guess it from the values (XC-240).

    Ordered by strength, so a caller showing three shows the three with the most behind them.
    """
    found: list[Proposal] = []
    names = sorted({name for values in per_case.values() for name in values})

    for index, left in enumerate(names):
        for right in names[index + 1:]:
            a, b, missing = _paired(per_case, left, right)
            if a.size < MINIMUM_FOR_CORRELATION:
                continue
            r = correlation(a, b)
            if r is None or abs(r) < NOTABLE_CORRELATION:
                continue
            without = f"、{missing} 件は値がありません" if missing else ""
            found.append(
                Proposal(
                    Kind.CORRELATION,
                    (left, right),
                    f"r = {r:.2f}（{a.size} ケース{without}）。"
                    "数値どうしの関係であって、原因を示すものではありません",
                    abs(r),
                )
            )

    for name in names:
        values = _values_of(per_case, name)
        if values.size < MINIMUM_FOR_DISTRIBUTION:
            continue
        spread = float(values.max() - values.min())
        largest = float(np.abs(values).max())
        if largest == 0.0 or spread / largest < FLAT_FRACTION:
            continue
        found.append(
            Proposal(
                Kind.DISTRIBUTION,
                (name,),
                f"{values.size} ケースで {values.min():g} から {values.max():g} まで"
                f"広がっています（幅は最大値の {spread / largest:.0%}）",
                min(1.0, spread / largest),
            )
        )

    for name in sorted(set(with_sequences)):
        if name not in names:
            continue
        found.append(
            Proposal(
                Kind.OVER_TIME,
                (name,),
                "この量はファイルが宣言した系列に沿って変化します（系列の種類はファイルの宣言に従います）",
                0.5,
            )
        )

    allowed = [one for one in found if session is None or session.allows(one)]
    return tuple(sorted(allowed, key=lambda one: (-one.strength, one.identity)))


def describe_all(proposals: Sequence[Proposal]) -> str:
    """The proposals as a person reads them, or the statement that there are none.

    "Nothing to suggest" is an answer. A feature that always finds something is one that is finding it
    in the noise.
    """
    if not proposals:
        return (
            "提案できる図はありません。"
            "何も出ないことは結果です — 常に何か見つける機能は、雑音の中に見つけています"
        )
    return "\n".join(one.describe() for one in proposals)
