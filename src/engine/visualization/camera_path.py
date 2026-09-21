"""A camera path: where a picture is looked at from, along a parameter (XC-289, 16_application_model §7).

A @Timeline answers *when* and carries no camera (XC-200); a camera path answers *from where*, as
keyframes of camera pose against a parameter from 0 to 1, with an interpolation rule that is part of
the definition and travels with every frame drawn from it - a frame between two keyframes is a
computed pose, and a computed number carries its formula (INV-020). Two rules exist and are named:
**linear** draws straight between the keyframes around the parameter, and **smooth** draws a uniform
Catmull-Rom curve through the keyframes for the position and the focal point. The view-up is
interpolated straight and normalised; the parallel scale straight; the projection is one for the whole
path, because a picture cannot be half orthographic.

What is refused, by name: a path with fewer than two keyframes, keyframes out of order or repeated,
a keyframe whose camera leaves position, focal point or view-up unset (a default pose cannot be
interpolated), a parameter outside the keyframes' range - nothing is clamped to the nearest end - and
keyframes disagreeing on the projection.

Specification: view/REQ-015, 16_application_model §7 (`timeline`), XC-200, XC-289.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np

from engine.visualization.render import Camera

INTERPOLATIONS = ("linear", "smooth")

RULE = {
    "linear": "位置・注視点・上方向（正規化）・平行投影の幅を、媒介変数を挟む 2 つのキーフレームの間で直線補間",
    "smooth": "位置と注視点はキーフレームを通る一様 Catmull-Rom 曲線、上方向（正規化）と平行投影の幅は直線補間",
}


class CameraPathError(Exception):
    """Raised where a path or a position on it cannot be honoured as stated."""


@dataclass(frozen=True, slots=True)
class Keyframe:
    at: float
    camera: Camera


@dataclass(frozen=True, slots=True)
class CameraPath:
    """A named path of keyframes on a parameter from 0 to 1, with its interpolation rule."""

    id: str
    name: str
    keyframes: tuple[Keyframe, ...]
    interpolation: str = "linear"

    def __post_init__(self) -> None:
        if self.interpolation not in INTERPOLATIONS:
            raise CameraPathError(f"補間 '{self.interpolation}' はありません（{list(INTERPOLATIONS)}）")
        if len(self.keyframes) < 2:
            raise CameraPathError(
                f"カメラパス '{self.name}' のキーフレームは {len(self.keyframes)} 件です。"
                "経路には 2 件以上が要ります（1 件では動画も途中の姿勢も作れません）"
            )
        for index, frame in enumerate(self.keyframes):
            if not 0.0 <= frame.at <= 1.0:
                raise CameraPathError(f"キーフレーム {index} の媒介変数 {frame.at!r} は 0〜1 の外です")
            if frame.camera.position_m is None or frame.camera.focal_point_m is None or frame.camera.view_up is None:
                raise CameraPathError(
                    f"キーフレーム {index} のカメラに位置・注視点・上方向のどれかがありません。"
                    "既定の向きは補間できないので、三つとも書いてください"
                )
            if frame.camera.projection == "orthographic" and frame.camera.parallel_scale_m is None:
                raise CameraPathError(f"キーフレーム {index} は平行投影ですが parallelScale_m がありません")
        parameters = [frame.at for frame in self.keyframes]
        if any(later <= earlier for earlier, later in zip(parameters, parameters[1:])):
            raise CameraPathError(
                f"キーフレームの媒介変数は昇順で重複なしです（{parameters}）。並べ替えは推測になるので行いません"
            )
        projections = {frame.camera.projection for frame in self.keyframes}
        if len(projections) > 1:
            raise CameraPathError(f"キーフレームの投影が揃っていません（{sorted(projections)}）。絵は途中で投影を変えられません")

    @property
    def first(self) -> float:
        return self.keyframes[0].at

    @property
    def last(self) -> float:
        return self.keyframes[-1].at

    @property
    def rule(self) -> str:
        return RULE[self.interpolation]

    def at(self, parameter: float) -> Camera:
        """The camera at `parameter`, by the path's own rule. Outside the keyframes' range is refused,
        never clamped: a frame at the end shown for a parameter past it would be a lie about where."""
        t = float(parameter)
        if not np.isfinite(t) or t < self.first or t > self.last:
            raise CameraPathError(
                f"媒介変数 {parameter!r} はカメラパス '{self.name}' の範囲 {self.first}〜{self.last} の外です。"
                "端の姿勢で代用はしません"
            )
        positions = np.array([frame.camera.position_m for frame in self.keyframes], dtype=np.float64)
        focal_points = np.array([frame.camera.focal_point_m for frame in self.keyframes], dtype=np.float64)
        view_ups = np.array([frame.camera.view_up for frame in self.keyframes], dtype=np.float64)
        parameters = np.array([frame.at for frame in self.keyframes], dtype=np.float64)
        segment = int(np.searchsorted(parameters, t, side="right") - 1)
        segment = min(max(segment, 0), len(parameters) - 2)
        span = parameters[segment + 1] - parameters[segment]
        local = (t - parameters[segment]) / span
        if self.interpolation == "smooth":
            position = _catmull_rom(positions, segment, local)
            focal_point = _catmull_rom(focal_points, segment, local)
        else:
            position = _lerp(positions, segment, local)
            focal_point = _lerp(focal_points, segment, local)
        view_up = _lerp(view_ups, segment, local)
        norm = float(np.linalg.norm(view_up))
        if norm == 0.0:
            raise CameraPathError(
                f"媒介変数 {parameter!r} で上方向が 0 になります（キーフレーム {segment} と {segment + 1} の上方向が正反対）"
            )
        view_up = view_up / norm
        first = self.keyframes[0].camera
        scale: float | None = None
        if first.projection == "orthographic":
            scales = np.array([frame.camera.parallel_scale_m for frame in self.keyframes], dtype=np.float64)
            scale = float(_lerp(scales[:, None], segment, local)[0])
        return Camera(
            position_m=tuple(float(one) for one in position),  # type: ignore[arg-type]
            focal_point_m=tuple(float(one) for one in focal_point),  # type: ignore[arg-type]
            view_up=tuple(float(one) for one in view_up),  # type: ignore[arg-type]
            parallel_scale_m=scale,
            projection=first.projection,
        )

    def describe(self) -> str:
        return f"カメラパス '{self.name}'：キーフレーム {len(self.keyframes)} 件（媒介変数 {self.first}〜{self.last}）・{self.rule}"


def _lerp(values: np.ndarray, segment: int, local: float) -> np.ndarray:
    return values[segment] * (1.0 - local) + values[segment + 1] * local


def _catmull_rom(values: np.ndarray, segment: int, local: float) -> np.ndarray:
    """Uniform Catmull-Rom through the keyframes; the ends repeat their neighbour, so the curve passes
    through every keyframe and starts and ends where they do."""
    before = values[max(segment - 1, 0)]
    start = values[segment]
    end = values[segment + 1]
    after = values[min(segment + 2, len(values) - 1)]
    t, t2, t3 = local, local * local, local * local * local
    return 0.5 * (
        2.0 * start
        + (end - before) * t
        + (2.0 * before - 5.0 * start + 4.0 * end - after) * t2
        + (3.0 * start - 3.0 * end + after - before) * t3
    )


def from_definition(stated: Mapping[str, Any], camera_of: Callable[[Mapping[str, Any] | None], Camera]) -> CameraPath:
    """A path as CT-004 stores one. `camera_of` is the caller's parser for the camera shape, so the
    one reading of a camera serves the definition's camera and its keyframes alike."""
    keyframes = []
    for index, frame in enumerate(stated.get("keyframes") or []):
        if not isinstance(frame, Mapping) or "at" not in frame:
            raise CameraPathError(f"キーフレーム {index} に媒介変数 at がありません")
        try:
            at = float(frame["at"])
        except (TypeError, ValueError):
            raise CameraPathError(f"キーフレーム {index} の at が数ではありません：{frame['at']!r}") from None
        keyframes.append(Keyframe(at, camera_of(frame.get("camera"))))
    return CameraPath(
        id=str(stated.get("id") or ""),
        name=str(stated.get("name") or stated.get("id") or ""),
        keyframes=tuple(keyframes),
        interpolation=str(stated.get("interpolation") or "linear"),
    )
