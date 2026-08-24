"""Sending a workspace to somebody who has neither your disk nor your library (XC-140).

Each clause of the decision is there because the obvious version fails somewhere: the size is stated
before writing, because finding out from a full disk is finding out too late; what could not go in is
**named** rather than counted, because the recipient is the person who cannot ask; and a pack without
data opens with every case unresolved rather than with cases that look fine until somebody clicks one.

Verifies: workspace/AC-048, AC-049, AC-050, workspace/TASK-047 to TASK-049.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from service.workspace.case_state import CaseState, state_of
from service.workspace.hierarchy import add, find, new_case
from service.workspace.pack import Omission, opened_without_data, plan
from service.workspace.sources import record


def workspace(tmp_path: Path, *, sources: list[str] | None = None) -> dict[str, Any]:
    document: dict[str, Any] = {
        "formatVersion": "4.0.0", "id": "w", "cases": [], "variables": [], "workspaceItems": {},
    }
    case = new_case("case:001", "baseline")
    for name in sources or []:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("result data", encoding="utf-8")
        case["sources"].append(record(path, relative_to=tmp_path))
    add(document["cases"], case)
    return document


class TestTheSizeIsStatedBeforeAnythingIsWritten:
    def test_it_counts_the_document_and_what_would_go_with_it(self, tmp_path: Path) -> None:
        document = workspace(tmp_path, sources=["run.vtu"])

        result = plan(document, root=tmp_path, document_bytes=1000, with_data=True)

        assert result.total_bytes == 1000 + len("result data")
        assert result.included == (("run.vtu", len("result data")),)

    def test_the_line_is_readable_before_the_decision(self, tmp_path: Path) -> None:
        """The only time it is useful. A user asking for a workspace with its data is asking for
        something that may be forty gigabytes."""
        document = workspace(tmp_path, sources=["run.vtu"])

        line = plan(document, root=tmp_path, document_bytes=2_000_000, with_data=True).describe()

        assert "MB" in line

    def test_leaving_the_data_out_says_so(self, tmp_path: Path) -> None:
        document = workspace(tmp_path, sources=["run.vtu"])

        result = plan(document, root=tmp_path, document_bytes=1000, with_data=False)

        assert result.included == ()
        assert "入力データは含みません" in result.describe()


class TestEverythingLeftBehindIsNamed:
    def test_an_asset_whose_licence_forbids_it_is_named(self, tmp_path: Path) -> None:
        """AC-049. "3 items omitted" tells the recipient that something is missing and not which
        thing, and the recipient is the person who cannot ask."""
        font = tmp_path / "Meiryo.ttc"
        font.write_bytes(b"font")
        document = workspace(tmp_path)

        result = plan(
            document, root=tmp_path, document_bytes=100, with_data=False,
            assets={"Meiryo.ttc": font}, redistributable=[],
        )

        assert [item.name for item in result.omitted] == ["Meiryo.ttc"]
        assert result.omitted[0].why is Omission.NOT_REDISTRIBUTABLE
        assert "Meiryo.ttc" in result.describe()

    def test_a_cleared_asset_travels(self, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        logo.write_bytes(b"\x89PNG")
        document = workspace(tmp_path)

        result = plan(
            document, root=tmp_path, document_bytes=100, with_data=False,
            assets={"logo.png": logo}, redistributable=["logo.png"],
        )

        assert result.included == (("logo.png", 4),)
        assert result.omitted == ()

    def test_a_linked_folder_outside_the_workspace_is_named_and_not_followed(
        self, tmp_path: Path
    ) -> None:
        """Following it would put files from outside the project into a pack the user believes holds
        their project."""
        document = workspace(tmp_path)
        find(document["cases"], "case:001")[0]["sources"] = [
            {"pathRelative": "../elsewhere/run.vtu", "sizeBytes": 10, "modifiedIso": "x"}
        ]

        result = plan(document, root=tmp_path, document_bytes=100, with_data=True)

        assert result.omitted[0].why is Omission.OUTSIDE
        assert result.included == ()

    def test_a_reference_that_is_no_longer_on_disk_is_named(self, tmp_path: Path) -> None:
        document = workspace(tmp_path, sources=["run.vtu"])
        (tmp_path / "run.vtu").unlink()

        result = plan(document, root=tmp_path, document_bytes=100, with_data=True)

        assert result.omitted[0].why is Omission.NOT_FOUND

    def test_data_left_out_on_purpose_is_still_named(self, tmp_path: Path) -> None:
        """The recipient needs to know which files to ask for, and "not requested" is a different
        message from "could not be found"."""
        document = workspace(tmp_path, sources=["run.vtu"])

        result = plan(document, root=tmp_path, document_bytes=100, with_data=False)

        assert result.omitted[0].why is Omission.NOT_REQUESTED
        assert result.omitted[0].name == "run.vtu"


class TestOpeningAPackWithoutData:
    def test_every_case_with_inputs_opens_unresolved(self, tmp_path: Path) -> None:
        """AC-050. Not cases that look fine until somebody clicks one - XC-136 already has the state,
        which is the whole reason it is a state rather than a flag on a loader."""
        document = workspace(tmp_path, sources=["run.vtu"])

        moved = opened_without_data(document)

        assert moved == ("case:001",)
        assert state_of(find(document["cases"], "case:001")[0]) is CaseState.UNRESOLVED

    def test_it_says_how_to_resolve_them(self, tmp_path: Path) -> None:
        document = workspace(tmp_path, sources=["run.vtu"])

        opened_without_data(document)

        assert "入力ファイルを同じ場所に置くと" in find(document["cases"], "case:001")[0]["stateReason"]

    def test_a_case_with_no_inputs_is_left_alone(self, tmp_path: Path) -> None:
        """It has nothing missing, and marking it unresolved would be the product reporting a problem
        it invented."""
        document = workspace(tmp_path)

        assert opened_without_data(document) == ()
        assert state_of(find(document["cases"], "case:001")[0]) is CaseState.UNLOADED

    def test_the_definitions_survive_the_pack_round_trip(self, tmp_path: Path) -> None:
        document = workspace(tmp_path, sources=["run.vtu"])
        document["workspaceItems"] = {"views": [{"id": "view:001", "name": "断面"}]}

        opened_without_data(document)

        assert document["workspaceItems"]["views"][0]["id"] == "view:001"
