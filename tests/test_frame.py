"""The canonical frame, and what happens to a file that declares another one.

ingest/AC-029. These run with no VTK installed, which is why the rule lives in `domain_core.frame`
rather than in the reader: a refusal that only CI can exercise is a refusal nobody checks while writing
it.
"""

from __future__ import annotations

import pytest

from domain_core.frame import (
    CANONICAL_SCALE,
    CANONICAL_UP,
    LENGTH_UNITS_IN_METRES,
    FrameDeclaration,
    UnsupportedFrameError,
    resolve_frame,
)


def test_a_file_that_declares_nothing_is_assumed_canonical() -> None:
    """AC-028: the assumption is what gets recorded, rather than being hidden."""
    assert resolve_frame(FrameDeclaration()) == (CANONICAL_UP, CANONICAL_SCALE)


@pytest.mark.parametrize(("unit", "metres"), sorted(LENGTH_UNITS_IN_METRES.items()))
def test_every_declared_unit_this_reader_accepts_has_a_factor(unit: str, metres: float) -> None:
    assert resolve_frame(FrameDeclaration(length_unit=unit)) == (CANONICAL_UP, metres)


def test_the_factors_are_the_measured_ones() -> None:
    """CGNS's enumeration, read from the shipped library rather than recalled (E-130). A wrong factor
    here is wrong by orders of magnitude and looks entirely ordinary."""
    assert LENGTH_UNITS_IN_METRES == {
        "Meter": 1.0, "Centimeter": 0.01, "Millimeter": 0.001, "Foot": 0.3048, "Inch": 0.0254,
    }


def test_an_unsupported_unit_refuses_and_names_it() -> None:
    with pytest.raises(UnsupportedFrameError) as refusal:
        resolve_frame(FrameDeclaration(length_unit="Furlong"))
    assert "Furlong" in str(refusal.value)
    assert "will not guess" in str(refusal.value)


def test_an_unsupported_up_axis_refuses_and_names_it() -> None:
    with pytest.raises(UnsupportedFrameError) as refusal:
        resolve_frame(FrameDeclaration(up_axis="W"))
    assert "'W'" in str(refusal.value)


@pytest.mark.parametrize("declaration", [
    FrameDeclaration(length_unit="mm"),      # the abbreviation, not the enumeration's spelling
    FrameDeclaration(length_unit="metre"),   # the other spelling
    FrameDeclaration(up_axis="-Z"),          # a direction rather than an axis
    FrameDeclaration(up_axis="up"),
])
def test_it_never_falls_back_to_the_canonical_value(declaration: FrameDeclaration) -> None:
    """The failure this exists to prevent: a file saying millimetres, read as metres, is wrong by a
    thousand and looks entirely reasonable. Anything not understood is refused, not assumed."""
    with pytest.raises(UnsupportedFrameError):
        resolve_frame(declaration)


def test_a_declared_axis_is_accepted_in_either_case() -> None:
    assert resolve_frame(FrameDeclaration(up_axis="y")) == ("Y", CANONICAL_SCALE)


class TestUnreadUnitInformation:
    """ingest/AC-034: a field whose file carried unit information the reader did not read is still
    undeclared - and the interface says the information was there. The difference matters: "the file
    said nothing" is fixed by asking the solver, "we did not read it" is fixed by us."""

    def test_only_the_format_measured_to_carry_units_is_listed(self) -> None:
        """Measured from the shipped library, not recalled (E-130). Listing a format that carries
        nothing would make every reader for it claim a gap it does not have; omitting one that does
        carry units lets a unit disappear silently, which is the failure AC-034 is about."""
        from domain_core.frame import FORMATS_CARRYING_UNIT_INFORMATION

        assert FORMATS_CARRYING_UNIT_INFORMATION == {
            ".cgns": "LengthUnits and DimensionalExponents",
        }

    def test_the_formats_this_build_reads_carry_none(self) -> None:
        from domain_core.frame import FORMATS_CARRYING_UNIT_INFORMATION

        for suffix in (".vtu", ".pvtu", ".vtp", ".stl"):
            assert suffix not in FORMATS_CARRYING_UNIT_INFORMATION
