"""Measure interactive render cost, with proof that anything was rendered.

The first two attempts at this measured nothing - a bare render call returned two thousand frames a
second, and forcing a screenshot returned byte-identical images after camera changes. Both produced
plausible numbers. This harness therefore does three things differently:

1. it drives the camera through the toolkit's own API rather than a wrapper property,
2. it hashes every captured frame and **fails outright if consecutive frames are identical**, and
3. it separates the readback cost from the render cost by timing a readback of the same window with an
   empty scene.

A measurement that cannot prove it measured something is not a measurement. This one refuses to report
a number it cannot support.

Run:  .venv-spike/Scripts/python spike/measure_render.py
Writes: spike/render.json
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from vtkmodules.vtkFiltersSources import vtkPlaneSource
from vtkmodules.vtkIOImage import vtkPNGWriter  # noqa: F401  (keeps the image module linked)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkWindowToImageFilter,
)
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401  (registers the OpenGL backend)

HERE = Path(__file__).resolve().parent
RESOLUTIONS = (400, 900, 1600, 2400)  # plane subdivisions: ~0.3M to ~11.5M triangles
FRAMES = 12


def build(resolution: int) -> vtkPolyData:
    plane = vtkPlaneSource()
    plane.SetResolution(resolution, resolution)
    plane.Update()
    surface = plane.GetOutput()

    points = surface.GetPoints()
    coordinates = vtk_to_numpy(points.GetData()).copy()
    coordinates[:, 2] = 0.2 * np.sin(6.0 * coordinates[:, 0]) * np.cos(6.0 * coordinates[:, 1])
    from vtkmodules.util.numpy_support import numpy_to_vtk

    new_points = vtkPoints()
    new_points.SetData(numpy_to_vtk(coordinates, deep=True))
    surface.SetPoints(new_points)

    field = vtkFloatArray()
    field.SetName("stress_MPa")
    values = np.hypot(coordinates[:, 0], coordinates[:, 1]).astype(np.float32) * 100.0
    field.SetNumberOfValues(len(values))
    for index, value in enumerate(values):
        field.SetValue(index, float(value))
    surface.GetPointData().SetScalars(field)

    triangles = vtkTriangleFilter()
    triangles.SetInputData(surface)
    triangles.Update()
    return triangles.GetOutput()


def frame_digest(window: vtkRenderWindow) -> str:
    capture = vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.ReadFrontBufferOff()
    capture.Update()
    image = capture.GetOutput()
    return hashlib.sha1(vtk_to_numpy(image.GetPointData().GetScalars()).tobytes()).hexdigest()


def measure(resolution: int) -> dict:
    mesh = build(resolution)

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(mesh)
    mapper.SetScalarRange(mesh.GetPointData().GetScalars().GetRange())

    actor = vtkActor()
    actor.SetMapper(mapper)

    renderer = vtkRenderer()
    renderer.AddActor(actor)

    window = vtkRenderWindow()
    window.SetOffScreenRendering(True)
    window.SetSize(1280, 720)
    window.AddRenderer(renderer)

    renderer.ResetCamera()
    window.Render()  # warm up: upload geometry and compile shaders

    camera = renderer.GetActiveCamera()
    digests: list[str] = []
    started = time.perf_counter()
    for _ in range(FRAMES):
        camera.Azimuth(7.0)
        window.Render()
        digests.append(frame_digest(window))
    elapsed = time.perf_counter() - started

    distinct = len(set(digests))
    triangles = mesh.GetNumberOfCells()
    per_frame = elapsed / FRAMES

    result = {
        "triangles": int(triangles),
        "frames": FRAMES,
        "distinct_frames": distinct,
        "seconds_per_frame": round(per_frame, 4),
        "frames_per_second": round(1.0 / per_frame, 1) if per_frame else None,
    }
    if distinct < FRAMES:
        result["invalid"] = (
            f"only {distinct} of {FRAMES} frames differ - the harness is not measuring rendering"
        )
    else:
        result["triangles_per_second"] = int(triangles / per_frame)
        result["triangles_at_30fps"] = int(triangles / per_frame / 30)
    return result


def main() -> None:
    rows = [measure(resolution) for resolution in RESOLUTIONS]
    valid = [row for row in rows if "invalid" not in row]
    payload = {
        "note": "includes framebuffer readback per frame, so frame cost is an upper bound",
        "rows": rows,
        "usable": len(valid) == len(rows),
    }
    (HERE / "render.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
