"""Working artefacts and reusable templates, kept apart (XC-109).

The decision's own correction is what these tests are for: an earlier model said the definition itself
was the template, and collapsing the working artefact into its reusable source made ordinary switching,
editing and pipeline references ambiguous to users.

Verifies: workspace/AC-030, AC-031, AC-032, AC-061, workspace/TASK-029 to TASK-031.
"""

from __future__ import annotations

from typing import Any

import pytest

from service.workspace.hierarchy import add, new_case
from service.workspace.items import (
    COLLECTIONS,
    ItemError,
    SourceTemplate,
    apply_template,
    preview_application,
    cases_owning_items,
    create,
    edit,
    find,
    save_as_template,
)


def workspace() -> dict[str, Any]:
    document: dict[str, Any] = {
        "formatVersion": "4.0.0", "id": "w", "cases": [], "variables": [], "workspaceItems": {},
    }
    add(document["cases"], new_case("case:001", "baseline"))
    return document


def apply(document: dict[str, Any], item_id: str, name: str) -> dict[str, Any]:
    """Preview then accept, which is the only way an item may be created from a template."""
    shown = preview_application(document, "views", "view-template:001")
    return apply_template(document, "views", item_id, name, accepted=shown)


def with_template(document: dict[str, Any]) -> dict[str, Any]:
    document.setdefault("templates", {})["views"] = [
        {"id": "view-template:001", "name": "断面テンプレート", "revision": 3,
         "scope": "workspace", "definition": {"camera": "front", "colourMap": "viridis"}}
    ]
    return document


class TestAnItemBelongsToTheWorkspace:
    def test_it_is_created_on_the_workspace_and_not_on_a_case(self) -> None:
        """AC-030. A case is an argument to an item, not its owner."""
        document = workspace()

        create(document, "views", "view:001", "断面", {"camera": "front"})

        assert document["workspaceItems"]["views"][0]["id"] == "view:001"
        assert cases_owning_items(document) == ()

    def test_a_case_holding_a_definition_is_found(self) -> None:
        """The model this replaced put artefacts on cases, and a document written by that model - or by
        hand - would put them back."""
        document = workspace()
        document["cases"][0]["views"] = [{"id": "view:009"}]

        assert cases_owning_items(document) == ("case:001",)

    def test_the_collections_carry_the_labels_the_decision_fixed(self) -> None:
        """XC-109 reserves `テンプレート` for the reusable library; a list of working artefacts calling
        itself that is the collapse the decision undid."""
        assert COLLECTIONS["views"] == "ビュー一覧"
        assert "テンプレート" not in "".join(COLLECTIONS.values())

    def test_an_unknown_collection_is_refused(self) -> None:
        with pytest.raises(ItemError):
            create(workspace(), "diagrams", "diagram:001", "x", {})

    def test_two_items_may_not_share_a_name(self) -> None:
        document = workspace()
        create(document, "views", "view:001", "断面", {})

        with pytest.raises(ItemError):
            create(document, "views", "view:002", "断面", {})


class TestEditingChangesOneItem:
    def test_it_changes_the_item_and_not_its_source_template(self) -> None:
        """AC-031."""
        document = with_template(workspace())
        apply(document, "view:001", "断面")

        edit(document, "views", "view:001", {"camera": "top"})

        assert find(document, "views", "view:001")["definition"] == {"camera": "top"}
        assert document["templates"]["views"][0]["definition"]["camera"] == "front"

    def test_it_changes_no_sibling_item(self) -> None:
        document = with_template(workspace())
        apply(document, "view:001", "断面 A")
        apply(document, "view:002", "断面 B")

        edit(document, "views", "view:001", {"camera": "top"})

        assert find(document, "views", "view:002")["definition"]["camera"] == "front"

    def test_an_item_is_the_same_item_whatever_case_is_selected(self) -> None:
        """Switching case re-renders the same item. A per-case copy is how a user ends up editing the
        wrong one of nine views called "断面" and finding out in a report."""
        document = workspace()
        add(document["cases"], new_case("case:002", "refined"))
        create(document, "views", "view:001", "断面", {"camera": "front"})

        assert len(document["workspaceItems"]["views"]) == 1
        assert cases_owning_items(document) == ()


class TestApplyingATemplateCopiesRatherThanLinks:
    def test_the_new_item_is_independent(self) -> None:
        """A shared structure would make a later template edit reach into a report somebody already
        sent."""
        document = with_template(workspace())
        apply(document, "view:001", "断面")

        document["templates"]["views"][0]["definition"]["colourMap"] = "changed"

        assert find(document, "views", "view:001")["definition"]["colourMap"] == "viridis"

    def test_it_records_where_it_came_from_with_the_revision(self) -> None:
        """AC-061. Provenance, not a subscription: "this came from 断面テンプレート v3" stays
        answerable, and nothing can mistake it for a link to v4."""
        document = with_template(workspace())

        item = apply(document, "view:001", "断面")

        assert item["sourceTemplate"] == {"id": "view-template:001", "revision": 3}

    def test_previewing_a_template_that_is_not_there_is_refused(self) -> None:
        with pytest.raises(ItemError):
            preview_application(workspace(), "views", "view-template:404")

    def test_an_item_cannot_be_created_without_a_resolution_having_been_shown(self) -> None:
        """AC-061: the result is shown and the item is created **only after acceptance**. Taking the
        preview rather than a template id is what makes that structural - the same shape as `prune`,
        which takes the plan it showed."""
        import inspect

        parameters = inspect.signature(apply_template).parameters

        assert "accepted" in parameters
        assert "template_id" not in parameters


class TestSavingAsATemplateLeavesTheItemAlone:
    def test_it_copies_the_current_definition_into_a_new_revision(self) -> None:
        """AC-032."""
        document = workspace()
        create(document, "views", "view:001", "断面", {"camera": "front"})

        template = save_as_template(document, "views", "view:001", "view-template:001", "断面 T")

        assert template["revision"] == 1
        assert template["definition"] == {"camera": "front"}

    def test_the_item_stays_independently_editable(self) -> None:
        document = workspace()
        create(document, "views", "view:001", "断面", {"camera": "front"})
        save_as_template(document, "views", "view:001", "view-template:001", "断面 T")

        edit(document, "views", "view:001", {"camera": "top"})

        assert document["templates"]["views"][0]["definition"]["camera"] == "front"

    def test_saving_again_makes_the_next_revision(self) -> None:
        document = workspace()
        create(document, "views", "view:001", "断面", {"camera": "front"})
        save_as_template(document, "views", "view:001", "view-template:001", "断面 T")
        edit(document, "views", "view:001", {"camera": "top"})

        second = save_as_template(document, "views", "view:001", "view-template:001", "断面 T")

        assert second["revision"] == 2
        assert second["definition"]["camera"] == "top"

    def test_a_shared_template_is_not_written_into_the_workspace(self) -> None:
        """Writing it here would mean handing somebody a workspace file also hands them entries in
        their shared library (CT-001)."""
        document = workspace()
        create(document, "views", "view:001", "断面", {"camera": "front"})

        with pytest.raises(ItemError) as refusal:
            save_as_template(
                document, "views", "view:001", "view-template:001", "断面 T", scope="shared"
            )
        assert "ワークスペース文書の外" in str(refusal.value)

    def test_the_source_template_of_an_applied_item_is_a_record_not_a_link(self) -> None:
        assert SourceTemplate("view-template:001", 3).revision == 3


class TestTheResolutionIsShownBeforeAnythingIsCreated:
    def test_a_preview_creates_nothing(self) -> None:
        document = with_template(workspace())

        preview_application(document, "views", "view-template:001")

        assert document["workspaceItems"].get("views", []) == []

    def test_it_reports_what_would_not_resolve(self) -> None:
        """XC-090: what resolves is copied, what does not is listed **before anything is drawn**."""
        document = with_template(workspace())
        document["templates"]["views"][0]["requirements"] = [
            {"kind": "field", "name": "stress"}, {"kind": "field", "name": "temperature"}
        ]

        shown = preview_application(document, "views", "view-template:001", available=["stress"])

        assert shown.resolved == ("stress",)
        assert shown.unresolved == ("temperature",)
        assert "temperature" in shown.describe()

    def test_everything_available_resolves_completely(self) -> None:
        document = with_template(workspace())

        assert preview_application(document, "views", "view-template:001").resolves_completely

    def test_the_accepted_preview_is_what_becomes_the_item(self) -> None:
        document = with_template(workspace())

        shown = preview_application(document, "views", "view-template:001")
        item = apply_template(document, "views", "view:001", "断面", accepted=shown)

        assert item["definition"] == shown.definition
        assert item["sourceTemplate"]["revision"] == shown.revision
