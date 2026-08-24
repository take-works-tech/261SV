"""Reading CGNS: the one format that declares its units, and the one this product cannot read them from.

Two facts about CGNS decide how it is read here, and they pull in opposite directions.

**It is the only format this build reads that declares a length unit.** CGNS carries `DimensionalUnits`
and `DimensionalExponents` nodes, which is why `FORMATS_CARRYING_UNIT_INFORMATION` names it and why
constructing a `ReaderChoice` for `.cgns` without saying what goes unread is refused (E-130).

**`vtkCGNSReader` has no method that returns any of it.** Measured on VTK 9.5.2: the class exposes no
accessor whose name contains `unit`, `dimension` or `dataclass` - not one (E-137). So the declaration is
in the file, this product can see that it is there, and the reader hands over nothing. The unit stays
**undeclared**, and the difference between "this file said nothing" and "this file said something we did
not read" is exactly what ingest/AC-034 requires be told to the user: only one of the two can be fixed
by asking the solver.

And, as with Exodus, the reader reads **no results at all** until each array is switched on (E-137).
That part is not CGNS-specific and lives in `engine.completeness`.

Specification: ingest/REQ-013, REQ-015, AC-034, XC-237. Evidence: E-130 (T1), E-137 (T1).
"""

from __future__ import annotations

from engine.completeness import (
    check_nothing_was_dropped,
    enable_selections,
    names_in_selections,
)

#: What the format declares and this reader does not read, in the words ingest/AC-034 asks for.
UNREAD_UNIT_INFORMATION = (
    "CGNS declares its units in DimensionalUnits and DimensionalExponents; the toolkit's reader exposes "
    "no accessor for either, so this product reads none of it and every field stays undeclared"
)

#: What has been exercised, and what has not. A support level is a claim and this is the part of the
#: claim that is measured: the fixture is a minimal single-zone unstructured file written by this
#: project's own test code, because the toolkit ships no CGNS writer (E-137).
KNOWN_GAPS = (
    "results are read only because every array is enabled here; verified against a generated "
    "single-zone unstructured file, so multi-zone, structured zones, boundary conditions and "
    "ADF-format CGNS are unexercised"
)


def _selections(reader: object) -> tuple[object, ...]:
    return (
        reader.GetPointDataArraySelection(),
        reader.GetCellDataArraySelection(),
        reader.GetFaceDataArraySelection(),
    )


def enable_everything(reader: object) -> None:
    """Switch on every array, base and family the file offers.

    `UpdateInformation` first: the selections are empty until the file has been looked at, so enabling
    before that enables nothing and reports success.
    """
    reader.UpdateInformation()
    enable_selections(*_selections(reader))
    reader.EnableAllBases()
    reader.EnableAllFamilies()


def verify(reader: object, output: object) -> None:
    """Refuse the read if a result the file offered did not arrive."""
    check_nothing_was_dropped(names_in_selections(*_selections(reader)), output, evidence="E-137")
