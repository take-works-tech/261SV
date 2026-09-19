"""Every command the interface writes down is one the contract accepts, with the parameters it takes.

The screens dispatch commands as literals - `submit({ operation: "view.render", parameters: { … } })`.
The typed client (`engine.submit`) is checked by the compiler against types generated from CT-003,
so a call through it cannot name a parameter the contract lacks. The design states' `submit` is not:
it logs and returns, and its literals were written before the contract settled, so they carry names
the contract refuses - `view.render {renderer}`, `dataset.load {file, action}` - and nothing said so
(#349). A design state is labelled as one and executes nothing, so the numbers are safe; what is not
safe is the day a screen is wired and its call is the first thing the engine refuses.

This reads the literals and holds them to the catalogue: the operation must exist, every parameter
named must be one the operation accepts, and every parameter the operation requires must be named.
The third is the strict one and it is deliberate: a literal that omits a required parameter is a call
that will be refused, and "the names are right" is not the same as "the call is right".

Exit 0 when every literal is a call the contract would accept, 1 with the list otherwise, 3 when the
interface source is absent.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from service.command.catalogue import OPERATIONS, PARAMETERS  # noqa: E402

UI = ROOT / "src" / "ui"
SKIP_PARTS = {"node_modules", "dist", "dist-preload", "client"}  # client/ is the typed side


@dataclass(frozen=True)
class Literal:
    file: Path
    line: int
    operation: str
    keys: tuple[str, ...]
    parameters_found: bool


def _matching_brace(text: str, start: int) -> int:
    """Index just past the brace that closes the one at `start`, skipping strings and templates."""
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char in "\"'`":
            quote = char
            index += 1
            while index < len(text) and text[index] != quote:
                if text[index] == "\\":
                    index += 1
                index += 1
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(text)


def _top_level_keys(object_text: str) -> tuple[str, ...]:
    """The keys of an object literal `{ a: 1, "b": x, ...spread }`, ignoring nested objects."""
    inner = object_text.strip()
    assert inner.startswith("{") and inner.endswith("}")
    inner = inner[1:-1]
    keys: list[str] = []
    depth = 0
    index = 0
    token = ""
    at_key = True
    while index < len(inner):
        char = inner[index]
        if char in "\"'`":
            quote = char
            end = index + 1
            while end < len(inner) and inner[end] != quote:
                if inner[end] == "\\":
                    end += 1
                end += 1
            if depth == 0 and at_key:
                token += inner[index + 1 : end]
            index = end + 1
            continue
        if char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif depth == 0:
            if char == ":" and at_key:
                name = token.strip()
                if name and not name.startswith("..."):
                    keys.append(name)
                token = ""
                at_key = False
            elif char == ",":
                if at_key and token.strip():
                    # shorthand property `{ viewId }`
                    name = token.strip()
                    if not name.startswith("..."):
                        keys.append(name)
                token = ""
                at_key = True
            elif at_key:
                token += char
        index += 1
    if at_key and token.strip() and not token.strip().startswith("..."):
        keys.append(token.strip())
    return tuple(keys)


def literals_in(file: Path) -> list[Literal]:
    text = file.read_text(encoding="utf-8")
    found: list[Literal] = []
    for match in re.finditer(r"\bsubmit\(\s*\{", text):
        start = match.end() - 1
        end = _matching_brace(text, start)
        body = text[start:end]
        operation = re.search(r"\boperation\s*:\s*[\"'`]([^\"'`]+)[\"'`]", body)
        if not operation:
            continue
        line = text.count("\n", 0, match.start()) + 1
        parameters = re.search(r"\bparameters\s*:\s*\{", body)
        if parameters:
            p_start = parameters.end() - 1
            p_end = _matching_brace(body, p_start)
            keys = _top_level_keys(body[p_start:p_end])
            found.append(Literal(file, line, operation.group(1), keys, True))
        else:
            found.append(Literal(file, line, operation.group(1), (), False))
    return found


def main(argv: list[str] | None = None) -> int:
    if not UI.exists():
        print("NOT checked: src/ui is absent, so there are no interface commands to read")
        return 3
    files = [
        path for path in UI.rglob("*.ts*")
        if not any(part in SKIP_PARTS for part in path.relative_to(UI).parts)
        and not path.name.endswith((".test.ts", ".test.tsx", ".d.ts"))
    ]
    literals = [one for path in sorted(files) for one in literals_in(path)]
    findings: list[str] = []
    for one in literals:
        where = f"{one.file.relative_to(ROOT).as_posix()}:{one.line}"
        if one.operation not in OPERATIONS:
            findings.append(f"{where}: '{one.operation}' is not an operation of CT-003")
            continue
        accepted, required = PARAMETERS[one.operation]
        unknown = [key for key in one.keys if key not in accepted]
        missing = [key for key in sorted(required) if key not in one.keys]
        if unknown:
            findings.append(f"{where}: {one.operation} does not take {unknown}; it takes {sorted(accepted)}")
        if missing:
            findings.append(f"{where}: {one.operation} requires {missing}, not named")
    for finding in findings:
        print(finding)
    print(f"Checked: {len(literals)} command literal(s) in {len(files)} interface file(s) against {len(OPERATIONS)} operations.")
    print(
        "NOT checked: calls through the typed client (state/engine.ts, client/): the compiler holds those to the "
        "generated types. Values are not checked, only names - a right name with a wrong value is the engine's to refuse."
    )
    if findings:
        print(f"{len(findings)} finding(s).")
        return 1
    print("Every interface command literal names an operation the contract has, with parameters it takes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
