"""The native renderer: a picture whose colours come from the display surface and whose numbers do not.

XC-257's step 3. E-191 measured that the pinned toolkit renders offscreen here; this is the product
doing it, held to the two rules that make the picture trustworthy: the legend's range is computed on
the full field even when the drawn surface is reduced (INV-001), and a frame with nothing in it is a
refusal rather than an image.

Verifies: view/AC-007, AC-019, XC-087, XC-111, INV-001, INV-009, XC-001, E-191, E-192.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from conftest import requires_offscreen_rendering, requires_vtk

requires_vtk()
requires_offscreen_rendering()

import numpy as np  # noqa: E402
from vtkmodules.util.numpy_support import vtk_to_numpy  # noqa: E402
from vtkmodules.vtkIOImage import vtkPNGReader  # noqa: E402

from domain_core.association import Association  # noqa: E402
from domain_core.dataset import Dataset, Field  # noqa: E402
from engine import reader  # noqa: E402
from engine.visualization.colour_maps import COLOUR_MAPS, GREYS, PLASMA, VIRIDIS  # noqa: E402
from engine.visualization.render import (  # noqa: E402
    Camera,
    Colouring,
    NativeOffscreenRenderer,
    RenderError,
    Scene,
    probe_offscreen,
    render_view,
    resolve_range,
)
from test_reader import write_grid  # noqa: E402

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def decode(png: bytes) -> np.ndarray:
    """The frame as (height, width, channels), read back through the toolkit."""
    png_reader = vtkPNGReader()
    png_reader.SetMemoryBufferLength(len(png))
    png_reader.SetMemoryBuffer(png)
    png_reader.Update()
    image = png_reader.GetOutput()
    width, height, _ = image.GetDimensions()
    channels = image.GetNumberOfScalarComponents()
    return vtk_to_numpy(image.GetPointData().GetScalars()).reshape(height, width, channels)


def a_dataset(tmp_path: Path) -> Dataset:
    path = tmp_path / "case.vtu"
    write_grid(path)
    return reader.read(path)


def stress(**changes) -> Colouring:
    settings = {"field_name": "stress", "association": Association.POINT}
    settings.update(changes)
    return Colouring(**settings)


class TestTheColourMapsShipWithTheirProvenance:
    def test_the_three_maps_the_interface_names_exist_with_256_samples_each(self) -> None:
        assert set(COLOUR_MAPS) == {"viridis", "plasma", "greys"}
        for one in COLOUR_MAPS.values():
            assert len(one.samples) == 256
            assert one.source and one.licence

    def test_the_published_ends_are_the_interface_token_s_ends(self) -> None:
        """tokens.css draws the legend gradient from the same two stops; if they drift, the chrome and
        the picture disagree about what the map looks like."""
        assert (VIRIDIS.samples[0], VIRIDIS.samples[-1]) == ("#440154", "#fde725")
        assert (PLASMA.samples[0], PLASMA.samples[-1]) == ("#0d0887", "#f0f921")
        assert (GREYS.samples[0], GREYS.samples[-1]) == ("#111111", "#f5f5f5")

    def test_every_map_here_says_it_is_uniform_and_cc0_maps_say_so(self) -> None:
        assert all(one.uniform for one in COLOUR_MAPS.values())
        assert "CC0" in VIRIDIS.licence and "CC0" in PLASMA.licence


class TestTheProbeAsksInAnotherProcess:
    def test_the_probe_answers_yes_here_with_the_vendor_line(self) -> None:
        """This module only runs where the probe said yes, so the answer is known; what is tested is
        that it is reached through a child process and carries something a person can read."""
        available, detail = probe_offscreen()

        assert available is True
        assert detail

    def test_a_probe_that_cannot_start_answers_no_rather_than_raising(self, monkeypatch) -> None:
        import subprocess

        def cannot_start(*args, **kwargs):
            raise OSError("no interpreter here")

        monkeypatch.setattr(subprocess, "run", cannot_start)

        available, detail = probe_offscreen()

        assert available is False
        assert "no interpreter here" in detail


class TestAPictureIsProduced:
    def test_a_point_field_renders_to_a_png_of_the_requested_size(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        rendered = render_view([dataset], stress(), width=320, height=200)

        assert rendered.png.startswith(PNG_MAGIC)
        assert rendered.width == 320 and rendered.height == 200
        frame = decode(rendered.png)
        assert frame.shape[:2] == (200, 320)
        assert rendered.reduced == "全三角形を表示しています"

    def test_a_cell_field_renders_through_the_cell_map(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        rendered = render_view([dataset], Colouring("element_stress", Association.CELL), width=200, height=200)

        assert rendered.png.startswith(PNG_MAGIC)
        assert (rendered.legend.minimum, rendered.legend.maximum) == (100.0, 200.0)

    def test_something_other_than_background_is_in_the_frame(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        frame = decode(render_view([dataset], stress(), width=200, height=200, background=(1.0, 1.0, 1.0)).png)

        assert np.any(frame[:, :, :3] != 255), "the geometry and the scalar bar were drawn"

    def test_two_cameras_give_two_different_frames(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        first = render_view([dataset], stress(), width=200, height=200).png
        second = render_view(
            [dataset], stress(), width=200, height=200,
            camera=Camera(position_m=(3.0, -3.0, 4.0), focal_point_m=(0.5, 0.5, 0.0), view_up=(0.0, 0.0, 1.0)),
        ).png

        assert hashlib.sha256(first).hexdigest() != hashlib.sha256(second).hexdigest()

    def test_an_orthographic_camera_is_accepted(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        rendered = render_view(
            [dataset], stress(), width=120, height=120,
            camera=Camera(projection="orthographic", parallel_scale_m=1.0),
        )

        assert rendered.png.startswith(PNG_MAGIC)

    def test_the_renderer_protocol_is_honoured(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        native = NativeOffscreenRenderer()

        png = native.draw(Scene(datasets=(dataset,), colouring=stress()), 100, 80)

        assert png.startswith(PNG_MAGIC)
        assert {"offscreen", "png"} <= native.capabilities()
        with pytest.raises(RenderError):
            native.draw("not a scene", 10, 10)


class TestTheLegendFactsComeFromTheFullField:
    def test_the_range_is_the_field_s_extremes_at_storage_digits_with_the_declared_unit(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        dataset.fields["stress"] = dataset.fields["stress"].declared("MPa")

        legend = render_view([dataset], stress(), width=100, height=100).legend

        assert (legend.minimum, legend.maximum) == (10.0, 40.0)
        assert legend.unit == "MPa"
        assert legend.digits == 6, "float32 storage: six digits, not fifteen (INV-014)"
        assert legend.colour_map == "viridis" and legend.uniform is True
        assert legend.missing_count == 0

    def test_a_reduced_surface_still_reports_the_full_range(self, tmp_path: Path) -> None:
        """INV-001: the picture may be decimated; the numbers on the legend may not be."""
        dataset = a_dataset(tmp_path)

        rendered = render_view([dataset], stress(), width=100, height=100, budget=1)

        assert "間引" in rendered.reduced
        assert (rendered.legend.minimum, rendered.legend.maximum) == (10.0, 40.0)

    def test_an_explicit_range_is_the_range_the_view_stated(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        legend = render_view(
            [dataset], stress(range_mode="explicit", minimum=0.0, maximum=100.0), width=100, height=100,
        ).legend

        assert (legend.minimum, legend.maximum) == (0.0, 100.0)
        assert legend.range_mode == "explicit"

    def test_a_symmetric_range_is_centred_on_zero(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        legend = render_view([dataset], stress(range_mode="symmetric"), width=100, height=100).legend

        assert (legend.minimum, legend.maximum) == (-40.0, 40.0)

    def test_missing_values_are_counted_and_excluded_from_the_range(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)
        values = dataset.fields["stress"].values.copy()
        values[3] = np.nan
        dataset.fields["stress"] = Field("stress", Association.POINT, values)

        rendered = render_view([dataset], stress(), width=100, height=100)

        assert rendered.legend.missing_count == 1
        assert rendered.legend.maximum == 30.0, "the missing entry is not the maximum, and not zero either"

    def test_resolve_range_refuses_a_field_with_no_values(self) -> None:
        field = Field("empty", Association.POINT, np.array([np.nan, np.nan], dtype=np.float32))

        with pytest.raises(RenderError):
            resolve_range([field], stress(field_name="empty"))


class TestWhatIsRefusedRatherThanGuessed:
    def test_an_unknown_colour_map_names_the_known_ones(self) -> None:
        with pytest.raises(RenderError) as refusal:
            stress(colour_map="jet")
        assert "viridis" in str(refusal.value)

    def test_hiding_out_of_range_values_is_refused(self) -> None:
        with pytest.raises(RenderError):
            stress(out_of_range="hide")

    def test_an_explicit_range_needs_both_ends(self) -> None:
        with pytest.raises(RenderError):
            stress(range_mode="explicit", minimum=0.0)

    def test_a_range_over_time_is_refused_until_the_axis_can_be_walked(self) -> None:
        with pytest.raises(RenderError):
            stress(range_mode="dataRangeOverTime")

    def test_an_integration_point_field_is_refused(self) -> None:
        with pytest.raises(RenderError):
            Colouring("sigma", Association.INTEGRATION_POINT)

    def test_a_field_that_is_not_there_is_refused_by_name(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        with pytest.raises(RenderError) as refusal:
            render_view([dataset], stress(field_name="nothing"), width=50, height=50)
        assert "nothing" in str(refusal.value)

    def test_colouring_point_data_as_cell_data_is_refused(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        with pytest.raises(RenderError) as refusal:
            render_view([dataset], Colouring("stress", Association.CELL), width=50, height=50)
        assert "INV-003" in str(refusal.value)

    def test_a_mistyped_size_is_refused(self, tmp_path: Path) -> None:
        dataset = a_dataset(tmp_path)

        with pytest.raises(RenderError):
            render_view([dataset], stress(), width=0, height=50)
        with pytest.raises(RenderError):
            render_view([dataset], stress(), width=50, height=100_000)

    def test_no_datasets_is_refused(self) -> None:
        with pytest.raises(RenderError):
            render_view([], stress(), width=50, height=50)
