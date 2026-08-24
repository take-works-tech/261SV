"""A case whose input file is missing or changed opens unresolved, and nothing is touched (AC-012).

The distinction that matters: **missing** and **changed** are different states, not one problem state.
A user can restore a missing file. A changed one they have to decide about, because the numbers in the
workspace were computed from what it used to be - and re-reading it silently would replace every figure
under a report someone already wrote.

No VTK: this is file metadata.

Verifies: workspace/AC-012, workspace/TASK-013.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from service.workspace.hierarchy import new_case
from service.workspace.sources import (
    SourceState,
    record,
    resolve_case,
    status_of,
)


def a_file(directory: Path, name: str, text: str = "result") -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


class TestWhatIsRecorded:
    def test_a_reference_holds_the_path_size_and_time_and_not_the_contents(self, tmp_path: Path) -> None:
        """CT-001: references, never the files themselves."""
        source = record(a_file(tmp_path, "run.vtu"), relative_to=tmp_path)

        assert set(source) == {"pathRelative", "sizeBytes", "modifiedIso"}
        assert source["pathRelative"] == "run.vtu"
        assert source["sizeBytes"] == len("result")

    def test_the_path_is_relative_so_a_moved_project_still_opens(self, tmp_path: Path) -> None:
        (tmp_path / "inputs").mkdir()
        source = record(a_file(tmp_path / "inputs", "run.vtu"), relative_to=tmp_path)

        assert source["pathRelative"] == "inputs/run.vtu"


class TestThreeStatesRatherThanTwo:
    def test_an_unchanged_file_is_present(self, tmp_path: Path) -> None:
        source = record(a_file(tmp_path, "run.vtu"), relative_to=tmp_path)

        assert status_of(source, relative_to=tmp_path).state is SourceState.PRESENT

    def test_a_deleted_file_is_missing(self, tmp_path: Path) -> None:
        path = a_file(tmp_path, "run.vtu")
        source = record(path, relative_to=tmp_path)
        path.unlink()

        status = status_of(source, relative_to=tmp_path)

        assert status.state is SourceState.MISSING
        assert "読み込みも書き換えもしていません" in status.describe()

    def test_a_file_of_a_different_size_is_changed_not_missing(self, tmp_path: Path) -> None:
        """A user can restore a missing file; a changed one they have to decide about."""
        path = a_file(tmp_path, "run.vtu")
        source = record(path, relative_to=tmp_path)
        path.write_text("result, longer", encoding="utf-8")

        status = status_of(source, relative_to=tmp_path)

        assert status.state is SourceState.CHANGED
        assert "読み直していません" in status.describe()

    def test_a_file_touched_later_is_changed(self, tmp_path: Path) -> None:
        path = a_file(tmp_path, "run.vtu")
        source = record(path, relative_to=tmp_path)
        later = time.time() + 120
        os.utime(path, (later, later))

        assert status_of(source, relative_to=tmp_path).state is SourceState.CHANGED

    def test_the_change_is_described_with_both_sides(self, tmp_path: Path) -> None:
        """"Changed" without what it was and what it is now leaves the user nothing to decide with."""
        path = a_file(tmp_path, "run.vtu")
        source = record(path, relative_to=tmp_path)
        path.write_text("much longer than before", encoding="utf-8")

        line = status_of(source, relative_to=tmp_path).describe()

        assert str(len("result")) in line
        assert str(len("much longer than before")) in line


class TestACaseOpensUnresolvedRatherThanFailing:
    def test_every_source_present_resolves_the_case(self, tmp_path: Path) -> None:
        case = new_case("c1", "baseline")
        case["sources"] = [record(a_file(tmp_path, f"{n}.vtu"), relative_to=tmp_path) for n in "ab"]

        assert resolve_case(case, relative_to=tmp_path).is_resolved

    def test_one_missing_source_leaves_the_case_unresolved(self, tmp_path: Path) -> None:
        case = new_case("c1", "baseline")
        paths = [a_file(tmp_path, f"{n}.vtu") for n in "ab"]
        case["sources"] = [record(path, relative_to=tmp_path) for path in paths]
        paths[0].unlink()

        resolution = resolve_case(case, relative_to=tmp_path)

        assert resolution.is_resolved is False
        assert len(resolution.unresolved) == 1

    def test_the_summary_counts_the_two_kinds_separately(self, tmp_path: Path) -> None:
        case = new_case("c1", "baseline")
        paths = [a_file(tmp_path, f"{n}.vtu") for n in "abc"]
        case["sources"] = [record(path, relative_to=tmp_path) for path in paths]
        paths[0].unlink()
        paths[1].write_text("different", encoding="utf-8")

        line = resolve_case(case, relative_to=tmp_path).describe()

        assert "不明 1 件" in line
        assert "変更 1 件" in line
        assert "削除も書き換えもしていません" in line

    def test_a_case_with_no_sources_is_resolved(self, tmp_path: Path) -> None:
        """Nothing to be unresolved about. A case may exist before anything is attached to it."""
        assert resolve_case(new_case("c1", "empty"), relative_to=tmp_path).is_resolved


class TestWhatThisCheckDoesNotClaim:
    def test_a_file_whose_bytes_changed_but_size_and_time_did_not_is_not_detected(
        self, tmp_path: Path
    ) -> None:
        """Recorded in a test rather than left for someone to discover. CT-001 stores a size and a time,
        not a checksum, and this is exactly what that costs - stating it is cheaper than a promise the
        contract cannot keep."""
        path = a_file(tmp_path, "run.vtu", "aaaaaa")
        source = record(path, relative_to=tmp_path)
        stat = path.stat()
        path.write_text("bbbbbb", encoding="utf-8")  # same length
        os.utime(path, (stat.st_atime, stat.st_mtime))

        assert status_of(source, relative_to=tmp_path).state is SourceState.PRESENT
