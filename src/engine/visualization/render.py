"""Pixels from a dataset, offscreen, with every number kept off the picture (XC-257, step 3).

This is XC-087's image role for the native toolkit: the still a deliverable embeds, and the frame the
interface shows until the interactive path exists. E-191 measured that the pinned toolkit can do it
on a machine with no window; this module is what does it.

**Colours come from the display surface; numbers never do** (INV-001, INV-009). The geometry drawn is
the reduced, triangulated `DisplayGeometry`, and each of its vertices is coloured by the field value of
the dataset point it came from, through `source_points`. But the range the colours are stretched over
- the two numbers a reader takes off the legend - is computed over the **full** field, so a reduced
picture still carries the true extremes. A range read off the reduced surface would be a number that
looks right and is not.

**The legend's words are not in the picture.** E-192 measured that the toolkit's embedded faces draw a
Japanese title as nothing at all, and 単位未宣言 is exactly the word the prototype must show. So the
image carries the colour ramp and Latin tick digits only, and `LegendFacts` hands whoever shows the
image - the document, the interface - the numbers to typeset the words from, in a face that has them.

**Nothing drawn is a refusal, not a picture.** The measurement harness that preceded this (E-191)
learned to fail when it could not prove a frame was rendered; the product does the same. A frame that
contains only background is returned as an error, never as an image.

Specification: view/AC-007, AC-019, XC-087, XC-111, INV-001, INV-009, XC-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkWindowToImageFilter,
)
import vtkmodules.vtkRenderingFreeType  # noqa: F401  (tick digits on the scalar bar)
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401  (registers the OpenGL backend)

from domain_core.association import Association
from domain_core.dataset import Dataset, Field
from domain_core.mesh import DisplayGeometry
from engine.limits import MAX_INTERACTIVE_TRIANGLES
from engine.visualization.colour_maps import COLOUR_MAPS, DEFAULT_COLOUR_MAP, ColourMap
from engine.visualization.display import as_polydata, display_geometry

#: The largest image edge this renderer produces. Not yet a LIM: the offscreen buffer's ceiling has
#: not been measured, and this is a guard against a mistyped size rather than a measured limit.
MAX_IMAGE_EDGE_PIXELS = 8192

#: Where an unset camera looks from: turned and raised a little from the toolkit's default, so a
#: box is seen as a box and not as a square. A stated choice, not a measured one.
DEFAULT_AZIMUTH_DEGREES = 30.0
DEFAULT_ELEVATION_DEGREES = 20.0

#: The colour of a place with no value. Grey rather than the map's low end, because a missing value
#: drawn as the minimum is a missing value passed off as a small one (XC-001, INV-011).
MISSING_RGBA = (0.5, 0.5, 0.5, 1.0)
#: The colour of a value outside an explicit range when the view asks for one: a hue no perceptually
#: uniform map here contains, so it reads as "outside" and not as an extreme.
OUT_OF_RANGE_RGBA = (1.0, 0.0, 1.0, 1.0)

#: Significant digits on the scalar bar's tick labels. Fewer than a field's storage supports is
#: allowed - a legend is read at a glance - and the full-precision extremes travel in `LegendFacts`.
TICK_DIGITS = 4
TICK_COUNT = 5

RANGE_MODES = ("dataRange", "explicit", "symmetric")
OUT_OF_RANGE_MODES = ("clamp", "distinctColour")
PROJECTIONS = ("perspective", "orthographic")


class RenderError(Exception):
    """Raised where no honest picture can be produced. Never returned as a picture."""


@dataclass(frozen=True, slots=True)
class Colouring:
    """What the colours mean: which field, stretched over which range, through which map (CT-004)."""

    field_name: str
    association: Association
    colour_map: str = DEFAULT_COLOUR_MAP
    range_mode: str = "dataRange"
    minimum: float | None = None
    maximum: float | None = None
    out_of_range: str = "clamp"

    def __post_init__(self) -> None:
        if self.association is Association.INTEGRATION_POINT:
            raise RenderError(
                f"'{self.field_name}' は積分点の値です。頂点の色にするには要素内の分布を潰す必要があり、"
                "それは黙ってはしません（XC-123）"
            )
        if self.range_mode not in RANGE_MODES:
            raise RenderError(
                f"範囲の決め方 '{self.range_mode}' はこの版では扱いません（{list(RANGE_MODES)}）。"
                "時間全体の範囲（dataRangeOverTime）は結果軸を辿れるようになってからです"
            )
        if self.range_mode == "explicit" and (self.minimum is None or self.maximum is None):
            raise RenderError("explicit な範囲には min と max の両方が要ります")
        if self.out_of_range not in OUT_OF_RANGE_MODES:
            raise RenderError(
                f"範囲外の扱い '{self.out_of_range}' はこの版では扱いません（{list(OUT_OF_RANGE_MODES)}）。"
                "hide は範囲外の面を消すので、消えた場所が値のない場所と見分けられなくなります"
            )
        if self.colour_map not in COLOUR_MAPS:
            raise RenderError(
                f"カラーマップ '{self.colour_map}' はこの版にありません（{sorted(COLOUR_MAPS)}）"
            )


@dataclass(frozen=True, slots=True)
class Camera:
    """A camera as CT-004 stores one. Every part optional: what is unset takes the default view."""

    position_m: tuple[float, float, float] | None = None
    focal_point_m: tuple[float, float, float] | None = None
    view_up: tuple[float, float, float] | None = None
    parallel_scale_m: float | None = None
    projection: str = "perspective"

    def __post_init__(self) -> None:
        if self.projection not in PROJECTIONS:
            raise RenderError(f"投影 '{self.projection}' はありません（{list(PROJECTIONS)}）")


@dataclass(frozen=True, slots=True)
class LegendFacts:
    """The numbers the legend's words are typeset from, by whoever shows the picture (E-192)."""

    field_name: str
    unit: str | None
    minimum: float
    maximum: float
    digits: int
    colour_map: str
    uniform: bool
    range_mode: str
    missing_count: int


@dataclass(frozen=True, slots=True)
class Rendered:
    """One frame, and what a reader needs to know about it that the pixels do not say."""

    png: bytes
    width: int
    height: int
    reduced: str
    legend: LegendFacts


@dataclass(frozen=True, slots=True)
class Scene:
    """What `NativeOffscreenRenderer.draw` is handed: the datasets and how to colour and frame them."""

    datasets: tuple[Dataset, ...]
    colouring: Colouring
    camera: Camera | None = None
    background: tuple[float, float, float] = (1.0, 1.0, 1.0)
    budget: int = MAX_INTERACTIVE_TRIANGLES


def render_view(
    datasets: Sequence[Dataset],
    colouring: Colouring,
    *,
    width: int,
    height: int,
    camera: Camera | None = None,
    background: tuple[float, float, float] = (1.0, 1.0, 1.0),
    budget: int = MAX_INTERACTIVE_TRIANGLES,
    legend: bool = True,
) -> Rendered:
    """Draw the datasets coloured by one field, and say what the picture leaves out.

    `legend` is whether the colour bar is drawn **inside** the picture. A document needs it there,
    because a document has nowhere else (XC-254). A screen has a legend beside the picture that can
    carry the unit, which the bar cannot (E-192), and drawing both is two scales for one image.
    """
    if not datasets:
        raise RenderError("描くデータセットがありません")
    for edge, name in ((width, "width"), (height, "height")):
        if not 1 <= edge <= MAX_IMAGE_EDGE_PIXELS:
            raise RenderError(f"{name}={edge} は 1 以上 {MAX_IMAGE_EDGE_PIXELS} 以下で指定してください")
    fields = [_field_of(dataset, colouring) for dataset in datasets]
    low, high = resolve_range(fields, colouring)
    colour_map = COLOUR_MAPS[colouring.colour_map]
    table = _lookup_table(colour_map, low, high, colouring.out_of_range)

    renderer = vtkRenderer()
    renderer.SetBackground(*background)
    geometries: list[DisplayGeometry] = []
    for dataset, field in zip(datasets, fields):
        geometry = display_geometry(dataset, budget=budget)
        geometries.append(geometry)
        renderer.AddActor(_actor(geometry, field, table, low, high))
    if legend:
        renderer.AddViewProp(_scalar_bar(table, background))

    renderer.ResetCamera()
    _aim(renderer, camera)

    window = vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.AddRenderer(renderer)
    window.SetSize(width, height)
    window.Render()

    to_image = vtkWindowToImageFilter()
    to_image.SetInput(window)
    to_image.ReadFrontBufferOff()
    to_image.Update()
    frame = to_image.GetOutput()
    _refuse_an_empty_frame(frame, background)

    writer = vtkPNGWriter()
    writer.WriteToMemoryOn()
    writer.SetInputData(frame)
    writer.Write()
    png = bytes(vtk_to_numpy(writer.GetResult()))

    plans = [geometry.reduction for geometry in geometries if geometry.reduction is not None]
    reduced = "；".join(dict.fromkeys(plan.describe() for plan in plans)) or "全三角形を表示しています"
    return Rendered(
        png=png,
        width=width,
        height=height,
        reduced=reduced,
        legend=LegendFacts(
            field_name=colouring.field_name,
            unit=fields[0].unit,
            minimum=low,
            maximum=high,
            digits=min(field.significant_digits for field in fields),
            colour_map=colour_map.id,
            uniform=colour_map.uniform,
            range_mode=colouring.range_mode,
            missing_count=int(sum(np.count_nonzero(np.isnan(field.values)) for field in fields)),
        ),
    )


def resolve_range(fields: Sequence[Field], colouring: Colouring) -> tuple[float, float]:
    """The two numbers the colours are stretched between, from the **full** field (INV-001).

    `explicit` takes the numbers the view states. `dataRange` and `symmetric` take them from every
    value the dataset holds, missing ones excluded - never from the reduced display surface, whose
    extremes are the extremes of a subset.
    """
    if colouring.range_mode == "explicit":
        assert colouring.minimum is not None and colouring.maximum is not None
        if colouring.minimum > colouring.maximum:
            raise RenderError(f"範囲の min ({colouring.minimum}) が max ({colouring.maximum}) より大きい")
        return float(colouring.minimum), float(colouring.maximum)
    values = np.concatenate([np.asarray(field.values, dtype=np.float64) for field in fields])
    present = values[np.isfinite(values)]
    if present.size == 0:
        raise RenderError(f"'{colouring.field_name}' に値がありません。色の範囲を決められません")
    low, high = float(present.min()), float(present.max())
    if colouring.range_mode == "symmetric":
        span = max(abs(low), abs(high))
        return -span, span
    return low, high


def _field_of(dataset: Dataset, colouring: Colouring) -> Field:
    field = dataset.fields.get(colouring.field_name)
    if field is None:
        raise RenderError(
            f"'{colouring.field_name}' というフィールドはありません（{sorted(dataset.fields)}）"
        )
    if field.association is not colouring.association:
        raise RenderError(
            f"'{colouring.field_name}' は {field.association.value} データで、"
            f"ビューは {colouring.association.value} として着色しようとしています。"
            "変換は値を変えるので、頼まれずにはしません（INV-003）"
        )
    return field


def _lookup_table(colour_map: ColourMap, low: float, high: float, out_of_range: str) -> vtkLookupTable:
    table = vtkLookupTable()
    samples = colour_map.rgb()
    table.SetNumberOfTableValues(len(samples))
    for index, (red, green, blue) in enumerate(samples):
        table.SetTableValue(index, red, green, blue, 1.0)
    table.SetRange(low, high)
    table.SetNanColor(*MISSING_RGBA)
    if out_of_range == "distinctColour":
        table.SetBelowRangeColor(*OUT_OF_RANGE_RGBA)
        table.SetAboveRangeColor(*OUT_OF_RANGE_RGBA)
        table.UseBelowRangeColorOn()
        table.UseAboveRangeColorOn()
    table.Build()
    return table


def _actor(geometry: DisplayGeometry, field: Field, table: vtkLookupTable, low: float, high: float) -> vtkActor:
    surface = as_polydata(geometry)
    values = np.asarray(field.values)
    if field.association is Association.POINT:
        # The value of the dataset point each display vertex came from - never the value at the
        # display index, which after surface extraction names a different place (E-132).
        colours = values[geometry.source_points]
        target = surface.GetPointData()
    else:
        # A decimated triangle that spans a cell boundary belongs to no cell (-1) and is drawn as
        # missing rather than as one of the cells it partly covers.
        colours = np.where(geometry.source_cells >= 0, values[np.maximum(geometry.source_cells, 0)], np.nan)
        target = surface.GetCellData()
    scalars = numpy_to_vtk(np.ascontiguousarray(colours, dtype=np.float64), deep=True)
    scalars.SetName(field.name)
    target.SetScalars(scalars)

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(surface)
    mapper.SetLookupTable(table)
    mapper.SetScalarRange(low, high)
    mapper.SetColorModeToMapScalars()
    mapper.UseLookupTableScalarRangeOn()
    if field.association is Association.POINT:
        mapper.SetScalarModeToUsePointData()
    else:
        mapper.SetScalarModeToUseCellData()
    actor = vtkActor()
    actor.SetMapper(mapper)
    return actor


def _scalar_bar(table: vtkLookupTable, background: tuple[float, float, float]) -> vtkScalarBarActor:
    """The colour ramp with tick digits, and no title: the words are typeset elsewhere (E-192).

    The digits are dark on a light background and light on a dark one, decided from the
    background's luminance rather than left at the toolkit's white-with-a-shadow default, which on a
    white page is legible only by its shadow.
    """
    bar = vtkScalarBarActor()
    bar.SetLookupTable(table)
    bar.SetTitle("")
    bar.SetNumberOfLabels(TICK_COUNT)
    bar.SetLabelFormat(f"%.{TICK_DIGITS}g")
    bar.DrawTickLabelsOn()
    labels = bar.GetLabelTextProperty()
    labels.SetColor(*_ink_for(background))
    labels.ItalicOff()
    labels.ShadowOff()
    labels.BoldOff()
    return bar


def _ink_for(background: tuple[float, float, float]) -> tuple[float, float, float]:
    """Near-black on a light background, near-white on a dark one, by relative luminance."""
    red, green, blue = background
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return (0.1, 0.1, 0.1) if luminance > 0.5 else (0.95, 0.95, 0.95)


def _aim(renderer: vtkRenderer, camera: Camera | None) -> None:
    active = renderer.GetActiveCamera()
    if camera is None or (camera.position_m is None and camera.focal_point_m is None):
        active.Azimuth(DEFAULT_AZIMUTH_DEGREES)
        active.Elevation(DEFAULT_ELEVATION_DEGREES)
        active.OrthogonalizeViewUp()
        renderer.ResetCamera()
    if camera is None:
        return
    if camera.position_m is not None:
        active.SetPosition(*camera.position_m)
    if camera.focal_point_m is not None:
        active.SetFocalPoint(*camera.focal_point_m)
    if camera.view_up is not None:
        active.SetViewUp(*camera.view_up)
    if camera.projection == "orthographic":
        active.ParallelProjectionOn()
        if camera.parallel_scale_m is not None:
            active.SetParallelScale(camera.parallel_scale_m)
    renderer.ResetCameraClippingRange()


def _refuse_an_empty_frame(frame: object, background: tuple[float, float, float]) -> None:
    """A frame that is all background is not a picture of anything, and is not returned as one."""
    pixels = vtk_to_numpy(frame.GetPointData().GetScalars())  # type: ignore[attr-defined]
    expected = np.array([round(channel * 255) for channel in background], dtype=pixels.dtype)
    drawn = np.any(pixels[:, :3] != expected, axis=1)
    if not bool(drawn.any()):
        raise RenderError(
            "何も描かれませんでした：フレームが背景色だけです。"
            "空の絵を成果物にするより、描けなかったと言います"
        )


#: What the probe runs in a process of its own: the smallest render there is. It is a separate
#: process because on a machine with no display the toolkit does not refuse - it **segfaults** in
#: `Render()` (E-194, measured on a GitHub runner), and a segfault in the engine process takes the
#: engine down with it (XC-045's reason for isolating the readers, now the renderer's too).
_PROBE_SCRIPT = """
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow
window = vtkRenderWindow()
window.SetOffScreenRendering(1)
window.AddRenderer(vtkRenderer())
window.SetSize(8, 8)
window.Render()
print(window.ReportCapabilities().splitlines()[0] if window.ReportCapabilities() else "rendered")
"""

PROBE_TIMEOUT_SECONDS = 30


def probe_offscreen(timeout_seconds: int = PROBE_TIMEOUT_SECONDS) -> tuple[bool, str]:
    """Whether this machine can render offscreen, found by trying it where a crash cannot hurt.

    An import proves the module is present, not that a context exists; only a render proves that,
    and a failed render may not return. So the attempt runs in a child process, and its exit status
    is the answer: (True, the OpenGL vendor line) or (False, what happened).
    """
    import subprocess
    import sys

    try:
        completed = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return False, f"オフスクリーン描画の確認が {timeout_seconds} 秒で終わりませんでした"
    except OSError as error:
        return False, f"確認用のプロセスを起動できません：{error}"
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        last = detail[-1] if detail else f"終了コード {completed.returncode}"
        return False, (
            f"この機械ではオフスクリーン描画ができません（確認プロセスが終了コード {completed.returncode}："
            f"{last[:160]}）。ディスプレイか、ディスプレイ無しで動く OpenGL が要ります"
        )
    return True, (completed.stdout.strip().splitlines() or ["rendered"])[-1][:160]


@dataclass(frozen=True, slots=True)
class PickedRay:
    """Where a pixel points, in the frame the geometry lives in."""

    near_m: tuple[float, float, float]
    far_m: tuple[float, float, float]


def ray_through(
    datasets: Sequence[Dataset],
    pixel: tuple[int, int],
    *,
    width: int,
    height: int,
    camera: Camera | None = None,
) -> PickedRay:
    """The line into the scene through one pixel of a frame drawn at this size.

    **The camera is the engine's, so the unprojection is the engine's.** An interface has a pixel a
    person clicked and nothing that turns it into a point of the model; doing the arithmetic there
    would need the projection the picture was drawn with, which the interface never saw. So the same
    scene is set up the same way - the same bounds, the same reset, the same default turn - and the
    toolkit is asked where that pixel points.

    Nothing is rendered: a ray needs the camera, not the pixels, and drawing a frame to throw it away
    would make a pick cost what a render costs.
    """
    if not 0 <= pixel[0] < width or not 0 <= pixel[1] < height:
        raise RenderError(f"画素 {pixel} は {width}x{height} の絵の外です")
    renderer = vtkRenderer()
    for dataset in datasets:
        renderer.AddActor(_plain_actor(display_geometry(dataset)))
    renderer.ResetCamera()
    _aim(renderer, camera)
    # The toolkit measures y from the bottom and every interface from the top.
    display_y = height - 1 - pixel[1]
    renderer.SetViewport(0.0, 0.0, 1.0, 1.0)
    window = vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.AddRenderer(renderer)
    window.SetSize(width, height)
    renderer.SetDisplayPoint(float(pixel[0]), float(display_y), 0.0)
    renderer.DisplayToWorld()
    near = renderer.GetWorldPoint()
    renderer.SetDisplayPoint(float(pixel[0]), float(display_y), 1.0)
    renderer.DisplayToWorld()
    far = renderer.GetWorldPoint()
    return PickedRay(near_m=_homogeneous(near), far_m=_homogeneous(far))


def _homogeneous(point: Sequence[float]) -> tuple[float, float, float]:
    """A toolkit world point, divided through by its fourth component."""
    w = point[3] if len(point) > 3 and point[3] != 0.0 else 1.0
    return (point[0] / w, point[1] / w, point[2] / w)


def _plain_actor(geometry: DisplayGeometry) -> vtkActor:
    """The surface with no colours: a ray needs where the geometry is, not what it means."""
    mapper = vtkPolyDataMapper()
    mapper.SetInputData(as_polydata(geometry))
    actor = vtkActor()
    actor.SetMapper(mapper)
    return actor


class NativeOffscreenRenderer:
    """XC-087's native path, in the shape `backends.Renderer` names."""

    def capabilities(self) -> frozenset[str]:
        return frozenset({"offscreen", "png", "scalarBar", "surface"})

    def draw(self, scene: object, width: int, height: int) -> bytes:
        if not isinstance(scene, Scene):
            raise RenderError(f"このレンダラは Scene を描きます（{type(scene).__name__} が渡されました）")
        return render_view(
            scene.datasets, scene.colouring, width=width, height=height,
            camera=scene.camera, background=scene.background, budget=scene.budget,
        ).png
