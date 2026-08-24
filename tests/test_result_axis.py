"""What indexes a @Case's results is read, not guessed (GL-036, ingest/AC-041, AC-043, AC-044).

A modal run and a transient run can be the same numbers in the same shape of file. Labelling mode 3 as
three seconds is a number that is wrong about the physics while looking entirely right, so the values
are read where a file declares them and the **kind** is reported as undeclared until a file says.

No VTK here: the rules are arithmetic and wording. `tests/test_cgns.py` covers the reading.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from domain_core.case_contents import (
    AxisKind,
    CaseContents,
    ResultAxis,
    differing_axes,
)

ROOT = Path(__file__).resolve().parents[1]

TIME = ResultAxis(AxisKind.TIME, (0.0, 1.0))
MODE = ResultAxis(AxisKind.MODE, (1.0, 2.0))
UNDECLARED = ResultAxis(AxisKind.UNDECLARED, (0.0, 0.5))
STEADY = ResultAxis(AxisKind.NONE)


class TestPositionsWithoutAKind:
    """The combination an earlier version of `ResultAxis` refused. Measuring the toolkit showed it is
    the ordinary case: a CGNS file declares its values in `BaseIterativeData_t` and the reader hands
    them over, while `SimulationType_t` - the node saying what they are - has no accessor at all
    (E-138)."""

    def test_an_undeclared_axis_may_carry_the_values_the_file_gave(self) -> None:
        axis = ResultAxis(AxisKind.UNDECLARED, (0.0, 0.5, 1.0))

        assert axis.positions == (0.0, 0.5, 1.0)
        assert axis.is_declared is False

    def test_the_line_shows_the_values_and_says_what_is_not_known(self) -> None:
        line = CaseContents(steps=2, parts=1, axis=UNDECLARED).describe()

        assert "0、0.5" in line
        assert "何を刻む値か" in line

    def test_a_long_sequence_is_abbreviated_rather_than_dumped(self) -> None:
        many = ResultAxis(AxisKind.UNDECLARED, tuple(float(n) for n in range(10)))

        line = CaseContents(steps=10, parts=1, axis=many).describe()

        assert "…" in line

    def test_a_steady_case_still_cannot_carry_positions(self) -> None:
        with pytest.raises(ValueError) as refusal:
            ResultAxis(AxisKind.NONE, (0.0,))
        assert "steady case has no axis" in str(refusal.value)

    def test_an_empty_sequence_is_none_rather_than_a_sequence_of_nothing(self) -> None:
        with pytest.raises(ValueError) as refusal:
            ResultAxis(AxisKind.UNDECLARED, ())
        assert "carries None" in str(refusal.value)


class TestPuttingResultsOfDifferentAxesTogether:
    """AC-044. Two results side by side read as comparable, and a mode number beside a time is not."""

    def test_two_of_the_same_declared_axis_need_no_statement(self) -> None:
        assert differing_axes(TIME, TIME) is None

    def test_two_different_declared_axes_are_named(self) -> None:
        statement = differing_axes(TIME, MODE)

        assert statement is not None
        assert "時刻" in statement
        assert "モード" in statement

    def test_an_undeclared_axis_always_produces_a_statement(self) -> None:
        """Even beside another undeclared one carrying the same values: two files that both say
        "0, 0.5" and neither of which says what that is may be one transient run and one modal one."""
        assert differing_axes(UNDECLARED, UNDECLARED) is not None

    def test_it_says_what_the_undeclared_one_is_sitting_beside(self) -> None:
        statement = differing_axes(TIME, UNDECLARED) or ""

        assert "宣言されていない" in statement
        assert "時刻" in statement

    def test_a_steady_result_has_no_positions_to_disagree_about(self) -> None:
        assert differing_axes(TIME, STEADY) is None
        assert differing_axes(STEADY, STEADY) is None

    def test_one_axis_alone_needs_no_statement(self) -> None:
        assert differing_axes(TIME) is None


class TestTheToolkitsGuessIsNotInherited:
    """`vtkExodusIIReader` documents its own default: HasModeShapes is false *"unless two time values in
    the Exodus file are identical, in which case it is true"* (E-138). Physics inferred from a
    coincidence - two equal values in a transient restart would make a run modal. Nothing in this
    product asks that reader what kind its sequence is, and this is the test that says so."""

    def test_no_axis_kind_is_ever_derived_from_the_positions(self) -> None:
        """Read from the file rather than from an imported object, so this runs on a machine with no
        engine environment - the claim is about the code, not about a loaded module."""
        source = (ROOT / "src" / "engine" / "result_axis.py").read_text(encoding="utf-8")

        body = source[source.index("def axis_of("):]
        for guessed in ("MODE", "TIME", "FREQUENCY"):
            assert f"AxisKind.{guessed}" not in body
