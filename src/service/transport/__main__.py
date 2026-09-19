"""Start the engine and serve it on loopback: `python -m service.transport`.

The shell starts this and reads the connection file it writes; a person starts it the same way to
drive the engine with `curl`, which is the point of a protocol rather than a private channel.

Deliberately small, like `service.pipeline.headless`. What the engine does is decided by the
handlers; this exists to prove the same surface is reachable over the wire, not to become a second
place where behaviour is chosen.
"""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

import os

from service.command.catalogue import PROTOCOL_VERSION
from service.command.handlers import Session, build_surface
from service.egress.diagnostics import Level, Log
from service.transport.local import Connection, Engine, serve


def announce(connection: Connection, where: Path | None) -> None:
    """One line on stdout so a person or a parent process knows it is up and how to reach it.

    The token is **not** printed: stdout is inherited, redirected into log files and scraped. Where
    the connection file is, is what the caller needs.
    """
    print(f"engine listening on {connection.base_url} (protocol {connection.protocol})", flush=True)
    if where is not None:
        print(f"connection file: {where}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="service.transport", description="Serve the command surface on loopback.")
    parser.add_argument("--port", type=int, default=0, help="0 lets the operating system choose (XC-258)")
    parser.add_argument(
        "--connection-directory", type=Path, default=None,
        help="where to write connection.json; omit to write none and print the address instead",
    )
    parser.add_argument(
        "--allow-origin", default=None,
        help="a browser origin permitted to call this engine, for a development build served by vite",
    )
    parser.add_argument(
        "--log-directory", type=Path, default=None,
        help="where the diagnostic log is written, rotated and retained (XC-263); omit for memory only",
    )
    parser.add_argument(
        "--log-level", choices=[one.value for one in Level], default=Level.INFO.value,
        help="the least level written; warning is the list of what was refused or failed",
    )
    arguments = parser.parse_args(argv if argv is not None else sys.argv[1:])

    session = Session(log=Log(directory=arguments.log_directory, level=Level(arguments.log_level)))
    session.log.record(Level.INFO, "engine.start", pid=os.getpid(), protocol=PROTOCOL_VERSION)
    engine = Engine(session, build_surface(session), allowed_origin=arguments.allow_origin)
    listener = serve(engine, port=arguments.port, connection_directory=arguments.connection_directory)
    where = (arguments.connection_directory / "connection.json") if arguments.connection_directory else None
    announce(listener.connection, where)

    stop = signal.SIGINT
    try:
        signal.signal(stop, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    except ValueError:  # pragma: no cover - not the main thread
        pass
    try:
        listener.thread.join()
    except KeyboardInterrupt:
        print("stopping", flush=True)
    finally:
        listener.stop()
        session.log.record(Level.INFO, "engine.stop", pid=os.getpid())
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
