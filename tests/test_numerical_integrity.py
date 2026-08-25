"""Two ways this product could report a wrong number while doing correct arithmetic.

Neither is exotic; both are the ordinary shape of CAE data meeting the ordinary way of reducing it, and
both were measured before they were specified (E-143, E-144).

**Accumulation.** A float32 field of 300.0 varying by 1e-3 has an exact mean of 299.999999895342 and a
float32-accumulated mean of exactly 300.000000000000 - the variation the field was written to carry is
gone, and what is printed is the offset. A difference between two such values is worse: 1e-7 apart, they
subtract to exactly 0.0 in float32, and zero is what an engineer reads as "these agree".

**Averaging.** The averaged maximum of a concentration inside a body is 110 MPa against an element
maximum of 200 MPa. Neither is wrong; they answer different questions, and the same concentration at an
end face gives 200 either way - so this is invisible to a check placed at a boundary.

Verifies: INV-031, INV-032, XC-246, XC-247, E-143, E-144.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from conftest import VTK_HEXAHEDRON

from domain_core.association import Association
from domain_core.dataset import Dataset, Field
from domain_core.mesh import Cells
from engine.analysis.nodal import (
    AVERAGING_WORD,
    Averaging,
    NodalError,
    both,
    disagreement,
    extremum,
    to_nodes,
)
from engine.analysis.summary import Reduction, Weighting, summarise

#: The measured figures of E-143, restated here so a change in behaviour fails against the record
#: rather than against a fresh expectation.
EXACT_MEAN = 299.999999895342
OFFSET, VARIATION, COUNT = 300.0, 1.0e-3, 10_000_000


def a_field(count: int, dtype: type = np.float32) -> np.ndarray:
    """A field varying in its fourth significant digit about a large value."""
    return (OFFSET + np.random.default_rng(20260825).normal(0.0, VARIATION, count)).astype(dtype)


def bar(cell_values: list[float]) -> tuple[Dataset, Field]:
    """A row of hexahedra sharing faces, one value per element."""
    count = len(cell_values)
    points = np.array(
        [
            (float(index), y, z)
            for index in range(count + 1)
            for y in (0.0, 1.0)
            for z in (0.0, 1.0)
        ],
        dtype=np.float64,
    )

    def node(index: int, y: int, z: int) -> int:
        return index * 4 + y * 2 + z

    connectivity: list[int] = []
    offsets = [0]
    for index in range(count):
        connectivity += [
            node(index, 0, 0), node(index + 1, 0, 0),
            node(index + 1, 1, 0), node(index, 1, 0),
            node(index, 0, 1), node(index + 1, 0, 1),
            node(index + 1, 1, 1), node(index, 1, 1),
        ]
        offsets.append(len(connectivity))

    field = Field("stress", Association.CELL, np.array(cell_values, dtype=np.float64), unit="MPa")
    dataset = Dataset(
        points_m=points,
        cells=Cells(
            np.array(offsets, dtype=np.int64),
            np.array(connectivity, dtype=np.int64),
            np.full(count, VTK_HEXAHEDRON, dtype=np.uint8),
        ),
        fields={"stress": field},
    )
    return dataset, field


class TestAccumulationHappensInDoublePrecision:
    def test_a_float32_field_summed_in_float32_loses_the_variation(self) -> None:
        """Not this product's behaviour - the measurement the rule exists for (E-143). If this ever
        stops being true, INV-031's reason has changed and the invariant should be re-read."""
        values = a_field(COUNT)

        naive = float(values.sum()) / COUNT
        careful = float(values.sum(dtype=np.float64)) / COUNT

        # The measured figure, restated: the float32 accumulation returns the offset exactly, and the
        # variation the field was written to carry is nowhere in it.
        assert naive == OFFSET
        assert careful == pytest.approx(EXACT_MEAN, abs=1e-9)

    def test_this_product_accumulates_in_double(self) -> None:
        """INV-031. The mean of a float32 field comes back with the variation intact."""
        values = a_field(COUNT)
        exact = math.fsum(values.astype(np.float64).tolist()) / COUNT

        found = summarise(
            values, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert found.value is not None
        assert abs(found.value - exact) < 1.0e-9
        assert found.value != float(values.sum()) / COUNT

    def test_the_storage_precision_is_not_changed_to_achieve_it(self) -> None:
        """XC-246's other half: store what the file gave, compute in double, show what the source
        supports. Promoting the storage would double what a case costs against LIM-001 for digits
        INV-014 refuses to display anyway."""
        values = a_field(COUNT)
        field = Field("stress", Association.CELL, values, unit="MPa")

        summarise(
            field.values, reduction=Reduction.MEAN, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert field.values.dtype == np.float32

    def test_subtraction_itself_loses_nothing_and_the_first_version_of_this_said_it_did(self) -> None:
        """The correction, kept as a test because it is the reason INV-031 no longer argues from it.

        Two float values within a factor of two subtract **exactly** - Sterbenz's lemma - so a @Diff
        computed in the storage precision loses nothing to the subtraction. The 0.0 that looked like a
        loss was two literals rounding to the same float32 before anything was subtracted.
        """
        rng = np.random.default_rng(1)
        left = rng.uniform(1.0, 1000.0, 10_000).astype(np.float32)
        right = (left * rng.uniform(0.5, 2.0, 10_000)).astype(np.float32)

        in_single = (left - right).astype(np.float64)
        in_double = left.astype(np.float64) - right.astype(np.float64)

        assert (in_single == in_double).all()
        assert np.float32(300.0000001) == np.float32(300.0)

    def test_the_reduction_is_accurate_to_the_measured_bound(self) -> None:
        """E-143 measured 1.6e-16 relative error for a pairwise float64 sum. Asserted against that
        figure rather than against the implementation, so it holds however the sum is written.

        The first version of this compared the result against Python's built-in `sum()` and asserted
        this product was closer. That test passed on 3.11 and **failed on CI**, because 3.12 changed
        `sum()` to Neumaier summation "to improve accuracy and commutativity when summing floats" - so
        the reference point moved and the assertion was measuring the interpreter, not this product.
        The local interpreter was 3.11 and `conftest.py` prints a warning about exactly that; the
        warning was there and I read past it.
        """
        values = a_field(COUNT, np.float64)
        exact = math.fsum(values.tolist())

        found = summarise(
            values, reduction=Reduction.SUM, association=Association.CELL,
            scope="全体", weighting=Weighting.NONE,
        )

        assert found.value is not None
        assert abs(found.value - exact) / abs(exact) < 1.0e-15


class TestASharedNodeHoldsSeveralValues:
    def test_the_averaged_maximum_is_lower_than_the_element_maximum(self) -> None:
        """INV-032, E-144: 110 MPa against 200 MPa on a concentration inside the body."""
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        raw, averaged = both(dataset, field)

        assert raw.value == 200.0
        assert averaged.value == pytest.approx(110.0)

    def test_the_gap_is_large_enough_to_change_what_a_report_says(self) -> None:
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        raw, averaged = both(dataset, field)

        assert averaged.value / raw.value == pytest.approx(0.55)

    def test_a_concentration_at_the_end_face_hides_the_effect_entirely(self) -> None:
        """Which is why the mesh above puts it in the middle. A check written on a boundary peak reports
        that averaging is harmless."""
        dataset, field = bar([10.0, 20.0, 60.0, 200.0])

        raw, averaged = both(dataset, field)

        assert raw.value == averaged.value == 200.0
        assert "1 つだけ" in disagreement(raw, averaged)

    def test_each_figure_says_which_one_it_is(self) -> None:
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        raw, averaged = both(dataset, field)

        assert AVERAGING_WORD[Averaging.UNAVERAGED] in raw.describe()
        assert AVERAGING_WORD[Averaging.AVERAGED] in averaged.describe()

    def test_the_averaged_figure_carries_the_spread_it_was_averaged_from(self) -> None:
        """XC-247. The combination that misleads is the smoothed peak shown alone: it looks
        converged."""
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        _, averaged = both(dataset, field)

        assert averaged.spread == pytest.approx(180.0)
        assert "ばらつき" in averaged.describe()

    def test_the_spread_is_offered_as_a_mesh_indicator_and_not_as_an_accuracy_claim(self) -> None:
        """INV-033: what a post-processor can measure from one solve is where to refine, not whether
        the answer converged."""
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        _, averaged = both(dataset, field)

        assert "メッシュ細分の目安" in averaged.describe()
        assert "精度の保証ではありません" in averaged.describe()

    def test_which_averaging_to_use_has_no_default(self) -> None:
        """The two differ by 45 per cent, so a product that picked would be choosing which of them
        somebody read."""
        import inspect

        assert inspect.signature(extremum).parameters["averaging"].default is inspect.Parameter.empty

    def test_the_disagreement_is_stated_in_both_absolute_and_relative_terms(self) -> None:
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        line = disagreement(*both(dataset, field))

        assert "90" in line and "%" in line


class TestTheSpreadIsPerNode:
    def test_a_node_between_two_elements_carries_their_difference(self) -> None:
        dataset, field = bar([10.0, 200.0])

        at_nodes = to_nodes(dataset, field)

        # The four nodes of the shared face see both cells; the outer ones see one each.
        assert at_nodes.spread[4] == pytest.approx(190.0)
        assert at_nodes.spread[0] == pytest.approx(0.0)

    def test_the_fraction_is_the_spread_over_the_average(self) -> None:
        """A 2 MPa spread means one thing on a 4 MPa average and another on a 400 MPa one."""
        dataset, field = bar([10.0, 200.0])

        at_nodes = to_nodes(dataset, field)

        assert at_nodes.fraction[4] == pytest.approx(190.0 / 105.0)

    def test_a_fraction_of_an_average_of_zero_is_undetermined_rather_than_zero(self) -> None:
        """Returning zero there would read as perfect agreement at exactly the nodes where the value
        cancels."""
        dataset, field = bar([-10.0, 10.0])

        at_nodes = to_nodes(dataset, field)

        assert np.isnan(at_nodes.fraction[4])

    def test_the_worst_node_is_answerable(self) -> None:
        dataset, field = bar([10.0, 20.0, 200.0, 20.0, 10.0])

        at_nodes = to_nodes(dataset, field)

        assert at_nodes.spread[at_nodes.worst_node or 0] == pytest.approx(180.0)

    def test_a_cell_with_no_value_contributes_nothing_rather_than_a_zero(self) -> None:
        """INV-011. A missing value pulled into an average as zero is a value nobody measured."""
        dataset, field = bar([float("nan"), 200.0])

        at_nodes = to_nodes(dataset, field)

        assert at_nodes.values[4] == pytest.approx(200.0)
        assert at_nodes.contributors[4] == 1

    def test_averaging_a_point_field_is_refused(self) -> None:
        dataset, _ = bar([10.0, 20.0])
        wrong = Field("stress", Association.POINT, np.zeros(dataset.point_count), unit="MPa")

        with pytest.raises(NodalError):
            to_nodes(dataset, wrong)

    def test_the_accumulation_here_is_double_precision_too(self) -> None:
        """The averaging sums over every cell attached to a point, which is the same accumulation
        INV-031 is about."""
        dataset, field = bar([10.0, 20.0])
        single = Field("stress", Association.CELL, field.values.astype(np.float32), unit="MPa")

        assert to_nodes(dataset, single).values.dtype == np.float64

class TestADifferenceReportsTheDigitsItHasLeft:
    """INV-034: the one place the arithmetic is exact and the printed number is still a lie."""

    def test_a_near_equal_difference_keeps_only_the_digits_that_survived(self) -> None:
        from domain_core.precision import FLOAT64_DIGITS, digits_after_subtraction

        left = digits_after_subtraction(300.0000001, 300.0, source_digits=FLOAT64_DIGITS)

        assert left == 5
        assert left < FLOAT64_DIGITS

    def test_a_difference_of_well_separated_values_keeps_nearly_all_of_them(self) -> None:
        from domain_core.precision import FLOAT64_DIGITS, digits_after_subtraction

        assert digits_after_subtraction(300.0, 100.0, source_digits=FLOAT64_DIGITS) == 14

    def test_a_difference_below_the_resolution_of_its_operands_has_none(self) -> None:
        """Reported as unresolvable rather than as a number: a value nobody can resolve is not a small
        value (INV-011)."""
        from domain_core.precision import FLOAT32_DIGITS, digits_after_subtraction, resolvable

        assert digits_after_subtraction(300.0001, 300.0, source_digits=FLOAT32_DIGITS) == 0
        assert resolvable(300.0001, 300.0, source_digits=FLOAT32_DIGITS) is False

    def test_two_equal_values_have_no_difference_to_report_digits_of(self) -> None:
        from domain_core.precision import FLOAT64_DIGITS, digits_after_subtraction

        assert digits_after_subtraction(5.0, 5.0, source_digits=FLOAT64_DIGITS) == 0

    def test_the_storage_type_does_not_answer_this_question(self) -> None:
        """`significant_digits` reads the storage, which is the right answer to a different question.
        A float64 difference of two nearly equal float64 values genuinely is float64, and genuinely
        carries five digits rather than fifteen."""
        from domain_core.precision import (
            FLOAT64_DIGITS,
            digits_after_subtraction,
            significant_digits,
        )

        stored = significant_digits(np.float64)
        actual = digits_after_subtraction(300.0000001, 300.0, source_digits=FLOAT64_DIGITS)

        assert stored == 15
        assert actual == 5
