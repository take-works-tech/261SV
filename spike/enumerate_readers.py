"""Enumerate what the shipped VTK build can open and compute.

The specification stages format support, and staging is only honest if the stages are drawn around
what actually exists. This enumerates the reader and filter classes present in the installed wheel -
first-hand, on the build the product would ship - rather than reasoning from documentation.

Run:  .venv-spike/Scripts/python spike/enumerate_readers.py
Writes: spike/readers.json
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import vtkmodules.all as vtk_all

HERE = Path(__file__).resolve().parent

CAE_KEYS = (
    "CGNS", "EnSight", "OpenFOAM", "FLUENT", "Exodus", "LSDyna", "Tecplot", "Plot3D",
    "IOSS", "CONVERGE", "GAMBIT", "MFIX", "SLAC", "NetCDF", "HDF", "Xdmf", "H5",
)
# Some readers live outside vtkmodules.all and would be missed by a naive scan.
EXTRA_MODULES = ("vtkmodules.vtkIOCGNSReader",)

FILTER_FAMILIES = (
    "Contour", "Clip", "Cut", "Threshold", "Glyph", "StreamTracer", "Calculator",
    "IntegrateAttributes", "ProbeFilter", "ResampleWithDataSet", "WarpVector", "WarpScalar",
    "ExtractEdges", "Decimate", "GradientFilter", "CellDataToPointData", "PointDataToCellData",
    "ArrayCalculator", "TemporalStatistics", "DescriptiveStatistics", "MergeBlocks",
    "ConnectivityFilter",
)


def main() -> None:
    names = set(dir(vtk_all))
    for module_name in EXTRA_MODULES:
        try:
            names.update(dir(importlib.import_module(module_name)))
        except ImportError:
            pass

    readers = sorted(n for n in names if n.startswith("vtk") and n.endswith("Reader"))
    writers = sorted(n for n in names if n.startswith("vtk") and n.endswith("Writer"))
    cae_readers = sorted(n for n in readers if any(key in n for key in CAE_KEYS))
    filters_present = sorted(f for f in FILTER_FAMILIES if any(f in n for n in names))

    result = {
        "vtk_version": vtk_all.vtkVersion.GetVTKVersion(),
        "reader_classes": len(readers),
        "writer_classes": len(writers),
        "cae_readers": cae_readers,
        "filter_families_present": filters_present,
        "filter_families_absent": [f for f in FILTER_FAMILIES if f not in filters_present],
        "all_readers": readers,
    }
    (HERE / "readers.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"{len(readers)} readers, {len(cae_readers)} CAE-relevant, {len(writers)} writers, "
        f"{len(filters_present)}/{len(FILTER_FAMILIES)} filter families"
    )


if __name__ == "__main__":
    main()
