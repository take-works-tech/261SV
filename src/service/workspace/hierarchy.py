"""The @Case tree: creating beneath, moving within, and deleting with the count in front of the user.

A @Case nests to any depth (workspace/AC-001). Two operations need guarding and they need it for
different reasons.

**A cycle is refused with the hierarchy unchanged** (AC-003). Not repaired, not partially applied: a
move that would make a case its own ancestor leaves the tree exactly as it was, because a tree
half-moved is a state nobody designed and the user cannot see.

**A deletion states how many go with it** (AC-002). The service takes the number the caller showed the
user and refuses if it disagrees with what is actually there. A confirmation is only a confirmation if
what was confirmed is what happens - a dialogue saying "3 descendants" over a tree that now has 11 is
worse than no dialogue, and only the layer holding the tree can tell.

Specification: workspace/AC-001, AC-002, AC-003, CT-001.
"""

from __future__ import annotations

from typing import Any, Iterator

Case = dict[str, Any]


class HierarchyError(Exception):
    """Raised when an operation would leave the tree in a shape nobody asked for. Changes nothing."""


def children_of(case: Case) -> list[Case]:
    return case.setdefault("children", [])


def walk(cases: list[Case], ancestors: tuple[str, ...] = ()) -> Iterator[tuple[Case, tuple[str, ...]]]:
    """Every case depth-first, each with the ids of its ancestors, outermost first."""
    for case in cases:
        yield case, ancestors
        yield from walk(case.get("children", []), ancestors + (str(case.get("id", "")),))


def find(cases: list[Case], case_id: str) -> tuple[Case, tuple[str, ...]] | None:
    """One case and its ancestor ids, or None."""
    for case, ancestors in walk(cases):
        if case.get("id") == case_id:
            return case, ancestors
    return None


def require(cases: list[Case], case_id: str) -> tuple[Case, tuple[str, ...]]:
    found = find(cases, case_id)
    if found is None:
        raise HierarchyError(f"ケース '{case_id}' はこのワークスペースにありません")
    return found


def descendant_count(case: Case) -> int:
    """How many cases would go with this one. The number a confirmation has to name."""
    return sum(1 for _ in walk(children_of(case)))


def new_case(case_id: str, name: str) -> Case:
    """A case with the fields CT-001 requires, and nothing invented beyond them."""
    return {"id": case_id, "name": name, "children": [], "sources": []}


def add(cases: list[Case], case: Case, *, beneath: str | None = None) -> Case:
    """Put a case at the top level, or beneath another at any depth."""
    case_id = str(case.get("id", ""))
    if not case_id:
        raise HierarchyError("ケースには id が必要です")
    if find(cases, case_id) is not None:
        raise HierarchyError(f"ケース '{case_id}' はすでにあります")
    if beneath is None:
        cases.append(case)
        return case
    parent, _ = require(cases, beneath)
    children_of(parent).append(case)
    return case


def move(cases: list[Case], case_id: str, *, beneath: str | None) -> None:
    """Move a case, or refuse and leave the hierarchy exactly as it was."""
    case, _ = require(cases, case_id)

    if beneath is not None:
        if beneath == case_id:
            raise HierarchyError(
                f"ケース '{case_id}' を自分自身の下には移せません。階層は変更していません"
            )
        _, target_ancestors = require(cases, beneath)
        # The case cannot become its own ancestor, which is the same thing as: the target must not be
        # inside it. Checked **before** anything is detached, so a refusal leaves the tree untouched
        # rather than repaired.
        if case_id in target_ancestors:
            raise HierarchyError(
                f"ケース '{case_id}' を自分の子孫 '{beneath}' の下には移せません"
                "（自分自身の祖先になります）。階層は変更していません"
            )

    _detach(cases, case_id)
    if beneath is None:
        cases.append(case)
    else:
        parent, _ = require(cases, beneath)
        children_of(parent).append(case)


def delete(cases: list[Case], case_id: str, *, descendants_confirmed: int) -> int:
    """Delete a case and everything beneath it, having been told how many that is.

    `descendants_confirmed` is the number the caller put in front of the user. A mismatch means what
    was confirmed is not what would happen - a stale dialogue over a tree that changed - and it is
    refused rather than resolved in either direction.
    """
    case, _ = require(cases, case_id)
    actual = descendant_count(case)
    if descendants_confirmed != actual:
        raise HierarchyError(
            f"確認された子孫の数は {descendants_confirmed} 件ですが、実際は {actual} 件です。"
            "確認した内容と起きることが違うので、削除しません"
        )
    _detach(cases, case_id)
    return actual + 1


def _detach(cases: list[Case], case_id: str) -> None:
    """Remove a case from wherever it currently sits, leaving its own subtree intact."""
    for index, case in enumerate(cases):
        if case.get("id") == case_id:
            del cases[index]
            return
    for case in cases:
        _detach(children_of(case), case_id)
