"""Where a file is, and whether it is still there (ingest/AC-022, AC-046, XC-285; #264).

Three things a shared folder does to a result file that a local one rarely does: the path is a UNC
name, the file goes away between two moments, and another process holds it. Each was measured here
(E-213) and each has one honest answer: a UNC path is a path; a file that vanished while it was read,
or since the dataset was loaded from it, is refused naming that; a file the operating system will not
let this process read is refused with the operating system's reason - not, as the toolkit's reader
reports it, as a file with nothing in it.

The UNC measurement needs a share reachable from the test - the administrative share of the drive the
temporary directory is on, on Windows. Where there is none this test says so rather than pretending;
the measurement recorded in E-213 was taken on such a share.
"""

from __future__ import annotations

import dataclasses
import os
import sys
from pathlib import Path

import pytest
from conftest import requires_h5py, requires_vtk

requires_vtk()

from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader  # noqa: E402

from engine import reader  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from service.workspace import sources  # noqa: E402
from demo_case import write_cube  # noqa: E402
from test_handlers import loaded, opened  # noqa: E402


class Vanishing(vtkXMLUnstructuredGridReader):
    """A reader whose file is deleted under it: a solver's cleanup, or a share that went away."""

    def Update(self) -> None:  # noqa: N802 - the toolkit's own name
        super().Update()
        os.remove(self.GetFileName())


class TestAFileThatVanishes:
    """AC-046: gone while it was read, or gone since the load - refused naming the disappearance."""

    def test_gone_during_the_read_is_refused_by_name(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        path = tmp_path / "gone.vtu"
        write_cube(path)
        monkeypatch.setitem(reader._READERS, ".vtu", dataclasses.replace(reader._READERS[".vtu"], factory=Vanishing))

        with pytest.raises(reader.FileChanged) as refusal:
            reader.read_case(path)

        assert "読んでいる間に消えました" in str(refusal.value) and "gone.vtu" in str(refusal.value)
        assert "バイト" in str(refusal.value), "what it was before it went, so the reader knows it was there"

    def test_gone_since_the_load_is_refused_by_name_and_not_read_as_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "gone.vtu"
        write_cube(path)
        fingerprint = reader.snapshot(path)
        os.remove(path)

        with pytest.raises(reader.FileChanged) as refusal:
            reader.read_case(path, expected=fingerprint)

        assert "読み込んだあとに消えました" in str(refusal.value)
        assert "does not exist" not in str(refusal.value)

    def test_through_the_handlers_what_was_read_stays_and_another_step_is_refused(self, tmp_path: Path) -> None:
        requires_h5py()
        from cgns_fixture import write_transient_cgns

        surface, session, dataset_id = loaded(tmp_path, write=write_transient_cgns, name="t.cgns")
        os.remove(session.datasets[dataset_id].path)

        first = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress"}))
        second = surface.submit(Command("field.statistics", {"datasetId": dataset_id, "fieldName": "stress", "resultPosition": 1}))

        assert first.status is Status.ANSWERED and first.value["maximum"]["value"] == 90.0
        assert second.status is Status.REFUSED
        assert "読み込んだあとに消えました" in (second.reason or "") and "t.cgns" in (second.reason or "")


@pytest.mark.skipif(sys.platform != "win32", reason="a mandatory byte-range lock is a Windows fact; POSIX locks are advisory and do not stop a read")
class TestAFileAnotherProcessHolds:
    """AC-022: the reason is the operating system's, not the toolkit's "nothing is there" (E-213)."""

    def test_a_locked_file_is_refused_with_the_operating_system_s_reason(self, tmp_path: Path) -> None:
        import msvcrt

        path = tmp_path / "held.vtu"
        write_cube(path)
        with path.open("r+b") as holder:
            msvcrt.locking(holder.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                with pytest.raises(reader.UnreadableFileError) as refusal:
                    reader.read_case(path)
                surface, _, workspace = opened(tmp_path)
                write_cube(workspace.parent / "other.vtu")
                result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(path)]}))
            finally:
                msvcrt.locking(holder.fileno(), msvcrt.LK_UNLCK, 1)

        assert "開けません、または読めません" in str(refusal.value) and "held.vtu" in str(refusal.value)
        assert "none of them is there" not in str(refusal.value)
        assert result.status is Status.REFUSED and "開けません" in (result.reason or "")
        assert reader.read_case(path).present[0].dataset.point_count == 8, "released, it reads"


def administrative_share(path: Path) -> Path | None:
    """The same path through the drive's administrative share, where one is reachable."""
    if sys.platform != "win32" or not path.drive.endswith(":"):
        return None
    candidate = Path(f"//localhost/{path.drive[0]}$" + str(path)[2:].replace("\\", "/"))
    try:
        return candidate if candidate.exists() else None
    except OSError:
        return None


class TestAUncPath:
    """XC-285, E-213: a UNC path reads, records and reopens like any path - except that a file on a
    share has no path relative to a document elsewhere, and the record says so by being absolute."""

    @staticmethod
    def _unc(tmp_path: Path, name: str) -> Path:
        path = tmp_path / name
        write_cube(path)
        through = administrative_share(path)
        if through is None:
            pytest.skip("no administrative share reachable here; the UNC measurement is E-213, taken on Windows")
        return through

    def test_a_file_reads_and_fingerprints_through_the_share(self, tmp_path: Path) -> None:
        through = self._unc(tmp_path, "cube.vtu")

        assert str(through).startswith("\\\\localhost\\")
        assert reader.read_case(through).present[0].dataset.point_count == 8
        assert set(reader.snapshot(through)) == {"cube.vtu"}

    def test_a_file_on_a_share_is_recorded_absolute_and_found_again(self, tmp_path: Path) -> None:
        surface, session, workspace = opened(tmp_path)
        through = self._unc(tmp_path, "cube.vtu")

        result = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(through)]}))

        assert result.status is Status.APPLIED, result.reason
        entry = session.workspace.cases[0]["sources"][-1]
        assert entry["pathRelative"].startswith("//localhost/"), "no relative path exists to a document on another root"
        assert Path(entry["pathAbsolute"]) == through.resolve()
        found = sources.find_source(session.workspace.cases[0], through, relative_to=workspace.parent)
        assert found is entry
        assert sources.status_of(entry, relative_to=workspace.parent).state is sources.SourceState.PRESENT

    def test_a_workspace_on_a_share_opens_locks_and_saves(self, tmp_path: Path) -> None:
        from service.command.handlers import Session, build_surface
        from test_handlers import a_workspace, at, counting_issuer

        document = a_workspace(tmp_path)
        through = administrative_share(document)
        if through is None:
            pytest.skip("no administrative share reachable here; the UNC measurement is E-213, taken on Windows")
        session = Session(clock=at(9), issue=counting_issuer(), native_offscreen=lambda: (False, "テスト"))
        surface = build_surface(session)

        opened_result = surface.submit(Command("workspace.open", {"path": str(through)}))
        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))

        assert opened_result.status is Status.APPLIED, opened_result.reason
        assert session.read_only is False
        assert (document.parent / (document.name + ".lock")).exists()
        assert saved.status is Status.APPLIED, saved.reason
