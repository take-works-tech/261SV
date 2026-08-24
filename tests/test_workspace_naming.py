"""Identifiers that never change and names that never collide, so a rename breaks nothing.

XC-103 in one line: references are stored by identifier, names are for people. A stored reference
containing a name breaks when somebody fixes a typo, and it breaks **quietly** - the view still opens,
the expression still parses, and the number it shows is from something else or from nothing.

Verifies: workspace/AC-022 to AC-025, workspace/TASK-021 to TASK-024.
"""

from __future__ import annotations

from typing import Any

import pytest

from service.workspace.hierarchy import add, new_case
from service.workspace.naming import (
    NamingError,
    Registry,
    references_in,
    registry_of,
)
from service.workspace.variables import declare


def registry() -> Registry:
    found = Registry()
    found.issue("case", "case:001", "baseline")
    found.issue("case", "case:002", "refined")
    return found


class TestAnIdentifierSaysWhatItRefersTo:
    def test_it_carries_its_kind(self) -> None:
        """A reference read out of a file says what it refers to even when the object is gone:
        "case:7f3a" is a case somebody deleted, and "7f3a" is nothing anybody can act on."""
        with pytest.raises(NamingError) as refusal:
            Registry().issue("case", "7f3a", "baseline")
        assert "種別・コロン" in str(refusal.value)

    def test_the_kind_in_it_has_to_be_the_kind_it_is(self) -> None:
        with pytest.raises(NamingError):
            Registry().issue("case", "view:001", "baseline")


class TestAnIdentifierIsNeverReused:
    def test_a_live_one_cannot_be_issued_again(self) -> None:
        with pytest.raises(NamingError):
            registry().issue("case", "case:001", "something else")

    def test_a_retired_one_cannot_be_issued_again_either(self) -> None:
        """Not after a delete, not after an undo. A reference held outside this workspace resolves to
        the object it meant or to nothing, and never to whatever took its place."""
        found = registry()
        found.retire("case", "case:001")

        with pytest.raises(NamingError) as refusal:
            found.issue("case", "case:001", "reincarnated")
        assert "再利用しません" in str(refusal.value)

    def test_a_retired_name_is_free_again(self) -> None:
        """The identifier is the thing that must not repeat. A name is what people call something, and
        a deleted case's name is available."""
        found = registry()
        found.retire("case", "case:001")

        found.issue("case", "case:003", "baseline")

        assert found.name_of("case", "case:003") == "baseline"


class TestACollidingNameIsRefusedRatherThanDecorated:
    def test_the_holder_is_named(self) -> None:
        """AC-023. "baseline (2)" beside "baseline" is a pair nobody can tell apart in a report,
        created by a product that decided not to bother the user."""
        with pytest.raises(NamingError) as refusal:
            registry().issue("case", "case:003", "baseline")
        assert "case:001" in str(refusal.value)
        assert "接尾辞" in str(refusal.value)

    def test_a_rename_onto_a_taken_name_is_refused(self) -> None:
        with pytest.raises(NamingError):
            registry().rename("case", "case:002", "baseline")

    def test_renaming_something_to_its_own_name_is_allowed(self) -> None:
        """Otherwise a form that saves every field refuses every save."""
        found = registry()

        found.rename("case", "case:001", "baseline")

        assert found.name_of("case", "case:001") == "baseline"

    def test_two_kinds_may_share_a_name(self) -> None:
        found = registry()

        found.issue("view", "view:001", "baseline")

        assert found.holder_of("view", "baseline") == "view:001"


class TestALookupAnswersWithOneOrFails:
    def test_a_unique_name_resolves(self) -> None:
        assert registry().resolve("case", "baseline") == "case:001"

    def test_a_miss_says_what_was_searched(self) -> None:
        """AC-024: fail with what it found. "Not found" alone leaves the user guessing whether they
        misspelled it or are looking in the wrong place."""
        with pytest.raises(NamingError) as refusal:
            registry().resolve("case", "missing")
        assert "baseline" in str(refusal.value)

    def test_it_never_returns_a_list_for_the_caller_to_choose_from(self) -> None:
        """Returning one moves the choice to a caller with less information than this layer has, and
        every caller that takes the first element is a bug nobody will find."""
        found = registry()
        found.live["case"]["case:003"] = "baseline"  # as an outside edit would leave it

        with pytest.raises(NamingError) as refusal:
            found.resolve("case", "baseline")
        assert "外部で編集されています" in str(refusal.value)


class TestARenameLeavesReferencesWorking:
    def test_nothing_stored_holds_a_name(self) -> None:
        """AC-025, as a property of the document rather than of one code path."""
        document: dict[str, Any] = {
            "formatVersion": "4.0.0", "id": "w", "cases": [], "variables": [], "workspaceItems": {},
        }
        add(document["cases"], new_case("case:001", "baseline"))
        declare(document, "variable:001", "許容応力", 235.0, on_case="case:001")

        found = registry_of(document)
        found.rename("case", "case:001", "renamed")

        assert "case:001" in set(references_in(document))
        assert found.resolve("case", "renamed") == "case:001"

    def test_references_are_found_wherever_they_sit(self) -> None:
        nested = {"a": [{"b": {"c": "view:009"}}], "d": "not an identifier"}

        assert set(references_in(nested)) == {"view:009"}


class TestReadingADocumentThatWasWrittenElsewhere:
    def test_existing_objects_are_adopted_without_the_checks_a_new_one_gets(self) -> None:
        """Refusing to load them would lose the user's work over a rule about how they were made. The
        collision check applies to what happens next."""
        document: dict[str, Any] = {
            "cases": [
                {"id": "odd one", "name": "same", "children": [], "sources": []},
                {"id": "another", "name": "same", "children": [], "sources": []},
            ],
            "variables": [],
            "workspaceItems": {},
        }

        found = registry_of(document)

        assert found.name_of("case", "odd one") == "same"

    def test_a_new_object_is_still_checked_against_what_was_loaded(self) -> None:
        document: dict[str, Any] = {
            "cases": [{"id": "case:001", "name": "baseline", "children": [], "sources": []}],
            "variables": [], "workspaceItems": {},
        }

        with pytest.raises(NamingError):
            registry_of(document).issue("case", "case:002", "baseline")

    def test_workspace_items_are_registered_by_their_singular_kind(self) -> None:
        document: dict[str, Any] = {
            "cases": [], "variables": [],
            "workspaceItems": {"views": [{"id": "view:001", "name": "断面"}]},
        }

        assert registry_of(document).resolve("view", "断面") == "view:001"
