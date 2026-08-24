"""How far a surface is reduced for display, and what the view says about it.

LIM-002 caps triangles drawn, not triangles held. Above it the picture is reduced and says so, while
every reported number stays computed on the full @Dataset - two separate guarantees, and this file
covers the arithmetic of the first. No VTK: the decision is a ratio.
"""

from __future__ import annotations

import pytest

from domain_core.reduction import ReductionPlan, plan_reduction
from engine.limits import MAX_INTERACTIVE_TRIANGLES


class TestWhetherAnythingIsDropped:
    def test_a_surface_inside_the_budget_is_drawn_whole(self) -> None:
        plan = plan_reduction(1000, budget=10_000)

        assert plan.needed is False
        assert plan.fraction_removed == 0.0
        assert plan.describe() == "全三角形を表示しています"

    def test_a_surface_at_exactly_the_budget_is_drawn_whole(self) -> None:
        """The limit is a ceiling that may be reached, not one that may be approached."""
        assert plan_reduction(10_000, budget=10_000).needed is False

    def test_a_surface_above_the_budget_is_cut_to_it(self) -> None:
        plan = plan_reduction(40_000, budget=10_000)

        assert plan.needed is True
        assert plan.target_triangles == 10_000
        assert plan.fraction_removed == pytest.approx(0.75)

    def test_the_default_budget_is_the_measured_one(self) -> None:
        """LIM-002, and one place: a second copy of the number is a second answer waiting to differ."""
        assert plan_reduction(MAX_INTERACTIVE_TRIANGLES + 1).target_triangles == MAX_INTERACTIVE_TRIANGLES

    def test_a_plan_that_is_not_needed_asks_for_no_work(self) -> None:
        """XC-230: a reduction of zero still costs the pass that performs it."""
        assert plan_reduction(5, budget=10).fraction_removed == 0.0


class TestWhatTheViewSays:
    def test_the_line_states_both_counts_and_where_the_numbers_come_from(self) -> None:
        """AC-030. "Reduced" alone is not useful - a view showing a tenth of its triangles and one
        showing 99% are both reduced, and only one is worth looking at twice."""
        line = plan_reduction(2_000_000, budget=500_000).describe()

        assert "2,000,000" in line
        assert "500,000" in line
        assert "25.0%" in line
        assert "間引く前の全データ" in line


class TestAPlanRefusesToBeMeaningless:
    def test_a_budget_of_nothing_is_a_refusal_to_draw(self) -> None:
        with pytest.raises(ValueError) as refusal:
            plan_reduction(100, budget=0)
        assert "refusal to draw" in str(refusal.value)

    def test_a_target_of_nothing_is_refused(self) -> None:
        with pytest.raises(ValueError):
            ReductionPlan(source_triangles=100, target_triangles=0)

    def test_an_empty_surface_still_yields_a_usable_plan(self) -> None:
        """A dataset with no cells has nothing to draw, which is not the same as a plan that cannot
        be built."""
        plan = plan_reduction(0)

        assert plan.needed is False
        assert plan.target_triangles == 1
