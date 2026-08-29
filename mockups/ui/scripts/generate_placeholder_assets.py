"""Generate every image the mockup catalogue references, so provenance is this script.

Run: python mockups/ui/scripts/generate_placeholder_assets.py

The originals had no recorded origin, and an asset whose terms cannot be stated cannot ship or be
published (XC-053b applies the same test to samples). These replacements are drawn here, from
nothing but arithmetic: material swatches as shaded gradients, part thumbnails as monochrome
wireframe silhouettes. Deliberately illustrative - a mockup asset that looked like a rendering
would be a mockup pretending to be evidence.

Pillow is not a project dependency; the script writes PNGs by hand (zlib + struct), so it runs
anywhere Python runs.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"


def write_png(path: Path, width: int, height: int, pixel) -> None:
    # RGBA (colour type 6): tests/test_ui_mockup_catalog.py pins the material swatches to it.
    raw = b"".join(
        b"\x00" + b"".join(bytes((*pixel(x, y), 255)) for x in range(width))
        for y in range(height)
    )
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def clamp(v: float) -> int:
    return max(0, min(255, int(v)))


def sphere_shade(x: int, y: int, size: int, base: tuple[int, int, int], gloss: float) -> tuple[int, int, int]:
    """A lit sphere on a dark ground - enough to read as a material, honest as a drawing."""
    cx = cy = size / 2
    r = size * 0.42
    dx, dy = (x - cx) / r, (y - cy) / r
    d2 = dx * dx + dy * dy
    if d2 > 1.0:
        g = 26 + (y / size) * 6
        return (clamp(g), clamp(g + 1), clamp(g + 2))
    nz = (1.0 - d2) ** 0.5
    light = max(0.0, (-0.5 * dx - 0.6 * dy + 0.62 * nz))
    spec = max(0.0, (-0.35 * dx - 0.5 * dy + 0.79 * nz)) ** 24
    return tuple(clamp(c * (0.25 + 0.75 * light) + 255 * gloss * spec) for c in base)


MATERIALS = {
    # Greys and restrained hues: a swatch is data-adjacent, and these read as materials, not brands.
    "neutral-gray.png": ((150, 152, 154), 0.25),
    "brushed-steel.png": ((166, 170, 174), 0.55),
    "technical-blue.png": ((96, 130, 168), 0.35),
    "inspection-orange.png": ((196, 138, 78), 0.35),
    "translucent-cyan.png": ((118, 168, 176), 0.6),
    "result-sample.png": None,  # handled below: a colour-mapped sphere, because it depicts a result
}

VIRIDIS = [(68, 1, 84), (65, 68, 135), (42, 120, 142), (34, 168, 132), (122, 209, 81), (253, 231, 37)]


def viridis(t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t)) * (len(VIRIDIS) - 1)
    i = min(int(t), len(VIRIDIS) - 2)
    f = t - i
    a, b = VIRIDIS[i], VIRIDIS[i + 1]
    return tuple(clamp(a[k] + (b[k] - a[k]) * f) for k in range(3))


def thumbnail(path: Path, seed: int) -> None:
    """A part silhouette as pale strokes on the panel ground - a sketch, visibly not a photo."""
    size = 96
    import random
    rng = random.Random(seed)
    points = [(rng.uniform(0.18, 0.82) * size, rng.uniform(0.2, 0.8) * size) for _ in range(6)]
    points.sort()
    def near_edge(x: int, y: int) -> bool:
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            span2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
            if span2 == 0:
                continue
            t = max(0.0, min(1.0, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / span2))
            px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
            if (x - px) ** 2 + (y - py) ** 2 < 1.6:
                return True
        return False
    def pixel(x: int, y: int) -> tuple[int, int, int]:
        if near_edge(x, y):
            return (138, 148, 154)
        g = 24 + (y / size) * 6
        return (clamp(g), clamp(g + 1), clamp(g + 2))
    write_png(path, size, size, pixel)


def main() -> None:
    # 512 for material swatches: tests/test_ui_mockup_catalog.py pins that size, because the shelf
    # renders them at retina densities. Part thumbnails stay small - they are sketches.
    size = 512
    for name, spec in MATERIALS.items():
        target = PUBLIC / "materials" / name
        if spec is None:
            def pixel(x: int, y: int) -> tuple[int, int, int]:
                cx = cy = size / 2
                r = size * 0.42
                dx, dy = (x - cx) / r, (y - cy) / r
                d2 = dx * dx + dy * dy
                if d2 > 1.0:
                    g = 26 + (y / size) * 6
                    return (clamp(g), clamp(g + 1), clamp(g + 2))
                return viridis(1.0 - (y / size) - 0.15 * dx)
            write_png(target, size, size, pixel)
        else:
            base, gloss = spec
            write_png(target, size, size, lambda x, y, b=base, g=gloss: sphere_shade(x, y, size, b, g))
        print(f"wrote {target.relative_to(PUBLIC.parent)}")
    for index, name in enumerate(
        ["bracket-1.png", "bracket-2.png", "housing.png", "manifold-1.png", "manifold-2.png", "wing.png"]
    ):
        target = PUBLIC / "thumbnails" / name
        thumbnail(target, seed=index + 7)
        print(f"wrote {target.relative_to(PUBLIC.parent)}")


if __name__ == "__main__":
    main()
