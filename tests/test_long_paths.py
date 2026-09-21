"""Paths longer than Windows allows (ingest/AC-048, XC-294; #254).

Windows stops at 260 characters unless a program lifts the limit for itself, and the policy that
lifts it for every program is off by default. Measured here (E-217): with that policy off, Python,
the toolkit's XML reader and writer, HDF5 under CGNS and netCDF under Exodus all take a path in the
extended-length form and none takes the plain one. So every path this engine hands to the operating
system goes through `domain_core.os_paths.for_os`, and what it records and answers is the plain form.
The tests below build a directory whose plain path is past the limit and walk every reader, the
document, the export and the engine process through it as a caller would - with plain paths.
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
from domain_core.os_paths import WINDOWS_PATH_LIMIT, for_os, for_people  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from service.workspace.document import FORMAT_VERSION  # noqa: E402
from demo_case import write_bar, write_cube, write_exodus  # noqa: E402
from test_handlers import a_surface  # noqa: E402

SEGMENT = "a_directory_named_at_the_length_a_study_folder_reaches_" + "x" * 8  # 64 characters


def long_directory(tmp_path: Path) -> Path:
    """A directory whose plain path is past the classic limit, made through the operating system's
    form because the plain one cannot make it (E-217). Returned plain: what a caller has."""
    deep = tmp_path
    while len(str(deep)) <= 300:
        deep = deep / SEGMENT
    os.makedirs(for_os(deep), exist_ok=True)
    assert len(str(deep)) > 260
    return deep


def copy_in(source: Path, target: Path) -> Path:
    shutil.copyfile(for_os(source), for_os(target))
    return target


def a_document_at(directory: Path) -> Path:
    document = {
        "formatVersion": FORMAT_VERSION,
        "id": "ws:1",
        "name": "長い場所の検討",
        "cases": [{"id": "case:1", "name": "baseline"}],
        "variables": [],
        "workspaceItems": {"simulations": [], "views": [], "graphs": [], "reports": []},
    }
    path = directory / "beam.svw"
    for_os(path).write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


class TestTheTwoForms:
    def test_a_short_path_is_left_alone_and_a_long_one_is_extended_on_windows_only(self, tmp_path: Path) -> None:
        short = tmp_path / "cube.vtu"
        assert for_os(short) == Path(os.path.abspath(short))
        long = long_directory(tmp_path) / "cube.vtu"
        taken = str(for_os(long))
        if sys.platform == "win32":
            assert taken.startswith("\\\\?\\") and taken.endswith("cube.vtu")
            assert for_os(taken) == Path(taken), "idempotent"
            unc = "\\\\localhost\\C$\\" + "y" * WINDOWS_PATH_LIMIT
            assert str(for_os(unc)).startswith("\\\\?\\UNC\\localhost\\C$\\")
            assert for_people(for_os(unc)) == Path(unc)
        else:
            assert taken == str(long)
        assert for_people(for_os(long)) == Path(os.path.abspath(long)), "the plain form comes back"
        assert for_people(short) == short


class TestEveryReaderReadsAtALongPath:
    def test_vtk_xml(self, tmp_path: Path) -> None:
        original = tmp_path / "cube.vtu"
        write_cube(original)
        path = copy_in(original, long_directory(tmp_path) / "cube.vtu")

        assert reader.read_case(path).present[0].dataset.point_count == 8
        assert set(reader.snapshot(path)) == {"cube.vtu"}

    def test_exodus_through_netcdf(self, tmp_path: Path) -> None:
        original = tmp_path / "case.ex2"
        write_exodus(original)
        path = copy_in(original, long_directory(tmp_path) / "case.ex2")

        assert sorted(reader.read_case(path).present[0].dataset.fields) == ["elem_stress", "stress", "temp"]

    def test_cgns_through_hdf5(self, tmp_path: Path) -> None:
        requires_h5py()
        from cgns_fixture import write_transient_cgns

        original = tmp_path / "t.cgns"
        write_transient_cgns(original)
        path = copy_in(original, long_directory(tmp_path) / "t.cgns")

        assert reader.read_case(path).maximum("stress").value == 90.0
        assert reader.read_case(path, step=1).maximum("stress").value == 91.0


class TestTheDocumentAndItsFilesAtALongPath:
    """The document, its lock, its sources, the deliverable and the output listing at a long path,
    every record and every answer in the plain form."""

    def test_open_inspect_load_save_export_and_list(self, tmp_path: Path) -> None:
        where = long_directory(tmp_path)
        workspace = a_document_at(where)
        original = tmp_path / "bar.vtu"
        write_bar(original)
        source = copy_in(original, where / "bar.vtu")
        surface, session = a_surface()

        opened = surface.submit(Command("workspace.open", {"path": str(workspace)}))
        inspected = surface.submit(Command("dataset.inspect", {"path": str(source)}))
        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))
        saved = surface.submit(Command("workspace.save", {"workspaceId": "ws:1"}))
        report_id = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
            "name": "棒", "targets": ["html"], "blocks": [{"kind": "valueTable", "fields": ["stress"]}],
        }})).value["id"]
        target = where / "report.html"
        exported = surface.submit(Command("report.export", {"reportId": report_id, "path": str(target)}))
        listed = surface.submit(Command("output.list", {"workspaceId": "ws:1"}))

        assert opened.status is Status.APPLIED, opened.reason
        assert session.read_only is False
        assert for_os(where / "beam.svw.lock").exists(), "the lock is beside the document"
        assert inspected.status is Status.ANSWERED and inspected.value["exists"] is True
        assert loaded.status is Status.APPLIED, loaded.reason
        entry = session.workspace.cases[0]["sources"][-1]
        assert entry["pathRelative"] == "bar.vtu"
        assert entry["pathAbsolute"] == str(source) and "\\\\?\\" not in entry["pathAbsolute"], "recorded plain, never in the wire form"
        assert saved.status is Status.APPLIED, saved.reason
        assert saved.value["path"] == str(workspace), "answered plain"
        assert "bar.vtu" in for_os(workspace).read_text(encoding="utf-8") and "\\\\?\\" not in for_os(workspace).read_text(encoding="utf-8")
        assert exported.status is Status.APPLIED, exported.reason
        assert exported.value["path"] == str(target) and for_os(target).stat().st_size == exported.value["bytes"]
        assert listed.status is Status.ANSWERED, listed.reason

    def test_a_saved_document_reopens_and_finds_its_source(self, tmp_path: Path) -> None:
        where = long_directory(tmp_path)
        workspace = a_document_at(where)
        original = tmp_path / "cube.vtu"
        write_cube(original)
        source = copy_in(original, where / "cube.vtu")
        surface, _ = a_surface()
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED
        assert surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]})).status is Status.APPLIED
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED

        again, _ = a_surface()
        reopened = again.submit(Command("workspace.open", {"path": str(workspace)}))

        assert reopened.status is Status.APPLIED, reopened.reason
        assert reopened.value["unresolvedCases"] == []

    def test_a_source_at_a_long_path_beside_a_document_at_a_short_one(self, tmp_path: Path) -> None:
        """The two forms meet: the document is short, the source is long, and the record between them
        is the plain relation the document can carry."""
        workspace = a_document_at(tmp_path)
        original = tmp_path / "cube.vtu"
        write_cube(original)
        source = copy_in(original, long_directory(tmp_path) / "cube.vtu")
        surface, session = a_surface()
        assert surface.submit(Command("workspace.open", {"path": str(workspace)})).status is Status.APPLIED

        loaded = surface.submit(Command("dataset.load", {"caseId": "case:1", "filePaths": [str(source)]}))

        assert loaded.status is Status.APPLIED, loaded.reason
        entry = session.workspace.cases[0]["sources"][-1]
        assert entry["pathRelative"] == source.relative_to(tmp_path).as_posix()
        assert "\\\\?\\" not in entry["pathRelative"] and "\\\\?\\" not in entry["pathAbsolute"]
        assert surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})).status is Status.APPLIED
        again, _ = a_surface()
        assert again.submit(Command("workspace.open", {"path": str(workspace)})).value["unresolvedCases"] == []


class TestTheEngineProcessAtALongPath:
    def test_the_connection_and_log_directories(self, tmp_path: Path) -> None:
        where = long_directory(tmp_path)
        run = where / "run"
        logs = where / "logs"
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"), "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [sys.executable, "-m", "service.transport", "--connection-directory", str(run), "--log-directory", str(logs), "--log-level", "debug"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.time() + 60
            while not for_os(run / "connection.json").exists():
                assert process.poll() is None, "the engine exited before writing its connection file"
                assert time.time() < deadline
                time.sleep(0.05)
            connection = json.loads(for_os(run / "connection.json").read_text(encoding="utf-8"))
            with urllib.request.urlopen(f"http://{connection['host']}:{connection['port']}/health", timeout=10) as answer:
                answer.read()
        finally:
            process.terminate()
            process.wait(timeout=20)
        lines = [json.loads(one) for one in for_os(logs / "solvia.log").read_text(encoding="utf-8").splitlines()]
        assert lines[0]["event"] == "engine.start" and lines[0]["pid"] == connection["pid"]


@pytest.mark.skipif(sys.platform != "win32", reason="the limit is a Windows fact")
def test_the_plain_long_path_is_what_fails_without_this(tmp_path: Path) -> None:
    """The measurement this module rests on, kept as a test so a Windows that lifts the limit
    unconditionally is noticed (XC-294's reversal trigger)."""
    deep = long_directory(tmp_path)
    try:
        (deep / "plain.txt").write_text("x", encoding="utf-8")
        plain_works = True
    except OSError:
        plain_works = False
    policy = 0
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            policy = int(winreg.QueryValueEx(key, "LongPathsEnabled")[0])
    except OSError:
        policy = 0
    assert plain_works == (policy == 1), f"the plain long path {'works' if plain_works else 'fails'} with LongPathsEnabled={policy}"
