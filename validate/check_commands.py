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
SURFACE_SCHEMA = ROOT / "specs" / "contracts" / "schema" / "CT-002.json"
SOURCE = ROOT / "src"
GENERATED = ROOT / "src" / "service" / "command" / "catalogue.py"
NEWLINE = chr(10)
UI_DIRECTORIES = ("ui", "shell")

OPERATION_ROW = re.compile(r"^\|\s*`([a-zA-Z]+\.[a-zA-Z]+)`\s*\|")
FULL_ROW = re.compile(r"^\|\s*`([a-zA-Z]+\.[a-zA-Z]+)`\s*\|([^|]*)\|")
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


def catalogue_rows() -> list[tuple[str, bool]]:
    """Each operation with whether it writes, from the CT-003 table's second column."""
    rows: list[tuple[str, bool]] = []
    for line in CATALOGUE.read_text(encoding="utf-8").splitlines():
        match = FULL_ROW.match(line.strip())
        if match:
            rows.append((match.group(1), "write" in match.group(2).lower()))
    return rows


def operation_parameters() -> dict[str, dict]:
    """The per-operation parameter schemas of CT-003 (OPEN-028's answer).

    Absent means the contract does not say what an operation takes, which is the state this repository
    was in until 2026-08-25 and is reported rather than treated as "no parameters".
    """
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return schema.get("$defs", {}).get("operationParameters", {}).get("properties", {})


def check_parameters_are_stated(findings: list[Finding]) -> None:
    """Every catalogue operation says what it takes, in a form something can check."""
    stated = operation_parameters()
    if not stated:
        findings.append(
            Finding(
                SCHEMA.name,
                "no per-operation parameter schemas: nothing can compare a handler's declaration "
                "against the contract, so CT-002's promise about unknown parameters is kept against "
                "whatever the handler happened to declare (OPEN-028)",
            )
        )
        return
    for name in catalogue_operations():
        if name not in stated:
            findings.append(Finding(SCHEMA.name, f"{name} has no parameter schema"))
    for name in stated:
        if name not in catalogue_operations():
            findings.append(Finding(SCHEMA.name, f"{name} has a parameter schema and is not in the catalogue"))


def render() -> str:
    """The catalogue as a Python module the product can import.

    Generated rather than parsed at run time: a shipped product that read a specification file to learn
    what its own operations are would fail wherever the specification is not installed, which is
    everywhere it is installed.
    """
    rows = catalogue_rows()
    writes = [name for name, is_write in rows if is_write]
    reads = [name for name, is_write in rows if not is_write]
    stated = operation_parameters()
    answers = operation_results()

    def declared(name: str) -> tuple[list[str], list[str]]:
        one = stated.get(name, {})
        return sorted(one.get("properties", {})), sorted(one.get("required", []))

    def answered(name: str) -> tuple[list[str], list[str]]:
        one = answers.get(name, {})
        return sorted(one.get("properties", {})), sorted(one.get("required", []))
    lines = [
        '"""The operation catalogue of CT-003, as code.',
        "",
        "**Generated from `specs/contracts/CT-003_engine_api.md` by",
        "`validate/check_commands.py --write`.** Do not edit by hand: the gate compares this file",
        "against the contract on every run, so an edit here fails the build rather than changing",
        "anything.",
        "",
        "The set is closed. An operation not in it is refused rather than attempted, which is what",
        "CT-002 promises happens to an unknown command - and the refusal is what stops a caller",
        "believing it disabled something when it merely misspelled it.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "#: Operations that change state. Each enters the undo history and may need authorisation.",
        "WRITES = frozenset({",
        *[f'    "{name}",' for name in writes],
        "})",
        "",
        "#: Operations that only answer. A read never needs confirmation and never enters undo.",
        "READS = frozenset({",
        *[f'    "{name}",' for name in reads],
        "})",
        "",
        "#: Every operation this build knows the name of, in the order the contract lists them.",
        "OPERATIONS = (",
        *[f'    "{name}",' for name, _ in rows],
        ")",
        "",
        "#: What each operation accepts, and which of those it requires. From CT-003's per-operation",
        "#: schemas, so a handler is checked against the **contract** rather than against its own",
        "#: declaration - which is what CT-002 promises when it says an unknown parameter is rejected.",
        "PARAMETERS: dict[str, tuple[frozenset[str], frozenset[str]]] = {",
        *[
            f'    "{name}": (frozenset({declared(name)[0]!r}), frozenset({declared(name)[1]!r})),'
            for name, _ in rows
        ],
        "}",
        "",
        "#: What each operation **answers**, and which of those fields it must carry. From CT-003's",
        "#: per-operation result schemas. A handler is checked against these the way a caller is checked",
        "#: against PARAMETERS: the contract states the answer, so a build cannot return a value the",
        "#: caller has no type for, nor omit a unit the contract requires beside a number (XC-003).",
        "RESULT_FIELDS: dict[str, tuple[frozenset[str], frozenset[str]]] = {",
        *[
            f'    "{name}": (frozenset({answered(name)[0]!r}), frozenset({answered(name)[1]!r})),'
            for name, _ in rows
        ],
        "}",
        "",
        "",
        "def writes(operation: str) -> bool:",
        '    """Whether an operation changes state. Unknown operations raise rather than defaulting.',
        "",
        "    Defaulting either way is wrong in a way that is hard to see: defaulting to read lets a",
        "    write escape the undo history, and defaulting to write puts a question in front of an",
        "    answer somebody just asked for.",
        '    """',
        "    if operation in WRITES:",
        "        return True",
        "    if operation in READS:",
        "        return False",
        "    raise KeyError(operation)",
        "",
    ]
    return NEWLINE.join(lines)


def check_surface_and_wire_agree(findings: list[Finding]) -> None:
    """AC-010: the same set in CT-002 and in CT-003, with neither holding an operation the other does not.

    Checked by reference rather than by comparison. CT-002's `command` points at CT-003's enumeration,
    so the two cannot hold different sets - there is only one set. An unconstrained string here would
    accept an unknown command, which is the one thing CT-002's own prose says it refuses, and a second
    copy of the enumeration would be the copy that stopped agreeing.
    """
    schema = json.loads(SURFACE_SCHEMA.read_text(encoding="utf-8"))
    command = schema.get("properties", {}).get("command", {})
    reference = command.get("$ref")
    if reference == "CT-003.json#/properties/operation":
        return
    if "enum" in command:
        catalogue = catalogue_operations()
        listed = list(command["enum"])
        for name in [n for n in catalogue if n not in listed]:
            findings.append(
                Finding(SURFACE_SCHEMA.name, f"{name} is in CT-003 and not in the CT-002 surface")
            )
        for name in [n for n in listed if n not in catalogue]:
            findings.append(
                Finding(SURFACE_SCHEMA.name, f"{name} is in the CT-002 surface and not in CT-003")
            )
        return
    findings.append(
        Finding(
            SURFACE_SCHEMA.name,
            "`command` is an unconstrained string: CT-002 cannot refuse an unknown command, which is "
            "what its own prose says it does. Point it at CT-003's enumeration "
            "($ref CT-003.json#/properties/operation) rather than repeating the list",
        )
    )


def check_generated_matches(findings: list[Finding]) -> bool:
    """The checked-in catalogue module against the contract it was generated from.

    Returns False where there is no source tree to check - which is reported as a blind spot, never as
    a pass. A gate that finds nothing and reports success is worse than no gate, because it is believed.
    """
    if not SOURCE.is_dir():
        return False
    if not GENERATED.exists():
        findings.append(Finding(GENERATED.name, "the generated catalogue is missing: run --write"))
        return
    if GENERATED.read_text(encoding="utf-8") != render():
        findings.append(
            Finding(
                GENERATED.name,
                "the generated catalogue disagrees with CT-003. It is an artefact, so the fix is "
                "`python validate/check_commands.py --write`, not an edit here",
            )
        )
    return True


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


def screen_state_ids() -> set[str]:
    """`screen.variant` ids from the required-screen-states table of the interface specification."""
    if not UI_SPEC.exists():
        return set()
    text = UI_SPEC.read_text(encoding="utf-8")
    marker = "### Required screen states"
    if marker not in text:
        return set()
    section = text.split(marker, 1)[1]
    ids: set[str] = set()
    for line in section.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            break
        if line.startswith("|"):
            ids.update(re.findall(r"`([a-z]+\.[a-z0-9-]+)`", line.split("|")[1]))
    return ids


def check_mentions_resolve(findings: list[Finding]) -> None:
    """An operation named in prose that does not exist is a reference to something nobody implements.

    `screen.variant` and `family.operation` are the same shape, so a screen state reads as an
    unimplemented command unless this check knows the other vocabulary. It learns it: the ids are read
    from the required-screen-states table of `specs/11_ui.md` and are known everywhere, in any file.

    Skipping that one section was the first attempt and was wrong in the ordinary way - it silenced
    the table and nothing else, so the same ids named in `08_decisions.md`, where the decision about
    them is recorded, still read as thirteen missing commands. A rule that holds only where the list
    is written is not a rule about the list. The ids are not renamed to suit the gate either: they are
    the catalogue keys and the mockup's URL parameters, and bending them here would make the gate the
    thing the design works around.
    """
    known = set(catalogue_operations()) | screen_state_ids()
    for path in sorted((ROOT / "specs").rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
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


def operation_results() -> dict[str, dict]:
    """The per-operation result schemas of CT-003.

    Absent means the contract does not say what an operation **answers** - the state this repository was
    in until 2026-08-25, when `result` was `additionalProperties: true` for all of them and every type
    generated above the service would have been `any`.
    """
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return schema.get("$defs", {}).get("operationResults", {}).get("properties", {})


def check_results_are_stated(findings: list[Finding]) -> None:
    """Every catalogue operation says what it answers, in a form something can check."""
    stated = operation_results()
    if not stated:
        findings.append(
            Finding(
                SCHEMA.name,
                "no per-operation result schemas: the contract says what each operation takes and not "
                "what it returns, so nothing can check that an answer carries a unit or a provenance",
            )
        )
        return
    catalogue = catalogue_operations()
    for name in catalogue:
        if name not in stated:
            findings.append(Finding(SCHEMA.name, f"{name} has no result schema"))
    for name in stated:
        if name not in catalogue:
            findings.append(
                Finding(SCHEMA.name, f"{name} has a result schema and is not in the catalogue")
            )


#: Number-typed result fields whose **name** carries the unit, in the manner GL-020 asks for. Listed
#: rather than inferred from a suffix: a rule that read a trailing capital would accept `deltaT` as
#: metres, and being able to say which fields these are is the point of the list.
NAMED_UNIT_FIELDS = frozenset({"minM", "maxM"})


def _number_fields(node: object, path: str = "") -> list[tuple[str, dict]]:
    """Every number-typed leaf in a schema, with the path that reaches it."""
    found: list[tuple[str, dict]] = []
    if isinstance(node, dict):
        kind = node.get("type")
        kinds = kind if isinstance(kind, list) else [kind]
        if "number" in kinds:
            found.append((path, node))
        for name, child in (node.get("properties") or {}).items():
            found += _number_fields(child, f"{path}.{name}" if path else name)
        if "items" in node:
            found += _number_fields(node["items"], f"{path}[]")
    return found


def _declares_unit(schema: dict, holder: str) -> bool:
    """Whether the object at `holder`, or any object enclosing it, declares a `unit`.

    Enclosing counts: a graph series states the unit once and its points carry the numbers (AC-002), and
    requiring it on every point would be a second answer to the same question.
    """
    node: object = schema
    seen: list[object] = [node]
    for part in [p for p in holder.split(".") if p]:
        if not isinstance(node, dict):
            return False
        node = (node.get("properties") or {}).get(part.removesuffix("[]"), {})
        if part.endswith("[]") and isinstance(node, dict):
            node = node.get("items", {})
        seen.append(node)
    return any(isinstance(one, dict) and "unit" in (one.get("properties") or {}) for one in seen)


def check_results_declare_units(findings: list[Finding]) -> None:
    """A number in an answer arrives with its unit, or this gate names the one that does not (XC-003).

    Prose could ask for this; a schema can require it. A number-typed field is accepted where the object
    holding it - or one enclosing it - also declares a `unit`, where the field's own name carries the
    unit, or where the schema bounds it to a ratio. Every other one is named here rather than found
    later in a report that printed a bare figure.

    Integers are exempt by type: counts are dimensionless and stay integers (INV-015).
    """
    for operation, schema in operation_results().items():
        for path, node in _number_fields(schema):
            leaf = path.rsplit(".", 1)[-1].removesuffix("[]")
            if leaf in NAMED_UNIT_FIELDS:
                continue
            if node.get("minimum") == 0 and node.get("maximum") == 1:
                continue  # a ratio, bounded in the schema itself
            holder = path.rsplit(".", 1)[0] if "." in path else ""
            if _declares_unit(schema, holder):
                continue
            findings.append(
                Finding(
                    SCHEMA.name,
                    f"{operation} answers with a bare number at '{path}': no unit beside it, none in "
                    "its name, and no bound making it a ratio. A value shown without its unit is a "
                    "value in whatever unit the reader assumed (XC-003)",
                )
            )


def unchecked(generated_checked: bool = True) -> list[str]:
    """What this gate could not examine. Printed every run, never silently omitted."""
    gaps: list[str] = []
    if not generated_checked:
        gaps.append(
            "the generated catalogue against CT-003: there is no src/ tree here, so "
            f"{GENERATED.relative_to(ROOT).as_posix()} was not compared"
        )

    if interface_directories():
        # Interface code exists, and this gate reads filenames, not TypeScript. Examining the
        # component names is not examining what an action dispatches - saying so is the difference
        # between a blind spot and a silence that reads as coverage.
        gaps.append(
            "interface actions dispatching commands (operations/AC-011): this gate matches component "
            "filenames and parses no TypeScript, so whether an action goes through the command "
            "surface was not examined"
        )
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
    if "--write" in sys.argv:
        GENERATED.write_text(render(), encoding="utf-8")
        print(f"wrote {GENERATED.relative_to(ROOT).as_posix()} from CT-003")
        return 0

    findings: list[Finding] = []
    check_catalogue_matches_schema(findings)
    check_parameters_are_stated(findings)
    check_results_are_stated(findings)
    check_results_declare_units(findings)
    check_surface_and_wire_agree(findings)
    generated_checked = check_generated_matches(findings)
    check_mentions_resolve(findings)
    check_components_are_unique(findings)

    for finding in findings:
        print(finding)

    print()
    print(f"Checked: {len(catalogue_operations())} operations in the CT-003 catalogue.")
    for gap in unchecked(generated_checked):
        print(f"NOT checked: {gap}")
    print()

    if findings:
        print(f"{len(findings)} finding(s).")
        return 1
    print("Command surface consistent, for what could be checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
