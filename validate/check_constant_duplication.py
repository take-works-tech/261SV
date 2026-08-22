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


STYLE_SUFFIXES = (".css",)

# `--muted: #f1f4f6;`
_CUSTOM_PROPERTY = re.compile(r"(--[a-zA-Z][\w-]*)\s*:\s*([^;{}]+)")
# A colour written as a bare hex literal. Only hex: `rgb(15 34 47 / 10%)` and `oklch(...)` carry
# alpha and colour-space variants that are genuinely different values, not different spellings.
_HEX = re.compile(r"#([0-9a-fA-F]{3,8})\b")


def _expand_hex(digits: str) -> str:
    """The same colour, one spelling, so that two spellings of it can be told apart from two colours."""
    lowered = digits.lower()
    if len(lowered) in (3, 4):
        lowered = "".join(character * 2 for character in lowered)
    if len(lowered) == 8 and lowered.endswith("ff"):
        lowered = lowered[:6]
    return "#" + lowered


def _blocks(text: str) -> list[tuple[str, str]]:
    """(context, body) for every rule, where context includes the at-rules it is nested in.

    Nesting is why this is a parser and not a regular expression. A responsive override -
    `@media (max-width: 900px) { .area-tabs { --area-tab-width: 96px } }` - declares the same custom
    property as the base rule and is entirely correct; flattening the two into one block reports it as
    a duplicate. That false finding was written, run and caught here before it reached anybody.
    """
    found: list[tuple[str, str]] = []
    stack: list[str] = []
    buffer = ""
    for character in text:
        if character == "{":
            stack.append(buffer.strip().replace("\n", " "))
            buffer = ""
        elif character == "}":
            if stack:
                found.append((" > ".join(stack), buffer))
                stack.pop()
            buffer = ""
        else:
            buffer += character
    return found


def style_findings() -> tuple[list[str], list[str]]:
    """Custom properties declared twice in one block, and colours written more than one way."""
    duplicates: list[str] = []
    spellings: list[str] = []
    for path in [p for p in _sources_of(STYLE_SUFFIXES)]:
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for context, body in _blocks(text):
            seen: dict[str, list[str]] = defaultdict(list)
            for name, value in _CUSTOM_PROPERTY.findall(body):
                seen[name].append(value.strip())
            for name, values in sorted(seen.items()):
                if len(values) < 2:
                    continue
                verdict = "the last one wins and the others are dead" if len(set(values)) > 1 else "identical"
                duplicates.append(f"{relative} `{context}` declares {name} {len(values)} times: {values} - {verdict}")

        spelled: dict[str, set[str]] = defaultdict(set)
        for digits in _HEX.findall(text):
            spelled[_expand_hex(digits)].add("#" + digits.lower())
        for colour, forms in sorted(spelled.items()):
            if len(forms) > 1:
                spellings.append(f"{relative}: {colour} is written as {sorted(forms)}")
    return duplicates, spellings


def _sources_of(suffixes: tuple[str, ...]) -> list[pathlib.Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.suffix in suffixes
        and path.is_file()
        and not any(part in SKIP_DIRS for part in path.parts)
    ]


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

    duplicates, spellings = style_findings()
    if duplicates:
        print(f"\nStyle tokens declared more than once in one block ({len(duplicates)}):")
        for line in duplicates:
            print(f"  - {line}")
        print("\nOne name, one role. `--muted` here held both a light background and grey body text;")
        print("the second declaration won, so every shadcn `bg-muted` rendered dark and nothing said so.")
    if spellings:
        print(f"\nColours written more than one way ({len(spellings)}):")
        for line in spellings:
            print(f"  - {line}")
        print("\nOne notation per colour. Two spellings of white defeat every count and every search,")
        print("so a value that looks centralised is silently written out by hand in both forms.")

    print("\nNOT checked: whether a literal should have been a token at all. A colour equal to a")
    print("token's value may be that token used badly or a different thing that shares a value today,")
    print("and only a reader can tell (OPEN-021 carries the measured count).")

    if contradictions or copies or duplicates or spellings:
        return 1
    print("\nOK: every constant and style token is defined in one place, in one notation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
