"""A camera path answers "from where" along a parameter, by a rule that travels with the frame (XC-289).

Verifies: 16_application_model §7 (`timeline`: named paths, keyframes, interpolation, preview), XC-200's
separation of when and where, and the refusals a path makes by name.
"""

from __future__ import annotations

import math

import pytest
from conftest import requires_vtk

requires_vtk()

from engine.visualization.camera_path import CameraPath, CameraPathError, Keyframe, from_definition  # noqa: E402
from engine.visualization.render import Camera  # noqa: E402


def pose(position, focal=(0.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), **rest) -> Camera:
    return Camera(position_m=position, focal_point_m=focal, view_up=up, **rest)


def straight() -> CameraPath:
    return CameraPath("path:1", "一周の半分", (
        Keyframe(0.0, pose((4.0, 0.0, 0.0))),
        Keyframe(0.5, pose((0.0, 4.0, 0.0))),
        Keyframe(1.0, pose((-4.0, 0.0, 2.0), up=(0.0, 1.0, 0.0))),
    ))


class TestTheCameraAlongThePath:
    def test_at_a_keyframe_the_camera_is_that_keyframe_s(self) -> None:
        path = straight()

        assert path.at(0.0).position_m == (4.0, 0.0, 0.0)
        assert path.at(0.5).position_m == (0.0, 4.0, 0.0)
        assert path.at(1.0).position_m == (-4.0, 0.0, 2.0)
        assert path.at(1.0).view_up == (0.0, 1.0, 0.0)

    def test_linear_is_straight_between_the_two_keyframes_around_the_parameter(self) -> None:
        path = straight()

        camera = path.at(0.25)

        assert camera.position_m == pytest.approx((2.0, 2.0, 0.0))
        assert camera.focal_point_m == (0.0, 0.0, 0.0)
        assert camera.projection == "perspective"

    def test_the_view_up_is_interpolated_and_normalised(self) -> None:
        path = straight()

        camera = path.at(0.75)

        assert camera.view_up == pytest.approx((0.0, 1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0)))
        assert math.isclose(math.hypot(*camera.view_up), 1.0)

    def test_smooth_passes_through_every_keyframe_and_bends_between_them(self) -> None:
        path = CameraPath("path:2", "滑らか", straight().keyframes, interpolation="smooth")

        assert path.at(0.5).position_m == pytest.approx((0.0, 4.0, 0.0))
        between = path.at(0.25).position_m
        assert between != pytest.approx((2.0, 2.0, 0.0)), "a curve, not the chord"
        assert path.rule.startswith("位置と注視点はキーフレームを通る一様 Catmull-Rom 曲線")

    def test_an_orthographic_path_interpolates_its_width(self) -> None:
        path = CameraPath("path:3", "平行", (
            Keyframe(0.0, pose((4.0, 0.0, 0.0), projection="orthographic", parallel_scale_m=1.0)),
            Keyframe(1.0, pose((0.0, 4.0, 0.0), projection="orthographic", parallel_scale_m=3.0)),
        ))

        camera = path.at(0.5)

        assert camera.projection == "orthographic" and camera.parallel_scale_m == pytest.approx(2.0)

    def test_the_rule_travels_with_the_path(self) -> None:
        assert "直線補間" in straight().describe() and "キーフレーム 3 件" in straight().describe()


class TestWhatIsRefused:
    def test_one_keyframe_is_not_a_path(self) -> None:
        with pytest.raises(CameraPathError, match="2 件以上"):
            CameraPath("p", "one", (Keyframe(0.0, pose((1.0, 0.0, 0.0))),))

    def test_a_parameter_past_the_ends_is_refused_and_not_clamped(self) -> None:
        with pytest.raises(CameraPathError, match="端の姿勢で代用はしません"):
            straight().at(1.5)
        partial = CameraPath("p", "late", (Keyframe(0.2, pose((1.0, 0.0, 0.0))), Keyframe(0.8, pose((0.0, 1.0, 0.0)))))
        with pytest.raises(CameraPathError, match="0.2〜0.8"):
            partial.at(0.1)

    def test_keyframes_out_of_order_are_refused_rather_than_sorted(self) -> None:
        with pytest.raises(CameraPathError, match="昇順"):
            CameraPath("p", "swapped", (Keyframe(0.5, pose((1.0, 0.0, 0.0))), Keyframe(0.0, pose((0.0, 1.0, 0.0)))))

    def test_a_default_pose_cannot_be_a_keyframe(self) -> None:
        with pytest.raises(CameraPathError, match="位置・注視点・上方向"):
            CameraPath("p", "unset", (Keyframe(0.0, Camera()), Keyframe(1.0, pose((0.0, 1.0, 0.0)))))

    def test_mixed_projections_are_refused(self) -> None:
        with pytest.raises(CameraPathError, match="投影が揃っていません"):
            CameraPath("p", "mixed", (
                Keyframe(0.0, pose((1.0, 0.0, 0.0))),
                Keyframe(1.0, pose((0.0, 1.0, 0.0), projection="orthographic", parallel_scale_m=1.0)),
            ))

    def test_an_unknown_rule_is_refused_by_name(self) -> None:
        with pytest.raises(CameraPathError, match="bezier"):
            CameraPath("p", "?", straight().keyframes, interpolation="bezier")


class TestFromTheDocument:
    def test_the_stored_shape_becomes_a_path_through_the_caller_s_camera_parser(self) -> None:
        from service.command.handlers import camera_of
        from service.command.surface import Result

        def parse(stated):
            camera = camera_of(stated)
            assert not isinstance(camera, Result), camera
            return camera

        path = from_definition({
            "id": "path:1", "name": "寄り", "interpolation": "smooth",
            "keyframes": [
                {"at": 0, "camera": {"position_m": [4, 0, 0], "focalPoint_m": [0, 0, 0], "viewUp": [0, 0, 1], "projection": "perspective"}},
                {"at": 1, "camera": {"position_m": [1, 0, 0], "focalPoint_m": [0, 0, 0], "viewUp": [0, 0, 1], "projection": "perspective"}},
            ],
        }, parse)

        assert path.name == "寄り" and path.interpolation == "smooth"
        assert path.at(0.5).position_m == pytest.approx((2.5, 0.0, 0.0))

    def test_a_keyframe_without_a_parameter_is_refused(self) -> None:
        with pytest.raises(CameraPathError, match="at がありません"):
            from_definition({"id": "p", "keyframes": [{"camera": {}}]}, lambda stated: Camera())
