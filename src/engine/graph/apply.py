"""Applying a graph template to a different study, and naming what did not come across.

XC-090's rule, in the one place it has a shape of its own: **a template applies as far as it resolves
and names what it could not**. A graph series whose quantity is absent in the target is drawn as **no
data** rather than omitted - and this module is where "which series, and what was missing" is answered,
because the generic machinery in MOD-007 works on requirement names and a report needs the series.

Two things this deliberately does.

**The requirements come from the definition** rather than from a list somebody maintained beside it. A
template's requirements are a promise to whoever applies it, and a promise written by hand next to the
thing it describes is one that stops matching after the third edit.

**An unresolved series stays in the definition.** Removing it would make the applied graph look complete
and quietly smaller than the one it came from, which is the failure XC-090 exists to prevent - and the
series module already draws a quantity it cannot find as no data with a reason (AC-013), so keeping it
is all that is needed.

Style is separate from structure and resolves separately (AC-017): a style key the target cannot honour
is dropped and named, and the applied graph says which scope the style came from. A style that failed
silently would leave somebody comparing two figures that differ for a reason neither shows.

Specification: CT-005, CT-008, XC-090, XC-109, graph/AC-017 to AC-019.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Any, Iterable, Mapping

from engine.graph.definition import GraphError, read_series


class Scope(str, Enum):
    """Where a library entry lives (CT-008). Shown wherever one is applied (AC-017)."""

    SAMPLE = "sample"
    WORKSPACE = "workspace"
    SHARED = "shared"


SCOPE_WORD = {
    Scope.SAMPLE: "サンプル",
    Scope.WORKSPACE: "ワークスペース",
    Scope.SHARED: "共有ライブラリ",
}

#: The keys of a CT-005 definition that a style may set. Written out, because a style that could set
#: anything could set the **series** - and a style that changes which numbers are plotted is not a
#: style.
STYLEABLE = frozenset({"axes", "kind", "style"})


@dataclass(frozen=True, slots=True)
class MissingSeries:
    """One series that did not come across, and what it wanted."""

    label: str
    needed: str

    def describe(self) -> str:
        return f"{self.label}（'{self.needed}' が見つかりません）"


@dataclass(frozen=True, slots=True)
class Applied:
    """What applying a graph template here produces, before anything is created.

    The definition is included **whole**, unresolved series and all. A caller draws it and the missing
    series arrive as no data with their reasons; a caller that wanted them gone would have to remove
    them deliberately, which is the right way round.
    """

    definition: dict[str, Any]
    scope: Scope
    resolved: tuple[str, ...] = dataclass_field(default_factory=tuple)
    missing: tuple[MissingSeries, ...] = dataclass_field(default_factory=tuple)
    style_dropped: tuple[str, ...] = dataclass_field(default_factory=tuple)

    @property
    def resolves_completely(self) -> bool:
        return not self.missing and not self.style_dropped

    def describe(self) -> str:
        line = f"{SCOPE_WORD[self.scope]}のテンプレートから適用します"
        if self.resolves_completely:
            return line + f"。{len(self.resolved)} 系列すべてが解決します"
        line += f"。{len(self.resolved)} 系列は解決します"
        if self.missing:
            named = "、".join(one.describe() for one in self.missing)
            line += (
                f"。{len(self.missing)} 系列は解決しません：{named}。"
                "系列は残し、データなしとして描きます（XC-090）"
            )
        if self.style_dropped:
            line += f"。書式のうち {'、'.join(self.style_dropped)} はこの対象に当てられません"
        return line


def series_requirements(definition: Mapping[str, Any]) -> tuple[str, ...]:
    """The quantity names a graph definition needs, read from the definition itself.

    A series computed by an expression needs whatever the expression names, and this does not try to
    work that out - an expression's names are the evaluator's business (`expression.names_in`), and a
    second parser here would be a second answer. What this returns is the fields the series read
    directly, which is what a template's requirements are made of.
    """
    found: list[str] = []
    for series in read_series(dict(definition)):
        name = series.field_name
        if name and name not in found:
            found.append(name)
    return tuple(found)


def apply_template(
    definition: Mapping[str, Any],
    *,
    available: Iterable[str],
    scope: Scope,
    style: Mapping[str, Any] | None = None,
) -> Applied:
    """What this template resolves to here (AC-017, AC-018, AC-019).

    Returns a **copy**. A shared structure would make a later edit to the template reach into a graph
    somebody already sent (XC-109), and the whole point of a template is that the two part company at
    the moment of application.
    """
    have = set(available)
    copied = _copy(definition)
    resolved: list[str] = []
    missing: list[MissingSeries] = []

    for series in read_series(copied):
        name = series.field_name
        if name is None or name in have:
            resolved.append(series.label)
            continue
        missing.append(MissingSeries(series.label, name))

    dropped: list[str] = []
    if style:
        for key, value in style.items():
            if key not in STYLEABLE:
                # Named rather than ignored: a style key nobody honours is a difference between two
                # figures that neither of them shows.
                dropped.append(key)
                continue
            copied[key] = _copy(value) if isinstance(value, (dict, list)) else value

    return Applied(copied, scope, tuple(resolved), tuple(missing), tuple(dropped))


def _copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy(item) for item in value]
    return value


def accept(applied: Applied, identifier: str, name: str) -> dict[str, Any]:
    """Turn an accepted resolution into an independent graph definition (XC-090, XC-109).

    Takes the resolution rather than the template, so a graph cannot be created without a resolution
    result having existed - the gaps were on screen before the thing was made, not after.

    The source template is **provenance, not a live link**: the new graph carries where it came from
    and nothing later reaches back through it.
    """
    if not applied.definition.get("series"):
        raise GraphError(
            "系列のないテンプレートからはグラフを作りません。"
            "空の図は、解決しなかったことと区別がつきません"
        )
    made = _copy(applied.definition)
    made["id"] = identifier
    made["name"] = name
    made["appliedFromScope"] = applied.scope.value
    if applied.missing:
        # Recorded on the artefact, not only in the moment of applying it: somebody opening this graph
        # next month reads the graph, not the dialogue that made it.
        made["unresolvedSeries"] = [
            {"label": one.label, "needed": one.needed} for one in applied.missing
        ]
    return made


def unresolved_of(definition: Mapping[str, Any]) -> tuple[MissingSeries, ...]:
    """What an applied graph recorded as unresolved when it was made (AC-019)."""
    return tuple(
        MissingSeries(str(one.get("label", "")), str(one.get("needed", "")))
        for one in definition.get("unresolvedSeries", []) or []
    )
