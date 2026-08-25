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

#: One instant, supplied by a test rather than read from a clock, so the same call twice produces the
#: same document and a failure never depends on the minute it ran. Here rather than in each file
#: because two copies of a constant are two answers waiting to differ.
FIXED_INSTANT = "2026-08-24T12:00:00Z"


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


def requires_h5py() -> None:
    """Skip the caller unless h5py is importable, under the same rule as VTK.

    CGNS is the one Verified format the toolkit ships **no writer** for (E-137), so its fixture is
    written by this project's own test code straight into the CGNS/HDF5 node layout (XC-085's rule, by
    a route XC-085 did not anticipate). h5py is what writes it, and it is a development dependency for
    that reason alone - nothing in the engine imports it.
    """
    try:
        import h5py  # noqa: F401
    except ImportError as exc:
        message = (
            f"h5py is not importable in this interpreter ({sys.executable}): {exc}. "
            "It writes the CGNS fixture; install with `python -m pip install -e \".[dev]\"`."
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


#: VTK's cell-type code for a hexahedron, held once for the tests that build a mesh by hand without the
#: toolkit present. `test_summary_weights.py` asserts it against `vtkmodules`' own constant where VTK is
#: available, so this copy cannot quietly disagree with the value it stands in for.
VTK_HEXAHEDRON = 12
