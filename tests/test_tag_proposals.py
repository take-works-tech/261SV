"""Tags proposed from what can be read, applied only when a person says so (XC-120).

The clause that makes the feature bearable is the last one: **a rejected proposal is not offered again
in the session.** A suggestion that returns every time you decline it is a suggestion you learn to click
past, and a user who clicks past suggestions accepts a wrong one eventually.

Verifies: workspace/AC-041, AC-042, AC-043, workspace/TASK-040 to TASK-042.
"""

from __future__ import annotations

from typing import Any

from service.workspace.hierarchy import new_case
from service.workspace.tag_proposals import (
    MESH_BANDS,
    Session,
    Signal,
    accept,
    propose,
)


def tags_of(case: dict[str, Any]) -> list[str]:
    return list(case.get("tags", []))


class TestWhatCanBeReadIsProposed:
    def test_the_solver_becomes_a_tag(self) -> None:
        found = propose(solver="OpenFOAM")

        assert [p.tag for p in found] == ["openfoam"]
        assert found[0].signal is Signal.SOLVER

    def test_the_mesh_is_proposed_as_a_band_rather_than_a_count(self) -> None:
        """"1,043,221 points" is not a tag anybody filters by, and it stops matching the moment the
        mesh is refined. "large-mesh" survives that and is what a person would have written."""
        assert [p.tag for p in propose(point_count=1_043_221)] == ["large-mesh"]
        assert [p.tag for p in propose(point_count=250_000)] == ["medium-mesh"]
        assert [p.tag for p in propose(point_count=900)] == ["small-mesh"]

    def test_the_bands_are_a_table_rather_than_a_chain_of_conditions(self) -> None:
        assert [band for _, band in MESH_BANDS] == ["large-mesh", "medium-mesh", "small-mesh"]

    def test_what_differs_from_siblings_is_proposed(self) -> None:
        found = propose(differing_variables=["inlet velocity", "mesh size"])

        assert [p.tag for p in found] == ["inlet-velocity", "mesh-size"]

    def test_every_proposal_says_where_it_came_from(self) -> None:
        """"steel" with no reason is a tag a user must trust or check by hand."""
        line = propose(solver="OpenFOAM")[0].describe()

        assert "openfoam" in line
        assert "ソルバ名から" in line

    def test_the_order_is_the_same_twice(self) -> None:
        arguments = {"solver": "OpenFOAM", "differing_variables": ["b", "a"]}

        assert propose(**arguments) == propose(**arguments)


class TestAnInferredTagSaysSo:
    def test_it_is_marked_as_inferred(self) -> None:
        """AC-042. A name is what somebody typed and a solver record is what the run contained, and the
        two do not deserve equal confidence."""
        found = propose(inferred_from_name=["baseline"])

        assert found[0].is_inferred
        assert "推測" in found[0].describe()

    def test_a_read_tag_is_not_marked_inferred(self) -> None:
        assert propose(solver="OpenFOAM")[0].is_inferred is False

    def test_inferred_proposals_come_after_the_read_ones(self) -> None:
        found = propose(solver="OpenFOAM", inferred_from_name=["draft"])

        assert [p.is_inferred for p in found] == [False, True]

    def test_a_tag_from_two_signals_is_offered_under_the_deterministic_one(self) -> None:
        found = propose(solver="steel", inferred_from_name=["steel"])

        assert len(found) == 1
        assert found[0].signal is Signal.SOLVER


class TestNothingIsAppliedUntilAccepted:
    def test_proposing_changes_no_case(self) -> None:
        case = new_case("case:001", "baseline")

        propose(solver="OpenFOAM")

        assert tags_of(case) == []

    def test_accepting_applies_the_whole_set_in_one_action(self) -> None:
        """A user reviewing eleven proposals and clicking eleven times is a user who stops reviewing at
        the fourth."""
        case = new_case("case:001", "baseline")

        added = accept(case, propose(solver="OpenFOAM", point_count=5000))

        assert added == ("openfoam", "small-mesh")
        assert tags_of(case) == ["openfoam", "small-mesh"]

    def test_a_tag_the_case_already_has_is_not_proposed(self) -> None:
        assert propose(solver="OpenFOAM", already_tagged=["openfoam"]) == ()

    def test_accepting_twice_adds_nothing_the_second_time(self) -> None:
        case = new_case("case:001", "baseline")
        accept(case, propose(solver="OpenFOAM"))

        assert accept(case, propose(solver="OpenFOAM")) == ()
        assert tags_of(case) == ["openfoam"]


class TestARejectedProposalStaysRejected:
    def test_it_is_not_offered_again_in_the_session(self) -> None:
        """AC-043."""
        session = Session()
        first = propose(solver="OpenFOAM", session=session)
        session.reject(first[0])

        assert propose(solver="OpenFOAM", session=session) == ()

    def test_rejecting_one_leaves_the_others(self) -> None:
        session = Session()
        found = propose(solver="OpenFOAM", point_count=5000, session=session)
        session.reject(found[0])

        assert [p.tag for p in propose(solver="OpenFOAM", point_count=5000, session=session)] == [
            "small-mesh"
        ]

    def test_the_same_tag_from_a_different_signal_is_still_offered(self) -> None:
        """A rejection is about a proposal, not about a word. Declining "steel" read from the solver
        does not decline somebody later inferring it from the name - that is a different claim with a
        different confidence."""
        session = Session()
        session.reject(propose(solver="steel", session=session)[0])

        assert [p.tag for p in propose(inferred_from_name=["steel"], session=session)] == ["steel"]

    def test_a_fresh_session_offers_it_again(self) -> None:
        """A rejection is "not now", not "never". Persisting it would mean a tag declined once in March
        is unavailable in June, with nothing on screen saying why."""
        session = Session()
        session.reject(propose(solver="OpenFOAM", session=session)[0])

        assert propose(solver="OpenFOAM", session=Session()) != ()


class TestATagKeepsTheFormSomebodyCanSearchFor:
    def test_ascii_is_lowercased_and_hyphenated(self) -> None:
        assert propose(solver="Open FOAM")[0].tag == "open-foam"

    def test_japanese_is_left_alone(self) -> None:
        """Japanese has no case and no word separator; rewriting it would turn a tag somebody typed
        into one they cannot search for."""
        assert propose(differing_variables=["入口流速"])[0].tag == "入口流速"
