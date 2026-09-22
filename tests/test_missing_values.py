"""A field with missing entries, through every path that reports a number (XC-001, XC-303; #215).

The holed grid of `demo_case.write_holed` has three missing points in `temperature`, one missing
component in `flux` and two missing cells in `load`. Each path below - the load answer, the
statistics with both numbers of a cell field, a probe, a pick, a derived quantity, a graph over two
cases, the deliverable's value table - is asked for its number and held to one rule: computed over
the entries that are there, carrying the caveat and the count; a place with no value is a stated
absence with its reason; nothing is a zero, a blank or a neighbour; and no answer carries a NaN
into JSON, where it would not be a number at all.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from conftest import requires_vtk

requires_vtk()

from demo_case import write_holed  # noqa: E402
from domain_core.reported_value import Caveat, ReportedValue, caveat_notes  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from test_handlers import a_surface, a_workspace  # noqa: E402

MISSING = Caveat.MISSING_VALUES.value


def as_json(answer) -> str:
    """The answer as the transport would send it, refusing a NaN: JSON has no such number."""
    return json.dumps(answer, ensure_ascii=False, allow_nan=False)


@pytest.fixture
def holed(tmp_path: Path):
    """Two cases: the holed grid, and the same grid with every temperature missing."""
    surface, session = a_surface()
    workspace = a_workspace(tmp_path, cases=[{"id": "case:1", "name": "holed"}, {"id": "case:2", "name": "allgone"}])
    opened = surface.submit(Command("workspace.open", {"path": str(workspace)}))
    assert opened.status is Status.APPLIED, opened.reason
    write_holed(tmp_path / "holed.vtu")
    loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(tmp_path / "holed.vtu")]}))
    assert loaded.status is Status.APPLIED, loaded.reason
    return surface, session, loaded.value, tmp_path


def all_gone(surface, tmp_path: Path) -> str:
    """The second case: the holed grid with `temperature` missing everywhere."""
    from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
    from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader, vtkXMLUnstructuredGridWriter

    reader = vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(tmp_path / "holed.vtu"))
    reader.Update()
    grid = reader.GetOutput()
    gone = np.full(vtk_to_numpy(grid.GetPointData().GetArray("temperature")).shape, np.nan, dtype=np.float32)
    replaced = numpy_to_vtk(gone, deep=True)
    replaced.SetName("temperature")
    grid.GetPointData().AddArray(replaced)
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(tmp_path / "allgone.vtu"))
    writer.SetInputData(grid)
    assert writer.Write()
    loaded = surface.submit(Command("dataset.load", {"caseId": "case:2", "filePaths": [str(tmp_path / "allgone.vtu")]}))
    assert loaded.status is Status.APPLIED, loaded.reason
    return loaded.value["datasetId"]


class TestTheLoadAnswer:
    def test_each_field_says_how_many_entries_are_missing(self, holed) -> None:
        _, _, loaded, _ = holed

        counts = {one["name"]: one["missingCount"] for one in loaded["fields"]}

        assert counts == {"temperature": 3, "flux": 1, "load": 2}
        as_json(loaded)


class TestTheStatistics:
    def test_a_point_field_is_summarised_over_the_present_entries_and_every_number_says_so(self, holed) -> None:
        surface, _, loaded, _ = holed

        answer = surface.submit(Command("field.statistics", {"datasetId": loaded["datasetId"], "fieldName": "temperature"}))

        assert answer.status is Status.ANSWERED, answer.reason
        value = answer.value
        assert value["missingCount"] == 3
        assert value["maximum"]["value"] == 400.0 and value["minimum"]["value"] == 300.0
        # 300 + 100 x over the 42 present points, dual-volume weighted: between the extrema, and not
        # the 350 of the full grid, which the three missing points would have pulled it to.
        assert 300.0 < value["mean"]["value"] < 400.0
        for key in ("maximum", "minimum", "mean"):
            assert MISSING in value[key]["caveats"], key
            assert value[key]["missingCount"] == 3, key
        as_json(value)

    def test_a_cell_field_gives_both_numbers_and_both_say_what_they_left_out(self, holed) -> None:
        surface, _, loaded, _ = holed

        answer = surface.submit(Command("field.statistics", {"datasetId": loaded["datasetId"], "fieldName": "load"}))

        assert answer.status is Status.ANSWERED, answer.reason
        value = answer.value
        assert value["missingCount"] == 2 and value["averaging"] == "unaveraged"
        assert value["maximum"]["value"] == 10.0 and value["maximum"]["missingCount"] == 2
        assert value["mean"]["value"] == pytest.approx(10.0) and MISSING in value["mean"]["caveats"]
        averaged = value["averaged"]
        assert averaged["maximum"]["value"] == pytest.approx(10.0)
        assert MISSING in averaged["maximum"]["caveats"] and averaged["maximum"]["missingCount"] == 2
        assert "averaged" in averaged["maximum"]["caveats"]
        assert "値なし" not in averaged["disagreement"]
        as_json(value)

    def test_a_field_missing_everywhere_is_a_stated_absence_with_the_count_and_never_a_zero(self, holed, tmp_path) -> None:
        surface, _, _, _ = holed
        dataset = all_gone(surface, tmp_path)

        answer = surface.submit(Command("field.statistics", {"datasetId": dataset, "fieldName": "temperature"}))

        assert answer.status is Status.ANSWERED, answer.reason
        value = answer.value
        assert value["missingCount"] == 45
        for key in ("maximum", "minimum", "mean"):
            assert value[key]["value"] is None, key
            assert "欠" in value[key]["missingBecause"], key
            assert "0" not in str(value[key]["value"]), key
        as_json(value)


class TestAProbeAndAPick:
    def test_a_probe_at_a_missing_point_is_an_absence_that_says_why(self, holed) -> None:
        surface, _, loaded, _ = holed

        gone = surface.submit(Command("dataset.probe", {"datasetId": loaded["datasetId"], "fieldName": "temperature", "pointM": [0.0, 0.0, 0.0], "resultPosition": 0}))
        there = surface.submit(Command("dataset.probe", {"datasetId": loaded["datasetId"], "fieldName": "temperature", "pointM": [0.5, 0.0, 0.0], "resultPosition": 0}))

        assert gone.status is Status.ANSWERED, gone.reason
        assert gone.value["value"]["value"] is None
        assert "欠測" in gone.value["value"]["missingBecause"]
        assert there.value["value"]["value"] == 350.0 and "missingBecause" not in there.value["value"]
        as_json(gone.value)

    def test_a_pick_reads_a_value_or_states_an_absence_and_never_a_neighbour(self, holed) -> None:
        surface, _, loaded, _ = holed
        view = surface.submit(Command("view.create", {"workspaceId": "ws:1", "definition": {
            "name": "穴", "datasetId": loaded["datasetId"], "representation": "surface",
            "colouring": {"fieldName": "temperature", "association": "point", "colourMap": "viridis"},
            "camera": {"position_m": [-3.0, 0.25, 0.25], "focalPoint_m": [0.0, 0.25, 0.25], "viewUp": [0.0, 1.0, 0.0], "projection": "perspective"},
        }}))
        assert view.status is Status.APPLIED, view.reason

        picked = surface.submit(Command("view.pick", {"viewId": view.value["id"], "width": 400, "height": 300, "x": 200, "y": 150}))

        if picked.status is Status.REFUSED and "描画" in (picked.reason or ""):
            pytest.skip(f"no offscreen renderer here: {picked.reason}")
        assert picked.status is Status.ANSWERED, picked.reason
        reported = picked.value["value"]
        if reported["value"] is None:
            assert reported["missingBecause"]
        else:
            # The x = 0 face carries 300 at every present point; a neighbour's 325 would be a lie.
            assert reported["value"] == 300.0
        as_json(picked.value)


class TestADerivedQuantity:
    def test_a_missing_component_makes_the_magnitude_missing_there_and_the_statistics_say_so(self, holed) -> None:
        surface, _, loaded, _ = holed

        made = surface.submit(Command("field.derive", {"datasetId": loaded["datasetId"], "fieldName": "flux", "quantity": "magnitude"}))
        assert made.status is Status.ANSWERED, made.reason
        answer = surface.submit(Command("field.statistics", {"datasetId": loaded["datasetId"], "fieldName": made.value["fieldName"]}))
        probe = surface.submit(Command("dataset.probe", {"datasetId": loaded["datasetId"], "fieldName": made.value["fieldName"], "pointM": [0.25, 0.0, 0.0], "resultPosition": 0}))

        assert answer.status is Status.ANSWERED, answer.reason
        assert answer.value["missingCount"] == 1
        assert answer.value["maximum"]["value"] == pytest.approx(3.0) and answer.value["maximum"]["missingCount"] == 1
        assert probe.value["value"]["value"] is None and "欠測" in probe.value["value"]["missingBecause"]
        as_json(answer.value)


class TestAGraphAndADeliverable:
    def test_a_graph_point_carries_the_caveat_and_the_count_and_a_case_with_nothing_is_a_gap_with_its_reason(self, holed, tmp_path) -> None:
        surface, _, loaded, _ = holed
        all_gone(surface, tmp_path)
        graph = surface.submit(Command("graph.create", {"workspaceId": "ws:1", "definition": {
            "name": "最大温度", "kind": "line",
            "series": [{"label": "最大温度", "source": {"kind": "field", "datasetId": loaded["datasetId"], "fieldName": "temperature", "association": "point", "reduction": "max"}, "unit": "K", "unitDeclared": True}],
        }}))
        assert graph.status is Status.APPLIED, graph.reason

        data = surface.submit(Command("graph.data", {"graphId": graph.value["id"]}))

        assert data.status is Status.ANSWERED, data.reason
        first, second = data.value["series"][0]["points"]
        assert first["caseId"] == "case:1" and first["value"] == 400.0
        assert MISSING in first["caveats"] and first["missingCount"] == 3
        assert second["caseId"] == "case:2" and second["value"] is None and "欠" in second["reason"]
        assert "caveats" not in second
        assert len(data.value["missing"]) == 1
        as_json(data.value)

    def test_the_deliverable_s_table_says_what_a_number_left_out_and_states_an_absence(self, holed, tmp_path) -> None:
        surface, _, loaded, _ = holed
        report = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "穴", "targets": ["html"], "blocks": [{"kind": "valueTable", "fields": ["temperature", "load"]}],
        }}))
        assert report.status is Status.APPLIED, report.reason

        exported = surface.submit(Command("report.export", {"reportId": report.value["id"], "path": str(tmp_path / "hole.html")}))

        assert exported.status is Status.APPLIED, exported.reason
        html = (tmp_path / "hole.html").read_text(encoding="utf-8")
        assert "欠測 3 件を除いて計算した値です" in html
        assert "欠測 2 件を除いて計算した値です" in html
        # The value cells themselves: never the toolkit's "nan", never a blank, never a zero for a
        # value that was not there. The absence of a whole field is a stated one, by its reason.
        import re

        cells = re.findall(r'<td class="value">(.*?)</td>', html)
        assert cells, html[:400]
        # A real zero - the spread at a node whose cells agree - is a value; a missing one is never a cell.
        assert all(cell.strip().lower() not in ("nan", "", "-", "—") for cell in cells), cells
        assert "<td></td>" not in html


class TestTheRuleItself:
    def test_a_value_computed_with_missing_entries_carries_the_caveat_and_the_count_together(self) -> None:
        held = ReportedValue(value=1.0, unit="Pa", digits=3, provenance=__import__("domain_core.reported_value", fromlist=["Provenance"]).Provenance.DATASET)

        marked = held.with_missing(4)

        assert Caveat.MISSING_VALUES in marked.caveats and marked.missing_count == 4
        assert held.with_missing(0) is held
        assert caveat_notes(marked) == ["欠測 4 件を除いて計算した値です"]
        with pytest.raises(ValueError):
            ReportedValue(value=1.0, unit="Pa", digits=3, provenance=marked.provenance, missing_count=2)

    def test_a_value_derived_from_marked_inputs_adds_up_what_they_left_out(self) -> None:
        from domain_core.reported_value import Provenance

        one = ReportedValue(value=2.0, unit="Pa", digits=3, provenance=Provenance.DATASET).with_missing(3)
        two = ReportedValue(value=4.0, unit="Pa", digits=3, provenance=Provenance.DATASET).with_missing(1)

        ratio = one.derive(0.5, formula="one / two", unit="1", others=[two])

        assert Caveat.MISSING_VALUES in ratio.caveats and ratio.missing_count == 4
