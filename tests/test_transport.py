"""The engine on the wire: the same surface, reached over HTTP on loopback (XC-258).

The command surface was always reachable in-process. These tests drive it the way the interface
will - a real listener on a real port, real JSON over real sockets - and hold three things the
transport must not blur:

**A refusal is an answer.** The surface refusing a command is carried with 200 and
`status: "refused"`, because the request arrived and was understood. Only a request that could not
become a command is an HTTP error. A caller that conflates the two retries the wrong one.

**The token is required.** Loopback is reachable by every process running as the user, so a port
without a token is a command surface any program on the machine can drive.

**The envelope is unchanged by being carried.** What goes in is CT-003's request and what comes back
is CT-003's response - not a shape this transport found convenient.

Verifies: CT-003, XC-258, XC-045, INV-006.
"""

from __future__ import annotations

import json
import os
import stat
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

from service.command.catalogue import PROTOCOL_VERSION  # noqa: E402
from service.command.handlers import Session, build_surface  # noqa: E402
from service.transport.local import (  # noqa: E402
    CONNECTION_FILE,
    LOOPBACK_HOST,
    TOKEN_HEADER,
    Connection,
    Engine,
    TransportError,
    command_from,
    serve,
    write_connection,
)
from test_handlers import a_workspace, at, counting_issuer  # noqa: E402
from test_reader import write_grid  # noqa: E402


@pytest.fixture
def engine(tmp_path: Path):
    session = Session(clock=at(9), issue=counting_issuer())
    listener = serve(Engine(session, build_surface(session)), connection_directory=tmp_path)
    try:
        yield listener
    finally:
        listener.stop()


def ask(listener, payload: dict, *, token: str | None = "use the real one") -> tuple[int, dict]:
    """POST one CT-003 request and return the status and the body."""
    request = urllib.request.Request(
        f"{listener.connection.base_url}/command",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if token is not None:
        request.add_header(TOKEN_HEADER, listener.engine.token if token == "use the real one" else token)
    try:
        with urllib.request.urlopen(request, timeout=20) as answer:
            return answer.status, json.loads(answer.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def fetch(listener, path: str, *, token: str | None = "use the real one") -> tuple[int, bytes]:
    request = urllib.request.Request(f"{listener.connection.base_url}{path}")
    if token is not None:
        request.add_header(TOKEN_HEADER, listener.engine.token if token == "use the real one" else token)
    try:
        with urllib.request.urlopen(request, timeout=20) as answer:
            return answer.status, answer.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def envelope(operation: str, **parameters) -> dict:
    return {"protocol": PROTOCOL_VERSION, "operation": operation, "parameters": parameters}


class TestItIsUpAndSaysWhatItSpeaks:
    def test_health_needs_no_token_because_a_shell_must_be_able_to_ask(self, engine) -> None:
        status, body = fetch(engine, "/health", token=None)

        assert status == 200
        assert json.loads(body)["protocols"] == [PROTOCOL_VERSION]

    def test_it_binds_loopback_and_nothing_else(self, engine) -> None:
        assert engine.connection.host == LOOPBACK_HOST == "127.0.0.1"
        assert engine.port > 0, "the operating system chose the port (XC-258)"

    def test_the_connection_file_says_how_to_reach_it(self, engine, tmp_path: Path) -> None:
        written = json.loads((tmp_path / CONNECTION_FILE).read_text(encoding="utf-8"))

        assert written["host"] == "127.0.0.1"
        assert written["port"] == engine.port
        assert written["token"] == engine.engine.token
        assert written["protocol"] == PROTOCOL_VERSION

    @pytest.mark.skipif(os.name == "nt", reason="Windows does not carry POSIX file modes")
    def test_the_connection_file_is_readable_only_by_its_owner(self, tmp_path: Path) -> None:
        """A token in a world-readable file is a token every process on the machine has."""
        write_connection(Connection("127.0.0.1", 1, "secret", PROTOCOL_VERSION), tmp_path / "run")

        mode = (tmp_path / "run" / CONNECTION_FILE).stat().st_mode
        assert not mode & (stat.S_IRGRP | stat.S_IROTH)


class TestTheTokenIsRequired:
    def test_a_command_without_the_token_is_refused(self, engine) -> None:
        status, body = ask(engine, envelope("system.protocols"), token=None)

        assert status == 401
        assert body["reason"]["id"] == "authorisation.required"

    def test_a_command_with_the_wrong_token_is_refused(self, engine) -> None:
        status, body = ask(engine, envelope("system.protocols"), token="not the token")

        assert status == 401
        assert body["reason"]["id"] == "authorisation.required"

    def test_a_handle_without_the_token_is_refused(self, engine) -> None:
        status, _ = fetch(engine, "/handle/handle:0001", token=None)

        assert status == 401


class TestTheEnvelopeSurvivesTheWire:
    def test_a_read_answers_in_the_contract_s_shape(self, engine) -> None:
        status, body = ask(engine, envelope("system.protocols"))

        assert status == 200
        assert body["status"] == "answered"
        assert body["result"] == {"versions": [PROTOCOL_VERSION]}

    def test_a_write_carries_its_undo_id_and_what_changed(self, engine, tmp_path: Path) -> None:
        status, body = ask(engine, envelope("workspace.open", path=str(a_workspace(tmp_path))))

        assert status == 200
        assert body["status"] == "applied"
        assert body["changed"] == ["ws:1"]
        assert body["undoId"]
        assert body["result"]["workspaceId"] == "ws:1"

    def test_a_surface_refusal_is_an_answer_not_a_transport_error(self, engine) -> None:
        """The request arrived and was understood; the case named in it is not there. 200."""
        status, body = ask(engine, envelope("dataset.load", caseId="case:9", filePaths=["x.vtu"]))

        assert status == 200, "a refusal is an answer - only an unparseable request is an HTTP error"
        assert body["status"] == "refused"
        assert body["reason"]

    def test_a_dry_run_travels(self, engine, tmp_path: Path) -> None:
        payload = dict(envelope("workspace.open", path=str(a_workspace(tmp_path))), dryRun=True)

        status, body = ask(engine, payload)

        assert status == 200
        assert body["status"] == "answered", "a dry run applied nothing"
        assert "undoId" not in body

    def test_the_whole_thread_runs_over_the_wire(self, engine, tmp_path: Path) -> None:
        """Open, load, declare, probe - the prototype's own steps, through sockets."""
        source = tmp_path / "case.vtu"
        write_grid(source)
        assert ask(engine, envelope("workspace.open", path=str(a_workspace(tmp_path))))[1]["status"] == "applied"
        loaded = ask(engine, envelope("dataset.load", caseId="case:1", filePaths=[str(source)]))[1]
        dataset_id = loaded["result"]["datasetId"]
        assert ask(engine, envelope(
            "field.declareUnit", datasetId=dataset_id, fieldName="stress", unitSymbol="MPa",
        ))[1]["status"] == "applied"

        _, probed = ask(engine, envelope(
            "dataset.probe", datasetId=dataset_id, fieldName="stress",
            pointM=[0.0, 1.0, 0.0], resultPosition=0,
        ))

        assert probed["status"] == "answered"
        assert probed["result"]["value"] == {
            "value": 40.0, "unit": "MPa", "digits": 6, "provenance": "dataset",
            "location": probed["result"]["value"]["location"],
        }


class TestWhatCannotBecomeACommand:
    def test_another_protocol_version_is_refused_politely(self, engine) -> None:
        status, body = ask(engine, {"protocol": "1.0.0", "operation": "system.protocols", "parameters": {}})

        assert status == 400
        assert body["reason"]["id"] == "protocol.unsupported"
        assert PROTOCOL_VERSION in body["reason"]["message"]

    def test_a_body_that_is_not_json_is_refused_with_the_reason(self, engine) -> None:
        request = urllib.request.Request(
            f"{engine.connection.base_url}/command", data=b"{not json",
            headers={"Content-Type": "application/json", TOKEN_HEADER: engine.engine.token}, method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(request, timeout=20)

        assert failure.value.code == 400
        assert json.loads(failure.value.read())["reason"]["id"] == "request.malformed"

    def test_an_unknown_path_is_refused_rather_than_served(self, engine) -> None:
        assert fetch(engine, "/anything")[0] == 404
        assert ask(engine, envelope("system.protocols"))[0] == 200

    def test_an_authorisation_field_the_contract_does_not_declare_is_refused(self) -> None:
        with pytest.raises(TransportError) as refusal:
            command_from({
                "protocol": PROTOCOL_VERSION, "operation": "system.protocols", "parameters": {},
                "authorisation": {"allowEverything": True},
            })
        assert "allowEverything" in refusal.value.message

    def test_an_authorisation_the_contract_declares_reaches_the_command(self) -> None:
        command = command_from({
            "protocol": PROTOCOL_VERSION, "operation": "case.delete", "parameters": {"caseId": "case:1"},
            "authorisation": {"allowDestructive": True},
        })

        assert [one.value for one in command.allowed] == ["allowDestructive"]


class TestHandlesAreFetchedSeparately:
    def test_an_unknown_handle_is_gone_rather_than_empty(self, engine) -> None:
        status, body = fetch(engine, "/handle/handle:nothing")

        assert status == 410
        assert json.loads(body)["reason"]["id"] == "handle.expired"

    def test_bytes_put_in_the_store_come_back_whole(self, engine) -> None:
        issued = engine.engine.session.handles.issue(b"\x89PNG\r\n\x1a\nnot really a picture")

        status, body = fetch(engine, f"/handle/{issued['id']}")

        assert status == 200
        assert body == b"\x89PNG\r\n\x1a\nnot really a picture"
