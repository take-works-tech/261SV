"""Where a @Case is in its lifecycle, and the only moves it may make (XC-136).

The reason the states exist is the last clause of the decision: **the pipeline decides what to skip
from the state rather than from an ad-hoc check.** A pipeline re-deriving "is this loadable" from files
on disk answers a slightly different question from the one the case tree is showing, and the two
disagree at exactly the moment somebody is watching a long run.

Verifies: workspace/AC-045, AC-046, AC-047, workspace/TASK-044 to TASK-046.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from service.workspace.case_state import (
    RUNNABLE,
    TRANSITIONS,
    CaseState,
    StateError,
    mark_unresolved,
    may_run,
    move,
    state_of,
    summary_of,
)
from service.workspace.hierarchy import add, new_case
from service.workspace.sources import record, resolve_case


def a_case(state: CaseState | None = None) -> dict[str, Any]:
    case = new_case("case:001", "baseline")
    if state is not None:
        case["state"] = state.value
    return case


class TestTheStateOfANewCase:
    def test_a_case_that_says_nothing_is_unloaded(self) -> None:
        """Unloaded rather than unresolved: a new case with no files yet is not a case whose files are
        missing, and showing it as broken would be the product complaining about its own empty state."""
        assert state_of(new_case("case:001", "baseline")) is CaseState.UNLOADED

    def test_a_state_this_build_does_not_know_is_refused(self) -> None:
        with pytest.raises(StateError):
            state_of({"id": "case:001", "state": "halfway"})


class TestOnlyTheTransitionsTheDecisionNames:
    def test_loading_reaches_the_three_outcomes(self) -> None:
        assert TRANSITIONS[CaseState.LOADING] == {
            CaseState.LOADED, CaseState.PARTIAL, CaseState.FAILED
        }

    def test_an_unloaded_case_starts_loading(self) -> None:
        case = a_case(CaseState.UNLOADED)

        assert move(case, CaseState.LOADING) is CaseState.LOADING

    def test_a_loaded_case_cannot_go_straight_back_to_loading(self) -> None:
        """A clear unit moves it to unloaded first (XC-099), and the table is what says so."""
        case = a_case(CaseState.LOADED)

        with pytest.raises(StateError) as refusal:
            move(case, CaseState.LOADING)
        assert "読み込み済み" in str(refusal.value)
        assert "読み込み中" in str(refusal.value)

    def test_a_refused_move_changes_nothing(self) -> None:
        case = a_case(CaseState.LOADED)

        with pytest.raises(StateError):
            move(case, CaseState.FAILED)

        assert state_of(case) is CaseState.LOADED

    def test_the_refusal_names_where_it_could_have_gone(self) -> None:
        """"Not permitted" alone leaves the caller to guess the table."""
        case = a_case(CaseState.FAILED)

        with pytest.raises(StateError) as refusal:
            move(case, CaseState.LOADED)
        assert "未読み込み" in str(refusal.value)

    def test_a_failure_is_reachable_only_from_loading(self) -> None:
        for state in (CaseState.UNLOADED, CaseState.LOADED, CaseState.PARTIAL):
            with pytest.raises(StateError):
                move(a_case(state), CaseState.FAILED)


class TestUnresolvedIsReachableFromAnywhere:
    def test_every_state_can_become_unresolved(self) -> None:
        """AC-046. Not a decision the product makes - something that happened to the files while
        nobody was looking."""
        for state in CaseState:
            case = a_case(state)
            assert move(case, CaseState.UNRESOLVED) is CaseState.UNRESOLVED

    def test_it_keeps_the_definitions(self, tmp_path: Path) -> None:
        """The user's views, graphs and reports are not wrong because a file moved, and discarding them
        would turn a restorable situation into lost work."""
        path = tmp_path / "run.vtu"
        path.write_text("result", encoding="utf-8")
        case = a_case(CaseState.LOADED)
        case["sources"] = [record(path, relative_to=tmp_path)]
        case["views"] = [{"id": "view:001"}]
        path.unlink()

        mark_unresolved(case, resolve_case(case, relative_to=tmp_path))

        assert state_of(case) is CaseState.UNRESOLVED
        assert case["views"] == [{"id": "view:001"}]

    def test_it_records_why(self, tmp_path: Path) -> None:
        path = tmp_path / "run.vtu"
        path.write_text("result", encoding="utf-8")
        case = a_case(CaseState.LOADED)
        case["sources"] = [record(path, relative_to=tmp_path)]
        path.unlink()

        mark_unresolved(case, resolve_case(case, relative_to=tmp_path))

        assert "不明 1 件" in case["stateReason"]

    def test_an_unresolved_case_returns_by_becoming_unloaded(self) -> None:
        case = a_case(CaseState.UNRESOLVED)

        assert move(case, CaseState.UNLOADED) is CaseState.UNLOADED

    def test_a_reason_is_cleared_when_the_state_moves_on(self) -> None:
        """A stale reason beside a current state is worse than none: it describes something that is no
        longer true."""
        case = a_case(CaseState.UNRESOLVED)
        case["stateReason"] = "ファイルがありません"

        move(case, CaseState.UNLOADED)

        assert "stateReason" not in case


class TestThePipelineReadsTheState:
    def test_only_loaded_and_partial_may_run(self) -> None:
        """AC-047, and the reason the states exist at all."""
        assert RUNNABLE == {CaseState.LOADED, CaseState.PARTIAL}

    def test_a_partial_case_still_runs(self) -> None:
        """Loaded with gaps is loaded. Skipping it would discard a result the user can act on because
        part of it is absent."""
        assert may_run(a_case(CaseState.PARTIAL)) is True

    def test_an_unresolved_or_failed_case_does_not(self) -> None:
        assert may_run(a_case(CaseState.UNRESOLVED)) is False
        assert may_run(a_case(CaseState.FAILED)) is False

    def test_a_loading_case_does_not(self) -> None:
        assert may_run(a_case(CaseState.LOADING)) is False


class TestTheTreeShowsIt:
    def test_a_summary_names_the_state_in_the_interface_language(self) -> None:
        cases: list[dict[str, Any]] = []
        add(cases, a_case(CaseState.PARTIAL))

        assert summary_of(cases, "case:001").describe() == "case:001：一部欠落"

    def test_a_reason_is_shown_beside_it(self) -> None:
        cases: list[dict[str, Any]] = []
        case = a_case(CaseState.UNRESOLVED)
        case["stateReason"] = "入力が見つかりません"
        add(cases, case)

        assert "入力が見つかりません" in summary_of(cases, "case:001").describe()
