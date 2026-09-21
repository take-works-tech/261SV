"""The shipped sample holds what its formulas say (XC-298, operations/AC-002).

The sample is generated, so every number in it follows from five constants and two formulas of
beam theory, and what the product reports about it can be checked against them - which is the
point of a sample: a first user reads a maximum stress and can see, from the beam in the picture,
that it is the right one.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from conftest import requires_vtk

requires_vtk()

from engine import reader, sample  # noqa: E402


class TestTheCantilever:
    def test_what_is_written_is_what_the_formulas_give(self, tmp_path: Path) -> None:
        facts = sample.write_cantilever(tmp_path / "beam.vtu", force_newton=100.0)
        case = reader.read_case(tmp_path / "beam.vtu")
        dataset = case.present[0].dataset

        assert (facts.points, facts.cells) == (615, 320) == (dataset.point_count, dataset.cell_count)
        assert facts.maximum_stress_pa == pytest.approx(1.2e6)
        assert facts.tip_deflection_m == pytest.approx(4.0e-5)
        # The extremes the product reports are the formulas' - at the clamped end's two surfaces.
        assert case.maximum("stress").value == pytest.approx(1.2e6)
        assert case.maximum("stress").digits == 6, "stored as float32, shown to float32's digits (INV-014)"
        stress = dataset.fields["stress"].values
        assert float(np.min(stress)) == pytest.approx(-1.2e6)
        assert dataset.fields["stress"].unit is None, "the file carries no unit, as a solver's would not (XC-003)"
        assert dataset.fields["displacement"].components == 3
        magnitude = np.linalg.norm(dataset.fields["displacement"].values, axis=1)
        assert float(np.max(magnitude)) == pytest.approx(4.0e-5, rel=1e-6)
        assert float(np.max(dataset.fields["element_stress"].values)) < 1.2e6, "a cell centre is inside the surface"

    def test_the_load_scales_the_answer_and_nothing_else(self, tmp_path: Path) -> None:
        one = sample.write_cantilever(tmp_path / "one.vtu", force_newton=100.0)
        more = sample.write_cantilever(tmp_path / "more.vtu", force_newton=150.0)

        assert more.maximum_stress_pa == pytest.approx(1.5 * one.maximum_stress_pa)
        assert more.tip_deflection_m == pytest.approx(1.5 * one.tip_deflection_m)
        assert (more.points, more.cells) == (one.points, one.cells)
        assert reader.read_case(tmp_path / "more.vtu").maximum("stress").value == pytest.approx(1.8e6)
