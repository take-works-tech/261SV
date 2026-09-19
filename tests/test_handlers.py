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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import REQUIRE_VTK, offscreen_rendering_available, requires_vtk

requires_vtk()

#: The rendering tests below run where the product's own probe says a picture can be drawn. Elsewhere
#: they skip with the probe's reason - except in CI, where test_render.py has already failed the run
#: for the same reason, because a renderer never exercised is a renderer nobody has seen work.
OFFSCREEN_AVAILABLE, OFFSCREEN_DETAIL = offscreen_rendering_available()
needs_offscreen = pytest.mark.skipif(
    not OFFSCREEN_AVAILABLE and not REQUIRE_VTK, reason=f"no offscreen rendering here: {OFFSCREEN_DETAIL}"
)


from service.command.catalogue import OPERATIONS, PROTOCOL_VERSION  # noqa: E402
from service.command.handlers import HandleExpired, HandleStore, Session, build_surface  # noqa: E402
from service.command.surface import Command, Status, Surface  # noqa: E402
from service.workspace.document import FORMAT_VERSION  # noqa: E402
from test_reader import write_grid  # noqa: E402
from demo_case import write_cube  # noqa: E402, F401 - re-exported for the tests that import it from here

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


class TestWhatThisBuildRegisters:
    def test_every_operation_on_the_path_has_a_handler(self) -> None:
        surface, _ = a_surface()

        registered = set(surface.registered())

        assert registered == {
            "workspace.open", "dataset.load", "dataset.describe", "dataset.parts",
            "field.declareUnit", "field.statistics", "view.create", "view.update", "view.render",
            "dataset.probe", "view.pick", "report.create", "report.export", "report.provenance",
            "workspace.save", "dataset.inspect",
            "system.capabilities", "system.protocols",
        }
        assert len(surface.unimplemented()) == len(OPERATIONS) - 18

    def test_an_unimplemented_operation_is_refused_and_named_as_such(self) -> None:
        surface, _ = a_surface()
        assert "graph.data" in surface.unimplemented()

        result = surface.submit(Command("graph.data", {"graphId": "g"}))

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
            "sources": [{"pathRelative": "gone.vtu", "sizeBytes": 10, "modifiedIso": "2026-09-18T00:00:00Z"}],
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
        assert fields["stress"] == {"name": "stress", "association": "point", "unit": None}
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
            "name": "case", "type": "part", "pointCount": 4, "cellCount": 2,
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

    def test_a_region_is_refused_until_it_is_built(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "region": "part 1"}))

        assert result.status is Status.REFUSED


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
        assert result.value["sources"][0]["modifiedUtc"]
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

    def test_a_result_position_this_build_cannot_reach_is_refused_by_name(self, tmp_path: Path) -> None:
        surface, _, dataset_id = loaded(tmp_path)

        result = surface.submit(Command("dataset.probe", {
            "datasetId": dataset_id, "fieldName": "stress", "pointM": [0.0, 0.0, 0.0], "resultPosition": 3,
        }))

        assert result.status is Status.REFUSED
        assert "resultPosition=3" in (result.reason or "")

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
        assert reloaded["fields"] == [{"name": "temperature", "association": "point", "unit": "K"}]

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

        assert reloaded["fields"] == [{"name": "temperature", "association": "point", "unit": None}]

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
