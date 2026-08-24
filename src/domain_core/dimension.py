"""What a quantity *is*, apart from the symbol somebody wrote for it.

`units.py` answers "what does this symbol convert to"; this module answers "may these two be added, and
what is the result of dividing one by the other". They are different questions, and the expression
language of `specs/13_scripting.md` needs the second: a length divided by a time is a velocity, and no
enumeration of quantities can hold an open set of products (XC-242).

A dimension is four integer exponents over mass, length, time and temperature. Pressure is not a base
quantity - it is (1, -1, -2, 0), which is why `Quantity.PRESSURE` needs a row in the table below rather
than a place among the exponents.

Specification: XC-242, INV-002, GL-020.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain_core.units import INTERNAL, Quantity, unit

#: The base symbols, in the order a composed symbol writes them. One entry per exponent.
BASE_SYMBOLS = ("kg", "m", "s", "K")


@dataclass(frozen=True, slots=True)
class Dimension:
    """Exponents over the base quantities. Equality is what decides whether two values may be added."""

    mass: int = 0
    length: int = 0
    time: int = 0
    temperature: int = 0

    @property
    def exponents(self) -> tuple[int, int, int, int]:
        return (self.mass, self.length, self.time, self.temperature)

    @property
    def is_dimensionless(self) -> bool:
        return self.exponents == (0, 0, 0, 0)

    def times(self, other: Dimension) -> Dimension:
        return Dimension(*(a + b for a, b in zip(self.exponents, other.exponents)))

    def over(self, other: Dimension) -> Dimension:
        return Dimension(*(a - b for a, b in zip(self.exponents, other.exponents)))

    def power(self, exponent: int) -> Dimension:
        return Dimension(*(a * exponent for a in self.exponents))

    def root(self) -> Dimension | None:
        """Half the exponents, or None where one of them is odd.

        A fractional exponent is not refused for tidiness: this product has no unit symbol for it, so
        the result would have to be reported with a unit nobody could read or with none at all.
        """
        if any(a % 2 for a in self.exponents):
            return None
        return Dimension(*(a // 2 for a in self.exponents))


DIMENSIONLESS = Dimension()

#: What each quantity this product knows is made of. The derived one is the reason this table exists.
DIMENSION_OF: dict[Quantity, Dimension] = {
    Quantity.MASS: Dimension(mass=1),
    Quantity.LENGTH: Dimension(length=1),
    Quantity.TIME: Dimension(time=1),
    Quantity.TEMPERATURE: Dimension(temperature=1),
    Quantity.PRESSURE: Dimension(mass=1, length=-1, time=-2),
}


def dimension_of(symbol: str) -> Dimension:
    """The dimension of a declared unit symbol. An unknown symbol raises, as in `units.unit`."""
    return DIMENSION_OF[unit(symbol).quantity]


def symbol_for(dimension: Dimension) -> str | None:
    """The unit a result of this dimension is reported in, or None where it has none.

    A dimension that matches a quantity this product knows is reported with **that quantity's internal
    symbol** - `Pa`, not `kg·m^-1·s^-2` - because the composed form is correct and unreadable. Anything
    else is composed from the base symbols in a fixed order, so the same dimension always prints the
    same way.
    """
    if dimension.is_dimensionless:
        return None
    for quantity, known in DIMENSION_OF.items():
        if known == dimension:
            return INTERNAL[quantity]
    parts = [
        symbol if exponent == 1 else f"{symbol}^{exponent}"
        for symbol, exponent in zip(BASE_SYMBOLS, dimension.exponents)
        if exponent
    ]
    return "·".join(parts)
