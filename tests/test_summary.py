"""A summary statistic that says how it was reduced - INV-017's own checked_by, made executable.

The invariant calls this "the single easiest way for this product to be confidently wrong", and the
arithmetic is why: the mean of a field over an unstructured mesh weights a millimetre-sized element the
same as a metre-sized one. Both reductions are defensible and they are **different numbers**, so an
"average" that does not say which it is has not been reported.

INV-017 names the test it wants: a mesh with deliberately non-uniform element sizes, asserting the two
reductions differ and that each output carries its weighting label. That is `TestTheTwoReductionsDiffer`
below, on a mesh whose two cells differ in volume by a factor of a thousand.

The labelling and refusal rules need no toolkit and are tested without one.

Verifies: INV-017, graph/AC-022 to AC-024, graph/TASK-018 to TASK-020, XC-245.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.association import Association
from engine.analysis.summary import (
    DEFAULT_WEIGHTING,
    WEIGHTABLE,
    Reduction,
    Summary,
    SummaryError,
    Weighting,
    dual_volumes,
    summarise,
)

VALUES = [10.0, 20.0, 30.0, 40.0]
BIG_AND_SMALL = [1000.0, 1.0, 1.0, 1.0]  # one cell a thousand times the others


class TestTheDefaultSaysWhatItWeightedBy:
    def test_cell_data_defaults_to_volume_weighted(self) -> None:
        """INV-017."""
        assert DEFAULT_WEIGHTING[Association.CELL] is Weighting.VOLUME

    def test_point_data_defaults_to_dual_volume_weighted(self) -> None:
        assert DEFAULT_WEIGHTING[Association.POINT] is Weighting.DUAL_VOLUME

    def test_the_default_is_used_when_nothing_is_chosen(self) -> None:
        found = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=BIG_AND_SMALL,
        )

        assert found.weighting is Weighting.VOLUME

    def test_the_weighting_is_in_the_line_the_value_is_shown_as(self) -> None:
        """AC-023: everywhere it appears. The place a label goes missing is the place somebody reads the
        number, so it travels on the value rather than beside it."""
        found = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=BIG_AND_SMALL, unit="MPa",
        )

        assert "体積加重" in found.describe()
        assert "MPa" in found.describe()

    def test_an_unweighted_reduction_is_labelled_unweighted(self) -> None:
        found = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert found.is_unweighted
        assert "重みなし" in found.describe()

    def test_min_and_max_are_not_weighted_at_all(self) -> None:
        """An entry does not become larger for occupying more space, so weighting one would be
        arithmetic nobody asked for."""
        assert Reduction.MIN not in WEIGHTABLE
        assert Reduction.MAX not in WEIGHTABLE

        found = summarise(
            VALUES, reduction=Reduction.MAX, association=Association.CELL,
            scope="全体", weights=BIG_AND_SMALL,
        )

        assert found.value == 40.0
        assert found.weighting is Weighting.NONE


class TestTheTwoReductionsDiffer:
    """INV-017's checked_by, on a mesh with deliberately non-uniform element sizes."""

    def test_weighted_and_unweighted_are_different_numbers(self) -> None:
        weighted = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=BIG_AND_SMALL,
        )
        arithmetic = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert weighted.value != arithmetic.value
        assert arithmetic.value == pytest.approx(25.0)
        # The large cell holds 10.0, so weighting pulls the average towards it.
        assert weighted.value == pytest.approx((10.0 * 1000 + 20 + 30 + 40) / 1003.0)

    def test_each_carries_its_own_label(self) -> None:
        weighted = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=BIG_AND_SMALL,
        )
        arithmetic = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert "体積加重" in weighted.describe()
        assert "重みなし" in arithmetic.describe()

    def test_the_difference_is_large_enough_to_change_a_verdict(self) -> None:
        """Not a rounding difference. 25.0 against 10.09 is the gap between passing a limit and not."""
        weighted = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weights=BIG_AND_SMALL,
        )

        assert abs((weighted.value or 0) - 25.0) > 10.0


class TestAWeightedReductionIsNeverDowngraded:
    def test_asking_for_one_without_weights_is_refused(self) -> None:
        """The downgrade produces a different number under the label of the one that was asked for,
        which is this invariant's whole subject."""
        with pytest.raises(SummaryError) as refusal:
            summarise(VALUES, reduction=Reduction.MEAN, association=Association.CELL, scope="全体")

        assert "INV-017" in str(refusal.value)

    def test_weights_of_the_wrong_length_are_refused(self) -> None:
        with pytest.raises(SummaryError):
            summarise(
                VALUES, reduction=Reduction.MEAN, association=Association.CELL,
                scope="全体", weights=[1.0, 2.0],
            )

    def test_weights_summing_to_zero_make_it_unavailable(self) -> None:
        found = summarise(
            VALUES, reduction=Reduction.MEAN, association=Association.CELL,
            scope="表面のみ", weights=[0.0, 0.0, 0.0, 0.0],
        )

        assert found.value is None
        assert "0" in (found.unavailable or "")


class TestAnEmptyScopeIsUnavailableRatherThanZero:
    def test_no_entries_at_all(self) -> None:
        """AC-024. Zero is a number a reader will compare against a limit."""
        found = summarise(
            [], reduction=Reduction.MEAN, association=Association.CELL, scope="空の範囲",
            weighting=Weighting.NONE,
        )

        assert found.value is None
        assert "0 は返しません" in (found.unavailable or "")

    def test_every_entry_missing(self) -> None:
        found = summarise(
            [float("nan")] * 3, reduction=Reduction.MEAN, association=Association.POINT,
            scope="欠測だけの範囲", weighting=Weighting.NONE,
        )

        assert found.value is None
        assert found.skipped == 3

    def test_missing_entries_are_excluded_and_counted(self) -> None:
        found = summarise(
            [10.0, float("nan"), 30.0], reduction=Reduction.MEAN,
            association=Association.CELL, scope="全体", weighting=Weighting.NONE,
        )

        assert found.value == pytest.approx(20.0)
        assert found.skipped == 1
        assert "欠測 1 件" in found.describe()

    def test_a_summary_with_no_value_and_no_reason_cannot_be_built(self) -> None:
        with pytest.raises(SummaryError):
            Summary(Reduction.MEAN, Weighting.NONE, "全体")

    def test_the_unavailable_line_says_so_rather_than_printing_a_number(self) -> None:
        found = summarise(
            [], reduction=Reduction.MEAN, association=Association.CELL, scope="空の範囲",
            weighting=Weighting.NONE,
        )

        assert "求められません" in found.describe()


class TestTheOtherReductions:
    def test_an_integral_is_not_a_mean(self) -> None:
        """Calling a weighted sum an average would divide by a total nobody asked about."""
        found = summarise(
            [2.0, 2.0], reduction=Reduction.INTEGRAL, association=Association.CELL,
            scope="全体", weights=[3.0, 5.0],
        )

        assert found.value == pytest.approx(16.0)

    def test_a_weighted_standard_deviation_uses_the_weighted_mean(self) -> None:
        found = summarise(
            [10.0, 20.0], reduction=Reduction.STANDARD_DEVIATION,
            association=Association.CELL, scope="全体", weights=[1.0, 1.0],
        )

        assert found.value == pytest.approx(5.0)

    def test_one_value_has_no_spread(self) -> None:
        with pytest.raises(SummaryError):
            summarise(
                [10.0], reduction=Reduction.STANDARD_DEVIATION,
                association=Association.CELL, scope="全体", weighting=Weighting.NONE,
            )


class TestDualVolumesSumBackToTheTotal:
    def test_each_cell_shares_its_volume_among_its_points(self) -> None:
        shares = dual_volumes([8.0], [[0, 1, 2, 3]], points=4)

        assert list(shares) == [2.0, 2.0, 2.0, 2.0]

    def test_the_shares_sum_to_the_total_volume(self) -> None:
        """The property a weighting has to have. One that did not would make the average depend on how
        the mesh was cut rather than on where the material is."""
        shares = dual_volumes([8.0, 1.0], [[0, 1, 2, 3], [2, 3, 4, 5]], points=6)

        assert float(np.sum(shares)) == pytest.approx(9.0)

    def test_a_point_no_cell_uses_keeps_a_weight_of_zero(self) -> None:
        shares = dual_volumes([8.0], [[0, 1, 2, 3]], points=5)

        assert shares[4] == 0.0
