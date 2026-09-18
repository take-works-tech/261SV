"""Measure whether the native scalar bar can carry Japanese text, and what happens when it cannot.

XC-257's prototype needs a legend that says which unit the colours are in - or that none was
declared, which in this product's own language is 単位未宣言. The offscreen renderer of E-191 draws
the bar; this asks whether it draws the words. The toolkit ships embedded Latin faces only, so the
question is not academic, and the answer matters more than a missing glyph usually does: a legend
title that is silently absent is a picture that looks finished and says less than it claims.

Three renders of the same bar: a Latin title, a Japanese title with the embedded face, and the same
Japanese title with a font file when one is found on this machine. Each is compared by hash with a
bar carrying no title at all, so "the words were dropped" is measured rather than eyeballed.

Run:  python spike/measure_legend_text.py
Writes: spike/legend_text.json
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path

from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkLookupTable, vtkVersion
from vtkmodules.vtkIOImage import vtkPNGReader, vtkPNGWriter
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow, vtkWindowToImageFilter
import vtkmodules.vtkRenderingFreeType  # noqa: F401
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401

HERE = Path(__file__).resolve().parent
SIZE = (400, 300)
VTK_FONT_FILE = 4  # vtkTextProperty's font-family value for "read this file"
JAPANESE_TITLE = "応力 単位未宣言"
#: Font files a Windows machine commonly carries. The first that exists is used; none is shipped.
CANDIDATE_FONT_FILES = (
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
)


def render(title: str, font_file: str | None = None) -> bytes:
    table = vtkLookupTable()
    table.SetRange(0.0, 50.0)
    table.Build()
    bar = vtkScalarBarActor()
    bar.SetLookupTable(table)
    bar.SetTitle(title)
    bar.SetNumberOfLabels(3)
    if font_file is not None:
        for text in (bar.GetTitleTextProperty(), bar.GetLabelTextProperty()):
            text.SetFontFamily(VTK_FONT_FILE)
            text.SetFontFile(font_file)
    renderer = vtkRenderer()
    renderer.AddViewProp(bar)
    renderer.SetBackground(0.1, 0.1, 0.1)
    window = vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.AddRenderer(renderer)
    window.SetSize(*SIZE)
    window.Render()
    to_image = vtkWindowToImageFilter()
    to_image.SetInput(window)
    to_image.Update()
    writer = vtkPNGWriter()
    writer.WriteToMemoryOn()
    writer.SetInputConnection(to_image.GetOutputPort())
    writer.Write()
    return bytes(vtk_to_numpy(writer.GetResult()))


def digest(image: bytes) -> str:
    return hashlib.sha256(image).hexdigest()


def text_pixels(image: bytes) -> int:
    """How many near-white pixels the frame holds - the text, and nothing else in this scene.

    The first version of this compared frame hashes, and a title that rendered **no glyphs at all**
    still changed the hash, because the bar is laid out shorter to leave room for a title. A hash
    says "something differed"; only counting the pixels the words occupy says "the words are there".
    """
    reader = vtkPNGReader()
    reader.SetMemoryBufferLength(len(image))
    reader.SetMemoryBuffer(image)
    reader.Update()
    pixels = vtk_to_numpy(reader.GetOutput().GetPointData().GetScalars())
    return int((pixels[:, :3].min(axis=1) > 200).sum())


def main() -> int:
    started = time.perf_counter()
    untitled = render("")
    latin = render("stress [MPa]")
    japanese_embedded = render(JAPANESE_TITLE)
    font_file = next((one for one in CANDIDATE_FONT_FILES if Path(one).exists()), None)
    japanese_file = render(JAPANESE_TITLE, font_file) if font_file else None

    # The baseline is an untitled bar drawn with the **same** font setting: a font file changes the
    # tick digits too, so an untitled bar in the embedded face is the wrong yardstick for it - the
    # second version of this counted fewer text pixels with the file than without and read that as
    # "not drawn", when the title was plainly there and the digits had merely become thinner.
    baseline = text_pixels(untitled)
    baseline_file = text_pixels(render("", font_file)) if font_file else None
    counts = {
        "untitled": baseline,
        "latin": text_pixels(latin),
        "japanese_embedded": text_pixels(japanese_embedded),
        "untitled_font_file": baseline_file,
        "japanese_font_file": text_pixels(japanese_file) if japanese_file is not None else None,
    }
    record = {
        "measured": time.strftime("%Y-%m-%d"),
        "vtk_version": vtkVersion.GetVTKVersion(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "title": JAPANESE_TITLE,
        "criterion": "near-white pixels beyond those of an untitled bar; a hash difference alone was not enough",
        "text_pixels": counts,
        "latin_title_drawn": counts["latin"] > baseline,
        "japanese_title_drawn_with_embedded_font": counts["japanese_embedded"] > baseline,
        "font_file_found": font_file,
        "japanese_title_drawn_with_font_file": (
            counts["japanese_font_file"] > baseline_file if japanese_file is not None else None
        ),
        "frames_differ_by_hash": {
            "japanese_embedded_vs_untitled": digest(japanese_embedded) != digest(untitled),
        },
        "seconds_total": round(time.perf_counter() - started, 3),
    }
    (HERE / "legend_text.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    artifacts = HERE / "artifacts"
    artifacts.mkdir(exist_ok=True)
    (artifacts / "legend_japanese_embedded.png").write_bytes(japanese_embedded)
    if japanese_file is not None:
        (artifacts / "legend_japanese_font_file.png").write_bytes(japanese_file)
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
