"""Figures proposed from the data alone, and the things a proposal must not become.

AC-014 asks for proposals with the **signal** behind each one named. The distinction the whole feature
turns on is that a proposal is a suggestion of a figure and never a statement about the physics: "r =
0.93 over 12 cases" is a measurement about a set of numbers, and "this drives that" is a claim about a
mechanism that nothing here is entitled to make.

The minimums matter as much as the signals. A correlation over two cases is 1.0 by construction, and a
spread over three is a handful of values rather than a distribution - so both are simply not offered.

Verifies: graph/AC-014, AC-016, graph/TASK-016, part of TASK-017, XC-013, E-071.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.analysis.expression import Value, quantity
from engine.graph.recommend import (
    MINIMUM_FOR_CORRELATION,
    MINIMUM_FOR_DISTRIBUTION,
    NOTABLE_CORRELATION,
    Kind,
    Session,
    correlation,
    describe_all,
    propose,
)


def study(pairs: list[tuple[float, float]]) -> dict[str, dict[str, Value]]:
    """One case per pair, holding a load and the stress it produced."""
    return {
        f"case:{index:03d}": {
            "load": quantity(load, "MPa"),
            "peak": quantity(peak, "MPa"),
        }
        for index, (load, peak) in enumerate(pairs)
    }


RELATED = study([(float(n), 2.0 * n + 1.0) for n in range(1, 13)])
UNRELATED = study([(1.0, 9.0), (2.0, 3.0), (3.0, 7.0), (4.0, 1.0), (5.0, 8.0), (6.0, 2.0)])


class TestAProposalNamesItsSignal:
    def test_a_correlation_carries_the_coefficient_and_the_count(self) -> None:
        """AC-014. A recommendation with no number attached cannot be judged and cannot be wrong, which
        is the same thing."""
        found = propose(RELATED)

        first = next(one for one in found if one.kind is Kind.CORRELATION)
        assert "r = 1.00" in first.signal
        assert "12 ケース" in first.signal

    def test_it_says_the_relation_is_between_numbers_and_not_a_cause(self) -> None:
        """The distinction the feature turns on. A proposal phrased as a conclusion has skipped the step
        where somebody decides whether it is one."""
        first = next(one for one in propose(RELATED) if one.kind is Kind.CORRELATION)

        assert "原因を示すものではありません" in first.signal

    def test_cases_without_a_value_are_counted_in_the_signal(self) -> None:
        """Pairwise deletion, stated: a correlation over the cases that happen to have both is over a
        different set from the one somebody selected."""
        partial = dict(RELATED)
        partial["case:012"] = {"load": quantity(20.0, "MPa")}

        first = next(one for one in propose(partial) if one.kind is Kind.CORRELATION)

        assert "1 件は値がありません" in first.signal

    def test_a_distribution_carries_the_range_it_saw(self) -> None:
        found = propose(RELATED)

        spread = next(one for one in found if one.kind is Kind.DISTRIBUTION)
        assert "ケース" in spread.signal
        assert "から" in spread.signal

    def test_the_three_kinds_are_the_three_the_criterion_lists(self) -> None:
        assert {kind.value for kind in Kind} == {"correlation", "distribution", "overTime"}


class TestNothingIsProposedFromTooLittle:
    def test_a_correlation_over_two_cases_is_not_offered(self) -> None:
        """It is 1.0 by construction, whatever the numbers are."""
        two = study([(1.0, 5.0), (2.0, 9.0)])

        assert [one for one in propose(two) if one.kind is Kind.CORRELATION] == []

    def test_the_minimum_is_stated_rather_than_implied(self) -> None:
        assert MINIMUM_FOR_CORRELATION == 5
        assert MINIMUM_FOR_DISTRIBUTION == 8

    def test_an_unremarkable_correlation_is_not_offered(self) -> None:
        found = [one for one in propose(UNRELATED) if one.kind is Kind.CORRELATION]

        assert found == []

    def test_a_quantity_that_does_not_vary_has_no_correlation_rather_than_zero(self) -> None:
        """Zero would read as "measured, and unrelated". A constant has no correlation with anything."""
        assert correlation(np.array([1.0, 1.0, 1.0]), np.array([1.0, 2.0, 3.0])) is None

    def test_a_flat_quantity_gets_no_distribution_proposal(self) -> None:
        flat = {
            f"case:{n:03d}": {"peak": quantity(150.0, "MPa")} for n in range(10)
        }

        assert propose(flat) == ()

    def test_no_proposals_at_all_is_an_answer(self) -> None:
        """A feature that always finds something is one that is finding it in the noise."""
        assert "何も出ないことは結果です" in describe_all(propose({}))


class TestOverTimeComesFromTheFilesDeclaration:
    def test_it_is_proposed_only_where_a_sequence_was_declared(self) -> None:
        """Whether a quantity varies along a sequence is a fact about the file. Guessing it from the
        values is what XC-240 refuses."""
        without = [one for one in propose(RELATED) if one.kind is Kind.OVER_TIME]
        with_it = [
            one for one in propose(RELATED, with_sequences=["peak"])
            if one.kind is Kind.OVER_TIME
        ]

        assert without == []
        assert len(with_it) == 1

    def test_it_does_not_name_the_sequence_as_time_on_its_own_authority(self) -> None:
        found = next(
            one for one in propose(RELATED, with_sequences=["peak"])
            if one.kind is Kind.OVER_TIME
        )

        assert "ファイルの宣言に従います" in found.signal

    def test_a_sequence_for_a_quantity_nobody_holds_is_ignored(self) -> None:
        assert [
            one for one in propose(RELATED, with_sequences=["nowhere"])
            if one.kind is Kind.OVER_TIME
        ] == []


class TestARejectedProposalDoesNotComeBack:
    def test_it_is_not_offered_again_in_the_session(self) -> None:
        """AC-016. Repeating a suggestion somebody declined is how a helpful feature becomes one people
        turn off."""
        session = Session()
        first = propose(RELATED, session=session)[0]

        session.reject(first)

        assert first.identity not in {one.identity for one in propose(RELATED, session=session)}

    def test_the_others_are_still_offered(self) -> None:
        session = Session()
        every = propose(RELATED, session=session)
        session.reject(every[0])

        assert len(propose(RELATED, session=session)) == len(every) - 1

    def test_the_same_two_quantities_in_the_other_order_are_the_same_proposal(self) -> None:
        """Otherwise declining "load against peak" would leave "peak against load" to come back."""
        from engine.graph.recommend import Proposal

        one = Proposal(Kind.CORRELATION, ("load", "peak"), "r = 1.00", 1.0)
        other = Proposal(Kind.CORRELATION, ("peak", "load"), "r = 1.00", 1.0)

        assert one.identity == other.identity

        session = Session()
        session.reject(other)

        assert session.allows(one) is False

    def test_the_memory_lasts_the_session_and_is_not_stored(self) -> None:
        """A proposal declined today because the study was half loaded is one worth making again next
        week, and a permanent refusal list is a product that quietly stops suggesting things."""
        session = Session()
        session.reject(propose(RELATED)[0])

        assert len(propose(RELATED, session=Session())) == len(propose(RELATED))


class TestProposalsAreOrderedByWhatIsBehindThem:
    def test_the_strongest_comes_first(self) -> None:
        found = propose(RELATED)

        assert found[0].strength >= found[-1].strength

    def test_the_order_is_stable_between_runs(self) -> None:
        """Two runs of the same study produce the same list, so a caller showing the first three shows
        the same three."""
        assert [one.identity for one in propose(RELATED)] == [
            one.identity for one in propose(RELATED)
        ]

    def test_a_notable_correlation_is_a_stated_judgement_rather_than_a_threshold_in_physics(self) -> None:
        assert NOTABLE_CORRELATION == pytest.approx(0.7)
