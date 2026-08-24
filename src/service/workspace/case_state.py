"""Where a @Case is in its lifecycle, and the only moves it may make.

XC-136 names six states and the transitions between them, and the reason it exists is the last clause:
**the @Pipeline decides what to skip from the state rather than from an ad-hoc check.** A pipeline that
re-derives "is this loadable" from files on disk answers a slightly different question from the one the
case tree is showing, and the two disagree at exactly the moment somebody is watching a long run.

So the transitions are a table, and a move that is not in it is refused with both states named. The
alternative - permitting anything and letting each caller be careful - produces a case that is `loading`
after a failure, which nothing displays sensibly and nothing recovers from.

**A missing or changed input moves a case to unresolved from any state, and keeps its definitions**
(AC-046). Keeping them is the point: the user's views, graphs and reports are not wrong because a file
moved, and discarding them would turn a restorable situation into lost work.

Specification: XC-136, GL-039, workspace/AC-045, AC-046, AC-047.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from service.workspace.hierarchy import require
from service.workspace.sources import CaseResolution


class CaseState(str, Enum):
    """The six (GL-039). Observed by the product - a tag is what a person decided."""

    UNRESOLVED = "unresolved"  # its files cannot be found or have changed
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    PARTIAL = "partial"        # loaded with gaps (XC-002)
    FAILED = "failed"


#: Every move XC-136 permits, as a table rather than as conditions spread through the callers. A move
#: absent from here is refused: permitting anything and asking each caller to be careful produces a case
#: that is `loading` after a failure, which nothing displays sensibly and nothing recovers from.
TRANSITIONS: dict[CaseState, frozenset[CaseState]] = {
    CaseState.UNRESOLVED: frozenset({CaseState.UNLOADED}),
    CaseState.UNLOADED: frozenset({CaseState.LOADING}),
    CaseState.LOADING: frozenset({CaseState.LOADED, CaseState.PARTIAL, CaseState.FAILED}),
    CaseState.LOADED: frozenset({CaseState.UNLOADED}),
    CaseState.PARTIAL: frozenset({CaseState.UNLOADED}),
    CaseState.FAILED: frozenset({CaseState.UNLOADED}),
}

#: The one move available from everywhere, because it is not a decision the product makes - it is
#: something that happened to the files while nobody was looking (AC-046).
FROM_ANYWHERE = CaseState.UNRESOLVED

#: What a pipeline may run against. Read from the state rather than re-derived, which is the whole point
#: of having states (AC-047).
RUNNABLE = frozenset({CaseState.LOADED, CaseState.PARTIAL})

_WORD = {
    CaseState.UNRESOLVED: "未解決",
    CaseState.UNLOADED: "未読み込み",
    CaseState.LOADING: "読み込み中",
    CaseState.LOADED: "読み込み済み",
    CaseState.PARTIAL: "一部欠落",
    CaseState.FAILED: "失敗",
}


class StateError(Exception):
    """Raised for a move XC-136 does not permit. Names both states and changes nothing."""


def state_of(case: dict[str, Any]) -> CaseState:
    """A case's state, defaulting to unloaded.

    Unloaded rather than unresolved for a case that says nothing: a new case with no files yet is not a
    case whose files are missing, and showing it as broken would be a product complaining about its own
    empty state.
    """
    stated = str(case.get("state", CaseState.UNLOADED.value))
    try:
        return CaseState(stated)
    except ValueError:
        raise StateError(
            f"ケースの状態 '{stated}' は {[s.value for s in CaseState]} のいずれでもありません"
        ) from None


def move(case: dict[str, Any], to: CaseState, *, because: str | None = None) -> CaseState:
    """Move a case along one permitted transition, or refuse naming both states."""
    current = state_of(case)
    if to is not FROM_ANYWHERE and to not in TRANSITIONS[current]:
        allowed = "、".join(_WORD[s] for s in sorted(TRANSITIONS[current], key=lambda s: s.value))
        raise StateError(
            f"ケース '{case.get('id')}' は{_WORD[current]}から{_WORD[to]}へは移れません。"
            f"移れるのは {allowed or '（どこへも）'} です（XC-136）"
        )
    case["state"] = to.value
    if because:
        case["stateReason"] = because
    else:
        case.pop("stateReason", None)
    return to


def mark_unresolved(case: dict[str, Any], resolution: CaseResolution) -> CaseState:
    """Move a case to unresolved because its inputs changed, keeping every definition (AC-046).

    Nothing is discarded. The user's views, graphs and reports are not wrong because a file moved, and
    throwing them away would turn a restorable situation into lost work.
    """
    return move(case, CaseState.UNRESOLVED, because=resolution.describe())


def may_run(case: dict[str, Any]) -> bool:
    """Whether a @Pipeline should run this case (AC-047).

    Read from the state. A pipeline re-deriving this from files on disk answers a slightly different
    question from the one the case tree is showing, and the two disagree at exactly the moment somebody
    is watching a long run.
    """
    return state_of(case) in RUNNABLE


@dataclass(frozen=True, slots=True)
class StateSummary:
    """What the case tree shows beside one case."""

    case_id: str
    state: CaseState
    reason: str | None = None

    def describe(self) -> str:
        line = f"{self.case_id}：{_WORD[self.state]}"
        return f"{line}（{self.reason}）" if self.reason else line


def summary_of(cases: list[dict[str, Any]], case_id: str) -> StateSummary:
    case, _ = require(cases, case_id)
    return StateSummary(case_id, state_of(case), case.get("stateReason"))
