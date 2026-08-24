"""A template travelling: to the shared library, into a file, and back out somewhere else.

A template exists to cross studies, so the interesting cases are the ones where it does not fit. XC-090
settles them - it applies as far as it resolves and names what it could not - and its own alternatives
say why: applying only on an exact match makes the rule trivial and defeats the purpose.

Verifies: workspace/AC-036 to AC-040, workspace/TASK-035 to TASK-039.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from service.workspace.items import create, save_as_template, templates_of
from service.workspace.templates import (
    Arity,
    TemplateError,
    check_arity,
    export,
    import_template,
    promote,
    requirements_of,
)

DEFINITION = {
    "fields": ["stress", "temperature"],
    "units": ["MPa"],
    "variables": ["allowable"],
    "parts": ["flange"],
}


def workspace() -> dict[str, Any]:
    document: dict[str, Any] = {
        "formatVersion": "4.0.0", "id": "w", "cases": [], "variables": [], "workspaceItems": {},
    }
    create(document, "views", "view:001", "断面", DEFINITION)
    save_as_template(document, "views", "view:001", "view-template:001", "断面 T")
    return document


class TestWhatATemplateNeedsIsWrittenDown:
    def test_every_kind_of_reference_is_collected(self) -> None:
        """AC-037: fields, units, variables, parts, dependent entries."""
        found = requirements_of(DEFINITION)

        assert {item.kind for item in found} == {"field", "unit", "variable", "part"}
        assert {item.name for item in found} >= {"stress", "MPa", "allowable", "flange"}

    def test_the_order_is_the_same_twice(self) -> None:
        assert requirements_of(DEFINITION) == requirements_of(DEFINITION)

    def test_a_definition_needing_nothing_yields_nothing(self) -> None:
        assert requirements_of({}) == ()


class TestPromotionReportsRatherThanRefuses:
    def test_it_records_the_requirements_on_the_template(self) -> None:
        """Whoever applies it next year reads the template, not the call that promoted it."""
        document = workspace()

        promote(document, "views", "view-template:001", scope="shared")

        stated = templates_of(document, "views")[0]["requirements"]
        assert {item["name"] for item in stated} >= {"stress", "allowable"}

    def test_something_resolvable_only_at_the_origin_is_reported_not_refused(self) -> None:
        """AC-037. Refusing turns a shareable template into an unshareable one over a detail the user
        may be happy to accept."""
        document = workspace()

        result = promote(
            document, "views", "view-template:001", scope="shared",
            resolvable_in_origin_only=["allowable"],
        )

        assert result.scope == "shared"
        assert [item.name for item in result.origin_only] == ["allowable"]
        assert "昇格は妨げませんが" in result.describe()

    def test_the_origin_workspace_still_stands_alone(self) -> None:
        """AC-036: promotion copies outward and does not make the origin depend on the library."""
        document = workspace()

        promote(document, "views", "view-template:001", scope="shared")

        assert templates_of(document, "views")[0]["definition"] == DEFINITION

    def test_promoting_into_the_sample_scope_is_refused(self) -> None:
        """`sample` ships with the product and is never edited in place (GL-019)."""
        with pytest.raises(TemplateError):
            promote(workspace(), "views", "view-template:001", scope="sample")

    def test_promoting_something_absent_is_refused(self) -> None:
        with pytest.raises(TemplateError):
            promote(workspace(), "views", "view-template:404", scope="shared")


class TestExportIsSelfContainedOrSaysWhyNot:
    def test_a_cleared_asset_is_embedded(self, tmp_path: Path) -> None:
        template = templates_of(workspace(), "views")[0]

        result = export(
            template, tmp_path / "t.svt",
            assets={"logo.png": b"\x89PNG"}, embeddable=["logo.png"],
        )

        assert result.embedded == ("logo.png",)
        assert "logo.png" in json.loads(result.path.read_text(encoding="utf-8"))["embeddedAssets"]

    def test_an_uncleared_asset_is_listed_by_name_and_not_included(self, tmp_path: Path) -> None:
        """AC-038, XC-025. A template that quietly embeds a font somebody redistributed is a licence
        problem the user finds out about from someone else."""
        template = templates_of(workspace(), "views")[0]

        result = export(
            template, tmp_path / "t.svt",
            assets={"logo.png": b"\x89PNG", "Meiryo.ttc": b"font"}, embeddable=["logo.png"],
        )

        assert result.listed_only == ("Meiryo.ttc",)
        body = json.loads(result.path.read_text(encoding="utf-8"))
        assert "Meiryo.ttc" not in body["embeddedAssets"]
        assert "Meiryo.ttc" in body["listedAssets"]

    def test_nothing_is_embedded_unless_it_was_cleared(self, tmp_path: Path) -> None:
        """Expressed as an allowance rather than a denial: an asset nobody has cleared is not
        embedded, whatever its size."""
        template = templates_of(workspace(), "views")[0]

        result = export(template, tmp_path / "t.svt", assets={"a.png": b"x", "b.png": b"y"})

        assert result.embedded == ()
        assert result.listed_only == ("a.png", "b.png")

    def test_the_line_names_what_could_not_travel(self, tmp_path: Path) -> None:
        template = templates_of(workspace(), "views")[0]

        line = export(
            template, tmp_path / "t.svt", assets={"Meiryo.ttc": b"font"}
        ).describe()

        assert "Meiryo.ttc" in line
        assert "XC-025" in line


class TestImportLandsSomewhereAndSaysWhatIsMissing:
    def exported(self, tmp_path: Path) -> Path:
        document = workspace()
        promote(document, "views", "view-template:001", scope="workspace")
        return export(templates_of(document, "views")[0], tmp_path / "t.svt").path

    def test_it_lands_in_the_chosen_scope_with_its_origin(self, tmp_path: Path) -> None:
        """AC-039. One that arrives anonymous is one nobody can go back to when its numbers are
        questioned."""
        target: dict[str, Any] = {"cases": [], "variables": [], "workspaceItems": {}}

        result = import_template(target, "views", self.exported(tmp_path), scope="workspace")

        assert result.scope == "workspace"
        assert result.origin == "view-template:001"
        assert templates_of(target, "views")[0]["origin"] == "view-template:001"

    def test_what_does_not_resolve_is_listed_rather_than_failing_the_import(
        self, tmp_path: Path
    ) -> None:
        target: dict[str, Any] = {"cases": [], "variables": [], "workspaceItems": {}}

        result = import_template(
            target, "views", self.exported(tmp_path), available=["stress", "MPa"]
        )

        assert {item.name for item in result.unresolved} == {"temperature", "allowable", "flange"}
        assert "未解決 3 件" in result.describe()

    def test_everything_available_leaves_nothing_unresolved(self, tmp_path: Path) -> None:
        target: dict[str, Any] = {"cases": [], "variables": [], "workspaceItems": {}}

        result = import_template(
            target, "views", self.exported(tmp_path),
            available=["stress", "temperature", "MPa", "allowable", "flange"],
        )

        assert result.unresolved == ()

    def test_a_file_that_is_not_a_template_export_is_refused_by_what_it_is(
        self, tmp_path: Path
    ) -> None:
        other = tmp_path / "other.json"
        other.write_text('{"kind": "something-else"}', encoding="utf-8")
        target: dict[str, Any] = {"cases": [], "variables": [], "workspaceItems": {}}

        with pytest.raises(TemplateError) as refusal:
            import_template(target, "views", other)
        assert "something-else" in str(refusal.value)


class TestAContradictedArityIsRefused:
    def test_a_single_case_template_applied_to_a_set(self) -> None:
        """AC-040. Not a near miss: a different operation with a different answer, and guessing which
        the user meant produces the answer nobody asked for."""
        with pytest.raises(TemplateError) as refusal:
            check_arity({"arity": Arity.ONE.value}, case_count=3)
        assert "推測はしません" in str(refusal.value)

    def test_a_multi_case_template_applied_to_one(self) -> None:
        with pytest.raises(TemplateError):
            check_arity({"arity": Arity.MANY.value}, case_count=1)

    def test_a_template_that_says_either_takes_both(self) -> None:
        check_arity({"arity": Arity.EITHER.value}, case_count=1)
        check_arity({"arity": Arity.EITHER.value}, case_count=5)

    def test_a_template_that_says_nothing_takes_both(self) -> None:
        check_arity({}, case_count=4)

    def test_an_arity_nobody_recognises_is_refused_rather_than_ignored(self) -> None:
        with pytest.raises(TemplateError):
            check_arity({"arity": "some"}, case_count=1)
