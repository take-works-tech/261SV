"""How a workspace document behaves as its cases grow (#238, LIM-005, OPEN-008).

Builds a document holding N cases of a realistic shape - a two-level tree of sweeps, each case with a
tag and one recorded source - and measures at each N what the product does with it: `save` (the
bytes on disk and the time), `load` (the time and the peak allocation), `workspace.open` through the
command surface (the time, which resolves every recorded source against the disk, and the size of
the `cases` answer the interface is sent), `workspace.save` through the surface, and the cost of
adding one more case through `hierarchy.add`, which walks the tree to check the identifier. Then it
adds cases one at a time up to smaller sizes, which is what a script or a sweep does: that path is
quadratic, and the number says whether it matters below the cap LIM-005 draws.

Prints one JSON object and merges it into results.json under `workspace_cases`. Run in the engine
environment: `python spike/measure_workspace_cases.py [sizes...]`. The numbers are of this machine on
this day, with a warm cache and the recorded files absent (their resolution is the stat of an absent
path); the interface's tree is measured on its own side (src/ui/logic/subject.scale.test.ts).
"""
from __future__ import annotations

import json
import platform
import shutil
import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from service.command.surface import Command, Status  # noqa: E402
from service.workspace import hierarchy  # noqa: E402
from service.workspace.document import FORMAT_VERSION, WorkspaceDocument, load, save  # noqa: E402
from test_handlers import a_surface  # noqa: E402

HERE = Path(__file__).resolve().parent
PER_SWEEP = 10


def case_of(index: int) -> dict[str, object]:
    """One case as the product records it: a name, a tag, one source with its size and time."""
    return {
        "id": f"case:{index:05d}",
        "name": f"荷重 {100 + index} N",
        "tags": ["静荷重"] if index % 2 else ["熱"],
        "children": [],
        "sources": [{
            "pathRelative": f"runs/case-{index:05d}/result.vtu",
            "sizeBytes": 1_234_567,
            "modified": {"utc": "2026-09-22T00:00:00Z", "offsetMinutes": 540},
        }],
    }


def cases_with(count: int) -> list[dict[str, object]]:
    """A two-level tree: every tenth case is a sweep with the nine after it beneath, which is the
    shape a parameter study takes and what the tree has to draw."""
    roots: list[dict[str, object]] = []
    for index in range(count):
        case = case_of(index)
        if index % PER_SWEEP == 0 or not roots:
            roots.append(case)
        else:
            roots[-1]["children"].append(case)  # type: ignore[union-attr]
    return roots


def document_with(count: int) -> dict[str, object]:
    return {
        "formatVersion": FORMAT_VERSION, "id": "ws:1", "name": "ケース数の計測",
        "cases": cases_with(count), "variables": [],
        "workspaceItems": {"simulations": [], "views": [], "graphs": [], "reports": []},
    }


def timed(action, repeats: int = 3) -> tuple[float, object]:
    """The median wall time in milliseconds over `repeats` runs, and the last result."""
    times: list[float] = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = action()
        times.append((time.perf_counter() - started) * 1000)
    return round(statistics.median(times), 1), result


def measure_size(count: int, directory: Path) -> dict[str, object]:
    document = document_with(count)
    path = directory / f"cases-{count}.svw"
    save_ms, _ = timed(lambda: save(WorkspaceDocument(raw=document), path))
    file_bytes = path.stat().st_size
    tracemalloc.start()
    load_ms, _ = timed(lambda: load(path))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def open_fresh():
        surface, _ = a_surface()
        return surface.submit(Command("workspace.open", {"path": str(path)}))

    open_ms, opened = timed(open_fresh)
    assert opened.status is Status.APPLIED, opened.reason
    answer_bytes = len(json.dumps(opened.value["cases"], ensure_ascii=False).encode("utf-8"))
    surface, _ = a_surface()
    assert surface.submit(Command("workspace.open", {"path": str(path)})).status is Status.APPLIED
    save_command_ms, saved = timed(lambda: surface.submit(Command("workspace.save", {"workspaceId": "ws:1"})))
    assert saved.status is Status.APPLIED, saved.reason

    # One more case into the loaded tree: the walk over everything already there.
    def one_more() -> None:
        working = json.loads(json.dumps(document["cases"]))
        try:
            hierarchy.add(working, hierarchy.new_case("case:added", "追加のケース"))
        except hierarchy.HierarchyError:
            pass  # past LIM-005 the add is refused, which costs the same walk

    copy_ms, _ = timed(lambda: json.loads(json.dumps(document["cases"])))
    add_ms, _ = timed(one_more)
    return {
        "cases": count,
        "file_bytes": file_bytes,
        "save_ms": save_ms,
        "load_ms": load_ms,
        "load_peak_mb": round(peak / 1_000_000, 1),
        "open_command_ms": open_ms,
        "open_cases_answer_bytes": answer_bytes,
        "open_warnings": [one[:60] for one in (opened.warnings or ())],
        "save_command_ms": save_command_ms,
        "add_one_more_ms": round(max(add_ms - copy_ms, 0.0), 2),
    }


def measure_sequential(count: int) -> dict[str, object]:
    """Adding `count` cases one at a time, as a sweep or a script does. Past LIM-005 the add is
    refused; the walk that refuses costs what the walk that adds would."""
    cases: list[dict[str, object]] = []
    started = time.perf_counter()
    last_ms = 0.0
    refused = 0
    for index in range(count):
        one = time.perf_counter()
        try:
            hierarchy.add(cases, hierarchy.new_case(f"case:{index:05d}", f"荷重 {100 + index} N"))
        except hierarchy.HierarchyError:
            refused += 1
        last_ms = (time.perf_counter() - one) * 1000
    return {
        "cases": count,
        "total_s": round(time.perf_counter() - started, 2),
        "last_add_ms": round(last_ms, 3),
        "refused_past_limit": refused,
    }


def main(argv: list[str]) -> int:
    sizes = [int(one) for one in argv] or [100, 500, 1_000, 5_000, 20_000]
    directory = Path(tempfile.mkdtemp(prefix="solvia-wscases-"))
    try:
        record: dict[str, object] = {
            "measured": time.strftime("%Y-%m-%d"),
            "script": "spike/measure_workspace_cases.py",
            "machine": f"{platform.system()} {platform.release()}, Python {platform.python_version()}, warm cache",
            "case_shape": (
                "a two-level tree of sweeps, ten cases each; every case named, tagged, and carrying one "
                "recorded source whose file is absent, so `workspace.open` resolves it by one stat of an "
                "absent path"
            ),
            "sizes": [measure_size(count, directory) for count in sizes],
            "sequential_add": [measure_sequential(count) for count in (500, 1_000, 2_000, 5_000)],
            "not_measured": (
                "a first open from a cold disk; recorded files that are present (a stat each, as here, "
                "plus the size and time compared); the interface drawing the tree, measured on its own "
                "side in src/ui/logic/subject.scale.test.ts"
            ),
        }
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    results_path = HERE / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results["workspace_cases"] = record
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
