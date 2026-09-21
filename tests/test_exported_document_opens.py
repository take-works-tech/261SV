"""An exported document opens the same from a download, a share and a local file (report/AC-036,
XC-295; #255).

A deliverable arrives by mail or by download, and Windows marks such a file as from another zone
(the `Zone.Identifier` stream, "Mark of the Web"). The product's claim has to hold on the receiving
screen, so this is measured with the browsers present rather than assumed: the exported document,
and a probe carrying every kind of dependency an exported document may have - an inline classic
script, an inline module script, inline style, an image as a data URI - are opened from a local file,
from the same file marked as downloaded, and through a network share, and the rendered document is
compared. Where no browser is installed the test says so; the measurement it stands on is E-218.

What a browser without a screen cannot show is stated in E-218 too: no SmartScreen prompt, no mail
client, no double-click from a folder.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

from service.command.surface import Command, Status  # noqa: E402
from test_handlers import loaded  # noqa: E402
from test_paths import administrative_share  # noqa: E402

#: The browsers a deliverable is opened in, where this machine has them. Chromium's two Windows
#: forms and their Linux commands; nothing is downloaded to make one appear.
CANDIDATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Edge", (
        os.environ.get("EDGE_PATH", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "microsoft-edge", "microsoft-edge-stable",
    )),
    ("Chrome", (
        os.environ.get("CHROME_PATH", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    )),
)

#: A 1x1 PNG, so an image's load is a fact the page can report.
ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

PROBE = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>probe</title>
<style>#styled {{ color: rgb(1, 2, 3); }}</style></head>
<body>
<p id="styled">style</p>
<p id="markers"></p>
<img id="picture" src="data:image/png;base64,{ONE_PIXEL_PNG}" alt="one pixel">
<script>
  const markers = document.getElementById("markers");
  const mark = (what) => {{ markers.textContent += " " + what; }};
  mark("script:ran");
  if (getComputedStyle(document.getElementById("styled")).color === "rgb(1, 2, 3)") mark("style:applied");
  const picture = document.getElementById("picture");
  const picked = () => mark(picture.naturalWidth === 1 ? "image:loaded" : "image:empty");
  if (picture.complete) picked(); else picture.addEventListener("load", picked);
</script>
<script type="module">document.getElementById("markers").textContent += " module:ran";</script>
</body></html>
"""

MARKERS = ("script:ran", "style:applied", "image:loaded", "module:ran")


def browsers() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for name, candidates in CANDIDATES:
        for candidate in candidates:
            if not candidate:
                continue
            resolved = candidate if Path(candidate).is_file() else shutil.which(candidate)
            if resolved:
                found.append((name, resolved))
                break
    return found


def version_of(executable: str) -> str:
    """The version, from the versioned folder Chromium installs beside its executable on Windows, or
    from `--version` elsewhere. Recorded so E-218 says which browsers answered."""
    if sys.platform == "win32":
        folders = sorted(one.name for one in Path(executable).parent.iterdir() if one.is_dir() and one.name[:1].isdigit())
        return folders[-1] if folders else "?"
    try:
        return subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "?"


def rendered(executable: str, url: str) -> str:
    """The document as the browser rendered it, scripts run - what `--dump-dom` prints.

    A profile of its own each time: a Chromium started without one hands the request to a browser
    already running under the same profile and exits with nothing printed, which is what Edge did
    here with a window open."""
    profile = tempfile.mkdtemp(prefix="solvia-browser-")
    command = [
        executable, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--disable-extensions",
        f"--user-data-dir={profile}", "--virtual-time-budget=5000", "--dump-dom", url,
    ]
    if sys.platform != "win32":
        command.insert(1, "--no-sandbox")
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    assert done.returncode == 0, f"{executable} exited {done.returncode}: {done.stderr[-500:]}"
    return done.stdout


def mark_as_downloaded(path: Path) -> None:
    """The mark Windows puts on a file that came from the Internet zone: what a download, a mail
    attachment saved to disk and a file copied from such a file carry (E-218)."""
    with open(str(path) + ":Zone.Identifier", "w", encoding="ascii", newline="") as stream:
        stream.write("[ZoneTransfer]\r\nZoneId=3\r\n")
    assert Path(str(path) + ":Zone.Identifier").read_text(encoding="ascii").startswith("[ZoneTransfer]")


def a_deliverable(tmp_path: Path) -> Path:
    surface, _, dataset_id = loaded(tmp_path)
    surface.submit(Command("field.declareUnit", {"datasetId": dataset_id, "fieldName": "stress", "unitSymbol": "MPa"}))
    created = surface.submit(Command("report.create", {"workspaceId": "ws:1", "definition": {
        "name": "Run 1 の最大応力", "targets": ["html"],
        "blocks": [{"kind": "text", "text": "梁の基本ケース。"}, {"kind": "valueTable", "fields": ["stress"]}],
    }}))
    assert created.status is Status.APPLIED, created.reason
    target = tmp_path / "run1.html"
    exported = surface.submit(Command("report.export", {"reportId": created.value["id"], "path": str(target)}))
    assert exported.status is Status.APPLIED, exported.reason
    return target


@pytest.fixture(scope="module")
def present() -> list[tuple[str, str]]:
    found = browsers()
    if not found:
        pytest.skip("no Chromium browser is installed here; the measurement is E-218, taken with Edge and Chrome")
    for name, executable in found:
        print(f"{name} {version_of(executable)} at {executable}")
    return found


class TestTheProbeRunsEverywhereADeliverableGoes:
    """Every kind of dependency an exported document may carry, opened the three ways."""

    def test_from_a_local_file(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        for name, executable in present:
            dom = rendered(executable, probe.resolve().as_uri())
            for marker in MARKERS:
                assert marker in dom, f"{name}: {marker} missing from a local file"

    @pytest.mark.skipif(sys.platform != "win32", reason="the zone mark is an NTFS stream")
    def test_from_a_file_marked_as_downloaded(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        plain = {name: rendered(executable, probe.resolve().as_uri()) for name, executable in present}
        mark_as_downloaded(probe)
        for name, executable in present:
            dom = rendered(executable, probe.resolve().as_uri())
            for marker in MARKERS:
                assert marker in dom, f"{name}: {marker} missing from a file marked as downloaded"
            assert dom == plain[name], f"{name}: the marked file rendered differently from the plain one"

    def test_through_a_network_share(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        through = administrative_share(probe)
        if through is None:
            pytest.skip("no administrative share reachable here; the share measurement is E-218")
        for name, executable in present:
            dom = rendered(executable, through.as_uri())
            for marker in MARKERS:
                assert marker in dom, f"{name}: {marker} missing through the share"


class TestTheExportedDocumentOpensTheSame:
    def test_local_marked_and_shared_render_identically(self, tmp_path: Path, present: list[tuple[str, str]]) -> None:
        deliverable = a_deliverable(tmp_path)
        plain = {name: rendered(executable, deliverable.resolve().as_uri()) for name, executable in present}
        for name, dom in plain.items():
            assert "Run 1 の最大応力" in dom and "制約" in dom and "MPa" in dom, f"{name}: the document did not render"
            assert "<script" not in dom.lower(), "this build's document carries no script; the probe above is for the one that will"
        if sys.platform == "win32":
            mark_as_downloaded(deliverable)
            for name, executable in present:
                assert rendered(executable, deliverable.resolve().as_uri()) == plain[name], f"{name}: the downloaded mark changed the document"
        through = administrative_share(deliverable)
        if through is not None:
            for name, executable in present:
                assert rendered(executable, through.as_uri()) == plain[name], f"{name}: the share changed the document"
