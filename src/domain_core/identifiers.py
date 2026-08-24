"""The identifiers a source file gave its points and cells, kept as identifiers (GL-034, INV-023).

"The maximum is at node 12345" is checkable in the solver. "The maximum is at index 8412" is checkable
nowhere, and it changes if the file is written again. So an identifier written by the source is
preserved and reported, and where a file carries none this product **says so** rather than offering the
array position wearing the same clothes.

**An identifier is not a @Field**, and it is held apart from them for three reasons that each rule out
the alternative on their own: it is not a physical quantity and does not belong in the list a user picks
a @Variable from; a global id is an integer whose exactness matters and the field store is float64,
which stops being exact above 2^53; and a pedigree id may be **text** (E-135), which no numeric array
can hold at all.

Specification: GL-034, INV-023, ingest/AC-035, AC-036. Evidence: E-075 (T1), E-135 (T1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SourceIdentifiers:
    """What the file called each entry of one association, and nothing invented where it called it
    nothing.

    Both may be absent, which is the ordinary case and is a fact to report rather than a gap to fill.
    """

    # A numeric identifier, unique across the dataset (`vtkDataSetAttributes::GLOBALIDS`). Held as
    # int64 because that is what the file holds; converting it to the float the fields use would make
    # node 9007199254740993 into node 9007199254740992 without saying so.
    global_ids: np.ndarray | None = None
    # An identifier that may be text and need not be unique (`PEDIGREEIDS`), carried through refinement
    # and transformation by the tool that wrote it.
    pedigree_ids: tuple[str, ...] | None = None
    # What the source called them, so a report can use the file's own word - `GlobalNodeId`,
    # `GlobalElementId`, `node`, whatever the writer chose.
    global_name: str | None = None
    pedigree_name: str | None = None

    def __post_init__(self) -> None:
        if self.global_ids is not None:
            if self.global_ids.ndim != 1:
                raise ValueError("a global identifier array is one value per entry")
            if not np.issubdtype(self.global_ids.dtype, np.integer):
                raise ValueError(
                    f"global identifiers are integers and these are {self.global_ids.dtype}; reading "
                    "them as anything else makes two different nodes into one at the top of the range"
                )
            if not self.global_name:
                raise ValueError("identifiers carry the name the file gave them")
        if self.pedigree_ids is not None and not self.pedigree_name:
            raise ValueError("identifiers carry the name the file gave them")

    @property
    def present(self) -> bool:
        return self.global_ids is not None or self.pedigree_ids is not None

    def count(self) -> int | None:
        if self.global_ids is not None:
            return int(self.global_ids.size)
        if self.pedigree_ids is not None:
            return len(self.pedigree_ids)
        return None

    def at(self, index: int) -> str | None:
        """How the source refers to one entry, or None where it gave it no name.

        None, never the index. An index presented as an identifier is a number a reader will take to
        the solver and fail to find (INV-023).
        """
        parts: list[str] = []
        if self.global_ids is not None:
            parts.append(f"{self.global_name} {int(self.global_ids[index])}")
        if self.pedigree_ids is not None:
            parts.append(f"{self.pedigree_name} {self.pedigree_ids[index]}")
        return " / ".join(parts) if parts else None


#: What is said instead of a location, when the file named nothing. Stated once so that two reports of
#: the same absence agree, and phrased as a fact about the file rather than as a failure of this product.
NO_IDENTIFIER = "このファイルは要素の識別子を持たないため、位置を示せません（配列位置は識別子ではありません）"


def location_of(identifiers: SourceIdentifiers | None, index: int) -> str:
    """Where a value is, in the source's own words, or the statement that the source did not say."""
    if identifiers is None:
        return NO_IDENTIFIER
    return identifiers.at(index) or NO_IDENTIFIER
