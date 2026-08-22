"""Dependency-pin gate: the specification and the manifest must name the same versions.

Check 7 of the spec linter compares a Fixed value against the code, and it works by looking for
`SYMBOL = literal` inside source files. A dependency version is not written that way. It is written
`"vtk==9.5.2"` inside a TOML array, and check 7 looks straight past it - which is how this project
carried `version: VTK 9.7.x` in `specs/06_external.md` while `pyproject.toml` pinned 9.5.2 and every
first-hand measurement in `evidence/sources.md` was taken on 9.5.2 (XC-185, OPEN-019).

Two directions, because the hole has two sides:

  declared -> pinned   a spec item carrying `pinned_in: <manifest>#<package>` must agree with the
                       version that manifest actually pins
  pinned -> declared   every runtime dependency in the manifest must appear in the dependency table of
                       `specs/09_technology.md`, which is where check 20 requires a licence, adoption
                       evidence and a support horizon. A dependency absent from that table has had
                       none of those three questions asked

**What this gate does not check is printed, not implied.** Silence from a gate reads as coverage, and
a dependency it never looked at is the one that ships without a notice.

Exit code: 0 clean, 1 findings. Stdlib only.
"""

from __future__ import annotations

import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]

MANIFESTS = {"pyproject.toml": ROOT / "pyproject.toml"}

TECHNOLOGY = ROOT / "specs" / "09_technology.md"
SPEC_ROOT = ROOT / "specs"

# Dev and build dependencies are deliberately outside the product's distribution closure: they are not
# shipped, so XC-025's notice obligation and check 20's three questions do not attach to them. They are
# named in the "NOT checked" report rather than silently skipped.
DEV_GROUPS = ("dev", "test", "docs")

# `- pinned_in: pyproject.toml#vtk` on a spec item, beside the `- version:` line it constrains.
_PINNED_IN = re.compile(r"^- pinned_in:\s*(?P<manifest>[\w./-]+)#(?P<package>[A-Za-z0-9._-]+)\s*$")
_ITEM = re.compile(r"^### (?P<id>[A-Z]+-\d+)\b")
_VERSION_LINE = re.compile(r"^- version:\s*(?P<body>.+)$")
# A version anywhere in the `- version:` prose: `9.5.2`, `**9.5.2**`, `1.39.5`.
_VERSION = re.compile(r"\b(\d+\.\d+(?:\.\d+)?)\b")

# `numpy==2.3.4`, `vtk==9.5.2`, `setuptools>=69`
_REQUIREMENT = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)\s*(?P<operator>[=<>!~]+)\s*(?P<version>[^;,\s]+)")


def normalise(name: str) -> str:
    """PyPI treats `-`, `_` and `.` as equivalent and is case-insensitive; so does the table column."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def read_manifest(path: pathlib.Path) -> tuple[dict[str, str], dict[str, str]]:
    """Runtime and non-runtime requirements of a `pyproject.toml`, each as name -> pinned version."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})

    def parse(entries: list[str]) -> dict[str, str]:
        found = {}
        for entry in entries:
            match = _REQUIREMENT.match(entry.strip())
            if match:
                found[match.group("name")] = match.group("version") if match.group("operator") == "==" else ""
        return found

    runtime = parse(project.get("dependencies", []))
    other = parse(data.get("build-system", {}).get("requires", []))
    for group, entries in (project.get("optional-dependencies", {}) or {}).items():
        target = other if group in DEV_GROUPS else runtime
        target.update(parse(entries))
    return runtime, other


def declared_rows() -> set[str]:
    """The first column of every dependency row in the technology file, normalised."""
    rows: set[str] = set()
    inside = False
    for line in TECHNOLOGY.read_text(encoding="utf-8").splitlines():
        if line.startswith("| Dependency |"):
            inside = True
            continue
        if inside:
            if not line.startswith("|"):
                break
            cell = line.split("|")[1].strip()
            if cell and not set(cell) <= set("-: "):
                # "MaterialX 1.39.5" and "OpenPBR Surface 1.1.1" carry their version in the name.
                rows.add(normalise(_VERSION.sub("", cell)))
    return rows


def pinned_claims() -> list[tuple[str, pathlib.Path, int, str, str, str]]:
    """Every `pinned_in:` claim: (item id, spec path, line, manifest, package, version stated)."""
    claims = []
    for spec in sorted(SPEC_ROOT.rglob("*.md")):
        item_id, version, version_line = "", "", 0
        for number, line in enumerate(spec.read_text(encoding="utf-8").splitlines(), start=1):
            if header := _ITEM.match(line):
                item_id, version, version_line = header.group("id"), "", 0
            elif body := _VERSION_LINE.match(line):
                if found := _VERSION.search(body.group("body")):
                    version, version_line = found.group(1), number
            elif pin := _PINNED_IN.match(line):
                claims.append(
                    (item_id, spec, version_line or number, pin.group("manifest"), pin.group("package"), version)
                )
    return claims


def main() -> int:
    findings: list[str] = []
    unchecked: list[str] = []

    manifests = {name: read_manifest(path) for name, path in MANIFESTS.items() if path.exists()}
    for name, path in MANIFESTS.items():
        if not path.exists():
            unchecked.append(f"{name}: no such file, so nothing in it was compared")

    claims = pinned_claims()
    for item_id, spec, line, manifest, package, stated in claims:
        rel = spec.relative_to(ROOT).as_posix()
        if manifest not in manifests:
            findings.append(f"{rel}:{line} {item_id} points at {manifest}, which was not read")
            continue
        runtime, other = manifests[manifest]
        pinned = {**other, **runtime}
        if package not in pinned:
            findings.append(f"{rel}:{line} {item_id} claims {manifest} pins '{package}', which it does not require")
            continue
        if not pinned[package]:
            unchecked.append(f"{item_id}: {manifest} does not pin '{package}' to one version, so no comparison was possible")
            continue
        if not stated:
            findings.append(f"{rel}:{line} {item_id} has no version to compare against {manifest} '{package}'")
        elif stated != pinned[package]:
            findings.append(
                f"{rel}:{line} {item_id} says {stated} but {manifest} pins {package}=={pinned[package]}"
            )

    rows = declared_rows()
    runtime, other = manifests.get("pyproject.toml", ({}, {}))
    for package in sorted(runtime):
        if normalise(package) not in rows:
            findings.append(
                f"pyproject.toml requires '{package}' at runtime, and it has no row in "
                f"specs/09_technology.md - so its licence, its adoption evidence and its support "
                f"horizon have never been recorded (XC-025, check 20)"
            )
    if other:
        unchecked.append(
            "build and development requirements ("
            + ", ".join(sorted(other))
            + ") are not in the distribution closure, so no notice obligation attaches to them"
        )
    if (ROOT / "mockups" / "ui" / "package.json").exists():
        unchecked.append(
            "mockups/ui/package.json: the mockup catalogue is design states, never shipped code, so its "
            "dependencies are outside the product's licence closure"
        )

    for note in unchecked:
        print(f"NOT checked: {note}")
    if findings:
        print()
        for finding in findings:
            print(f"  {finding}")
        print(f"\n{len(findings)} dependency-pin finding(s).", file=sys.stderr)
        return 1
    print(f"\nDependency pins agree: {len(claims)} declared version(s), {len(runtime)} runtime requirement(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
