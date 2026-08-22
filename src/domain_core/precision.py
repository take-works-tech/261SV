"""How many digits a stored value can honestly carry, and how to write it down.

A field read as a 32-bit float carries about seven significant decimal digits. Printing fifteen of
them does not make the number better; it makes the display a claim the data cannot support, and in a
report that claim is indistinguishable from a measurement. So significant digits are derived from the
stored type rather than chosen per screen, and mixing precisions takes the weaker of the two.

Specification: GL-023, GL-024, INV-014, INV-015, INV-016, XC-096.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

import numpy as np

# IEEE 754 decimal digits that survive a round trip: float32 has 24 bits of significand, float64 has
# 53. The values are the standard's, not a preference, which is why they are named rather than typed
# in at each use.
FLOAT32_DIGITS = 6
FLOAT64_DIGITS = 15

# The comparison tolerance used when nothing stricter is stated. It is relative, because an absolute
# tolerance means one thing for a coordinate in metres and another for a stress in pascals.
DEFAULT_RELATIVE_TOLERANCE = 1e-9


class PrecisionError(Exception):
    """Raised when a value would be presented as more precise than it is stored (INV-014)."""


def significant_digits(dtype: np.dtype | type) -> int:
    """Significant decimal digits a value of this type can carry.

    Integers are exact: a count is not a measurement, and rounding one is how a mesh acquires
    999999.9999 points (INV-015).
    """
    resolved = np.dtype(dtype)
    if np.issubdtype(resolved, np.integer):
        return 0
    if resolved == np.float32:
        return FLOAT32_DIGITS
    if resolved == np.float64:
        return FLOAT64_DIGITS
    if np.issubdtype(resolved, np.floating):
        # float16 and long double both land here. Deriving from the type rather than guessing keeps
        # a platform-specific width from silently claiming double precision.
        return int(np.finfo(resolved).precision)
    raise PrecisionError(f"{resolved} is not a numeric type, so it has no significant digits")


def weakest(dtypes: Iterable[np.dtype | type]) -> int:
    """Digits available when values of several types are combined.

    A float32 field added to a float64 field yields a float64 array, and the result looks like double
    precision to every downstream reader. It is not: the answer is only as good as its worst input.
    """
    digits = [significant_digits(dtype) for dtype in dtypes]
    if not digits:
        raise PrecisionError("no types given: the available precision of nothing is not zero, it is undefined")
    floating = [count for count in digits if count > 0]
    return min(floating) if floating else 0


def format_value(value: float, digits: int, *, missing: str = "-") -> str:
    """Write a value to the digits its storage supports.

    Missing is missing: NaN prints as the missing marker rather than as `nan`, and never as 0.
    """
    if digits < 0:
        raise PrecisionError("significant digits cannot be negative")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if not np.isfinite(value):
        if np.isnan(value):
            return missing
        return "+inf" if value > 0 else "-inf"
    if digits == 0:
        return str(int(round(value)))
    formatted = f"{Decimal(float(value)):.{digits}g}"
    return formatted


def format_field_value(value: float, dtype: np.dtype | type, *, missing: str = "-") -> str:
    """Write one value of a stored field, at that field's honest precision."""
    return format_value(value, significant_digits(dtype), missing=missing)


def equal_within(
    left: float,
    right: float,
    *,
    relative: float = DEFAULT_RELATIVE_TOLERANCE,
    absolute: float = 0.0,
) -> bool:
    """Compare two physical values with a stated tolerance (INV-016).

    Exact equality on floating point is a coin toss dressed as a test: the same quantity computed two
    ways differs in the last bits, and `==` reports that difference as a disagreement about physics.
    Two missing values are not equal - a comparison of what was never measured has no answer, and
    returning True would let a check pass on absence.
    """
    if np.isnan(left) or np.isnan(right):
        return False
    return bool(np.isclose(left, right, rtol=relative, atol=absolute))
