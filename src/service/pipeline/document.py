"""A pipeline as it is edited: units in an order, each pinned to what it acts through.

A @Pipeline is built by editing rather than by recording (REQ-001), which means every rule here is
enforced **at edit time** rather than when somebody presses run. A pipeline that only reveals its
problems on the night it runs is a pipeline nobody can plan a study around.

Four rules that each rule out a plausible alternative.

**A reference says whether it is a workspace item or a template, and is never inferred** (AC-042). The
two have separate identity and lifecycle (XC-109), and a product that guessed from the identifier would
silently follow whichever one still existed.

**A reference never falls forward to a later revision.** A pinned revision that quietly becomes the
newest one is a pipeline whose output changed because somebody else edited a template.

**A missing reference keeps its unit and refuses the run** (AC-003). Removing the unit would lose the
user's work over somebody else's deletion; running without it would produce a study missing a step
nobody noticed.

**Several cases dropped together become one unit holding all of them** (AC-023). Six units of one case
each look the same on screen and behave differently the moment somebody reorders or removes one.

Specification: CT-009, LIM-007, XC-109, pipeline/AC-001 to AC-007, AC-023, AC-042.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from typing import Any, Iterable, Iterator

from engine.analysis.expression import ExpressionError, check
from engine.limits import MAX_PIPELINE_DEPTH


class Kind(str, Enum):
    """What a unit does. CT-009's enumeration, which is closed on purpose."""

    ADD_CASES = "addCases"
    CLEAR = "clear"
    VIEW = "view"
    GRAPH = "graph"
    REPORT = "report"
    EXPORT = "export"
    TAG = "tag"
    LOOP = "loop"
    VARIABLE = "variable"
    FORMULA = "formula"
    CONDITION = "condition"
    SIMULATION = "simulation"


class Source(str, Enum):
    """Where a unit's definition comes from. Stated, never inferred (AC-042)."""

    WORKSPACE_ITEM = "workspaceItem"
    TEMPLATE = "template"


#: The kinds that may contain other units, each consuming one level of LIM-007's depth. Written out
#: rather than derived from "has a units field", so adding a container is a decision somebody makes
#: here rather than a side effect of a schema edit.
CONTAINERS = frozenset({Kind.LOOP, Kind.CONDITION, Kind.SIMULATION})

#: The kinds that act on the target set rather than changing it. What they have in common is that
#: running one with an empty set is a skip rather than a failure (AC-007).
ACT_ON_TARGETS = frozenset({Kind.VIEW, Kind.GRAPH, Kind.REPORT, Kind.EXPORT, Kind.TAG})

#: The kinds whose definition must be pinned to something that exists.
NEED_DEFINITION = frozenset({Kind.VIEW, Kind.GRAPH, Kind.REPORT, Kind.SIMULATION})

#: The kinds that carry an @Expression, and therefore get checked when they are written rather than
#: when they run (AC-032).
CARRY_EXPRESSION = frozenset({Kind.FORMULA, Kind.CONDITION})

#: The kinds that bind a name for the units below them (AC-029).
BIND_A_NAME = frozenset({Kind.VARIABLE, Kind.FORMULA})

#: What a loop counts. XC-100 fixes the count before the loop begins, and these are the three sources
#: it may come from - there is no `while` and no user-written early exit.
COUNT_LITERAL = "count"
COUNT_FROM_VARIABLE = "countFromVariable"
COUNT_PER_CASE = "countPerCase"
COUNT_SOURCES = (COUNT_LITERAL, COUNT_FROM_VARIABLE, COUNT_PER_CASE)

#: What a loop calls its index where the unit does not say. Written here rather than defaulted at each
#: reader, so a pipeline that omits the name still means one thing.
DEFAULT_INDEX_NAME = "index"


class PipelineError(Exception):
    """Raised for an edit that would leave a pipeline that cannot be read or cannot be run."""


@dataclass(frozen=True, slots=True)
class DefinitionRef:
    """What a unit acts through, pinned."""

    source: Source
    identifier: str
    revision: int

    def as_stored(self) -> dict[str, Any]:
        return {"source": self.source.value, "id": self.identifier, "revision": self.revision}

    def describe(self) -> str:
        word = "ワークスペース項目" if self.source is Source.WORKSPACE_ITEM else "テンプレート"
        return f"{word} '{self.identifier}' 第 {self.revision} 版"


def kind_of(unit: dict[str, Any]) -> Kind:
    stated = str(unit.get("kind", ""))
    try:
        return Kind(stated)
    except ValueError:
        raise PipelineError(
            f"ユニットの種類 '{stated}' は CT-009 の一覧にありません（{[k.value for k in Kind]}）"
        ) from None


def reference_of(unit: dict[str, Any]) -> DefinitionRef | None:
    """A unit's pinned reference, or None where it has none.

    Refuses a reference missing its source or its revision rather than filling either in. A revision
    this build supplied is a pin nobody chose, and it would follow whatever the newest one happened to
    be on the day it ran.
    """
    stated = unit.get("definitionRef")
    if stated is None:
        return None
    for required in ("source", "id", "revision"):
        if required not in stated:
            raise PipelineError(
                f"ユニット '{unit.get('id')}' の参照に {required} がありません。"
                "補完はしません — こちらが補った版は誰も選んでいない固定であり、"
                "実行日の最新版に追随してしまいます（AC-042）"
            )
    try:
        source = Source(str(stated["source"]))
    except ValueError:
        raise PipelineError(
            f"参照の source が '{stated['source']}' です。"
            f"{[s.value for s in Source]} のいずれかで、識別子からの推測はしません（XC-109）"
        ) from None
    return DefinitionRef(source, str(stated["id"]), int(stated["revision"]))


def walk(units: Iterable[dict[str, Any]], depth: int = 1) -> Iterator[tuple[dict[str, Any], int]]:
    """Every unit with the level it sits at, outermost first."""
    for unit in units:
        yield unit, depth
        for contained in unit.get("units", []) or []:
            yield from walk([contained], depth + 1)


def depth_of(units: Iterable[dict[str, Any]]) -> int:
    """The deepest level any unit sits at. Every container costs one level, whichever kind it is."""
    return max((level for _, level in walk(units)), default=0)


def add_cases_unit(unit_id: str, case_ids: Iterable[str], *, label: str | None = None) -> dict[str, Any]:
    """One unit holding a whole multiple selection (AC-023).

    Six units of one case each look the same on screen and behave differently the moment somebody
    reorders or removes one.
    """
    cases = [str(case) for case in case_ids]
    if not cases:
        raise PipelineError("ケースユニットには少なくとも 1 件のケースが必要です")
    unit: dict[str, Any] = {"id": unit_id, "kind": Kind.ADD_CASES.value, "caseIds": cases}
    if label:
        unit["label"] = label
    return unit


def artefact_unit(
    unit_id: str, kind: Kind, reference: DefinitionRef, *, label: str | None = None
) -> dict[str, Any]:
    """A unit that acts through a pinned view, graph, report or simulation."""
    if kind not in NEED_DEFINITION:
        raise PipelineError(f"{kind.value} は定義参照を持ちません")
    unit: dict[str, Any] = {
        "id": unit_id, "kind": kind.value, "definitionRef": reference.as_stored()
    }
    if label:
        unit["label"] = label
    return unit


def variable_unit(
    unit_id: str,
    name: str,
    *,
    value: float | None = None,
    values: Iterable[float] | None = None,
    unit_symbol: str | None = None,
    quantity_kind: str | None = None,
    to_workspace: bool = False,
) -> dict[str, Any]:
    """A unit that binds a name for the units below it (AC-029).

    It does **not** change the @Workspace's own variables unless `to_workspace` says to. A pipeline that
    quietly rewrote a workspace variable would change every other pipeline that reads it, and the change
    would be invisible from the pipeline that made it.

    `values` is the several-valued form, which is what a loop counts over (XC-100).

    `quantity_kind` is INV-028's absolute-or-difference, and it is written under **`quantityKind`**
    rather than `kind`. A unit already has a `kind` - `variable`, `formula`, `loop` - and handing the
    whole unit to a reader of quantity kinds made it read "variable" as a temperature scale and refuse.
    Two meanings of one word in one document is the kind of collision that is invisible until it is a
    wrong number.
    """
    if (value is None) == (values is None):
        raise PipelineError(
            f"変数ユニット '{unit_id}' には value か values のどちらか一方が要ります"
        )
    unit: dict[str, Any] = {"id": unit_id, "kind": Kind.VARIABLE.value, "name": name}
    if values is not None:
        listed = [float(item) for item in values]
        if not listed:
            raise PipelineError(f"変数ユニット '{unit_id}' の values が空です")
        unit["values"] = listed
    else:
        unit["value"] = float(value)  # type: ignore[arg-type]
    if unit_symbol:
        unit["unit"] = unit_symbol
    if quantity_kind:
        unit["quantityKind"] = quantity_kind
    if to_workspace:
        unit["toWorkspace"] = True
    return unit


def formula_unit(unit_id: str, name: str, expression: str) -> dict[str, Any]:
    """A unit that evaluates an @Expression and binds the result **with the unit it produced** (AC-030)."""
    return {
        "id": unit_id, "kind": Kind.FORMULA.value, "name": name, "expression": expression
    }


def condition_unit(unit_id: str, expression: str) -> dict[str, Any]:
    """A container whose contents run when its @Expression is true and are recorded when it is false."""
    return {"id": unit_id, "kind": Kind.CONDITION.value, "expression": expression, "units": []}


def loop_unit(
    unit_id: str,
    *,
    count: int | None = None,
    over_variable: str | None = None,
    per_case: bool = False,
    index_name: str = DEFAULT_INDEX_NAME,
) -> dict[str, Any]:
    """A container that repeats its contents a number of times fixed before it begins (XC-100).

    Exactly one of the three sources. Accepting more than one would mean the product choosing which
    count a pipeline meant, and the two would disagree on the day somebody edited only one of them.
    """
    stated = [count is not None, over_variable is not None, per_case]
    if sum(stated) != 1:
        raise PipelineError(
            f"ループ '{unit_id}' の回数の指定は 1 つだけです"
            f"（{COUNT_LITERAL}／{COUNT_FROM_VARIABLE}／{COUNT_PER_CASE}）"
        )
    unit: dict[str, Any] = {
        "id": unit_id, "kind": Kind.LOOP.value, "indexName": index_name, "units": []
    }
    if count is not None:
        if count < 1:
            raise PipelineError(f"ループ '{unit_id}' の回数は 1 以上です（{count} が来ました）")
        unit[COUNT_LITERAL] = int(count)
    elif over_variable is not None:
        unit[COUNT_FROM_VARIABLE] = over_variable
    else:
        unit[COUNT_PER_CASE] = True
    return unit


def names_bound_before(
    pipeline: dict[str, Any], unit_id: str, *, outside: Iterable[str] = ()
) -> tuple[str, ...]:
    """Every name in scope at the position a unit sits at.

    In scope means: bound by a variable or formula unit **above** it at the same level or at an enclosing
    one, plus the index name of every loop it is inside, plus whatever the workspace supplies. A name
    bound inside a sibling container is not in scope, which is the point - a formula that read one would
    work until somebody made that branch conditional.
    """
    found: list[str] = list(outside)

    def walk_level(units: list[dict[str, Any]]) -> bool:
        for unit in units:
            if str(unit.get("id", "")) == unit_id:
                return True
            contained = unit.get("units") or []
            if contained:
                depth = len(found)
                if kind_of(unit) is Kind.LOOP:
                    if unit.get("indexName"):
                        found.append(str(unit["indexName"]))
                    # A loop over a variable's values binds that name to the value of this iteration,
                    # and only inside itself. Outside it there is no single value the name could mean.
                    if unit.get(COUNT_FROM_VARIABLE):
                        found.append(str(unit[COUNT_FROM_VARIABLE]))
                if walk_level(contained):
                    return True
                del found[depth:]
            if kind_of(unit) in BIND_A_NAME and unit.get("name"):
                if kind_of(unit) is Kind.VARIABLE and "values" in unit:
                    continue  # several-valued: it is what a loop counts over, not a value to read
                found.append(str(unit["name"]))
        return False

    walk_level(pipeline.get("units", []))
    return tuple(dict.fromkeys(found))


def _check_expression_here(
    pipeline: dict[str, Any], unit: dict[str, Any], *, outside: Iterable[str]
) -> None:
    """Refuse an expression naming something not bound at this point, when it is written (AC-032).

    At edit time rather than at run time. A study that fails at midnight on a name somebody could have
    seen was wrong is what this removes; the same expression a level higher may be perfectly valid, so
    the check has to know where the unit sits.
    """
    expression = unit.get("expression")
    if not expression:
        raise PipelineError(f"ユニット '{unit.get('id')}' に式がありません")
    try:
        check(str(expression), bound=names_bound_before(pipeline, str(unit.get("id", "")), outside=outside))
    except ExpressionError as error:
        raise PipelineError(f"ユニット '{unit.get('id')}' の式：{error}") from None


def add(
    pipeline: dict[str, Any],
    unit: dict[str, Any],
    *,
    inside: str | None = None,
    outside: Iterable[str] = (),
) -> dict[str, Any]:
    """Add a unit, or refuse the drop with the reason (AC-001).

    Validated before it goes in, so a pipeline is never briefly invalid - a state the editor would have
    to render and the user would have to interpret.
    """
    kind_of(unit)
    reference_of(unit)
    units = pipeline.setdefault("units", [])

    if inside is None:
        target = units
    else:
        container = _find(units, inside)
        if kind_of(container) not in CONTAINERS:
            raise PipelineError(
                f"'{inside}' は {kind_of(container).value} で、ほかのユニットを含みません。"
                f"含められるのは {sorted(k.value for k in CONTAINERS)} です"
            )
        target = container.setdefault("units", [])

    if _find_or_none(units, str(unit.get("id", ""))) is not None:
        raise PipelineError(f"ユニット '{unit.get('id')}' はすでにあります")

    target.append(unit)
    deepest = depth_of(units)
    if deepest > MAX_PIPELINE_DEPTH:
        target.pop()
        raise PipelineError(
            f"入れ子が {deepest} 段になり、上限 {MAX_PIPELINE_DEPTH} 段を超えます（LIM-007）。"
            "一目で読めないパイプラインは、誰も予測できず、データを消す許可を与えられないものです"
        )
    if kind_of(unit) in CARRY_EXPRESSION:
        # Checked with the unit in place, because "bound at this point" is a question about where it
        # sits. A refused edit then leaves the pipeline exactly as it was.
        try:
            _check_expression_here(pipeline, unit, outside=outside)
        except PipelineError:
            target.pop()
            raise
    return unit


def reorder(pipeline: dict[str, Any], order: Iterable[str]) -> None:
    """Put the top-level units in a stated order (AC-002).

    Every unit must appear exactly once. A reorder that silently dropped one would remove a step from a
    study while looking like a rearrangement.
    """
    units = pipeline.setdefault("units", [])
    wanted = [str(item) for item in order]
    present = [str(unit.get("id", "")) for unit in units]
    if sorted(wanted) != sorted(present):
        raise PipelineError(
            f"並べ替えの一覧が現在のユニットと一致しません（指定 {wanted}、現在 {present}）。"
            "並べ替えのつもりで工程が消えることを防ぐため、過不足があれば行いません"
        )
    by_id = {str(unit.get("id", "")): unit for unit in units}
    pipeline["units"] = [by_id[item] for item in wanted]


def unresolved(
    pipeline: dict[str, Any],
    *,
    available: Iterable[tuple[str, str, int]] = (),
) -> tuple[tuple[str, str], ...]:
    """Units whose pinned reference is not among what exists (AC-003).

    `available` is (source, id, revision) triples. Compared including the **revision**, because a
    reference that resolves to a different revision is a unit that would run something else.
    """
    have = {(str(s), str(i), int(r)) for s, i, r in available}
    missing: list[tuple[str, str]] = []
    for unit, _ in walk(pipeline.get("units", [])):
        reference = reference_of(unit)
        if reference is None:
            continue
        if (reference.source.value, reference.identifier, reference.revision) not in have:
            missing.append((str(unit.get("id", "")), reference.describe()))
    return tuple(missing)


def may_run(pipeline: dict[str, Any], *, available: Iterable[tuple[str, str, int]] = ()) -> str | None:
    """Why this pipeline cannot run, or None.

    A missing reference **keeps its unit** and refuses the run. Removing the unit would lose the user's
    work over somebody else's deletion; running without it would produce a study missing a step nobody
    noticed.
    """
    missing = unresolved(pipeline, available=available)
    if not missing:
        return None
    listed = "、".join(f"{unit_id}（{what}）" for unit_id, what in missing)
    return (
        f"解決できない参照が {len(missing)} 件あります：{listed}。"
        "ユニットは残してあります — 更新するか取り除くまで実行しません（AC-003）"
    )


def _find(units: list[dict[str, Any]], unit_id: str) -> dict[str, Any]:
    found = _find_or_none(units, unit_id)
    if found is None:
        raise PipelineError(f"ユニット '{unit_id}' はこのパイプラインにありません")
    return found


def _find_or_none(units: list[dict[str, Any]], unit_id: str) -> dict[str, Any] | None:
    for unit, _ in walk(units):
        if unit.get("id") == unit_id:
            return unit
    return None


@dataclass(slots=True)
class TargetSet:
    """The cases the units below act on, and how it got that way (REQ-002)."""

    cases: list[str] = dataclass_field(default_factory=list)
    #: One line per unit that changed or read the set, so "how many cases did this act on" is
    #: answerable afterwards rather than reconstructed.
    log: list[str] = dataclass_field(default_factory=list)

    def add(self, unit_id: str, case_ids: Iterable[str]) -> int:
        """Add cases and state how many the set now holds (AC-004)."""
        for case in case_ids:
            if case not in self.cases:
                self.cases.append(str(case))
        self.log.append(f"{unit_id}：ケースを追加し、対象は {len(self.cases)} 件になりました")
        return len(self.cases)

    def clear(self, unit_id: str) -> None:
        self.log.append(f"{unit_id}：対象を空にしました")
        self.cases.clear()

    def acted_on(self, unit_id: str) -> tuple[str, ...]:
        """Every case in the set at this point, including ones earlier units added (AC-005).

        An empty set is a **skip**, stated, and the run continues (AC-007) - a unit with nothing to do
        is not a failure, and stopping there would end a study because one branch happened to be empty.
        """
        if not self.cases:
            self.log.append(f"{unit_id}：対象が空のため実行しません（続行します）")
            return ()
        self.log.append(f"{unit_id}：対象 {len(self.cases)} 件に対して実行します")
        return tuple(self.cases)
