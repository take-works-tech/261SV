"""What one @Case turned out to contain: how many steps, how many parts, and what indexes the steps.

A @Case is not a file (GL-002). A transient run arrives as a directory of files, a decomposed run as a
manifest naming its pieces, and both are **one** @Case with a stated shape - not many cases, and not one
case whose extent nobody counted (ingest/AC-026).

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
    """The axis, and the positions along it the files declared - `None` when they declared none."""

    kind: AxisKind
    positions: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.kind is AxisKind.NONE and self.positions:
            raise ValueError("a steady case has no axis, so it cannot carry positions")
        if self.kind is AxisKind.UNDECLARED and self.positions:
            raise ValueError(
                "positions were read but the axis they belong to was not; say which axis, or carry none"
            )

    @property
    def is_declared(self) -> bool:
        return self.kind not in (AxisKind.UNDECLARED, AxisKind.NONE)


@dataclass(frozen=True, slots=True)
class CaseContents:
    """One @Case's extent, as read. Every count here is something that was looked at, not estimated."""

    steps: int
    parts: int
    axis: ResultAxis
    missing_parts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.steps < 1 or self.parts < 1:
            raise ValueError("a case that loaded has at least one step and at least one part")
        declared = self.axis.positions
        if declared is not None and len(declared) != self.steps:
            raise ValueError(
                f"{len(declared)} positions were declared for {self.steps} steps; one of the two was "
                "counted wrongly, and guessing which would put a value on the wrong step"
            )

    @property
    def is_partial(self) -> bool:
        """Whether a part the manifest named could not be found (ingest/AC-027)."""
        return bool(self.missing_parts)

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
        if self.axis.kind is not AxisKind.NONE and self.axis.positions is None:
            line += "（位置の値はファイルにありません）"
        if self.is_partial:
            line += f"・不足パート {len(self.missing_parts)} 件：{', '.join(self.missing_parts)}"
        return line
