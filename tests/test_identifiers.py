"""What the file called a point, kept and reported (INV-023, ingest/AC-035, AC-036).

"The maximum is at node 12345" is checkable in the solver. "The maximum is at index 8412" is checkable
nowhere and changes if the file is written again. So the identifier the source wrote is preserved and
reported, and where a file carries none this product says so instead of offering the array position
wearing the same clothes.

No VTK: the rules are the rules. `tests/test_reader.py` covers the reading.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.association import Association
from domain_core.dataset import Dataset, Field
from domain_core.identifiers import NO_IDENTIFIER, SourceIdentifiers, location_of
from domain_core.mesh import Cells

QUAD = Cells(np.array([0, 3, 6], np.int64), np.array([0, 1, 2, 1, 3, 2], np.int64), np.array([5, 5], np.uint8))
POINTS = np.array([[0.0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])


def dataset(*, identified: bool) -> Dataset:
    identifiers = {}
    if identified:
        identifiers[Association.POINT] = SourceIdentifiers(
            global_ids=np.array([1001, 1002, 1003, 1004], np.int64), global_name="GlobalNodeId"
        )
    return Dataset(
        points_m=POINTS,
        cells=QUAD,
        fields={"stress": Field("stress", Association.POINT, np.array([10.0, 20.0, 90.0, 40.0]), unit="MPa")},
        identifiers=identifiers,
    )


class TestAnExtremeValueSaysWhereItIs:
    def test_it_uses_the_identifier_the_file_wrote(self) -> None:
        value = dataset(identified=True).maximum("stress")

        assert value.value == 90.0
        assert value.location == "GlobalNodeId 1003"

    def test_a_file_with_no_identifiers_says_so_and_offers_no_index(self) -> None:
        """AC-036. The index of the maximum here is 2, and 2 appears nowhere in what is said."""
        value = dataset(identified=False).maximum("stress")

        assert value.value == 90.0
        assert value.location == NO_IDENTIFIER
        assert "2" not in (value.location or "")

    def test_the_absence_is_phrased_as_a_fact_about_the_file(self) -> None:
        """Not as a failure of this product: the reader did nothing wrong and the user can act on the
        difference - one of the two can be fixed by asking the solver to write ids."""
        assert "このファイル" in NO_IDENTIFIER
        assert "配列位置は識別子ではありません" in NO_IDENTIFIER

    def test_a_pedigree_identifier_is_reported_beside_the_global_one(self) -> None:
        identifiers = SourceIdentifiers(
            global_ids=np.array([7, 8], np.int64),
            global_name="node",
            pedigree_ids=("weld-A", "weld-B"),
            pedigree_name="tag",
        )

        assert identifiers.at(1) == "node 8 / tag weld-B"


class TestAnIdentifierIsNotAField:
    def test_identifiers_are_held_apart_from_the_variables(self) -> None:
        """`GlobalNodeId` in the list a user picks a @Variable from invites a plot of node numbers
        against node numbers."""
        held = dataset(identified=True)

        assert sorted(held.fields) == ["stress"]
        assert Association.POINT in held.identifiers

    def test_a_global_identifier_stays_an_integer(self) -> None:
        """float64 stops being exact above 2^53, and an identifier's exactness is the whole of its
        value: node 9007199254740993 must not become node 9007199254740992."""
        with pytest.raises(ValueError) as refusal:
            SourceIdentifiers(global_ids=np.array([1.0, 2.0]), global_name="node")
        assert "two different nodes into one" in str(refusal.value)

    def test_a_pedigree_identifier_may_be_text(self) -> None:
        """E-135: VTK accepts a string array as PEDIGREEIDS, which no numeric field could hold."""
        identifiers = SourceIdentifiers(pedigree_ids=("A", "B"), pedigree_name="tag")

        assert identifiers.at(0) == "tag A"

    def test_identifiers_carry_the_name_the_file_gave_them(self) -> None:
        """A report says `GlobalNodeId 1003` rather than inventing a word for it."""
        with pytest.raises(ValueError) as refusal:
            SourceIdentifiers(global_ids=np.array([1, 2], np.int64))
        assert "the name the file gave them" in str(refusal.value)


class TestWhatIsSaidWhenNothingIsKnown:
    def test_no_identifiers_at_all_still_answers(self) -> None:
        assert location_of(None, 0) == NO_IDENTIFIER

    def test_an_empty_identifier_record_answers_the_same_way(self) -> None:
        assert location_of(SourceIdentifiers(), 0) == NO_IDENTIFIER

    def test_a_record_knows_how_many_entries_it_names(self) -> None:
        assert SourceIdentifiers(global_ids=np.array([1, 2, 3], np.int64), global_name="n").count() == 3
        assert SourceIdentifiers().count() is None
