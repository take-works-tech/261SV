"""Paths with characters outside ASCII (ingest/AC-047, XC-293; #253).

A path on a Japanese desktop carries Japanese, full-width forms, spaces and punctuation, and CAE
readers have historically failed there - in the first minute, on the first file. Every reader this
build has, every file it writes and the engine process's own directories are exercised at such a path
here, and the result is recorded as E-216 rather than assumed from the libraries' documentation.
Every native library that takes a path takes it as the UTF-8 `str` Python hands over; where one
cannot turn that into the platform's own form, the failure is this test's finding, and the fix goes
where the path is handed over, not into a rule that tells people to rename their folders.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from conftest import requires_h5py, requires_vtk

requires_vtk()

from engine import reader  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from demo_case import write_bar, write_cube, write_ensight, write_vtkhdf  # noqa: E402
from test_handlers import a_surface, opened  # noqa: E402
from test_reader import write_exodus  # noqa: E402

#: Japanese, full-width letters and a full-width solidus, a space, punctuation, and a character
#: outside the Basic Multilingual Plane - every class of character a path from a Japanese desktop
#: can carry, in one directory name.
HARD = "解析 結果／ｒｕｎ－１ #1 (a&b) 📐"


def hard(tmp_path: Path) -> Path:
    where = tmp_path / HARD
    where.mkdir()
    return where


class TestEveryReaderReadsAtSuchAPath:
    """The readers take the path as UTF-8; each format's own library - VTK's XML reader, netCDF under
    Exodus, HDF5 under CGNS and VTKHDF, the EnSight reader's own file handling - must turn it into the
    platform's form (E-216, E-227)."""

    def test_vtk_xml(self, tmp_path: Path) -> None:
        path = hard(tmp_path) / "立方体 (最終).vtu"
        write_cube(path)

        case = reader.read_case(path)

        assert case.present[0].dataset.point_count == 8
        assert set(reader.snapshot(path)) == {path.name}

    def test_exodus_through_netcdf(self, tmp_path: Path) -> None:
        """E-216: the toolkit's Exodus writer cannot create a file at such a path on Windows, and its
        reader, handed one, ends the process with 0xC0000409 rather than an error. So the file is
        written where the writer can and copied, and the read is refused by name before the library
        sees the path - except in a process running in the UTF-8 code page, where it reads (XC-293)."""
        plain = tmp_path / "plain.ex2"
        write_exodus(plain)
        path = hard(tmp_path) / "ケース ＃２.ex2"
        shutil.copyfile(plain, path)

        if sys.platform == "win32" and reader.active_code_page() != reader.UTF8_CODE_PAGE:
            with pytest.raises(reader.UnreadableFileError) as refusal:
                reader.read_case(path)
            assert "netCDF" in str(refusal.value) and "ケース ＃２.ex2" in str(refusal.value) and "E-216" in str(refusal.value)
            assert "解析" in str(refusal.value), "the offending characters are named"
            assert reader.support_level(path)[0] == "Verified", "the format is supported; this path is not"
            assert "この経路からは読めません" in (reader.load_refusal(path) or ""), "the inspection says it before any load"
            assert reader.load_refusal(plain) is None, "an ASCII path meets no refusal"
        else:
            assert sorted(reader.read_case(path).present[0].dataset.fields) == ["elem_stress", "stress", "temp"]

    def test_ensight_gold(self, tmp_path: Path) -> None:
        """E-227: the EnSight reader takes the case path as given and finds the geometry and variable
        files beside it at such a path; the files are written where the toolkit's writer is known to
        write and copied, so that what is measured is the read."""
        plain = tmp_path / "plain.case"
        write_ensight(plain)
        where = hard(tmp_path)
        for one in tmp_path.iterdir():
            if one.is_file() and one.name.startswith("plain."):
                shutil.copyfile(one, where / one.name.replace("plain.", "板＃２.", 1))
        path = where / "板＃２.case"
        path.write_text(plain.read_text(encoding="utf-8").replace("plain.", "板＃２."), encoding="utf-8")

        case = reader.read_case(path)

        assert case.present[0].dataset.fields["temperature_n"].values.tolist() == [300.0, 310.0, 320.0, 330.0]
        assert set(reader.snapshot(path)) == {"板＃２.case", "板＃２.0.00000.geo", "板＃２.0.00000_n.temperature", "板＃２.0.00000_c.load"}

    def test_vtkhdf_through_hdf5(self, tmp_path: Path) -> None:
        """E-227: the HDF5 library under the VTKHDF reader takes the path as given, as it does under
        CGNS (E-216)."""
        path = hard(tmp_path) / "格子 (最終).vtkhdf"
        write_vtkhdf(path)

        assert reader.read_case(path).present[0].dataset.fields["load"].values.tolist() == [1.5, 2.5]
        assert set(reader.snapshot(path)) == {path.name}

    def test_the_guard_is_the_exodus_family_s_alone(self, tmp_path: Path) -> None:
        """The readers whose libraries take the path as given are not refused what they can read."""
        where = hard(tmp_path)
        for name in ("a.vtu", "a.cgns", "a.stl", "a.vtp", "a.case", "a.vtkhdf", "a.unknown"):
            assert reader.load_refusal(where / name) is None, name
        for name in ("a.e", "a.ex2", "a.exo"):
            expected = sys.platform == "win32" and reader.active_code_page() != reader.UTF8_CODE_PAGE
            assert (reader.load_refusal(where / name) is not None) is expected, name

    def test_cgns_through_hdf5(self, tmp_path: Path) -> None:
        requires_h5py()
        from cgns_fixture import write_transient_cgns

        path = hard(tmp_path) / "過渡 解析.cgns"
        write_transient_cgns(path)

        assert reader.read_case(path).maximum("stress").value == 90.0
        assert reader.read_case(path, step=1).maximum("stress").value == 91.0, "another step is read from the same path"


class TestALoadThatWouldEndTheProcessIsARefusal:
    """Through the handlers: the inspection names the gap, the load is a refusal that names the file
    and the library, the workspace is unchanged, and the engine is still there to say so."""

    @pytest.mark.skipif(sys.platform != "win32", reason="the narrow path is a Windows fact (E-216)")
    def test_inspect_names_it_and_load_refuses_it(self, tmp_path: Path) -> None:
        if reader.active_code_page() == reader.UTF8_CODE_PAGE:
            pytest.skip("this process runs in the UTF-8 code page, where the library takes the path")
        where = hard(tmp_path)
        surface, session, _ = opened(where)
        plain = tmp_path / "plain.ex2"
        write_exodus(plain)
        source = where / "ケース.ex2"
        shutil.copyfile(plain, source)

        inspected = surface.submit(Command("dataset.inspect", {"path": str(source)}))
        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))

        assert inspected.status is Status.ANSWERED and "この経路からは読めません" in inspected.value["refusal"]
        assert not any("この経路" in gap for gap in inspected.value["gaps"]), "the format's gaps are the format's; the path is the file's"
        assert loaded.status is Status.REFUSED and "netCDF" in (loaded.reason or "") and "ケース.ex2" in (loaded.reason or "")
        assert session.datasets == {} and session.workspace.cases[0].get("sources", []) == []


class TestTheDocumentAndItsFilesAtSuchAPath:
    """What the engine writes - the document, its lock, its previous version, the deliverable - and
    what it records about a file, at such a path and with such a name."""

    def test_open_inspect_load_save_export_and_list(self, tmp_path: Path) -> None:
        where = hard(tmp_path)
        surface, session, workspace = opened(where)
        source = where / "棒 (荷重１.５倍).vtu"
        write_bar(source)

        inspected = surface.submit(Command("dataset.inspect", {"path": str(source)}))
        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "棒", "targets": ["html"], "blocks": [{"kind": "valueTable", "fields": ["stress"]}],
        }})).value["id"]
        target = where / "報告書 （最終）.html"
        exported = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))
        listed = surface.submit(Command("output.list", {"workspaceId": "ws:1"}))

        assert inspected.status is Status.ANSWERED and inspected.value["exists"] is True and inspected.value["format"] == "vtu"
        assert loaded.status is Status.APPLIED, loaded.reason
        entry = session.workspace.cases[0]["sources"][-1]
        assert entry["pathRelative"] == source.name, "recorded relative to the document, as the characters they are"
        assert saved.status is Status.APPLIED, saved.reason
        assert source.name in workspace.read_text(encoding="utf-8"), "the document keeps the characters, not escapes of them"
        assert (where / (workspace.name + ".lock")).exists()
        assert exported.status is Status.APPLIED, exported.reason
        assert Path(exported.value["path"]) == target and target.stat().st_size == exported.value["bytes"]
        assert "200" in target.read_text(encoding="utf-8")
        assert listed.status is Status.ANSWERED, listed.reason

    def test_a_saved_document_reopens_and_finds_its_source(self, tmp_path: Path) -> None:
        where = hard(tmp_path)
        surface, _, workspace = opened(where)
        source = where / "立方体.vtu"
        write_cube(source)
        assert surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]})).status is Status.APPLIED
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED

        again, _ = a_surface()
        reopened = again.submit(Command("workspace.open", {"path": str(workspace)}))

        assert reopened.status is Status.APPLIED, reopened.reason
        assert reopened.value["unresolvedCases"] == [], "the relative path with its characters resolves again"


class TestTheEngineProcessAtSuchAPath:
    """The directories the shell hands the engine - where the connection file and the log go - are
    under the user's profile, which on a Japanese desktop is the user's name."""

    def test_the_connection_and_log_directories(self, tmp_path: Path) -> None:
        where = hard(tmp_path)
        run = where / "実行"
        logs = where / "記録"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"), "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [sys.executable, "-m", "service.transport", "--connection-directory", str(run), "--log-directory", str(logs), "--log-level", "debug"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.time() + 60
            while not (run / "connection.json").exists():
                assert process.poll() is None, "the engine exited before writing its connection file"
                assert time.time() < deadline
                time.sleep(0.05)
            connection = json.loads((run / "connection.json").read_text(encoding="utf-8"))
            with urllib.request.urlopen(f"http://{connection['host']}:{connection['port']}/health", timeout=10) as answer:
                answer.read()
        finally:
            process.terminate()
            process.wait(timeout=20)
        lines = [json.loads(one) for one in (logs / "solvia.log").read_text(encoding="utf-8").splitlines()]
        assert lines[0]["event"] == "engine.start" and lines[0]["pid"] == connection["pid"]
