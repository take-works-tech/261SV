"""The expression language: what it computes, what it refuses, and when it refuses it.

XC-101's rule is that there is no interpreter behind this language, so a workspace from an untrusted
source can be opened and its formulas read without running anything. XC-242's rule is that a unit
travels through an expression as a dimension, so a length over a time is a velocity and a length plus a
time is refused naming both.

The refusals here are the point rather than the arithmetic. Three of them cost the user something and
each buys back a wrong number that would have looked right: `stress > 200` with no unit, two absolute
temperatures added, and a name that is not bound at that position.

Verifies: pipeline/AC-030 to AC-032, pipeline/TASK-011 to TASK-013, XC-242, E-141.
"""

from __future__ import annotations

import math
import pathlib
import re

import pytest

from domain_core.dimension import DIMENSIONLESS, Dimension, dimension_of, symbol_for
from engine.analysis import expression
from engine.analysis.expression import (
    ExpressionError,
    Value,
    check,
    evaluate,
    names_in,
    parse,
    quantity,
)

STRESS = {"stress": quantity(150.0, "MPa")}


class TestADimensionIsWhatDecides:
    def test_pressure_is_not_a_base_quantity(self) -> None:
        """The reason the table exists: Pa is kg/(m s^2), so an enumeration of quantities cannot be the
        thing arithmetic works on."""
        assert dimension_of("Pa") == Dimension(mass=1, length=-1, time=-2)

    def test_a_dimension_that_matches_a_known_quantity_prints_its_symbol(self) -> None:
        """`Pa`, not `kg·m^-1·s^-2` - the composed form is correct and unreadable."""
        assert symbol_for(dimension_of("MPa")) == "Pa"

    def test_anything_else_is_composed_in_a_fixed_order(self) -> None:
        assert symbol_for(dimension_of("m").over(dimension_of("s"))) == "m·s^-1"

    def test_a_dimensionless_quantity_is_written_as_one_rather_than_as_nothing(self) -> None:
        """SI writes a quantity that genuinely has no unit - a ratio, a safety factor - as `1`. It is
        **not** the same as a unit nobody declared, and conflating the two makes every safety factor
        look like a stress whose unit went missing.

        The first version of this asserted `symbol_for(DIMENSIONLESS) is None`, which made the two
        indistinguishable in exactly the way `reported_value` warns about.
        """
        assert symbol_for(DIMENSIONLESS) == "1"

    def test_a_ratio_of_two_declared_lengths_is_dimensionless_and_says_so(self) -> None:
        assert evaluate("1 m / 1 m").describe() == "1 1"

    def test_a_product_of_two_bare_numbers_is_still_undeclared(self) -> None:
        """Giving it `1` would be this product declaring a unit on somebody's behalf (XC-003)."""
        assert "宣言されていません" in evaluate("2 * 3").describe()

    def test_an_odd_exponent_has_no_square_root_this_product_can_write(self) -> None:
        assert dimension_of("m").root() is None
        assert dimension_of("m").power(2).root() == dimension_of("m")


class TestUnitsTravelThroughTheArithmetic:
    def test_a_length_over_a_time_is_a_velocity(self) -> None:
        """AC-030: the result carries the unit the expression produced, not one it was told."""
        assert evaluate("100 mm / 2 s").describe() == "0.05 m·s^-1"

    def test_a_bare_number_scales_a_quantity(self) -> None:
        assert evaluate("2 * stress", STRESS).describe() == "3e+08 Pa"

    def test_the_power_multiplies_the_exponents(self) -> None:
        assert evaluate("(2 m) ** 3").dimension == dimension_of("m").power(3)

    def test_the_square_root_halves_them(self) -> None:
        assert evaluate("sqrt(16 m ** 2)").describe() == "16 m"

    def test_a_root_that_would_be_half_an_exponent_is_refused(self) -> None:
        with pytest.raises(ExpressionError) as refusal:
            evaluate("sqrt(4 m)")
        assert "半端" in str(refusal.value)

    def test_values_are_held_in_the_internal_unit_and_labelled_with_it(self) -> None:
        """An earlier version of this labelled the magnitude with the symbol the user wrote, so the
        larger of 1 MPa and 200 kPa printed as `1e+06 MPa` while holding 1e6 Pa - a number shown in one
        unit and labelled with another."""
        result = evaluate("max(1 MPa, 200 kPa)")

        assert result.magnitude == pytest.approx(1.0e6)
        assert result.describe() == "1e+06 Pa"

    def test_a_declared_unit_is_still_quoted_back_in_a_refusal(self) -> None:
        """The two questions the one field used to answer: what the magnitude is in, and what the user
        wrote. A refusal wants the second."""
        with pytest.raises(ExpressionError) as refusal:
            evaluate("1 MPa + 1 s")
        assert "MPa" in str(refusal.value)


class TestIncompatibleUnitsAreRefusedNamingBoth:
    def test_a_length_added_to_a_time(self) -> None:
        """AC-031, INV-002."""
        with pytest.raises(ExpressionError) as refusal:
            evaluate("1 m + 1 s")

        message = str(refusal.value)
        assert "m" in message and "s" in message
        assert "INV-002" in message

    def test_a_comparison_across_dimensions(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("1 m > 1 s")

    def test_the_functions_that_take_several_values_require_one_unit(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("max(1 m, 1 s)")

    def test_a_transcendental_function_requires_a_plain_number(self) -> None:
        """Its series adds powers of the argument together, and only a dimensionless quantity may be
        added to its own square."""
        with pytest.raises(ExpressionError):
            evaluate("log(10 m)")

    def test_an_exponent_may_not_carry_a_unit(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("2 ** (1 m)")


class TestABareNumberIsUndeclaredRatherThanMatching:
    def test_a_threshold_with_no_unit_is_refused(self) -> None:
        """XC-003, and the expensive half of XC-242. `stress > 200` succeeds in most products, the
        verdict prints, and whether it meant 200 Pa or 200 MPa is nowhere in the record."""
        with pytest.raises(ExpressionError) as refusal:
            evaluate("stress > 200", STRESS)

        assert "XC-003" in str(refusal.value)
        assert "MPa" in str(refusal.value)

    def test_the_same_threshold_with_a_unit_is_answered(self) -> None:
        assert evaluate("stress > 200 MPa", STRESS).magnitude is False
        assert evaluate("stress > 100 MPa", STRESS).magnitude is True

    def test_a_bare_number_may_still_scale(self) -> None:
        """Refusing this too would make the language unusable, and it is not the trap: a multiplier has
        no unit to get wrong."""
        assert evaluate("stress / 2", STRESS).describe() == "7.5e+07 Pa"


class TestAUnitWithAnOffsetDoesNotTravel:
    def test_multiplying_a_temperature_point_is_refused(self) -> None:
        """E-141: doubling 20 degC gives 313.15 K one way and 586.3 K the other."""
        with pytest.raises(ExpressionError) as refusal:
            evaluate("20 degC * 2")

        assert "E-141" in str(refusal.value)
        assert "273.15" in str(refusal.value)

    def test_two_temperature_points_may_not_be_added(self) -> None:
        with pytest.raises(ExpressionError) as refusal:
            evaluate("20 degC + 20 degC")
        assert "INV-028" in str(refusal.value)

    def test_one_subtracted_from_another_is_a_difference_in_the_internal_unit(self) -> None:
        result = evaluate("20 degC - 15 degC")

        assert result.magnitude == pytest.approx(5.0)
        assert result.describe() == "5 K"
        assert result.absolute is False

    def test_a_difference_may_then_be_multiplied(self) -> None:
        """Because the offsets cancelled: what is left is an interval, and doubling an interval has one
        answer."""
        assert evaluate("(20 degC - 15 degC) * 2").magnitude == pytest.approx(10.0)

    def test_a_value_declared_as_a_difference_carries_no_offset(self) -> None:
        """INV-028's kind is read from the declaration rather than chosen here."""
        rise = quantity(10.0, "degC", declaration={"kind": "difference"})

        assert rise.magnitude == pytest.approx(10.0)
        assert evaluate("rise * 2", {"rise": rise}).magnitude == pytest.approx(20.0)

    def test_kelvin_is_a_plain_scale_and_is_left_alone(self) -> None:
        """The refusal follows the measurement rather than the topic: K's gap was 0.0 (E-141)."""
        assert evaluate("293.15 K * 2").magnitude == pytest.approx(586.3)

    def test_comparing_two_points_is_allowed(self) -> None:
        assert evaluate("20 degC > 15 degC").magnitude is True


class TestTheSyntaxIsWhatTheLanguageTableSays:
    def test_the_conditional(self) -> None:
        assert evaluate("1 m if true else 2 m").describe() == "1 m"

    def test_the_boolean_words(self) -> None:
        assert evaluate("true and not false").magnitude is True

    def test_a_chained_comparison_is_refused_rather_than_reinterpreted(self) -> None:
        """`a < b < c` reads as a range to a person and as `(a < b) < c` in the language this syntax
        comes from, and the two disagree."""
        with pytest.raises(ExpressionError) as refusal:
            evaluate("1 < 2 < 3")
        assert "括弧" in str(refusal.value)

    def test_text_compares_only_with_text(self) -> None:
        assert evaluate("'a' == 'a'").magnitude is True
        with pytest.raises(ExpressionError):
            evaluate("'a' == 1")

    def test_an_unknown_symbol_after_a_number_is_refused_rather_than_read_as_a_name(self) -> None:
        """There is no implicit multiplication, so `2 x` has no reading in which x is a variable."""
        with pytest.raises(ExpressionError) as refusal:
            evaluate("2 furlong")
        assert "furlong" in str(refusal.value)

    def test_division_by_zero_says_so(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("1 m / 0")

    def test_an_unclosed_parenthesis_says_where(self) -> None:
        with pytest.raises(ExpressionError) as refusal:
            evaluate("(1 + 2")
        assert "括弧" in str(refusal.value)


class TestThereIsNoInterpreterBehindIt:
    def test_a_python_expression_that_reaches_out_does_not_parse(self) -> None:
        """XC-101. Attribute access is the door into the object model, and the language does not have
        one to close."""
        for attempt in (
            "__import__('os').system('echo')",
            "sv.data.cases",
            "open('secret')",
            "[1, 2][0]",
            "x = 1",
        ):
            with pytest.raises(ExpressionError):
                evaluate(attempt, {"sv": Value(1.0), "x": Value(1.0)})

    def test_the_module_contains_no_way_to_run_python_at_all(self) -> None:
        """Structural, because the behavioural test above only covers the attempts somebody thought of.
        XC-101's claim is about the code, not about a list of blocked inputs."""
        source = pathlib.Path(expression.__file__).read_text(encoding="utf-8")

        # Bare builtins only: `re.compile` is a regular expression, not a way into Python, and the
        # first version of this test failed on it. A check that cannot tell the two apart would be
        # turned off by whoever hit it next.
        doors = re.findall(r"(?<![.\w])(eval|exec|compile|__import__|importlib)\s*[(.]", source)
        assert doors == []

    def test_an_unknown_function_names_what_there_is(self) -> None:
        with pytest.raises(ExpressionError) as refusal:
            evaluate("eval(1)")
        assert "sqrt" in str(refusal.value)


class TestAnUnboundNameIsRefusedWhenItIsWritten:
    def test_check_refuses_it_and_names_it(self) -> None:
        """AC-032: at edit time, not at run time. A study that fails at midnight on a name somebody
        could have seen was wrong is the failure this removes."""
        with pytest.raises(ExpressionError) as refusal:
            check("inlet_velocity * 2", bound=["outlet_velocity"])

        assert "inlet_velocity" in str(refusal.value)
        assert "outlet_velocity" in str(refusal.value)
        assert "AC-032" in str(refusal.value)

    def test_a_bound_name_passes_and_the_names_come_back(self) -> None:
        assert check("a + b", bound=["a", "b", "c"]) == ("a", "b")

    def test_the_arity_of_a_function_is_checked_before_the_run_too(self) -> None:
        with pytest.raises(ExpressionError):
            check("atan2(1)", bound=[])

    def test_the_names_are_reported_in_the_order_they_appear(self) -> None:
        assert names_in(parse("b + a + b")) == ("b", "a")

    def test_evaluating_an_unbound_name_still_refuses(self) -> None:
        """The edit-time pass is the one that helps; this is the one that must never guess."""
        with pytest.raises(ExpressionError):
            evaluate("nowhere + 1")


class TestTheFunctionTable:
    def test_the_statistics_take_several_values(self) -> None:
        assert evaluate("mean(1 m, 2 m, 3 m)").describe() == "2 m"
        assert evaluate("median(1 m, 5 m, 2 m)").describe() == "2 m"
        assert evaluate("sum(1 m, 2 m)").describe() == "3 m"

    def test_std_needs_two_values_because_one_has_no_spread(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("std(1 m)")

    def test_rounding_keeps_the_unit(self) -> None:
        assert evaluate("round(1.2345 m, 2)").describe() == "1.23 m"
        assert evaluate("floor(1.9 m)").describe() == "1 m"

    def test_clamp_requires_one_unit_across_all_three(self) -> None:
        assert evaluate("clamp(5 m, 1 m, 3 m)").describe() == "3 m"
        with pytest.raises(ExpressionError):
            evaluate("clamp(5 m, 1 s, 3 m)")

    def test_clamp_with_the_bounds_the_wrong_way_round_is_refused(self) -> None:
        """Silently swapping them would answer a question nobody asked."""
        with pytest.raises(ExpressionError):
            evaluate("clamp(5 m, 3 m, 1 m)")

    def test_atan2_agrees_with_the_toolkit_it_wraps(self) -> None:
        assert evaluate("atan2(1 m, 1 m)").magnitude == pytest.approx(math.pi / 4)

    def test_the_result_of_atan2_has_no_unit(self) -> None:
        assert evaluate("atan2(1 m, 1 m)").dimension == DIMENSIONLESS
