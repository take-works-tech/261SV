"""Every time this product records is two facts on the wire, in every contract and at every exit.

XC-142 decided on 2026-08-20 that a recorded time is UTC with the local offset beside it. On
2026-09-20 every contract still carried a time as a bare UTC string - eighteen fields in seven
schemas, each named `...Iso` or `...Utc` - and the engine, holding both facts in memory, dropped the
second at every serialisation (#318). XC-266 gave a recorded time one wire form, `{utc, offsetMinutes}`,
defined once in CT-001 and referenced by every contract. These are the sweep that would have found the
gap, kept so it cannot reopen: the schemas first, then each place the engine writes a time, against a
session whose clock stands at noon in Osaka (UTC+09:00).

Verifies: workspace/AC-054, workspace/TASK-069.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from conftest import requires_vtk

requires_vtk()

from domain_core.recorded_time import RecordedTime, from_stored, record as record_time, record_instant  # noqa: E402
from service.command.handlers import Session, build_surface  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from service.egress.diagnostics import Level, Log  # noqa: E402
from service.workspace import variables  # noqa: E402
from service.workspace.document import FORMAT_VERSION  # noqa: E402
from service.workspace.hierarchy import add, new_case  # noqa: E402
from test_handlers import a_workspace, counting_issuer  # noqa: E402
from test_reader import write_grid  # noqa: E402

SCHEMAS = Path(__file__).resolve().parents[1] / "specs" / "contracts" / "schema"
OSAKA = timezone(timedelta(hours=9))
NOON = datetime(2026, 9, 20, 12, 0, tzinfo=OSAKA)
NOON_UTC = "2026-09-20T03:00:00Z"

#: The names a recorded time goes by in the contracts. Listed, so that a new one is a line here and
#: not a string field nobody swept.
TIME_NAMES = frozenset({
    "at", "modified", "produced", "started", "finished", "occurred", "detached", "copied",
    "updated", "generated", "created", "imported",
})
DEFINITION = "#/$defs/recordedTime"
REFERENCE = "CT-001.json#/$defs/recordedTime"


def properties_of(schema: Any, path: str = "") -> Iterator[tuple[str, str, Any]]:
    """Every (path, name, node) under a `properties` map, at any depth."""
    if isinstance(schema, dict):
        for name, node in (schema.get("properties") or {}).items():
            yield f"{path}/{name}", name, node
        for key, child in schema.items():
            if key != "properties":
                yield from properties_of(child, f"{path}/{key}")
    elif isinstance(schema, list):
        for index, child in enumerate(schema):
            yield from properties_of(child, f"{path}[{index}]")


def every_schema() -> dict[str, dict[str, Any]]:
    return {one.name: json.loads(one.read_text(encoding="utf-8")) for one in sorted(SCHEMAS.glob("*.json"))}


class TestNoContractCarriesATimeAsAString:
    def test_no_property_is_named_as_a_bare_timestamp(self) -> None:
        """The convention the offset was lost under: `modifiedIso`, `atUtc`. A name ending that way is
        a string, and a string cannot be told from a timestamp by anything but a person."""
        found = [
            f"{file} {path}"
            for file, schema in every_schema().items()
            for path, name, node in properties_of(schema)
            if name.endswith(("Iso", "Utc")) or (isinstance(node, dict) and node.get("format") == "date-time")
        ]

        assert found == [], "a recorded time as a bare string: " + ", ".join(found)

    def test_every_recorded_time_is_the_one_definition(self) -> None:
        """One shape, defined once (CT-001 `$defs.recordedTime`) and referenced - so a sweep can see it."""
        wrong = []
        for file, schema in every_schema().items():
            for path, name, node in properties_of(schema):
                if name not in TIME_NAMES or not isinstance(node, dict):
                    continue
                if node.get("properties"):
                    continue  # a container that happens to share a name, such as CT-008's `imported`
                expected = DEFINITION if file == "CT-001.json" else REFERENCE
                if node.get("$ref") != expected:
                    wrong.append(f"{file} {path} -> {node.get('$ref') or node.get('type')}")

        assert wrong == [], "not the one definition: " + ", ".join(wrong)

    def test_the_definition_is_what_the_engine_stores(self) -> None:
        definition = every_schema()["CT-001.json"]["$defs"]["recordedTime"]
        stored = RecordedTime(NOON_UTC, 540).as_stored()

        assert set(definition["required"]) == set(stored) == {"utc", "offsetMinutes"}
        assert definition["additionalProperties"] is False
        assert "null" in definition["properties"]["offsetMinutes"]["type"]
        assert from_stored(stored) == RecordedTime(NOON_UTC, 540)


def at_noon_in_osaka() -> Session:
    return Session(clock=lambda: NOON, issue=counting_issuer())


def is_the_pair(value: object, *, offset: int | None = 540) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"utc", "offsetMinutes"}
        and value["offsetMinutes"] == offset
        and from_stored(value).utc == value["utc"]
    )


class TestEveryTimeTheEngineWritesIsThePair:
    """Each exit the engine has for a time, exercised; each carries the session's offset, +540."""

    def test_the_history_answer(self, tmp_path: Path) -> None:
        surface = build_surface(at_noon_in_osaka())
        surface.submit(Command("workspace.open", {"path": str(a_workspace(tmp_path))}))

        listed = surface.submit(Command("history.list", {"workspaceId": "ws:1"}))

        assert listed.status is Status.ANSWERED, listed.reason
        entry = listed.value["entries"][-1]
        assert is_the_pair(entry["at"]) and entry["at"]["utc"] == NOON_UTC
        assert "atUtc" not in entry

    def test_the_inspection_answer_carries_the_file_time_with_this_offset(self, tmp_path: Path) -> None:
        """A file's own zone no filesystem keeps; the offset is the recorder's (XC-266)."""
        surface = build_surface(at_noon_in_osaka())
        source = tmp_path / "case.vtu"
        write_grid(source)

        inspected = surface.submit(Command("dataset.inspect", {"path": str(source)}))

        assert inspected.status is Status.ANSWERED, inspected.reason
        assert is_the_pair(inspected.value["modified"])
        expected = record_instant(datetime.fromtimestamp(source.stat().st_mtime, tz=timezone.utc), where=NOON)
        assert inspected.value["modified"] == expected.as_stored()
        assert "modifiedIso" not in inspected.value

    def test_a_missing_file_has_no_time_rather_than_an_empty_one(self, tmp_path: Path) -> None:
        surface = build_surface(at_noon_in_osaka())

        inspected = surface.submit(Command("dataset.inspect", {"path": str(tmp_path / "absent.vtu")}))

        assert inspected.status is Status.ANSWERED, inspected.reason
        assert inspected.value["exists"] is False and "modified" not in inspected.value

    def test_the_source_record_the_provenance_and_the_deliverable(self, tmp_path: Path) -> None:
        session = at_noon_in_osaka()
        surface = build_surface(session)
        surface.submit(Command("workspace.open", {"path": str(a_workspace(tmp_path))}))
        source = tmp_path / "case.vtu"
        write_grid(source)
        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        assert loaded.status is Status.APPLIED, loaded.reason

        assert session.workspace is not None
        recorded = session.workspace.raw["cases"][0]["sources"][0]
        assert is_the_pair(recorded["modified"]) and "modifiedIso" not in recorded

        created = surface.submit(Command("report.create", {
            "workspaceId": "ws:1",
            "definition": {
                "name": "報告", "targets": ["html"],
                "blocks": [{"kind": "text", "text": "梁の基本ケース。"}, {"kind": "valueTable", "fields": ["stress"]}],
            },
        }))
        assert created.status is Status.APPLIED, created.reason
        provenance = surface.submit(Command("report.provenance", {"reportId": created.value["id"]}))

        assert provenance.status is Status.ANSWERED, provenance.reason
        # What the document recorded when the file was read, not the file's clock now: the numbers
        # came from the recorded file, and the record carries who recorded it.
        assert provenance.value["sources"][0]["modified"] == recorded["modified"]
        assert "modifiedUtc" not in provenance.value["sources"][0]
        assert is_the_pair(provenance.value["produced"]) and provenance.value["produced"]["utc"] == NOON_UTC

        # The deliverable has no reader's zone to show a time in, so it shows the recorded moment with
        # the zone named - the same moment to every reader.
        described = session.provenance_of([session.datasets[loaded.value["datasetId"]]]).as_text()
        assert "作成：2026-09-20 12:00（UTC+09:00）" in described
        assert "（UTC+09:00）" in described.split("元ファイル：")[1]

    def test_a_detachment_is_recorded_with_where_it_happened(self) -> None:
        document: dict[str, Any] = {
            "formatVersion": FORMAT_VERSION, "id": "w", "cases": [], "variables": [], "workspaceItems": {},
        }
        root = add(document["cases"], new_case("case:1", "root"))
        add(document["cases"], new_case("case:2", "child"), beneath="case:1")
        variables.declare(document, "mesh", "メッシュ寸法", 5.0)

        variables.detach(document, "case:2", "mesh", when=record_time(NOON))

        state = root["children"][0]["variableStates"]["mesh"]
        assert is_the_pair(state["detached"]) and state["detached"]["utc"] == NOON_UTC
        assert "detachedIso" not in state

    def test_the_log_line(self, tmp_path: Path) -> None:
        log = Log(clock=lambda: NOON, directory=tmp_path / "logs")

        log.record(Level.INFO, "command", operation="view.render", status="answered")

        line = json.loads((tmp_path / "logs" / "solvia.log").read_text(encoding="utf-8").splitlines()[0])
        assert is_the_pair(line["at"]) and line["at"]["utc"] == NOON_UTC
        assert "offsetMinutes" not in line


class TestARecordWrittenBeforeTheOffsetWasKept:
    """A version-4 document wrote a source's and a detachment's time as bare strings. It is lifted on
    open with the offset null - unknown, never zero (XC-001) - said in the open's answer, and written
    back as this version (CT-001 5.0.0)."""

    def old_document(self, tmp_path: Path) -> Path:
        path = tmp_path / "old.svw"
        path.write_text(json.dumps({
            "formatVersion": "4.0.0", "id": "ws:old", "name": "旧", "variables": [],
            "workspaceItems": {"views": [], "graphs": [], "reports": [], "simulations": []},
            "cases": [{
                "id": "case:1", "name": "baseline",
                "sources": [{"pathRelative": "run.vtu", "sizeBytes": 10, "modifiedIso": "2026-08-24T12:00:00Z"}],
                "children": [{
                    "id": "case:2", "name": "child", "children": [], "sources": [],
                    "variableStates": {"mesh": {"state": "independent", "value": 3.0, "detachedIso": "2026-08-24T12:00:00Z"}},
                }],
            }],
        }, ensure_ascii=False), encoding="utf-8")
        return path

    def test_it_is_lifted_with_the_offset_unknown_and_the_open_says_so(self, tmp_path: Path) -> None:
        session = at_noon_in_osaka()
        surface = build_surface(session)
        path = self.old_document(tmp_path)

        opened = surface.submit(Command("workspace.open", {"path": str(path)}))

        assert opened.status is Status.APPLIED, opened.reason
        assert any("4.0.0" in one and FORMAT_VERSION in one and "不明" in one for one in opened.warnings)
        assert session.workspace is not None
        raw = session.workspace.raw
        assert raw["formatVersion"] == FORMAT_VERSION
        lifted = raw["cases"][0]["sources"][0]
        assert lifted["modified"] == {"utc": "2026-08-24T12:00:00Z", "offsetMinutes": None}
        assert "modifiedIso" not in lifted
        nested = raw["cases"][0]["children"][0]["variableStates"]["mesh"]
        assert nested["detached"] == {"utc": "2026-08-24T12:00:00Z", "offsetMinutes": None}
        assert "detachedIso" not in nested
        assert from_stored(nested["detached"]).describe(540) == "2026-08-24 21:00（記録時のゾーンは不明）"

        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:old"}))

        assert saved.status is Status.APPLIED, saved.reason
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written["formatVersion"] == FORMAT_VERSION
        assert written["cases"][0]["sources"][0]["modified"]["offsetMinutes"] is None

    def test_a_current_document_opens_without_a_word_about_lifting(self, tmp_path: Path) -> None:
        surface = build_surface(at_noon_in_osaka())

        opened = surface.submit(Command("workspace.open", {"path": str(a_workspace(tmp_path))}))

        assert opened.status is Status.APPLIED, opened.reason
        assert not any("読み替え" in one for one in opened.warnings)
