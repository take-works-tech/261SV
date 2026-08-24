"""Whether display geometry must be reduced, by how much, and what the reduction is allowed to touch.

LIM-002 is a ceiling on triangles drawn interactively, not on triangles held. Above it the picture is
reduced and **says so**, while every reported number stays computed on the full @Dataset (ingest/AC-030,
AC-031, INV-001). Those are two separate guarantees and this module carries only the first: the decision
of how far to reduce, kept apart from the toolkit that performs it so the arithmetic is testable with no
renderer present.

The plan is a value rather than a boolean because "reduced" alone is not a useful thing to tell someone.
A view showing a tenth of its triangles and a view showing 99% of them are both reduced, and only one of
them is worth looking twice at.

Specification: LIM-002, INV-001, ingest/AC-030, ingest/AC-031. Evidence: E-063 (T1), E-134 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.limits import MAX_INTERACTIVE_TRIANGLES


@dataclass(frozen=True, slots=True)
class ReductionPlan:
    """How much of a surface is drawn, and how much of it was left out."""

    source_triangles: int
    target_triangles: int

    def __post_init__(self) -> None:
        if self.source_triangles < 0 or self.target_triangles < 1:
            raise ValueError("a plan draws at least one triangle out of a non-negative number of them")

    @property
    def needed(self) -> bool:
        """Whether anything is dropped at all."""
        return self.source_triangles > self.target_triangles

    @property
    def fraction_removed(self) -> float:
        """What share of the triangles the reduction takes out, as the decimator's own parameter.

        Zero when nothing is dropped, so a plan that is not needed asks for no work rather than asking
        for a reduction of zero and paying for the pass anyway (XC-230).
        """
        if not self.needed:
            return 0.0
        return 1.0 - (self.target_triangles / self.source_triangles)

    def describe(self) -> str:
        """The line a view shows beside a reduced picture (AC-030)."""
        if not self.needed:
            return "全三角形を表示しています"
        percent = self.target_triangles / self.source_triangles * 100
        return (
            f"表示は間引かれています：{self.source_triangles:,} 三角形のうち "
            f"{self.target_triangles:,}（{percent:.1f}%）を描画。"
            "報告する数値は間引く前の全データで計算しています"
        )


def plan_reduction(
    source_triangles: int, *, budget: int = MAX_INTERACTIVE_TRIANGLES
) -> ReductionPlan:
    """The plan for a surface of this size against the interactive budget (LIM-002)."""
    if budget < 1:
        raise ValueError("a budget of no triangles is a refusal to draw, which is not a reduction")
    return ReductionPlan(source_triangles=source_triangles, target_triangles=min(source_triangles or 1, budget))
