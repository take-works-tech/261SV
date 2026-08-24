"""What a path contains, counted before anything is loaded.

ingest/AC-026 and the half of AC-027 that is discovery: a series or a partitioned set is **one** @Case
with a stated number of steps and parts, and a part the manifest named but that is not there is
reported rather than skipped.

These run with no VTK installed - the manifest is XML and the series is filenames - which is why the
survey is stdlib work in its own module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from domain_core.case_contents import AxisKind, CaseContents, ResultAxis
from engine.survey import survey


def write_manifest(path: Path, sources: list[str], *, create: list[str] | None = None) -> Path:
    """A `.pvtu` naming pieces, with only the listed ones actually written."""
    pieces = "\n".join(f'    <Piece Source="{source}"/>' for source in sources)
    path.write_text(
        '<?xml version="1.0"?>\n<VTKFile type="PUnstructuredGrid">\n'
        f'  <PUnstructuredGrid GhostLevel="0">\n{pieces}\n  </PUnstructuredGrid>\n</VTKFile>\n',
        encoding="utf-8",
    )
    for source in (sources if create is None else create):
        (path.parent / source).write_text("piece", encoding="utf-8")
    return path


class TestPartitionedSet:
    def test_a_manifest_is_one_case_with_its_parts_counted(self, tmp_path: Path) -> None:
        manifest = write_manifest(tmp_path / "run.pvtu", ["run_0.vtu", "run_1.vtu", "run_2.vtu"])

        contents = survey(manifest)

        assert contents.steps == 1
        assert contents.parts == 3
        assert contents.is_partial is False

    def test_a_named_piece_that_is_absent_is_reported_not_skipped(self, tmp_path: Path) -> None:
        """AC-027. The manifest is read here rather than taken from the toolkit precisely for this: a
        reader that hands back the pieces it opened cannot tell you about the one it did not."""
        manifest = write_manifest(
            tmp_path / "run.pvtu",
            ["run_0.vtu", "run_1.vtu", "run_2.vtu"],
            create=["run_0.vtu", "run_2.vtu"],
        )

        contents = survey(manifest)

        assert contents.parts == 2
        assert contents.is_partial is True
        assert contents.missing_parts == ("run_1.vtu",)
        assert "run_1.vtu" in contents.describe()

    def test_a_piece_with_no_source_is_a_missing_part(self, tmp_path: Path) -> None:
        """The manifest said there was a piece there; silence about it would be this product deciding
        the file meant something other than what it says."""
        (tmp_path / "run.pvtu").write_text(
            '<?xml version="1.0"?>\n<VTKFile type="PUnstructuredGrid"><PUnstructuredGrid>'
            '<Piece Source="run_0.vtu"/><Piece/></PUnstructuredGrid></VTKFile>\n',
            encoding="utf-8",
        )
        (tmp_path / "run_0.vtu").write_text("piece", encoding="utf-8")

        contents = survey(tmp_path / "run.pvtu")

        assert contents.is_partial is True
        assert "no Source" in contents.missing_parts[0]


class TestNumberedSeries:
    def test_numbered_files_are_one_case_with_its_steps_counted(self, tmp_path: Path) -> None:
        for index in range(4):
            (tmp_path / f"case_{index:04d}.vtu").write_text("step", encoding="utf-8")

        contents = survey(tmp_path / "case_0000.vtu")

        assert contents.steps == 4
        assert contents.parts == 1

    def test_the_order_is_not_read_as_a_time(self, tmp_path: Path) -> None:
        """GL-036 and E-130: nothing this build reads declares a time value, so a fourth file is the
        fourth step and not `t = 4`. A modal run and a transient run are the same directory of numbered
        files, and labelling mode 3 as a moment says something false about the physics."""
        for index in range(3):
            (tmp_path / f"case_{index:04d}.vtu").write_text("step", encoding="utf-8")

        contents = survey(tmp_path / "case_0000.vtu")

        assert contents.axis.kind is AxisKind.UNDECLARED
        assert contents.axis.positions is None
        assert contents.axis.is_declared is False
        assert "軸の種類は宣言されていません" in contents.describe()

    def test_a_stem_that_merely_ends_in_digits_is_not_a_series(self, tmp_path: Path) -> None:
        """`mesh2d.vtu` is not a second step of `mesh`. The separator is required for this reason."""
        (tmp_path / "mesh2d.vtu").write_text("one", encoding="utf-8")
        (tmp_path / "mesh3d.vtu").write_text("one", encoding="utf-8")

        contents = survey(tmp_path / "mesh2d.vtu")

        assert contents.steps == 1

    def test_a_lone_numbered_file_stays_one_step(self, tmp_path: Path) -> None:
        (tmp_path / "case_0001.vtu").write_text("step", encoding="utf-8")

        assert survey(tmp_path / "case_0001.vtu").steps == 1

    def test_a_single_file_is_one_step_and_one_part(self, tmp_path: Path) -> None:
        (tmp_path / "case.vtu").write_text("one", encoding="utf-8")

        contents = survey(tmp_path / "case.vtu")

        assert (contents.steps, contents.parts) == (1, 1)
        assert contents.axis.kind is AxisKind.NONE


class TestContentsRefusesToBeInconsistent:
    """The counts describe something that was looked at, so a set that cannot be true is a defect here
    rather than a figure someone reads later."""

    def test_positions_must_match_the_step_count(self) -> None:
        with pytest.raises(ValueError) as refusal:
            CaseContents(steps=3, parts=1, axis=ResultAxis(AxisKind.TIME, (0.0, 0.5)))
        assert "counted wrongly" in str(refusal.value)

    def test_a_steady_case_carries_no_positions(self) -> None:
        with pytest.raises(ValueError):
            ResultAxis(AxisKind.NONE, (0.0,))

    def test_positions_without_a_named_axis_are_refused(self) -> None:
        with pytest.raises(ValueError) as refusal:
            ResultAxis(AxisKind.UNDECLARED, (0.0, 1.0))
        assert "say which axis" in str(refusal.value)

    def test_a_case_that_loaded_has_at_least_one_step_and_part(self) -> None:
        with pytest.raises(ValueError):
            CaseContents(steps=0, parts=1, axis=ResultAxis(AxisKind.NONE))
