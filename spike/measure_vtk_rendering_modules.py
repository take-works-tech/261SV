"""What the published VTK wheel can actually draw with, enumerated rather than assumed.

XC-034 ships the published wheel and lists two reasons to build from source later: size (LIM-004) and
disabling readers with open advisories (XC-047). This measures a third, which nothing had checked: what
rendering back ends the wheel contains at all.

It matters because both candidate photorealistic paths are unavailable for different reasons - Omniverse
by licence (XC-250), ray tracing through VTK by absence - and "absence" is a claim that has to be
measured on the pinned build rather than read from VTK's documentation, which describes what VTK *can*
be built with.

Run in a prepared spike environment (`pip install vtk==9.5.2`). Writes `vtk_rendering_modules.json`.
"""

from __future__ import annotations

import json
import pkgutil
from pathlib import Path

import vtkmodules

#: The back ends worth asking about, and what each would be for.
WANTED = {
    "OSPRay": "Intel の CPU レイトレーサ経由の描画（ParaView のレイトレース描画はこれ）",
    "RayTracing": "VTK のレイトレーシング一式",
    "Anari": "ANARI 経由での任意のレイトレーサ接続",
    "OptiX": "NVIDIA GPU レイトレーシング",
    "OpenVKL": "ボリュームカーネル",
    "Embree": "レイトレーシングカーネル",
}


def main() -> None:
    names = sorted(module.name for module in pkgutil.iter_modules(vtkmodules.__path__))
    rendering = [name for name in names if name.startswith("vtkRendering")]
    found = {
        pattern: [name for name in names if pattern.lower() in name.lower()]
        for pattern in WANTED
    }

    measured = {
        "vtk_version": vtkmodules.__file__ and _version(),
        "module_count": len(names),
        "rendering_modules": rendering,
        "looked_for": {pattern: found[pattern] for pattern in WANTED},
        "any_ray_tracing": any(found[pattern] for pattern in WANTED),
    }
    Path(__file__).with_name("vtk_rendering_modules.json").write_text(
        json.dumps(measured, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"modules: {len(names)}, rendering: {len(rendering)}")
    for pattern, hits in found.items():
        print(f"  {pattern:12} {hits if hits else 'absent'}")
    print(f"any ray-tracing back end present: {measured['any_ray_tracing']}")


def _version() -> str:
    from vtkmodules.vtkCommonCore import vtkVersion

    return vtkVersion.GetVTKVersion()


if __name__ == "__main__":
    main()
