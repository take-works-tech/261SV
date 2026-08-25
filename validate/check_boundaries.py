"""Enforce the module and layer boundaries the specification declares.

The specification is the single source: `specs/01_boundaries.md` names the layers, and each `MOD-` item
carries the layer it belongs to, the paths it owns, and the modules it may depend on. This script reads
that and checks the code against it, so the boundaries are a gate rather than a paragraph.

Three checks, matching the three ways a boundary decays:

1. **Ownership** - every source file belongs to exactly one module. A file owned by nobody is a file
   nobody reviews; a file owned twice means two modules believe they control it.
2. **Layer direction** - a module may import only from its own layer or below. An upward import is the
   defect that turns a layered design into a graph.
3. **Declared dependencies** - a module may import only from modules it lists in `depends_on`. This is
   what keeps the blast radius of a change equal to the reverse-dependency set.

Usage:  python validate/check_boundaries.py [--root .]
Exit code 0 when clean, 1 when any violation is found, 2 on usage error.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_specs import parse_spec_file  # noqa: E402

# Highest first. A module may import from its own layer or any layer after it in this order.
LAYERS = ("ui", "ui-logic", "state", "client", "service", "engine", "domain-core")
SKIP_DIRS = {".git", "__pycache__", ".venv", ".venv-spike", "node_modules", "spike", "tests", "validate"}


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    layer: str
    paths: tuple[str, ...]
    depends_on: tuple[str, ...]


def load_modules(boundaries: Path) -> list[Module]:
    spec = parse_spec_file(boundaries)
    modules: list[Module] = []
    for item in spec.items:
        if item.kind != "MOD" or not item.active:
            continue
        paths = tuple(
            part.strip() for part in item.attrs.get("paths", "").split(",") if part.strip() and not part.strip().startswith("TBD")
        )
        depends = tuple(
            part.strip()
            for part in item.attrs.get("depends_on", "").split(",")
            if part.strip() and part.strip().lower() not in ("nothing", "none", "-")
        )
        modules.append(Module(item.id, item.title, item.attrs.get("layer", ""), paths, depends))
    return modules


def owner_of(path: Path, modules: list[Module], root: Path) -> list[Module]:
    relative = path.relative_to(root).as_posix()
    return [m for m in modules if any(relative == p or relative.startswith(p.rstrip("/") + "/") for p in m.paths)]


def module_by_name(modules: list[Module], name: str) -> Module | None:
    return next((m for m in modules if m.name == name), None)


def resolve_import(dotted: str, modules: list[Module], source_root: str = "src") -> str | None:
    """Map a dotted import onto the module that owns the file it refers to.

    Resolution is by longest owned path, not by matching a path component: `engine.limits` owned as
    `src/engine/limits.py` belongs to one module, and matching on the component `engine` alone would
    blame every module that happens to live under it.
    """
    candidate = f"{source_root}/" + dotted.replace(".", "/")
    best: tuple[int, str] | None = None
    for module in modules:
        for owned in module.paths:
            owned_clean = owned.rstrip("/")
            stem = owned_clean[:-3] if owned_clean.endswith(".py") else owned_clean
            if candidate == stem or candidate.startswith(stem + "/"):
                if best is None or len(stem) > best[0]:
                    best = (len(stem), module.name)
    return best[1] if best else None


def imported_modules(source: Path, modules: list[Module], root: Path) -> set[str]:
    """Module names this file imports, one per import rather than one per coincidental path match."""
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()

    imported: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            # `from engine import reader` names a submodule in the alias, not in node.module. Looking
            # only at node.module misses the most common import style in this codebase entirely.
            names = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
        for dotted in names:
            owner = resolve_import(dotted, modules)
            if owner is not None:
                imported.add(owner)
    return imported


def unchecked(modules: list[Module], root: Path) -> list[str]:
    """What this gate could not examine. Printed every run, never left as silence.

    It reads `*.py`, so the four layers above `service` - which are TypeScript (XC-252) - are invisible
    to it. A gate that checked the Python half and reported "boundaries hold" would be describing a
    product that is half here.
    """
    gaps: list[str] = []
    above = [m for m in modules if m.layer in ("ui", "ui-logic", "state", "client")]
    if above:
        present = [m for m in above if any((root / path).exists() for path in m.paths)]
        named = ", ".join(m.name for m in above)
        gaps.append(
            f"the {len(above)} module(s) above `service` ({named}): this gate reads *.py and those "
            f"layers are TypeScript (XC-252). {len(present)} of them exist on disk today"
        )
    return gaps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the code against the module boundaries the specification declares.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    boundaries = root / "specs" / "01_boundaries.md"
    if not boundaries.exists():
        print(f"boundaries specification not found: {boundaries}", file=sys.stderr)
        return 2

    modules = load_modules(boundaries)
    if not modules:
        print("no modules declared in the specification", file=sys.stderr)
        return 2

    findings: list[str] = []
    sources = [
        path
        for path in (root / "src").rglob("*.py")
        if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
    ] if (root / "src").exists() else []

    for source in sources:
        owners = owner_of(source, modules, root)
        relative = source.relative_to(root).as_posix()
        if not owners:
            findings.append(f"{relative}: owned by no module - add its path to a MOD item in the specification")
            continue
        if len(owners) > 1:
            names = ", ".join(m.id for m in owners)
            findings.append(f"{relative}: owned by more than one module ({names})")
            continue

        owner = owners[0]
        for imported in sorted(imported_modules(source, modules, root)):
            if imported == owner.name:
                continue
            target = module_by_name(modules, imported)
            if target is None:
                continue
            if owner.layer in LAYERS and target.layer in LAYERS:
                if LAYERS.index(target.layer) < LAYERS.index(owner.layer):
                    findings.append(
                        f"{relative}: {owner.name} ({owner.layer}) imports {imported} ({target.layer}) - dependencies point downward only"
                    )
                    continue
            if imported not in owner.depends_on:
                findings.append(
                    f"{relative}: {owner.name} imports {imported}, which it does not declare in depends_on"
                )

    for gap in unchecked(modules, root):
        print(f"NOT checked: {gap}")
    if unchecked(modules, root):
        print()

    for finding in findings:
        print(finding)
    print(f"\n{len(findings)} boundary violation(s)." if findings else "\nBoundaries hold: 0 violations.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
