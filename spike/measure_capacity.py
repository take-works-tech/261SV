"""Measure the two capacity limits the specification still holds as assumptions.

LIM-001 says a dataset may occupy up to 8 GB in memory; LIM-002 says twenty million triangles render
interactively. Both were taken from platform documentation rather than from this product. This script
replaces the first with a measured ratio - how many bytes of process memory one point of loaded mesh
actually costs - and the second with a measured render throughput, so the numbers stop being guesses.

Run:  .venv-spike/Scripts/python spike/measure_capacity.py
Writes: spike/capacity.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pyvista as pv
import vtk

HERE = Path(__file__).resolve().parent
SIZES = (200, 500, 900)  # side of the structured grid: 40k, 250k, 810k points


def build(side: int) -> pv.PolyData:
    x = np.linspace(-1.0, 1.0, side, dtype=np.float32)
    xx, yy = np.meshgrid(x, x)
    zz = (0.2 * np.sin(5.0 * xx) * np.cos(5.0 * yy)).astype(np.float32)
    grid = pv.StructuredGrid(xx, yy, zz)
    grid["stress_MPa"] = (np.hypot(xx, yy) * 100.0).astype(np.float32).ravel(order="F")
    return grid.extract_surface().triangulate()


def measure_memory() -> list[dict]:
    """VTK reports what a dataset occupies, which is what LIM-001 governs - a truer figure than the
    process working set, which also holds the interpreter, the renderer and whatever else is loaded."""
    rows = []
    for side in SIZES:
        mesh = build(side)
        dataset_bytes = int(mesh.actual_memory_size) * 1024
        points, cells = int(mesh.n_points), int(mesh.n_cells)
        rows.append(
            {
                "points": points,
                "cells": cells,
                "dataset_bytes": dataset_bytes,
                "bytes_per_point": round(dataset_bytes / max(points, 1), 1),
            }
        )
        del mesh
    return rows


def measure_render(frames: int = 8) -> list[dict]:
    """Offscreen render cost per frame.

    **This measurement does not work, and the numbers it produces must not be used.** Two attempts
    failed in different ways. A bare `render()` returned two thousand frames a second. Forcing a
    framebuffer readback gave a frame time that barely moved between 79 thousand and 20 million
    triangles - and a direct check settled it: after changing camera azimuth and elevation, successive
    screenshots were byte-identical. Nothing was being re-rendered; the readback was returning a cached
    image.

    Measuring this properly needs an interactive loop whose frames are verified to differ, on the
    machine class the product targets. Until then LIM-002 stays open, and the function is kept here so
    the next attempt starts from the failure rather than repeating it.
    """
    return [{"invalid": "camera changes produced byte-identical frames; nothing was re-rendered"}]
    rows = []
    for side in SIZES:
        mesh = build(side)
        plotter = pv.Plotter(off_screen=True, window_size=(1280, 720))
        plotter.add_mesh(mesh, scalars="stress_MPa")
        plotter.show(auto_close=False)
        plotter.screenshot(return_img=True)  # warm up: upload geometry, compile shaders

        started = time.perf_counter()
        for index in range(frames):
            plotter.camera.azimuth = index * 7.0
            plotter.screenshot(return_img=True)
        elapsed = time.perf_counter() - started
        per_frame = elapsed / frames
        rows.append(
            {
                "triangles": int(mesh.n_cells),
                "seconds_per_frame_including_readback": round(per_frame, 4),
                "triangles_per_second": int(mesh.n_cells / per_frame) if per_frame else None,
                "triangles_at_30fps": int(mesh.n_cells / per_frame / 30) if per_frame else None,
                "renderer": describe_renderer(plotter),
            }
        )
        plotter.close()
        del mesh
    return rows


def describe_renderer(plotter: pv.Plotter) -> str:
    window = getattr(plotter, "render_window", None) or getattr(plotter, "ren_win", None)
    if window is None:
        return "unknown"
    try:
        for line in window.ReportCapabilities().splitlines():
            if "OpenGL renderer string" in line or "renderer string" in line.lower():
                return line.strip()[:140]
    except Exception:
        pass
    return "unknown"


def main() -> None:
    result = {
        "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "memory": measure_memory(),
    }
    try:
        result["render"] = measure_render()
    except Exception as error:
        result["render"] = {"failed": type(error).__name__, "message": str(error)[:300]}

    (HERE / "capacity.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
