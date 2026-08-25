"""A graph as a definition over quantities: what is plotted, in what unit, and where it came from.

**The definition is what is saved, never the plotted values** (AC-004). A figure that stored its numbers
would still draw after the study changed, showing last week's answer under this week's title - and it
would look right, which is the failure this product exists to avoid.

**Every series carries its provenance** (INV-013): declared by a person, read from data, computed, or
taken from reference material, and a computed one carries its expression. The variable list deliberately
mixes values a person typed with values a solver produced (XC-088). Mixing them is convenient; mixing
them invisibly would make every number in the product unfalsifiable.

**A unit nobody declared is marked, not assumed** (AC-002, XC-003), and two series whose units do not
combine are refused with **both named** (AC-003). The mixed case is the one worth being strict about: a
declared series and an undeclared one on one axis reads as agreement between them, and nothing said the
undeclared one was in the same unit.

Nothing here computes a value. Expressions are evaluated by MOD-004 and appear as quantities (XC-080,
XC-088); this module records what was plotted and refuses combinations that would mislead.

Specification: CT-005, INV-013, XC-003, XC-080, XC-088, XC-131, graph/AC-001 to AC-004.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Sequence

from domain_core.case_contents import ResultAxis, differing_axes
from domain_core.dimension import Dimension, parse_symbol, symbol_for
from domain_core.reported_value import UNDECLARED_MARKER, Provenance
from domain_core.units import UndeclaredUnitError




class GraphError(Exception):
    """Raised for a definition that would draw something misleading."""


class SourceKind(str, Enum):
    """CT-005's three source kinds."""

    FIELD = "field"
    DERIVED = "derived"
    REFERENCE_FILE = "referenceFile"


#: GL-016's five, in words. The vocabulary is `domain_core.reported_value.Provenance` and not a second
#: one here: a graph that called the same origin `read` while a report called it `dataset` would make the
#: same value look like two.
PROVENANCE_WORD = {
    Provenance.DECLARED: "宣言値",
    Provenance.DATASET: "ファイル由来",
    Provenance.COMPUTED: "計算値",
    Provenance.MEASURED: "実測値",
    Provenance.REFERENCE: "参考資料由来",
}


@dataclass(frozen=True, slots=True)
class Series:
    """One line on a graph, with everything needed to say what it is.

    `unit` is None where nobody declared one - not an empty string, which reads as a unit that happens
    to print as nothing.
    """

    label: str
    source: SourceKind
    provenance: Provenance
    unit: str | None = None
    dataset_id: str | None = None
    field_name: str | None = None
    association: str | None = None
    expression: str | None = None
    path: str | None = None

    def __post_init__(self) -> None:
        if self.provenance is Provenance.COMPUTED and not self.expression:
            raise GraphError(
                f"系列 '{self.label}' は計算値ですが式がありません。"
                "INV-013 は計算値にその式を添えることを求めています — "
                "式のない計算値は、確かめようのない数字です"
            )
        if self.source is SourceKind.REFERENCE_FILE and not self.path:
            raise GraphError(f"系列 '{self.label}' は参考ファイル由来ですが出所がありません")
        if self.unit == "":
            raise GraphError(
                f"系列 '{self.label}' の単位が空文字です。"
                "宣言がないなら None です — 空文字は「何も印字しない単位」に読めます"
            )
        if self.unit is not None:
            try:
                parse_symbol(self.unit)
            except (KeyError, ValueError, UndeclaredUnitError) as error:
                raise GraphError(f"系列 '{self.label}'：{error}") from None

    @property
    def unit_declared(self) -> bool:
        return self.unit is not None

    @property
    def dimension(self) -> Dimension | None:
        return parse_symbol(self.unit).dimension if self.unit is not None else None

    def describe(self) -> str:
        """The series as it is labelled: what it plots, in what unit, from where (INV-013)."""
        unit = self.unit if self.unit is not None else UNDECLARED_MARKER
        line = f"{self.label}［{unit}］（{PROVENANCE_WORD[self.provenance]}）"
        if self.expression:
            line += f"：{self.expression}"
        return line

    def as_stored(self) -> dict[str, Any]:
        """The CT-005 form. Values are not among the fields, and that is the point (AC-004)."""
        source: dict[str, Any] = {"kind": self.source.value}
        for key, value in (
            ("datasetId", self.dataset_id),
            ("fieldName", self.field_name),
            ("association", self.association),
            ("expression", self.expression),
            ("path", self.path),
        ):
            if value is not None:
                source[key] = value
        stored: dict[str, Any] = {
            "label": self.label,
            "source": source,
            "unitDeclared": self.unit_declared,
        }
        if self.unit is not None:
            stored["unit"] = self.unit
        return stored


def axis_label(series: Sequence[Series]) -> str:
    """What the value axis says, given everything on it.

    An axis carrying no declared unit says so (AC-002). One carrying declared units says the internal
    unit of the quantity, because that is what the plotted numbers are in - labelling it with whichever
    symbol the first series happened to use would be a number shown in one unit and labelled with
    another.
    """
    if not series:
        return UNDECLARED_MARKER
    if all(one.unit is None for one in series):
        return UNDECLARED_MARKER
    dimension = next(one.dimension for one in series if one.dimension is not None)
    return symbol_for(dimension) or UNDECLARED_MARKER


def refusal_for(series: Sequence[Series]) -> str | None:
    """Why these series may not share one axis, or None.

    Two cases, and the second is the one that looks harmless. **Different dimensions** is the obvious
    refusal - a length beside a time. **A declared unit beside an undeclared one** is the quiet one: the
    figure reads as a comparison, and nothing ever said the undeclared series was in the same unit as
    the other (XC-003).
    """
    if len(series) < 2:
        return None
    declared = [one for one in series if one.unit is not None]
    undeclared = [one for one in series if one.unit is None]
    if declared and undeclared:
        return (
            f"同じ軸に、単位が宣言された系列（{declared[0].unit}）と宣言のない系列"
            f"（'{undeclared[0].label}'）が並んでいます。"
            "並べれば比較に読めますが、宣言のない側が同じ単位である保証はどこにもありません（XC-003）"
        )
    for one in declared[1:]:
        if one.dimension != declared[0].dimension:
            return (
                f"同じ軸に組み合わせられない単位があります：{declared[0].unit} と {one.unit}。"
                "換算できる同じ量どうしでなければ、一本の軸には載せません"
            )
    return None


def new_graph(identifier: str, name: str, kind: str) -> dict[str, Any]:
    """An empty CT-005 definition."""
    if kind not in KINDS:
        raise GraphError(f"グラフの種類 '{kind}' は CT-005 の一覧にありません（{sorted(KINDS)}）")
    return {"id": identifier, "name": name, "kind": kind, "series": []}


#: CT-005's enumeration, held here so a kind this build cannot draw is refused when it is written
#: rather than when somebody opens the figure.
KINDS = frozenset(
    {"line", "scatter", "bar", "histogram", "overTime", "overLine",
     "surface3d", "scatter3d", "contour3d"}
)


def add_series(graph: dict[str, Any], series: Series) -> dict[str, Any]:
    """Add a series, or refuse the combination with both units named (AC-003).

    Validated before it goes in, so a definition is never briefly holding a combination the product
    would refuse to draw.
    """
    present = read_series(graph)
    refusal = refusal_for([*present, series])
    if refusal is not None:
        raise GraphError(refusal)
    graph.setdefault("series", []).append(series.as_stored())
    return graph


def read_series(graph: dict[str, Any]) -> list[Series]:
    """The series of a stored definition, back as objects.

    A definition read from a document is the same thing as one built in memory, so the rules that
    refused a bad combination on the way in also refuse it on the way out.
    """
    found: list[Series] = []
    for stored in graph.get("series", []):
        source = stored.get("source", {})
        unit = stored.get("unit")
        declared = stored.get("unitDeclared")
        if declared is False and unit is not None:
            raise GraphError(
                f"系列 '{stored.get('label')}' は単位未宣言と書かれているのに単位 '{unit}' を"
                "持っています。どちらが本当かはこちらでは決められません"
            )
        found.append(
            Series(
                label=str(stored.get("label", "")),
                source=SourceKind(source.get("kind", "field")),
                provenance=_provenance_of(source),
                unit=unit,
                dataset_id=source.get("datasetId"),
                field_name=source.get("fieldName"),
                association=source.get("association"),
                expression=source.get("expression"),
                path=source.get("path"),
            )
        )
    return found


def _provenance_of(source: dict[str, Any]) -> Provenance:
    kind = SourceKind(source.get("kind", "field"))
    if kind is SourceKind.REFERENCE_FILE:
        return Provenance.REFERENCE
    if kind is SourceKind.DERIVED or source.get("expression"):
        return Provenance.COMPUTED
    return Provenance.DATASET


def note_result_axes(graph: dict[str, Any], axes: Iterable[ResultAxis]) -> str | None:
    """Record what must be said where series come from different result axes (XC-131).

    The statement is produced by `domain_core.case_contents` rather than composed here: a mode index
    beside a time means the horizontal position is a different thing in each series, and a display site
    that phrased that itself would be one more place for it to go missing.
    """
    note = differing_axes(*axes)
    if note is None:
        graph.pop("resultAxisNote", None)
        return None
    graph["resultAxisNote"] = note
    return note


def stored_values(graph: dict[str, Any]) -> list[Any]:
    """Any plotted numbers found in a definition. Should always be empty (AC-004).

    Exists to be asserted against rather than to be called in anger: a definition that acquired a cached
    series would keep drawing after the study changed, showing last week's answer under this week's
    title.
    """
    found: list[Any] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("values", "data", "points", "cached"):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(graph)
    return found
