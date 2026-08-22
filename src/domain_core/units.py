"""Units, and the refusal to invent them.

CAE result files do not carry units reliably: the solver wrote numbers, and their meaning lives in the
engineer's head. This module therefore has no unit detection and no default unit. A quantity is either
declared by a person or it is undeclared, and an undeclared quantity cannot be converted, compared
across cases, or labelled.

Specification: GL-020 (declared unit), XC-003 (undeclared units), INV-001 (canonical frame).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Quantity(str, Enum):
    """The physical quantities this product converts between units of."""

    LENGTH = "length"
    TIME = "time"
    MASS = "mass"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"


@dataclass(frozen=True, slots=True)
class Unit:
    """A unit the user declared, and the affine map that takes it to the internal unit.

    `value * to_internal + offset` is the value in the internal unit of its quantity. Most units need
    only the factor; **temperature needs the offset**, and an earlier version of this module said the
    offset case was "handled by its own conversion" while providing no such conversion and registering
    no unit that needed one. The first person to add degrees Celsius with a factor of 1.0 would have
    produced kelvin values 273.15 too low, in a product whose whole claim is the number.
    """

    symbol: str
    quantity: Quantity
    to_internal: float
    offset: float = 0.0


class UndeclaredUnitError(Exception):
    """Raised when a conversion is attempted on a value whose unit nobody declared.

    This is not an error the product recovers from by choosing a unit. It is reported to the user, who
    is the only one who knows (XC-003).
    """


# The internal units, one per quantity. Everything is held in these and converted at display only.
INTERNAL = {
    Quantity.LENGTH: "m",
    Quantity.TIME: "s",
    Quantity.MASS: "kg",
    Quantity.PRESSURE: "Pa",
    Quantity.TEMPERATURE: "K",
}

_KNOWN: dict[str, Unit] = {
    unit.symbol: unit
    for unit in (
        Unit("m", Quantity.LENGTH, 1.0),
        Unit("mm", Quantity.LENGTH, 1.0e-3),
        Unit("cm", Quantity.LENGTH, 1.0e-2),
        Unit("in", Quantity.LENGTH, 0.0254),
        Unit("s", Quantity.TIME, 1.0),
        Unit("ms", Quantity.TIME, 1.0e-3),
        Unit("kg", Quantity.MASS, 1.0),
        Unit("g", Quantity.MASS, 1.0e-3),
        Unit("Pa", Quantity.PRESSURE, 1.0),
        Unit("kPa", Quantity.PRESSURE, 1.0e3),
        Unit("MPa", Quantity.PRESSURE, 1.0e6),
        Unit("K", Quantity.TEMPERATURE, 1.0),
        Unit("degC", Quantity.TEMPERATURE, 1.0, 273.15),
        Unit("degF", Quantity.TEMPERATURE, 5.0 / 9.0, 273.15 - 32.0 * 5.0 / 9.0),
    )
}


def unit(symbol: str) -> Unit:
    """Look up a declared unit symbol. Unknown symbols raise rather than being guessed at."""
    try:
        return _KNOWN[symbol]
    except KeyError:
        raise UndeclaredUnitError(f"'{symbol}' is not a unit this product knows; declare one of {sorted(_KNOWN)}") from None


def convert(value: float, source: str | None, target: str, *, difference: bool = False) -> float:
    """Convert a value between declared units.

    `source` is None when the field carries no declared unit. That is not a reason to assume the
    internal unit - it is the reason to refuse.

    `difference=True` converts an **interval** rather than a point on the scale. A temperature of
    10 degrees Celsius is 283.15 K; a temperature *rise* of 10 degrees Celsius is 10 K. Applying the
    offset to a difference is the same mistake as omitting it from an absolute value, and it is harder
    to notice because the answer stays in a plausible range (INV-028).
    """
    if source is None:
        raise UndeclaredUnitError(
            "this value has no declared unit, so it cannot be converted; declare the unit on the field first"
        )
    origin, destination = unit(source), unit(target)
    if origin.quantity is not destination.quantity:
        raise UndeclaredUnitError(
            f"'{source}' measures {origin.quantity.value} and '{target}' measures {destination.quantity.value}"
        )
    if difference:
        return value * origin.to_internal / destination.to_internal
    internal = value * origin.to_internal + origin.offset
    return (internal - destination.offset) / destination.to_internal


def to_internal(value: float, source: str | None, *, difference: bool = False) -> float:
    """Convert into the internal unit of the source's quantity, refusing if undeclared."""
    if source is None:
        raise UndeclaredUnitError("this value has no declared unit, so it cannot be converted")
    return convert(value, source, INTERNAL[unit(source).quantity], difference=difference)
