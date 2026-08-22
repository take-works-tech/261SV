"""Gate: the command surface is one set, everywhere it is written down.

INV-006 says the interface, the assistant, a script and a pipeline all act through one command surface.
That has been prose in three files. Prose does not fail a build, and an invariant nothing can fail is
an invariant on its way to being false.

What this gate checks today:

  1. the operation catalogue in CT-003 against the enumeration in its JSON schema - a schema that
     accepts any string cannot refuse an unknown command, which is what CT-002 promises it does
  2. every operation named in the specification prose resolves to one in the catalogue

What it cannot check yet, and says so rather than passing: there is no interface code, so nothing can be
asserted about interface actions dispatching commands (operations/AC-011). **A gate that finds nothing
and reports success is worse than no gate**, because it is believed - so this one prints its blind spots
every run, and its exit status covers only what it actually examined.

Specification: specs/features/operations/spec.md REQ-004, XC-127, INV-006.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "specs" / "contracts" / "CT-003_engine_api.md"
UI_SPEC = ROOT / "specs" / "11_ui.md"
SCHEMA = ROOT / "specs" / "contracts" / "schema" / "CT-003.json"
SOURCE = ROOT / "src"
UI_DIRECTORIES = ("ui", "shell")

OPERATION_ROW = re.compile(r"^\|\s*`([a-zA-Z]+\.[a-zA-Z]+)`\s*\|")
OPERATION_MENTION = re.compile(r"`([a-z][a-zA-Z]*\.[a-z][a-zA-Z]*)`")

# Words that look like an operation and are not: file suffixes, module paths, attribute access in
# example code. Matching the shape alone would report every one of them as a missing command.
NOT_OPERATIONS = re.compile(r"\.(json|md|py|ts|tsx|js|csv|vtk|vtu|exo|case|yaml|yml|toml|html|png|mp4)$")


@dataclass(frozen=True)
class Finding:
    where: str
    message: str

    def __str__(self) -> str:
        return f"[commands] {self.where}: {self.message}"


def catalogue_operations() -> list[str]:
    """Operation names from the CT-003 table, in the order the contract lists them."""
    operations: list[str] = []
    for line in CATALOGUE.read_text(encoding="utf-8").splitlines():
        match = OPERATION_ROW.match(line.strip())
        if match:
            operations.append(match.group(1))
    return operations


def schema_operations() -> list[str] | None:
    """The enumeration the schema constrains `operation` to, or None if it constrains nothing."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    operation = schema.get("properties", {}).get("operation", {})
    values = operation.get("enum")
    return list(values) if isinstance(values, list) else None


def check_catalogue_matches_schema(findings: list[Finding]) -> bool:
    operations = catalogue_operations()
    if not operations:
        findings.append(Finding(CATALOGUE.name, "no operations found: the catalogue table did not parse"))
        return False

    enumerated = schema_operations()
    if enumerated is None:
        findings.append(
            Finding(
                SCHEMA.name,
                "`operation` is an unconstrained string: an unknown command cannot be refused by the "
                "schema, which is what CT-002 says happens to it",
            )
        )
        return True

    missing = [name for name in operations if name not in enumerated]
    extra = [name for name in enumerated if name not in operations]
    for name in missing:
        findings.append(Finding(SCHEMA.name, f"{name} is in the catalogue and not in the schema enumeration"))
    for name in extra:
        findings.append(Finding(CATALOGUE.name, f"{name} is in the schema enumeration and not in the catalogue"))
    return True


def check_mentions_resolve(findings: list[Finding]) -> None:
    """An operation named in prose that does not exist is a reference to something nobody implements.

    `screen.variant` and `family.operation` are the same shape, so the required-screen-states table of
    `specs/11_ui.md` reads as thirteen unimplemented commands unless this check knows what it is
    looking at. The section is skipped by name rather than by renaming the ids: those ids are the
    catalogue keys and the mockup's URL parameters, and bending them to satisfy a gate would make the
    gate the thing the design has to work around.
    """
    known = set(catalogue_operations())
    for path in sorted((ROOT / "specs").rglob("*.md")):
        in_screen_states = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.startswith("### Required screen states"):
                in_screen_states = True
                continue
            if in_screen_states:
                # The table ends at the next heading of the same level or above.
                if line.startswith("## ") or line.startswith("### "):
                    in_screen_states = False
                else:
                    continue
            for match in OPERATION_MENTION.finditer(line):
                name = match.group(1)
                if name in known or NOT_OPERATIONS.search(name):
                    continue
                prefix = name.split(".", 1)[0]
                if not any(operation.startswith(prefix + ".") for operation in known):
                    continue
                findings.append(
                    Finding(
                        f"{path.relative_to(ROOT)}:{number}",
                        f"`{name}` looks like a command of the `{prefix}` family and is not in the catalogue",
                    )
                )


def shared_components() -> list[str]:
    """Component names from the shared-components table of the interface specification."""
    if not UI_SPEC.is_file():
        return []
    names: list[str] = []
    in_table = False
    for line in UI_SPEC.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("| Component |"):
            in_table = True
            continue
        if in_table:
            if not stripped.startswith("|"):
                break
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and cells[0] and set(cells[0]) - set("- :"):
                names.append(cells[0])
    return names


def interface_directories() -> list[Path]:
    return [
        SOURCE / directory
        for directory in UI_DIRECTORIES
        if (SOURCE / directory).is_dir() and any((SOURCE / directory).rglob("*"))
    ]


def check_components_are_unique(findings: list[Finding]) -> bool:
    """Each named component exists once, in the module that owns it (XC-015).

    Returns False when there is no interface to examine - which is reported, never treated as a pass.
    """
    directories = interface_directories()
    if not directories:
        return False
    for name in shared_components():
        slug = name.lower().replace(" ", "").replace("-", "")
        matches = [
            path
            for directory in directories
            for path in directory.rglob("*")
            if path.is_file() and slug == path.stem.lower().replace("-", "").replace("_", "")
        ]
        if len(matches) > 1:
            where = ", ".join(str(path.relative_to(ROOT)) for path in matches)
            findings.append(Finding(UI_SPEC.name, f"'{name}' has more than one implementation: {where}"))
    return True


def unchecked() -> list[str]:
    """What this gate could not examine. Printed every run, never silently omitted."""
    gaps: list[str] = []
    if not interface_directories():
        gaps.append(
            "interface actions dispatching commands (operations/AC-011): no interface code exists yet, "
            f"so nothing was examined under {', '.join(f'src/{d}' for d in UI_DIRECTORIES)}"
        )
        found = len(shared_components())
        gaps.append(
            "shared components having one implementation each (operations/AC-024): the "
            f"{found} components of 11_ui.md were not examined, for the same reason"
            if found
            else "shared components (operations/AC-024): 11_ui.md was not found, so no component list was read"
        )
    gaps.append(
        "keyboard reachability (operations/AC-013): the scheme is specified in prose and has no "
        "machine-readable form to check against"
    )
    return gaps


def main() -> int:
    findings: list[Finding] = []
    check_catalogue_matches_schema(findings)
    check_mentions_resolve(findings)
    check_components_are_unique(findings)

    for finding in findings:
        print(finding)

    print()
    print(f"Checked: {len(catalogue_operations())} operations in the CT-003 catalogue.")
    for gap in unchecked():
        print(f"NOT checked: {gap}")
    print()

    if findings:
        print(f"{len(findings)} finding(s).")
        return 1
    print("Command surface consistent, for what could be checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
