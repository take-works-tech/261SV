"""A pipeline as it is edited, with every rule enforced before anybody presses run.

REQ-001: built by editing, not by recording. Which means the rules hold at **edit time** - a pipeline
that only reveals its problems on the night it runs is one nobody can plan a study around.

Verifies: pipeline/AC-001 to AC-007, AC-023, AC-042, pipeline/TASK-001 to TASK-010.
"""

from __future__ import annotations

from typing import Any

import pytest

from engine.limits import MAX_PIPELINE_DEPTH
from service.pipeline.document import (
    CONTAINERS,
    DefinitionRef,
    Kind,
    PipelineError,
    Source,
    TargetSet,
    add,
    add_cases_unit,
    artefact_unit,
    depth_of,
    may_run,
    reference_of,
    reorder,
    unresolved,
)

VIEW_REF = DefinitionRef(Source.WORKSPACE_ITEM, "view:001", 1)


def pipeline() -> dict[str, Any]:
    return {"id": "pipeline:001", "name": "毎回の確認", "units": []}


def container(unit_id: str, kind: Kind = Kind.LOOP) -> dict[str, Any]:
    return {"id": unit_id, "kind": kind.value, "units": []}


class TestAReferenceSaysWhatItIs:
    def test_it_states_workspace_item_or_template(self) -> None:
        """AC-042. The two have separate identity and lifecycle (XC-109), and guessing from the
        identifier would silently follow whichever one still existed."""
        unit = artefact_unit("unit:001", Kind.VIEW, VIEW_REF)

        found = reference_of(unit)

        assert found is not None
        assert found.source is Source.WORKSPACE_ITEM
        assert "ワークスペース項目" in found.describe()

    def test_a_reference_missing_its_revision_is_refused_rather_than_filled_in(self) -> None:
        """A revision this build supplied is a pin nobody chose, and it would follow whatever the
        newest one happened to be on the day it ran."""
        with pytest.raises(PipelineError) as refusal:
            reference_of({"id": "u", "kind": "view", "definitionRef": {"source": "workspaceItem", "id": "v"}})
        assert "誰も選んでいない固定" in str(refusal.value)

    def test_a_source_this_build_does_not_know_is_refused(self) -> None:
        with pytest.raises(PipelineError):
            reference_of({"id": "u", "definitionRef": {"source": "guess", "id": "v", "revision": 1}})

    def test_a_kind_with_no_definition_may_not_carry_one(self) -> None:
        with pytest.raises(PipelineError):
            artefact_unit("unit:001", Kind.TAG, VIEW_REF)


class TestOneUnitHoldsAWholeSelection:
    def test_six_cases_dropped_together_make_one_unit(self) -> None:
        """AC-023. Six units of one case each look the same on screen and behave differently the moment
        somebody reorders or removes one."""
        unit = add_cases_unit("unit:001", [f"case:{n:03d}" for n in range(6)])

        assert unit["kind"] == Kind.ADD_CASES.value
        assert len(unit["caseIds"]) == 6

    def test_a_case_unit_with_no_cases_is_refused(self) -> None:
        with pytest.raises(PipelineError):
            add_cases_unit("unit:001", [])


class TestEditingIsValidatedBeforeItLands:
    def test_a_unit_is_added_at_the_top_level(self) -> None:
        document = pipeline()

        add(document, add_cases_unit("unit:001", ["case:001"]))

        assert [u["id"] for u in document["units"]] == ["unit:001"]

    def test_a_duplicate_identifier_is_refused(self) -> None:
        document = pipeline()
        add(document, add_cases_unit("unit:001", ["case:001"]))

        with pytest.raises(PipelineError):
            add(document, add_cases_unit("unit:001", ["case:002"]))

    def test_a_unit_can_be_added_inside_a_container(self) -> None:
        document = pipeline()
        add(document, container("loop:001"))

        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF), inside="loop:001")

        assert document["units"][0]["units"][0]["id"] == "unit:001"

    def test_a_non_container_refuses_contents_and_names_what_may(self) -> None:
        document = pipeline()
        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF))

        with pytest.raises(PipelineError) as refusal:
            add(document, add_cases_unit("unit:002", ["case:001"]), inside="unit:001")
        assert "loop" in str(refusal.value)


class TestNestingIsBounded:
    def test_the_limit_comes_from_the_one_place_that_holds_it(self) -> None:
        assert MAX_PIPELINE_DEPTH == 3

    def test_every_containing_kind_costs_one_level(self) -> None:
        """TASK-006: asserted for all three, because a depth rule that counted only loops would let a
        condition inside a simulation inside a loop through."""
        assert CONTAINERS == {Kind.LOOP, Kind.CONDITION, Kind.SIMULATION}

        for kind in CONTAINERS:
            document = pipeline()
            add(document, container("a", kind))
            add(document, container("b", kind), inside="a")
            assert depth_of(document["units"]) == 2

    def test_exceeding_the_depth_is_refused_and_names_the_limit(self) -> None:
        document = pipeline()
        add(document, container("a"))
        add(document, container("b"), inside="a")
        add(document, container("c"), inside="b")

        with pytest.raises(PipelineError) as refusal:
            add(document, container("d"), inside="c")
        assert "3 段" in str(refusal.value)

    def test_a_refused_edit_leaves_the_pipeline_as_it_was(self) -> None:
        document = pipeline()
        add(document, container("a"))
        add(document, container("b"), inside="a")
        add(document, container("c"), inside="b")

        with pytest.raises(PipelineError):
            add(document, container("d"), inside="c")

        assert depth_of(document["units"]) == 3


class TestReorderingCannotLoseAStep:
    def test_it_puts_the_units_in_the_stated_order(self) -> None:
        document = pipeline()
        add(document, add_cases_unit("unit:001", ["case:001"]))
        add(document, artefact_unit("unit:002", Kind.VIEW, VIEW_REF))

        reorder(document, ["unit:002", "unit:001"])

        assert [u["id"] for u in document["units"]] == ["unit:002", "unit:001"]

    def test_an_order_missing_a_unit_is_refused(self) -> None:
        """A reorder that silently dropped one would remove a step from a study while looking like a
        rearrangement."""
        document = pipeline()
        add(document, add_cases_unit("unit:001", ["case:001"]))
        add(document, artefact_unit("unit:002", Kind.VIEW, VIEW_REF))

        with pytest.raises(PipelineError) as refusal:
            reorder(document, ["unit:002"])
        assert "工程が消える" in str(refusal.value)


class TestAMissingReferenceKeepsItsUnit:
    def test_it_is_reported_with_what_is_missing(self) -> None:
        """AC-003."""
        document = pipeline()
        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF))

        missing = unresolved(document, available=[])

        assert missing[0][0] == "unit:001"
        assert "view:001" in missing[0][1]

    def test_the_unit_stays(self) -> None:
        """Removing it would lose the user's work over somebody else's deletion."""
        document = pipeline()
        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF))

        unresolved(document, available=[])

        assert len(document["units"]) == 1

    def test_the_run_is_refused_until_it_is_updated_or_removed(self) -> None:
        document = pipeline()
        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF))

        assert "実行しません" in (may_run(document, available=[]) or "")

    def test_a_different_revision_does_not_satisfy_it(self) -> None:
        """A reference that resolved to a different revision is a unit that would run something else."""
        document = pipeline()
        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF))

        assert unresolved(document, available=[("workspaceItem", "view:001", 2)]) != ()

    def test_everything_present_permits_the_run(self) -> None:
        document = pipeline()
        add(document, artefact_unit("unit:001", Kind.VIEW, VIEW_REF))

        assert may_run(document, available=[("workspaceItem", "view:001", 1)]) is None


class TestTheTargetSetAccumulates:
    def test_a_case_unit_states_how_many_the_set_now_holds(self) -> None:
        """AC-004."""
        targets = TargetSet()

        assert targets.add("unit:001", ["case:001", "case:002"]) == 2
        assert "2 件" in targets.log[0]

    def test_a_unit_acts_on_cases_added_by_every_earlier_case_unit(self) -> None:
        """AC-005."""
        targets = TargetSet()
        targets.add("unit:001", ["case:001"])
        targets.add("unit:002", ["case:002"])

        assert targets.acted_on("unit:003") == ("case:001", "case:002")

    def test_the_same_case_twice_is_held_once(self) -> None:
        targets = TargetSet()
        targets.add("unit:001", ["case:001"])

        assert targets.add("unit:002", ["case:001"]) == 1

    def test_an_empty_set_skips_and_the_run_continues(self) -> None:
        """AC-007. A unit with nothing to do is not a failure, and stopping there would end a study
        because one branch happened to be empty."""
        targets = TargetSet()

        assert targets.acted_on("unit:001") == ()
        assert "続行します" in targets.log[0]

    def test_clearing_says_so(self) -> None:
        targets = TargetSet()
        targets.add("unit:001", ["case:001"])
        targets.clear("unit:002")

        assert targets.cases == []
        assert "空にしました" in targets.log[-1]

    def test_the_log_answers_how_many_each_unit_acted_on(self) -> None:
        """Afterwards, rather than reconstructed from the pipeline and the case list."""
        targets = TargetSet()
        targets.add("unit:001", ["case:001", "case:002"])
        targets.acted_on("unit:002")

        assert any("対象 2 件" in line for line in targets.log)
