"""The recovery file beside a workspace document (workspace/AC-026, AC-027; XC-311; #431).

Every applied write to an open document leaves the document as it stands in `<name>.recovery`
beside the file, with the writes since the last save; a save removes it; a document opened with one
beside it says so and offers it, and takes it only on `recover`. The saved file is untouched until the
person saves. Measured here with real files: what a crash leaves is what the next session finds.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

from demo_case import write_cube  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from service.workspace import recovery  # noqa: E402
from service.workspace.document import fresh, load  # noqa: E402
from test_handlers import a_surface, loaded  # noqa: E402


def held_elsewhere(workspace: Path) -> None:
    """The document's lock as another machine would leave it: never examined for liveness, so the next
    open here is read-only (XC-241, XC-269)."""
    (workspace.parent / (workspace.name + ".lock")).write_text(json.dumps({
        "processId": 4321, "host": "pc9", "user": "hanako",
        "takenAt": {"utc": "2026-10-03T00:00:00Z", "offsetMinutes": 540},
    }), encoding="utf-8")


def declare(surface, dataset_id: str, symbol: str) -> None:
    applied = surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "temperature", "unitSymbol": symbol}))
    assert applied.status is Status.APPLIED, applied.reason


class TestEveryAppliedWriteLeavesTheDocumentBesideTheFile:
    def test_the_file_appears_with_the_document_and_the_writes_and_the_saved_file_is_untouched(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert workspace is not None
        saved_bytes = workspace.read_bytes()
        beside = recovery.recovery_path(workspace)
        assert beside.name == workspace.name + ".recovery"

        declare(surface, dataset_id, "K")
        declare(surface, dataset_id, "MPa")

        assert beside.exists(), "the recovery file stands beside the document"
        found = recovery.read_recovery(beside)
        assert found.document_id == session.workspace.identifier
        assert [one["operation"] for one in found.writes] == ["dataset.load", "field.declareUnit", "field.declareUnit"]
        assert found.count == 3 and "MPa" in found.writes[-1]["summary"]
        assert found.document["cases"][0]["sources"][0]["declaredUnits"] == {"temperature": "MPa"}
        assert workspace.read_bytes() == saved_bytes, "the saved file is not rewritten (AC-026)"
        with pytest.raises(Exception):
            load(beside)  # never a document: a loader handed it refuses it

    def test_a_save_removes_it_and_a_write_after_starts_it_again(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        beside = recovery.recovery_path(workspace)
        declare(surface, dataset_id, "K")
        assert beside.exists()

        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))

        assert saved.status is Status.APPLIED, saved.reason
        assert not beside.exists(), "the save wrote the work; the recovery file goes"
        assert session.unsaved_writes == []
        declare(surface, dataset_id, "MPa")
        found = recovery.read_recovery(beside)
        assert [one["operation"] for one in found.writes] == ["field.declareUnit"] and found.count == 1

    def test_a_read_only_session_writes_none(self, tmp_path: Path) -> None:
        surface, session, _ = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED
        held_elsewhere(workspace)
        other, other_session = a_surface()
        opened = other.submit(Command("workspace.open", {"path": str(workspace)}))
        assert opened.status is Status.APPLIED and opened.value["readOnly"] is True
        loaded_again = other.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(workspace.parent / "cube.vtu")]}))
        assert loaded_again.status is Status.APPLIED, loaded_again.reason

        assert not recovery.recovery_path(workspace).exists(), "another window's document gets no file from this one"
        assert other_session.unsaved_writes == []


def crashed_session(tmp_path: Path) -> tuple[Path, Path]:
    """A session that saved, declared a unit, and ended: the recovery file alone is what remains."""
    surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
    workspace = session.workspace_path
    assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED
    declare(surface, dataset_id, "MPa")
    # The engine ends here: nothing more is saved, and the lock it held is released as a clean end
    # would release it, so what the next session meets is the recovery file alone.
    session.release_workspace()
    return workspace, workspace.parent / "cube.vtu"


class TestTheNextSessionIsOfferedItAndTakesItOnlyWhenAsked:
    def test_opening_says_what_stood_beside_and_opens_the_saved_document(self, tmp_path: Path) -> None:
        workspace, source = crashed_session(tmp_path)
        surface, session = a_surface()

        opened = surface.submit(Command("workspace.open", {"path": str(workspace)}))

        assert opened.status is Status.APPLIED, opened.reason
        assert opened.value["recovered"] is False
        offer = opened.value["recovery"]
        assert offer["count"] == 1 and offer["writes"][0]["operation"] == "field.declareUnit"
        assert offer["baseChanged"] is False and offer["writtenAt"]["utc"]
        entry = session.workspace.cases[0]["sources"][0]
        assert entry.get("declaredUnits", {}) == {}, "the saved document, not the recovered one"
        assert recovery.recovery_path(workspace).exists(), "offered, not consumed"
        assert session.unsaved_writes == []

    def test_recover_opens_that_document_unsaved_and_a_save_then_removes_the_file(self, tmp_path: Path) -> None:
        workspace, source = crashed_session(tmp_path)
        surface, session = a_surface()

        opened = surface.submit(Command("workspace.open", {"path": str(workspace), "recover": True}))

        assert opened.status is Status.APPLIED, opened.reason
        assert opened.value["recovered"] is True and opened.value["recovery"]["count"] == 1
        assert session.workspace.cases[0]["sources"][0]["declaredUnits"] == {"temperature": "MPa"}
        assert [one["operation"] for one in session.unsaved_writes] == ["field.declareUnit"]
        assert json.loads(workspace.read_text(encoding="utf-8"))["cases"][0]["sources"][0].get("declaredUnits", {}) == {}, "the file waits for the save"
        loaded_again = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        assert loaded_again.status is Status.APPLIED
        assert {field["name"]: field["unit"] for field in loaded_again.value["fields"]}["temperature"] == "MPa"
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED
        assert not recovery.recovery_path(workspace).exists()
        assert json.loads(workspace.read_text(encoding="utf-8"))["cases"][0]["sources"][0]["declaredUnits"] == {"temperature": "MPa"}

    def test_discarding_removes_it_and_the_undo_puts_it_back(self, tmp_path: Path) -> None:
        workspace, _ = crashed_session(tmp_path)
        surface, _ = a_surface()
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        beside = recovery.recovery_path(workspace)
        before = beside.read_bytes()

        discarded = surface.submit(Command("workspace.discardRecovery", {"workspaceId": "ws:1"}))

        assert discarded.status is Status.APPLIED and discarded.value == {"discarded": True}
        assert not beside.exists()
        assert surface.undo(discarded.undo_id).status is Status.APPLIED
        assert beside.read_bytes() == before
        again = surface.submit(Command("workspace.discardRecovery", {"workspaceId": "ws:1"}))
        assert again.value == {"discarded": True}
        assert surface.submit(Command("workspace.discardRecovery", {"workspaceId": "ws:1"})).value == {"discarded": False}

    def test_a_read_only_open_is_offered_it_and_does_not_take_it(self, tmp_path: Path) -> None:
        surface, session, dataset_id = loaded(tmp_path, write=write_cube, name="cube.vtu")
        workspace = session.workspace_path
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED
        declare(surface, dataset_id, "MPa")
        # Another machine holds the lock: a second window here opens read-only.
        held_elsewhere(workspace)
        other, other_session = a_surface()

        opened = other.submit(Command("workspace.open", {"path": str(workspace), "recover": True}))

        assert opened.status is Status.APPLIED and opened.value["readOnly"] is True
        assert opened.value["recovered"] is False and opened.value["recovery"]["count"] == 1
        assert any("読み取り専用" in one and "復元していません" in one for one in opened.warnings)
        assert other_session.workspace.cases[0]["sources"][0].get("declaredUnits", {}) == {}

    def test_a_file_that_is_not_a_recovery_file_or_is_another_documents_is_said_and_not_taken(self, tmp_path: Path) -> None:
        workspace, _ = crashed_session(tmp_path)
        beside = recovery.recovery_path(workspace)
        beside.write_bytes(b"not json at all")
        surface, _ = a_surface()
        opened = surface.submit(Command("workspace.open", {"path": str(workspace), "recover": True}))
        assert opened.status is Status.APPLIED and opened.value["recovered"] is False and "recovery" not in opened.value
        assert any("復旧ファイルとして読めません" in one for one in opened.warnings)

        other_document = fresh("ws:other", "別の文書", cases=[{"id": "case:x", "name": "x", "children": [], "sources": []}])
        recovery.write_recovery(other_document.raw, workspace, writes=[{"operation": "view.create", "summary": "x", "at": {"utc": "2026-10-03T00:00:00Z", "offsetMinutes": 540}}], now=__import__("datetime").datetime.now().astimezone(), product_version="test", session_id="other")
        opened = a_surface()[0].submit(Command("workspace.open", {"path": str(workspace), "recover": True}))
        assert opened.status is Status.APPLIED and opened.value["recovered"] is False
        assert any("別の文書" in one for one in opened.warnings)

    def test_a_document_saved_by_somebody_else_since_is_said_to_have_changed(self, tmp_path: Path) -> None:
        workspace, _ = crashed_session(tmp_path)
        time.sleep(0.02)
        text = json.loads(workspace.read_text(encoding="utf-8"))
        text["name"] = "誰かが保存した"
        workspace.write_text(json.dumps(text, ensure_ascii=False) + "\n", encoding="utf-8")

        opened = a_surface()[0].submit(Command("workspace.open", {"path": str(workspace)}))

        assert opened.value["recovery"]["baseChanged"] is True


class TestAnOfferIsNeverOverwrittenByTheSessionItWasMadeTo:
    """The connected thread found the hole (E-230): the first applied write after taking over a dead
    engine's lock overwrote the dead engine's offer with the saved document. Now that write sets the
    offer aside, this session writes its own file, `recover` takes the offer wherever it stands, a
    save removes only this session's files, and a discard moves an older offer up."""

    def test_a_write_while_the_offer_stands_sets_it_aside_and_a_save_keeps_it(self, tmp_path: Path) -> None:
        workspace, source = crashed_session(tmp_path)
        surface, session = a_surface()
        opened = surface.submit(Command("workspace.open", {"path": str(workspace)}))
        assert opened.status is Status.APPLIED and opened.value["recovered"] is False
        offered = recovery.recovery_path(workspace).read_bytes()

        loaded_again = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))

        assert loaded_again.status is Status.APPLIED
        assert recovery.earlier_path(workspace).read_bytes() == offered, "the offer, moved aside and whole"
        mine = recovery.read_recovery(recovery.recovery_path(workspace))
        assert mine.session_id == session.session_id and [one["operation"] for one in mine.writes] == ["dataset.load"]
        assert session.recovery_pending is False

        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))

        assert saved.status is Status.APPLIED
        assert not recovery.recovery_path(workspace).exists(), "this session's own file goes with the save"
        assert recovery.earlier_path(workspace).read_bytes() == offered, "the offer stays"
        assert any("残しました" in one for one in saved.warnings), saved.warnings
        assert recovery.find_offer(workspace, session.workspace.identifier, session.session_id).recovery is not None

    def test_recover_after_working_on_takes_the_offer_set_aside(self, tmp_path: Path) -> None:
        workspace, source = crashed_session(tmp_path)
        surface, session = a_surface()
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        assert surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]})).status is Status.APPLIED
        assert recovery.earlier_path(workspace).exists()

        taken = surface.submit(Command("workspace.open", {"path": str(workspace), "recover": True}))

        assert taken.status is Status.APPLIED and taken.value["recovered"] is True
        assert session.workspace.cases[0]["sources"][0]["declaredUnits"] == {"temperature": "MPa"}
        assert not recovery.earlier_path(workspace).exists(), "taken, the file taken from goes"
        own = recovery.read_recovery(recovery.recovery_path(workspace))
        assert own.session_id == session.session_id and own.document["cases"][0]["sources"][0]["declaredUnits"] == {"temperature": "MPa"}
        assert [one["operation"] for one in own.writes] == ["field.declareUnit"], "the offer's list, continued by this session"

    def test_discarding_removes_the_offer_and_leaves_this_sessions_own_file(self, tmp_path: Path) -> None:
        workspace, source = crashed_session(tmp_path)
        surface, session = a_surface()
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        assert surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]})).status is Status.APPLIED

        discarded = surface.submit(Command("workspace.discardRecovery", {"workspaceId": "ws:1"}))

        assert discarded.status is Status.APPLIED and discarded.value == {"discarded": True}
        assert not recovery.earlier_path(workspace).exists()
        assert recovery.read_recovery(recovery.recovery_path(workspace)).session_id == session.session_id
        assert session.recovery_pending is False

    def test_two_generations_are_offered_newest_first_and_a_discard_moves_the_older_up(self, tmp_path: Path) -> None:
        workspace, source = crashed_session(tmp_path)
        second, second_session = a_surface()
        assert second.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        loaded_again = second.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        assert loaded_again.status is Status.APPLIED
        declare(second, loaded_again.value["datasetId"], "Pa")
        second_session.release_workspace()  # the second session ends without saving too
        third, third_session = a_surface()

        opened = third.submit(Command("workspace.open", {"path": str(workspace)}))

        assert opened.status is Status.APPLIED
        offer = opened.value["recovery"]
        assert offer["olderOffer"] is True and [one["operation"] for one in offer["writes"]] == ["dataset.load", "field.declareUnit"], "the newest first"
        assert "Pa" in offer["writes"][-1]["summary"]
        discarded = third.submit(Command("workspace.discardRecovery", {"workspaceId": "ws:1"}))
        assert discarded.value["discarded"] is True
        older = discarded.value["nextOffer"]
        assert older["olderOffer"] is False and [one["operation"] for one in older["writes"]] == ["field.declareUnit"] and "MPa" in older["writes"][0]["summary"]
        assert recovery.recovery_path(workspace).exists() and not recovery.earlier_path(workspace).exists(), "moved up into the main slot"
        assert third_session.recovery_pending is True
        assert third.undo(discarded.undo_id).status is Status.APPLIED
        assert recovery.earlier_path(workspace).exists(), "the undo puts both back where they were"
        assert [one["operation"] for one in recovery.read_recovery(recovery.recovery_path(workspace)).writes] == ["dataset.load", "field.declareUnit"]


class TestWhatItCosts:
    def test_a_two_thousand_case_document_is_written_in_well_under_a_second(self, tmp_path: Path) -> None:
        """The file is written after every applied write, so its cost is a cost on every edit: measured
        at LIM-005's size and printed (this machine), held to a bound a person does not notice."""
        cases = [{"id": f"case:{index}", "name": f"荷重 {100 + index} N", "children": [], "sources": [], "tags": ["掃引"]} for index in range(2000)]
        document = fresh("ws:big", "大きな文書", cases=cases)
        target = tmp_path / "big.svw"
        target.write_text("{}", encoding="utf-8")
        writes = [{"operation": "case.tag", "summary": "tagged", "at": {"utc": "2026-10-03T00:00:00Z", "offsetMinutes": 540}}] * 50

        started = time.perf_counter()
        for _ in range(5):
            recovery.write_recovery(document.raw, target, writes=writes, now=__import__("datetime").datetime.now().astimezone(), product_version="test", session_id="probe")
        elapsed = (time.perf_counter() - started) / 5

        size = recovery.recovery_path(target).stat().st_size
        print(f"recovery file: 2000 cases, {size / 1e6:.2f} MB, written in {elapsed * 1000:.1f} ms per write (this machine)")
        assert elapsed < 1.0
