"""One list of quantities, every entry saying where it came from (INV-013, AC-018 to AC-021).

XC-088 puts values a person typed, values a solver produced, values an expression computed and values
from reference material in one list, because a user wanting "the yield strength" should not have to know
which of four places it lives in. INV-013 is the price: mixing them is useful, and mixing them invisibly
would make every number in the product unfalsifiable.

Verifies: workspace/AC-018, AC-019, AC-020, AC-021, workspace/TASK-017 to TASK-020.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from domain_core.dataset import Association, Dataset, Field
from domain_core.measurement import MeasuredValue, Uncertainty, UncertaintyKind
from domain_core.mesh import Cells
from domain_core.precision import digits_written
from domain_core.reported_value import Provenance
from service.workspace.hierarchy import add, new_case
from service.workspace.quantities import quantity_list
from service.workspace.variables import declare

TRIANGLE = Cells(np.array([0, 3], np.int64), np.arange(3, dtype=np.int64), np.array([5], np.uint8))


def workspace() -> dict[str, Any]:
    document: dict[str, Any] = {
        "formatVersion": "4.0.0", "id": "w", "cases": [], "variables": [], "workspaceItems": {},
    }
    add(document["cases"], new_case("c1", "baseline"))
    declare(document, "allowable", "許容応力", 235.0, unit="MPa")
    declare(document, "bare", "単位未宣言の値", 12.0)
    document["variables"] += [
        {"id": "sf", "name": "安全率", "value": 1.17, "unit": "1",
         "provenance": "computed", "expression": "allowable / maximum"},
        {"id": "code", "name": "JIS の許容値", "value": None, "unit": "MPa", "provenance": "reference"},
        {"id": "broken", "name": "評価できない量", "provenance": "computed", "expression": "a / b"},
    ]
    return document


def dataset(dtype: Any = np.float32) -> Dataset:
    return Dataset(
        points_m=np.zeros((3, 3)),
        cells=TRIANGLE,
        fields={"stress": Field("stress", Association.POINT, np.arange(3, dtype=dtype), unit="MPa")},
    )


def by_name(document: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return {q.name: q for q in quantity_list(document, "c1", **kwargs)}


class TestEveryOriginInOneList:
    def test_all_four_origins_appear_together(self) -> None:
        measured = MeasuredValue("gauge7", 231.0, "MPa", source="rig A")

        found = by_name(workspace(), dataset=dataset(), measurements=[measured])

        assert {q.provenance for q in found.values()} == {
            Provenance.DECLARED, Provenance.DATASET, Provenance.COMPUTED,
            Provenance.MEASURED, Provenance.REFERENCE,
        }

    def test_each_entry_names_its_origin(self) -> None:
        """INV-013: never shown without provenance."""
        found = by_name(workspace())

        assert "（宣言）" in found["許容応力"].describe()
        assert "（計算）" in found["安全率"].describe()
        assert "（参照資料）" in found["JIS の許容値"].describe()

    def test_the_order_is_the_same_twice(self) -> None:
        """A list whose order depends on a dictionary's iteration is a list two screenshots disagree
        about."""
        document = workspace()

        assert [q.identifier for q in quantity_list(document, "c1")] == [
            q.identifier for q in quantity_list(document, "c1")
        ]

    def test_a_value_with_no_declared_unit_says_so(self) -> None:
        assert "単位未宣言" in by_name(workspace())["単位未宣言の値"].describe()


class TestAComputedEntryCarriesItsExpression:
    def test_the_expression_is_part_of_the_entry(self) -> None:
        """AC-019. "1.17" and "1.17 = allowable / maximum" are different claims, and only the second
        can be checked."""
        line = by_name(workspace())["安全率"].describe()

        assert "= allowable / maximum" in line

    def test_a_declared_value_has_no_expression_to_show(self) -> None:
        assert by_name(workspace())["許容応力"].reported.formula is None


class TestUnavailableRatherThanAbsent:
    def test_a_quantity_that_cannot_be_evaluated_is_still_listed(self) -> None:
        """AC-020. An entry that disappears reads as a quantity that does not apply; one marked
        unavailable reads as one that does apply and could not be worked out."""
        found = by_name(workspace())

        assert "評価できない量" in found
        assert found["評価できない量"].is_available is False

    def test_reference_material_is_listed_and_supplies_nothing(self) -> None:
        """XC-013 forbids it as a source of numbers. Leaving it out would hide that the value the user
        is looking for exists in a document the product declines to read a number from."""
        entry = by_name(workspace())["JIS の許容値"]

        assert entry.provenance is Provenance.REFERENCE
        assert entry.is_available is False
        assert "@Measurement" in (entry.reported.missing_because or "")

    def test_a_field_is_listed_as_a_field_rather_than_as_one_of_its_values(self) -> None:
        """Showing one number would be a choice of which entry to show, and nothing here has the
        standing to make it."""
        entry = by_name(workspace(), dataset=dataset())["stress"]

        assert entry.provenance is Provenance.DATASET
        assert "3 件の値" in (entry.reported.missing_because or "")

    def test_a_variable_declared_on_another_case_is_absent_rather_than_unavailable(self) -> None:
        """Not this case's quantity at all - a different thing from one of its quantities that could
        not be worked out."""
        document = workspace()
        add(document["cases"], new_case("other", "別"))
        declare(document, "local", "別ケースの値", 1.0, on_case="other")

        assert "別ケースの値" not in by_name(document)


class TestDigitsComeFromWhatTheValueDistinguishes:
    def test_a_typed_value_is_not_padded(self) -> None:
        """INV-014 calls a padded decimal expansion "a claim the data cannot support". 1.17 shown as
        1.17000 is exactly that claim."""
        assert by_name(workspace())["安全率"].describe().count("1.17") == 1
        assert "1.17000" not in by_name(workspace())["安全率"].describe()

    def test_an_integral_value_keeps_its_own_digits(self) -> None:
        assert digits_written(235.0) == 3
        assert digits_written(12.0) == 2

    def test_a_full_precision_double_is_capped_at_what_storage_carries(self) -> None:
        assert digits_written(1 / 3) == 15

    def test_a_single_precision_field_is_listed_with_single_precision_digits(self) -> None:
        """AC-021 through the same shared component every other display uses."""
        single = by_name(workspace(), dataset=dataset(np.float32))["stress"]
        double = by_name(workspace(), dataset=dataset(np.float64))["stress"]

        assert single.reported.digits == 6
        assert double.reported.digits == 15


class TestMeasuredValuesJoinTheSameList:
    def test_a_measured_entry_reports_as_measured(self) -> None:
        measured = MeasuredValue(
            "gauge7", 231.0, "MPa",
            Uncertainty(0.4, UncertaintyKind.EXPANDED, 2.0), at="gauge 7", source="rig A",
        )

        entry = by_name(workspace(), measurements=[measured])["gauge7"]

        assert entry.provenance is Provenance.MEASURED
        assert entry.reported.location == "gauge 7"
