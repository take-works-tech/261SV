"""The composition root: the first production handlers on the command surface (XC-257, step 2).

Until 2026-09-18 no production code registered a handler, so every operation was answered "in the
catalogue, not in this build". These tests drive the real thing through the real surface - a
workspace file on disk, a result file the toolkit wrote, the contract's parameter names - and hold
the answers to CT-003's shapes, including the nested reported-value check of XC-253.

What is **not** registered is tested too: `view.render` and `dataset.probe` stay unimplemented here,
and the surface says so rather than answering with a picture or a number it does not have.

Verifies: CT-003, INV-006, INV-017, XC-003, XC-253, XC-257 (step 2).
"""

from __future__ import annotations

import base64
import json
import os
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import REQUIRE_VTK, offscreen_rendering_available, requires_h5py, requires_vtk

requires_vtk()

#: The rendering tests below run where the product's own probe says a picture can be drawn. Elsewhere
#: they skip with the probe's reason - except in CI, where test_render.py has already failed the run
#: for the same reason, because a renderer never exercised is a renderer nobody has seen work.
OFFSCREEN_AVAILABLE, OFFSCREEN_DETAIL = offscreen_rendering_available()
needs_offscreen = pytest.mark.skipif(
    not OFFSCREEN_AVAILABLE and not REQUIRE_VTK, reason=f"no offscreen rendering here: {OFFSCREEN_DETAIL}"
)


from engine.limits import MAX_WORKSPACE_ITEMS  # noqa: E402
from service.command.catalogue import OPERATIONS, PROTOCOL_VERSION  # noqa: E402
from service.command.handlers import HandleExpired, HandleStore, Session, build_surface  # noqa: E402
from service.command.surface import Command, Permission, Status, Surface  # noqa: E402
from service.egress.gate import Outcome, Permission as EgressPermission, SearchRequest  # noqa: E402
from service.workspace import items  # noqa: E402
from service.workspace.document import FORMAT_VERSION  # noqa: E402
from domain_core.recorded_time import STORED_FORMAT, record as record_time  # noqa: E402
from test_reader import write_exodus, write_grid  # noqa: E402
from demo_case import write_bar, write_cube, write_fields, write_two_blocks  # noqa: E402, F401 - re-exported for the tests that import it from here
from test_render import decode  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ZONE = timezone(timedelta(hours=9))


def at(hour: int, minute: int = 0):
    return lambda: datetime(2026, 9, 18, hour, minute, tzinfo=ZONE)


def counting_issuer():
    """Identifiers a test can predict: kind:0001, kind:0002 ..."""
    issued: dict[str, int] = {}

    def issue(kind: str) -> str:
        issued[kind] = issued.get(kind, 0) + 1
        return f"{kind}:{issued[kind]:04d}"

    return issue


def a_workspace(tmp_path: Path, *, cases: list[dict] | None = None) -> Path:
    document = {
        "formatVersion": FORMAT_VERSION,
        "id": "ws:1",
        "name": "梁の検討",
        "cases": cases if cases is not None else [{"id": "case:1", "name": "baseline"}],
        "variables": [],
        "workspaceItems": {"simulations": [], "views": [], "graphs": [], "reports": []},
    }
    path = tmp_path / "beam.svw"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def a_surface() -> tuple[Surface, Session]:
    session = Session(clock=at(9), issue=counting_issuer())
    return build_surface(session), session


def opened(tmp_path: Path) -> tuple[Surface, Session, Path]:
    surface, session = a_surface()
    workspace = a_workspace(tmp_path)
    result = surface.submit(Command("workspace.open", {"path": str(workspace)}))
    assert result.status is Status.APPLIED, result.reason
    return surface, session, workspace


def loaded(tmp_path: Path, *, write=write_grid, name: str = "case.vtu") -> tuple[Surface, Session, str]:
    surface, session, workspace = opened(tmp_path)
    source = workspace.parent / name
    write(source)
    result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
    assert result.status is Status.APPLIED, result.reason
    return surface, session, result.value["datasetId"]


class TestANewWorkspace:
    """XC-297: a document written where the person chose, with one case, and opened as any other."""

    def test_it_is_written_opened_and_reopens_by_its_name(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        target = tmp_path / "studies" / "梁.svw"
        target.parent.mkdir()

        created = surface.submit(Command("workspace.create", {"path": str(target), "name": "梁の検討", "caseName": "基準"}))

        assert created.status is Status.APPLIED, created.reason
        assert created.value["name"] == "梁の検討" and created.value["tags"] == []
        assert [one["name"] for one in created.value["cases"]] == ["基準"]
        assert created.value["readOnly"] is False and created.value["unresolvedCases"] == []
        assert session.workspace is not None and session.workspace.identifier == created.value["workspaceId"]
        on_disk = json.loads(target.read_text(encoding="utf-8"))
        assert on_disk["formatVersion"] == FORMAT_VERSION and on_disk["name"] == "梁の検討"
        assert on_disk["workspaceItems"] == {"simulations": [], "views": [], "graphs": [], "reports": []}
        again, _ = a_surface()
        reopened = again.submit(Command("workspace.open", {"path": str(target)}))
        assert reopened.status is Status.APPLIED and reopened.value["name"] == "梁の検討"

    def test_it_takes_the_file_name_and_a_default_case_where_none_is_given(self, tmp_path: Path) -> None:
        surface, _ = a_surface()
        created = surface.submit(Command("workspace.create", {"path": str(tmp_path / "bracket.svw")}))
        assert created.status is Status.APPLIED, created.reason
        assert created.value["name"] == "bracket" and [one["name"] for one in created.value["cases"]] == ["ケース 1"]

    def test_an_existing_file_and_a_missing_folder_are_refused_by_name_and_nothing_is_written(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        existing = a_workspace(tmp_path)
        before = existing.read_bytes()

        over = surface.submit(Command("workspace.create", {"path": str(existing)}))
        nowhere = surface.submit(Command("workspace.create", {"path": str(tmp_path / "no such folder" / "x.svw")}))

        assert over.status is Status.REFUSED and "すでにあります" in (over.reason or "")
        assert existing.read_bytes() == before, "nothing touched"
        assert nowhere.status is Status.REFUSED and "フォルダがありません" in (nowhere.reason or "")
        assert session.workspace is None

    def test_the_open_answer_names_the_document_and_the_tags_of_its_cases(self, tmp_path: Path) -> None:
        surface, _ = a_surface()
        workspace = a_workspace(tmp_path, cases=[
            {"id": "case:1", "name": "baseline", "tags": ["構造", "基準"], "children": [{"id": "case:2", "name": "variant", "tags": ["熱"]}]},
        ])
        opened = surface.submit(Command("workspace.open", {"path": str(workspace)}))
        assert opened.status is Status.APPLIED, opened.reason
        assert opened.value["name"] == "梁の検討" and opened.value["tags"] == ["基準", "構造", "熱"]


class TestTheSample:
    """XC-298, operations/AC-002: the shipped sample, generated where the person chose and opened."""

    def test_it_is_written_beside_its_document_with_two_cases_and_their_declared_units(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        target = tmp_path / "片持ち梁.svw"

        made = surface.submit(Command("workspace.sample", {"path": str(target)}))

        assert made.status is Status.APPLIED, made.reason
        assert made.value["name"] == "片持ち梁（サンプル）" and made.value["tags"] == ["1.5 倍", "静荷重"]
        assert [one["name"] for one in made.value["cases"]] == ["荷重 100 N", "荷重 150 N"]
        assert made.value["unresolvedCases"] == []
        first = made.value["cases"][0]
        assert first["sources"] == [{"name": "cantilever_100N.vtu", "path": str(tmp_path / "片持ち梁.data" / "cantilever_100N.vtu"), "present": True}]
        assert (tmp_path / "片持ち梁.data" / "cantilever_150N.vtu").exists()
        # Loading a case applies the units its author declared, and the maximum is the formula's.
        loaded = surface.submit(Command("dataset.load", {"caseId": first["id"], "filePaths": [first["sources"][0]["path"]]}))
        assert loaded.status is Status.APPLIED, loaded.reason
        units = {field["name"]: field["unit"] for field in loaded.value["fields"]}
        assert units == {"stress": "Pa", "element_stress": "Pa", "displacement": "m"}
        statistics = surface.submit(Command("field.statistics", {"datasetId": loaded.value["datasetId"], "fieldName": "stress"}))
        assert statistics.value["maximum"]["value"] == pytest.approx(1.2e6) and statistics.value["maximum"]["unit"] == "Pa"
        on_disk = json.loads(target.read_text(encoding="utf-8"))
        assert on_disk["createdBy"] and on_disk["cases"][1]["sources"][0]["pathRelative"] == "片持ち梁.data/cantilever_150N.vtu"
        assert session.workspace is not None and session.workspace.identifier == made.value["workspaceId"]

    def test_a_document_or_a_data_folder_already_there_is_refused_and_nothing_is_written(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        (tmp_path / "梁.data").mkdir()

        folder = surface.submit(Command("workspace.sample", {"path": str(tmp_path / "梁.svw")}))
        existing = surface.submit(Command("workspace.sample", {"path": str(a_workspace(tmp_path))}))

        assert folder.status is Status.REFUSED and "梁.data" in (folder.reason or "")
        assert existing.status is Status.REFUSED and "すでにあります" in (existing.reason or "")
        assert not (tmp_path / "梁.svw").exists() and session.workspace is None

    def test_the_open_answer_says_where_each_case_s_file_is_and_whether_it_is_there(self, tmp_path: Path) -> None:
        surface, _ = a_surface()
        made = surface.submit(Command("workspace.sample", {"path": str(tmp_path / "s.svw")}))
        assert made.status is Status.APPLIED, made.reason
        gone = Path(made.value["cases"][1]["sources"][0]["path"])
        gone.unlink()

        again, _ = a_surface()
        reopened = again.submit(Command("workspace.open", {"path": str(tmp_path / "s.svw")}))

        assert reopened.status is Status.APPLIED, reopened.reason
        assert [one["sources"][0]["present"] for one in reopened.value["cases"]] == [True, False]
        assert reopened.value["unresolvedCases"] == [reopened.value["cases"][1]["id"]]


class TestWhatThisBuildRegisters:
    def test_every_operation_on_the_path_has_a_handler(self) -> None:
        surface, _ = a_surface()

        registered = set(surface.registered())

        assert registered == {
            "workspace.open", "workspace.create", "workspace.sample", "dataset.load", "dataset.describe", "dataset.parts",
            "field.declareUnit", "field.statistics", "field.derive", "view.create", "view.update", "view.get", "view.render",
            "graph.create", "graph.update", "graph.get", "graph.data",
            "dataset.probe", "view.pick", "report.create", "report.update", "report.get",
            "report.export", "report.provenance",
            "workspace.save", "dataset.inspect", "history.list",
            "system.capabilities", "system.protocols", "system.audit", "system.operations", "system.log",
            "system.supportManifest", "system.supportBundle",
            "output.list", "output.plan", "output.prune",
        }
        assert len(surface.unimplemented()) == len(OPERATIONS) - 37

    def test_operations_list_what_this_build_answers_and_what_it_does_not(self) -> None:
        """XC-277: the list is the surface's own registry, and the two halves are the whole catalogue."""
        surface, _ = a_surface()

        result = surface.submit(Command("system.operations", {}))

        assert result.status is Status.ANSWERED, result.reason
        registered, unimplemented = result.value["registered"], result.value["unimplemented"]
        assert "system.operations" in registered and "graph.duplicate" in unimplemented
        assert tuple(registered) == surface.registered()
        assert tuple(unimplemented) == surface.unimplemented()
        assert set(registered) | set(unimplemented) == set(OPERATIONS)
        assert not set(registered) & set(unimplemented)

    def test_an_unimplemented_operation_is_refused_and_named_as_such(self) -> None:
        surface, _ = a_surface()
        assert "graph.duplicate" in surface.unimplemented()

        result = surface.submit(Command("graph.duplicate", {"graphId": "g", "newName": "copy"}))

        assert result.status is Status.REFUSED
        assert "実装がありません" in (result.reason or "")

    def test_the_protocol_version_is_the_contract_s(self) -> None:
        surface, _ = a_surface()
        contract = (ROOT / "specs/contracts/CT-003_engine_api.md").read_text(encoding="utf-8")
        declared = next(line.split(":", 1)[1].strip() for line in contract.splitlines() if line.startswith("- version:"))

        result = surface.submit(Command("system.protocols", {}))

        assert result.status is Status.ANSWERED
        assert result.value == {"versions": [declared]}
        assert PROTOCOL_VERSION == declared

    def test_capabilities_say_which_formats_and_which_renderers_with_their_requirements(self) -> None:
        session = Session(clock=at(9), issue=counting_issuer(), native_offscreen=lambda: (False, "テスト：無し"))
        surface = build_surface(session)

        result = surface.submit(Command("system.capabilities", {}))

        assert result.status is Status.ANSWERED
        formats = {one["format"]: one["level"] for one in result.value["formats"]}
        assert formats["vtu"] == "verified"
        assert set(formats.values()) <= {"verified", "offered", "absent"}
        renderers = {one["backend"]: one for one in result.value["renderers"]}
        assert renderers["nativeOffscreen"]["available"] is False
        assert renderers["nativeOffscreen"]["requires"]
        assert renderers["webgl2"]["available"] is False, "the engine cannot know about the browser"
        assert result.value["machineClass"] == "integrated-graphics", "the safe class, until measured"


class TestOpeningAWorkspace:
    def test_a_missing_file_is_refused_with_the_reason(self, tmp_path: Path) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("workspace.open", {"path": str(tmp_path / "none.svw")}))

        assert result.status is Status.REFUSED
        assert "none.svw" in (result.reason or "")

    def test_opening_answers_in_the_contract_s_shape(self, tmp_path: Path) -> None:
        surface, session, workspace = opened(tmp_path)

        assert session.workspace is not None
        assert session.workspace_path == workspace
        history = surface.history()
        assert history[-1].operation == "workspace.open"

    def test_a_case_whose_source_is_gone_is_named_as_unresolved(self, tmp_path: Path) -> None:
        surface, _ = a_surface()
        workspace = a_workspace(tmp_path, cases=[{
            "id": "case:1", "name": "baseline",
            "sources": [{"pathRelative": "gone.vtu", "sizeBytes": 10, "modified": {"utc": "2026-09-18T00:00:00Z", "offsetMinutes": 540}}],
        }])

        result = surface.submit(Command("workspace.open", {"path": str(workspace)}))

        assert result.status is Status.APPLIED
        assert result.value["unresolvedCases"] == ["case:1"]
        assert result.value["workspaceId"] == "ws:1"
        assert result.value["formatVersion"] == FORMAT_VERSION

    def test_undo_closes_it_again(self, tmp_path: Path) -> None:
        surface, session, _ = opened(tmp_path)
        undo_id = surface.history()[-1].undo_id
        assert undo_id

        result = surface.undo(undo_id)

        assert result.status is Status.APPLIED
        assert session.workspace is None


class TestViewsAndReportsAsWorkspaceItems:
    def test_creating_needs_an_open_workspace(self) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {}}))

        assert result.status is Status.REFUSED
        assert "workspace.open" in (result.reason or "")

    def test_the_wrong_workspace_is_refused(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("view.create", {"workspaceId": "ws:other", "definition": {}}))

        assert result.status is Status.REFUSED

    def test_a_view_is_created_with_its_identifier_and_revision(self, tmp_path: Path) -> None:
        surface, session, _ = opened(tmp_path)

        result = surface.submit(Command("view.create", {
            "workspaceId": "ws:1",
            "definition": {"name": "応力", "datasetId": "dataset:0001", "representation": "surface"},
        }))

        assert result.status is Status.APPLIED, result.reason
        assert result.value == {"id": "view:0001", "revision": 1}
        assert session.workspace is not None
        stored = session.workspace.raw["workspaceItems"]["views"][0]
        assert stored["id"] == "view:0001"
        assert stored["definition"]["id"] == "view:0001"
        assert stored["definition"]["representation"] == "surface"

    def test_updating_bumps_the_revision_and_undo_puts_the_definition_back(self, tmp_path: Path) -> None:
        surface, session, _ = opened(tmp_path)
        surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {"name": "応力", "representation": "surface"}}))

        updated = surface.submit(Command("view.update", {"viewId": "view:0001", "definition": {"representation": "wireframe"}}))
        assert updated.status is Status.APPLIED, updated.reason
        assert updated.value == {"id": "view:0001", "revision": 2}
        assert session.workspace is not None
        assert session.workspace.raw["workspaceItems"]["views"][0]["definition"] == {"representation": "wireframe"}

        undone = surface.undo(updated.undo_id or "")
        assert undone.status is Status.APPLIED
        assert session.workspace.raw["workspaceItems"]["views"][0]["definition"]["representation"] == "surface"
        assert session.revisions["view:0001"] == 1

    def test_a_template_source_is_refused_rather_than_ignored(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("view.create", {
            "workspaceId": "ws:1", "definition": {}, "sourceTemplateId": "template:1",
        }))

        assert result.status is Status.REFUSED
        assert "テンプレート" in (result.reason or "")

    def test_a_report_is_created_the_same_way(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("report.create", {
            "workspaceId": "ws:1", "definition": {"name": "報告", "blocks": [], "targets": ["html"]},
        }))

        assert result.status is Status.APPLIED, result.reason
        assert result.value == {"id": "report:0001", "revision": 1}


class TestHandles:
    def test_a_handle_names_its_lifetime_and_expires_after_it(self) -> None:
        now = {"minute": 0}
        store = HandleStore(clock=lambda: datetime(2026, 9, 18, 9, now["minute"], tzinfo=ZONE), lifetime_seconds=60)

        issued = store.issue(b"png bytes")

        assert issued["bytes"] == 9
        assert issued["expiresAfterSeconds"] == 60
        assert store.fetch(issued["id"]) == b"png bytes"
        now["minute"] = 2
        with pytest.raises(HandleExpired):
            store.fetch(issued["id"])

    def test_an_unknown_handle_is_a_refusal_not_an_empty_answer(self) -> None:
        store = HandleStore(clock=at(9))
        with pytest.raises(HandleExpired):
            store.fetch("handle:nothing")


class TestLoadingADataset:
    def test_loading_needs_an_open_workspace(self, tmp_path: Path) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": ["x.vtu"]}))

        assert result.status is Status.REFUSED

    def test_an_unknown_case_is_refused(self, tmp_path: Path) -> None:
        surface, _, workspace = opened(tmp_path)

        result = surface.submit(Command("dataset.load", {"caseId": "case:9", "filePaths": [str(workspace)]}))

        assert result.status is Status.REFUSED
        assert "case:9" in (result.reason or "")

    def test_a_file_that_cannot_be_read_is_the_caller_s_problem_not_the_build_s(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(tmp_path / "none.vtu")]}))

        assert result.status is Status.REFUSED, "refused, not failed: the file is missing, the build is not defective"

    def test_several_files_are_refused_and_the_reason_says_why(self, tmp_path: Path) -> None:
        surface, _, workspace = opened(tmp_path)
        write_grid(tmp_path / "a.vtu")

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(tmp_path / "a.vtu"), str(tmp_path / "a.vtu")]}))

        assert result.status is Status.REFUSED
        assert "1 ファイル" in (result.reason or "")

    def test_a_loaded_dataset_answers_with_its_fields_undeclared(self, tmp_path: Path) -> None:
        surface, session, _ = opened(tmp_path)
        source = tmp_path / "case.vtu"
        write_grid(source)

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))

        assert result.status is Status.APPLIED, result.reason
        assert result.value["datasetId"] == "dataset:0001"
        assert result.value["supportLevel"] == "verified"
        assert result.value["gaps"] == []
        fields = {one["name"]: one for one in result.value["fields"]}
        assert fields["stress"] == {"name": "stress", "association": "point", "unit": None, "components": 1, "missingCount": 0}
        assert fields["element_stress"]["association"] == "cell"
        assert "dataset:0001" in session.datasets

    def test_describe_and_parts_count_what_arrived(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        described = surface.submit(Command("dataset.describe", {"datasetId": dataset_id}))
        parts = surface.submit(Command("dataset.parts", {"datasetId": dataset_id}))

        assert described.status is Status.ANSWERED, described.reason
        assert described.value["pointCount"] == 4
        assert described.value["cellCount"] == 2
        assert described.value["boundsM"] == {"minM": [0.0, 0.0, 0.0], "maxM": [1.0, 1.0, 0.0]}
        assert described.value["partial"] is False
        assert described.value["resultAxis"]["kind"] in {"time", "mode", "frequency", "undeclared", "none"}
        assert described.value["resultAxis"]["unit"] is None
        assert parts.status is Status.ANSWERED
        assert parts.value["parts"] == [{
            "name": "case", "type": "part", "path": ["case"], "pointCount": 4, "cellCount": 2,
            "boundsM": {"minM": [0.0, 0.0, 0.0], "maxM": [1.0, 1.0, 0.0]},
        }]

    def test_an_unknown_dataset_is_refused(self, tmp_path: Path) -> None:
        surface, _, _ = loaded(tmp_path)

        result = surface.submit(Command("dataset.describe", {"datasetId": "dataset:9"}))

        assert result.status is Status.REFUSED


class TestDeclaringAUnit:
    def test_a_symbol_this_product_does_not_know_is_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "furlongs"}))

        assert result.status is Status.REFUSED
        assert "furlongs" in (result.reason or "")

    def test_a_field_that_is_not_there_is_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "nothing", "unitSymbol": "MPa"}))

        assert result.status is Status.REFUSED

    def test_a_declaration_reaches_the_statistics_and_undo_removes_it(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path)

        declared = surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        assert declared.status is Status.APPLIED, declared.reason
        after = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))
        assert after.value["maximum"]["unit"] == "MPa"
        assert session.datasets[dataset_id].declared_units == {"stress": "MPa"}

        surface.undo(declared.undo_id or "")
        before = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))
        assert before.value["maximum"]["unit"] is None
        assert "undeclared-unit" in before.value["maximum"]["caveats"]


class TestStatistics:
    def test_the_answer_is_held_to_the_contract_s_reported_value_shape(self, tmp_path: Path) -> None:
        """The whole point of step one's nested check: this handler passes it, which means every number
        in the answer arrived with its unit, its digits and its provenance."""
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        assert result.status is Status.ANSWERED, result.reason
        for key in ("minimum", "maximum", "mean"):
            assert {"value", "unit", "digits", "provenance"} <= set(result.value[key])

    def test_extrema_are_exact_and_carry_storage_digits_and_a_location(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        maximum, minimum = result.value["maximum"], result.value["minimum"]
        assert maximum["value"] == 40.0
        assert maximum["digits"] == 6, "float32 in the file, six digits and not fifteen (INV-014)"
        assert maximum["provenance"] == "computed"
        assert maximum["location"], "where the maximum sits, in the source's words"
        assert minimum["value"] == 10.0
        assert result.value["missingCount"] == 0
        assert result.value["association"] == "point"

    def test_a_surface_mesh_has_no_weighted_mean_and_says_so_rather_than_averaging(self, tmp_path: Path) -> None:
        """INV-017: an arithmetic mean under the weighted label, or the weighted label over an arithmetic
        mean, are both refused. Two triangles have no volume, so the dual-volume mean is unavailable."""
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        mean = result.value["mean"]
        assert mean["value"] is None
        assert "面" in mean["missingBecause"]
        assert result.value["weighting"] == "dualVolume"

    def test_a_mesh_with_volume_gets_the_weighted_mean(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "temperature"}))

        assert result.status is Status.ANSWERED, result.reason
        mean = result.value["mean"]
        assert mean["value"] == pytest.approx(4.5)
        assert mean["formula"] == "mean(temperature)"
        assert result.value["weighting"] == "dualVolume"
        assert result.value["maximum"]["value"] == 8.0

    def test_a_region_is_one_part_and_its_numbers_are_that_part_s_with_the_scope_stated(self, tmp_path: Path) -> None:
        """INV-019, view/AC-035: a part's maximum differs from the model's, and each says what it covered."""
        surface, _, dataset_id = loaded(tmp_path, write=write_two_blocks, name="two.ex2")
        parts = surface.submit(Command("dataset.parts", {"datasetId": dataset_id})).value["parts"]
        quad = next(one["name"] for one in parts if one["cellCount"] == 1)
        triangles = next(one["name"] for one in parts if one["cellCount"] == 2)

        whole = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))
        in_quad = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "region": quad}))
        in_triangles = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "region": triangles}))

        assert whole.status is Status.ANSWERED and in_quad.status is Status.ANSWERED, (whole.reason, in_quad.reason)
        assert whole.value["maximum"]["value"] == 90.0 and whole.value["scope"].startswith("ケース全体")
        assert in_quad.value["maximum"]["value"] == 60.0
        assert in_quad.value["minimum"]["value"] == 20.0
        assert in_quad.value["scope"] == f"パート {quad}"
        assert in_quad.value["maximum"]["location"].startswith(quad)
        assert in_triangles.value["maximum"]["value"] == 90.0
        assert in_triangles.value["scope"] == f"パート {triangles}"

    def test_a_cell_field_answers_both_numbers_and_the_spread_at_the_peak(self, tmp_path: Path) -> None:
        """INV-032, XC-247, E-144: 110 against 200 on a concentration inside the body, the spread 180 at
        that node, each figure labelled, and the disagreement said."""
        surface, _, dataset_id = loaded(tmp_path, write=write_bar, name="bar.vtu")
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["averaging"] == "unaveraged"
        assert result.value["maximum"]["value"] == 200.0
        averaged = result.value["averaged"]
        assert averaged["maximum"]["value"] == pytest.approx(110.0)
        assert "averaged" in averaged["maximum"]["caveats"]
        assert averaged["maximum"]["unit"] == "MPa"
        assert averaged["maximum"]["location"].startswith("bar：")
        assert averaged["minimum"]["value"] == pytest.approx(10.0)
        assert averaged["spreadAtMaximum"]["value"] == pytest.approx(180.0)
        assert averaged["spreadFraction"]["value"] == pytest.approx(180.0 / 110.0)
        assert averaged["spreadFraction"]["unit"] == "1", "a ratio is dimensionless, and SI writes that as 1"
        assert "90" in averaged["disagreement"] and "45%" in averaged["disagreement"]

    def test_a_point_field_has_no_averaging_question(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        assert result.status is Status.ANSWERED
        assert "averaging" not in result.value and "averaged" not in result.value

    def test_the_document_states_both_numbers_for_a_cell_field(self, tmp_path: Path) -> None:
        """A report that gives one without saying which has answered neither (INV-032)."""
        surface, _, dataset_id = loaded(tmp_path, write=write_bar, name="bar.vtu")
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "棒", "targets": ["html"], "blocks": [{"kind": "valueTable", "fields": ["stress"]}],
        }})).value["id"]
        target = tmp_path / "bar.html"

        exported = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert exported.status is Status.APPLIED, exported.reason
        text = target.read_text(encoding="utf-8")
        assert "要素値・平均なし" in text and "200" in text
        assert "節点平均" in text and "110" in text
        assert "ばらつき" in text and "180" in text
        assert "セル間で平均した値です" in text

    def test_a_region_that_is_no_part_is_refused_by_name(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "region": "part 1"}))

        assert result.status is Status.REFUSED
        assert "part 1" in (result.reason or "") and "case" in (result.reason or "")


class TestDerivedQuantities:
    """`field.derive` (XC-282, INV-020): a catalogue quantity made by the engine from canonical data,
    listed beside the file's fields with its formula and conventions; and a field of several
    components refused as one number wherever one is asked for."""

    def test_the_load_says_how_many_components_each_field_has(self, tmp_path: Path) -> None:
        surface, session, workspace = opened(tmp_path)
        source = workspace.parent / "fields.vtu"
        write_fields(source)

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))

        assert result.status is Status.APPLIED, result.reason
        components = {one["name"]: one["components"] for one in result.value["fields"]}
        assert components == {"displacement": 3, "stress6": 6}

    def test_a_vector_is_refused_as_one_number_and_its_magnitude_is_derived_with_the_formula(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_fields, name="fields.vtu")
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "displacement", "unitSymbol": "mm"}))

        raw = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "displacement"}))
        probed = surface.submit(Command("dataset.probe", {"datasetId": dataset_id, "fieldName": "displacement", "pointM": [0.0, 0.0, 0.0], "resultPosition": 0}))
        made = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "magnitude"}))
        statistics = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "displacement.magnitude"}))

        assert raw.status is Status.REFUSED and "3 成分" in (raw.reason or "")
        assert probed.status is Status.REFUSED and "導出量" in (probed.reason or "")
        assert made.status is Status.ANSWERED, made.reason
        assert made.value["fieldName"] == "displacement.magnitude"
        assert made.value["fieldNames"] == ["displacement.magnitude"]
        assert made.value["formula"] == "sqrt(X^2 + Y^2 + Z^2)"
        assert any("global Cartesian" in one for one in made.value["conventions"])
        assert made.value["association"] == "point" and made.value["unit"] == "mm"
        assert statistics.status is Status.ANSWERED, statistics.reason
        assert statistics.value["maximum"]["value"] == 7.0
        assert statistics.value["maximum"]["unit"] == "mm"
        assert statistics.value["maximum"]["digits"] == 6, "the source's precision, not the arithmetic's"

    def test_von_mises_and_the_three_principal_values_come_with_their_conventions(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_fields, name="fields.vtu")

        mises = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "stress6", "quantity": "vonMises"}))
        principal = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "stress6", "quantity": "principal"}))
        top = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress6.principal1"}))
        mises_stats = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress6.vonMises"}))

        assert mises.status is Status.ANSWERED, mises.reason
        assert mises.value["formula"].startswith("sqrt( ((XX-YY)^2")
        assert any("XX, YY, ZZ, XY, YZ, XZ" in one for one in mises.value["conventions"])
        assert principal.value["fieldNames"] == ["stress6.principal1", "stress6.principal2", "stress6.principal3"]
        assert any("大きい順" in one for one in principal.value["conventions"])
        assert top.value["maximum"]["value"] == 200.0
        assert mises_stats.value["maximum"]["value"] == pytest.approx(173.205, abs=0.001)
        assert mises_stats.value["maximum"]["unit"] is None, "the source's unit was never declared"

    def test_what_is_not_derived_is_refused_by_name(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_fields, name="fields.vtu")

        unknown = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "stress6", "quantity": "curl"}))
        not_built = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "stress6", "quantity": "invariants"}))
        framed = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "component", "component": "X", "frameId": "frame:cyl"}))
        unnamed = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "component"}))

        assert unknown.status is Status.REFUSED and "magnitude" in (unknown.reason or "")
        assert not_built.status is Status.REFUSED and "二乗" in (not_built.reason or "")
        assert framed.status is Status.REFUSED and "frame:cyl" in (framed.reason or "") and "global Cartesian" in (framed.reason or "")
        assert unnamed.status is Status.REFUSED and "'X', 'Y', 'Z'" in (unnamed.reason or "")


@needs_offscreen
class TestColouringByAVector:
    def test_a_vector_is_not_coloured_and_its_magnitude_is(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_fields, name="fields.vtu")
        surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "magnitude"}))

        def view(field: str) -> str:
            return surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
                "name": f"図 {field}", "datasetId": dataset_id, "representation": "surface",
                "colouring": {"fieldName": field, "association": "point", "colourMap": "viridis"},
            }})).value["id"]

        raw = surface.submit(Command("view.render", {"viewId": view("displacement"), "width": 200, "height": 200, "format": "png"}))
        magnitude = surface.submit(Command("view.render", {"viewId": view("displacement.magnitude"), "width": 200, "height": 200, "format": "png"}))

        assert raw.status is Status.REFUSED and "3 成分" in (raw.reason or "")
        assert magnitude.status is Status.ANSWERED, magnitude.reason


class TestExportingADeliverable:
    def _report(self, surface: Surface) -> str:
        created = surface.submit(Command("report.create", {
            "workspaceId": "ws:1",
            "definition": {
                "name": "Run 1 の最大応力",
                "targets": ["html"],
                "blocks": [
                    {"kind": "text", "text": "梁の基本ケース。"},
                    {"kind": "valueTable", "fields": ["stress"]},
                ],
            },
        }))
        assert created.status is Status.APPLIED, created.reason
        return created.value["id"]

    def test_the_whole_thread_from_file_to_document_through_the_surface(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        report_id = self._report(surface)
        target = tmp_path / "out" / "run1.html"
        target.parent.mkdir()

        exported = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert exported.status is Status.APPLIED, exported.reason
        assert exported.value["path"] == str(target)
        assert exported.value["bytes"] == target.stat().st_size > 0
        assert exported.value["reductions"] == []
        # No font ships (OPEN-032): the document says which characters it could not carry, and the
        # answer lists the same statements rather than keeping them to itself.
        assert exported.value["omitted"], "the omission is stated, not silent"
        text = target.read_text(encoding="utf-8")
        assert "40" in text and "MPa" in text
        assert "case.vtu" in text, "the source file is named in the provenance"
        assert "http" not in text.lower() or "http-equiv" in text.lower(), "self-contained: no external reference"

    def test_provenance_names_the_workspace_the_case_the_source_and_the_declared_unit(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        report_id = self._report(surface)

        result = surface.submit(Command("report.provenance", {"reportId": report_id}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["workspaceId"] == "ws:1"
        assert result.value["caseIds"] == ["case:1"]
        assert result.value["sources"][0]["path"].endswith("case.vtu")
        assert result.value["sources"][0]["modified"]["utc"]
        assert result.value["produced"]["offsetMinutes"] == 540
        assert result.value["declaredUnits"] == {"stress": "MPa"}
        assert result.value["productVersion"]

    def test_an_existing_file_is_not_overwritten(self, tmp_path: Path) -> None:
        surface, _, _ = loaded(tmp_path)
        report_id = self._report(surface)
        target = tmp_path / "taken.html"
        target.write_text("already here", encoding="utf-8")

        result = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert result.status is Status.REFUSED
        assert target.read_text(encoding="utf-8") == "already here"

    def test_a_value_table_with_two_datasets_loaded_is_refused_rather_than_guessed(self, tmp_path: Path) -> None:
        surface, _, _ = loaded(tmp_path)
        write_grid(tmp_path / "second.vtu")
        surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(tmp_path / "second.vtu")]}))
        report_id = self._report(surface)

        result = surface.submit(Command("report.export", {"reportId": report_id, "path": str(tmp_path / "two.html")}))

        assert result.status is Status.REFUSED
        assert "推測" in (result.reason or "")

    def test_reading_provenance_back_from_a_file_is_refused_until_built(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("report.provenance", {"exportedPath": str(tmp_path / "x.html")}))

        assert result.status is Status.REFUSED


class TestProbingAPoint:
    """Step 4 through the surface. The answer is held to CT-003's nested reported-value shape, a
    point off the model is an answer of nothing rather than a refusal, and a result position this
    build cannot walk to is refused by name."""

    def test_a_vertex_answers_with_its_value_and_says_it_is_a_point_s(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))

        result = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "stress", "pointM": [0.0, 1.0, 0.0], "resultPosition": 0,
        }))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["association"] == "point"
        value = result.value["value"]
        assert value["value"] == 40.0
        assert value["unit"] == "MPa"
        assert value["digits"] == 6
        assert value["provenance"] == "dataset"
        assert value["location"], "where, in the source's words - or the statement that it had none"

    def test_a_cell_field_answers_with_the_cell_s_value(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "element_stress", "pointM": [0.7, 0.2, 0.0], "resultPosition": 0,
        }))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["association"] == "cell"
        assert result.value["value"]["value"] == 100.0

    def test_a_point_off_the_model_is_an_answer_of_nothing(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "stress", "pointM": [9.0, 9.0, 9.0], "resultPosition": 0,
        }))

        assert result.status is Status.ANSWERED, "a well-formed question with nothing there is answered, not refused"
        value = result.value["value"]
        assert value["value"] is None
        assert "外" in value["missingBecause"]
        assert value["unit"] is None and value["digits"] == 6

    def test_a_step_a_steady_case_does_not_have_is_refused_by_name(self, tmp_path: Path) -> None:
        """view/AC-033: a steady case has one step; asking for a fourth is refused, not read as the first."""
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "stress", "pointM": [0.0, 0.0, 0.0], "resultPosition": 3,
        }))

        assert result.status is Status.REFUSED
        assert "ステップ番号 3" in (result.reason or "") and "定常" in (result.reason or "")

    def test_an_unknown_field_is_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "nothing", "pointM": [0.0, 0.0, 0.0], "resultPosition": 0,
        }))

        assert result.status is Status.REFUSED

    def test_the_contract_now_names_the_field(self) -> None:
        """CT-003 2.2.0: a probe without a field name was a question with no answer."""
        from service.command.catalogue import PARAMETERS

        assert "fieldName" in PARAMETERS["dataset.probe"][1]


class TestEditingAReport:
    """`report.update` and `report.get` (CT-003 3.6.0): the block list an interface edits reaches the
    document, and is read back from it with the revision rather than remembered (XC-275)."""

    def test_the_block_list_is_written_and_read_back_with_its_revision(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)
        report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "梁", "targets": ["html"], "blocks": [{"kind": "text", "text": "一。"}],
        }})).value["id"]
        first = surface.submit(Command("report.get", {"reportId": report_id}))

        updated = surface.submit(Command("report.update", {"reportId": report_id, "definition": {
            "id": report_id, "name": "梁", "targets": ["html"],
            "blocks": [{"kind": "pageBreak"}, {"kind": "text", "text": "一。"}],
        }}))
        second = surface.submit(Command("report.get", {"reportId": report_id}))

        assert first.status is Status.ANSWERED, first.reason
        assert first.value["revision"] == 1
        assert [one["kind"] for one in first.value["definition"]["blocks"]] == ["text"]
        assert updated.status is Status.APPLIED, updated.reason
        assert updated.value == {"id": report_id, "revision": 2}
        assert second.value["revision"] == 2
        assert [one["kind"] for one in second.value["definition"]["blocks"]] == ["pageBreak", "text"]

    def test_a_report_the_document_does_not_hold_is_refused(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("report.get", {"reportId": "report:none"}))

        assert result.status is Status.REFUSED
        assert "report:none" in (result.reason or "")


class TestReadingAViewBack:
    """`view.get` (CT-003 3.5.0): the definition the document holds now, with its revision - what an
    interface reads before it writes, so a saved camera or a hidden part survives the next redraw."""

    def test_get_answers_the_definition_the_document_holds_and_its_revision(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)
        view_id = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "応力", "representation": "surface",
        }})).value["id"]

        first = surface.submit(Command("view.get", {"viewId": view_id}))
        surface.submit(Command("view.update", {"viewId": view_id, "definition": {
            "name": "応力", "representation": "surface", "partVisibility": {"gasket": False},
        }}))
        second = surface.submit(Command("view.get", {"viewId": view_id}))

        assert first.status is Status.ANSWERED, first.reason
        assert first.value["id"] == view_id and first.value["revision"] == 1
        assert first.value["definition"]["name"] == "応力"
        assert "partVisibility" not in first.value["definition"]
        assert second.value["revision"] == 2
        assert second.value["definition"]["partVisibility"] == {"gasket": False}

    def test_a_view_the_document_does_not_hold_is_refused(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("view.get", {"viewId": "view:none"}))

        assert result.status is Status.REFUSED
        assert "view:none" in (result.reason or "")


@needs_offscreen
class TestPartVisibility:
    """What the outliner's visibility toggle means to the engine (CT-004 `partVisibility`, INV-019,
    XC-274): a hidden part is not drawn, not picked and not exported; a definition that hides every
    part, or names one that is not there, is refused rather than drawn past."""

    @staticmethod
    def _two(tmp_path: Path) -> tuple[Surface, Session, str, list[str]]:
        surface, session, dataset_id = loaded(tmp_path, write=write_two_blocks, name="two.ex2")
        parts = surface.submit(Command("dataset.parts", {"datasetId": dataset_id})).value["parts"]
        return surface, session, dataset_id, [one["name"] for one in parts]

    @staticmethod
    def _view(surface: Surface, dataset_id: str, visibility: dict | None = None) -> str:
        definition: dict = {
            "name": f"全体図 {json.dumps(visibility, ensure_ascii=False, sort_keys=True)}", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point", "colourMap": "viridis"},
            # One fixed look for every view here. Without it the renderer fits the camera to what is
            # shown, and a frame with a part hidden covers *more* pixels, not fewer - measured on
            # 2026-09-20, and the reason the interface always draws with a camera of its own.
            "camera": {"position_m": [1.0, 0.5, 6.0], "focalPoint_m": [1.0, 0.5, 0.0], "viewUp": [0.0, 1.0, 0.0], "projection": "perspective"},
        }
        if visibility is not None:
            definition["partVisibility"] = visibility
        return surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": definition})).value["id"]

    @staticmethod
    def _drawn(session: Session, surface: Surface, view_id: str) -> int:
        """How many pixels the model covers in a frame: those not the background's colour."""
        answer = surface.submit(Command("view.render", {
            "viewId": view_id, "width": 200, "height": 200, "format": "png", "legend": False,
        }))
        assert answer.status is Status.ANSWERED, answer.reason
        frame = decode(session.handles.fetch(answer.value["handle"]))
        return int((frame != frame[0, 0]).any(axis=2).sum())

    def test_the_parts_come_with_the_file_s_own_hierarchy(self, tmp_path: Path) -> None:
        surface, _, dataset_id, names = self._two(tmp_path)

        parts = surface.submit(Command("dataset.parts", {"datasetId": dataset_id})).value["parts"]

        assert len(parts) == 2 and len(set(names)) == 2
        for one in parts:
            assert one["path"][:2] == ["two", "Element Blocks"] and len(one["path"]) == 3
            assert one["parentId"] == "two / Element Blocks"
            assert one["name"] == " / ".join(one["path"])
            assert one["type"] == "part" and one["cellCount"] > 0

    def test_a_hidden_part_is_not_drawn(self, tmp_path: Path) -> None:
        surface, session, dataset_id, names = self._two(tmp_path)

        everything = self._drawn(session, surface, self._view(surface, dataset_id))
        without_one = self._drawn(session, surface, self._view(surface, dataset_id, {names[1]: False}))

        assert 0 < without_one < everything

    def test_hiding_every_part_is_refused_rather_than_drawn_empty(self, tmp_path: Path) -> None:
        surface, _, dataset_id, names = self._two(tmp_path)
        view_id = self._view(surface, dataset_id, {name: False for name in names})

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 200, "height": 200, "format": "png"}))

        assert result.status is Status.REFUSED
        assert "非表示" in (result.reason or "")

    def test_a_name_the_dataset_does_not_have_is_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id, names = self._two(tmp_path)
        view_id = self._view(surface, dataset_id, {names[0]: True, "two / Element Blocks / ghost": False})

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 200, "height": 200, "format": "png"}))

        assert result.status is Status.REFUSED
        assert "ghost" in (result.reason or "") and names[0] in (result.reason or "")

    def test_the_pick_names_the_part_that_answered_and_never_a_hidden_one(self, tmp_path: Path) -> None:
        surface, _, dataset_id, names = self._two(tmp_path)
        pixel = {"width": 200, "height": 200, "x": 150, "y": 100}

        shown = surface.submit(Command("view.pick", {"viewId": self._view(surface, dataset_id), **pixel}))
        assert shown.status is Status.ANSWERED, shown.reason
        answered = shown.value.get("part")
        assert answered in names, "the pixel is on the model, and the part that answered is named"
        hidden = surface.submit(Command("view.pick", {"viewId": self._view(surface, dataset_id, {answered: False}), **pixel}))

        assert hidden.status is Status.ANSWERED, hidden.reason
        assert hidden.value.get("part") != answered, "a hidden part is not in the picture, so it cannot answer"

    def test_the_document_s_figure_shows_what_the_view_shows(self, tmp_path: Path) -> None:
        surface, _, dataset_id, names = self._two(tmp_path)

        def figure(view_id: str) -> bytes:
            report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
                "name": f"図 {view_id}", "targets": ["html"],
                "blocks": [{"kind": "view", "viewId": view_id, "form": "still"}],
            }})).value["id"]
            target = tmp_path / f"{view_id.replace(':', '-')}.html"
            result = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))
            assert result.status is Status.APPLIED, result.reason
            document = target.read_text(encoding="utf-8")
            start = document.index("data:image/png;base64,") + len("data:image/png;base64,")
            return base64.b64decode(document[start : document.index('"', start)])

        everything = figure(self._view(surface, dataset_id))
        without_one = figure(self._view(surface, dataset_id, {names[0]: False}))

        assert without_one != everything


@needs_offscreen
class TestPickingAPixel:
    """XC-257's "picks a point", from the thing an interface actually has. CT-003 2.3.0 adds
    `view.pick`: a view and a pixel in, the same answer `dataset.probe` gives out."""

    @staticmethod
    def _view(surface: Surface, dataset_id: str, field: str = "temperature", association: str = "point") -> str:
        return surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "全体図", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": field, "association": association, "colourMap": "viridis"},
        }})).value["id"]

    def test_a_pixel_on_the_model_answers_with_a_value_from_the_dataset(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": "K"}))
        view_id = self._view(surface, dataset_id)

        result = surface.submit(Command("view.pick", {"viewId": view_id, "width": 400, "height": 300, "x": 200, "y": 150}))

        assert result.status is Status.ANSWERED, result.reason
        value = result.value["value"]
        assert value["value"] in {float(one) for one in range(1, 9)}, "a value the cube actually holds"
        assert value["unit"] == "K"
        assert value["digits"] == 6
        assert value["provenance"] == "dataset"
        assert result.value["association"] == "point"

    def test_a_pixel_in_the_corner_is_off_the_model_and_says_so(self, tmp_path: Path) -> None:
        """view/AC-029: nothing there is reported as nothing, never as the nearest value there is."""
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = self._view(surface, dataset_id)

        result = surface.submit(Command("view.pick", {"viewId": view_id, "width": 400, "height": 300, "x": 2, "y": 2}))

        assert result.status is Status.ANSWERED, "a well-formed question about empty space is answered"
        assert result.value["value"]["value"] is None
        assert "モデル" in result.value["value"]["missingBecause"]

    def test_a_pixel_outside_the_frame_is_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = self._view(surface, dataset_id)

        result = surface.submit(Command("view.pick", {"viewId": view_id, "width": 400, "height": 300, "x": 400, "y": 10}))

        assert result.status is Status.REFUSED

    def test_two_pixels_far_apart_on_a_gradient_read_different_values(self, tmp_path: Path) -> None:
        """The pick lands where it is pointed. A pick that answered the same everywhere would pass
        every test above and be useless - this is the one that says the pixel matters."""
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = self._view(surface, dataset_id)
        size = {"viewId": view_id, "width": 600, "height": 450}

        found = {
            (x, y): surface.submit(Command("view.pick", {**size, "x": x, "y": y})).value["value"]["value"]
            for x, y in ((240, 300), (240, 170), (360, 300))
        }

        present = [one for one in found.values() if one is not None]
        assert len(present) >= 2, f"at least two pixels landed on the cube: {found}"
        assert len(set(present)) > 1, f"the pixel decides which value is read: {found}"

    def test_a_cell_field_is_picked_as_a_cell_s_value(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id, field="element_stress", association="cell")

        result = surface.submit(Command("view.pick", {"viewId": view_id, "width": 300, "height": 300, "x": 150, "y": 150}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["association"] == "cell"


@needs_offscreen
class TestADeliverableCarriesAStill:
    """Step 5 through the surface: a report whose view block asked for a still gets the picture, its
    legend as text, and the sentence that says it does not turn."""

    @staticmethod
    def _with_view(surface: Surface, dataset_id: str, form: str | None) -> tuple[str, str]:
        view = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "応力の全体図", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point", "colourMap": "viridis"},
        }})).value["id"]
        block: dict[str, object] = {"kind": "view", "viewId": view}
        if form is not None:
            block["form"] = form
        report = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "Run 1", "targets": ["html"],
            "blocks": [block, {"kind": "valueTable", "fields": ["stress"]}],
        }})).value["id"]
        return view, report

    def test_a_document_s_figure_keeps_its_bar_whatever_the_screen_asked(self, tmp_path: Path) -> None:
        """The screen renders with `legend: false` (E-192). The document must not inherit that: its
        figure is drawn by `report.export` with the default, and the bar is inside the picture."""
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "全体図", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "temperature", "association": "point", "colourMap": "viridis"},
        }})).value["id"]
        # The screen's render of the same view, without a bar.
        screen = surface.submit(Command("view.render", {
            "viewId": view_id, "width": 400, "height": 300, "format": "png", "legend": False,
        }))
        assert screen.status is Status.ANSWERED, screen.reason
        bare = session.handles.fetch(screen.value["handle"])
        report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "図つき", "targets": ["html"],
            "blocks": [{"kind": "view", "viewId": view_id, "form": "still"}],
        }})).value["id"]
        target = tmp_path / "with-figure.html"

        surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        document = target.read_text(encoding="utf-8")
        start = document.index("data:image/png;base64,") + len("data:image/png;base64,")
        embedded = base64.b64decode(document[start : document.index('"', start)])
        assert embedded != bare, "the document's figure is not the screen's bare frame"
        assert len(embedded) > len(bare) * 0.9, "and is a full picture of the same view, not a stub"

    def test_the_picture_its_legend_and_the_still_statement_are_in_the_file(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        _, report_id = self._with_view(surface, dataset_id, "still")
        target = tmp_path / "with-figure.html"

        result = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert result.status is Status.APPLIED, result.reason
        text = target.read_text(encoding="utf-8")
        assert "data:image/png;base64," in text
        assert "静止画です" in text
        assert "MPa" in text and "viridis" in text
        assert "40" in text, "the legend's upper end, from the full field"
        assert result.value["reductions"] == []
        assert not any("view" in one and "vtk.js" in one for one in result.value["omitted"])

    def test_a_view_that_asked_to_rotate_is_named_rather_than_given_a_photograph(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        _, report_id = self._with_view(surface, dataset_id, "interactive")
        target = tmp_path / "interactive.html"

        result = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert result.status is Status.APPLIED, result.reason
        assert any("vtk.js" in one for one in result.value["omitted"])
        assert "data:image/png;base64," not in target.read_text(encoding="utf-8")

    def test_a_view_block_with_no_form_is_named_rather_than_given_the_writable_one(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        _, report_id = self._with_view(surface, dataset_id, None)
        target = tmp_path / "formless.html"

        result = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert result.status is Status.APPLIED, result.reason
        assert any("どの形" in one for one in result.value["omitted"])


class TestWhenNoPictureCanBeDrawn:
    """E-194: with no display the toolkit does not refuse, it segfaults. The engine therefore asks a
    child process first, and a machine that cannot draw gets a refusal that names the requirement."""

    def test_view_render_refuses_before_drawing_when_the_probe_says_no(self, tmp_path: Path) -> None:
        session = Session(clock=at(9), issue=counting_issuer(), native_offscreen=lambda: (False, "テスト：ディスプレイ無し"))
        surface = build_surface(session)
        workspace = a_workspace(tmp_path)
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        source = tmp_path / "case.vtu"
        write_grid(source)
        dataset_id = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]})).value["datasetId"]
        view_id = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point"},
        }})).value["id"]

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 10, "height": 10, "format": "png"}))

        assert result.status is Status.REFUSED
        assert "ディスプレイ無し" in (result.reason or "")

    def test_capabilities_carry_the_same_answer_and_ask_only_once(self) -> None:
        asked = {"count": 0}

        def probe() -> tuple[bool, str]:
            asked["count"] += 1
            return False, "テスト：無し"

        session = Session(clock=at(9), issue=counting_issuer(), native_offscreen=probe)
        surface = build_surface(session)

        surface.submit(Command("system.capabilities", {}))
        result = surface.submit(Command("system.capabilities", {}))

        renderers = {one["backend"]: one for one in result.value["renderers"]}
        assert renderers["nativeOffscreen"]["available"] is False
        assert asked["count"] == 1, "a child process is not free; the answer is kept for the session"


@needs_offscreen
class TestRenderingAView:
    """Step 3 through the surface: a view definition names the dataset, the field and the map; the
    answer is a handle to PNG bytes and the sentence about reduction, which is what CT-003 states."""

    PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

    @staticmethod
    def _view(surface: Surface, dataset_id: str, **changes) -> str:
        definition = {
            "name": "応力の等高線",
            "datasetId": dataset_id,
            "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point", "colourMap": "viridis"},
        }
        definition.update(changes)
        created = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": definition}))
        assert created.status is Status.APPLIED, created.reason
        return created.value["id"]

    def test_a_view_renders_to_a_handle_whose_bytes_are_a_png(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id)

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 240, "height": 180, "format": "png"}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["reduced"] == "全三角形を表示しています"
        assert session.handles.fetch(result.value["handle"]).startswith(self.PNG_MAGIC)

    def test_a_camera_in_the_definition_is_used(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path)
        plain = self._view(surface, dataset_id)
        turned = self._view(surface, dataset_id, name="別の向き", camera={
            "position_m": [3.0, -3.0, 4.0], "focalPoint_m": [0.5, 0.5, 0.0], "viewUp": [0.0, 0.0, 1.0],
            "projection": "orthographic", "parallelScale_m": 1.2,
        })
        size = {"width": 160, "height": 120, "format": "png"}

        first = surface.submit(Command("view.render", {"viewId": plain, **size}))
        second = surface.submit(Command("view.render", {"viewId": turned, **size}))

        assert first.status is Status.ANSWERED and second.status is Status.ANSWERED
        assert session.handles.fetch(first.value["handle"]) != session.handles.fetch(second.value["handle"])

    def test_a_camera_given_to_the_render_is_used_and_the_definition_is_not_touched(self, tmp_path: Path) -> None:
        """XC-270: a camera move is drawn, not written. The same view drawn from a given camera is
        another picture; the definition's camera is as it was, and the history holds no write."""
        surface, session, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id)
        size = {"width": 160, "height": 120, "format": "png"}
        turned = {
            "position_m": [3.0, -3.0, 4.0], "focalPoint_m": [0.5, 0.5, 0.0], "viewUp": [0.0, 0.0, 1.0],
            "projection": "orthographic", "parallelScale_m": 1.2,
        }

        plain = surface.submit(Command("view.render", {"viewId": view_id, **size}))
        given = surface.submit(Command("view.render", {"viewId": view_id, **size, "camera": turned}))

        assert plain.status is Status.ANSWERED and given.status is Status.ANSWERED, given.reason
        assert session.handles.fetch(plain.value["handle"]) != session.handles.fetch(given.value["handle"])
        assert session.workspace is not None
        stored = items.find(session.workspace.raw, "views", view_id)["definition"]
        assert "camera" not in stored, "the definition's camera is what it was: absent"
        operations = [one.operation for one in surface.history()[-2:]]
        assert operations == ["view.render", "view.render"]
        picked = surface.submit(Command("view.pick", {"viewId": view_id, "width": 160, "height": 120, "x": 80, "y": 60, "camera": turned}))
        assert picked.status is Status.ANSWERED, picked.reason

    def test_a_format_this_build_cannot_write_is_refused_by_name(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id)

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 10, "height": 10, "format": "jpeg"}))

        assert result.status is Status.REFUSED
        assert "jpeg" in (result.reason or "")

    def test_a_view_that_does_not_exist_is_refused(self, tmp_path: Path) -> None:
        surface, _, _ = loaded(tmp_path)

        result = surface.submit(Command("view.render", {"viewId": "view:9999", "width": 10, "height": 10, "format": "png"}))

        assert result.status is Status.REFUSED

    def test_a_view_without_colouring_is_refused_rather_than_drawn_grey(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id, colouring=None)

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 10, "height": 10, "format": "png"}))

        assert result.status is Status.REFUSED
        assert "colouring" in (result.reason or "")

    def test_a_representation_this_build_cannot_draw_is_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id, representation="wireframe")

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 10, "height": 10, "format": "png"}))

        assert result.status is Status.REFUSED
        assert "wireframe" in (result.reason or "")

    def test_a_renderer_refusal_reaches_the_caller_as_a_refusal(self, tmp_path: Path) -> None:
        """The map name is wrong: the caller's mistake, said so, not a failure of the build."""
        surface, _, dataset_id = loaded(tmp_path)
        view_id = self._view(surface, dataset_id, colouring={"fieldName": "stress", "association": "point", "colourMap": "jet"})

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 10, "height": 10, "format": "png"}))

        assert result.status is Status.REFUSED
        assert "jet" in (result.reason or "")


class TestWhatWasSavedIsIntact:
    """XC-259's sentence, made true: a declaration saved into the document is found by the next
    session; one never saved is not, and nothing pretends otherwise (#306, CT-001 `declaredUnits`)."""

    @staticmethod
    def _second_session(tmp_path: Path, workspace: Path, source: Path) -> tuple[Surface, dict]:
        surface, _ = a_surface()
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        assert loaded.status is Status.APPLIED, loaded.reason
        return surface, loaded.value

    def test_a_declaration_saved_is_the_declaration_the_next_session_finds(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        assert surface.submit(Command("field.declareUnit", {
            "datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": "K",
        })).status is Status.APPLIED

        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))

        assert saved.status is Status.APPLIED, saved.reason
        assert saved.value["path"] == str(workspace)
        written = json.loads(workspace.read_text(encoding="utf-8"))
        entry = written["cases"][0]["sources"][0]
        assert entry["declaredUnits"] == {"temperature": "K"}
        assert entry["pathRelative"] == "cube.vtu"
        _, reloaded = self._second_session(tmp_path, workspace, workspace.parent / "cube.vtu")
        assert reloaded["fields"] == [{"name": "temperature", "association": "point", "unit": "K", "components": 1, "missingCount": 0}]

    def test_a_declaration_never_saved_is_not_found_and_the_field_is_undeclared_again(self, tmp_path: Path) -> None:
        """The other half of the sentence. Nothing rebuilds it: the next session sees what the file
        carries, which is no unit (XC-003)."""
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        assert surface.submit(Command("field.declareUnit", {
            "datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": "K",
        })).status is Status.APPLIED

        _, reloaded = self._second_session(tmp_path, workspace, workspace.parent / "cube.vtu")

        assert reloaded["fields"] == [{"name": "temperature", "association": "point", "unit": None, "components": 1, "missingCount": 0}]

    def test_saving_keeps_the_previous_version_beside_the_file(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        before = workspace.read_bytes()

        first = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        assert first.status is Status.APPLIED, first.reason

        previous = workspace.with_name(workspace.name + ".previous")
        assert previous.exists() and previous.read_bytes() == before, "the version before the save is beside it"
        assert first.value["previousKept"] == str(previous)

    def test_saving_a_workspace_that_is_not_open_is_refused(self, tmp_path: Path) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))

        assert result.status is Status.REFUSED

    def test_undoing_a_save_puts_the_previous_file_back(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        before = workspace.read_bytes()
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": "K"}))
        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        assert saved.status is Status.APPLIED and workspace.read_bytes() != before

        undone = surface.undo(saved.undo_id or "")

        assert undone.status is Status.APPLIED, undone.reason
        assert workspace.read_bytes() == before


class TestOpeningSaysWhatTheDocumentHolds:
    def test_a_saved_view_is_named_by_the_next_open_so_it_can_be_updated_not_recreated(self, tmp_path: Path) -> None:
        """CT-003 2.6.0. The recovery path created its view again under the same name and was refused,
        correctly (AC-030); the next open now says what is there."""
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        created = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "temperature", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "temperature", "association": "point", "colourMap": "viridis"},
        }}))
        assert created.status is Status.APPLIED, created.reason
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED

        again, _ = a_surface()
        opened = again.submit(Command("workspace.open", {"path": str(workspace)}))

        assert opened.status is Status.APPLIED, opened.reason
        assert opened.value["items"]["views"] == [
            {"id": created.value["id"], "name": "temperature", "datasetId": dataset_id},
        ]
        assert opened.value["items"]["reports"] == []


class TestAFileIsInspectedBeforeItIsRead:
    def test_the_support_level_and_the_gaps_are_stated_without_opening_the_file(self, tmp_path: Path) -> None:
        """ingest/AC-032 before anything loads: the level is a promise about a format, made from the
        extension, and the reader's gaps come with it (AC-034)."""
        surface, _ = a_surface()
        source = tmp_path / "case.vtu"
        write_cube(source)

        result = surface.submit(Command("dataset.inspect", {"path": str(source)}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["format"] == "vtu"
        assert result.value["supportLevel"] in {"Verified", "Limited", "Offered"}
        assert result.value["exists"] is True
        assert result.value["sizeBytes"] == source.stat().st_size

    def test_a_format_this_build_does_not_read_is_named_as_absent(self, tmp_path: Path) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("dataset.inspect", {"path": str(tmp_path / "thing.unknownformat")}))

        assert result.status is Status.ANSWERED
        assert result.value["supportLevel"] == "Absent"
        assert result.value["exists"] is False


class TestNothingHalfWrittenIsLeftBehind:
    """#313, XC-262: a save that did not finish is removed and said on the next open; a deliverable
    is written beside its target and moved into place, so it is whole or absent."""

    def test_an_interrupted_save_is_removed_on_open_and_said(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        workspace = a_workspace(tmp_path)
        interrupted = workspace.with_name(workspace.name + ".writing")
        interrupted.write_text("{ this save never finished", encoding="utf-8")

        result = surface.submit(Command("workspace.open", {"path": str(workspace)}))

        assert result.status is Status.APPLIED, result.reason
        assert not interrupted.exists()
        assert any("途中で終わって" in one for one in result.warnings)

    def test_an_export_leaves_no_writing_file_beside_the_deliverable(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "whole", "targets": ["html"], "blocks": [{"kind": "valueTable", "fields": ["temperature"]}],
        }})).value["id"]
        target = tmp_path / "whole.html"

        exported = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))

        assert exported.status is Status.APPLIED, exported.reason
        assert target.exists() and target.stat().st_size == exported.value["bytes"]
        assert not target.with_name(target.name + ".writing").exists()


class TestEveryCommandReachesTheDiagnosticLog:
    def test_a_refusal_is_a_warning_line_with_the_operation_and_the_reason(self, tmp_path: Path) -> None:
        """XC-263: the surface hands every entry to the session's log, so the file and history.list
        cannot tell different stories. A refusal is a warning; a read that answered is info."""
        from service.egress.diagnostics import Level, Log

        session = Session(log=Log(directory=tmp_path / "logs"))
        surface = build_surface(session)

        surface.submit(Command("system.protocols", {}))
        surface.submit(Command("dataset.describe", {"datasetId": "dataset:none"}))

        lines = session.log.lines()
        assert [one.level for one in lines] == [Level.INFO, Level.WARNING]
        assert lines[1].context["operation"] == "dataset.describe"
        assert lines[1].context["status"] == "refused"
        assert lines[1].context["reason"]
        written = (tmp_path / "logs" / "solvia.log").read_text(encoding="utf-8").splitlines()
        assert len(written) == 2 and json.loads(written[1])["status"] == "refused"

    def test_capabilities_say_where_the_log_is(self, tmp_path: Path) -> None:
        from service.egress.diagnostics import Log

        session = Session(log=Log(directory=tmp_path / "logs"))
        surface = build_surface(session)

        result = surface.submit(Command("system.capabilities", {}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["diagnostics"]["logDirectory"] == str(tmp_path / "logs")
        assert result.value["diagnostics"]["level"] == "info"


class TestUndoHoldsNothingItCanReread:
    """XC-264: the undo of workspace.open no longer keeps the previous workspace's datasets, and says
    so; the undo of workspace.save puts the previous file back from disk."""

    def test_opening_another_workspace_warns_that_the_datasets_will_need_reading_again(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        other = tmp_path / "other"
        other.mkdir()
        second = a_workspace(other)

        opened = surface.submit(Command("workspace.open", {"path": str(second)}))

        assert opened.status is Status.APPLIED, opened.reason
        assert any("読み直し" in one for one in opened.warnings)
        assert session.datasets == {}
        undone = surface.undo(opened.undo_id or "")
        assert undone.status is Status.APPLIED
        assert session.workspace is not None and session.workspace_path == tmp_path / "beam.svw"
        assert session.datasets == {}, "the previous datasets are not held by the undo"

    def test_undoing_a_save_restores_the_previous_file_from_disk(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        original = workspace.read_bytes()
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": "K"}))
        second = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        assert second.status is Status.APPLIED and workspace.read_bytes() != original

        undone = surface.undo(second.undo_id or "")

        assert undone.status is Status.APPLIED, undone.reason
        assert json.loads(workspace.read_text(encoding="utf-8"))["cases"][0]["sources"][0].get("declaredUnits", {}) == {}
        previous = workspace.with_name(workspace.name + ".previous")
        assert previous.exists() and previous.read_bytes() == original

    def test_history_list_says_what_is_undoable_and_what_the_cap_took(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        declared = surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": "K"}))

        listed = surface.submit(Command("history.list", {"workspaceId": "ws:1"}))

        assert listed.status is Status.ANSWERED, listed.reason
        assert listed.value["undoDropped"] == 0 and listed.value["omitted"] == 0
        # The answer is what was recorded before this read; the read itself is recorded after.
        last = listed.value["entries"][-1]
        assert last["operation"] == "field.declareUnit" and last["undoId"] == declared.undo_id and last["undoable"] is True
        assert all(one["undoable"] is False for one in listed.value["entries"] if one["operation"] == "dataset.describe")

class TestAWorkspaceIsBoundedInItems:
    """LIM-016 (XC-265): a document past the ceiling opens whole and says so, saves, and refuses to
    take one more item by the limit's name. Nothing it holds is dropped for the sake of a number."""

    def test_a_document_past_the_limit_opens_whole_says_so_and_takes_no_more(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        path = a_workspace(tmp_path)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["workspaceItems"]["views"] = [
            {"id": f"view:{n:05d}", "name": f"v{n}", "definition": {}} for n in range(MAX_WORKSPACE_ITEMS + 1)
        ]
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

        result = surface.submit(Command("workspace.open", {"path": str(path)}))

        assert result.status is Status.APPLIED, result.reason
        assert any("LIM-016" in one and f"{MAX_WORKSPACE_ITEMS + 1:,} 件" in one for one in result.warnings)
        assert session.workspace is not None
        assert len(session.workspace.raw["workspaceItems"]["views"]) == MAX_WORKSPACE_ITEMS + 1
        assert len(result.value["items"]["views"]) == MAX_WORKSPACE_ITEMS + 1

        created = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {"name": "もう一つ"}}))
        assert created.status is Status.REFUSED
        assert "LIM-016" in (created.reason or "")

        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        assert saved.status is Status.APPLIED, saved.reason
        assert len(json.loads(path.read_text(encoding="utf-8"))["workspaceItems"]["views"]) == MAX_WORKSPACE_ITEMS + 1

    def test_a_document_under_the_limit_opens_without_a_word_about_it(self, tmp_path: Path) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("workspace.open", {"path": str(a_workspace(tmp_path))}))

        assert result.status is Status.APPLIED, result.reason
        assert not any("LIM-016" in one for one in result.warnings)

class TestNothingHasLeftAndItSaysSo:
    """#317 (XC-267): a person checks the fact, not the sentence. What may leave and whether anything
    can is in `system.capabilities`; what did leave is in `system.audit`; both are the engine's own
    answers, from the gate that would have had to do the sending."""

    HOST = "search.example.test"

    def test_the_capabilities_say_no_way_out_nothing_permitted_and_an_empty_audit(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        result = surface.submit(Command("system.capabilities", {}))

        assert result.status is Status.ANSWERED, result.reason
        egress = result.value["egress"]
        assert egress["transportConfigured"] is False, "this build injects no transport: nothing can leave"
        assert egress["workspaceId"] == "ws:1"
        assert (egress["search"], egress["languageModel"], egress["updateCheck"]) == (False, False, False)
        assert egress["hosts"] == [] and egress["withoutAsking"] is False and egress["workspaceContent"] is False
        assert egress["auditEntries"] == 0 and egress["sentEntries"] == 0

    def test_the_audit_is_empty_as_a_record_and_not_as_a_sentence(self) -> None:
        surface, _ = a_surface()

        result = surface.submit(Command("system.audit", {}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value == {"entries": []}

    def test_a_refused_request_is_in_the_audit_with_its_host_content_and_time(self) -> None:
        surface, session = a_surface()
        session.gate.permit("ws:1", EgressPermission(search=True, hosts=frozenset({self.HOST}), without_asking=True))
        attempted = session.gate.search(SearchRequest("疲労限度", self.HOST), workspace_id="ws:1", confirmed=True)
        assert attempted.outcome is Outcome.REFUSED, "no transport: refused, never pretended"

        result = surface.submit(Command("system.audit", {}))

        assert result.status is Status.ANSWERED, result.reason
        [entry] = result.value["entries"]
        assert entry["host"] == self.HOST and entry["purpose"] == "webSearch" and entry["outcome"] == "refused"
        assert entry["at"] == record_time(at(9)()).as_stored()
        assert "送信経路" in entry["reason"]
        egress = surface.submit(Command("system.capabilities", {})).value["egress"]
        assert egress["auditEntries"] == 1 and egress["sentEntries"] == 0

    def test_since_narrows_the_record_and_a_folded_offset_is_refused(self) -> None:
        surface, session = a_surface()
        session.gate.permit("ws:1", EgressPermission(search=True, hosts=frozenset({self.HOST}), without_asking=True))
        session.gate.search(SearchRequest("一", self.HOST), workspace_id="ws:1", confirmed=True)
        moment = record_time(at(9)()).utc

        assert len(surface.submit(Command("system.audit", {"since": moment})).value["entries"]) == 1
        later = (record_time(at(9)()).instant + timedelta(seconds=1)).strftime(STORED_FORMAT)
        assert surface.submit(Command("system.audit", {"since": later})).value["entries"] == []
        refused_ = surface.submit(Command("system.audit", {"since": "2026-09-18T09:00:00+09:00"}))
        assert refused_.status is Status.REFUSED and "UTC" in (refused_.reason or "")

class TestOutputIsListedPlannedAndPrunedByName:
    """XC-141's three refusals, across the wire (#314, XC-268): what pruning would delete is shown as a
    plan, the act names the files it expects and needs the caller's say-so, and a folder that changed
    in between - or a run holding an input - is refused with nothing deleted."""

    OLD = "report-a/2026-09-01T00-00-00"
    NEW = "report-a/2026-09-02T00-00-00"

    def runs(self, tmp_path: Path) -> Path:
        root = tmp_path / "output"
        old = root / self.OLD
        (old / "case-1").mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({
            "pipelineId": "pipeline:1", "started": {"utc": "2026-09-01T00:00:00Z", "offsetMinutes": 540},
            "cases": [], "outcomes": [],
        }), encoding="utf-8")
        (old / "case-1" / "figure.png").write_bytes(b"x" * 300)
        (old / "case-1" / "table.csv").write_bytes(b"y" * 200)
        new = root / self.NEW
        new.mkdir(parents=True)
        (new / "figure.png").write_bytes(b"z" * 100)
        return root

    def test_the_runs_are_listed_with_their_sizes_and_where_their_times_came_from(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)
        self.runs(tmp_path)

        result = surface.submit(Command("output.list", {"workspaceId": "ws:1"}))

        assert result.status is Status.ANSWERED, result.reason
        runs = {one["id"]: one for one in result.value["runs"]}
        assert set(runs) == {self.OLD, self.NEW}
        assert runs[self.OLD]["started"] == {"utc": "2026-09-01T00:00:00Z", "offsetMinutes": 540}
        assert runs[self.OLD]["startedFrom"] == "record" and runs[self.OLD]["hasRecord"] is True
        assert runs[self.OLD]["artefactFiles"] == 2 and runs[self.OLD]["artefactBytes"] == 500
        assert runs[self.NEW]["startedFrom"] == "folder" and runs[self.NEW]["hasRecord"] is False
        assert runs[self.NEW]["started"]["offsetMinutes"] == 540, "the folder's time carries this session's offset"
        assert result.value["totalBytes"] == 600 and result.value["overLimit"] is False
        assert result.value["suggestedRunIds"] == [], "under the limit nothing is suggested"

    def test_the_plan_names_every_file_and_the_record_it_keeps(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)
        self.runs(tmp_path)

        result = surface.submit(Command("output.plan", {"workspaceId": "ws:1", "runsToRemove": [self.OLD]}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["files"] == [f"{self.OLD}/case-1/figure.png", f"{self.OLD}/case-1/table.csv"]
        assert result.value["freedBytes"] == 500
        assert result.value["keptRecords"] == [f"{self.OLD}/run.json"]

    def test_pruning_needs_authorisation_and_deletes_exactly_the_plan(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)
        root = self.runs(tmp_path)
        chosen = {"workspaceId": "ws:1", "runsToRemove": [self.OLD]}
        plan = surface.submit(Command("output.plan", chosen)).value

        unauthorised = surface.submit(Command("output.prune", {**chosen, "expectedFiles": plan["files"]}))
        assert unauthorised.status is Status.REFUSED and "allowDestructive" in (unauthorised.reason or "")
        assert (root / self.OLD / "case-1" / "figure.png").exists(), "a refusal changes nothing"

        pruned = surface.submit(Command(
            "output.prune", {**chosen, "expectedFiles": plan["files"]}, allowed=frozenset({Permission.DESTRUCTIVE}),
        ))

        assert pruned.status is Status.APPLIED, pruned.reason
        assert pruned.value == {"removedRunIds": [self.OLD], "freedBytes": 500, "deletedFiles": plan["files"]}
        assert not (root / self.OLD / "case-1" / "figure.png").exists()
        assert (root / self.OLD / "run.json").exists(), "the record survives its artefacts (XC-046)"
        assert (root / self.NEW / "figure.png").exists(), "a run not chosen is not touched"
        assert pruned.undo_id is None, "a deleted artefact is regenerated from its record, not undone"
        assert any("取り消せません" in one for one in pruned.warnings)
        listed = surface.submit(Command("history.list", {"workspaceId": "ws:1"})).value["entries"]
        entry = next(one for one in reversed(listed) if one["operation"] == "output.prune")
        assert "undoId" not in entry and entry["undoable"] is False

    def test_a_folder_that_changed_since_the_plan_is_refused_and_nothing_goes(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)
        root = self.runs(tmp_path)
        chosen = {"workspaceId": "ws:1", "runsToRemove": [self.OLD]}
        plan = surface.submit(Command("output.plan", chosen)).value
        (root / self.OLD / "case-1" / "just-exported.png").write_bytes(b"n")

        pruned = surface.submit(Command(
            "output.prune", {**chosen, "expectedFiles": plan["files"]}, allowed=frozenset({Permission.DESTRUCTIVE}),
        ))

        assert pruned.status is Status.REFUSED and "変わって" in (pruned.reason or "")
        assert (root / self.OLD / "case-1" / "figure.png").exists()
        assert (root / self.OLD / "case-1" / "just-exported.png").exists()

    def test_an_unknown_run_and_a_run_holding_an_input_are_refused(self, tmp_path: Path) -> None:
        surface, session, _ = opened(tmp_path)
        self.runs(tmp_path)

        unknown = surface.submit(Command("output.plan", {"workspaceId": "ws:1", "runsToRemove": ["report-a/nope"]}))
        assert unknown.status is Status.REFUSED and "report-a/nope" in (unknown.reason or "")

        # A file a case records as a source is input data, whatever folder it sits in.
        assert session.workspace is not None
        session.workspace.raw["cases"][0]["sources"] = [{
            "pathRelative": f"output/{self.OLD}/case-1/table.csv", "sizeBytes": 200,
            "modified": {"utc": "2026-09-01T00:00:00Z", "offsetMinutes": 540},
        }]
        guarded = surface.submit(Command("output.plan", {"workspaceId": "ws:1", "runsToRemove": [self.OLD]}))
        assert guarded.status is Status.REFUSED
        assert "入力" in (guarded.reason or "") and "table.csv" in (guarded.reason or "")

class TestASecondOpenIsReadOnlyThroughTheAPI:
    """XC-241 through the API (#262, XC-269): the open takes the lock; held by somebody else, the
    document opens read-only and says who; the window works in memory; saving and pruning are refused;
    a stale lock is taken over only on the caller's word, and a live holder's never."""

    def held_elsewhere(self, path: Path) -> None:
        # Another host is never examined for liveness, so this lock counts as held whatever the pid.
        (path.parent / (path.name + ".lock")).write_text(json.dumps({
            "processId": 4321, "host": "pc9", "user": "hanako",
            "takenAt": {"utc": "2026-09-18T00:00:00Z", "offsetMinutes": 540},
        }), encoding="utf-8")

    def test_opening_takes_the_lock_and_says_so(self, tmp_path: Path) -> None:
        surface, session, path = opened(tmp_path)

        assert (path.parent / "beam.svw.lock").exists()
        assert session.read_only is False and session.lock is not None and session.lock.holder is not None
        assert session.lock.holder.process_id == os.getpid()
        result = surface.submit(Command("workspace.open", {"path": str(path)}))
        assert result.status is Status.APPLIED, result.reason
        assert result.value["readOnly"] is False and result.value["lock"]["state"] == "free"
        assert result.value["lock"]["holder"]["processId"] == os.getpid()
        assert result.value["lock"]["lockFile"].endswith("beam.svw.lock")

    def test_held_by_somebody_else_it_opens_read_only_and_names_the_holder(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        path = a_workspace(tmp_path)
        self.held_elsewhere(path)

        result = surface.submit(Command("workspace.open", {"path": str(path)}))

        assert result.status is Status.APPLIED, result.reason
        assert result.value["readOnly"] is True and result.value["lock"]["state"] == "held"
        assert result.value["lock"]["holder"]["user"] == "hanako"
        assert any("読み取り専用" in one and "hanako" in one for one in result.warnings)
        # The window works in memory: a view is created, because the failure is the second save.
        created = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {"name": "応力"}}))
        assert created.status is Status.APPLIED, created.reason
        # Writing the document back is what is refused, and it names the holder.
        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        assert saved.status is Status.REFUSED and "hanako" in (saved.reason or "") and "読み取り専用" in (saved.reason or "")
        pruned = surface.submit(Command(
            "output.prune", {"workspaceId": "ws:1", "runsToRemove": ["x/y"]}, allowed=frozenset({Permission.DESTRUCTIVE}),
        ))
        assert pruned.status is Status.REFUSED and "読み取り専用" in (pruned.reason or "")
        # The other window's lock is exactly where it was.
        assert json.loads((path.parent / "beam.svw.lock").read_text(encoding="utf-8"))["user"] == "hanako"

    def test_a_stale_lock_is_reported_and_taken_over_only_on_the_callers_word(self, tmp_path: Path) -> None:
        surface, session = a_surface()
        path = a_workspace(tmp_path)
        (path.parent / "beam.svw.lock").write_text(json.dumps({
            "processId": 999999, "host": session.host, "user": "taro",
            "takenAt": {"utc": "2026-09-18T00:00:00Z", "offsetMinutes": 540},
        }), encoding="utf-8")

        stale = surface.submit(Command("workspace.open", {"path": str(path)}))
        assert stale.status is Status.APPLIED, stale.reason
        assert stale.value["readOnly"] is True and stale.value["lock"]["state"] == "stale"
        assert any("自動では解除しません" in one for one in stale.warnings)
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.REFUSED

        taken = surface.submit(Command("workspace.open", {"path": str(path), "takeOverStaleLock": True}))

        assert taken.status is Status.APPLIED, taken.reason
        assert taken.value["readOnly"] is False and taken.value["lock"]["holder"]["processId"] == os.getpid()
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED

    def test_a_live_holder_is_never_taken_over_whatever_the_caller_says(self, tmp_path: Path) -> None:
        surface, _ = a_surface()
        path = a_workspace(tmp_path)
        self.held_elsewhere(path)

        result = surface.submit(Command("workspace.open", {"path": str(path), "takeOverStaleLock": True}))

        assert result.status is Status.APPLIED, result.reason
        assert result.value["readOnly"] is True and result.value["lock"]["holder"]["user"] == "hanako"
        assert any("引き継ぎませんでした" in one for one in result.warnings)

    def test_opening_another_document_releases_the_first_and_stopping_releases_the_last(self, tmp_path: Path) -> None:
        surface, session, first = opened(tmp_path)
        second = tmp_path / "other.svw"
        second.write_text(first.read_text(encoding="utf-8").replace("ws:1", "ws:2"), encoding="utf-8")

        result = surface.submit(Command("workspace.open", {"path": str(second)}))

        assert result.status is Status.APPLIED, result.reason
        assert not (tmp_path / "beam.svw.lock").exists(), "the first document's lock went with it"
        assert (tmp_path / "other.svw.lock").exists()
        session.release_workspace()
        assert not (tmp_path / "other.svw.lock").exists()
        assert session.lock is None


class TestTheResultPosition:
    """XC-283, view/AC-031 to AC-033: the numbers, the picture and the probe are of the step asked
    for, every answer says which step it is of, and a step the case lacks is refused by name."""

    @staticmethod
    def _transient(tmp_path: Path) -> tuple[Surface, Session, str]:
        requires_h5py()
        from cgns_fixture import write_transient_cgns

        return loaded(tmp_path, write=write_transient_cgns, name="t.cgns")

    @staticmethod
    def _view(surface: Surface, dataset_id: str, position: dict) -> str:
        return surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "遷移", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point", "colourMap": "viridis"},
            "resultPosition": position,
        }})).value["id"]

    def test_statistics_are_of_the_step_asked_for_and_say_which(self, tmp_path: Path) -> None:
        surface, _, dataset_id = self._transient(tmp_path)

        first = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))
        second = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "resultPosition": 1}))

        assert first.status is Status.ANSWERED and second.status is Status.ANSWERED, (first.reason, second.reason)
        assert first.value["maximum"]["value"] == 90.0 and second.value["maximum"]["value"] == 91.0
        assert first.value["resultPosition"] == {
            "step": 0, "count": 2, "kind": "undeclared", "value": 0.0, "unit": None,
            "stated": "ステップ 1/2（位置 0・軸の種類は宣言なし）",
        }
        assert second.value["resultPosition"]["stated"] == "ステップ 2/2（位置 0.5・軸の種類は宣言なし）"
        assert second.value["scope"] == "ケース全体（1 パート）・ステップ 2/2（位置 0.5・軸の種類は宣言なし）"

    def test_a_steady_case_says_it_has_one_step_and_no_axis(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        assert result.value["resultPosition"] == {
            "step": 0, "count": 1, "kind": "none", "value": None, "unit": None, "stated": "定常（結果軸なし・ステップ 1/1）",
        }
        assert "ステップ" not in result.value["scope"]

    def test_a_step_the_case_lacks_is_refused_and_nothing_nearer_is_answered(self, tmp_path: Path) -> None:
        surface, _, dataset_id = self._transient(tmp_path)

        statistics = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "resultPosition": 2}))
        probe = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "stress", "pointM": [0.0, 1.0, 0.0], "resultPosition": 5,
        }))

        assert statistics.status is Status.REFUSED and "ステップ番号 2" in (statistics.reason or "")
        assert "0〜1" in (statistics.reason or "") and "代用はしません" in (statistics.reason or "")
        assert probe.status is Status.REFUSED and "ステップ番号 5" in (probe.reason or "")

    def test_the_probe_reads_the_step_asked_for(self, tmp_path: Path) -> None:
        surface, _, dataset_id = self._transient(tmp_path)
        point = {"datasetId": dataset_id, "fieldName": "stress", "pointM": [0.0, 1.0, 0.0]}

        at_first = surface.submit(Command("dataset.probe", {**point, "resultPosition": 0}))
        at_second = surface.submit(Command("dataset.probe", {**point, "resultPosition": 1}))

        assert at_first.status is Status.ANSWERED and at_second.status is Status.ANSWERED, (at_first.reason, at_second.reason)
        assert at_first.value["value"]["value"] == 90.0 and at_second.value["value"]["value"] == 91.0
        assert at_second.value["resultPosition"]["step"] == 1

    def test_a_declared_unit_reaches_every_step(self, tmp_path: Path) -> None:
        surface, _, dataset_id = self._transient(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))

        second = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "resultPosition": 1}))

        assert second.status is Status.ANSWERED, second.reason
        assert second.value["maximum"]["unit"] == "MPa"

    def test_a_derivation_is_made_again_on_a_step_read_later(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A derived field is a rule of the dataset, not a column of its first step (XC-282, XC-283).
        The transient fixture carries one scalar, so a vector is put on each step as it is read."""
        import math

        import numpy as np
        from domain_core.association import Association
        from domain_core.dataset import Field
        from engine import reader as reader_module

        surface, session, dataset_id = self._transient(tmp_path)

        def vector(offset: float) -> Field:
            values = np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 0.0], [1.0, 2.0, 2.0], [2.0, 3.0, 6.0]], dtype=np.float32)
            return Field("displacement", Association.POINT, values + np.float32(offset))

        session.datasets[dataset_id].case.present[0].dataset.fields["displacement"] = vector(0.0)
        real = reader_module.read_case

        def read_with_vector(path, *, step=0, expected=None):
            case = real(path, step=step, expected=expected)
            case.present[0].dataset.fields["displacement"] = vector(float(step))
            return case

        monkeypatch.setattr(reader_module, "read_case", read_with_vector)
        made = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "magnitude"}))
        assert made.status is Status.ANSWERED, made.reason

        at_first = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "displacement.magnitude"}))
        at_second = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "displacement.magnitude", "resultPosition": 1}))

        assert at_first.status is Status.ANSWERED and at_second.status is Status.ANSWERED, (at_first.reason, at_second.reason)
        assert at_first.value["maximum"]["value"] == pytest.approx(7.0)
        assert at_second.value["maximum"]["value"] == pytest.approx(math.sqrt(9.0 + 16.0 + 49.0))

    def test_a_member_that_names_the_kind_is_refused_on_an_undeclared_axis(self, tmp_path: Path) -> None:
        """XC-240: calling the second of "0, 0.5" a time step labels a value the file did not label."""
        surface, _, dataset_id = self._transient(tmp_path)
        view_id = self._view(surface, dataset_id, {"timeStep": 1})

        drawn = surface.submit(Command("view.render", {"viewId": view_id, "width": 300, "height": 300, "format": "png"}))

        assert drawn.status is Status.REFUSED
        assert "timeStep" in (drawn.reason or "") and "宣言なし" in (drawn.reason or "") and "step" in (drawn.reason or "")

    @needs_offscreen
    def test_the_picture_and_the_pick_are_of_the_view_s_step(self, tmp_path: Path) -> None:
        surface, _, dataset_id = self._transient(tmp_path)
        view_id = self._view(surface, dataset_id, {"step": 1})

        drawn = surface.submit(Command("view.render", {"viewId": view_id, "width": 300, "height": 300, "format": "png"}))
        picked = surface.submit(Command("view.pick", {"viewId": view_id, "width": 300, "height": 300, "x": 150, "y": 150}))

        assert drawn.status is Status.ANSWERED, drawn.reason
        assert drawn.value["resultPosition"]["step"] == 1
        assert picked.status is Status.ANSWERED, picked.reason
        assert picked.value["resultPosition"]["stated"] == "ステップ 2/2（位置 0.5・軸の種類は宣言なし）"
        assert picked.value["value"]["value"] in {11.0, 21.0, 91.0, 41.0}, "a value the second step holds"

    def test_the_report_s_table_is_of_the_view_s_step_and_each_row_says_so(self, tmp_path: Path) -> None:
        from service.command.handlers import rows_for_report

        surface, session, dataset_id = self._transient(tmp_path)
        view_id = self._view(surface, dataset_id, {"step": 1})

        rows, _ = rows_for_report(session, {"blocks": [
            {"kind": "valueTable", "fields": ["stress"], "viewId": view_id},
            {"kind": "valueTable", "fields": ["stress"]},
        ]})

        assert rows[view_id][0].label == "stress の最大・ステップ 2/2（位置 0.5・軸の種類は宣言なし）"
        assert rows[view_id][0].value.value == 91.0
        assert rows["1"][0].label == "stress の最大・ステップ 1/2（位置 0・軸の種類は宣言なし）"
        assert rows["1"][0].value.value == 90.0


class TestAFileThatIsNotAllThere:
    """ingest/AC-022, AC-046, XC-284 (#263): a file cut short, or one that changes under the product,
    is refused with the reason - a refusal, since the file is the problem - and never a dataset."""

    def test_an_exodus_file_the_reader_would_zero_fill_is_refused_with_both_lengths(self, tmp_path: Path) -> None:
        surface, _, workspace = opened(tmp_path)
        write_exodus(workspace.parent / "whole.ex2")
        body = (workspace.parent / "whole.ex2").read_bytes()
        cut = workspace.parent / "cut.ex2"
        cut.write_bytes(body[: int(len(body) * 0.95)])

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(cut)]}))

        assert result.status is Status.REFUSED, result.status
        assert f"{len(body)} バイト" in (result.reason or "") and "cut.ex2" in (result.reason or "")

    def test_a_file_whose_results_the_reader_dropped_is_refused_not_failed(self, tmp_path: Path) -> None:
        """A 50 per cent cut leaves the header naming results the reader cannot find: that is the
        file's problem, so it is refused with the reason rather than reported as this build's failure."""
        surface, _, workspace = opened(tmp_path)
        write_exodus(workspace.parent / "whole.ex2")
        body = (workspace.parent / "whole.ex2").read_bytes()
        cut = workspace.parent / "half.ex2"
        cut.write_bytes(body[: len(body) // 2])

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(cut)]}))

        assert result.status is Status.REFUSED, result.status
        assert result.reason

    def test_another_step_is_not_read_from_a_file_that_changed_since_the_load(self, tmp_path: Path) -> None:
        requires_h5py()
        from cgns_fixture import write_transient_cgns

        surface, session, dataset_id = loaded(tmp_path, write=write_transient_cgns, name="t.cgns")
        path = session.datasets[dataset_id].path
        with open(path, "ab") as handle:
            handle.write(b"\0" * 16)

        first = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))
        second = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "resultPosition": 1}))

        assert first.status is Status.ANSWERED, "what was read stays what it was"
        assert first.value["maximum"]["value"] == 90.0
        assert second.status is Status.REFUSED
        assert "読み込んだあとに変わりました" in (second.reason or "") and "t.cgns" in (second.reason or "")


class TestTheLogArea:
    """XC-286 (#292): the three kinds - what was refused or warned, what ran, what left the machine -
    are one log, read back by `system.log`, from the files where there are files."""

    def test_a_refusal_and_a_warning_are_read_back_with_where_they_came_from(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path)
        surface.submit(Command("dataset.describe", {"datasetId": "dataset:none"}))
        surface.submit(Command("workspace.open", {"path": str(session.workspace_path)}))  # a lock this process holds: a warning

        result = surface.submit(Command("system.log", {}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["source"] == "memory" and result.value["logDirectory"] is None
        events = [(one["event"], one["level"]) for one in result.value["entries"]]
        assert ("command", "warning") in events, events
        refused = next(one for one in result.value["entries"] if one["event"] == "command" and one["context"].get("status") == "refused")
        assert refused["context"]["operation"] == "dataset.describe" and refused["context"]["reason"]
        assert all(one["level"] in ("warning", "error") for one in result.value["entries"]), "warning is the default level"
        assert result.value["omitted"] == 0 and result.value["unreadable"] == 0

    def test_the_answers_warnings_reach_the_log_as_their_own_lines(self, tmp_path: Path) -> None:
        requires_h5py()
        from demo_case import write_partial_case

        surface, _, workspace = opened(tmp_path)
        partial = write_partial_case(workspace.parent)
        assert partial is not None
        loaded_result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(partial)]}))
        assert loaded_result.status is Status.APPLIED and loaded_result.warnings

        entries = surface.submit(Command("system.log", {"level": "warning"})).value["entries"]

        warned = [one for one in entries if one["event"] == "warning"]
        assert warned and warned[0]["context"]["operation"] == "dataset.load"
        assert "不完全" in warned[0]["context"]["text"]

    def test_an_egress_decision_is_a_log_line_without_the_content(self, tmp_path: Path) -> None:
        surface, session, _ = opened(tmp_path)
        session.gate.search(SearchRequest("stress 200 MPa", "search.example.test"), workspace_id="ws:1")

        entries = surface.submit(Command("system.log", {"level": "info"})).value["entries"]

        egress = [one for one in entries if one["event"] == "egress"]
        assert len(egress) == 1 and egress[0]["level"] == "warning"
        assert egress[0]["context"]["outcome"] == "refused" and egress[0]["context"]["purpose"] == "webSearch"
        assert "200" not in str(egress[0]["context"]), "the content stays in the audit; the log keeps names and outcomes"
        audit = surface.submit(Command("system.audit", {})).value["entries"]
        assert len(audit) == 1 and audit[0]["outcome"] == "refused"

    def test_a_directory_makes_it_a_file_that_a_new_session_reads(self, tmp_path: Path) -> None:
        from service.egress.diagnostics import Log

        first = Session(clock=at(9), issue=counting_issuer(), log=Log(directory=tmp_path / "logs"))
        build_surface(first).submit(Command("dataset.describe", {"datasetId": "dataset:none"}))
        second = Session(clock=at(10), issue=counting_issuer(), log=Log(directory=tmp_path / "logs"))

        result = build_surface(second).submit(Command("system.log", {"level": "warning"}))

        assert result.value["source"] == "file" and result.value["logDirectory"] == str(tmp_path / "logs")
        assert result.value["files"] == 1 and result.value["retainDays"] == 7
        assert [one["context"]["operation"] for one in result.value["entries"]] == ["dataset.describe"]

    def test_what_is_asked_for_wrongly_is_refused_by_name(self, tmp_path: Path) -> None:
        surface, _, _ = opened(tmp_path)

        assert surface.submit(Command("system.log", {"level": "loud"})).status is Status.REFUSED
        assert surface.submit(Command("system.log", {"limit": 0})).status is Status.REFUSED
        assert surface.submit(Command("system.log", {"since": "yesterday"})).status is Status.REFUSED


PATH_KEYFRAMES = [
    {"at": 0.0, "camera": {"position_m": [4.0, 0.0, 0.0], "focalPoint_m": [0.5, 0.5, 0.5], "viewUp": [0.0, 0.0, 1.0], "projection": "perspective"}},
    {"at": 1.0, "camera": {"position_m": [0.0, 4.0, 0.0], "focalPoint_m": [0.5, 0.5, 0.5], "viewUp": [0.0, 0.0, 1.0], "projection": "perspective"}},
]


def a_view_with_a_path(surface: Surface, dataset_id: str, keyframes=None) -> str:
    return surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
        "name": "経路つき", "datasetId": dataset_id, "representation": "surface",
        "colouring": {"fieldName": "temperature", "association": "point", "colourMap": "viridis"},
        "cameraPaths": [{"id": "path:1", "name": "四分の一周", "interpolation": "linear", "keyframes": keyframes or PATH_KEYFRAMES}],
    }})).value["id"]


@needs_offscreen
class TestAFrameFromACameraPath:
    """XC-289: a picture drawn from a position on one of the view's camera paths, answered with the
    pose the path's rule gave and the rule, so the frame carries how its viewpoint was computed."""

    def test_the_frame_is_drawn_from_the_interpolated_pose_and_says_so(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id)

        drawn = surface.submit(Command("view.render", {"viewId": view_id, "width": 200, "height": 150, "format": "png", "cameraPath": {"id": "path:1", "at": 0.5}}))

        assert drawn.status is Status.ANSWERED, drawn.reason
        stated = drawn.value["cameraPath"]
        assert stated["id"] == "path:1" and stated["at"] == 0.5 and stated["interpolation"] == "linear"
        assert stated["camera"]["position_m"] == [2.0, 2.0, 0.0]
        assert stated["camera"]["viewUp"] == [0.0, 0.0, 1.0] and stated["camera"]["projection"] == "perspective"
        assert "直線補間" in stated["rule"]

    def test_the_same_pose_given_as_a_camera_draws_the_same_picture(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id)
        size = {"viewId": view_id, "width": 200, "height": 150, "format": "png"}

        from_path = surface.submit(Command("view.render", {**size, "cameraPath": {"id": "path:1", "at": 0.25}}))
        pose = from_path.value["cameraPath"]["camera"]
        from_camera = surface.submit(Command("view.render", {**size, "camera": pose}))

        assert from_path.status is Status.ANSWERED and from_camera.status is Status.ANSWERED
        assert session.handles.fetch(from_path.value["handle"]) == session.handles.fetch(from_camera.value["handle"])
        assert "cameraPath" not in from_camera.value

    def test_a_pick_on_a_path_frame_reads_the_same_picture(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id)

        picked = surface.submit(Command("view.pick", {"viewId": view_id, "width": 300, "height": 300, "x": 150, "y": 150, "cameraPath": {"id": "path:1", "at": 0.5}}))

        assert picked.status is Status.ANSWERED, picked.reason
        assert picked.value["cameraPath"]["camera"]["position_m"] == [2.0, 2.0, 0.0]
        assert picked.value["value"]["value"] in {float(one) for one in range(1, 9)}


class TestWhatACameraPathRefuses:
    def test_a_path_the_view_does_not_have_is_refused_with_what_there_is(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id)

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 200, "height": 150, "format": "png", "cameraPath": {"id": "path:9", "at": 0.5}}))

        assert result.status is Status.REFUSED and "path:9" in (result.reason or "") and "path:1" in (result.reason or "")

    def test_a_parameter_past_the_ends_is_refused_not_clamped(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id)

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 200, "height": 150, "format": "png", "cameraPath": {"id": "path:1", "at": 1.5}}))

        assert result.status is Status.REFUSED and "代用はしません" in (result.reason or "")

    def test_a_camera_and_a_path_together_are_two_answers_and_refused(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id)

        result = surface.submit(Command("view.render", {
            "viewId": view_id, "width": 200, "height": 150, "format": "png",
            "cameraPath": {"id": "path:1", "at": 0.5}, "camera": PATH_KEYFRAMES[0]["camera"],
        }))

        assert result.status is Status.REFUSED and "同時に" in (result.reason or "")

    def test_a_path_of_one_keyframe_is_refused_by_name(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        view_id = a_view_with_a_path(surface, dataset_id, keyframes=PATH_KEYFRAMES[:1])

        result = surface.submit(Command("view.render", {"viewId": view_id, "width": 200, "height": 150, "format": "png", "cameraPath": {"id": "path:1", "at": 0.0}}))

        assert result.status is Status.REFUSED and "2 件以上" in (result.reason or "")


def a_graph(surface: Surface, dataset_id: str, *, kind: str = "line", series=None, cases=None) -> str:
    definition = {
        "name": "温度の最大", "kind": kind,
        "series": series if series is not None else [
            {"label": "温度の最大", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "temperature", "association": "point", "reduction": "max"}, "unitDeclared": False},
        ],
    }
    if cases is not None:
        definition["caseSelection"] = {"caseIds": cases}
    created = surface.submit(Command("graph.create", {"workspaceId": "ws:1", "definition": definition}))
    assert created.status is Status.APPLIED, created.reason
    return created.value["id"]


class TestAGraphOverTheLoadedCase:
    """XC-290, graph/AC-001, AC-002, AC-008, AC-013, AC-022: the definition's series as numbers, one
    point per loaded case, with reduction, scope, weighting, digits and units stated."""

    def test_a_field_s_maximum_is_one_point_per_loaded_case_and_the_axis_says_undeclared(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        graph_id = a_graph(surface, dataset_id)

        result = surface.submit(Command("graph.data", {"graphId": graph_id}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["cases"] == ["case:1"] and result.value["selection"] == "loaded"
        series = result.value["series"][0]
        assert series["points"] == [{"caseId": "case:1", "x": None, "value": 8.0}]
        assert series["reduction"] == "max" and series["scope"] == "ケース全体（1 パート）" and series["digits"] == 6
        assert series["unit"] is None and series["declaredUnit"] is None and series["provenance"] == "dataset"
        assert result.value["axisLabel"] == "単位未宣言"
        assert result.value["missing"] == []
        got = surface.submit(Command("graph.get", {"graphId": graph_id}))
        assert got.status is Status.ANSWERED and got.value["definition"]["kind"] == "line" and got.value["revision"] == 1

    def test_the_context_case_is_plotted_where_the_definition_names_none_and_the_answer_says_so(self, tmp_path: Path) -> None:
        """XC-292, graph/AC-008: the asking area's case is the graph's subject where the definition
        names none; a case with nothing loaded is a point with its reason, not the loaded case instead."""
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        graph_id = a_graph(surface, dataset_id)

        result = surface.submit(Command("graph.data", {"graphId": graph_id, "contextCaseIds": ["case:2"]}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["cases"] == ["case:2"] and result.value["selection"] == "context"
        point = result.value["series"][0]["points"][0]
        assert point["caseId"] == "case:2" and point["value"] is None
        assert point["reason"] == "ケース 'case:2' は読み込まれていません"
        assert result.value["missing"] == ["温度の最大 / case:2：ケース 'case:2' は読み込まれていません"]

        same = surface.submit(Command("graph.data", {"graphId": graph_id, "contextCaseIds": ["case:1"]}))
        assert same.value["selection"] == "context" and same.value["series"][0]["points"][0]["value"] == 8.0

    def test_a_definition_that_names_its_cases_is_the_authority_over_the_context(self, tmp_path: Path) -> None:
        """11_ui.md, XC-292: an item that binds its own cases is not overridden by the tree."""
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        graph_id = a_graph(surface, dataset_id)
        got = surface.submit(Command("graph.get", {"graphId": graph_id})).value["definition"]
        bound = {**got, "caseSelection": {"caseIds": ["case:1"]}}
        updated = surface.submit(Command("graph.update", {"graphId": graph_id, "definition": bound}))
        assert updated.status is Status.APPLIED, updated.reason

        result = surface.submit(Command("graph.data", {"graphId": graph_id, "contextCaseIds": ["case:2"]}))

        assert result.status is Status.ANSWERED, result.reason
        assert result.value["cases"] == ["case:1"] and result.value["selection"] == "given"
        assert result.value["series"][0]["points"][0]["value"] == 8.0

    def test_a_declared_unit_puts_the_values_in_the_internal_unit_with_the_declared_one_beside(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        graph_id = a_graph(surface, dataset_id, series=[
            {"label": "応力の最大", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "stress", "association": "point", "reduction": "max"}, "unit": "MPa", "unitDeclared": True},
        ])

        series = surface.submit(Command("graph.data", {"graphId": graph_id})).value["series"][0]

        assert series["unit"] == "Pa" and series["declaredUnit"] == "MPa"
        assert series["points"][0]["value"] == pytest.approx(40.0e6), "40 MPa plotted in pascal, as CT-005 labels the axis"

    def test_the_mean_states_its_weighting(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        graph_id = a_graph(surface, dataset_id, series=[
            {"label": "温度の平均", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "temperature", "association": "point", "reduction": "mean"}, "unitDeclared": False},
        ])

        series = surface.submit(Command("graph.data", {"graphId": graph_id})).value["series"][0]

        assert series["reduction"] == "mean" and series["weighting"] == "dualVolume"
        assert series["points"][0]["value"] == pytest.approx(4.5)

    def test_a_field_of_several_components_is_no_data_with_the_reason_and_stays_in_the_legend(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_fields, name="fields.vtu")
        surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "magnitude"}))
        graph_id = a_graph(surface, dataset_id, series=[
            {"label": "変位の大きさの最大", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "displacement.magnitude", "association": "point", "reduction": "max"}, "unitDeclared": False},
            {"label": "変位そのもの", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "displacement", "association": "point", "reduction": "max"}, "unitDeclared": False},
        ])

        result = surface.submit(Command("graph.data", {"graphId": graph_id}))

        assert result.status is Status.ANSWERED, result.reason
        magnitude, vector = result.value["series"]
        assert magnitude["points"][0]["value"] == pytest.approx(7.0)
        assert vector["points"][0]["value"] is None and "3 成分" in vector["points"][0]["reason"]
        assert any(line.startswith("変位そのもの / case:1") for line in result.value["missing"])

    def test_a_series_without_a_reduction_is_refused_because_a_field_is_many_numbers(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        graph_id = a_graph(surface, dataset_id, series=[
            {"label": "温度", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "temperature", "association": "point"}, "unitDeclared": False},
        ])

        result = surface.submit(Command("graph.data", {"graphId": graph_id}))

        assert result.status is Status.REFUSED and "reduction" in (result.reason or "")

    def test_two_series_whose_units_cannot_share_an_axis_are_refused_naming_both(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
        surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "element_stress", "unitSymbol": "K"}))
        graph_id = a_graph(surface, dataset_id, series=[
            {"label": "応力", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "stress", "association": "point", "reduction": "max"}, "unit": "MPa", "unitDeclared": True},
            {"label": "温度のふりをした要素値", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "element_stress", "association": "cell", "reduction": "max"}, "unit": "K", "unitDeclared": True},
        ])

        result = surface.submit(Command("graph.data", {"graphId": graph_id}))

        assert result.status is Status.REFUSED
        assert "MPa" in (result.reason or "") and "K" in (result.reason or "")

    def test_a_case_that_is_not_loaded_is_a_missing_point_that_stays_in_the_series(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        graph_id = a_graph(surface, dataset_id, cases=["case:1", "case:9"])

        result = surface.submit(Command("graph.data", {"graphId": graph_id}))

        assert result.value["selection"] == "given" and result.value["cases"] == ["case:1", "case:9"]
        points = result.value["series"][0]["points"]
        assert points[0]["value"] == 8.0 and points[1]["value"] is None and "case:9" in points[1]["reason"]

    def test_over_the_result_axis_each_point_is_a_step_and_says_which(self, tmp_path: Path) -> None:
        requires_h5py()
        from cgns_fixture import write_transient_cgns

        surface, _, dataset_id = loaded(tmp_path, write=write_transient_cgns, name="t.cgns")
        graph_id = a_graph(surface, dataset_id, kind="overTime", series=[
            {"label": "応力の最大", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "stress", "association": "point", "reduction": "max"}, "unitDeclared": False},
        ])

        result = surface.submit(Command("graph.data", {"graphId": graph_id}))

        assert result.status is Status.ANSWERED, result.reason
        points = result.value["series"][0]["points"]
        assert [(one["x"], one["value"]) for one in points] == [(0.0, 90.0), (0.5, 91.0)]
        assert points[1]["resultPosition"]["stated"] == "ステップ 2/2（位置 0.5・軸の種類は宣言なし）"
        assert "宣言されていない" in result.value.get("resultAxisNote", "")


class TestTheOpenAnswerNamesTheCases:
    """XC-291: a file dropped on the window goes to a case the document names, never one the
    interface guessed; the open answer lists them flat, with their parents."""

    def test_the_demo_workspace_has_its_one_case(self, tmp_path: Path) -> None:
        surface, _, workspace = opened(tmp_path)

        result = surface.submit(Command("workspace.open", {"path": str(workspace)}))

        assert result.status is Status.APPLIED, result.reason
        assert result.value["cases"] == [{"id": "case:1", "name": "baseline", "sources": []}]

    def test_a_nested_case_names_its_parent(self, tmp_path: Path) -> None:
        document = a_workspace(tmp_path, cases=[{"id": "case:1", "name": "study", "children": [{"id": "case:1a", "name": "variant"}]}])
        session = Session(clock=at(9), issue=counting_issuer(), native_offscreen=lambda: (False, "テスト"))
        surface = build_surface(session)

        result = surface.submit(Command("workspace.open", {"path": str(document)}))

        assert result.status is Status.APPLIED, result.reason
        assert result.value["cases"] == [{"id": "case:1", "name": "study", "sources": []}, {"id": "case:1a", "name": "variant", "parentId": "case:1", "sources": []}]


class TestASupportBundle:
    """XC-302, operations/AC-008: listed before it exists, the person's own information by their
    choice, the log's free text only with both, and the archive whole or absent."""

    @staticmethod
    def _opened_with_a_file_log(tmp_path: Path) -> tuple[Surface, Session, Path]:
        from service.egress import diagnostics

        session = Session(clock=at(9), issue=counting_issuer(), log=diagnostics.Log(directory=tmp_path / "logs"))
        surface = build_surface(session)
        workspace = a_workspace(tmp_path)
        opened = surface.submit(Command("workspace.open", {"path": str(workspace)}))
        assert opened.status is Status.APPLIED, opened.reason
        source = workspace.parent / "case.vtu"
        write_grid(source)
        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        assert loaded.status is Status.APPLIED, loaded.reason
        # A refusal whose reason names a path, so the log holds free text the bundle must not leak.
        missing = surface.submit(Command("workspace.open", {"path": str(tmp_path / "ない.svw")}))
        assert missing.status is Status.REFUSED
        return surface, session, source

    def test_the_list_holds_the_log_product_and_environment_and_the_customer_s_information_only_when_chosen(self, tmp_path: Path) -> None:
        surface, _, source = self._opened_with_a_file_log(tmp_path)

        plain = surface.submit(Command("system.supportManifest", {}))
        chosen = surface.submit(Command("system.supportManifest", {"include": {"caseNames": True, "filePaths": True}}))

        assert plain.status is Status.ANSWERED, plain.reason
        kinds = [one["kind"] for one in plain.value["items"]]
        assert kinds == ["log", "product", "environment", "workspace"]
        assert plain.value["freeTextKept"] is False and "伏せます" in plain.value["items"][0]["detail"]
        assert plain.value["customerItems"] == 0
        assert chosen.status is Status.ANSWERED, chosen.reason
        items = chosen.value["items"]
        assert [one["name"] for one in items if one["kind"] == "case"] == ["baseline"]
        assert [one["name"] for one in items if one["kind"] == "file"] == [str(source)]
        assert all(one["customer"] for one in items if one["kind"] in ("case", "file"))
        assert not any(one["customer"] for one in items if one["kind"] not in ("case", "file"))
        assert chosen.value["customerItems"] == 2 and chosen.value["freeTextKept"] is True
        assert "お客さまの情報です" in chosen.value["text"] and "そのまま" in items[0]["detail"]

    def test_the_bundle_needs_consent_and_the_list_shown_with_the_same_choice(self, tmp_path: Path) -> None:
        surface, _, _ = self._opened_with_a_file_log(tmp_path)
        target = tmp_path / "診断.zip"

        unseen = surface.submit(Command("system.supportBundle", {"consent": True, "path": str(target)}))
        shown = surface.submit(Command("system.supportManifest", {"include": {"caseNames": True}}))
        other = surface.submit(Command("system.supportBundle", {"consent": True, "path": str(target), "include": {"filePaths": True}}))
        unconsented = surface.submit(Command("system.supportBundle", {"consent": False, "path": str(target), "include": {"caseNames": True}}))

        assert shown.status is Status.ANSWERED
        assert unseen.status is Status.REFUSED and "一覧" in (unseen.reason or "")
        assert other.status is Status.REFUSED and "同じ選択" in (other.reason or "")
        assert unconsented.status is Status.REFUSED and "同意" in (unconsented.reason or "")
        assert not target.exists() and not (tmp_path / "診断.zip.writing").exists()

    def test_what_is_written_is_what_was_listed_and_the_free_text_goes_in_only_with_both(self, tmp_path: Path) -> None:
        from service.egress import diagnostics

        surface, session, source = self._opened_with_a_file_log(tmp_path)
        names_only = tmp_path / "名前だけ.zip"
        everything = tmp_path / "全部.zip"

        surface.submit(Command("system.supportManifest", {"include": {"caseNames": True}}))
        made = surface.submit(Command("system.supportBundle", {"consent": True, "path": str(names_only), "include": {"caseNames": True}}))
        surface.submit(Command("system.supportManifest", {"include": {"caseNames": True, "filePaths": True}}))
        made_all = surface.submit(Command("system.supportBundle", {"consent": True, "path": str(everything), "include": {"caseNames": True, "filePaths": True}}))
        again = surface.submit(Command("system.supportBundle", {"consent": True, "path": str(everything), "include": {"caseNames": True, "filePaths": True}}))

        assert made.status is Status.APPLIED, made.reason
        with zipfile.ZipFile(names_only) as archive:
            names = archive.namelist()
            assert names == ["manifest.txt", "manifest.json", "environment.json", "log/solvia.jsonl", "cases.json"]
            log_text = archive.read("log/solvia.jsonl").decode("utf-8")
            assert diagnostics.REDACTED in log_text and "ない.svw" not in log_text and str(source) not in log_text
            assert "baseline" in archive.read("manifest.txt").decode("utf-8")
            environment = json.loads(archive.read("environment.json"))
            assert environment["python"] and "productVersion" in environment and "logDirectory" not in environment
        assert made.value["entries"] == ["manifest.txt", "manifest.json", "environment.json", "log/solvia.jsonl", "cases.json"]
        assert made.value["bytes"] == names_only.stat().st_size and made.value["path"] == str(names_only)
        assert made.value["contents"] and any("baseline" in line for line in made.value["contents"])
        assert made_all.status is Status.APPLIED, made_all.reason
        with zipfile.ZipFile(everything) as archive:
            assert "sources.json" in archive.namelist()
            log_text = archive.read("log/solvia.jsonl").decode("utf-8")
            assert "ない.svw" in log_text and diagnostics.REDACTED not in log_text
            recorded = json.loads(archive.read("sources.json"))
            assert recorded == [{"caseId": "case:1", "path": str(source), "present": True}]
        assert again.status is Status.REFUSED and "すでにあります" in (again.reason or "")
        assert any(line.event == "supportBundle" for line in session.log.lines())
        assert not any(name.endswith(".writing") for name in os.listdir(tmp_path))


class TestAWorkspaceIsBoundedInCases:
    """LIM-005 (XC-306): a document past the ceiling opens whole and says so, lists every case to the
    interface, and saves. Nothing it holds is dropped for the sake of a number."""

    def test_a_document_past_the_limit_opens_whole_says_so_and_saves(self, tmp_path: Path) -> None:
        from engine.limits import MAX_CASES_PER_WORKSPACE

        surface, session = a_surface()
        path = a_workspace(tmp_path, cases=[{"id": f"case:{n:05d}", "name": f"c{n}"} for n in range(MAX_CASES_PER_WORKSPACE + 1)])

        result = surface.submit(Command("workspace.open", {"path": str(path)}))

        assert result.status is Status.APPLIED, result.reason
        assert any("LIM-005" in one and f"{MAX_CASES_PER_WORKSPACE + 1:,} 件" in one for one in result.warnings)
        assert session.workspace is not None and len(result.value["cases"]) == MAX_CASES_PER_WORKSPACE + 1
        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        assert saved.status is Status.APPLIED, saved.reason
        # A document at the limit is not crowded: nothing is said of it.
        within = a_workspace(tmp_path / "within", cases=[{"id": f"case:{n:05d}", "name": f"c{n}"} for n in range(MAX_CASES_PER_WORKSPACE)]) if (tmp_path / "within").mkdir() is None else None
        opened = surface.submit(Command("workspace.open", {"path": str(within)}))
        assert opened.status is Status.APPLIED, opened.reason
        assert not any("LIM-005" in one for one in opened.warnings)
