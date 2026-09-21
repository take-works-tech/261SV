"""The product's numbers against a known solution, through every path that reports one (XC-299,
E-221; #204).

The shipped sample is a cantilever beam whose fields come from beam theory (engine/sample.py), so
every number the product reports about it has a value a reader can compute by hand. This module
asks for those numbers the way a person does - statistics with their weighting, both numbers of a
cell field, a probe at a point, a pick on a picture, a derived quantity, a graph over two cases, the
value table of a deliverable - and holds each to the formula. Where the discrete answer must differ
from the continuous one, the difference is predicted and asserted, not tolerated: the trilinear
interpolant of a cubic deflection integrates to the trapezoid rule's value, and that is what the
weighted mean is expected to be, to a part in a hundred thousand, and not the analytic mean.
"""

from __future__ import annotations

import numpy as np
import pytest
from conftest import requires_vtk

requires_vtk()

from domain_core.precision import format_value  # noqa: E402
from engine import reader, sample  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from test_handlers import a_surface  # noqa: E402

FORCE_N = 100.0
L, H, B, E = sample.LENGTH_M, sample.HEIGHT_M, sample.WIDTH_M, sample.YOUNG_PA
INERTIA = sample.SECOND_MOMENT_M4
NX, NY, NZ = sample.DIVISIONS
DX = L / NX


def sigma(x: float, y: float, force: float = FORCE_N) -> float:
    return force * (L - x) * (y - H / 2.0) / INERTIA


#: The bending stress at the clamped end's top surface - F L (h/2) / I = 1.2 MPa by hand, which the
#: formula reaches to floating point's last place and float32 holds exactly - and at the centre of the
#: cell touching it.
SIGMA_MAX = 1.2e6
assert sigma(0.0, H) == pytest.approx(SIGMA_MAX, rel=1e-12)
CELL_MAX = sigma(DX / 2.0, H - H / (2.0 * NY))
#: The free end's deflection, the beam's mean deflection, and what a trapezoid rule over this grid adds
#: to the mean of a cubic: (dx^2 / 12) * mean of w'' = dx^2 F L / (24 E I).
TIP_M = FORCE_N * L**3 / (3.0 * E * INERTIA)
MEAN_DEFLECTION_M = FORCE_N * L**3 / (8.0 * E * INERTIA)
TRAPEZOID_EXCESS_M = DX**2 * FORCE_N * L / (24.0 * E * INERTIA)


@pytest.fixture
def beam(tmp_path):
    """The sample written and opened, its first case loaded with the units its author declared."""
    surface, session = a_surface()
    made = surface.submit(Command("workspace.sample", {"path": str(tmp_path / "beam.svw")}))
    assert made.status is Status.APPLIED, made.reason
    cases = made.value["cases"]
    loaded = surface.submit(Command("dataset.load", {"caseId": cases[0]["id"], "filePaths": [cases[0]["sources"][0]["path"]]}))
    assert loaded.status is Status.APPLIED, loaded.reason
    return surface, session, made.value, loaded.value["datasetId"]


class TestTheStatistics:
    def test_the_stress_extrema_are_the_formula_s_and_its_weighted_mean_is_the_formula_s_zero(self, beam) -> None:
        surface, _, _, dataset_id = beam

        answer = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))

        assert answer.status is Status.ANSWERED, answer.reason
        value = answer.value
        # 1.2e6 is exactly a float32 number, so the file holds it exactly and the product reports it so.
        assert value["maximum"]["value"] == SIGMA_MAX
        assert value["minimum"]["value"] == -SIGMA_MAX
        assert value["maximum"]["unit"] == "Pa" and value["maximum"]["digits"] == 6
        # The stress is bilinear, so its trilinear interpolant is itself and its integral over the beam
        # is the analytic zero; what remains is float32's rounding of the nodal values, under a pascal.
        assert value["weighting"] == "dualVolume"
        assert abs(value["mean"]["value"]) < 1.0, value["mean"]
        assert value["resultPosition"]["count"] == 1, "a steady result has one position"

    def test_the_cell_field_gives_both_numbers_and_here_they_agree(self, beam) -> None:
        surface, _, _, dataset_id = beam

        answer = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "element_stress"}))

        assert answer.status is Status.ANSWERED, answer.reason
        value = answer.value
        assert value["averaging"] == "unaveraged"
        assert value["maximum"]["value"] == pytest.approx(CELL_MAX, rel=1e-6) and CELL_MAX == pytest.approx(888750.0)
        assert value["weighting"] == "volume" and abs(value["mean"]["value"]) < 1.0
        # The node at the clamped end's top touches cells of one value only, so the averaged maximum is
        # the element maximum and the spread there is nothing - the case INV-033 says looks converged,
        # and here it is converged, because the cells that meet there are the same cell twice over z.
        averaged = value["averaged"]
        assert averaged["maximum"]["value"] == pytest.approx(CELL_MAX, rel=1e-6)
        assert averaged["spreadAtMaximum"]["value"] == pytest.approx(0.0, abs=1e-3)
        assert "averaged" in averaged["maximum"]["caveats"]


class TestAProbeAndAPick:
    @pytest.mark.parametrize(
        ("point", "expected"),
        [
            ((0.5, H, 0.0), sigma(0.5, H)),
            ((0.25, 0.0, B), sigma(0.25, 0.0)),
            ((0.5, H / 2.0, B), 0.0),
        ],
    )
    def test_a_probe_at_a_node_reads_the_formula_s_value_there(self, beam, point, expected) -> None:
        """At nodes on the beam's surface: a probe reads the nearest surface, and a point inside the
        body is a stated absence (view/AC-029), which is a different test."""
        surface, _, _, dataset_id = beam

        answer = surface.submit(Command("dataset.probe", {"datasetId": dataset_id, "fieldName": "stress", "pointM": list(point), "resultPosition": 0}))

        assert answer.status is Status.ANSWERED, answer.reason
        assert answer.value["value"]["value"] == pytest.approx(expected, rel=1e-6, abs=1e-3)
        assert answer.value["value"]["unit"] == "Pa" and answer.value["value"]["provenance"] == "dataset"

    def test_a_pick_on_the_picture_reads_a_value_the_beam_holds_at_a_node(self, beam, tmp_path) -> None:
        """A pick names no node here - the file carries no identifiers - so what is checked is that the
        value read off the picture is one the field takes at some node, in the declared unit."""
        surface, _, opened, dataset_id = beam
        view = surface.submit(Command("view.create", {"workspaceId": opened["workspaceId"], "definition": {
            "name": "梁", "datasetId": dataset_id, "representation": "surface",
            "colouring": {"fieldName": "stress", "association": "point", "colourMap": "viridis"},
            "camera": {"position_m": [0.5, 0.05, 3.0], "focalPoint_m": [0.5, 0.05, 0.0], "viewUp": [0.0, 1.0, 0.0], "projection": "perspective"},
        }}))
        assert view.status is Status.APPLIED, view.reason

        picked = surface.submit(Command("view.pick", {"viewId": view.value["id"], "width": 400, "height": 300, "x": 200, "y": 150}))

        if picked.status is Status.REFUSED and "描画" in (picked.reason or ""):
            pytest.skip(f"no offscreen renderer here: {picked.reason}")
        assert picked.status is Status.ANSWERED, picked.reason
        held = {float(one) for one in reader.read_case(tmp_path / "beam.data" / "cantilever_100N.vtu").present[0].dataset.fields["stress"].values}
        assert picked.value["value"]["value"] in held
        assert picked.value["value"]["unit"] == "Pa" and abs(picked.value["value"]["value"]) <= SIGMA_MAX


class TestADerivedQuantity:
    def test_the_displacement_magnitude_has_the_tip_deflection_as_its_maximum_and_the_trapezoid_mean(self, beam) -> None:
        surface, _, _, dataset_id = beam

        made = surface.submit(Command("field.derive", {"datasetId": dataset_id, "fieldName": "displacement", "quantity": "magnitude"}))
        assert made.status is Status.ANSWERED, made.reason
        answer = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": made.value["fieldName"]}))

        assert answer.status is Status.ANSWERED, answer.reason
        value = answer.value
        assert value["maximum"]["value"] == pytest.approx(TIP_M, rel=1e-6)
        assert value["maximum"]["unit"] == "m"
        assert "sqrt" in made.value["formula"] or "magnitude" in made.value["formula"]
        # The deflection is cubic in x, so the trilinear interpolant is not it, and its integral is the
        # trapezoid rule's: the analytic mean plus dx^2 F L / (24 E I). Predicted, then asserted.
        assert value["mean"]["value"] == pytest.approx(MEAN_DEFLECTION_M + TRAPEZOID_EXCESS_M, rel=1e-5)
        assert value["mean"]["value"] != pytest.approx(MEAN_DEFLECTION_M, rel=1e-5), "the discretisation is visible, as it should be"


class TestAGraphAndADeliverable:
    def test_a_graph_over_both_cases_plots_the_two_maxima(self, beam) -> None:
        surface, _, opened, dataset_id = beam
        second = opened["cases"][1]
        loaded = surface.submit(Command("dataset.load", {"caseId": second["id"], "filePaths": [second["sources"][0]["path"]]}))
        assert loaded.status is Status.APPLIED, loaded.reason
        graph = surface.submit(Command("graph.create", {"workspaceId": opened["workspaceId"], "definition": {
            "name": "応力の最大", "kind": "line",
            "series": [{"label": "応力の最大", "source": {"kind": "field", "datasetId": dataset_id, "fieldName": "stress", "association": "point", "reduction": "max"}, "unit": "Pa", "unitDeclared": True}],
        }}))
        assert graph.status is Status.APPLIED, graph.reason

        data = surface.submit(Command("graph.data", {"graphId": graph.value["id"]}))

        assert data.status is Status.ANSWERED, data.reason
        # 1.8e6 is an integer below 2^24, so float32 holds it exactly too.
        assert [one["value"] for one in data.value["series"][0]["points"]] == [SIGMA_MAX, 1.8e6]
        assert data.value["series"][0]["unit"] == "Pa" and data.value["cases"] == [opened["cases"][0]["id"], second["id"]]

    def test_the_deliverable_states_the_maximum_as_the_formula_gives_it(self, beam, tmp_path) -> None:
        surface, _, opened, _ = beam
        report = surface.submit(Command("report.create", {"workspaceId": opened["workspaceId"], "definition": {
            "name": "梁", "targets": ["html"], "blocks": [{"kind": "valueTable", "fields": ["stress"]}],
        }}))
        assert report.status is Status.APPLIED, report.reason

        exported = surface.submit(Command("report.export", {"reportId": report.value["id"], "path": str(tmp_path / "beam.html")}))

        assert exported.status is Status.APPLIED, exported.reason
        text = (tmp_path / "beam.html").read_text(encoding="utf-8")
        assert format_value(SIGMA_MAX, 6) in text and format_value(SIGMA_MAX, 6) == "1.20000e+6"
        assert "Pa" in text and "1200000" not in text.replace("1.20000e+6", ""), "the digits are float32's, not more"


def test_the_predicted_discretisation_error_is_what_the_grid_gives() -> None:
    """The prediction the mean test rests on, checked on the same grid without the product: the
    trapezoid rule over the nodes against the analytic integral of the deflection."""
    xs = np.linspace(0.0, L, NX + 1)
    w = sample.deflection_m(xs, FORCE_N)
    trapezoid_mean = float(np.sum((w[1:] + w[:-1]) / 2.0 * np.diff(xs))) / L
    assert trapezoid_mean == pytest.approx(MEAN_DEFLECTION_M + TRAPEZOID_EXCESS_M, rel=1e-12)
