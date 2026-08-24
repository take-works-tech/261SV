"""A @Variable has one definition, and a child either follows it or has said it will not.

INV-004: exactly one definition in a @Workspace. That is achieved here by **resolving on read and
copying nothing**. A parent's change reaches every inheriting descendant in the same operation
(workspace/AC-004) because there is no second copy to update - not because an update walks the tree.
The version that walks the tree is the one that misses a branch.

XC-117 decides the rest, and its correction is worth reading before changing anything here. An earlier
model was "inherited unless overridden", where a child could type a new value and detach silently: the
user changes one number to try something, and three months later the parent no longer drives that child
and nothing on screen said so. **Detaching is a deliberate act with a name.** So an inherited variable
is read-only in the child, and `detach` is the only way out - it takes the current value as its starting
point and records when it stopped following.

A variable declared on a child is not visible on its parent (AC-006). `declaredOn` is the only field
that says so, and it is one field rather than a copy on each case, for the same reason as above.

Specification: INV-004, XC-117, workspace/AC-004 to AC-008, AC-044, CT-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from service.workspace.hierarchy import require, walk

Case = dict[str, Any]


class VariableState(str, Enum):
    """What a child does with a variable an ancestor defines (XC-117)."""

    INHERITED = "inherited"      # shows the parent's value, cannot be edited here, follows every change
    INDEPENDENT = "independent"  # holds its own value; the parent's changes do not reach it


class VariableError(Exception):
    """Raised when an operation would break the one-definition rule or detach something silently."""


@dataclass(frozen=True, slots=True)
class Resolution:
    """What a variable is worth on one case, and where that came from."""

    variable_id: str
    value: Any = None
    unit: str | None = None
    state: VariableState = VariableState.INHERITED
    #: The case whose `variableStates` supplied the value, or None where the declaration did.
    held_by: str | None = None
    #: The case the variable is declared on, or None for a workspace-wide one.
    declared_on: str | None = None
    #: Why it could not be resolved, where it could not. AC-008: reported, never substituted.
    unresolved_because: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.unresolved_because is None

    @property
    def is_editable_here(self) -> bool:
        """An inherited variable is read-only in the child (XC-117)."""
        return self.state is VariableState.INDEPENDENT


def _declaration(document: dict[str, Any], variable_id: str) -> dict[str, Any] | None:
    for variable in document.get("variables", []):
        if variable.get("id") == variable_id:
            return variable
    return None


def _states(case: Case) -> dict[str, Any]:
    return case.setdefault("variableStates", {})


def in_scope(document: dict[str, Any], case_id: str, variable_id: str) -> bool:
    """Whether the variable applies to this case at all.

    A workspace-wide variable applies everywhere; one declared on a case applies to it and to its
    descendants, and **not to its parent** (AC-006).
    """
    declaration = _declaration(document, variable_id)
    if declaration is None:
        return False
    declared_on = declaration.get("declaredOn")
    if not declared_on:
        return True
    case, ancestors = require(document.get("cases", []), case_id)
    return case_id == declared_on or declared_on in ancestors


def resolve(document: dict[str, Any], case_id: str, variable_id: str) -> Resolution:
    """What a variable is worth on one case, walking outwards and copying nothing."""
    declaration = _declaration(document, variable_id)
    if declaration is None:
        return Resolution(
            variable_id,
            unresolved_because=f"変数 '{variable_id}' はこのワークスペースに宣言されていません",
        )

    cases = document.get("cases", [])
    case, ancestors = require(cases, case_id)
    declared_on = declaration.get("declaredOn") or None
    if declared_on and case_id != declared_on and declared_on not in ancestors:
        return Resolution(
            variable_id,
            declared_on=declared_on,
            unresolved_because=(
                f"変数 '{variable_id}' はケース '{declared_on}' で宣言されており、"
                f"ケース '{case_id}' からは見えません"
            ),
        )

    unit = declaration.get("unit")
    # Outwards from this case: the nearest ancestor that has detached decides, and if none has, the
    # declaration does. Nothing is copied along the way, which is what makes a parent's change reach
    # every inheriting descendant without anything walking down to find them.
    for holder_id in (case_id, *reversed(ancestors)):
        holder, _ = require(cases, holder_id)
        entry = _states(holder).get(variable_id)
        if entry and entry.get("state") == VariableState.INDEPENDENT.value:
            return Resolution(
                variable_id,
                value=entry.get("value"),
                unit=unit,
                state=(
                    VariableState.INDEPENDENT if holder_id == case_id else VariableState.INHERITED
                ),
                held_by=holder_id,
                declared_on=declared_on,
            )

    if "value" not in declaration:
        return Resolution(
            variable_id, unit=unit, declared_on=declared_on,
            unresolved_because=f"変数 '{variable_id}' に値がありません",
        )
    return Resolution(
        variable_id, value=declaration.get("value"), unit=unit,
        state=VariableState.INHERITED, held_by=None, declared_on=declared_on,
    )


def declare(
    document: dict[str, Any],
    variable_id: str,
    name: str,
    value: Any,
    *,
    unit: str | None = None,
    on_case: str | None = None,
) -> dict[str, Any]:
    """Declare a variable once, workspace-wide or on one case and its descendants."""
    if _declaration(document, variable_id) is not None:
        raise VariableError(
            f"変数 '{variable_id}' はすでに宣言されています。ワークスペース内の定義はひとつです（INV-004）"
        )
    if on_case is not None:
        require(document.get("cases", []), on_case)
    declaration: dict[str, Any] = {"id": variable_id, "name": name, "value": value}
    if unit:
        declaration["unit"] = unit
    if on_case:
        declaration["declaredOn"] = on_case
    document.setdefault("variables", []).append(declaration)
    return declaration


def set_value(document: dict[str, Any], case_id: str, variable_id: str, value: Any) -> None:
    """Set a variable's value on a case, or refuse because it is following its parent.

    The refusal is the point of XC-117: a child that could simply be typed into would detach without
    anyone deciding to.
    """
    resolution = resolve(document, case_id, variable_id)
    if not resolution.is_resolved:
        raise VariableError(resolution.unresolved_because or "解決できません")
    declaration = _declaration(document, variable_id)
    assert declaration is not None
    if declaration.get("declaredOn") == case_id and resolution.held_by is None:
        declaration["value"] = value
        return
    if resolution.state is VariableState.INHERITED:
        source = resolution.held_by or "ワークスペース"
        raise VariableError(
            f"変数 '{variable_id}' はケース '{case_id}' で継承中のため、ここでは編集できません"
            f"（値は {source} が持っています）。"
            "独立させてから変更してください — 切り離しは意図した操作であり、"
            "値を書き換えた副作用ではありません（XC-117）"
        )
    _states(require(document.get("cases", []), case_id)[0])[variable_id]["value"] = value


def detach(
    document: dict[str, Any], case_id: str, variable_id: str, *, when: str
) -> Resolution:
    """Stop following the parent, starting from the value it currently shows (AC-044).

    `when` is supplied by the caller rather than read from a clock here, so that the same call twice
    produces the same document and a test does not depend on the time it ran.
    """
    resolution = resolve(document, case_id, variable_id)
    if not resolution.is_resolved:
        raise VariableError(resolution.unresolved_because or "解決できません")
    if resolution.state is VariableState.INDEPENDENT:
        raise VariableError(
            f"変数 '{variable_id}' はケース '{case_id}' ですでに独立しています"
        )
    case, _ = require(document.get("cases", []), case_id)
    _states(case)[variable_id] = {
        "state": VariableState.INDEPENDENT.value,
        "value": resolution.value,
        "detachedIso": when,
    }
    return resolve(document, case_id, variable_id)


def reattach(document: dict[str, Any], case_id: str, variable_id: str) -> Resolution:
    """Follow the parent again, discarding the independent value - which is a loss, so it is returned."""
    case, _ = require(document.get("cases", []), case_id)
    states = _states(case)
    if variable_id not in states:
        raise VariableError(
            f"変数 '{variable_id}' はケース '{case_id}' で独立していません"
        )
    del states[variable_id]
    return resolve(document, case_id, variable_id)


def remove(document: dict[str, Any], case_id: str, variable_id: str) -> None:
    """Delete a variable from a case, or refuse and name the ancestor that defines it (AC-007)."""
    declaration = _declaration(document, variable_id)
    if declaration is None:
        raise VariableError(f"変数 '{variable_id}' はありません")
    declared_on = declaration.get("declaredOn")
    if declared_on != case_id:
        where = f"ケース '{declared_on}'" if declared_on else "ワークスペース全体"
        raise VariableError(
            f"変数 '{variable_id}' は {where} で定義されているため、ケース '{case_id}' からは"
            "削除できません。子は変数を追加できますが、祖先が定義したものは削除できません（XC-117）"
        )
    document["variables"] = [
        variable for variable in document.get("variables", []) if variable.get("id") != variable_id
    ]
    for case, _ in walk(document.get("cases", [])):
        _states(case).pop(variable_id, None)
