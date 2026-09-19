"""How a workspace document behaves as it grows: read, write, the open answer, and one more item (#316).

Builds a document holding N concrete items of a realistic shape - views over a dataset, graphs with
series, reports with blocks, in equal parts - and measures at each N what the product does with it:
`save` (the bytes on disk and the time), `load` (the time and the peak allocation), the `items`
answer `workspace.open` sends to the interface (its serialised size), and the cost of creating one
more item through `items.create`, which walks the whole document to check the name and the
identifier (`naming.registry_of`). Then it creates items one at a time up to smaller sizes, which is
what a script or a loop does: that path is quadratic, and the number says whether it matters below
the cap LIM-016 draws.

Prints one JSON object and merges it into results.json under `workspace_document`. Run in the engine
environment: `python spike/measure_workspace_document.py [sizes...]`. The numbers are of this machine
on this day, with a warm cache; a first open from a cold disk is slower and is not measured here.
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

from service.command.handlers import items_of  # noqa: E402
from service.workspace import items  # noqa: E402
from service.workspace.document import FORMAT_VERSION, WorkspaceDocument, load, save  # noqa: E402

HERE = Path(__file__).resolve().parent
KINDS = ("views", "graphs", "reports")
COMMENTARY = (
    "最大主応力は固定端近傍の角に集中し、メッシュを一段細かくしても 3 % 以内で収束した。"
    "平均化前後の差は 12 % で、これは要素サイズに対する応力勾配の比から予想される範囲にある。"
)


def definition_of(kind: str, index: int) -> dict[str, object]:
    """One item of each kind, with the fields a real definition carries (CT-004, CT-005, CT-006)."""
    name = f"{kind}-{index:06d}"
    if kind == "views":
        return {
            "id": f"view:{index:06d}", "name": name, "datasetId": "dataset:0001",
            "fieldName": "von_mises", "representation": "surface",
            "colorMap": {"name": "viridis", "range": [0.0, 250.0]},
            "camera": {"position": [1.2, -2.4, 1.6], "focalPoint": [0.0, 0.0, 0.1], "viewUp": [0.0, 0.0, 1.0]},
            "legend": {"visible": True, "title": "応力 [MPa]", "digits": 3},
        }
    if kind == "graphs":
        return {
            "id": f"graph:{index:06d}", "name": name,
            "series": [
                {"caseId": "case:1", "x": "time", "y": "displacement", "label": f"系列 {n}"} for n in range(3)
            ],
            "axes": {"x": {"label": "時間 [s]", "scale": "linear"}, "y": {"label": "変位 [mm]", "scale": "linear"}},
        }
    return {
        "id": f"report:{index:06d}", "name": name, "targets": ["html"],
        "blocks": [
            {"type": "heading", "text": f"梁の検討 {index}"},
            {"type": "view", "viewId": f"view:{index:06d}"},
            {"type": "table", "fieldName": "von_mises", "statistics": ["min", "max", "mean"]},
            {"type": "commentary", "text": COMMENTARY},
        ],
    }


def document_with(count: int) -> dict[str, object]:
    """A document with `count` items spread over the three collections, built directly rather than
    through `items.create`, so the size can be reached in milliseconds; the create path is measured
    separately, because it is the slow one."""
    held: dict[str, list[dict[str, object]]] = {kind: [] for kind in KINDS}
    held["simulations"] = []
    for index in range(count):
        kind = KINDS[index % len(KINDS)]
        definition = definition_of(kind, index)
        held[kind].append({"id": definition["id"], "name": definition["name"], "definition": definition})
    return {
        "formatVersion": FORMAT_VERSION, "id": "ws:scale", "name": "規模の計測",
        "cases": [{"id": "case:1", "name": "baseline", "children": [], "sources": []}],
        "variables": [], "workspaceItems": held,
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
    path = directory / f"scale-{count}.svw"

    save_ms, _ = timed(lambda: save(WorkspaceDocument(raw=document), path))
    file_bytes = path.stat().st_size

    tracemalloc.start()
    load_ms, loaded = timed(lambda: load(path))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    answer_ms, answer = timed(lambda: items_of(loaded))
    answer_bytes = len(json.dumps(answer, ensure_ascii=False).encode("utf-8"))

    # One more item into the loaded document: the registry walk over everything already there.
    def one_more() -> None:
        working = json.loads(json.dumps(document))
        items.create(working, "views", "view:added", "追加のビュー", definition_of("views", count + 1))

    copy_ms, _ = timed(lambda: json.loads(json.dumps(document)))
    create_ms, _ = timed(one_more)

    return {
        "items": count,
        "file_bytes": file_bytes,
        "save_ms": save_ms,
        "load_ms": load_ms,
        "load_peak_mb": round(peak / 1_000_000, 1),
        "open_answer_bytes": answer_bytes,
        "open_answer_ms": answer_ms,
        "create_one_more_ms": round(max(create_ms - copy_ms, 0.0), 1),
    }


def measure_sequential(count: int) -> dict[str, object]:
    """Creating `count` items one at a time through the create path, as a loop or a script does."""
    document = document_with(0)
    started = time.perf_counter()
    last_ms = 0.0
    for index in range(count):
        kind = KINDS[index % len(KINDS)]
        definition = definition_of(kind, index)
        one = time.perf_counter()
        items.create(document, kind, str(definition["id"]), str(definition["name"]), definition)
        last_ms = (time.perf_counter() - one) * 1000
    return {
        "items": count,
        "total_s": round(time.perf_counter() - started, 2),
        "last_create_ms": round(last_ms, 2),
    }


def main(argv: list[str]) -> int:
    sizes = [int(one) for one in argv] or [100, 1_000, 10_000, 100_000]
    directory = Path(tempfile.mkdtemp(prefix="solvia-wsdoc-"))
    try:
        record: dict[str, object] = {
            "measured": time.strftime("%Y-%m-%d"),
            "script": "spike/measure_workspace_document.py",
            "machine": f"{platform.system()} {platform.release()}, Python {platform.python_version()}, warm cache",
            "item_shape": (
                "views, graphs and reports in equal parts over one case; each carries a definition of the "
                "shape CT-004 to CT-006 describe (a camera and a colour map, three series with axes, four "
                "report blocks with a commentary)"
            ),
            "sizes": [measure_size(count, directory) for count in sizes],
            "sequential_create": [measure_sequential(count) for count in (1_000, 2_000, 5_000, 10_000)],
            "not_measured": (
                "a first open from a cold disk; the interface rendering the lists it is sent; a document with "
                "hundreds of cases beside the items (LIM-005 is measured separately when it is)"
            ),
        }
    finally:
        # Its own directory goes with the run (E-208).
        shutil.rmtree(directory, ignore_errors=True)

    results_path = HERE / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results["workspace_document"] = record
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
