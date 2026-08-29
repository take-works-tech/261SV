"""The command gate must be able to fail, in both directions, and must admit its blind spots.

The gate exists because INV-006 was prose in three files. A gate that cannot fail would be the same
thing with a green tick attached - so each test here breaks the contracts on purpose and asserts the
gate notices.

Specification: specs/features/operations/spec.md AC-010, AC-012.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "validate" / "check_commands.py"


def run(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(project / "validate" / "check_commands.py")],
        capture_output=True,
        text=True,
        cwd=project,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A copy of the specification and the gate, so a test may break the contracts safely."""
    for relative in ("specs/contracts", "validate/check_commands.py"):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    (tmp_path / "specs" / "contracts" / "schema").mkdir(exist_ok=True)
    return tmp_path


def schema_path(project: Path) -> Path:
    return project / "specs" / "contracts" / "schema" / "CT-003.json"


def catalogue_path(project: Path) -> Path:
    return project / "specs" / "contracts" / "CT-003_engine_api.md"


def test_the_gate_passes_on_the_specification_as_it_stands() -> None:
    result = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stdout


def test_an_operation_missing_from_the_schema_fails(project: Path) -> None:
    schema = json.loads(schema_path(project).read_text(encoding="utf-8"))
    dropped = schema["properties"]["operation"]["enum"].pop()
    schema_path(project).write_text(json.dumps(schema), encoding="utf-8")
    result = run(project)
    assert result.returncode == 1
    assert dropped in result.stdout


def test_an_operation_missing_from_the_catalogue_fails(project: Path) -> None:
    schema = json.loads(schema_path(project).read_text(encoding="utf-8"))
    schema["properties"]["operation"]["enum"].append("workspace.teleport")
    schema_path(project).write_text(json.dumps(schema), encoding="utf-8")
    result = run(project)
    assert result.returncode == 1
    assert "workspace.teleport" in result.stdout


def test_an_unconstrained_schema_fails(project: Path) -> None:
    """A schema that accepts any string cannot refuse an unknown command, which CT-002 promises it does."""
    schema = json.loads(schema_path(project).read_text(encoding="utf-8"))
    del schema["properties"]["operation"]["enum"]
    schema_path(project).write_text(json.dumps(schema), encoding="utf-8")
    result = run(project)
    assert result.returncode == 1
    assert "unconstrained" in result.stdout


def surface_schema_path(project: Path) -> Path:
    return project / "specs" / "contracts" / "schema" / "CT-002.json"


def test_the_surface_pointing_at_nothing_fails(project: Path) -> None:
    """AC-010, and the state this repository was actually in until 2026-08-25: CT-002's `command` was an
    unconstrained string, so nothing compared the abstract surface's set against the wire form's, and
    CT-002 could not refuse the unknown command its own prose says it refuses."""
    schema = json.loads(surface_schema_path(project).read_text(encoding="utf-8"))
    schema["properties"]["command"] = {"type": "string"}
    surface_schema_path(project).write_text(json.dumps(schema), encoding="utf-8")

    result = run(project)

    assert result.returncode == 1
    assert "unconstrained" in result.stdout


def test_an_operation_in_the_wire_form_and_not_the_surface_fails(project: Path) -> None:
    """One direction of AC-010, proven against a surface that lists its own set rather than referring."""
    catalogue = catalogue_operations_of(project)
    schema = json.loads(surface_schema_path(project).read_text(encoding="utf-8"))
    schema["properties"]["command"] = {"enum": catalogue[:-1]}
    surface_schema_path(project).write_text(json.dumps(schema), encoding="utf-8")

    result = run(project)

    assert result.returncode == 1
    assert catalogue[-1] in result.stdout


def test_an_operation_in_the_surface_and_not_the_wire_form_fails(project: Path) -> None:
    """The other direction."""
    schema = json.loads(surface_schema_path(project).read_text(encoding="utf-8"))
    schema["properties"]["command"] = {"enum": [*catalogue_operations_of(project), "workspace.teleport"]}
    surface_schema_path(project).write_text(json.dumps(schema), encoding="utf-8")

    result = run(project)

    assert result.returncode == 1
    assert "workspace.teleport" in result.stdout


def test_referring_to_the_one_enumeration_passes(project: Path) -> None:
    """The arrangement this repository uses: one set, referenced. There is no second list to disagree."""
    schema = json.loads(surface_schema_path(project).read_text(encoding="utf-8"))

    assert schema["properties"]["command"]["$ref"] == "CT-003.json#/properties/operation"
    assert run(project).returncode == 0


def catalogue_operations_of(project: Path) -> list[str]:
    return json.loads(schema_path(project).read_text(encoding="utf-8"))["properties"]["operation"]["enum"]


def test_a_prose_reference_to_a_nonexistent_command_fails(project: Path) -> None:
    path = project / "specs" / "contracts" / "CT-002_command_surface.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n\nSee `workspace.vanish` for details.\n", encoding="utf-8")
    result = run(project)
    assert result.returncode == 1
    assert "workspace.vanish" in result.stdout


def test_a_file_suffix_is_not_read_as_a_command(project: Path) -> None:
    path = project / "specs" / "contracts" / "CT-002_command_surface.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n\nThe schema is `schema/CT-003.json`.\n", encoding="utf-8")
    assert run(project).returncode == 0


def test_the_gate_always_states_what_it_did_not_check() -> None:
    """Silence about a blind spot reads as coverage. Every run names them."""
    result = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True, cwd=ROOT)
    assert "NOT checked:" in result.stdout
    assert "operations/AC-011" in result.stdout


def test_the_gate_reports_shared_components_as_unexamined(project: Path) -> None:
    """With no interface code, uniqueness is unknown - and saying so is the point (AC-024).

    Run against a project with no src/ui or src/shell, because this repository stopped being that
    project on 2026-08-30: mockup 2 put interface code under src/ui, and the gate began examining."""
    shutil.copy2(ROOT / "specs" / "11_ui.md", project / "specs" / "11_ui.md")
    result = run(project)
    assert "operations/AC-024" in result.stdout
    assert "shared components" in result.stdout


def test_shared_components_are_examined_once_interface_code_exists() -> None:
    """The expiry of the test above, asserted rather than assumed: with src/ui present in this
    repository, the unexamined line is gone - the components are checked, not excused."""
    result = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True, cwd=ROOT)
    assert "shared components" not in result.stdout
    assert (ROOT / "src" / "ui").is_dir()


def test_a_duplicated_component_implementation_fails(project: Path) -> None:
    shutil.copy2(ROOT / "specs" / "11_ui.md", project / "specs" / "11_ui.md")
    for directory in ("ui", "shell"):
        target = project / "src" / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "case-tree.tsx").write_text("// the same component, twice\n", encoding="utf-8")
    result = run(project)
    assert result.returncode == 1
    assert "Case tree" in result.stdout
