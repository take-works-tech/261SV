"""Single-source-of-truth gate for constants in sim-viewer.

The same named constant defined in two files is the defect that produces the longest debugging
sessions in this kind of codebase, because nothing about it looks wrong. Both definitions are
correct-looking, both are reachable, and the day one of them is edited the other keeps serving the
old value to whoever imports it. Parity tests find this **after** it has diverged; this finds it when
the second definition is written.

Two shapes are reported, and both are the same defect at different stages:

  contradiction  the same name bound to different values in different files - already diverged
  copy           the same name bound to the same value in different files - diverging next week

What is scanned: module-level `UPPER_SNAKE = literal` in Python, and `const`/`export const`
`UPPER_SNAKE = literal` in TypeScript and JavaScript. Only literals, because a name bound to an
expression is usually a derivation rather than a second source, and a gate that cannot tell the
difference gets switched off.

**Exemptions are written here, in the open.** A name in EXEMPT is a decision somebody made and can be
read; a baseline file that accumulates silently is how a gate stops meaning anything.

Exit code: 0 clean, 1 duplicates found. Stdlib only.
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]

SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx")
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", ".next", "archive", "__pycache__", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "site-packages",
}

# Names that legitimately appear in more than one file. Each entry is a decision, not a workaround:
# add one only when the second definition is genuinely a different thing that happens to share a name.
EXEMPT: frozenset[str] = frozenset({"__all__", "TYPE_CHECKING"})

_PY = re.compile(r"^([A-Z][A-Z0-9_]{2,})\s*(?::[^=]+)?=\s*(.+?)\s*(?:#.*)?$")
_TS = re.compile(r"^(?:export\s+)?const\s+([A-Z][A-Z0-9_]{2,})\s*(?::[^=]+)?=\s*(.+?)\s*(?://.*)?;?$")
_LITERAL = re.compile(r"""^(?:[-+]?\d[\d_]*(?:\.\d+)?(?:[eE][-+]?\d+)?|"[^"]*"|'[^']*'|True|False|None|true|false|null)$""")


def _sources() -> list[pathlib.Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.suffix in SOURCE_SUFFIXES
        and path.is_file()
        and not any(part in SKIP_DIRS for part in path.parts)
    ]


def definitions() -> dict[str, list[tuple[str, str]]]:
    """name -> [(relative path, literal value)] for every module-level constant definition."""
    found: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in _sources():
        pattern = _PY if path.suffix == ".py" else _TS
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for raw in lines:
            if raw[:1].isspace():
                continue  # indented: a local or a class attribute, not a module-level source of truth
            match = pattern.match(raw.strip() if path.suffix != ".py" else raw)
            if not match:
                continue
            name, value = match.group(1), match.group(2).strip()
            if name in EXEMPT or not _LITERAL.match(value):
                continue
            found[name].append((str(path.relative_to(ROOT)).replace("\\", "/"), value))
    return found


def main() -> int:
    contradictions: list[str] = []
    copies: list[str] = []

    for name, sites in sorted(definitions().items()):
        if len(sites) < 2:
            continue
        values = {value for _, value in sites}
        where = ", ".join(f"{path} = {value}" for path, value in sites)
        (contradictions if len(values) > 1 else copies).append(f"{name}: {where}")

    if contradictions:
        print(f"Contradicting definitions ({len(contradictions)}):")
        for line in contradictions:
            print(f"  - {line}")
        print("\nThese already disagree. One of them is serving a stale value to its importers.")
    if copies:
        print(f"\nDuplicated definitions ({len(copies)}):")
        for line in copies:
            print(f"  - {line}")
        print("\nThese agree today. Keep one, import it from the other, or add the name to EXEMPT")
        print("with the reason - an exemption anybody can read beats a baseline nobody rereads.")

    if contradictions or copies:
        return 1
    print("OK: every constant is defined in one place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
