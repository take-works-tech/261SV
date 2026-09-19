"""Measure whether the pinned VTK renders a colour-mapped surface with a legend to PNG bytes, offscreen.

XC-087 gives the native toolkit two jobs: images for the deliverable, and datasets above the
interactive budget. Before the visualisation path is built on that, the one thing worth knowing is
whether the shipped wheel can do it at all on a machine with no window - and whether it actually
drew something, rather than returning a plausible byte count.

So, like `measure_render.py`, this harness refuses to report a render it cannot prove: it captures
two frames with the camera moved between them and **fails if their hashes are equal**. The legend
is a scalar bar carrying a unit label, because that is what the deliverable needs and what the
interactive placeholder currently fakes with a CSS gradient.

Run:  python spike/measure_offscreen_render.py
Writes: spike/offscreen_render.json
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkLookupTable, vtkVersion
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkWindowToImageFilter,
)
import vtkmodules.vtkRenderingFreeType  # noqa: F401  (text for the scalar bar)
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401  (registers the OpenGL backend)

HERE = Path(__file__).resolve().parent
SIZE = (800, 600)


def scene() -> tuple[vtkRenderWindow, vtkRenderer, int, int]:
    source = vtkSphereSource()
    source.SetThetaResolution(200)
    source.SetPhiResolution(200)
    source.Update()
    surface = source.GetOutput()

    points = vtk_to_numpy(surface.GetPoints().GetData())
    # A float32 field, as a solver writes one. Colours come from it; no number is read from the picture.
    values = (np.hypot(points[:, 0], points[:, 1]) * 100.0).astype(np.float32)
    array = numpy_to_vtk(values, deep=True)
    array.SetName("stress")
    surface.GetPointData().SetScalars(array)

    table = vtkLookupTable()
    table.SetNumberOfTableValues(256)
    table.SetRange(float(values.min()), float(values.max()))
    table.Build()

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(surface)
    mapper.SetLookupTable(table)
    mapper.SetScalarRange(table.GetRange())
    mapper.ScalarVisibilityOn()
    actor = vtkActor()
    actor.SetMapper(mapper)

    bar = vtkScalarBarActor()
    bar.SetLookupTable(table)
    bar.SetTitle("stress [MPa]")
    bar.SetNumberOfLabels(5)

    renderer = vtkRenderer()
    renderer.AddActor(actor)
    renderer.AddViewProp(bar)
    renderer.SetBackground(0.1, 0.1, 0.1)

    window = vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.AddRenderer(renderer)
    window.SetSize(*SIZE)
    return window, renderer, surface.GetNumberOfPoints(), surface.GetNumberOfPolys()


def frame(window: vtkRenderWindow) -> bytes:
    window.Render()
    to_image = vtkWindowToImageFilter()
    to_image.SetInput(window)
    to_image.ReadFrontBufferOff()
    to_image.Update()
    writer = vtkPNGWriter()
    writer.WriteToMemoryOn()
    writer.SetInputConnection(to_image.GetOutputPort())
    writer.Write()
    result = writer.GetResult()
    return bytes(vtk_to_numpy(result)) if result.GetNumberOfTuples() else b""


def main() -> int:
    started = time.perf_counter()
    window, renderer, point_count, polygon_count = scene()
    first = frame(window)
    camera = renderer.GetActiveCamera()
    camera.Azimuth(45.0)
    camera.Elevation(20.0)
    renderer.ResetCamera()
    second = frame(window)
    elapsed = time.perf_counter() - started

    first_hash = hashlib.sha256(first).hexdigest()
    second_hash = hashlib.sha256(second).hexdigest()
    drew_something = bool(first) and bool(second) and first_hash != second_hash
    capabilities = window.ReportCapabilities().splitlines()
    record = {
        "measured": time.strftime("%Y-%m-%d"),
        "vtk_version": vtkVersion.GetVTKVersion(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "opengl": capabilities[0].strip() if capabilities else "",
        "size": list(SIZE),
        "points": point_count,
        "polygons": polygon_count,
        "frame_bytes": [len(first), len(second)],
        "frames_differ": drew_something,
        "seconds_total": round(elapsed, 3),
    }
    (HERE / "offscreen_render.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (HERE / "artifacts").mkdir(exist_ok=True)
    (HERE / "artifacts" / "offscreen_render.png").write_bytes(second)
    print(json.dumps(record, indent=2))
    if not drew_something:
        print("REFUSED: the two frames are identical or empty, so nothing was proven to render.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
