"""A number this product is willing to show, with everything a reader needs to judge it.

@Provenance travels with a value from the moment it exists, because a number's origin cannot be
reconstructed afterwards (GL-016). The same is true of the caveats: that the dataset it came from was
missing a part, that it was averaged across cells, that it was read from reduced geometry. A caveat
discovered at load and remembered only in a log is a caveat the figure does not carry.

So a reported value carries three things a bare `float` cannot: where it came from, what is qualified
about it, and how many digits it honestly has. **Deriving a value from others unions their caveats**,
which is what makes "every derived number carries the mark" (ingest/AC-027) a property of the type
rather than something each call site has to remember.

A missing value is `None` and stays `None`: no substituted zero, no previous value, no interpolated
neighbour (XC-001).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable

from domain_core.precision import format_value


class Provenance(str, Enum):
    """Where a quantity came from (GL-016)."""

    DECLARED = "declared"      # a person said so
    DATASET = "dataset"        # read from a @Dataset
    COMPUTED = "computed"      # computed by a formula, which is carried alongside
    REFERENCE = "reference"    # taken from @Reference material, never a source of numbers


class Caveat(str, Enum):
    """Something true of a value that a reader must know to act on it.

    Each of these changes what the number means, and none of them changes the number. That is exactly
    why they have to travel: nothing about the digits themselves reveals that a part was missing.
    """

    PARTIAL_DATASET = "partial-dataset"        # a part the manifest named was not there (AC-027)
    AVERAGED = "averaged"                      # averaged across cells sharing a point (INV-003)
    FROM_REDUCED_GEOMETRY = "from-reduced"     # measured on display geometry, not the full dataset
    UNDECLARED_UNIT = "undeclared-unit"        # the quantity has no unit and none was inferred (XC-003)


# A quantity that genuinely has no unit - a ratio, a safety factor, a count - is **dimensionless**, and
# SI writes that as 1. It is not the same as a unit nobody declared, and conflating the two would make
# every safety factor look like a stress whose unit went missing. Found by writing the first ratio.
DIMENSIONLESS = "1"

CAVEAT_TEXT: dict[Caveat, str] = {
    Caveat.PARTIAL_DATASET: "データセットの一部が欠落しています",
    Caveat.AVERAGED: "セル間で平均した値です",
    Caveat.FROM_REDUCED_GEOMETRY: "縮退した表示形状から測った値です",
    Caveat.UNDECLARED_UNIT: "単位が宣言されていません",
}


@dataclass(frozen=True, slots=True)
class ReportedValue:
    """One number, with its origin, its caveats and the digits it honestly carries."""

    value: float | None
    unit: str | None
    digits: int
    provenance: Provenance
    caveats: frozenset[Caveat] = frozenset()
    formula: str | None = None
    # Why the value is not there, when it is not. A refusal that gives no reason reads as an oversight,
    # and the reader then supplies their own explanation - usually a wrong one.
    missing_because: str | None = None

    def __post_init__(self) -> None:
        if self.provenance is Provenance.COMPUTED and not self.formula:
            raise ValueError(
                "a computed value carries the formula that produced it (GL-032); without it the number "
                "cannot be checked or reproduced"
            )
        if self.digits < 1:
            raise ValueError("a value carries at least one significant digit")
        if self.missing_because and self.value is not None:
            raise ValueError("a value that is there does not also carry a reason for being absent")
        if self.unit is None and Caveat.UNDECLARED_UNIT not in self.caveats:
            raise ValueError(
                "a value with no unit carries UNDECLARED_UNIT; a unit that is merely absent reads as a "
                "unit nobody needed (XC-003)"
            )

    @classmethod
    def unavailable(
        cls, reason: str, *, unit: str | None, digits: int, provenance: Provenance,
        caveats: frozenset[Caveat] = frozenset(), formula: str | None = None,
    ) -> "ReportedValue":
        """A number this product declines to report, saying why.

        Refusing is a result (XC-001). It is not the same as a value that happened to be NaN in the
        file, and both are `None` here - `missing_because` is what separates them.
        """
        if unit is None:
            caveats = caveats | {Caveat.UNDECLARED_UNIT}
        return cls(None, unit, digits, provenance, caveats, formula, reason)

    @property
    def is_missing(self) -> bool:
        """A value that was not there. It stays not there (XC-001)."""
        return self.value is None

    def formatted(self, *, missing: str = "—") -> str:
        """The number as it may be shown, at the digits it carries and no more."""
        if self.value is None:
            return missing
        return format_value(self.value, self.digits)

    def with_caveat(self, *caveats: Caveat) -> "ReportedValue":
        return replace(self, caveats=self.caveats | frozenset(caveats))

    def derive(
        self,
        value: float | None,
        *,
        formula: str,
        unit: str | None,
        others: Iterable["ReportedValue"] = (),
        digits: int | None = None,
    ) -> "ReportedValue":
        """A value computed from this one and any others, carrying every caveat of all of them.

        The union is the point. A ratio of a partial maximum to a declared allowable is still about a
        partial dataset, and the ratio is what someone reads. Digits default to the weakest input's,
        because a result is not more precise than what it was computed from.

        `unit` has no default: a caller states whether the result is in a unit, is `DIMENSIONLESS`, or
        has none declared. Defaulting it would let a ratio and an undeclared stress look identical.
        """
        inputs = (self, *others)
        return ReportedValue(
            value=value,
            unit=unit,
            digits=digits if digits is not None else min(item.digits for item in inputs),
            provenance=Provenance.COMPUTED,
            caveats=frozenset().union(*(item.caveats for item in inputs)),
            formula=formula,
        )


def caveat_notes(value: ReportedValue) -> list[str]:
    """The caveats as lines to show beside the number, in a fixed order so two reports agree."""
    return [CAVEAT_TEXT[caveat] for caveat in Caveat if caveat in value.caveats]
