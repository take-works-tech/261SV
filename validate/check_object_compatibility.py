"""CT-012: every object this product can meet has a stated disposition, and the code agrees with it.

A compatibility table is worth nothing if a type can arrive that it does not mention. Three ways that
happens, and this gate closes all three:

* **the toolkit grows one** - a VTK upgrade adds a data object type and every table written against the
  old list silently stops being total. The measured list in `spike/object_types.json` is compared
  against the contract, so the upgrade fails here rather than in a reader six months later;
* **the code accepts one the contract does not** - `engine.reader` names the classes it reads, and a
  class read but not marked `read` is a capability nobody decided;
* **the executable copy drifts** - `src/domain_core/object_compatibility.py` is generated from the
  contract so that a disposition and a refusal reason exist once. This gate regenerates it and compares,
  which is what makes a checked-in generated file safe. `--write` regenerates it after the contract
  changes;
* **a conversion is left unsaid** - a table with holes is read as a table whose holes are permitted, so
  every ordered pair of view object types must appear, allowed or refused with a reason.

The view object types are checked against CT-004's own enumeration rather than a copy, because two
lists of the same thing disagree eventually and the one nobody reads is the one that drifts.

Exit 0 when everything holds, 1 when it does not, 3 when a measurement it needs is absent - never
silence read as coverage.
"""

from __future__ import annotations

import json
import re
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "specs" / "contracts" / "schema" / "CT-012.json"
VIEW_SCHEMA = ROOT / "specs" / "contracts" / "schema" / "CT-004.json"
MEASURED_TYPES = ROOT / "spike" / "object_types.json"
READER = ROOT / "src" / "engine" / "reader.py"
GENERATED = ROOT / "src" / "domain_core" / "object_compatibility.py"

DISPOSITIONS = {"read", "convert", "decompose", "refuse"}


HEADER = '''"""What this product does with each data object type it may be handed (CT-012).

**Generated from `specs/contracts/schema/CT-012.json` by `validate/check_object_compatibility.py --write`.**
Do not edit: `validate/check_object_compatibility.py` regenerates this file and fails if it differs, so
an edit here is a build failure rather than a divergence nobody notices. Change the contract instead.

A closed table with a default of refusal. A type absent from it is a type the product would meet without
a decision having been made about it, which is why the gate compares the keys against the toolkit's own
measured list (E-132) as well as against this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Disposition(str, Enum):
    """What happens to a data object of a given type."""

    READ = "read"              # accepted as it stands
    CONVERT = "convert"        # accepted after one named conversion, whose cost is stated
    DECOMPOSE = "decompose"    # taken apart into the parts of one @Case
    REFUSE = "refuse"          # named and refused; never approximated, never silently emptied


@dataclass(frozen=True, slots=True)
class Handling:
    """One row of CT-012's data-object table."""

    disposition: Disposition
    # `convert` only: the filter chain CT-012 names, and what running it costs.
    via: str | None = None
    costs: str | None = None
    # `refuse` only: why, in the words the user is shown.
    reason: str | None = None
    # `decompose` only: what it comes apart into.
    into: str | None = None

    @property
    def is_accepted(self) -> bool:
        return self.disposition is not Disposition.REFUSE


HANDLING: dict[str, Handling] = {
'''

FOOTER = '''}


def handling(class_name: str) -> Handling:
    """CT-012's row for a class, or a refusal that says the table has a hole rather than guessing."""
    found = HANDLING.get(class_name)
    if found is None:
        raise KeyError(
            f"{class_name} is not in CT-012's table. The table is meant to be total, so this is a "
            "defect in the contract and not a permission: add a disposition for it"
        )
    return found
'''


def literal(value: str | None) -> str:
    return "None" if value is None else json.dumps(value, ensure_ascii=False)


_CROSS_REFERENCE = re.compile(r"^as (vtk\w+)(, .*)?$")


def resolve(text: str | None, table: dict, seen: tuple[str, ...] = ()) -> str | None:
    """Turn a contract's cross-reference into the words it points at.

    "as vtkGraph" is good prose in a document a person reads and tells nobody anything in an error
    message, which is where these strings end up. So the contract keeps the reference and the generated
    copy carries the resolved text - one authored definition, usable at both ends.
    """
    if not text:
        return text
    match = _CROSS_REFERENCE.match(text.strip())
    if match is None:
        return text
    target, remainder = match.group(1), (match.group(2) or "")
    if target in seen or target not in table:
        return text
    entry = table[target]
    pointed = entry.get("reason") or entry.get("costs") or entry.get("note")
    resolved = resolve(pointed, table, seen + (target,))
    if not resolved:
        return text
    return f"{resolved}（{target} と同じ）{remainder}".rstrip()


def render() -> str:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    table = contract["dataObjectTypes"]
    lines = [HEADER]
    for name, entry in table.items():
        entry = dict(entry)
        for key in ("reason", "costs"):
            if entry.get(key):
                entry[key] = resolve(entry[key], table)
        disposition = entry["disposition"].upper()
        fields = [f"Disposition.{disposition}"]
        for key in ("via", "costs", "reason", "into"):
            if entry.get(key) is not None:
                fields.append(f"{key}={literal(entry[key])}")
        rendered = ", ".join(fields)
        lines.append(f"    {json.dumps(name)}: Handling(\n        {rendered},\n    ),\n")
    lines.append(FOOTER)
    return "".join(lines)



def findings() -> list[str]:
    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    # 0 - the executable copy is the contract, not a hand-maintained echo of it
    if not GENERATED.exists() or GENERATED.read_text(encoding="utf-8") != render():
        problems.append(
            "src/domain_core/object_compatibility.py is not what CT-012 generates. It is a build "
            "artefact, so the fix is `python validate/check_object_compatibility.py --write`, not an "
            "edit to the file"
        )
    stated = contract["dataObjectTypes"]

    # 1 - every disposition is one of the four, and says enough to act on
    for name, entry in stated.items():
        disposition = entry.get("disposition")
        if disposition not in DISPOSITIONS:
            problems.append(f"{name} has disposition '{disposition}', which is not one of {sorted(DISPOSITIONS)}")
            continue
        if disposition == "convert" and not (entry.get("via") and entry.get("costs")):
            problems.append(
                f"{name} is converted but does not say by what and at what cost; a conversion whose "
                "price is unstated is one nobody can refuse"
            )
        if disposition == "refuse" and not entry.get("reason"):
            problems.append(f"{name} is refused with no reason; a refusal that gives no reason reads as an oversight")
        if disposition == "decompose" and not entry.get("into"):
            problems.append(f"{name} is decomposed but does not say into what - a part and a partition are not the same")

    # 2 - the toolkit's own list, as measured, is covered
    measured = json.loads(MEASURED_TYPES.read_text(encoding="utf-8"))
    names = {entry["class"] for entry in measured["data_object_types"]}
    for missing in sorted(names - set(stated)):
        problems.append(
            f"{missing} exists in VTK {measured['vtk_version']} and CT-012 does not mention it: the table "
            "is not total, and an unmentioned type is one the product meets without a decision"
        )

    # 3 - what the reader actually accepts is what the contract says it accepts
    source = READER.read_text(encoding="utf-8")
    accepted = set(re.findall(r"isinstance\(data, (vtk\w+)\)", source))
    for name in sorted(accepted):
        entry = stated.get(name)
        if entry is None:
            problems.append(f"engine/reader.py reads {name}, which CT-012 does not mention")
        elif entry["disposition"] != "read":
            problems.append(
                f"engine/reader.py reads {name} directly, but CT-012 says '{entry['disposition']}'"
            )
    for name, entry in stated.items():
        if entry["disposition"] == "read" and name not in accepted and entry.get("as") != "rows":
            problems.append(
                f"CT-012 says {name} is read as it stands and engine/reader.py accepts no such class; "
                "a promised capability with no code behind it is the kind CI is supposed to catch"
            )

    # 4 - the view object types are CT-004's, and the conversion table is total over them
    view_schema = json.loads(VIEW_SCHEMA.read_text(encoding="utf-8"))
    declared = set(_object_type_enum(view_schema))
    described = set(contract["viewObjectTypes"])
    for missing in sorted(declared - described):
        problems.append(f"CT-004 defines the view object type '{missing}' and CT-012 says nothing about it")
    for extra in sorted(described - declared):
        problems.append(f"CT-012 describes the view object type '{extra}', which CT-004 does not define")

    conversions = contract["conversions"]
    reasons = conversions["refusedReasons"]
    stated_pairs: dict[tuple[str, str], str] = {}
    for allowed in conversions["allowed"]:
        stated_pairs[(allowed["from"], allowed["to"])] = "allowed"
    for refused in conversions["refused"]:
        pair = (refused["from"], refused["to"])
        if pair in stated_pairs:
            problems.append(f"{pair[0]} -> {pair[1]} is both allowed and refused")
        if refused["reason"] not in reasons:
            problems.append(f"{pair[0]} -> {pair[1]} is refused for '{refused['reason']}', which is not a stated reason")
        stated_pairs[pair] = "refused"
    for pair in product(sorted(described), repeat=2):
        if pair not in stated_pairs:
            problems.append(
                f"{pair[0]} -> {pair[1]} appears nowhere in the conversion table; a table with holes is "
                "read as a table whose holes are permitted"
            )

    return problems


def _object_type_enum(schema: dict) -> list[str]:
    """CT-004's own list of view object types, wherever in the schema it sits."""
    found: list[str] = []

    def walk(node: object, key: str = "") -> None:
        if isinstance(node, dict):
            if key == "objectType" and isinstance(node.get("enum"), list):
                found.extend(node["enum"])
            for name, value in node.items():
                walk(value, name)
        elif isinstance(node, list):
            for value in node:
                walk(value, key)

    walk(schema)
    return found


def main() -> int:
    if "--write" in sys.argv:
        GENERATED.write_text(render(), encoding="utf-8")
        print(f"wrote {GENERATED.relative_to(ROOT).as_posix()} from CT-012")
        return 0
    for needed in (CONTRACT, VIEW_SCHEMA, READER):
        if not needed.exists():
            print(f"check_object_compatibility: {needed.relative_to(ROOT).as_posix()} is missing.")
            return 3
    if not MEASURED_TYPES.exists():
        print(
            "check_object_compatibility: spike/object_types.json is missing, so the contract could not "
            "be checked against the toolkit's own list.\n"
            "  Run spike/measure_object_types.py in a prepared spike environment.\n"
            "  Refusing to report success for a check that did not run."
        )
        return 3

    problems = findings()
    for problem in problems:
        print(f"check_object_compatibility: {problem}")
    if problems:
        print(f"\n{len(problems)} finding(s).")
        return 1
    print("Object compatibility holds: every type has a disposition and every conversion is stated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
