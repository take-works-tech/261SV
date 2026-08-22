"""Digits, types and comparison: the part of numerical correctness that is not arithmetic.

Every test here corresponds to a way a correct calculation still reaches the customer as a wrong
number: printed to more digits than it has, promoted by being mixed with something better, rounded
because a count was held as a float, or compared with `==`.

Specification: INV-014, INV-015, INV-016, XC-096.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from domain_core.precision import (  # noqa: E402
    DEFAULT_RELATIVE_TOLERANCE,
    PrecisionError,
    equal_within,
    format_field_value,
    format_value,
    significant_digits,
    weakest,
)


def test_single_precision_carries_fewer_digits_than_double() -> None:
    assert significant_digits(np.float32) == 6
    assert significant_digits(np.float64) == 15


def test_a_single_precision_value_is_not_printed_to_fifteen_digits() -> None:
    """The whole point: a float32 field displayed at double precision invents digits."""
    stored = np.float32(1.0 / 3.0)
    written = format_field_value(float(stored), np.float32)
    assert written == "0.333333"
    assert len(written.replace("0.", "")) == 6


def test_the_same_number_in_double_precision_keeps_its_digits() -> None:
    written = format_field_value(1.0 / 3.0, np.float64)
    assert written.startswith("0.333333333333333")


def test_mixing_precisions_takes_the_weaker() -> None:
    """numpy promotes float32 + float64 to float64; the answer is not thereby better."""
    combined = np.float32(1.0) + np.float64(1.0)
    assert combined.dtype == np.float64
    assert weakest([np.float32, np.float64]) == 6


def test_weakest_of_nothing_is_refused_rather_than_zero() -> None:
    with pytest.raises(PrecisionError):
        weakest([])


def test_counts_are_integers_end_to_end() -> None:
    """A count held as a float rounds, and a mesh acquires 999999.9999 points."""
    assert significant_digits(np.int64) == 0
    assert format_value(1_000_000, 0) == "1000000"
    assert format_field_value(np.int64(999999), np.int64) == "999999"


def test_missing_prints_as_missing_not_as_zero() -> None:
    assert format_field_value(float("nan"), np.float64) == "-"
    assert format_field_value(float("nan"), np.float64, missing="no data") == "no data"


def test_infinity_is_named_rather_than_shown_as_a_number() -> None:
    assert format_value(float("inf"), 6) == "+inf"
    assert format_value(float("-inf"), 6) == "-inf"


def test_negative_digits_are_refused() -> None:
    with pytest.raises(PrecisionError):
        format_value(1.0, -1)


def test_a_non_numeric_type_has_no_digits() -> None:
    with pytest.raises(PrecisionError):
        significant_digits(np.dtype("U8"))


def test_the_same_quantity_computed_two_ways_compares_equal() -> None:
    """0.1 + 0.2 != 0.3 in binary floating point, and that is not a disagreement about physics."""
    assert (0.1 + 0.2) != 0.3
    assert equal_within(0.1 + 0.2, 0.3)


def test_a_real_difference_still_compares_unequal() -> None:
    assert not equal_within(1.0, 1.0 + 1e-6)


def test_the_tolerance_is_relative_so_it_travels_across_magnitudes() -> None:
    """An absolute tolerance means one thing in metres and another in pascals."""
    assert equal_within(1e9, 1e9 * (1 + DEFAULT_RELATIVE_TOLERANCE / 10))
    assert equal_within(1e-9, 1e-9 * (1 + DEFAULT_RELATIVE_TOLERANCE / 10))


def test_missing_values_are_never_equal() -> None:
    """Returning True here would let a check pass on data nobody measured."""
    assert not equal_within(float("nan"), float("nan"))
    assert not equal_within(float("nan"), 1.0)


def test_a_field_reports_the_digits_of_the_type_it_was_stored_as() -> None:
    from domain_core.dataset import Association, Field

    single = Field("stress", Association.POINT, np.array([1.0 / 3.0], dtype=np.float32))
    double = Field("stress", Association.POINT, np.array([1.0 / 3.0], dtype=np.float64))
    assert single.significant_digits == 6
    assert double.significant_digits == 15
    assert single.formatted(0) == "0.333333"
    assert double.formatted(0).startswith("0.333333333333333")


def test_a_missing_entry_of_a_field_formats_as_missing() -> None:
    from domain_core.dataset import Association, Field

    values = np.array([1.0, np.nan], dtype=np.float64)
    field = Field("stress", Association.POINT, values)
    assert field.formatted(1) == "-"
    assert field.missing_count == 1
