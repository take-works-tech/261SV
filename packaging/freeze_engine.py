"""Freeze the engine into a directory that runs with no Python installed (XC-261).

    python packaging/freeze_engine.py            # writes build/engine/solvia-engine/
    python packaging/freeze_engine.py --check    # freezes, then starts the result and asks /health

PyInstaller, one directory (`--onedir`), never one file: a single-file build unpacks itself into a
temporary directory on every start, which is the cold start #307 is about, paid on every launch. The
options are written here rather than in a spec file so that what is collected is readable at a
glance and reviewed with the code:

  - `--collect-all vtkmodules`: VTK is a tree of extension modules loading shared libraries by name,
    and PyInstaller's static analysis sees the imports but not the libraries; collecting the package
    whole is what the toolkit's own packaging guidance amounts to, and hooks-contrib carries no hook
    for it (checked 2026-09-19: only trame_vtk hooks exist)
  - `--collect-submodules` for the three source packages: readers are chosen by name at run time,
    and a module nothing imports statically is a module the frozen engine does not have
  - `--copy-metadata` for the two runtime distributions: `importlib.metadata.version` is how the
    engine reports what it runs on (`system.capabilities`), and metadata is not code

The result is measured, not assumed: `--check` starts the frozen engine the way the shell does and
prints the time to its connection file and the answer of `/health`. The numbers go to
spike/results.json by hand, with the machine they were taken on (E-202).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
DIST = BUILD / "engine"
NAME = "solvia-engine"
RUNTIME_DISTRIBUTIONS = ("vtk", "numpy")

#: What `--collect-all vtkmodules` drags in that the engine never uses: VTK's GUI bindings import
#: Tk, Qt, GTK and wx, and its image utilities import Pillow, so the first freeze shipped 830 Tcl
#: data files, Tk, and Pillow's extension modules - found by the notices generator, which attributes
#: every shipped file and refused to (XC-025). None of it is reachable from the engine's surface,
#: which renders offscreen and hands bytes over HTTP; excluding it here keeps the closure to what the
#: product is, and the notices generator is what proves the exclusion held.
EXCLUDED_MODULES = (
    "tkinter", "_tkinter", "PIL",
    "vtkmodules.tk", "vtkmodules.qt", "vtkmodules.gtk", "vtkmodules.wx",
    # readline is GPL-3.0 and pulls libreadline and libtinfo into a Linux freeze; nothing in the
    # engine reads a terminal. Found by the notices generator on the first Linux run.
    "readline",
)


def freeze() -> Path:
    if DIST.exists():
        shutil.rmtree(DIST)
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--console",
        "--name", NAME,
        "--paths", str(ROOT / "src"),
        "--collect-all", "vtkmodules",
        "--collect-submodules", "service",
        "--collect-submodules", "engine",
        "--collect-submodules", "domain_core",
        "--distpath", str(DIST),
        "--workpath", str(BUILD / "pyinstaller"),
        "--specpath", str(BUILD),
        "--log-level", "WARN",
    ]
    if os.name == "nt":
        # The UTF-8 code page for every narrow-string call, so the toolkit's Exodus library takes a
        # path with Japanese in it instead of ending the process (XC-293, E-216).
        command += ["--manifest", str(ROOT / "packaging" / "engine.manifest")]
    for distribution in RUNTIME_DISTRIBUTIONS:
        command += ["--copy-metadata", distribution]
    for excluded in EXCLUDED_MODULES:
        command += ["--exclude-module", excluded]
    command.append(str(ROOT / "packaging" / "engine_entry.py"))
    started = time.perf_counter()
    subprocess.run(command, check=True, cwd=ROOT)
    seconds = time.perf_counter() - started
    executable = DIST / NAME / (NAME + (".exe" if os.name == "nt" else ""))
    if not executable.exists():
        raise SystemExit(f"PyInstaller finished but {executable} is not there")
    files = [p for p in (DIST / NAME).rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    print(json.dumps({
        "executable": str(executable),
        "files": len(files),
        "bytes": total,
        "megabytes": round(total / 1_000_000, 1),
        "freeze_seconds": round(seconds, 1),
    }, ensure_ascii=False))
    return executable


def check(executable: Path) -> int:
    """Start the frozen engine the way the shell does, and say what happened."""
    sys.path.insert(0, str(ROOT / "src"))
    from engine.code_page import CODE_PAGE_PROBE_ARGUMENT  # noqa: PLC0415 - imports nothing of the toolkit

    # Whether the manifest took: on Windows the frozen engine must be in the UTF-8 code page, or the
    # Exodus family refuses every path with Japanese in it (XC-293, E-216).
    probe = subprocess.run([str(executable), CODE_PAGE_PROBE_ARGUMENT], cwd=executable.parent, capture_output=True, text=True, encoding="utf-8")
    code_page = json.loads(probe.stdout.strip().splitlines()[-1]) if probe.stdout.strip() else {}
    print(json.dumps({"code_page": code_page}, ensure_ascii=False))
    if os.name == "nt" and not code_page.get("utf8"):
        print("the frozen engine is not in the UTF-8 code page: packaging/engine.manifest did not take (XC-293)")
        return 1
    directory = Path(tempfile.mkdtemp(prefix="solvia-frozen-"))
    connection_file = directory / "connection.json"
    started = time.perf_counter()
    process = subprocess.Popen(
        [str(executable), "--connection-directory", str(directory)],
        cwd=executable.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        while not connection_file.exists():
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                print(f"the frozen engine exited with {process.returncode} before writing its file:\n{output}")
                return 1
            if time.perf_counter() - started > 120:
                print("the frozen engine wrote no connection file within 120 s")
                return 1
            time.sleep(0.02)
        ready = time.perf_counter() - started
        connection = json.loads(connection_file.read_text(encoding="utf-8"))
        asked = time.perf_counter()
        with urllib.request.urlopen(f"http://{connection['host']}:{connection['port']}/health", timeout=10) as answer:
            health = json.loads(answer.read())
        health_ms = (time.perf_counter() - asked) * 1000
        print(json.dumps({
            "spawn_to_connection_file_s": round(ready, 3),
            "first_health_ms": round(health_ms, 1),
            "protocols": health.get("protocols"),
            "operations": health.get("operations"),
            "pid_in_file": connection.get("pid"),
        }, ensure_ascii=False))
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(directory, ignore_errors=True)


def thread(executable: Path) -> int:
    """The prototype thread (XC-257) against the frozen engine, over the wire, with no Python.

    `/health` answering proves the executable starts. It says nothing about whether the readers and
    the offscreen renderer survived freezing, which is where a frozen VTK fails when it fails: a
    shared library not collected, a reader chosen by a name nothing imported. So the same thread
    the pytest suite walks in-process is walked here through HTTP: open, load, declare, render, pick,
    export. Each step's answer is printed; the first refusal ends it.
    """
    sys.path.insert(0, str(ROOT / "tests"))
    from demo_case import write_demo_case, write_exodus  # noqa: PLC0415 - tests/ is not a package

    directory = Path(tempfile.mkdtemp(prefix="solvia-frozen-thread-"))
    workspace, cube = write_demo_case(directory / "demo")
    connection_file = directory / "connection.json"
    process = subprocess.Popen(
        [str(executable), "--connection-directory", str(directory)],
        cwd=executable.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    summary: dict[str, object] = {}
    try:
        started = time.perf_counter()
        while not connection_file.exists():
            if process.poll() is not None:
                print("the frozen engine exited before writing its file")
                return 1
            if time.perf_counter() - started > 120:
                print("no connection file within 120 s")
                return 1
            time.sleep(0.02)
        connection = json.loads(connection_file.read_text(encoding="utf-8"))
        base = f"http://{connection['host']}:{connection['port']}"
        headers = {"Content-Type": "application/json", "X-Solvia-Token": connection["token"]}

        def ask(operation: str, **parameters: object) -> dict:
            body = json.dumps({"protocol": connection["protocol"], "operation": operation, "parameters": parameters}).encode()
            request = urllib.request.Request(base + "/command", data=body, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=120) as answer:
                response = json.loads(answer.read())
            if response.get("status") not in ("applied", "answered"):
                raise RuntimeError(f"{operation}: {response.get('status')} - {response.get('reason')}")
            return response.get("result") or {}

        ask("workspace.open", path=str(workspace))
        loaded = ask("dataset.load", caseId="case:1", filePaths=[str(cube)])
        summary["fields"] = loaded.get("fields")
        dataset_id = loaded["datasetId"]
        ask("field.declareUnit", datasetId=dataset_id, fieldName="temperature", unitSymbol="K")
        statistics = ask("field.statistics", datasetId=dataset_id, fieldName="temperature")
        summary["maximum"] = statistics.get("maximum")
        view = ask("view.create", workspaceId="ws:1", definition={
            "id": "view:pending", "datasetId": dataset_id, "representation": "surface", "name": "temperature",
            "colouring": {"fieldName": "temperature", "association": "point", "colourMap": "viridis"},
        })
        rendered = ask("view.render", viewId=view["id"], width=640, height=480, format="png")
        request = urllib.request.Request(base + "/handle/" + urllib.parse.quote(rendered["handle"], safe=""), headers=headers)
        with urllib.request.urlopen(request, timeout=60) as answer:
            png = answer.read()
        summary["render"] = {"bytes": len(png), "png": png[:4] == bytes([0x89, 0x50, 0x4E, 0x47]), "reduced": rendered.get("reduced")}
        picked = ask("view.pick", viewId=view["id"], width=640, height=480, x=320, y=240)
        summary["pick"] = picked.get("value")
        report = ask("report.create", workspaceId="ws:1", definition={
            "id": "report:pending", "name": "frozen", "targets": ["html"],
            "blocks": [{"kind": "view", "viewId": view["id"], "form": "still"}, {"kind": "valueTable", "fields": ["temperature"]}],
        })
        target = directory / "frozen.html"
        exported = ask("report.export", reportId=report["id"], path=str(target))
        summary["export"] = {"bytes": exported.get("bytes"), "on_disk": target.stat().st_size if target.exists() else None}
        # An Exodus file at a path with Japanese and an emoji in it, through the frozen engine's own
        # code page (XC-293, E-216): written where the toolkit's writer can, and copied.
        plain = directory / "plain.ex2"
        write_exodus(plain)
        elsewhere = directory / "解析 結果 📐"
        elsewhere.mkdir()
        exotic = elsewhere / "ケース.ex2"
        shutil.copyfile(plain, exotic)
        loaded_there = ask("dataset.load", caseId="case:1", filePaths=[str(exotic)])
        summary["non_ascii_path"] = {"file": exotic.name, "fields": sorted(one["name"] for one in loaded_there.get("fields", []))}
        summary["ok"] = (
            bool(summary["render"]["png"])
            and summary["export"]["bytes"] == summary["export"]["on_disk"]
            and summary["non_ascii_path"]["fields"] == ["elem_stress", "stress", "temp"]
        )
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        return 0 if summary["ok"] else 1
    except Exception as error:  # noqa: BLE001 - the point is to print whatever the frozen engine did
        output = ""
        if process.poll() is not None and process.stdout:
            output = process.stdout.read()
        print(json.dumps({"ok": False, "error": str(error), "engine_output": output[-2000:]}, ensure_ascii=False, indent=1))
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(directory, ignore_errors=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="start the frozen engine and ask /health")
    parser.add_argument("--thread", action="store_true", help="walk the prototype thread against the frozen engine over HTTP")
    parser.add_argument("--no-freeze", action="store_true", help="skip freezing; check what is already built")
    arguments = parser.parse_args(argv)
    executable = (DIST / NAME / (NAME + (".exe" if os.name == "nt" else ""))) if arguments.no_freeze else freeze()
    if arguments.check and (code := check(executable)):
        return code
    if arguments.thread:
        return thread(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
