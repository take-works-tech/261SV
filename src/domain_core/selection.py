"""Which cases a graph draws, a report covers, or a template is applied to.

CT-007's declarative form: a tree of conditions over things the product already knows - tags, names,
variables with their units, and case state. **It has no arithmetic and no function calls**, because a
selection that can compute is an evaluator, and the reason this form is declarative is that it must not
be one (XC-080).

Three rules, each ruling out a plausible alternative.

**An unknown condition is refused, never ignored.** A selection carrying a condition this build does not
understand would silently select the wrong cases, which is worse than refusing (CT-007). Ignoring an
unrecognised key is how a filter quietly becomes "everything".

**A comparison against an undeclared unit is refused** (XC-003). `inlet_velocity > 10` with no unit on
either side is a comparison whose answer depends on what the file happened to be written in, and the
answer prints as a case list nobody can see the units of.

**An empty result names the condition that emptied it** (graph/AC-009). An empty graph with no
explanation reads as "no data" when it means "your filter excluded everything", and those are different
problems with different fixes.

State and tags are kept apart (GL-039): a state is what the product observed, a tag is what a person
decided, so "every case that failed" is answerable without anyone having tagged them.

Specification: CT-007, GL-039, XC-003, XC-080, graph/AC-009, AC-011.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dataclass_field
from typing import Any, Iterable, Mapping, Sequence

from domain_core.dimension import parse_symbol
from domain_core.units import UndeclaredUnitError

#: The keys a condition may carry. Closed, and checked, because an unrecognised key is how a filter
#: quietly becomes "everything".
CONDITIONS = frozenset({"all", "any", "not", "tag", "name", "variable", "caseIds", "state", "code"})

#: The six states of GL-039. A state this build does not know is refused rather than never matching -
#: never matching looks like a selection that found nothing.
STATES = frozenset({"unresolved", "unloaded", "loading", "loaded", "partial", "failed"})

#: What a name condition may test. No expression, no capture - `matches` is a pattern.
NAME_TESTS = frozenset({"equals", "startsWith", "contains", "matches"})

#: What a variable condition may test, beyond naming the variable and its unit.
VARIABLE_TESTS = frozenset({"equals", "greaterThan", "lessThan", "inSet", "exists"})


class SelectionError(Exception):
    """Raised for a selection that cannot be read, or that would compare things that do not compare."""


@dataclass(frozen=True, slots=True)
class VariableValue:
    """A variable as a selection sees it: a value and the unit somebody declared, or none."""

    value: Any
    unit: str | None = None

    @property
    def declared(self) -> bool:
        return self.unit is not None


@dataclass(frozen=True, slots=True)
class CaseFacts:
    """What a selection may look at: **metadata only**, never data (CT-007).

    No dataset, no field values, no paths to open. The line CT-007 draws is not about convenience: the
    choice of what to show may be arbitrary, and the values shown may not be.
    """

    identifier: str
    name: str = ""
    tags: frozenset[str] = frozenset()
    state: str = "unloaded"
    variables: Mapping[str, VariableValue] = dataclass_field(default_factory=dict)
    time_steps: int = 0


@dataclass(frozen=True, slots=True)
class Resolution:
    """Which cases a selection chose, and - when none - which condition emptied the set."""

    selected: tuple[str, ...]
    emptied_by: str | None = None
    considered: int = 0
    #: Set where the set came from somewhere other than a written selection - the fallback of AC-008.
    #: Carried rather than left implicit: a graph that plotted the selected case without saying so looks
    #: identical to one that was told to plot it.
    stated: str | None = None

    def describe(self) -> str:
        if self.selected:
            line = f"{self.considered} 件中 {len(self.selected)} 件を選びました"
            return f"{line}（{self.stated}）" if self.stated else line
        if self.emptied_by:
            return (
                f"{self.considered} 件を調べて 1 件も選ばれませんでした。"
                f"空にした条件：{self.emptied_by}"
            )
        return "選択の対象になるケースがありません"


def describe_condition(node: Mapping[str, Any]) -> str:
    """One condition, in words, for naming it in a refusal or in an empty result."""
    if "all" in node:
        return "すべて（" + "、".join(describe_condition(one) for one in node["all"]) + "）"
    if "any" in node:
        return "いずれか（" + "、".join(describe_condition(one) for one in node["any"]) + "）"
    if "not" in node:
        return f"〜でない（{describe_condition(node['not'])}）"
    if "tag" in node:
        return f"タグ '{node['tag']}'"
    if "caseIds" in node:
        return f"ケース識別子 {len(node['caseIds'])} 件の指定"
    if "state" in node:
        return "状態 " + "・".join(str(one) for one in node["state"])
    if "name" in node:
        test = node["name"]
        which = next((key for key in NAME_TESTS if key in test), "?")
        return f"名前が {which} '{test.get(which)}'"
    if "variable" in node:
        test = node["variable"]
        which = next((key for key in VARIABLE_TESTS if key in test), "存在")
        unit = f" {test['unit']}" if test.get("unit") else ""
        return f"変数 '{test.get('name')}' が {which} {test.get(which, '')}{unit}".rstrip()
    if "code" in node:
        return "利用者が書いた選択コード"
    return "（読めない条件）"


def resolve(selection: Mapping[str, Any] | None, cases: Iterable[CaseFacts]) -> Resolution:
    """Which of these cases the selection chooses.

    A selection of `None` chooses **nothing** and says so, rather than everything. "No selection" and
    "select all" are different intentions, and the expensive direction is the one where a study
    silently covers every case in the workspace.
    """
    listed = list(cases)
    if selection is None:
        return Resolution((), "選択が指定されていません", len(listed))

    _check(selection)
    if "all" in selection:
        # Narrowed one condition at a time, so the one that emptied the set can be named rather than
        # inferred from a whole tree that came back with nothing.
        remaining = listed
        for condition in selection["all"]:
            narrowed = [case for case in remaining if _matches(condition, case)]
            if not narrowed:
                return Resolution((), describe_condition(condition), len(listed))
            remaining = narrowed
        return Resolution(tuple(case.identifier for case in remaining), None, len(listed))

    chosen = [case for case in listed if _matches(selection, case)]
    if not chosen:
        return Resolution((), describe_condition(selection), len(listed))
    return Resolution(tuple(case.identifier for case in chosen), None, len(listed))


def check_selection(node: Mapping[str, Any]) -> None:
    """Refuse a selection this build cannot honour, before it is stored (CT-007).

    Public because a selection is written long before it is resolved - a pipeline unit carries one that
    runs at midnight - and the refusal is worth having at the moment somebody writes it.
    """
    _check(node)


def _check(node: Mapping[str, Any]) -> None:
    """Refuse anything this build does not understand, before any case is examined."""
    if not isinstance(node, Mapping):
        raise SelectionError(f"条件はオブジェクトです（{type(node).__name__} が来ました）")
    unknown = sorted(set(node) - CONDITIONS)
    if unknown:
        raise SelectionError(
            f"選択に理解できない条件 {unknown} があります。無視はしません — "
            "読めない条件を飛ばすと、絞り込みが黙って「すべて」になります（CT-007）"
        )
    if len(node) != 1:
        raise SelectionError(
            f"一つの条件が {sorted(node)} を同時に持っています。"
            "どれを適用するかはこちらでは決められません — all か any で組んでください"
        )
    if "code" in node:
        raise SelectionError(
            "コード形式の選択はこのビルドでは実行できません（CT-007、XC-089）。"
            "別プロセス・メタデータのみ・時間と記憶容量の制限という条件を満たすまでは、"
            "空の結果を返すのではなく拒否します — 空のグラフは「データなし」に読めます"
        )
    for key in ("all", "any"):
        if key in node:
            if not node[key]:
                raise SelectionError(f"'{key}' が空です。何も書いていない条件は選択になりません")
            for one in node[key]:
                _check(one)
    if "not" in node:
        _check(node["not"])
    if "state" in node:
        unknown_states = sorted(set(node["state"]) - STATES)
        if unknown_states:
            raise SelectionError(
                f"状態 {unknown_states} はこの製品のものではありません（{sorted(STATES)}）。"
                "一致しないまま通すと、選択が何も見つけなかったように見えます"
            )
    if "name" in node:
        extra = sorted(set(node["name"]) - NAME_TESTS)
        if extra:
            raise SelectionError(f"名前の条件に {extra} は使えません（{sorted(NAME_TESTS)}）")
    if "variable" in node:
        test = node["variable"]
        if "name" not in test:
            raise SelectionError("変数の条件には name が要ります")
        extra = sorted(set(test) - VARIABLE_TESTS - {"name", "unit"})
        if extra:
            raise SelectionError(f"変数の条件に {extra} は使えません")
        if test.get("unit") is not None:
            try:
                parse_symbol(str(test["unit"]))
            except (KeyError, ValueError, UndeclaredUnitError) as error:
                raise SelectionError(f"変数の条件の単位：{error}") from None


def _matches(node: Mapping[str, Any], case: CaseFacts) -> bool:
    if "all" in node:
        return all(_matches(one, case) for one in node["all"])
    if "any" in node:
        return any(_matches(one, case) for one in node["any"])
    if "not" in node:
        return not _matches(node["not"], case)
    if "tag" in node:
        return node["tag"] in case.tags
    if "caseIds" in node:
        return case.identifier in node["caseIds"]
    if "state" in node:
        return case.state in node["state"]
    if "name" in node:
        return _name_matches(node["name"], case.name)
    if "variable" in node:
        return _variable_matches(node["variable"], case)
    raise SelectionError(f"読めない条件です：{sorted(node)}")


def _name_matches(test: Mapping[str, Any], name: str) -> bool:
    if "equals" in test and name != test["equals"]:
        return False
    if "startsWith" in test and not name.startswith(str(test["startsWith"])):
        return False
    if "contains" in test and str(test["contains"]) not in name:
        return False
    if "matches" in test:
        # A pattern, not an expression: `re.search` with no groups read back and nothing evaluated.
        if re.search(str(test["matches"]), name) is None:
            return False
    return True


def _variable_matches(test: Mapping[str, Any], case: CaseFacts) -> bool:
    name = str(test["name"])
    held = case.variables.get(name)
    if "exists" in test:
        return bool(test["exists"]) == (held is not None)
    if held is None:
        return False

    comparing = any(key in test for key in ("greaterThan", "lessThan"))
    if comparing:
        wanted_unit = test.get("unit")
        if wanted_unit is None or not held.declared:
            raise SelectionError(
                f"変数 '{name}' を数値で比べるには、両側に単位が要ります"
                f"（条件の単位 {wanted_unit!r}、変数の単位 {held.unit!r}）。"
                "単位のない比較は、ファイルが何で書かれていたかで答えが変わります（XC-003）"
            )
        here = parse_symbol(str(held.unit))
        there = parse_symbol(str(wanted_unit))
        if here.dimension != there.dimension:
            raise SelectionError(
                f"変数 '{name}' の単位 {held.unit} と条件の単位 {wanted_unit} は"
                "組み合わせられません"
            )
        value = float(held.value) * here.to_internal
        if "greaterThan" in test and not value > float(test["greaterThan"]) * there.to_internal:
            return False
        if "lessThan" in test and not value < float(test["lessThan"]) * there.to_internal:
            return False

    if "equals" in test and held.value != test["equals"]:
        return False
    if "inSet" in test and held.value not in test["inSet"]:
        return False
    return True


def selected_cases(
    selection: Mapping[str, Any] | None,
    cases: Iterable[CaseFacts],
    *,
    fallback: Sequence[str] = (),
) -> Resolution:
    """Resolve a selection, or fall back to what the user already had selected (graph/AC-008).

    The fallback is **stated** in the result rather than applied silently: a graph that plotted the
    selected case without saying so looks identical to one that was told to plot it.
    """
    listed = list(cases)
    if selection is None and fallback:
        return Resolution(
            tuple(fallback), None, len(listed),
            stated=f"選択が書かれていないため、選択中のケース {len(fallback)} 件を使いました",
        )
    return resolve(selection, listed)
