"""A pick lands on the surface the person sees and answers from the dataset they did not.

XC-257's step 4. The three honest answers a pick can give - a point's own value, a cell's own value
said to be a cell's, and nothing - are each tested, and the one dishonest answer a pick could give
(the nearest value there is, for a point that is off the model) is tested to be refused.

Verifies: view/AC-027, AC-028, AC-029, INV-001, INV-003, INV-011, INV-023.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

import numpy as np  # noqa: E402

from domain_core.association import Association  # noqa: E402
from domain_core.dataset import Dataset, Field  # noqa: E402
from domain_core.identifiers import NO_IDENTIFIER, SourceIdentifiers, no_identifier  # noqa: E402
from domain_core.reported_value import Caveat, Provenance  # noqa: E402
from engine import reader  # noqa: E402
from engine.visualization.pick import PickError, probe  # noqa: E402
from test_reader import write_grid  # noqa: E402


def a_dataset(tmp_path: Path) -> Dataset:
    path = tmp_path / "case.vtu"
    write_grid(path)
    return reader.read(path)


class TestAPointValueIsThePointsOwn:
    def test_a_pick_on_a_vertex_reads_that_vertex_from_the_full_dataset(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        found = probe(dataset, "stress", (0.0, 1.0, 0.0))

        assert found.association is Association.POINT
        assert found.value.value == 40.0
        assert found.value.digits == 6, "float32 storage (INV-014)"
        assert found.value.provenance is Provenance.DATASET
        assert found.value.unit is None
        assert Caveat.UNDECLARED_UNIT in found.value.caveats
        assert found.distance_m == pytest.approx(0.0)

    def test_a_pick_inside_a_triangle_takes_the_nearest_vertex_and_never_interpolates(self, tmp_path: Path) -> None:
        """INV-003: 0.9 of the way from vertex 0 (10) to vertex 1 (20) is 19 by interpolation and 20
        by the nearest mesh point. Only the second is a number the mesh holds."""
        dataset = a_dataset(tmp_path)

        found = probe(dataset, "stress", (0.9, 0.05, 0.0))

        assert found.value.value == 20.0

    def test_a_pick_slightly_off_the_surface_still_lands(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        found = probe(dataset, "stress", (0.0, 1.0, 0.002))

        assert found.value.value == 40.0
        assert 0.0 < found.distance_m < 0.01

    def test_the_declared_unit_travels_with_the_value(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        dataset.fields["stress"] = dataset.fields["stress"].declared("MPa")

        found = probe(dataset, "stress", (1.0, 1.0, 0.0))

        assert found.value.value == 30.0
        assert found.value.unit == "MPa"
        assert Caveat.UNDECLARED_UNIT not in found.value.caveats

    def test_the_location_is_in_the_source_s_words_or_says_the_source_had_none(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        assert probe(dataset, "stress", (0.0, 0.0, 0.0)).value.location == no_identifier(Association.POINT)
        assert "節点" in no_identifier(Association.POINT), "a node value names the node numbers it lacks"

        dataset.identifiers[Association.POINT] = SourceIdentifiers(
            global_ids=np.array([101, 102, 103, 104], dtype=np.int64), global_name="GlobalNodeId",
        )
        found = probe(dataset, "stress", (0.0, 0.0, 0.0))

        assert found.value.location == "GlobalNodeId 101"

    def test_a_reduced_display_still_answers_with_an_original_point(self, tmp_path: Path) -> None:
        """The pick lands on the decimated surface; the value is the source point's own (INV-001)."""
        dataset = a_dataset(tmp_path)

        found = probe(dataset, "stress", (0.0, 1.0, 0.0), budget=1)

        assert found.value.value in {10.0, 20.0, 30.0, 40.0}
        assert found.value.provenance is Provenance.DATASET


class TestACellValueIsSaidToBeACells:
    def test_a_pick_in_a_cell_reports_the_cell_s_value_and_the_association(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        first = probe(dataset, "element_stress", (0.7, 0.2, 0.0))
        second = probe(dataset, "element_stress", (0.2, 0.7, 0.0))

        assert first.association is Association.CELL
        assert (first.value.value, second.value.value) == (100.0, 200.0)
        assert first.value.location == NO_IDENTIFIER


class TestNothingIsReportedAsNothing:
    def test_a_point_off_the_model_is_missing_not_the_nearest_value(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        found = probe(dataset, "stress", (5.0, 5.0, 5.0))

        assert found.value.value is None
        assert found.value.missing_because and "外" in found.value.missing_because
        assert found.value.unit is None and found.value.digits == 6
        assert found.triangle == -1

    def test_a_missing_entry_stays_missing(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        values = dataset.fields["stress"].values.copy()
        values[3] = np.nan
        dataset.fields["stress"] = Field("stress", Association.POINT, values)

        found = probe(dataset, "stress", (0.0, 1.0, 0.0))

        assert found.value.value is None
        assert found.value.value != 0.0


class TestWhatCannotBeAsked:
    def test_an_unknown_field_is_named(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        with pytest.raises(PickError) as refusal:
            probe(dataset, "nothing", (0.0, 0.0, 0.0))
        assert "nothing" in str(refusal.value)

    def test_a_point_with_the_wrong_shape_is_refused(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        with pytest.raises(PickError):
            probe(dataset, "stress", (0.0, 0.0))
        with pytest.raises(PickError):
            probe(dataset, "stress", (0.0, float("nan"), 0.0))

    def test_an_integration_point_field_is_refused(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        dataset.fields["sigma"] = Field(
            "sigma", Association.INTEGRATION_POINT, np.zeros(2 * 4, dtype=np.float32), points_per_cell=4,
        )
        with pytest.raises(PickError):
            probe(dataset, "sigma", (0.0, 0.0, 0.0))
