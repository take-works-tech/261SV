"""Turning a graph definition into points, and keeping the gaps visible.

Three rules, and each of them is about what happens when something is missing.

**A case that lacks the plotted quantity is drawn as no data and stays in the legend** (AC-013). Dropping
it would make the figure look complete: five cases plotted where six were asked for, and nothing on the
page says which one is absent or why.

**An expression that cannot be evaluated for one case is that case's no-data, not the series'
deletion** (AC-007). The series survives with a reason against the case that failed, because a series
that vanished would take the other cases' answers with it.

**Nothing is computed here** (AC-006, XC-080, XC-088). An expression series is evaluated by MOD-004 and
this module records what came back. A graph layer that computed would be a second place where numbers
are produced, and the two would disagree on the day one of them was fixed.

Repeated studies are plotted **deliberately** (AC-012): each repeat separately or all repeats together,
and the result says which was used. Neither is the default that gets applied silently, and combining
does not average - an average is a number nobody asked for, and it would appear on the axis as though
it had been measured.

Specification: CT-005, graph/AC-005 to AC-007, AC-012, AC-013, XC-080, XC-088, INV-013.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Callable, Iterable, Mapping, Sequence

from engine.analysis.expression import ExpressionError, Value, evaluate
from engine.graph.definition import (
    UNDECLARED_MARKER,
    GraphError,
    Provenance,
    Series,
    SourceKind,
)


class Repeats(str, Enum):
    """How a repeated study is plotted (AC-012). Stated, never assumed."""

    PER_REPEAT = "perRepeat"   # one series per repeat, so a drifting repeat is visible
    COMBINED = "combined"      # every repeat's points under one label, spread and all


REPEAT_WORD = {
    Repeats.PER_REPEAT: "繰り返しごとに分けて描画",
    Repeats.COMBINED: "繰り返しをまとめて描画",
}


@dataclass(frozen=True, slots=True)
class Quantity:
    """A quantity a graph may plot, as it is offered to somebody building one (AC-005)."""

    name: str
    unit: str | None
    provenance: Provenance
    expression: str | None = None

    def describe(self) -> str:
        unit = self.unit if self.unit is not None else UNDECLARED_MARKER
        line = f"{self.name}［{unit}］"
        if self.expression:
            line += f"：{self.expression}"
        return line


@dataclass(frozen=True, slots=True)
class Point:
    """One case's contribution to a series - a value, or the absence of one with its reason.

    `value` of None is not zero and not a gap to be closed by the line that draws it. A missing value
    that arrives as zero is the failure XC-001 exists to prevent, so there is no numeric stand-in here
    to be mistaken for a measurement.
    """

    case_id: str
    value: float | None = None
    reason: str | None = None
    repeat: str | None = None

    @property
    def missing(self) -> bool:
        return self.value is None


@dataclass(frozen=True, slots=True)
class Plotted:
    """One series after evaluation: its points, and what had to be said about it."""

    label: str
    unit: str | None
    provenance: Provenance
    points: tuple[Point, ...]
    repeat: str | None = None
    notes: tuple[str, ...] = dataclass_field(default_factory=tuple)

    @property
    def missing_count(self) -> int:
        return sum(1 for point in self.points if point.missing)

    def describe(self) -> str:
        unit = self.unit if self.unit is not None else UNDECLARED_MARKER
        line = f"{self.label}［{unit}］{len(self.points)} 点"
        if self.missing_count:
            line += f"・うち {self.missing_count} 点はデータなし"
        for note in self.notes:
            line += f"・{note}"
        return line

    def in_legend(self) -> str:
        """What the legend shows. A series with nothing plotted still appears (AC-013)."""
        if self.missing_count == len(self.points) and self.points:
            return f"{self.label}（データなし）"
        return self.label


@dataclass(frozen=True, slots=True)
class Figure:
    """Everything a graph draws, with the repeat handling stated (AC-012)."""

    series: tuple[Plotted, ...]
    repeats: Repeats
    considered: tuple[str, ...] = dataclass_field(default_factory=tuple)

    def describe(self) -> str:
        head = f"{len(self.series)} 系列・対象 {len(self.considered)} ケース（{REPEAT_WORD[self.repeats]}）"
        return "\n".join([head, *(one.describe() for one in self.series)])

    def legend(self) -> tuple[str, ...]:
        return tuple(one.in_legend() for one in self.series)


def available_quantities(
    per_case: Mapping[str, Mapping[str, Value]],
    *,
    computed: Iterable[Quantity] = (),
    reference: Iterable[Quantity] = (),
) -> tuple[Quantity, ...]:
    """Every quantity the selected cases offer, in one list (AC-005).

    Read quantities, computed ones and values from an uploaded reference file, together - because a
    builder that offered only what came out of the solver would make the other two second-class, and
    they are the ones a comparison usually needs.

    A quantity present in some cases and not others is offered **once**, and the cases that lack it
    become no-data points when it is plotted (AC-013). Offering it per case would put the same name on
    the list six times.
    """
    found: dict[str, Quantity] = {}
    for values in per_case.values():
        for name, value in values.items():
            if name not in found:
                found[name] = Quantity(name, value.declared, Provenance.DATASET)
    for quantity in computed:
        found.setdefault(quantity.name, quantity)
    for quantity in reference:
        found.setdefault(quantity.name, quantity)
    return tuple(found.values())


def plot(
    series: Series,
    cases: Sequence[str],
    quantities_of: Callable[[str], Mapping[str, Value]],
    *,
    repeat_of: Callable[[str], str] | None = None,
) -> Plotted:
    """Evaluate one series over the cases, keeping every case in the result.

    A case that has no such quantity, and a case where an expression fails, both become a point with a
    reason. Neither removes the case from the series and neither removes the series from the figure.
    """
    points: list[Point] = []
    for case in cases:
        repeat = repeat_of(case) if repeat_of else None
        try:
            value = _value_for(series, quantities_of(case))
        except _NoValue as absence:
            points.append(Point(case, None, str(absence), repeat))
            continue
        points.append(Point(case, value, None, repeat))
    return Plotted(series.label, series.unit, series.provenance, tuple(points))


class _NoValue(Exception):
    """One case has no value for this series, with the reason it has none."""


def _value_for(series: Series, quantities: Mapping[str, Value]) -> float:
    if series.source is SourceKind.DERIVED or series.expression:
        return _evaluated(series, quantities)
    name = series.field_name or series.label
    held = quantities.get(name)
    if held is None:
        offered = "、".join(sorted(quantities)) or "（このケースには量がありません）"
        raise _NoValue(f"このケースに量 '{name}' がありません。あるのは：{offered}")
    return _number(held, name)


def _evaluated(series: Series, quantities: Mapping[str, Value]) -> float:
    """Evaluated by MOD-004, never here (AC-006, XC-080).

    A failure is this case's no-data with the evaluator's own reason, not a swallowed exception and not
    a zero: the reason is what tells somebody whether the expression is wrong or the case is.
    """
    if not series.expression:
        raise GraphError(f"系列 '{series.label}' は計算値ですが式がありません")
    try:
        result = evaluate(series.expression, quantities)
    except ExpressionError as error:
        raise _NoValue(f"式を評価できませんでした：{error}") from None
    return _number(result, series.label)


def _number(value: Value, name: str) -> float:
    if isinstance(value.magnitude, (bool, str)):
        raise _NoValue(f"'{name}' は数値ではありません（{value.describe()}）")
    return float(value.magnitude)


def figure(
    series: Iterable[Series],
    cases: Sequence[str],
    quantities_of: Callable[[str], Mapping[str, Value]],
    *,
    repeats: Repeats,
    repeat_of: Callable[[str], str] | None = None,
) -> Figure:
    """Every series over every case, with the repeat handling recorded (AC-012).

    `repeats` has no default. Which of the two a figure used changes what it shows - one drifting repeat
    is visible in the first and hidden in the second - and a product that picked for the user would be
    choosing which of those they saw.
    """
    if repeats is Repeats.PER_REPEAT and repeat_of is None:
        raise GraphError(
            "繰り返しごとに分けて描くには、どのケースがどの繰り返しかを決める規則が要ります。"
            "推測はしません — 名前の似たケースを同じ繰り返しにまとめるのは、"
            "利用者が言っていないグループ分けです"
        )
    drawn: list[Plotted] = []
    for one in series:
        plotted = plot(one, cases, quantities_of, repeat_of=repeat_of)
        if repeats is Repeats.COMBINED:
            drawn.append(
                Plotted(
                    plotted.label, plotted.unit, plotted.provenance, plotted.points,
                    notes=(REPEAT_WORD[repeats],),
                )
            )
            continue
        for name in _repeat_names(plotted.points):
            inside = tuple(point for point in plotted.points if point.repeat == name)
            drawn.append(
                Plotted(
                    f"{plotted.label}（{name}）", plotted.unit, plotted.provenance, inside,
                    repeat=name, notes=(REPEAT_WORD[repeats],),
                )
            )
    return Figure(tuple(drawn), repeats, tuple(cases))


def _repeat_names(points: Sequence[Point]) -> tuple[str, ...]:
    """The repeats in the order they first appear, so the legend is stable between runs."""
    seen: list[str] = []
    for point in points:
        name = point.repeat or ""
        if name not in seen:
            seen.append(name)
    return tuple(seen)


def missing_report(figure_: Figure) -> tuple[str, ...]:
    """One line per case that could not be plotted, with the reason (AC-007, AC-013).

    Produced from the figure rather than collected while drawing, so a renderer that never ran still
    has the same answer about what is missing.
    """
    lines: list[str] = []
    for one in figure_.series:
        for point in one.points:
            if point.missing:
                lines.append(f"{one.label} / {point.case_id}：{point.reason}")
    return tuple(lines)
