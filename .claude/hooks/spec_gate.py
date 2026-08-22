"""Keep the specification set green, and say so at the start of a session.

Two events, one job. On SessionStart it reports the work list so nobody starts from a stale idea of
what is decided. After an edit under specs/ or evidence/ it runs the linter and blocks the turn from
ending while findings remain, because a spec that drifts for a day is a spec that drifts for a month.

Fail-open by design: if Python, the linter or the repository layout is not what this expects, the hook
prints nothing and exits 0. A guard that breaks a session is worse than a guard that misses one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINTER = ROOT / "validate" / "check_specs.py"
BOUNDARIES = ROOT / "validate" / "check_boundaries.py"
WATCHED = ("specs/", "evidence/")


def run_linter() -> tuple[int, list[dict]]:
    result = subprocess.run(
        [sys.executable, str(LINTER), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    try:
        findings = json.loads(result.stdout).get("findings", [])
    except (json.JSONDecodeError, AttributeError):
        return 0, []
    return len(findings), findings


def run_boundaries() -> int:
    """Boundary violations, or zero if the checker cannot run."""
    if not BOUNDARIES.exists():
        return 0
    result = subprocess.run(
        [sys.executable, str(BOUNDARIES)], cwd=ROOT, capture_output=True, text=True, timeout=120
    )
    return result.returncode


def session_start() -> None:
    count, findings = run_linter()
    if count == 0:
        boundary_state = "boundaries hold" if run_boundaries() == 0 else "BOUNDARY VIOLATIONS - run python validate/check_boundaries.py"
        print(f"specs: 0 findings, {boundary_state}. Open questions are tracked in specs/08_decisions.md.")
        return
    checks = sorted({f["check"] for f in findings})
    print(f"specs: {count} findings across checks {checks}. Run python validate/check_specs.py for the list.")


def after_edit(payload: dict) -> int:
    path = str(payload.get("tool_input", {}).get("file_path", "")).replace("\\", "/")
    if path.endswith(".py") and "/src/" in path and run_boundaries() != 0:
        print("Module boundaries are violated: run python validate/check_boundaries.py", file=sys.stderr)
        return 2
    if not any(part in path for part in WATCHED):
        return 0
    count, findings = run_linter()
    if count == 0:
        return 0
    lines = [f"  [check {f['check']}] {f['file']}:{f['line']} {f['message']}" for f in findings[:8]]
    more = "" if count <= 8 else f"\n  ... and {count - 8} more"
    print(f"The specification set has {count} finding(s):\n" + "\n".join(lines) + more, file=sys.stderr)
    return 2  # ask the model to fix them before finishing


def main() -> int:
    if not LINTER.exists():
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    event = payload.get("hook_event_name", "")
    try:
        if event == "SessionStart":
            session_start()
            return 0
        if event in ("PostToolUse", "Stop"):
            return after_edit(payload)
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
