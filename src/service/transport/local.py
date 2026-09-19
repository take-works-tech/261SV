"""CT-003's envelope over HTTP on loopback, with a per-session token (XC-258).

The command surface has always been reachable in-process. This is what makes it reachable from the
interface, which runs in a browser engine and cannot import Python.

Three endpoints and no more. `POST /command` takes one request object and answers with one response
object - the same envelope CT-003 states, unchanged by being carried. `GET /handle/{id}` fetches the
bytes an answer named, because geometry and images do not travel in a response body. `GET /health`
answers the protocol versions, and is the one request that needs no token: a shell that cannot yet
prove who it is still has to be able to ask whether the engine is up.

**Loopback is not private.** Every process running as the user can reach 127.0.0.1, so a port with no
token is a command surface any program on the machine can drive - one that reads and writes files
wherever the user can. The token is generated per session, written to a file with owner-only
permissions, and required on every request but `/health`. It is in a file rather than an argument
because arguments are visible in the process list to every user on the machine.

**Nothing here decides anything.** The listener parses, checks the token, hands the envelope to the
surface, and writes back what the surface answered. A refusal the surface made is carried with
status 200 and `status: "refused"` in the body, because it is an answer rather than a transport
failure - the two are different things and a caller that conflates them retries the wrong one.

Specification: CT-003, XC-258, XC-045, INV-007.
"""

from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote

from service.command.catalogue import (
    COMMAND_PATH,
    HANDLE_PATH,
    HEALTH_PATH,
    PROTOCOL_VERSION,
    TOKEN_HEADER,
)
from service.command.handlers import HandleExpired, Session
from service.command.surface import Command, Origin, Permission, Result, Status, Surface

# The header, the three paths and the protocol version are **generated** into the catalogue from
# CT-003's `$defs.transport`, and generated into the interface from the same place (XC-252, XC-258).
# A header the request carries and a header the listener checks are one name or they are a bug that
# only a failing request reveals. A header rather than a query parameter, because a URL with a token
# in it lands in logs, in a browser's history and in a referrer.

#: How the interface finds the engine. Written by the engine, read by the shell that started it.
CONNECTION_FILE = "connection.json"

#: The address. Never 0.0.0.0: binding every interface would put the command surface on the network,
#: which is the one thing INV-007 and this product's whole position refuse.
LOOPBACK_HOST = "127.0.0.1"

#: Origins a browser page may call from. The interface is served from a file or a local preview, so
#: this is what a development build needs and a packaged shell does not use at all.
ALLOWED_ORIGIN_HEADER = "Access-Control-Allow-Origin"

#: The largest request body this listener reads. A command envelope is identifiers and numbers; a
#: megabyte is far past any of them, and the point of the bound is that an unauthorised caller cannot
#: make this process allocate. Data of any size travels by handle, never in a request (CT-003).
MAX_REQUEST_BYTES = 1_048_576

#: How the errors CT-003 names appear on the wire. The identifier is what a caller matches on; the
#: message is for a person and may be translated (XC-020, XC-021).
UNAUTHORISED = "authorisation.required"
UNSUPPORTED_PROTOCOL = "protocol.unsupported"
HANDLE_EXPIRED = "handle.expired"
MALFORMED = "request.malformed"

PERMISSION_FIELDS = {
    "allowDestructive": Permission.DESTRUCTIVE,
    "allowOverwrite": Permission.OVERWRITE,
    "allowNetwork": Permission.NETWORK,
}


class TransportError(Exception):
    """A request that cannot become a command. Answered with a reason, never with a guess."""

    def __init__(self, identifier: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.identifier = identifier
        self.message = message
        self.status = status


@dataclass(frozen=True, slots=True)
class Connection:
    """What the shell needs to reach the engine, and what it is written to."""

    host: str
    port: int
    token: str
    protocol: str

    def as_json(self) -> str:
        return json.dumps(
            {"host": self.host, "port": self.port, "token": self.token, "protocol": self.protocol},
            ensure_ascii=False,
        )

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def write_connection(connection: Connection, directory: Path) -> Path:
    """Write the connection file so only its owner can read it.

    The mode matters more than the contents: a token in a world-readable file is a token every
    process on the machine has, which is the thing the token exists to prevent.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / CONNECTION_FILE
    path.write_text(connection.as_json(), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        # Some filesystems (a mounted share, a container's overlay) refuse the mode. The token is
        # still per-session and still required; saying nothing would be worse than not enforcing it.
        pass
    return path


def command_from(payload: Any) -> Command:
    """CT-003's request object as a `Command`, or the refusal that says what is wrong with it."""
    if not isinstance(payload, dict):
        raise TransportError(MALFORMED, f"要求はオブジェクトです（{type(payload).__name__} が届きました）")
    protocol = payload.get("protocol")
    if protocol != PROTOCOL_VERSION:
        # Refused politely below the floor rather than attempted: a caller speaking another version
        # believes fields mean what its own version says, and the engine cannot tell which.
        raise TransportError(
            UNSUPPORTED_PROTOCOL,
            f"このエンジンが話すのは protocol {PROTOCOL_VERSION} です（'{protocol}' が届きました）",
        )
    operation = payload.get("operation")
    if not isinstance(operation, str):
        raise TransportError(MALFORMED, "operation は文字列です")
    parameters = payload.get("parameters", {})
    if not isinstance(parameters, dict):
        raise TransportError(MALFORMED, "parameters はオブジェクトです")
    targets = payload.get("targets", []) or []
    if not isinstance(targets, list):
        raise TransportError(MALFORMED, "targets は配列です")
    authorisation = payload.get("authorisation") or {}
    if not isinstance(authorisation, dict):
        raise TransportError(MALFORMED, "authorisation はオブジェクトです")
    unknown = sorted(set(authorisation) - set(PERMISSION_FIELDS))
    if unknown:
        raise TransportError(MALFORMED, f"authorisation に知らない項目 {unknown} があります")
    allowed = frozenset(
        permission for field, permission in PERMISSION_FIELDS.items() if authorisation.get(field)
    )
    return Command(
        operation=operation,
        parameters=parameters,
        origin=Origin.INTERFACE,
        targets=tuple(str(one) for one in targets),
        group_id=payload.get("groupId"),
        allowed=allowed,
        dry_run=bool(payload.get("dryRun", False)),
    )


def response_from(result: Result) -> dict[str, Any]:
    """A `Result` as CT-003's response object. Only what the answer carries is present."""
    body: dict[str, Any] = {"status": result.status.value}
    if result.changed:
        body["changed"] = list(result.changed)
    if result.effect_summary:
        body["effectSummary"] = result.effect_summary
    if result.reason:
        body["reason"] = result.reason
    if result.undo_id:
        body["undoId"] = result.undo_id
    if result.value is not None:
        body["result"] = result.value
    if result.warnings:
        body["warnings"] = list(result.warnings)
    return body


class Engine:
    """One engine process's session, surface and token - what the listener serves."""

    def __init__(
        self,
        session: Session,
        surface: Surface,
        *,
        token: str | None = None,
        allowed_origin: str | None = None,
    ) -> None:
        self.session = session
        self.surface = surface
        # 32 bytes of urlsafe randomness. Long enough that guessing is not a threat model and short
        # enough to sit in a header without wrapping.
        self.token = token or secrets.token_urlsafe(32)
        self.allowed_origin = allowed_origin

    def submit(self, payload: Any) -> dict[str, Any]:
        return response_from(self.surface.submit(command_from(payload)))

    def handle(self, identifier: str) -> bytes:
        try:
            return self.session.handles.fetch(identifier)
        except HandleExpired as error:
            raise TransportError(HANDLE_EXPIRED, str(error), status=410) from None

    def health(self) -> dict[str, Any]:
        return {"protocols": [PROTOCOL_VERSION], "operations": len(self.surface.registered())}


def _handler_class(engine: Engine) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "solvia-engine"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            """Silent by default. What a command did is the surface's log, which records who asked,
            when, and how it went - a second record in a different shape helps nobody."""

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            if engine.allowed_origin:
                self.send_header(ALLOWED_ORIGIN_HEADER, engine.allowed_origin)
                self.send_header("Access-Control-Allow-Headers", TOKEN_HEADER + ", Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: Any) -> None:
            self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _refuse(self, error: TransportError, operation: str = "") -> None:
            self._json(error.status, {
                "status": Status.REFUSED.value,
                "reason": {"id": error.identifier, "message": error.message, "operation": operation},
            })

        def _authorised(self) -> bool:
            # Compared in constant time: a comparison that returns early leaks the token one
            # character at a time to anything that can measure the reply.
            return secrets.compare_digest(self.headers.get(TOKEN_HEADER, ""), engine.token)

        def do_OPTIONS(self) -> None:  # noqa: N802 - the base class names it
            self._send(204, b"", "text/plain")

        def do_GET(self) -> None:  # noqa: N802
            if self.path == HEALTH_PATH:
                self._json(200, engine.health())
                return
            if not self._authorised():
                self._refuse(TransportError(UNAUTHORISED, "トークンがありません（XC-258）", status=401))
                return
            if self.path.startswith(HANDLE_PATH):
                # Decoded: a handle's identifier holds a colon, which a correct client percent-encodes
                # in a path segment. Reading the raw segment looks up `handle%3Aab12` and finds
                # nothing, and the answer is "expired" for a handle issued a second ago - a message
                # that sends whoever reads it looking for the wrong fault entirely.
                identifier = unquote(self.path[len(HANDLE_PATH):])
                try:
                    self._send(200, engine.handle(identifier), "application/octet-stream")
                except TransportError as error:
                    self._refuse(error)
                return
            self._refuse(TransportError(MALFORMED, f"'{self.path}' はこのエンジンの経路ではありません", status=404))

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_REQUEST_BYTES:
                # Not read at all: a caller that has not proved who it is does not get to make this
                # process allocate. The connection closes because the body is still on the wire.
                self.close_connection = True
                self._refuse(TransportError(
                    MALFORMED,
                    f"要求が大きすぎます（{length:,} バイト、上限 {MAX_REQUEST_BYTES:,}）。"
                    "大きなデータはハンドルで受け渡します（CT-003）",
                    status=413,
                ))
                return
            # **Read the body before answering**, even to refuse. A reply sent while the request is
            # still arriving leaves bytes on a connection the client believes is reusable, and the
            # client sees the connection reset rather than the 401 - which is how this first behaved.
            raw = self.rfile.read(length) if length else b""
            if not self._authorised():
                self._refuse(TransportError(UNAUTHORISED, "トークンがありません（XC-258）", status=401))
                return
            if self.path != COMMAND_PATH:
                self._refuse(TransportError(MALFORMED, f"'{self.path}' はこのエンジンの経路ではありません", status=404))
                return
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else None
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                self._refuse(TransportError(MALFORMED, f"本文を読めません：{error}"))
                return
            try:
                # A refusal from the surface is an **answer**, carried with 200: the request arrived
                # and was understood. Only a request that could not become a command is an HTTP error.
                self._json(200, engine.submit(payload))
            except TransportError as error:
                self._refuse(error, str((payload or {}).get("operation", "")))

    return Handler


@dataclass
class Listener:
    """A running engine, and how to reach and stop it."""

    engine: Engine
    server: ThreadingHTTPServer
    thread: threading.Thread

    @property
    def port(self) -> int:
        return int(self.server.server_address[1])

    @property
    def connection(self) -> Connection:
        return Connection(host=LOOPBACK_HOST, port=self.port, token=self.engine.token, protocol=PROTOCOL_VERSION)

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=10)


def serve(
    engine: Engine,
    *,
    port: int = 0,
    connection_directory: Path | None = None,
    ready: Callable[[Connection], None] | None = None,
) -> Listener:
    """Start the listener on loopback and return it, without blocking.

    Port 0 by default: the operating system picks a free one and the connection file says which,
    so two engines on one machine never fight over a number somebody wrote down.
    """
    server = ThreadingHTTPServer((LOOPBACK_HOST, port), _handler_class(engine))
    thread = threading.Thread(target=server.serve_forever, name="solvia-engine", daemon=True)
    thread.start()
    listener = Listener(engine=engine, server=server, thread=thread)
    if connection_directory is not None:
        write_connection(listener.connection, connection_directory)
    if ready is not None:
        ready(listener.connection)
    return listener
