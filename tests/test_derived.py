"""The derived-quantity catalogue against analytic answers (INV-020's check, 15_derived_quantities.md).

Every entry this build derives is computed on a tensor or vector whose answer is known by hand, and the
recorded formula and conventions are asserted with the value - a formula nobody reads is a formula
nobody can check (INV-020, XC-121, E-073).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from domain_core.association import Association
from domain_core.dataset import Field
from engine.analysis.derived import (
    GLOBAL_CARTESIAN,
    NOT_BUILT,
    Derived,
    DerivedError,
    Quantity,
    component_names,
    components_of,
    derive,
)

SIGMA = Field(
    "stress6",
    Association.POINT,
    np.array(
        [
            [100.0, 0.0, 0.0, 0.0, 0.0, 0.0],   # uniaxial: von Mises 100, principal 100/0/0, shear 50, trace 100
            [0.0, 0.0, 0.0, 50.0, 0.0, 0.0],    # pure shear XY: von Mises 86.60, principal 50/0/-50, shear 50, trace 0
            [10.0, 10.0, 10.0, 0.0, 0.0, 0.0],  # hydrostatic: von Mises 0, principal 10/10/10, shear 0, trace 30
            [200.0, 100.0, 0.0, 0.0, 0.0, 0.0], # von Mises 173.2, principal 200/100/0, shear 100, trace 300
        ],
        dtype=np.float32,
    ),
    unit="MPa",
)

DISPLACEMENT = Field(
    "displacement",
    Association.POINT,
    np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 0.0], [1.0, 2.0, 2.0], [2.0, 3.0, 6.0]], dtype=np.float32),
    unit="mm",
)


def one(result: tuple[Derived, ...]) -> Derived:
    assert len(result) == 1
    return result[0]


class TestTheTensorEntries:
    def test_von_mises_matches_the_hand_answer_and_records_the_catalogue_formula(self) -> None:
        found = one(derive(SIGMA, Quantity.VON_MISES))

        assert found.name == "stress6.vonMises"
        assert found.values == pytest.approx([100.0, math.sqrt(7500.0), 0.0, math.sqrt(30000.0)])
        assert found.formula == "sqrt( ((XX-YY)^2 + (YY-ZZ)^2 + (ZZ-XX)^2 + 6*(XY^2 + YZ^2 + XZ^2)) / 2 )"
        assert any("XX, YY, ZZ, XY, YZ, XZ" in convention for convention in found.conventions)
        assert any(GLOBAL_CARTESIAN in convention for convention in found.conventions)

    def test_principal_values_are_three_fields_ordered_largest_to_smallest_and_say_so(self) -> None:
        first, second, third = derive(SIGMA, Quantity.PRINCIPAL)

        assert (first.name, second.name, third.name) == ("stress6.principal1", "stress6.principal2", "stress6.principal3")
        assert first.values == pytest.approx([100.0, 50.0, 10.0, 200.0])
        assert second.values == pytest.approx([0.0, 0.0, 10.0, 100.0])
        assert third.values == pytest.approx([0.0, -50.0, 10.0, 0.0])
        assert all(any("大きい順" in convention for convention in found.conventions) for found in (first, second, third))
        assert "largest to smallest" in first.formula

    def test_maximum_shear_and_trace(self) -> None:
        shear = one(derive(SIGMA, Quantity.MAXIMUM_SHEAR))
        trace = one(derive(SIGMA, Quantity.TRACE))

        assert shear.values == pytest.approx([50.0, 50.0, 0.0, 100.0])
        assert shear.formula == "(σ1 - σ3) / 2"
        assert trace.values == pytest.approx([100.0, 0.0, 30.0, 300.0])
        assert trace.formula == "XX + YY + ZZ"

    def test_a_tensor_component_is_named_by_the_convention(self) -> None:
        found = one(derive(SIGMA, Quantity.COMPONENT, component="XY"))

        assert found.name == "stress6.XY"
        assert found.values == pytest.approx([0.0, 50.0, 0.0, 0.0])
        assert found.formula == "stress6[XY]"

    def test_a_missing_component_leaves_every_principal_value_missing(self) -> None:
        holed = Field("s", Association.POINT, np.array([[1.0, 2.0, 3.0, np.nan, 0.0, 0.0], [5.0, 0.0, 0.0, 0.0, 0.0, 0.0]]))

        first, _, third = derive(holed, Quantity.PRINCIPAL)

        assert np.isnan(first.values[0]) and np.isnan(third.values[0])
        assert first.values[1] == pytest.approx(5.0)

    def test_a_two_dimensional_tensor_is_read_as_plane_only_when_asked(self) -> None:
        plane = Field("s2", Association.CELL, np.array([[100.0, 0.0, 0.0], [0.0, 0.0, 50.0]]))

        with pytest.raises(DerivedError, match="対称テンソルではありません"):
            derive(plane, Quantity.VON_MISES)
        found = one(derive(plane, Quantity.VON_MISES, as_tensor=True))

        assert found.values == pytest.approx([100.0, math.sqrt(7500.0)])
        assert any("ZZ, YZ, XZ を 0" in convention for convention in found.conventions)


class TestTheVectorEntries:
    def test_magnitude_is_the_euclidean_norm_with_its_formula(self) -> None:
        found = one(derive(DISPLACEMENT, Quantity.MAGNITUDE))

        assert found.name == "displacement.magnitude"
        assert found.values == pytest.approx([5.0, 0.0, 3.0, 7.0])
        assert found.formula == "sqrt(X^2 + Y^2 + Z^2)"

    def test_a_vector_component_names_its_frame(self) -> None:
        found = one(derive(DISPLACEMENT, Quantity.COMPONENT, component="Z"))

        assert found.values == pytest.approx([0.0, 0.0, 2.0, 6.0])
        assert any("global Cartesian" in convention for convention in found.conventions)

    def test_magnitude_of_a_tensor_is_refused(self) -> None:
        with pytest.raises(DerivedError, match="ベクトル"):
            derive(SIGMA, Quantity.MAGNITUDE)


class TestWhatIsRefused:
    def test_a_frame_that_does_not_exist_is_refused_by_name(self) -> None:
        with pytest.raises(DerivedError, match="cylindrical"):
            derive(DISPLACEMENT, Quantity.COMPONENT, component="X", frame="cylindrical")

    def test_a_scalar_has_nothing_to_derive(self) -> None:
        scalar = Field("t", Association.POINT, np.array([1.0, 2.0]))
        with pytest.raises(DerivedError, match="一成分"):
            derive(scalar, Quantity.MAGNITUDE)

    def test_an_unnamed_component_is_refused_with_the_names_there_are(self) -> None:
        with pytest.raises(DerivedError, match="'X', 'Y', 'Z'"):
            derive(DISPLACEMENT, Quantity.COMPONENT)

    def test_nine_components_have_no_standard_naming(self) -> None:
        nine = Field("full", Association.POINT, np.zeros((2, 9)))
        with pytest.raises(DerivedError, match="九成分"):
            component_names(nine)

    def test_the_rest_of_the_catalogue_says_why_it_is_not_here(self) -> None:
        assert set(NOT_BUILT) == {"principalDirections", "deviatoric", "invariants", "amplitude", "valueAtPhase", "phaseAngle"}
        assert components_of(SIGMA) == 6 and components_of(DISPLACEMENT) == 3
