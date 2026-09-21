"""This product's numbers against the toolkit's own filters, repeated on every run (#321, XC-287).

`spike/measure_cross_check.py` is the measurement and E-214 its record. This test runs the same
measurement and holds it to what was recorded: every quantity that agreed still agrees exactly, every
difference is still the difference with the reason it had, and nothing has quietly moved from one
column to the other. The reference is the kernel ParaView runs - the VTK filter - and not ParaView
itself, which is stated in the record and repeated here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

ROOT = Path(__file__).resolve().parents[1]


def load_measurement():
    location = ROOT / "spike" / "measure_cross_check.py"
    spec = importlib.util.spec_from_file_location("measure_cross_check", location)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["measure_cross_check"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def record(tmp_path_factory: pytest.TempPathFactory) -> dict:
    return load_measurement().measure(tmp_path_factory.mktemp("cross-check"))


def by_quantity(record: dict) -> dict[tuple[str, str], dict]:
    return {(row["case"], row["quantity"]): row for row in record["rows"]}


class TestWhatAgrees:
    """Exactly, not approximately: the same arithmetic on the same numbers."""

    AGREE = (
        ("cube", "max(temperature)"),
        ("cube", "mean(temperature), dual-volume weights"),
        ("cube", "volume"),
        ("bar", "max(stress) unaveraged"),
        ("bar", "mean(stress), volume weights"),
        ("bar", "max(nodal average of stress)"),
        ("bar", "min(nodal average of stress)"),
        ("bar", "every nodal average"),
        ("fields", "every |displacement|"),
        ("fields", "every principal value 1"),
        ("fields", "every principal value 2"),
        ("fields", "every principal value 3"),
        ("fields", "every von Mises"),
        ("fields", "every maximum shear"),
        ("two parts", "max(nodal average) in the part holding the concentration"),
        ("two parts", "max(nodal average) in the other part"),
        ("box", "mean(f = x), dual-volume weights, against the integrator"),
        ("box", "mean(f = x), dual-volume weights, against the trilinear interpolant"),
        ("box", "volume"),
    )

    @pytest.mark.parametrize("key", AGREE, ids=[f"{case}: {quantity}" for case, quantity in AGREE])
    def test_it_still_agrees(self, record: dict, key: tuple[str, str]) -> None:
        row = by_quantity(record)[key]
        assert row["verdict"] == "agrees", row

    def test_the_numbers_are_the_ones_the_hand_answers_say(self, record: dict) -> None:
        rows = by_quantity(record)
        assert rows[("cube", "mean(temperature), dual-volume weights")]["ours"] == 4.5
        assert rows[("bar", "mean(stress), volume weights")]["ours"] == 52.0
        assert rows[("bar", "max(nodal average of stress)")]["ours"] == 110.0, "E-144"
        assert rows[("two parts", "max(nodal average) in the part holding the concentration")]["ours"] == 200.0


class TestWhatDiffersAndWhy:
    """A difference is recorded with its reason, and the reason is checked, not the mere fact."""

    def test_a_surface_mean_is_refused_here_and_integrated_there(self, record: dict) -> None:
        row = by_quantity(record)[("grid", "mean(stress) on a surface mesh")]
        assert row["verdict"] == "differs"
        assert row["ours"] is None, "INV-017: no volume, no area weighting built - refused, never an unweighted mean"
        assert row["reference"] == pytest.approx(70.0 / 3.0), "the integrator's area average of 10, 20, 30, 40 over two triangles"

    def test_the_merged_average_halves_the_peak_at_a_shared_face(self, record: dict) -> None:
        row = by_quantity(record)[("two parts", "max(nodal average) across the shared face")]
        assert row["verdict"] == "differs"
        assert row["ours"] == 200.0 and row["reference"] == 110.0, "INV-022, E-074: this product never averages across a part"

    def test_the_dual_volume_mean_is_exact_on_a_box_and_not_on_a_skewed_cell(self, record: dict) -> None:
        rows = by_quantity(record)
        against_integrator = rows[("skewed hexahedron", "mean(f = x), dual-volume weights, against the integrator")]
        against_exact = rows[("skewed hexahedron", "mean(f = x), dual-volume weights, against the trilinear interpolant")]
        assert against_integrator["verdict"] == "differs" and against_exact["verdict"] == "differs"
        assert against_exact["ours"] == pytest.approx(0.625)
        assert against_integrator["reference"] == pytest.approx(0.75)
        assert against_exact["reference"] == pytest.approx(5.0 / 7.0), "the trilinear interpolant's own volume average (#402)"

    def test_the_spread_has_no_reference_and_says_so(self, record: dict) -> None:
        row = by_quantity(record)[("bar", "spread at the averaged maximum")]
        assert row["verdict"] == "no reference" and row["ours"] == 180.0


def test_the_record_on_disk_is_the_measurement(record: dict) -> None:
    """`spike/cross_check.json` is what E-214 cites; it must say what a fresh run says, column by column."""
    import json

    written = json.loads((ROOT / "spike" / "cross_check.json").read_text(encoding="utf-8"))
    fresh = {(row["case"], row["quantity"]): row["verdict"] for row in record["rows"]}
    stored = {(row["case"], row["quantity"]): row["verdict"] for row in written["rows"]}
    assert stored == fresh
    assert written["reference"].startswith("VTK filters")
