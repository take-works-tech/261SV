"""The @Case tree, and the per-variable inheritance that hangs off it.

INV-004 - one definition per variable - is met by **resolving on read and copying nothing**. A parent's
change reaches every inheriting descendant in the same operation because there is no second copy to
update, not because an update walks the tree. The version that walks the tree is the one that misses a
branch.

XC-117's correction is what the read-only rule is for. The earlier model let a child type a new value
and detach silently: the user changes one number to try something, and three months later the parent no
longer drives that child and nothing on screen said so.

No VTK, no engine environment.

Verifies: workspace/AC-001 to AC-008, AC-044, workspace/TASK-005 to TASK-010.
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import FIXED_INSTANT

from service.workspace.hierarchy import (
    HierarchyError,
    add,
    delete,
    descendant_count,
    find,
    move,
    new_case,
    walk,
)
from service.workspace.variables import (
    VariableError,
    VariableState,
    declare,
    detach,
    reattach,
    remove,
    resolve,
    set_value,
)

WHEN = FIXED_INSTANT


def workspace() -> dict[str, Any]:
    """root, with children a and b, and a1 beneath a."""
    document: dict[str, Any] = {
        "formatVersion": "4.0.0", "id": "w", "cases": [], "variables": [], "workspaceItems": {},
    }
    cases = document["cases"]
    add(cases, new_case("root", "親"))
    add(cases, new_case("a", "子A"), beneath="root")
    add(cases, new_case("b", "子B"), beneath="root")
    add(cases, new_case("a1", "孫"), beneath="a")
    return document


def ids(document: dict[str, Any]) -> list[str]:
    return [case["id"] for case, _ in walk(document["cases"])]


class TestTheTreeNestsToAnyDepth:
    def test_a_case_is_created_beneath_another(self) -> None:
        document = workspace()

        found = find(document["cases"], "a1")

        assert found is not None
        assert found[1] == ("root", "a")

    def test_a_new_case_carries_the_fields_the_contract_requires(self) -> None:
        """And nothing invented beyond them: a field this build makes up is one a later version has to
        keep forever."""
        assert set(new_case("x", "n")) == {"id", "name", "children", "sources"}

    def test_a_duplicate_identifier_is_refused(self) -> None:
        with pytest.raises(HierarchyError):
            add(workspace()["cases"], new_case("a", "また子A"), beneath="root")

    def test_a_case_can_be_moved_to_the_top_level(self) -> None:
        document = workspace()

        move(document["cases"], "a1", beneath=None)

        assert find(document["cases"], "a1")[1] == ()


class TestOperationsThatWouldBreakTheTree:
    def test_making_a_case_its_own_ancestor_is_refused(self) -> None:
        document = workspace()

        with pytest.raises(HierarchyError) as refusal:
            move(document["cases"], "root", beneath="a1")
        assert "自分自身の祖先" in str(refusal.value)

    def test_the_hierarchy_is_unchanged_after_that_refusal(self) -> None:
        """AC-003 says unchanged, not repaired. The check happens before anything is detached, so a
        tree half-moved is a state that cannot occur rather than one that gets cleaned up."""
        document = workspace()
        before = ids(document)

        with pytest.raises(HierarchyError):
            move(document["cases"], "root", beneath="a1")

        assert ids(document) == before

    def test_moving_a_case_beneath_itself_is_refused(self) -> None:
        with pytest.raises(HierarchyError):
            move(workspace()["cases"], "a", beneath="a")


class TestDeletionStatesWhatGoesWithIt:
    def test_the_descendant_count_is_what_a_confirmation_names(self) -> None:
        document = workspace()

        assert descendant_count(find(document["cases"], "root")[0]) == 3

    def test_a_confirmed_count_that_no_longer_matches_is_refused(self) -> None:
        """A dialogue saying "2 descendants" over a tree that now has 3 is worse than no dialogue, and
        only the layer holding the tree can tell."""
        document = workspace()

        with pytest.raises(HierarchyError) as refusal:
            delete(document["cases"], "root", descendants_confirmed=2)
        assert "確認した内容と起きることが違う" in str(refusal.value)
        assert ids(document) == ["root", "a", "a1", "b"]

    def test_a_matching_count_deletes_the_case_and_its_descendants(self) -> None:
        document = workspace()

        removed = delete(document["cases"], "a", descendants_confirmed=1)

        assert removed == 2
        assert ids(document) == ["root", "b"]


class TestOneDefinitionResolvedThroughTheTree:
    def test_a_workspace_variable_resolves_everywhere(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0, unit="mm")

        assert [resolve(document, case, "mesh").value for case in ("root", "a", "a1", "b")] == [5.0] * 4

    def test_a_parent_change_reaches_every_inheriting_descendant_at_once(self) -> None:
        """INV-004. Nothing is copied, so nothing has to be walked to be updated - and nothing can be
        missed."""
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)

        document["variables"][0]["value"] = 7.0

        assert [resolve(document, case, "mesh").value for case in ("root", "a", "a1", "b")] == [7.0] * 4

    def test_an_independent_descendant_is_left_alone(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)
        detach(document, "a", "mesh", when=WHEN)
        set_value(document, "a", "mesh", 3.0)

        document["variables"][0]["value"] = 7.0

        assert resolve(document, "a", "mesh").value == 3.0
        assert resolve(document, "b", "mesh").value == 7.0

    def test_a_descendant_follows_its_nearest_detached_ancestor(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)
        detach(document, "a", "mesh", when=WHEN)
        set_value(document, "a", "mesh", 3.0)

        grandchild = resolve(document, "a1", "mesh")

        assert grandchild.value == 3.0
        assert grandchild.held_by == "a"
        assert grandchild.state is VariableState.INHERITED

    def test_an_undeclared_variable_reports_unresolved_and_substitutes_nothing(self) -> None:
        """AC-008."""
        resolution = resolve(workspace(), "a", "nothing")

        assert resolution.is_resolved is False
        assert resolution.value is None


class TestDetachingIsDeliberate:
    def test_an_inherited_variable_cannot_be_edited_in_the_child(self) -> None:
        """XC-117's correction, as a refusal. The earlier model let a child type a value and detach
        without anyone deciding to."""
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)

        with pytest.raises(VariableError) as refusal:
            set_value(document, "a", "mesh", 3.0)
        assert "継承中" in str(refusal.value)
        assert "意図した操作" in str(refusal.value)

    def test_detaching_takes_the_current_value_as_its_starting_point(self) -> None:
        """AC-044."""
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)

        after = detach(document, "a", "mesh", when=WHEN)

        assert after.value == 5.0
        assert after.state is VariableState.INDEPENDENT
        assert after.is_editable_here

    def test_it_records_when_it_stopped_following(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)
        detach(document, "a", "mesh", when=WHEN)

        assert find(document["cases"], "a")[0]["variableStates"]["mesh"]["detachedIso"] == WHEN

    def test_detaching_twice_is_refused_rather_than_silently_repeated(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)
        detach(document, "a", "mesh", when=WHEN)

        with pytest.raises(VariableError):
            detach(document, "a", "mesh", when=WHEN)

    def test_reattaching_follows_the_parent_again(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)
        detach(document, "a", "mesh", when=WHEN)
        set_value(document, "a", "mesh", 3.0)

        after = reattach(document, "a", "mesh")

        assert after.value == 5.0
        assert after.state is VariableState.INHERITED


class TestAVariableAChildAddedIsNotTheParents:
    def test_it_does_not_appear_on_the_parent(self) -> None:
        """AC-006."""
        document = workspace()
        declare(document, "local", "子だけの値", 9.9, on_case="a")

        assert resolve(document, "root", "local").is_resolved is False
        assert resolve(document, "b", "local").is_resolved is False

    def test_it_does_appear_on_its_own_descendants(self) -> None:
        document = workspace()
        declare(document, "local", "子だけの値", 9.9, on_case="a")

        assert resolve(document, "a1", "local").value == 9.9

    def test_the_refusal_says_where_it_was_declared(self) -> None:
        document = workspace()
        declare(document, "local", "子だけの値", 9.9, on_case="a")

        assert "'a'" in (resolve(document, "b", "local").unresolved_because or "")

    def test_declaring_the_same_variable_twice_is_refused(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)

        with pytest.raises(VariableError) as refusal:
            declare(document, "mesh", "また", 1.0)
        assert "INV-004" in str(refusal.value)


class TestDeletingAVariableFromAChild:
    def test_an_inherited_one_is_refused_and_the_ancestor_named(self) -> None:
        """AC-007."""
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0, on_case="root")

        with pytest.raises(VariableError) as refusal:
            remove(document, "a", "mesh")
        assert "'root'" in str(refusal.value)

    def test_a_workspace_wide_one_names_the_workspace(self) -> None:
        document = workspace()
        declare(document, "mesh", "メッシュ寸法", 5.0)

        with pytest.raises(VariableError) as refusal:
            remove(document, "a", "mesh")
        assert "ワークスペース全体" in str(refusal.value)

    def test_a_child_only_one_is_deleted_where_it_was_declared(self) -> None:
        document = workspace()
        declare(document, "local", "子だけの値", 9.9, on_case="a")
        detach(document, "a1", "local", when=WHEN)

        remove(document, "a", "local")

        assert resolve(document, "a", "local").is_resolved is False
        assert "local" not in find(document["cases"], "a1")[0].get("variableStates", {})
