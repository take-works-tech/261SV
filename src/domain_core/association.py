"""Where a value lives on a mesh: on the points, or on the cells.

This is one word, and three modules now need it - a @Field remembers it and refuses to be read as the
other (INV-003), and the ghost vocabulary needs it because **the same bit means different things for a
point and for a cell** (see `partitions`). A word two modules share is not owned by whichever one
happened to be written first, so it lives here and `dataset` re-exports it.
"""

from __future__ import annotations

from enum import Enum


class Association(str, Enum):
    """Where a field lives. Converting between these changes values, so it is never implicit."""

    POINT = "point"
    CELL = "cell"


class AssociationError(Exception):
    """Raised when a field is read as the association it does not have (INV-003)."""
