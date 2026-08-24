"""Numbers a person reads follow the language; numbers a machine reads never do (INV-018).

The hazard leaves no trace, which is why the invariant spells it out: in several European locales a
comma is the decimal separator and a period groups thousands, so `1.234` is one thousand two hundred and
thirty-four. A file written under one locale and read under another is off by a factor of a thousand,
and every value in it still looks entirely plausible.

Verifies: INV-018, workspace/AC-033, AC-034, AC-035, workspace/TASK-032 to TASK-034.
"""

from __future__ import annotations

import inspect

from domain_core.locale_format import (
    CONVENTIONS,
    MACHINE,
    NARROW_NO_BREAK_SPACE,
    convention_note,
    for_display,
    for_machine,
)


class TestAMachineNeverSeesALocale:
    def test_the_function_cannot_be_told_to_use_a_comma(self) -> None:
        """The point of AC-034 holding at every call site rather than the ones somebody remembered: a
        function that could be told to use a comma is one that will be, at the site nobody checked."""
        parameters = set(inspect.signature(for_machine).parameters)

        assert "language" not in parameters
        assert "locale" not in parameters
        assert "convention" not in parameters

    def test_it_writes_a_period_and_no_grouping(self) -> None:
        assert for_machine(1234.5, 6) == "1234.5"

    def test_a_thousands_value_is_not_grouped(self) -> None:
        """"1,234" in a CSV is two fields in most parsers."""
        assert "," not in for_machine(1234567.0, 9)

    def test_a_missing_value_is_empty_rather_than_zero(self) -> None:
        assert for_machine(float("nan"), 6) == ""


class TestAPersonSeesTheirOwnConvention:
    def test_japanese_and_english_use_a_period(self) -> None:
        assert for_display(1234.5, 6, "ja") == "1,234.5"
        assert for_display(1234.5, 6, "en") == "1,234.5"

    def test_german_swaps_both(self) -> None:
        assert for_display(1234.5, 6, "de") == "1.234,5"

    def test_french_groups_with_a_narrow_no_break_space(self) -> None:
        """Referenced by name rather than typed: a literal U+202F in a test is indistinguishable from
        an ASCII space by eye, and the two disagreed here the first time this was written."""
        assert for_display(1234.5, 6, "fr") == f"1{NARROW_NO_BREAK_SPACE}234,5"

    def test_an_unknown_language_falls_back_to_plain_rather_than_to_a_lookalike(self) -> None:
        """A near miss on a decimal separator is the whole of the hazard, so guessing is worse than
        plain."""
        assert for_display(1234.5, 6, "xx") == "1234.5"

    def test_grouping_starts_at_four_digits_and_is_consistent(self) -> None:
        """This test asserted that 2026 stays ungrouped "because a year must not become 2,026", which
        was an inference the formatter cannot make: nothing tells it whether it has a year or a
        quantity that happens to be 2026. A year is not a measured quantity and does not come through
        here at all."""
        assert for_display(999.0, 3, "en") == "999"
        assert for_display(1234.0, 4, "en") == "1,234"
        assert for_display(20260.0, 5, "en") == "20,260"

    def test_a_negative_number_keeps_its_sign_outside_the_grouping(self) -> None:
        assert for_display(-1234567.0, 9, "de") == "-1.234.567"

    def test_an_exponent_form_is_not_grouped(self) -> None:
        shown = for_display(1.5e-9, 2, "de")

        assert shown.startswith("1,5e")
        assert "." not in shown


class TestTheSameValueBothWays:
    def test_the_machine_form_is_identical_whatever_the_language_is(self) -> None:
        """INV-018's own check: the file bytes do not depend on the interface language."""
        assert len({for_machine(1234.5, 6) for _ in CONVENTIONS}) == 1

    def test_a_comma_locale_display_would_not_survive_a_machine_reader(self) -> None:
        """Not a test of this product - a demonstration of why the two functions are separate. This is
        the string that becomes two CSV fields."""
        assert for_display(1234.5, 6, "de") == "1.234,5"
        assert for_machine(1234.5, 6) == "1234.5"


class TestAFileReadByBothStatesWhatItDid:
    def test_the_note_names_the_separator_and_the_grouping(self) -> None:
        """AC-035. A stated convention is checkable; a guessed one is a factor of a thousand."""
        note = convention_note()

        assert "decimal-point='.'" in note
        assert "digit-grouping='none'" in note

    def test_it_can_state_a_locale_convention_where_one_was_used(self) -> None:
        note = convention_note(CONVENTIONS["de"])

        assert "decimal-point=','" in note
        assert "digit-grouping='.'" in note

    def test_the_machine_convention_is_the_one_with_no_grouping(self) -> None:
        assert MACHINE.decimal == "."
        assert MACHINE.grouping == ""
