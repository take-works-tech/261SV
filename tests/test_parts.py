"""One @Case, many parts: what is counted, what is named, and what is not summed.

A part is a distinct thing in the model and a partition is one part cut up for parallel input and
output (XC-234). The two are counted separately here because they invalidate different numbers - a
missing partition leaves a hole in one part's mesh, a missing part leaves a whole component out of the
case.

No VTK: these are the rules, not the reading.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.association import Association
from domain_core.case_contents import AxisKind, CaseContents, ResultAxis
from domain_core.dataset import Dataset, Field
from domain_core.mesh import Cells
from domain_core.parts import LoadedCase, Part
from domain_core.reported_value import Caveat

TRIANGLE = Cells(np.array([0, 3], np.int64), np.arange(3, dtype=np.int64), np.array([5], np.uint8))


def mesh(*values: float, unit: str | None = "MPa") -> Dataset:
    return Dataset(
        points_m=np.array([[0.0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        cells=TRIANGLE,
        fields={"stress": Field("stress", Association.POINT, np.array(values), unit=unit)},
    )


def assembly(*, missing: tuple[str, ...] = ()) -> LoadedCase:
    parts = (
        Part("flange", ("asm", "assembly", "flange"), mesh(10.0, 11.0, 12.0)),
        Part("gasket", ("asm", "assembly", "gasket"), mesh(90.0, 91.0, 92.0)),
        Part("bolt", ("asm", "bolt"), mesh(40.0, 41.0, 42.0)),
    )
    return LoadedCase(
        parts=parts,
        contents=CaseContents(
            steps=1, parts=3, axis=ResultAxis(AxisKind.NONE), missing_parts=missing
        ),
    )


class TestPartsAreNamedAndPlaced:
    def test_a_part_is_found_by_name_or_by_its_full_path(self) -> None:
        case = assembly()

        assert case.part("gasket") is case.part("asm / assembly / gasket")

    def test_the_path_is_what_tells_two_parts_of_the_same_name_apart(self) -> None:
        """Two assemblies may each hold a `gasket`, and a name alone would name both."""
        left = Part("gasket", ("asm", "left", "gasket"), mesh(1.0, 2.0, 3.0))
        right = Part("gasket", ("asm", "right", "gasket"), mesh(4.0, 5.0, 6.0))

        assert left.label != right.label

    def test_a_part_whose_path_does_not_end_in_its_name_is_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            Part("gasket", ("asm", "flange"), None)
        assert "ends with its own name" in str(refusal.value)

    def test_an_unnamed_part_is_refused(self) -> None:
        with pytest.raises(ValueError):
            Part("", ("",), None)


class TestAPartTheFileNamedAndDidNotProvide:
    def test_it_is_kept_as_a_part_rather_than_dropped(self) -> None:
        """AC-027. A part silently missing from an assembly is an assembly nobody knows is incomplete."""
        case = assembly(missing=("asm / washer",))

        assert case.is_partial is True
        assert "パート asm / washer" in case.describe()

    def test_the_count_is_of_what_is_there(self) -> None:
        case = assembly(missing=("asm / washer",))

        assert len(case.present) == 3
        assert case.contents.parts == 3

    def test_a_count_that_disagrees_with_what_is_here_is_refused(self) -> None:
        """A count somebody will read is a count that has to be of something."""
        with pytest.raises(ValueError) as refusal:
            LoadedCase(
                parts=(Part("a", ("a",), mesh(1.0, 2.0, 3.0)),),
                contents=CaseContents(steps=1, parts=4, axis=ResultAxis(AxisKind.NONE)),
            )
        assert "disagrees with what is here" in str(refusal.value)


class TestWhatIsAggregatedAcrossParts:
    def test_the_extremum_is_the_largest_across_every_part(self) -> None:
        """The one case-wide aggregate offered: the same taken part by part as taken all at once, and
        the number an engineer reports."""
        value = assembly().maximum("stress")

        assert value.value == 92.0
        assert value.formula == "extremum(stress) over 3 parts"

    def test_a_missing_part_marks_the_case_wide_extremum(self) -> None:
        """The largest value of what is here is not the largest value, and nothing in the digits says
        so."""
        assert Caveat.PARTIAL_DATASET in assembly(missing=("asm / washer",)).maximum("stress").caveats

    def test_a_field_no_part_carries_is_refused_by_name(self) -> None:
        value = assembly().maximum("temperature")

        assert value.is_missing
        assert "temperature" in (value.missing_because or "")

    def test_parts_that_cannot_report_are_named_rather_than_skipped(self) -> None:
        """If every part refuses its own maximum, the case says why rather than saying nothing."""
        holed = LoadedCase(
            parts=(Part("a", ("a",), mesh(1.0, np.nan, 3.0)),),
            contents=CaseContents(steps=1, parts=1, axis=ResultAxis(AxisKind.NONE)),
        )

        value = holed.maximum("stress")

        assert value.is_missing
        assert "欠損" in (value.missing_because or "")

    def test_nothing_offers_a_sum_across_parts(self) -> None:
        """XC-234. Adding a flange's values to a gasket's is arithmetically fine and means nothing, so
        the case does not offer it at all rather than offering it with a warning."""
        assert not hasattr(assembly(), "total")
        assert not hasattr(assembly(), "mean")


class TestPartsAndPartitionsAreCountedApart:
    def test_a_partitioned_part_is_one_part(self) -> None:
        contents = CaseContents(
            steps=1, parts=1, axis=ResultAxis(AxisKind.NONE), partitions=64
        )

        assert contents.parts == 1
        assert contents.partitions == 64
        assert "64 パーティションに分割" in contents.describe()

    def test_the_two_kinds_of_absence_say_which_they_are(self) -> None:
        contents = CaseContents(
            steps=1,
            parts=2,
            axis=ResultAxis(AxisKind.NONE),
            missing_parts=("gasket",),
            partitions=4,
            missing_partitions=("run_1.vtu",),
        )

        assert contents.absences == ("パート gasket", "パーティション run_1.vtu")
        assert contents.is_partial is True


class TestTheCaseWideExtremumSaysWhereItIs:
    def test_it_names_the_part_and_the_place_in_it(self) -> None:
        """A location naming only the node is unusable in an assembly where every part numbers its own
        nodes from one."""
        from domain_core.identifiers import SourceIdentifiers

        def identified(first: float, ids: list[int]) -> Dataset:
            return Dataset(
                points_m=np.array([[0.0, 0, 0], [1, 0, 0], [0, 1, 0]]),
                cells=TRIANGLE,
                fields={
                    "stress": Field(
                        "stress", Association.POINT, np.array([first, first + 1, first + 2]), unit="MPa"
                    )
                },
                identifiers={
                    Association.POINT: SourceIdentifiers(
                        global_ids=np.array(ids, np.int64), global_name="node"
                    )
                },
            )

        case = LoadedCase(
            parts=(
                Part("flange", ("asm", "flange"), identified(10.0, [1, 2, 3])),
                Part("gasket", ("asm", "gasket"), identified(90.0, [1, 2, 3])),
            ),
            contents=CaseContents(steps=1, parts=2, axis=ResultAxis(AxisKind.NONE)),
        )

        value = case.maximum("stress")

        assert value.value == 92.0
        assert value.location == "asm / gasket：node 3"

    def test_a_part_that_cannot_report_is_named_in_the_reason(self) -> None:
        holed = LoadedCase(
            parts=(Part("a", ("a",), mesh(1.0, np.nan, 3.0)),),
            contents=CaseContents(steps=1, parts=1, axis=ResultAxis(AxisKind.NONE)),
        )

        assert "a：" in (holed.maximum("stress").missing_because or "")
