"""How long the shell takes, from its own start, to a window, a loaded interface and a reachable
engine (#307, XC-304).

Launches the shell with `--measure-launch --profile <fresh temp dir>` N times - the development
shell through Electron, and the packaged application when `src/shell/release/win-unpacked/SOLVIA.exe`
exists - and reads the one JSON line each launch prints once the engine is running and the interface
has loaded, after which the shell quits on its own. Prints one JSON object; the record of a run lives
in results.json under `launch`. The numbers are of this machine on this day with a warm file cache;
a cold start on a machine that has never run the product is not measured here, and the record says
so rather than estimating it.

Run in the engine environment with the shell built (`cd src/shell && npm run build`):
    python spike/measure_launch.py [runs] [--packaged]
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "src" / "shell"
PACKAGED = SHELL / "release" / "win-unpacked" / "SOLVIA.exe"
TIMEOUT_S = 150


def launch(command: list[str], *, cwd: Path) -> dict[str, object]:
    profile = Path(tempfile.mkdtemp(prefix="solvia-launch-"))
    try:
        completed = subprocess.run(
            [*command, "--measure-launch", "--profile", str(profile)],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "SOLVIA_PYTHON": sys.executable, "PYTHONIOENCODING": "utf-8"},
            timeout=TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        # A build that does not know the flag runs as the product and never quits: said, not hung on.
        return {"error": f"no measurement within {TIMEOUT_S} s: a build without --measure-launch runs on as the product"}
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    lines = [one for one in completed.stdout.splitlines() if one.startswith("{")]
    if not lines:
        return {"error": f"no measurement printed (exit {completed.returncode})", "stderr": completed.stderr[-400:]}
    return json.loads(lines[-1])


def main(argv: list[str]) -> int:
    packaged = "--packaged" in argv
    numbers = [one for one in argv if one.isdigit()]
    runs = int(numbers[0]) if numbers else 3
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    record: dict[str, object] = {
        "script": "spike/measure_launch.py",
        "machine": f"{platform.system()} {platform.release()}, Python {platform.python_version()}, warm file cache",
        "development": [launch([npx, "electron", ".", "--"], cwd=SHELL) for _ in range(runs)],
        # The packaged application only on request, and only a build that knows the flag: an older
        # build runs on as the product until the timeout and measures nothing.
        "packaged": (
            [launch([str(PACKAGED)], cwd=PACKAGED.parent) for _ in range(runs)]
            if packaged and PACKAGED.exists() else None
        ),
        "not_measured": "a cold start on a machine that has never run the product: the file cache here is warm",
    }
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
