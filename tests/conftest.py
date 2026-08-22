"""Shared test setup: the engine on the import path, and one honest rule about skipping.

`AGENTS.md` documents `python -m pytest tests` as a command anyone can run. Before this file existed it
did not run: `tests/test_reader.py` imports `vtkmodules`, and on a machine without the engine
environment the suite failed **at collection**, so none of the other 80-odd tests ran either. A
documented command that does not work teaches people to stop running it.

The rule here has two halves, and both are needed:

  on a laptop   VTK may be absent, and the tests that need it skip with a reason that names the
                missing package rather than failing the whole collection
  in CI         `SIM_VIEWER_REQUIRE_VTK=1` turns that skip into a failure. A suite allowed to skip
                where it matters reports success for tests that never ran, which is the same defect
                as a gate that is never invoked

Nothing here changes what a test asserts. It changes only whether the absence of an optional
environment is reported as a skip or as a failure, and who is allowed which answer.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REQUIRE_VTK = os.environ.get("SIM_VIEWER_REQUIRE_VTK") == "1"


def requires_vtk() -> None:
    """Skip the caller unless VTK is importable - or fail, where a skip is not an acceptable answer.

    Call at module scope, above the `vtkmodules` imports, so a missing engine environment never
    reaches collection of the rest of the suite.
    """
    try:
        import vtkmodules  # noqa: F401
    except ImportError as exc:
        message = (
            f"VTK is not importable in this interpreter ({sys.executable}): {exc}. "
            "Install the engine environment with `python -m pip install -e \".[dev]\"`."
        )
        if REQUIRE_VTK:
            pytest.fail(message + " SIM_VIEWER_REQUIRE_VTK=1 forbids skipping this.", pytrace=False)
        pytest.skip(message, allow_module_level=True)


@pytest.fixture(scope="session", autouse=True)
def _report_the_interpreter(record_testsuite_property: object) -> None:
    """The Python that ran the suite, in the report.

    `pyproject.toml` requires 3.12 and a machine may well have 3.11 first on its PATH; a failure that
    depends on the interpreter is much cheaper to read when the interpreter is written down.
    """
    if sys.version_info < (3, 12):
        print(
            f"\nNOTE: running on Python {sys.version.split()[0]}, "
            "while pyproject.toml requires >=3.12. Results may differ from CI.",
            file=sys.stderr,
        )
