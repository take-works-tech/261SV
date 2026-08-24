"""Putting a computed value beside a measured one, and saying what that comparison does not settle.

This is where the word **validation** becomes available, and XC-107 governs it tightly: validation is
reported as a **quantified model error, never as pass or fail** unless the user defined the threshold,
which is then named. So a comparison here produces a difference and both uncertainties, and produces a
verdict only when someone supplied the criterion it is measured against.

Two refusals do most of the work, and each exists because the alternative is invisible.

**A difference across an undeclared unit is not computed.** Subtracting 231 from 235 gives 4 whether
the two are both megapascals or one is a pascal, and nothing in the answer shows which. The measured
value keeps its own unit or keeps none; it never borrows the computed field's (ingest/AC-039).

**A computed value with no uncertainty is said to have none**, rather than being treated as exact. A
discretisation error that has not been quantified is a fact about the study, and XC-107 requires the
report to state it rather than omit the subject.

Specification: XC-107, XC-125, ingest/AC-038, AC-039. Evidence: E-070 (T1).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from domain_core.measurement import MeasuredValue, Uncertainty
from domain_core.reported_value import Caveat, Provenance, ReportedValue


@dataclass(frozen=True, slots=True)
class Comparison:
    """One computed value beside one measured value, with what separates them."""

    computed: ReportedValue
    measured: MeasuredValue
    #: The difference, computed minus measured. Missing where it cannot honestly be formed - which is
    #: a result, not a failure, and `difference.missing_because` says which case it was.
    difference: ReportedValue
    #: The user's criterion, where a user gave one. Nothing here supplies a default: a threshold this
    #: product chose would turn its own convention into somebody's engineering verdict.
    threshold: float | None = None

    @property
    def within_threshold(self) -> bool | None:
        """Whether the difference is inside the criterion, or None where no criterion was given.

        None rather than True. An absent threshold is an absent question, and answering it anyway is
        exactly the pass-or-fail XC-107 forbids.
        """
        if self.threshold is None or self.difference.value is None:
            return None
        return abs(self.difference.value) <= self.threshold

    def describe(self) -> str:
        """The comparison as a report may state it: both values, both uncertainties, no verdict unless
        one was asked for."""
        # A computed value carries no uncertainty in this build - nothing quantifies discretisation
        # error yet - and XC-107 requires the report to **state that** rather than omit the subject,
        # because a bare computed figure beside a measured one with error bars reads as the exact one.
        lines = [
            f"計算値 {self.computed.formatted()}"
            + (f" {self.computed.unit}" if self.computed.unit else "")
            + "（離散化誤差は定量化されていません）",
            f"実測値 {self.measured.value:g}"
            + (f" {self.measured.unit}" if self.measured.unit else "")
            + (
                " " + self.measured.uncertainty.describe(self.measured.unit)
                if self.measured.uncertainty
                else "（不確かさの申告がありません）"
            ),
        ]
        if self.difference.is_missing:
            lines.append(f"差は求められません：{self.difference.missing_because}")
        else:
            lines.append(f"差 {self.difference.formatted()}")
            if self.threshold is None:
                lines.append("判定基準が指定されていないため、合否は述べません")
            else:
                verdict = "基準内" if self.within_threshold else "基準外"
                lines.append(f"判定基準 {self.threshold:g} に対して {verdict}")
        return "。".join(lines)


def compare(
    computed: ReportedValue,
    measured: MeasuredValue,
    *,
    threshold: float | None = None,
) -> Comparison:
    """A computed value against a measured one, refusing the difference where it would mislead."""
    caveats = computed.caveats | (
        frozenset({Caveat.UNDECLARED_UNIT}) if measured.unit is None else frozenset()
    )
    formula = f"{computed.formula or 'computed'} - {measured.name}"

    def refuse(reason: str) -> ReportedValue:
        return ReportedValue.unavailable(
            reason, unit=computed.unit, digits=computed.digits,
            provenance=Provenance.COMPUTED, caveats=caveats, formula=formula,
        )

    if computed.is_missing:
        difference = refuse(
            "計算値がありません：" + (computed.missing_because or "理由の記録がありません")
        )
    elif computed.unit is None or measured.unit is None:
        # The refusal AC-039 is about. 231 from 235 is 4 whether both are MPa or one is Pa, and the
        # answer looks the same either way.
        which = "計算値" if computed.unit is None else "実測値"
        difference = refuse(
            f"{which}の単位が宣言されていないため、差は求められません。"
            "比較対象の単位を借りることはしません（XC-003）"
        )
    elif computed.unit != measured.unit:
        difference = refuse(
            f"単位が異なります（計算値 {computed.unit}、実測値 {measured.unit}）。"
            "換算は明示的に求められたときにだけ行います"
        )
    else:
        difference = ReportedValue(
            value=computed.value - measured.value,
            unit=computed.unit,
            digits=min(computed.digits, measured.digits),
            provenance=Provenance.COMPUTED,
            caveats=caveats,
            formula=formula,
        )

    return Comparison(computed=computed, measured=measured, difference=difference,
                      threshold=threshold)


def combined_uncertainty(*uncertainties: Uncertainty | None) -> float | None:
    """The uncertainties combined in quadrature, as standard uncertainties, or None if none was given.

    In quadrature because that is how independent contributions combine; each is converted to its
    standard form first, which is the whole reason an expanded uncertainty has to carry its k (E-070).
    A missing contribution is **not** treated as zero: with nothing to combine the answer is None, and
    a caller states that it is unquantified rather than showing a smaller number than the truth.
    """
    present = [item.standard for item in uncertainties if item is not None]
    if not present:
        return None
    return math.sqrt(sum(value * value for value in present))
