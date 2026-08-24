"""Which entries of a partitioned dataset a number may be computed over (INV-010).

A decomposed run arrives as many pieces, and the reader **merges nothing**: `vtkXMLPUnstructuredDataReader`
contains no locator and no merge step, so it appends the pieces and propagates ghost levels (E-039,
E-131). Every point on a partition interface therefore arrives once per piece that touches it, and a
naive sum over a 64-piece run over-counts every interface - by an amount small enough to look plausible
and large enough to be wrong.

Two things follow, and they are different.

**When the duplicates are marked**, an array named `vtkGhostType` says which entries to leave out, and
this module builds the mask. That is the mechanism VTK's own integrator uses, and it excludes exactly
`DUPLICATECELL | HIDDENCELL` (E-131).

**When they are not marked, no mask can be built** - and that is the common case, because a `.pvtu`
written at the default `GhostLevel="0"` carries no ghost array at all. The duplicated points are then
indistinguishable from real ones. Coordinate-merging them would need a tolerance, and a tolerance welds
a crack face shut: it turns a visible over-count into an invisible change of geometry. So this module
refuses the affected aggregates instead, and says which and why. Not every aggregate is affected -
see `Partitioning.refusal`.

Specification: INV-010, XC-001. Evidence: E-039 (T1), E-131 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntFlag

import numpy as np

from domain_core.association import Association

# The array VTK marks ghost entries in, on point data and on cell data alike
# (`vtkFieldData::GhostArrayName`, E-131). It is not a physical quantity, so a @Dataset holds it apart
# from the fields a user chooses among rather than in the same dictionary - which is also the only way
# to hold both, since the point one and the cell one have the same name.
GHOST_ARRAY_NAME = "vtkGhostType"


class PointGhost(IntFlag):
    """`vtkDataSetAttributes::PointGhostTypes` (E-131)."""

    DUPLICATE = 1   # the point is present in multiple partitions
    HIDDEN = 2      # present only for connectivity; its data values mean nothing


class CellGhost(IntFlag):
    """`vtkDataSetAttributes::CellGhostTypes` (E-131).

    **The two vocabularies collide.** Bit 2 is `HIDDEN` for a point and `HIGH_CONNECTIVITY` for a cell,
    and both arrays carry the same name. A mask built without knowing the association would silently
    drop every high-connectivity cell from an integral - a wrong number that looks right, which is why
    `counted` takes the association and has no default for it.
    """

    DUPLICATE = 1
    HIGH_CONNECTIVITY = 2
    LOW_CONNECTIVITY = 4
    REFINED = 8
    EXTERIOR = 16
    HIDDEN = 32


# What a quantity is not computed over. Taken from what VTK's own integrator excludes rather than
# chosen here: `vtkIntegrateAttributes` skips a cell whose ghost byte has DUPLICATECELL or HIDDENCELL
# set, and consults no other bit (E-131). The remaining cell bits describe a cell; they do not
# disqualify it.
EXCLUDED = {
    Association.POINT: PointGhost.DUPLICATE | PointGhost.HIDDEN,
    Association.CELL: CellGhost.DUPLICATE | CellGhost.HIDDEN,
}


def counted(ghosts: np.ndarray, association: Association) -> np.ndarray:
    """A boolean mask of the entries a reported number is computed over.

    `association` is required: the byte is the same and its meaning is not.
    """
    if ghosts.dtype != np.uint8:
        raise ValueError(
            f"a ghost array is unsigned bytes of flags, not {ghosts.dtype}; reading it as anything "
            "wider makes the bit tests silently wrong"
        )
    return (ghosts & int(EXCLUDED[association])) == 0


class Aggregate(str, Enum):
    """A kind of number computed over many entries. They do not survive duplication equally."""

    EXTREMUM = "extremum"   # min or max
    COUNT = "count"
    TOTAL = "total"         # a sum over the entries
    MEAN = "mean"


# An extremum is unharmed by duplication: the largest of a set is the largest of that set with some of
# it written twice. Everything that adds entries up, or divides by how many there are, is not.
_SURVIVES_DUPLICATION = frozenset({Aggregate.EXTREMUM})


@dataclass(frozen=True, slots=True)
class Partitioning:
    """How a @Dataset was decomposed, as the files declared it."""

    parts: int = 1
    # The `GhostLevel` attribute of the `.pvtu`: how many layers of cells each piece carries beyond its
    # own. The writer's default is 0 (E-131), and at 0 no cell belongs to two pieces - only the points
    # on the interfaces are repeated.
    ghost_level: int = 0

    def __post_init__(self) -> None:
        if self.parts < 1 or self.ghost_level < 0:
            raise ValueError("a dataset has at least one part and cannot have negative ghost layers")

    @property
    def cells_are_repeated(self) -> bool:
        """Whether a cell can belong to more than one piece. Only ghost layers put it there."""
        return self.parts > 1 and self.ghost_level > 0

    @property
    def points_are_repeated(self) -> bool:
        """Whether a point can arrive more than once. Any interface does that, at any ghost level."""
        return self.parts > 1

    def refusal(
        self, aggregate: Aggregate, association: Association, *, marked: bool
    ) -> str | None:
        """Why this number cannot be reported over this dataset, or None if it can.

        `marked` says whether a ghost array for that association arrived, because a mask makes every
        aggregate computable again.
        """
        if marked or aggregate in _SURVIVES_DUPLICATION:
            return None
        repeated = (
            self.points_are_repeated if association is Association.POINT else self.cells_are_repeated
        )
        if not repeated:
            return None
        where = "パートの境界で点が重複しています" if association is Association.POINT else (
            f"ゴースト層が {self.ghost_level} 層あるためセルが重複しています"
        )
        return (
            f"{self.parts} パートに分割されたデータで、{where}。"
            f"重複を示す {GHOST_ARRAY_NAME} 配列がファイルにないため、どの要素が重複かを判定できません。"
            "推定した値は妥当に見えて誤っているため、この量は報告しません（INV-010）。"
        )
