"""The same field compared between two cases on a mesh they share.

GL-011's `not` names the dangerous version: a diff that is **a number standing alone**. This file covers
the shared-mesh case, where physical difference is all that is in the number - and every refusal here
exists so that it stays that way.

No VTK: subtraction is numpy.

Verifies: diff/AC-001 to AC-004, AC-009, AC-010, diff/TASK-001 to TASK-006.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.association import Association, AssociationError
from domain_core.dataset import Dataset, Field
from domain_core.identifiers import SourceIdentifiers
from domain_core.mesh import Cells
from engine.analysis.difference import (
    DiffError,
    Method,
    difference,
    relative_difference,
)

TRIANGLE = Cells(np.array([0, 3], np.int64), np.arange(3, dtype=np.int64), np.array([5], np.uint8))
POINTS = np.array([[0.0, 0, 0], [1, 0, 0], [0, 1, 0]])


def case(
    values: list[float],
    *,
    unit: str | None = "MPa",
    ids: list[int] | None = None,
    association: Association = Association.POINT,
) -> Dataset:
    identifiers = {}
    if ids is not None:
        identifiers[association] = SourceIdentifiers(
            global_ids=np.array(ids, np.int64), global_name="node"
        )
    count = len(values)
    return Dataset(
        points_m=POINTS[:count] if association is Association.POINT else POINTS,
        cells=TRIANGLE,
        fields={"stress": Field("stress", association, np.array(values), unit=unit)},
        identifiers=identifiers,
    )


class TestASharedMeshDiffIsASubtraction:
    def test_it_matches_a_hand_computed_value(self) -> None:
        result = difference(
            case([10.0, 20.0, 30.0]), case([1.0, 2.0, 3.0]),
            "stress", left_case="refined", right_case="baseline",
        )

        assert result.field.values.tolist() == [9.0, 18.0, 27.0]

    def test_it_keeps_the_association_of_its_sources(self) -> None:
        """INV-003: a cell diff is cell data, and nothing here promotes it."""
        result = difference(
            case([1.0], association=Association.CELL), case([0.5], association=Association.CELL),
            "stress", left_case="a", right_case="b",
        )

        assert result.field.association is Association.CELL

    def test_two_different_associations_are_refused(self) -> None:
        """Subtracting a cell value from a point value subtracts two different places."""
        with pytest.raises(AssociationError) as refusal:
            difference(
                case([1.0, 2.0, 3.0]), case([1.0], association=Association.CELL),
                "stress", left_case="a", right_case="b",
            )
        assert "別の場所どうし" in str(refusal.value)

    def test_the_result_carries_both_cases_and_the_method(self) -> None:
        """AC-009."""
        result = difference(
            case([10.0]), case([1.0]), "stress", left_case="refined", right_case="baseline"
        )

        assert "refined" in result.provenance
        assert "baseline" in result.provenance
        assert result.method is Method.SHARED_MESH


class TestIdentifiersDecideWhatMatchesWhat:
    def test_locations_match_by_identifier_rather_than_by_position(self) -> None:
        """AC-002. Array position is the same location only if both files were written the same way,
        and two runs of the same solver on the same mesh do not guarantee that."""
        left = case([10.0, 20.0, 30.0], ids=[1, 2, 3])
        right = case([3.0, 2.0, 1.0], ids=[3, 2, 1])  # same values, reversed order

        result = difference(left, right, "stress", left_case="a", right_case="b")

        assert result.field.values.tolist() == [9.0, 18.0, 27.0]
        assert result.method is Method.SHARED_MESH_BY_IDENTIFIER

    def test_matching_by_position_would_have_given_a_different_answer(self) -> None:
        """The defect that looks right for as long as nobody remeshes."""
        left_values = np.array([10.0, 20.0, 30.0])
        right_values = np.array([3.0, 2.0, 1.0])

        assert (left_values - right_values).tolist() != [9.0, 18.0, 27.0]

    def test_a_location_present_on_one_side_only_is_missing(self) -> None:
        """AC-004, INV-011. Zero is a value an engineer reads as "these agree"."""
        left = case([10.0, 20.0, 30.0], ids=[1, 2, 9])
        right = case([1.0, 2.0, 3.0], ids=[1, 2, 3])

        result = difference(left, right, "stress", left_case="a", right_case="b")

        assert result.field.values[:2].tolist() == [9.0, 18.0]
        assert np.isnan(result.field.values[2])
        assert result.unmatched == 1

    def test_the_unmatched_count_is_reported(self) -> None:
        left = case([10.0, 20.0, 30.0], ids=[1, 2, 9])
        right = case([1.0, 2.0, 3.0], ids=[1, 2, 3])

        assert "1 件は欠測" in difference(
            left, right, "stress", left_case="a", right_case="b"
        ).describe()

    def test_without_identifiers_lengths_must_agree(self) -> None:
        with pytest.raises(DiffError) as refusal:
            difference(case([1.0, 2.0, 3.0]), case([1.0, 2.0]), "stress", left_case="a", right_case="b")
        assert "対応がつきません" in str(refusal.value)


class TestUnitsAreNamedRatherThanConverted:
    def test_differing_units_are_refused_with_both_named(self) -> None:
        """AC-003. A conversion here is one nobody asked for, inside an operation whose entire output
        is a difference."""
        with pytest.raises(DiffError) as refusal:
            difference(
                case([10.0], unit="MPa"), case([1.0], unit="Pa"),
                "stress", left_case="a", right_case="b",
            )
        assert "MPa" in str(refusal.value)
        assert "Pa" in str(refusal.value)

    def test_an_undeclared_unit_on_one_side_is_refused_and_named_as_undeclared(self) -> None:
        with pytest.raises(DiffError) as refusal:
            difference(
                case([10.0], unit="MPa"), case([1.0], unit=None),
                "stress", left_case="a", right_case="b",
            )
        assert "未宣言" in str(refusal.value)

    def test_two_undeclared_units_diff_and_stay_undeclared(self) -> None:
        """Both undeclared is not a mismatch: it is two fields nobody has declared, and the difference
        is as undeclared as they are."""
        result = difference(
            case([10.0], unit=None), case([1.0], unit=None),
            "stress", left_case="a", right_case="b",
        )

        assert result.field.unit is None
        assert result.field.values.tolist() == [9.0]


class TestAMissingValuePropagates:
    def test_a_missing_value_on_either_side_gives_missing(self) -> None:
        result = difference(
            case([10.0, np.nan]), case([1.0, 2.0]), "stress", left_case="a", right_case="b"
        )

        assert result.field.values[0] == 9.0
        assert np.isnan(result.field.values[1])

    def test_it_is_never_zero(self) -> None:
        result = difference(
            case([np.nan]), case([np.nan]), "stress", left_case="a", right_case="b"
        )

        assert np.isnan(result.field.values[0])


class TestARelativeDifferenceNamesItsReference:
    def test_the_reference_must_be_one_of_the_two_cases(self) -> None:
        """AC-010. A relative difference against an unnamed denominator is a percentage nobody can
        reproduce."""
        with pytest.raises(DiffError) as refusal:
            relative_difference(
                case([10.0]), case([1.0]), "stress",
                left_case="a", right_case="b", reference="somewhere-else",
            )
        assert "再現できない百分率" in str(refusal.value)

    def test_it_divides_by_the_named_case(self) -> None:
        result = relative_difference(
            case([12.0]), case([10.0]), "stress",
            left_case="a", right_case="b", reference="b",
        )

        assert result.field.values.tolist() == [pytest.approx(0.2)]
        assert result.reference_case == "b"

    def test_the_result_is_dimensionless(self) -> None:
        result = relative_difference(
            case([12.0]), case([10.0]), "stress", left_case="a", right_case="b", reference="b"
        )

        assert result.field.unit == "1"

    def test_a_zero_reference_is_undefined_rather_than_infinite(self) -> None:
        """An infinity in a field propagates into a colour scale and takes the whole picture with it."""
        result = relative_difference(
            case([5.0, 5.0]), case([0.0, 10.0]), "stress",
            left_case="a", right_case="b", reference="b",
        )

        assert np.isnan(result.field.values[0])
        assert result.undefined_reference == 1
        assert np.isinf(result.field.values).sum() == 0

    def test_it_says_how_many_were_undefined(self) -> None:
        result = relative_difference(
            case([5.0]), case([0.0]), "stress", left_case="a", right_case="b", reference="b"
        )

        assert "未定義" in result.describe()
        assert "無限大ではありません" in result.describe()

    def test_the_provenance_shows_the_division(self) -> None:
        result = relative_difference(
            case([12.0]), case([10.0]), "stress", left_case="a", right_case="b", reference="b"
        )

        assert result.provenance.endswith("/ b")
