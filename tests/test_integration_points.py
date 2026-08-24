"""Values a solver wrote at quadrature points are read as written and never extrapolated (AC-040).

XC-123: "Integration-point values written by a solver are read as written; **this product does not
extrapolate them to nodes**, because the extrapolation depends on the element formulation and the file
does not carry it." That is not a feature left unimplemented - there is no correct version of it to
write, so the refusal is the behaviour.

The structural half matters as much as the refusal. Before this, `Association` had two members and an
integration-point field had **nowhere truthful to sit**; anything holding one would have called it cell
data, and from there every rule about cell data would have applied to it wrongly.

No VTK: no format in this build declares integration-point data, so a field becomes one by declaration,
the way a unit does.
"""

from __future__ import annotations

import numpy as np
import pytest

from domain_core.dataset import Association, AssociationError, Dataset, Field
from domain_core.mesh import Cells

TWO_TRIANGLES = Cells(
    np.array([0, 3, 6], np.int64), np.array([0, 1, 2, 1, 3, 2], np.int64), np.array([5, 5], np.uint8)
)
POINTS = np.array([[0.0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])


def gauss_field(values: np.ndarray, per_cell: int = 4) -> Field:
    return Field("sigma", Association.CELL, values, unit="MPa").at_integration_points(per_cell)


def dataset(values: np.ndarray, per_cell: int = 4) -> Dataset:
    return Dataset(points_m=POINTS, cells=TWO_TRIANGLES, fields={"sigma": gauss_field(values, per_cell)})


class TestTheValuesHaveSomewhereToSit:
    def test_a_field_may_be_declared_at_integration_points(self) -> None:
        field = gauss_field(np.arange(1.0, 9.0))

        assert field.association is Association.INTEGRATION_POINT
        assert field.points_per_cell == 4

    def test_it_must_say_how_many_per_cell(self) -> None:
        """A mesh of n cells with 8 points each and one of 8n cells with one each hold the same number
        of values, so the length alone says nothing about which cell a value belongs to."""
        with pytest.raises(AssociationError) as refusal:
            Field("x", Association.INTEGRATION_POINT, np.arange(8.0))
        assert "how many per cell" in str(refusal.value)

    def test_a_point_or_cell_field_may_not_carry_a_count(self) -> None:
        with pytest.raises(AssociationError):
            Field("x", Association.CELL, np.arange(8.0), points_per_cell=2)

    def test_the_length_is_checked_against_cells_times_points(self) -> None:
        with pytest.raises(ValueError) as refusal:
            dataset(np.arange(7.0))
        assert "8 integration-points" in str(refusal.value)

    def test_the_declaration_is_never_inferred(self) -> None:
        """Solvers name these arrays by convention - `sigma_xx_1` through `_8`. Reading a convention as
        a fact is how eight independent results become one quantity nobody asked to combine."""
        read_as_written = Field("sigma_xx_1", Association.CELL, np.arange(2.0), unit="MPa")

        assert read_as_written.association is Association.CELL
        assert read_as_written.points_per_cell is None


class TestNothingExtrapolatesThemToNodes:
    def test_asking_for_them_as_point_data_is_refused(self) -> None:
        with pytest.raises(AssociationError) as refusal:
            gauss_field(np.arange(1.0, 9.0)).as_point_data()
        assert "要素定式化に依存" in str(refusal.value)
        assert "XC-123" in str(refusal.value)

    def test_asking_for_them_as_cell_data_is_refused_too(self) -> None:
        """Collapsing eight Gauss points into one cell value is the same extrapolation pointed the
        other way, and needs the same information the file does not carry."""
        with pytest.raises(AssociationError):
            gauss_field(np.arange(1.0, 9.0)).as_cell_data()

    def test_the_reason_names_the_file_rather_than_the_product(self) -> None:
        """The user can act on "the file does not carry the element formulation" and cannot act on
        "unsupported"."""
        try:
            gauss_field(np.arange(1.0, 9.0)).as_point_data()
        except AssociationError as refusal:
            assert "ファイルにありません" in str(refusal)


class TestWhichAggregatesAreHonest:
    def test_the_extremum_is_reported(self) -> None:
        """It is exactly the peak value the solver evaluated - no weighting, no interpolation."""
        assert dataset(np.arange(1.0, 9.0)).maximum("sigma").value == 8.0

    def test_a_sum_is_refused_because_the_weights_are_missing(self) -> None:
        total = dataset(np.arange(1.0, 9.0)).total("sigma")

        assert total.is_missing
        assert "求積則の重み" in (total.missing_because or "")

    def test_a_mean_is_refused_for_the_same_reason(self) -> None:
        """An unweighted average of quadrature-point values is not the cell's average."""
        assert dataset(np.arange(1.0, 9.0)).mean("sigma").is_missing

    def test_counting_the_entries_is_a_fact_about_the_array(self) -> None:
        """Not about the physics, so it needs no weights."""
        assert dataset(np.arange(1.0, 9.0)).counted_entries("sigma").value == 8.0
