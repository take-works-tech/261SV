"""Walking-skeleton measurement for the claim the product is built on.

The spec bets on a self-contained deliverable: geometry, numbers with units, and annotations in one
file a recipient opens with nothing installed. An independent check measured the free path at about
48 MB and 19 s for a million-point surface, and found that text actors and 2D props are dropped
silently. This script reproduces those numbers here, on this machine, and measures the floor: how many
bytes the geometry itself costs once compressed, which is what any viewer must carry.

Run:  .venv-spike/Scripts/python spike/measure_export.py
Writes: spike/results.json and the artefacts it measured, so the numbers can be re-checked.
"""

from __future__ import annotations

import base64
import gzip
import json
import time
from pathlib import Path

import numpy as np
import pyvista as pv
import vtk

HERE = Path(__file__).resolve().parent
OUT = HERE / "artifacts"
OUT.mkdir(exist_ok=True)

# A surface of about 1.1 million points, the scale the independent measurement used, so the two
# numbers are comparable. Real CAE meshes are unstructured; a structured grid understates the index
# cost, so the floor computed here is a lower bound, and that is stated in the result.
POINTS_TARGET = 1_128_448
SIDE = int(POINTS_TARGET**0.5)  # 1062 x 1062 = 1_127_844 points

ANNOTATION = "PEAK_STRESS_MARKER_431"


def build_surface() -> pv.PolyData:
    x = np.linspace(-1.0, 1.0, SIDE, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, SIDE, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    zz = (0.25 * np.sin(6.0 * xx) * np.cos(6.0 * yy)).astype(np.float32)
    grid = pv.StructuredGrid(xx, yy, zz)
    field = (np.hypot(xx, yy) * 120.0).astype(np.float32).ravel(order="F")
    grid["stress_MPa"] = field
    return grid.extract_surface().triangulate()


def measure_free_path(mesh: pv.PolyData) -> dict:
    """The path a user gets today: PyVista's one-line HTML export, with an annotation and a scale bar."""
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh, scalars="stress_MPa", show_scalar_bar=True)
    plotter.add_text(ANNOTATION, position="upper_left", font_size=12)
    plotter.add_point_labels(
        np.array([[0.0, 0.0, 0.5]]), [ANNOTATION], point_size=10, font_size=12
    )

    target = OUT / "free_path.html"
    started = time.perf_counter()
    plotter.export_html(str(target))
    elapsed = time.perf_counter() - started
    plotter.close()

    body = target.read_bytes()
    return {
        "artifact": target.name,
        "bytes": len(body),
        "seconds": round(elapsed, 2),
        "annotation_survives": ANNOTATION.encode() in body,
        "scalar_bar_present": b"ScalarBar" in body or b"vtkScalarBarActor" in body,
    }


def measure_geometry_floor(mesh: pv.PolyData) -> dict:
    """What any self-contained viewer must carry: positions, indices and one field, compressed."""
    points = np.asarray(mesh.points, dtype=np.float32)
    faces = mesh.faces.reshape(-1, 4)[:, 1:].astype(np.uint32)
    field = np.asarray(mesh["stress_MPa"], dtype=np.float32)

    raw = points.tobytes() + faces.tobytes() + field.tobytes()
    started = time.perf_counter()
    packed = gzip.compress(raw, compresslevel=6)
    encoded = base64.b64encode(packed)
    elapsed = time.perf_counter() - started

    (OUT / "geometry_floor.bin.gz").write_bytes(packed)
    return {
        "points": int(points.shape[0]),
        "triangles": int(faces.shape[0]),
        "raw_bytes": len(raw),
        "gzip_bytes": len(packed),
        "base64_bytes": len(encoded),
        "seconds": round(elapsed, 2),
    }


def measure_decimated(mesh: pv.PolyData, fraction: float) -> dict:
    """The reduced representation the spec promises to mark as reduced (ingest/AC-030)."""
    started = time.perf_counter()
    reduced = mesh.decimate_pro(1.0 - fraction, preserve_topology=True)
    elapsed = time.perf_counter() - started
    points = np.asarray(reduced.points, dtype=np.float32)
    faces = reduced.faces.reshape(-1, 4)[:, 1:].astype(np.uint32)
    packed = gzip.compress(points.tobytes() + faces.tobytes(), compresslevel=6)
    return {
        "kept_fraction": fraction,
        "points": int(points.shape[0]),
        "gzip_bytes": len(packed),
        "seconds": round(elapsed, 2),
    }


def inspect_vtk_build() -> dict:
    """Which libraries the shipped wheel actually contains - the gl2ps question, checked locally."""
    root = Path(vtk.__file__).resolve().parent
    names = sorted(p.name for p in root.rglob("*") if p.is_file() and p.suffix in (".dll", ".so", ".pyd"))
    interesting = {
        key: [n for n in names if key.lower() in n.lower()]
        for key in ("gl2ps", "freetype", "jpeg", "hdf5", "proj", "eigen", "scn")
    }
    return {
        "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "library_count": len(names),
        "wheel_bytes": sum(p.stat().st_size for p in root.rglob("*") if p.is_file()),
        "found": {k: v for k, v in interesting.items() if v},
    }


def main() -> None:
    print("building surface ...")
    mesh = build_surface()
    print(f"  {mesh.n_points:,} points, {mesh.n_cells:,} cells")

    results = {
        "measured_on": "local workstation, Windows",
        "mesh": {"points": int(mesh.n_points), "cells": int(mesh.n_cells)},
        "vtk_build": inspect_vtk_build(),
    }

    print("measuring the geometry floor ...")
    results["geometry_floor"] = measure_geometry_floor(mesh)

    print("measuring the free export path ...")
    try:
        results["free_path"] = measure_free_path(mesh)
    except Exception as error:  # the failure itself is a result worth recording
        results["free_path"] = {"failed": type(error).__name__, "message": str(error)[:400]}

    print("measuring a reduced representation ...")
    results["decimated_10pct"] = measure_decimated(mesh, 0.10)

    (HERE / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
