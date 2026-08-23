"""The canonical frame, and the rule for reaching it from what a file declared.

Geometry in this product is right-handed, Z up, metres (GL-021). A file that declares something else is
converted once, on load (XC-230); a file that declares nothing is assumed to be canonical already, and
the assumption is recorded rather than hidden (ingest/AC-028).

This lives in the domain rather than in the reader because it is a rule about what a coordinate means,
not about how a file is parsed - and because it is then testable with no VTK installed, which is how it
was verified.
"""

from __future__ import annotations

from dataclasses import dataclass

CANONICAL_UP = "Z"
CANONICAL_SCALE = 1.0

# What a declared length unit means in metres. Measured, not chosen: CGNS is the one format in this
# stack that declares one, and this is its enumeration - `Meter`, `Centimeter`, `Millimeter`, `Foot`,
# `Inch` (E-130). The VTK XML formats and STL declare no frame and no unit at all.
LENGTH_UNITS_IN_METRES: dict[str, float] = {
    "Meter": 1.0,
    "Centimeter": 0.01,
    "Millimeter": 0.001,
    "Foot": 0.3048,
    "Inch": 0.0254,
}

# Which formats can carry unit information at all, and what they carry. Measured, not assumed (E-130):
# CGNS declares `LengthUnits` and `DimensionalExponents`, and no other format in this stack declares a
# unit. A format listed here whose reader does not read that information has to say so - a file that
# knows its own units, opened by a reader that ignores them, must not leave a user believing the unit
# came through (ingest/AC-034).
FORMATS_CARRYING_UNIT_INFORMATION: dict[str, str] = {
    ".cgns": "LengthUnits and DimensionalExponents",
}

# The up axes this reader can bring to the canonical frame. A file declaring anything else is refused
# rather than rotated on a guess: a rotation applied to the wrong axis produces geometry that looks
# plausible and measures wrongly (ingest/AC-029).
SUPPORTED_UP_AXES = ("X", "Y", "Z")


class UnsupportedFrameError(Exception):
    """Raised when a file declares a frame or a length unit this reader cannot bring to the canonical
    frame. It names what it did not support, because "import failed" leaves a user guessing at a file
    that is probably fine (ingest/AC-029)."""


@dataclass(frozen=True, slots=True)
class FrameDeclaration:
    """What a file said about its own frame. `None` anywhere means the file did not say."""

    up_axis: str | None = None
    length_unit: str | None = None


def resolve_frame(declaration: FrameDeclaration) -> tuple[str, float]:
    """The up axis and the scale to metres to apply, or a refusal naming what could not be honoured.

    A declaration this reader cannot honour refuses the import (ingest/AC-029). It never falls back to
    the canonical values, because a file that says millimetres and is read as metres is wrong by a
    thousand and looks entirely reasonable.
    """
    up = declaration.up_axis
    if up is not None and up.upper() not in SUPPORTED_UP_AXES:
        raise UnsupportedFrameError(
            f"the file declares '{up}' as its up axis; this reader supports {list(SUPPORTED_UP_AXES)}"
        )

    unit = declaration.length_unit
    if unit is not None and unit not in LENGTH_UNITS_IN_METRES:
        raise UnsupportedFrameError(
            f"the file declares its length unit as '{unit}'; this reader converts "
            f"{sorted(LENGTH_UNITS_IN_METRES)} and will not guess at another"
        )

    return (
        up.upper() if up else CANONICAL_UP,
        LENGTH_UNITS_IN_METRES[unit] if unit else CANONICAL_SCALE,
    )
