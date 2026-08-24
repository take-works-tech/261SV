"""What a conversion changed, kept with the thing it changed.

CT-012 accepts nine data object types after one named conversion, and each conversion costs something.
Three of those costs cannot be recovered afterwards, which is the whole reason this record exists rather
than a log line: an image grid's spacing is **the one number in a voxel result that carries a length**,
and after the points are explicit nothing in the dataset remembers what it was.

A conversion is also the moment a cost can still be refused. `Cost` is computed from the unconverted
object - a structured grid knows its cell count before anything expands it - so a conversion that would
exceed the interactive budget is stated **before** it runs and not discovered afterwards
(ingest/AC-032).

Specification: CT-012, LIM-002, ingest/AC-032. Evidence: E-132 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field


@dataclass(frozen=True, slots=True)
class ConversionRecord:
    """One conversion that happened, in the words CT-012 uses for it.

    `preserved` holds facts that were implicit in the source and are gone from the result. They are
    key-value rather than prose because something later reads them: a voxel result's spacing is what
    turns a cell index into a length.
    """

    source_type: str
    target_type: str
    via: str
    costs: str
    cells: int
    preserved: dict[str, tuple[float, ...]] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.via or not self.costs:
            raise ValueError(
                "a conversion records what performed it and what it cost; one that records neither is "
                "indistinguishable from data that arrived that way (CT-012)"
            )

    def describe(self) -> str:
        kept = "".join(f"・{name} {values}" for name, values in sorted(self.preserved.items()))
        return (
            f"{self.source_type} を {self.via} で {self.target_type} に変換しました"
            f"（{self.cells:,} セル）{kept}"
        )


class ConversionTooLarge(Exception):
    """Raised before a conversion runs, when what it would produce exceeds the budget.

    Before rather than after: the count is read from the unconverted object, so this costs nothing and
    the user still has the choice. A conversion discovered to be too large once it has finished has
    already spent the memory it was supposed to protect.
    """

    def __init__(self, source_type: str, cells: int, budget: int, costs: str) -> None:
        self.source_type = source_type
        self.cells = cells
        self.budget = budget
        super().__init__(
            f"{source_type} を変換すると {cells:,} セルになり、上限 {budget:,} を超えます。{costs}"
        )
