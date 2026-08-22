"""A gate that never runs is not a gate.

Every check in `validate/` must be invoked by something that actually runs it. The failure this
catches has no symptom: the file exists, its logic is right, its tests pass, and the pipeline that was
supposed to call it never mentions it. Everything is green because nothing is being checked.

This is the cheapest of the gates here and the one that keeps the others honest, so it is deliberately
the smallest thing that can work: read every runner, read every validator, report the difference.

Exit code: 0 all wired, 1 something is not. Stdlib only.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "validate"

# Anything that can invoke a validator. A project that adds a task runner adds it here, and the
# omission is visible as a false positive rather than as a silent pass.
RUNNER_PATTERNS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "Makefile",
    "pyproject.toml",
    "noxfile.py",
    "tox.ini",
    ".claude/settings.json",
)


def runners() -> list[pathlib.Path]:
    found: list[pathlib.Path] = []
    for pattern in RUNNER_PATTERNS:
        found.extend(path for path in ROOT.glob(pattern) if path.is_file())
    return found


def unwired() -> list[str]:
    invoked = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in runners())
    return [
        path.name
        for path in sorted(VALIDATORS.glob("*.py"))
        if not path.name.startswith(("test_", "_")) and path.name not in invoked
    ]


def main() -> int:
    where = runners()
    if not where:
        print("NOT checked: no workflow or task runner was found, so nothing could be read")
        print(f"as an invocation. Looked for: {', '.join(RUNNER_PATTERNS)}")
        return 0

    missing = unwired()
    total = len([p for p in VALIDATORS.glob("*.py") if not p.name.startswith(("test_", "_"))])
    if missing:
        print(f"Validators nothing invokes ({len(missing)} of {total}):")
        for name in missing:
            print(f"  - validate/{name}")
        print("\nWire it into CI or delete it. A check written and never run reads as enforcement")
        print("while enforcing nothing, which is worse than not having written it.")
        return 1

    print(f"OK: all {total} validators are invoked, across {len(where)} runner file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
