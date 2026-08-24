"""Tests for the unit rules.

The product's position is that a unit is declared or it is absent, and an absent unit stops a
conversion rather than defaulting to one. These tests exist to make that refusal permanent.

Verifies: ingest/AC-024, ingest/AC-025.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain_core.dataset import Association, Field  # noqa: E402
from domain_core.units import UndeclaredUnitError, convert, to_internal, unit  # noqa: E402


def test_conversion_between_declared_units() -> None:
    assert convert(1000.0, "mm", "m") == pytest.approx(1.0)
    assert convert(1.0, "MPa", "Pa") == pytest.approx(1.0e6)


def test_undeclared_unit_refuses_conversion() -> None:
    """ingest/AC-024: no unit declared means no conversion, not a guessed one."""
    with pytest.raises(UndeclaredUnitError) as error:
        convert(1.0, None, "m")
    assert "no declared unit" in str(error.value)


def test_unknown_symbol_is_refused_rather_than_guessed() -> None:
    with pytest.raises(UndeclaredUnitError):
        unit("furlong")


def test_quantities_do_not_convert_into_each_other() -> None:
    with pytest.raises(UndeclaredUnitError) as error:
        convert(1.0, "mm", "Pa")
    assert "length" in str(error.value) and "pressure" in str(error.value)


def test_to_internal_refuses_without_a_declaration() -> None:
    with pytest.raises(UndeclaredUnitError):
        to_internal(1.0, None)
    assert to_internal(1000.0, "mm") == pytest.approx(1.0)


def test_a_field_carries_its_declaration_only_when_given_one() -> None:
    """ingest/AC-025: a field without a declaration stays without one until a person declares it."""
    values = np.array([1.0, 2.0, 3.0])
    field = Field("stress", Association.POINT, values)

    assert field.unit is None
    declared = field.declared("MPa")
    assert declared.unit == "MPa"
    assert field.unit is None, "declaring a unit returns a new field rather than mutating the old one"


def test_missing_values_are_counted_not_hidden() -> None:
    """INV-011: missing is NaN, and the count is available rather than silently swallowed."""
    field = Field("stress", Association.POINT, np.array([1.0, np.nan, 3.0]))
    assert field.missing_count == 1


def test_celsius_is_affine_not_a_factor() -> None:
    """A factor-only conversion puts every Celsius value 273.15 K too low, and it looks plausible."""
    assert convert(0.0, "degC", "K") == pytest.approx(273.15)
    assert convert(100.0, "degC", "K") == pytest.approx(373.15)
    assert convert(273.15, "K", "degC") == pytest.approx(0.0)


def test_fahrenheit_round_trips() -> None:
    assert convert(212.0, "degF", "K") == pytest.approx(373.15)
    assert convert(100.0, "degC", "degF") == pytest.approx(212.0)
    assert convert(-40.0, "degC", "degF") == pytest.approx(-40.0)


def test_a_temperature_difference_carries_no_offset() -> None:
    """A rise of 10 degrees Celsius is 10 K, not 283.15 K (INV-028)."""
    assert convert(10.0, "degC", "K", difference=True) == pytest.approx(10.0)
    assert convert(18.0, "degF", "K", difference=True) == pytest.approx(10.0)


def test_the_difference_flag_changes_nothing_for_a_pure_factor() -> None:
    """Only offsets distinguish the two, so length must be identical either way."""
    assert convert(5.0, "mm", "m") == convert(5.0, "mm", "m", difference=True)


def test_an_undeclared_unit_is_still_refused_for_a_difference() -> None:
    with pytest.raises(UndeclaredUnitError):
        convert(10.0, None, "K", difference=True)


class TestTheQuantityDeclaresWhichItIs:
    """INV-028: "A quantity is declared as one or the other, and a quantity declared as neither is
    treated as absolute." Declared - not chosen at each conversion. A call-site flag is right at every
    site somebody thought about and wrong at the one they did not, and the wrong direction here stays in
    a plausible range: a temperature difference converted with the offset is inflated by 273.15 and
    looks like a temperature."""

    def test_an_absolute_declaration_gets_the_offset(self) -> None:
        from domain_core.units import convert_declared

        assert convert_declared(10.0, "degC", "K", {"kind": "absolute"}) == pytest.approx(283.15)

    def test_a_difference_declaration_does_not(self) -> None:
        from domain_core.units import convert_declared

        assert convert_declared(10.0, "degC", "K", {"kind": "difference"}) == pytest.approx(10.0)

    def test_a_declaration_that_says_nothing_is_absolute(self) -> None:
        """Fixed by the invariant rather than left to a default argument."""
        from domain_core.units import DEFAULT_KIND, Kind, convert_declared

        assert DEFAULT_KIND is Kind.ABSOLUTE
        assert convert_declared(10.0, "degC", "K", {}) == pytest.approx(283.15)

    def test_a_field_answers_the_same_way_as_a_mapping(self) -> None:
        """A @Variable, a @Field and a raw mapping read from a document all state it the same way, so
        no caller has to know which it is holding."""
        from types import SimpleNamespace

        from domain_core.units import Kind, kind_of

        assert kind_of(SimpleNamespace(kind="difference")) is Kind.DIFFERENCE
        assert kind_of({"kind": "difference"}) is Kind.DIFFERENCE

    def test_a_kind_this_build_does_not_recognise_is_refused(self) -> None:
        """A typo in a stored document must not silently choose the conversion."""
        from domain_core.units import UndeclaredUnitError, kind_of

        with pytest.raises(UndeclaredUnitError) as refusal:
            kind_of({"kind": "relatve"})
        assert "INV-028" in str(refusal.value)
