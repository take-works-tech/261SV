"""One list of quantities, where every entry says where it came from.

XC-088 puts values a person typed, values a solver produced, values an expression computed and values
taken from reference material in **one list**, because a user wanting "the yield strength" should not
have to know which of four places it lives in. INV-013 is the price of that convenience: mixing them is
useful, and **mixing them invisibly would make every number in the product unfalsifiable**.

Three things this list does that a plainer one would not.

**A computed entry carries its expression** (AC-019). Not as a tooltip - as part of the entry, because
"3.4" and "3.4 = allowable / maximum" are different claims and only the second can be checked.

**A quantity that cannot be evaluated for a case is present and marked unavailable** (AC-020), never
omitted. An entry that disappears reads as a quantity that does not apply; one marked unavailable reads
as a quantity that does apply and could not be worked out, which is what happened.

**Reference material appears and can supply nothing.** XC-013 forbids it as a source of numbers, and
leaving it out of the list would hide that a value the user is looking for exists in a document the
product declines to read a number from. It is listed, and its value is absent by rule rather than by
accident.

Specification: XC-088, INV-013, INV-014, workspace/AC-018 to AC-021.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from domain_core.dataset import Dataset
from domain_core.measurement import MeasuredValue
from domain_core.precision import digits_written, significant_digits
from domain_core.reported_value import Caveat, Provenance, ReportedValue
from service.workspace.variables import resolve

#: What a reference-material entry says instead of a value. Reference material is documents; a number
#: in one is a number nobody can trace to a run, so it is listed and never read from (XC-013).
REFERENCE_SUPPLIES_NO_VALUE = (
    "参照資料は数値を供給しません。値が必要な場合は、@Measurement として取り込むか、"
    "変数として宣言してください（XC-013, XC-125）"
)


@dataclass(frozen=True, slots=True)
class Quantity:
    """One row of the list: what it is called, what it is worth here, and where that came from."""

    identifier: str
    name: str
    reported: ReportedValue

    @property
    def provenance(self) -> Provenance:
        return self.reported.provenance

    @property
    def is_available(self) -> bool:
        return not self.reported.is_missing

    def describe(self) -> str:
        """The row as a person reads it. Provenance is never optional and never abbreviated away."""
        origin = _PROVENANCE_WORD[self.provenance]
        if self.reported.is_missing:
            return f"{self.name}（{origin}）：{self.reported.missing_because or '値がありません'}"
        unit = self.reported.unit
        shown = self.reported.formatted() + (
            f" {unit}" if unit and unit != "1" else ("（単位未宣言）" if unit is None else "")
        )
        line = f"{self.name}（{origin}）：{shown}"
        if self.reported.formula:
            # AC-019. "3.4" and "3.4 = allowable / maximum" are different claims, and only the second
            # can be checked.
            line += f" = {self.reported.formula}"
        return line


_PROVENANCE_WORD = {
    Provenance.DECLARED: "宣言",
    Provenance.DATASET: "データ",
    Provenance.COMPUTED: "計算",
    Provenance.MEASURED: "実測",
    Provenance.REFERENCE: "参照資料",
}


def _from_variables(document: dict[str, Any], case_id: str) -> list[Quantity]:
    found: list[Quantity] = []
    for declaration in document.get("variables", []):
        identifier = str(declaration.get("id", ""))
        resolution = resolve(document, case_id, identifier)
        if resolution.declared_on and not resolution.is_resolved:
            # Declared on a case this one cannot see. Not this case's quantity at all, rather than one
            # of its quantities that is unavailable - the distinction AC-020 is not about.
            continue
        name = str(declaration.get("name", identifier))
        stated = str(declaration.get("provenance", Provenance.DECLARED.value))
        provenance = Provenance(stated) if stated in {p.value for p in Provenance} else Provenance.DECLARED
        unit = resolution.unit
        caveats = frozenset({Caveat.UNDECLARED_UNIT}) if unit is None else frozenset()

        if provenance is Provenance.REFERENCE:
            reported = ReportedValue.unavailable(
                REFERENCE_SUPPLIES_NO_VALUE, unit=unit, digits=1,
                provenance=Provenance.REFERENCE, caveats=caveats,
            )
        elif not resolution.is_resolved:
            reported = ReportedValue.unavailable(
                resolution.unresolved_because or "解決できません", unit=unit, digits=1,
                provenance=provenance, caveats=caveats,
                formula=declaration.get("expression") if provenance is Provenance.COMPUTED else None,
            )
        else:
            number = _as_number(resolution.value)
            reported = ReportedValue(
                value=number,
                unit=unit,
                # What the value distinguishes, not a default. A variable somebody typed as 1.17 shown
                # as 1.17000 is the padded expansion INV-014 calls a claim the data cannot support.
                digits=digits_written(number) if number is not None else 1,
                provenance=provenance,
                caveats=caveats,
                formula=declaration.get("expression") if provenance is Provenance.COMPUTED else None,
                missing_because=(
                    None if number is not None else f"'{name}' の値が数値ではありません"
                ),
            )
        found.append(Quantity(identifier, name, reported))
    return found


def _as_number(value: Any) -> float | None:
    """A variable may hold text or a structure; only a number is a number."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _from_dataset(dataset: Dataset, prefix: str) -> list[Quantity]:
    found: list[Quantity] = []
    for name, field in sorted(dataset.fields.items()):
        caveats = dataset.caveats()
        if field.unit is None:
            caveats = caveats | {Caveat.UNDECLARED_UNIT}
        # The field itself is a quantity with many values, so the list carries what it is rather than
        # one of them: its extent, its association and its unit. A single number would be a choice of
        # which entry to show, and nothing here has the standing to make it.
        found.append(
            Quantity(
                identifier=f"{prefix}.{name}",
                name=name,
                reported=ReportedValue.unavailable(
                    f"{field.values.size} 件の値を持つ{field.association.value}フィールドです。"
                    "一つの数値としては表示しません",
                    unit=field.unit, digits=significant_digits(field.values.dtype),
                    provenance=Provenance.DATASET, caveats=caveats,
                ),
            )
        )
    return found


def _from_measurements(measurements: Iterable[MeasuredValue]) -> list[Quantity]:
    return [
        Quantity(f"measured.{value.name}", value.name, value.as_reported())
        for value in measurements
    ]


def quantity_list(
    document: dict[str, Any],
    case_id: str,
    *,
    dataset: Dataset | None = None,
    measurements: Iterable[MeasuredValue] = (),
) -> tuple[Quantity, ...]:
    """Every quantity available on one case, from every origin, each saying which origin.

    Ordered by provenance and then by name, so the same case produces the same list twice - a list
    whose order depends on a dictionary's iteration is a list two screenshots disagree about.
    """
    found = _from_variables(document, case_id)
    if dataset is not None:
        found += _from_dataset(dataset, case_id)
    found += _from_measurements(measurements)
    order = list(_PROVENANCE_WORD)
    return tuple(sorted(found, key=lambda q: (order.index(q.provenance), q.name)))
