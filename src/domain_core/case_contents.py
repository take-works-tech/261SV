"""What one @Case turned out to contain: how many steps, how many parts and partitions, and what
indexes the steps.

A @Case is not a file (GL-002). A transient run arrives as a directory of files, a decomposed run as a
manifest naming its pieces, and both are **one** @Case with a stated shape - not many cases, and not one
case whose extent nobody counted (ingest/AC-026).

**A part and a partition are counted separately** (XC-234). A partition is one dataset cut up for
parallel input and output: its pieces recombine, their interface points are duplicates of each other,
and INV-010 governs them. A part is a distinct thing in the model - an element block, a side set, a
material - whose points are nobody else's duplicates and across which nothing is summed unless it was
asked for. A `.pvtu` names partitions; a `vtkMultiBlockDataSet` names parts.

The shape is reported, never inferred. In particular a series of numbered files gives an **order** and
no values: nothing in it says the third file is at three seconds, so the axis carries positions only
where the file declared them, and says `UNDECLARED` where it did not. Numbering a step `t = 3` because
it is third is the same class of mistake as reading a millimetre as a metre - plausible, and wrong about
the physics (GL-036).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AxisKind(str, Enum):
    """What indexes a @Case's results (GL-036).

    `UNDECLARED` is not a fifth kind of physics. It is this product saying that the files order the
    steps and do not say what the order means, which a reader must be able to express: a modal run and
    a transient run look identical as a directory of numbered files.
    """

    TIME = "time"
    MODE = "mode"
    FREQUENCY = "frequency"
    NONE = "none"
    UNDECLARED = "undeclared"


@dataclass(frozen=True, slots=True)
class ResultAxis:
    """The axis, and the positions along it the files declared - `None` when they declared none.

    **A kind of `UNDECLARED` may carry positions.** An earlier version of this refused that combination,
    on the reasoning that positions belong to an axis and one without the other is incoherent. Measuring
    the toolkit showed the combination is the ordinary case rather than an incoherent one: a CGNS file
    declares its values in `BaseIterativeData_t` and the reader hands them over, while the node that
    says what they *are* - `SimulationType_t` - has no accessor at all (E-138). The file gives numbers
    along an axis and does not say which axis, and dropping the numbers or naming the axis are both
    worse than saying so.
    """

    kind: AxisKind
    positions: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.kind is AxisKind.NONE and self.positions:
            raise ValueError("a steady case has no axis, so it cannot carry positions")
        if self.positions is not None and len(self.positions) < 1:
            raise ValueError("an axis with no positions carries None, not an empty sequence")

    @property
    def is_declared(self) -> bool:
        return self.kind not in (AxisKind.UNDECLARED, AxisKind.NONE)


_AXIS_WORD = {
    AxisKind.TIME: "時刻",
    AxisKind.MODE: "モード",
    AxisKind.FREQUENCY: "周波数",
    AxisKind.UNDECLARED: "宣言なし",
}


def differing_axes(*axes: ResultAxis) -> str | None:
    """What must be said when results from these axes are put together, or None when nothing must.

    ingest/AC-044. Two results side by side in a @Graph or a @Report read as comparable, and a mode
    number beside a time is not - the horizontal position means a different thing in each. The statement
    is produced here rather than at each display site because a site that forgets it produces a chart
    that looks ordinary.

    An **undeclared** axis is the case this exists for, and it produces a statement whatever it sits
    beside - including another undeclared axis carrying the same values. Two files that both say
    "0, 0.5" and neither of which says what that is may be one transient run and one modal one.
    """
    kinds = {axis.kind for axis in axes}
    kinds.discard(AxisKind.NONE)  # a steady result has no positions to disagree about
    if AxisKind.UNDECLARED in kinds:
        # Any undeclared axis, even beside another undeclared one carrying the same values. Two files
        # that both say "0, 0.5" and neither of which says what that is may be one transient run and
        # one modal one, and silence here would be read as a statement that they agree.
        others = kinds - {AxisKind.UNDECLARED}
        beside = "".join(
            f"（他方は{_AXIS_WORD[kind]}）" for kind in sorted(others, key=lambda k: k.value)
        )
        return (
            f"並べた結果のうち、軸の種類がファイルに宣言されていないものがあります{beside}。"
            "同じ軸である保証はありません"
        )
    if len(kinds) < 2:
        return None
    named = "、".join(_AXIS_WORD[kind] for kind in sorted(kinds, key=lambda k: k.value))
    return f"異なる結果軸の値を並べています（{named}）。横軸の意味が結果ごとに異なります"


@dataclass(frozen=True, slots=True)
class CaseContents:
    """One @Case's extent, as read. Every count here is something that was looked at, not estimated."""

    steps: int
    parts: int
    axis: ResultAxis
    # Named parts the file declared and that were not there (ingest/AC-027).
    missing_parts: tuple[str, ...] = ()
    # How many pieces the parts are cut into for parallel input and output. Separate from `parts`
    # because the two invalidate different numbers: a missing partition leaves a hole in one part's
    # mesh, a missing part leaves a whole component out of the case (XC-234).
    partitions: int = 1
    missing_partitions: tuple[str, ...] = ()
    # The `GhostLevel` a piece manifest declared: how many layers of cells each piece carries beyond
    # its own. It decides whether *cells* can be repeated across pieces as well as points, which is a
    # different question with a different answer (INV-010, `domain_core.partitions`).
    ghost_level: int = 0

    def __post_init__(self) -> None:
        if self.ghost_level < 0:
            raise ValueError("a piece cannot carry a negative number of ghost layers")
        if self.steps < 1 or self.parts < 1 or self.partitions < 1:
            raise ValueError(
                "a case that loaded has at least one step, one part and one partition"
            )
        declared = self.axis.positions
        if declared is not None and len(declared) != self.steps:
            raise ValueError(
                f"{len(declared)} positions were declared for {self.steps} steps; one of the two was "
                "counted wrongly, and guessing which would put a value on the wrong step"
            )

    @property
    def is_partial(self) -> bool:
        """Whether anything the file named could not be found - a part or a partition (AC-027)."""
        return bool(self.missing_parts or self.missing_partitions)

    @property
    def absences(self) -> tuple[str, ...]:
        """Everything named and not found, parts first, each saying which kind it is."""
        return tuple(
            [f"パート {name}" for name in self.missing_parts]
            + [f"パーティション {name}" for name in self.missing_partitions]
        )

    def describe(self) -> str:
        """One line a user can read, stating the counts rather than implying completeness."""
        steps = f"{self.steps} ステップ" if self.steps > 1 else "1 ステップ"
        parts = f"{self.parts} パート" if self.parts > 1 else "1 パート"
        axis = {
            AxisKind.TIME: "時刻",
            AxisKind.MODE: "モード",
            AxisKind.FREQUENCY: "周波数",
            AxisKind.NONE: "結果軸なし",
            AxisKind.UNDECLARED: "軸の種類は宣言されていません",
        }[self.axis.kind]
        line = f"{steps}・{parts}・{axis}"
        if self.partitions > 1:
            line += f"（{self.partitions} パーティションに分割）"
        if self.axis.kind is not AxisKind.NONE and self.axis.positions is None:
            line += "（位置の値はファイルにありません）"
        elif self.axis.kind is AxisKind.UNDECLARED and self.axis.positions is not None:
            shown = "、".join(f"{value:g}" for value in self.axis.positions[:4])
            more = " …" if len(self.axis.positions) > 4 else ""
            line += f"（値は {shown}{more}。何を刻む値かはファイルが述べていません）"
        if self.ghost_level:
            line += f"・ゴースト層 {self.ghost_level}"
        if self.is_partial:
            absences = self.absences
            line += f"・不足 {len(absences)} 件：{', '.join(absences)}"
        return line
