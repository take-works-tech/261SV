"""Filtering the case tree by tag, and never hiding what the user is looking at.

AC-014: a filter states how many it hid, because a tree that quietly shrinks looks like a tree that lost
cases. AC-015: the selected case stays visible and marked as outside the filter, because hiding what
somebody has open is how a filter loses their place.

Verifies: workspace/AC-014, AC-015, workspace/TASK-014.
"""

from __future__ import annotations

from typing import Any

from service.workspace.hierarchy import add, new_case
from service.workspace.tags import all_tags, filter_by_tags, tags_of


def tagged(case_id: str, name: str, *tags: str) -> dict[str, Any]:
    case = new_case(case_id, name)
    if tags:
        case["tags"] = list(tags)
    return case


def tree() -> list[dict[str, Any]]:
    """root(-) > a(steel, draft), a1(steel), b(alu)"""
    cases: list[dict[str, Any]] = []
    add(cases, tagged("root", "親"))
    add(cases, tagged("a", "子A", "steel", "draft"), beneath="root")
    add(cases, tagged("a1", "孫", "steel"), beneath="a")
    add(cases, tagged("b", "子B", "alu"), beneath="root")
    return cases


class TestWhatIsOffered:
    def test_the_tags_a_filter_offers_are_the_tags_that_are_there(self) -> None:
        assert all_tags(tree()) == ("alu", "draft", "steel")

    def test_a_case_with_no_tags_has_none_rather_than_a_default(self) -> None:
        assert tags_of(new_case("x", "n")) == frozenset()


class TestAFilterSaysWhatItHid:
    def test_it_shows_matches_and_counts_the_rest(self) -> None:
        result = filter_by_tags(tree(), {"alu"})

        assert "b" in result.shown
        assert result.matched == {"b"}
        assert result.hidden_count == 2  # a and a1; root is kept as b's ancestor

    def test_an_ancestor_of_a_match_is_kept_but_is_not_a_match(self) -> None:
        """A tree with its middle removed is not a tree - but the ancestor is not what was asked for,
        and it says so."""
        result = filter_by_tags(tree(), {"steel"})

        assert set(result.shown) == {"root", "a", "a1"}
        assert result.matched == {"a", "a1"}
        assert result.shown_outside_filter == {"root"}

    def test_any_of_the_wanted_tags_matches_by_default(self) -> None:
        assert filter_by_tags(tree(), {"steel", "alu"}).matched == {"a", "a1", "b"}

    def test_every_wanted_tag_is_required_when_asked_for(self) -> None:
        """Two answers on the same tree, and neither is the obvious one, so the caller chooses."""
        assert filter_by_tags(tree(), {"steel", "draft"}, match_all=True).matched == {"a"}

    def test_no_filter_shows_everything(self) -> None:
        result = filter_by_tags(tree(), set())

        assert len(result.shown) == 4
        assert result.hidden_count == 0

    def test_the_line_states_both_numbers(self) -> None:
        line = filter_by_tags(tree(), {"alu"}).describe()

        assert "1 件が一致" in line
        assert "2 件を隠して" in line


class TestTheSelectionIsNeverHidden:
    def test_a_selected_case_outside_the_filter_stays_visible(self) -> None:
        """AC-015: they came back to a case, filtered to find its siblings, and the thing they were
        reading vanished."""
        result = filter_by_tags(tree(), {"alu"}, selected="a1")

        assert "a1" in result.shown
        assert "a1" in result.shown_outside_filter
        assert "a1" not in result.matched

    def test_its_ancestors_come_with_it(self) -> None:
        result = filter_by_tags(tree(), {"alu"}, selected="a1")

        assert set(result.shown) == {"root", "a", "a1", "b"}

    def test_keeping_it_reduces_what_is_counted_as_hidden(self) -> None:
        without = filter_by_tags(tree(), {"alu"})
        with_selection = filter_by_tags(tree(), {"alu"}, selected="a1")

        assert with_selection.hidden_count < without.hidden_count

    def test_a_selection_that_matches_is_simply_a_match(self) -> None:
        result = filter_by_tags(tree(), {"alu"}, selected="b")

        assert result.matched == {"b"}
        assert "b" not in result.shown_outside_filter

    def test_a_selection_that_is_not_in_the_tree_changes_nothing(self) -> None:
        assert filter_by_tags(tree(), {"alu"}, selected="gone").shown == filter_by_tags(
            tree(), {"alu"}
        ).shown
