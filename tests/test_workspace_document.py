"""Reading a workspace without losing anything, writing it without risking it.

CT-001's strictness is that unknown fields are **preserved** - not rejected, not dropped. The contract
sets out why: a user with two machines on two versions is the normal case for a desktop product, and
dropping means they lose work with no error.

XC-055: the previous good version is kept beside the new one on save, and the only copy is never
overwritten. A restore is then a file operation the user can perform without the product.

No VTK, no engine environment: this is JSON and renames.

Verifies: workspace/AC-011, AC-013, workspace/TASK-001, TASK-002, TASK-003, TASK-004.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from service.workspace.document import (
    FORMAT_VERSION,
    PREVIOUS_SUFFIX,
    WorkspaceDocument,
    WorkspaceFileError,
    WorkspaceVersionError,
    load,
    save,
)

MINIMAL = {
    "formatVersion": FORMAT_VERSION,
    "id": "ws-1",
    "name": "梁の検討",
    "cases": [{"id": "case-1", "name": "baseline"}],
    "variables": [],
    "workspaceItems": {"simulations": [], "views": [], "graphs": [], "reports": []},
}


def write(path: Path, document: dict) -> Path:
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


class TestARoundTripKeepsWhatItRead:
    def test_a_document_reopens_with_its_definitions(self, tmp_path: Path) -> None:
        source = write(tmp_path / "w.svw", MINIMAL)

        document = load(source)

        assert document.identifier == "ws-1"
        assert document.cases[0]["name"] == "baseline"
        assert document.format_version == FORMAT_VERSION

    def test_saving_and_reloading_changes_nothing(self, tmp_path: Path) -> None:
        source = write(tmp_path / "w.svw", MINIMAL)

        document = load(source)
        save(document, source)

        assert load(source).raw == MINIMAL

    def test_the_schema_version_this_build_writes_matches_the_contract(self) -> None:
        """CT-001 declares its version in prose and in the schema; the code is the third place, and
        three places that must agree need a test rather than an intention."""
        schema = json.loads(
            (Path(__file__).resolve().parents[1] / "specs" / "contracts" / "schema" / "CT-001.json")
            .read_text(encoding="utf-8")
        )

        assert schema["version"] == FORMAT_VERSION


class TestUnknownFieldsSurvive:
    """The property the contract chose over rejecting and over dropping."""

    def test_a_top_level_field_this_build_never_heard_of_comes_back(self, tmp_path: Path) -> None:
        future = dict(MINIMAL, annotationLayers=[{"id": "a1", "kind": "something-new"}])
        source = write(tmp_path / "w.svw", future)

        save(load(source), source)

        assert load(source).raw["annotationLayers"] == [{"id": "a1", "kind": "something-new"}]

    def test_a_field_nested_deep_inside_a_known_one_comes_back(self, tmp_path: Path) -> None:
        """The reason the document is held as the parsed mapping rather than unpacked into attributes:
        unpacking is how a field nobody wrote an attribute for disappears."""
        future = json.loads(json.dumps(MINIMAL))
        future["cases"][0]["futureThing"] = {"deeper": [1, 2, 3]}
        source = write(tmp_path / "w.svw", future)

        save(load(source), source)

        assert load(source).raw["cases"][0]["futureThing"] == {"deeper": [1, 2, 3]}

    def test_unknown_top_level_fields_can_be_named_to_the_user(self, tmp_path: Path) -> None:
        source = write(tmp_path / "w.svw", dict(MINIMAL, annotationLayers=[], somethingElse=1))

        assert load(source).unknown_fields == ("annotationLayers", "somethingElse")

    def test_a_newer_document_opens_and_may_not_be_written_back(self, tmp_path: Path) -> None:
        """CT-001 compatibility: keep every field it does not understand, and refuse to write it back
        under the older version - writing it would claim to understand a shape that changed."""
        source = write(tmp_path / "w.svw", dict(MINIMAL, formatVersion="5.0.0", newSection={"a": 1}))

        document = load(source)

        assert document.is_newer_than_this_build
        assert document.raw["newSection"] == {"a": 1}
        with pytest.raises(WorkspaceVersionError) as refusal:
            save(document, source)
        assert "5.0.0" in str(refusal.value)


class TestADamagedFileIsNeverWrittenTo:
    def test_a_truncated_document_reports_where_it_stopped(self, tmp_path: Path) -> None:
        source = tmp_path / "w.svw"
        source.write_text(json.dumps(MINIMAL, ensure_ascii=False)[:60], encoding="utf-8")

        with pytest.raises(WorkspaceFileError) as refusal:
            load(source)
        assert "行" in str(refusal.value)

    def test_the_bytes_on_disk_are_unchanged_after_a_failed_open(self, tmp_path: Path) -> None:
        """AC-013. Nothing in `load` opens the file for writing, so this holds by construction rather
        than by the absence of a bug - and the test says so out loud."""
        source = tmp_path / "w.svw"
        damaged = json.dumps(MINIMAL, ensure_ascii=False)[:60].encode("utf-8")
        source.write_bytes(damaged)

        with pytest.raises(WorkspaceFileError):
            load(source)

        assert source.read_bytes() == damaged

    def test_a_document_missing_a_required_field_is_not_an_old_one(self, tmp_path: Path) -> None:
        incomplete = {key: value for key, value in MINIMAL.items() if key != "cases"}
        source = write(tmp_path / "w.svw", incomplete)

        with pytest.raises(WorkspaceFileError) as refusal:
            load(source)
        assert "cases" in str(refusal.value)

    def test_a_file_that_is_not_an_object_is_refused_by_what_it_is(self, tmp_path: Path) -> None:
        source = tmp_path / "w.svw"
        source.write_text("[1, 2, 3]", encoding="utf-8")

        with pytest.raises(WorkspaceFileError) as refusal:
            load(source)
        assert "list" in str(refusal.value)


class TestTheOnlyCopyIsNeverAbsent:
    def test_a_save_keeps_the_previous_version_beside_the_new_one(self, tmp_path: Path) -> None:
        source = write(tmp_path / "w.svw", MINIMAL)
        document = load(source)
        document.raw["name"] = "changed"

        kept = save(document, source)

        assert kept.name == "w.svw" + PREVIOUS_SUFFIX
        assert json.loads(kept.read_text(encoding="utf-8"))["name"] == "梁の検討"
        assert load(source).raw["name"] == "changed"

    def test_the_first_save_has_no_previous_version_to_keep(self, tmp_path: Path) -> None:
        target = tmp_path / "new.svw"

        kept = save(WorkspaceDocument(raw=dict(MINIMAL)), target)

        assert kept == target
        assert not (tmp_path / ("new.svw" + PREVIOUS_SUFFIX)).exists()

    def test_the_previous_version_is_a_file_a_person_can_find(self, tmp_path: Path) -> None:
        """XC-055's restore procedure is "a file operation the user can perform without the product",
        which requires the file to be somewhere they can see."""
        source = write(tmp_path / "w.svw", MINIMAL)

        save(load(source), source)

        assert sorted(p.name for p in tmp_path.iterdir()) == ["w.svw", "w.svw.previous"]

    def test_no_working_file_is_left_behind(self, tmp_path: Path) -> None:
        source = write(tmp_path / "w.svw", MINIMAL)

        save(load(source), source)

        assert not list(tmp_path.glob("*.writing"))
