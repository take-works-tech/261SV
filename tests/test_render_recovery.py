"""A frame the GPU refused while it was being reset comes back on the next try, and the second empty
frame is a refusal that names the causes and the action (operations/AC-035, XC-310; #260, #261).

The renderer makes a fresh window - a fresh context - for every frame, so a context the driver lost
on a resume from sleep, a display change or a reset is nobody's to keep: the next frame makes its
own. What can still happen is the frame drawn while the driver is resetting, which comes back all
background. That frame is drawn once more after a short wait, and only the second empty frame is
refused - with both possibilities named, because "nothing drawn" has two causes and a person can act
on one. Measured with the frames stubbed: an actual reset is not something a test may do to the
machine it runs on (E-229).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from conftest import requires_offscreen_rendering, requires_vtk

requires_vtk()
requires_offscreen_rendering()

from vtkmodules.util.numpy_support import numpy_to_vtk  # noqa: E402
from vtkmodules.vtkCommonDataModel import vtkImageData  # noqa: E402

from engine.visualization import render  # noqa: E402
from engine.visualization.render import EMPTY_FRAME_REFUSAL, RETRY_AFTER_EMPTY_SECONDS, RenderError, render_view  # noqa: E402
from test_render import a_dataset, stress  # noqa: E402


def a_blank_frame(width: int, height: int, background: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> vtkImageData:
    """What the driver hands back while it is resetting: every pixel the background."""
    image = vtkImageData()
    image.SetDimensions(width, height, 1)
    pixels = np.full((width * height, 3), [round(channel * 255) for channel in background], dtype=np.uint8)
    image.GetPointData().SetScalars(numpy_to_vtk(pixels, deep=True))
    return image


class TestAFrameLostToAResettingGPU:
    def test_the_second_try_is_the_picture(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dataset = a_dataset(tmp_path)
        real = render._draw_frame
        tries: list[int] = []

        def flaky(renderer: object, width: int, height: int) -> object:
            tries.append(len(tries))
            return a_blank_frame(width, height) if len(tries) == 1 else real(renderer, width, height)

        monkeypatch.setattr(render, "_draw_frame", flaky)
        monkeypatch.setattr(render, "RETRY_AFTER_EMPTY_SECONDS", 0.0)

        rendered = render_view([dataset], stress(), width=160, height=120)

        assert len(tries) == 2, "one retry, no more"
        assert rendered.png.startswith(b"\x89PNG") and (rendered.width, rendered.height) == (160, 120)

    def test_two_empty_frames_are_a_refusal_naming_the_causes_and_the_action(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dataset = a_dataset(tmp_path)
        tries: list[int] = []

        def resetting(renderer: object, width: int, height: int) -> object:
            tries.append(len(tries))
            return a_blank_frame(width, height)

        monkeypatch.setattr(render, "_draw_frame", resetting)
        monkeypatch.setattr(render, "RETRY_AFTER_EMPTY_SECONDS", 0.0)

        with pytest.raises(RenderError) as refusal:
            render_view([dataset], stress(), width=160, height=120)

        assert len(tries) == 2, "the second empty frame is the answer; a third would be a wait"
        assert str(refusal.value) == EMPTY_FRAME_REFUSAL
        for named in ("GPU", "スリープからの復帰", "ディスプレイの変更", "ドライバのリセット", "視野に何も入っていない", "もう一度描いてください"):
            assert named in str(refusal.value), named

    def test_a_frame_that_draws_is_not_drawn_twice(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dataset = a_dataset(tmp_path)
        real = render._draw_frame
        tries: list[int] = []

        def counted(renderer: object, width: int, height: int) -> object:
            tries.append(len(tries))
            return real(renderer, width, height)

        monkeypatch.setattr(render, "_draw_frame", counted)

        render_view([dataset], stress(), width=160, height=120)

        assert len(tries) == 1

    def test_the_wait_is_short_and_real(self) -> None:
        """Long enough for a driver to finish a reset it has begun, short enough that a person who
        pointed the camera at nothing is not kept waiting."""
        assert 0.1 <= RETRY_AFTER_EMPTY_SECONDS <= 2.0
