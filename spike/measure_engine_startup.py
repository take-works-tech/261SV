"""How long the engine takes to be reachable, and what a termination leaves behind (#305, #307).

Starts `python -m service.transport` the way a shell would, N times, and reports for each run the
time from spawn to the connection file, the time of the first `/health`, the exit code after
`terminate()`, and whether the connection file survived it. Prints one JSON object; the record of a
run lives in results.json under `engine_startup`.

Run in the engine environment: `python spike/measure_engine_startup.py [runs]`. The numbers are of
this machine on this day - a warm cache, an unpacked interpreter - and say nothing about a packaged
cold start on a machine that has never run it, which is what #307 is about and stays unmeasured.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def one_run() -> dict[str, object]:
    directory = Path(tempfile.mkdtemp(prefix="solvia-start-"))
    connection_file = directory / "connection.json"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"}
    started = time.perf_counter()
    process = subprocess.Popen(
        [sys.executable, "-m", "service.transport", "--connection-directory", str(directory)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    while not connection_file.exists():
        time.sleep(0.01)
        if time.perf_counter() - started > 120:
            process.kill()
            raise SystemExit("the engine did not write its connection file within 120 s")
    ready_s = time.perf_counter() - started
    connection = json.loads(connection_file.read_text(encoding="utf-8"))
    asked = time.perf_counter()
    with urllib.request.urlopen(f"http://{connection['host']}:{connection['port']}/health", timeout=10) as answer:
        answer.read()
    health_ms = (time.perf_counter() - asked) * 1000
    process.terminate()
    process.wait(timeout=30)
    return {
        "spawn_to_connection_file_s": round(ready_s, 3),
        "first_health_ms": round(health_ms, 1),
        "exit_code_after_terminate": process.returncode,
        "connection_file_survives_terminate": connection_file.exists(),
        "pid_in_file": connection.get("pid"),
    }


def main(argv: list[str]) -> int:
    runs = int(argv[0]) if argv else 3
    record = {
        "measured": time.strftime("%Y-%m-%d"),
        "machine": f"{platform.system()} {platform.release()}, Python {platform.python_version()}",
        "runs": [one_run() for _ in range(runs)],
        "not_measured": "a packaged cold start on a machine that has never run the product (#307)",
    }
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
