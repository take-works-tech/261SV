"""Measured values, their uncertainty, and the comparison that does not deliver a verdict.

@Measurement data is data (XC-125) and is the reason the word **validation** can be written at all:
XC-107 permits it only where measured data is present with its own uncertainty. What "with its own
uncertainty" means is not a matter of taste - the metrology guidance requires either an expanded
uncertainty **with its coverage factor** or a combined standard one, because the same number means
intervals that differ by a factor of two depending on which it is (E-070).

No VTK: measurements come from a rig, not from a solver.

Verifies: ingest/AC-037, AC-038, AC-039, ingest/TASK-020, TASK-021, TASK-022.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from domain_core.comparison import combined_uncertainty, compare
from domain_core.measurement import MeasuredValue, Uncertainty, UncertaintyKind
from domain_core.reported_value import Caveat, Provenance, ReportedValue
from engine.measurements import MeasurementFileError, read_measurements

COMPUTED = ReportedValue(235.0, "MPa", 4, Provenance.COMPUTED, formula="maximum(stress)")


def measured(**changes: object) -> MeasuredValue:
    fields: dict[str, object] = {
        "name": "gauge7", "value": 231.0, "unit": "MPa", "at": "gauge 7", "source": "rig A",
        "uncertainty": Uncertainty(0.4, UncertaintyKind.EXPANDED, 2.0),
    }
    fields.update(changes)
    return MeasuredValue(**fields)  # type: ignore[arg-type]


class TestAnUncertaintySaysWhichKindItIs:
    def test_an_expanded_uncertainty_without_its_coverage_factor_is_refused(self) -> None:
        """E-070. "±0.4" at k=1 and at k=2 describe intervals that differ by a factor of two."""
        with pytest.raises(ValueError) as refusal:
            Uncertainty(0.4, UncertaintyKind.EXPANDED)
        assert "coverage factor" in str(refusal.value)

    def test_a_standard_uncertainty_carrying_a_coverage_factor_is_refused(self) -> None:
        """It would be read as an expanded one by anybody who trusts the label."""
        with pytest.raises(ValueError):
            Uncertainty(0.2, UncertaintyKind.STANDARD, 2.0)

    def test_an_expanded_uncertainty_converts_to_its_standard_form(self) -> None:
        assert Uncertainty(0.4, UncertaintyKind.EXPANDED, 2.0).standard == 0.2

    def test_the_description_always_names_the_basis(self) -> None:
        expanded = Uncertainty(0.4, UncertaintyKind.EXPANDED, 2.0).describe("MPa")
        standard = Uncertainty(0.2, UncertaintyKind.STANDARD).describe("MPa")

        assert "k=2" in expanded and "95%" in expanded
        assert "合成標準" in standard and "68%" in standard

    def test_a_stated_confidence_keeps_its_digits(self) -> None:
        """99.7 per cent printed at one decimal place becomes 100, which is a coverage nobody has."""
        assert "99.7%" in Uncertainty(0.6, UncertaintyKind.EXPANDED, 3.0, confidence=0.997).describe(None)

    def test_a_negative_uncertainty_is_refused(self) -> None:
        with pytest.raises(ValueError):
            Uncertainty(-0.1, UncertaintyKind.STANDARD)


class TestAMeasuredValueKnowsWhereItCameFrom:
    def test_it_reports_as_measured_rather_than_declared(self) -> None:
        """@Reference material may never supply a number; @Measurement data may, and the two must be
        distinguishable in the value itself (XC-125)."""
        assert measured().as_reported().provenance is Provenance.MEASURED

    def test_it_carries_where_it_was_measured(self) -> None:
        assert measured().as_reported().location == "gauge 7"

    def test_a_value_with_no_stated_origin_is_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            measured(source="")
        assert "nobody can go back to" in str(refusal.value)

    def test_an_undeclared_unit_is_marked_rather_than_borrowed(self) -> None:
        reported = measured(unit=None).as_reported()

        assert reported.unit is None
        assert Caveat.UNDECLARED_UNIT in reported.caveats


class TestTheComparisonStatesRatherThanJudges:
    def test_it_gives_the_difference_and_both_uncertainties(self) -> None:
        line = compare(COMPUTED, measured()).describe()

        assert "差 4" in line
        assert "±0.4" in line
        assert "離散化誤差は定量化されていません" in line

    def test_it_refuses_a_verdict_when_nobody_gave_a_criterion(self) -> None:
        """XC-107: validation is a quantified model error, never pass or fail unless the user defined
        the threshold."""
        comparison = compare(COMPUTED, measured())

        assert comparison.within_threshold is None
        assert "合否は述べません" in comparison.describe()

    def test_it_names_the_criterion_when_one_was_given(self) -> None:
        inside = compare(COMPUTED, measured(), threshold=10.0)
        outside = compare(COMPUTED, measured(), threshold=1.0)

        assert inside.within_threshold is True
        assert outside.within_threshold is False
        assert "判定基準 1" in outside.describe()

    def test_an_undeclared_unit_stops_the_difference(self) -> None:
        """AC-039. 231 from 235 is 4 whether both are megapascals or one is a pascal, and the answer
        looks the same either way."""
        difference = compare(COMPUTED, measured(unit=None)).difference

        assert difference.is_missing
        assert "単位を借りることはしません" in (difference.missing_because or "")

    def test_different_units_stop_the_difference_rather_than_converting(self) -> None:
        difference = compare(COMPUTED, measured(unit="Pa", value=231e6)).difference

        assert difference.is_missing
        assert "MPa" in (difference.missing_because or "")

    def test_a_missing_computed_value_says_so_rather_than_comparing(self) -> None:
        absent = ReportedValue.unavailable(
            "パーティション境界のため", unit="MPa", digits=4,
            provenance=Provenance.COMPUTED, formula="total(stress)",
        )

        assert compare(absent, measured()).difference.is_missing


class TestCombiningUncertainties:
    def test_they_combine_in_quadrature_as_standard_uncertainties(self) -> None:
        """Which is the whole reason an expanded uncertainty has to carry its k."""
        combined = combined_uncertainty(
            Uncertainty(0.4, UncertaintyKind.EXPANDED, 2.0),  # u_c = 0.2
            Uncertainty(0.15, UncertaintyKind.STANDARD),
        )

        assert combined == pytest.approx(0.25)

    def test_an_absent_contribution_is_not_treated_as_zero(self) -> None:
        """With nothing to combine the answer is None, so a caller states that it is unquantified
        rather than showing a smaller number than the truth."""
        assert combined_uncertainty(None, None) is None


class TestImportingATable:
    def write(self, tmp_path: Path, text: str) -> Path:
        path = tmp_path / "m.csv"
        path.write_text(text, encoding="utf-8")
        return path

    def test_a_declared_table_reads(self, tmp_path: Path) -> None:
        path = self.write(
            tmp_path,
            "name,value,unit,uncertainty,uncertainty_kind,coverage_factor,at,source\n"
            "gauge7,231.0,MPa,0.4,expanded,2,gauge 7,rig A\n"
            "gauge8,198.5,MPa,0.2,standard,,gauge 8,rig A\n",
        )

        values = read_measurements(path)

        assert [value.name for value in values] == ["gauge7", "gauge8"]
        assert values[0].uncertainty.kind is UncertaintyKind.EXPANDED
        assert values[1].uncertainty.coverage_factor is None

    def test_an_empty_cell_means_absent_and_never_zero(self, tmp_path: Path) -> None:
        path = self.write(tmp_path, "name,value,unit,uncertainty,source\ngauge9,12.0,,,rig A\n")

        value = read_measurements(path)[0]

        assert value.unit is None
        assert value.uncertainty is None

    def test_an_uncertainty_with_no_kind_is_refused(self, tmp_path: Path) -> None:
        path = self.write(tmp_path, "name,value,uncertainty,source\nA,1,0.4,rig\n")

        with pytest.raises(MeasurementFileError) as refusal:
            read_measurements(path)
        assert "種類が書かれていません" in str(refusal.value)

    def test_a_column_nobody_reads_is_refused_rather_than_ignored(self, tmp_path: Path) -> None:
        """Ignoring it loses data the user believes was imported."""
        path = self.write(tmp_path, "name,value,source,notes\nA,1,rig,hello\n")

        with pytest.raises(MeasurementFileError) as refusal:
            read_measurements(path)
        assert "notes" in str(refusal.value)

    def test_every_refusal_names_the_row(self, tmp_path: Path) -> None:
        path = self.write(tmp_path, "name,value,source\nA,1,rig\nB,abc,rig\n")

        with pytest.raises(MeasurementFileError) as refusal:
            read_measurements(path)
        assert "3 行目" in str(refusal.value)

    def test_a_file_with_no_measurements_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(MeasurementFileError):
            read_measurements(self.write(tmp_path, "name,value,source\n"))

    def test_a_blank_line_a_spreadsheet_left_behind_is_skipped(self, tmp_path: Path) -> None:
        path = self.write(tmp_path, "name,value,source\nA,1,rig\n,,\n")

        assert len(read_measurements(path)) == 1
