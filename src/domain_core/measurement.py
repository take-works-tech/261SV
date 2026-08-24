"""Measured values imported against a @Case, and the uncertainty that has to travel with them.

@Measurement data is data (XC-125): values from a test, a rig or a sensor, imported against a @Case and
usable as a source of numbers - unlike @Reference material, which is documents and may never supply
one. Without it the word **validation** could never honestly be written, because XC-107 permits it only
where measured data is present with its own uncertainty.

**An uncertainty says which kind it is, and an expanded one says its coverage factor.** That is not a
refinement; it is the difference between two numbers that differ by a factor of two. The metrology
guidance this follows is explicit: report either the expanded uncertainty *U* **with its coverage factor
k**, or the combined standard uncertainty *u_c*; U = 2u_c is roughly 95 per cent and u_c roughly 68 per
cent, and a level of confidence differing significantly from those **must be stated** (E-070). A bare
"±0.4" is unreportable here, because a reader cannot tell whether it means 68 per cent or 95.

**No unit is ever taken from the thing being compared against.** A measured value with no declared unit
stays undeclared even when it sits beside a computed field in megapascals, because the comparison is
precisely the moment at which assuming they agree would be invisible (ingest/AC-039).

Specification: GL-035, XC-107, XC-125, ingest/AC-037, AC-038, AC-039. Evidence: E-070 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain_core.reported_value import Caveat, Provenance, ReportedValue


class UncertaintyKind(str, Enum):
    """Which uncertainty a number is, in the metrology sense (E-070)."""

    STANDARD = "standard"   # combined standard uncertainty u_c, roughly 68 per cent
    EXPANDED = "expanded"   # U = k * u_c, and k is not optional


#: The coverage factor whose omission would be conventional rather than careless, and the confidence it
#: corresponds to. Stated here so that a value using it is still written down rather than left implicit:
#: E-070's own instruction is that it is preferable to give too much information rather than too little.
CONVENTIONAL_COVERAGE = 2.0
CONVENTIONAL_CONFIDENCE = 0.95
STANDARD_CONFIDENCE = 0.68


@dataclass(frozen=True, slots=True)
class Uncertainty:
    """How far a measured value may be from the quantity it measures, and on what basis."""

    value: float
    kind: UncertaintyKind
    #: Required for an expanded uncertainty. `U = k * u_c`, and without k the number means nothing
    #: definite - "±0.4" at k=1 and at k=2 describe intervals that differ by a factor of two.
    coverage_factor: float | None = None
    #: Stated only where the reporter gave it. E-070 requires it where the level of confidence differs
    #: significantly from the conventional; carrying it always means never having to decide whether a
    #: given difference was significant.
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("an uncertainty is a magnitude and cannot be negative")
        if self.kind is UncertaintyKind.EXPANDED and self.coverage_factor is None:
            raise ValueError(
                "an expanded uncertainty carries its coverage factor k; without it the interval is "
                "undefined, and k=1 and k=2 describe intervals that differ by a factor of two (E-070)"
            )
        if self.coverage_factor is not None and self.coverage_factor <= 0:
            raise ValueError("a coverage factor is positive")
        if self.kind is UncertaintyKind.STANDARD and self.coverage_factor is not None:
            raise ValueError(
                "a standard uncertainty has no coverage factor; one given here would be read as an "
                "expanded uncertainty by a reader who trusts the label"
            )
        if self.confidence is not None and not 0.0 < self.confidence < 1.0:
            raise ValueError("a level of confidence is a fraction between 0 and 1")

    @property
    def standard(self) -> float:
        """The combined standard uncertainty u_c, whichever form was reported."""
        if self.kind is UncertaintyKind.STANDARD:
            return self.value
        assert self.coverage_factor is not None  # refused at construction
        return self.value / self.coverage_factor

    def describe(self, unit: str | None) -> str:
        """The uncertainty as it may be shown, always saying which kind it is."""
        shown = f"{self.value:g}" + (f" {unit}" if unit else "")
        if self.kind is UncertaintyKind.STANDARD:
            basis = f"合成標準不確かさ（約 {STANDARD_CONFIDENCE * 100:g}%）"
        else:
            basis = f"拡張不確かさ k={self.coverage_factor:g}"
            if self.confidence is not None:
                # `:g` rather than a fixed width: at one decimal place 99.7 per cent prints as 100,
                # which is a coverage nobody has and a digit lost in the one place it matters.
                basis += f"（{self.confidence * 100:g}%）"
            elif self.coverage_factor == CONVENTIONAL_COVERAGE:
                basis += f"（慣行として約 {CONVENTIONAL_CONFIDENCE * 100:g}%）"
        return f"±{shown}（{basis}）"


@dataclass(frozen=True, slots=True)
class MeasuredValue:
    """One value from a test, a rig or a sensor, with where it came from kept beside it."""

    name: str
    value: float
    #: `None` until a person declares one. Nothing here fills it in, and least of all the unit of the
    #: computed field it will be compared against (ingest/AC-039).
    unit: str | None = None
    uncertainty: Uncertainty | None = None
    #: Where it was measured, in the words the source used - a gauge number, a station, a thermocouple.
    at: str | None = None
    #: What produced it. Recorded rather than optional: a measured value with no stated origin is a
    #: number somebody will have to take on trust later, with nobody left to ask.
    source: str = ""
    digits: int = 6

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a measured value is named")
        if not self.source:
            raise ValueError(
                "a measured value records what produced it - a test, a rig, a sensor. One without an "
                "origin is a number nobody can go back to"
            )
        if self.digits < 1:
            raise ValueError("a value carries at least one significant digit")

    def as_reported(self) -> ReportedValue:
        """The value as this product reports numbers, carrying its provenance and its caveats."""
        caveats = frozenset() if self.unit else frozenset({Caveat.UNDECLARED_UNIT})
        return ReportedValue(
            value=self.value,
            unit=self.unit,
            digits=self.digits,
            provenance=Provenance.MEASURED,
            caveats=caveats,
            location=self.at,
        )
