"""An exported document opens the same from a download, a share and a local file, in the browsers
the document names (report/AC-036, AC-046; XC-295, XC-309; #255, #256).

A deliverable arrives by mail or by download, and Windows marks such a file as from another zone
(the `Zone.Identifier` stream, "Mark of the Web"). The product's claim has to hold on the receiving
screen, so this is measured with the browsers present rather than assumed: the exported document,
and a probe carrying every kind of dependency an exported document may have - an inline classic
script, an inline module script, inline style, an image as a data URI, a font face as a data URI,
and each CSS feature the document's own stylesheet relies on - are opened from a local file, from
the same file marked as downloaded, and through a network share, and the rendered document is
compared. Where no browser is installed the test says so; the measurements it stands on are E-218
and E-228.

The browsers this proves are the ones the document itself names in its footer (`VERIFIED_BROWSERS`,
XC-309): a browser measured here has to be claimed there no newer than measured, and a browser
measured here and not claimed is said in a warning, so the claim grows only from a measurement.

What a browser without a screen cannot show is stated in E-218 too: no SmartScreen prompt, no mail
client, no double-click from a folder.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest
from conftest import requires_vtk

requires_vtk()

from browsers import Browser, installed  # noqa: E402
from engine.report.html import VERIFIED_BROWSERS  # noqa: E402
from service.command.surface import Command, Status  # noqa: E402
from test_handlers import loaded  # noqa: E402
from test_paths import administrative_share  # noqa: E402

#: A 1x1 PNG, so an image's load is a fact the page can report.
ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

PROBE = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>probe</title>
<style>
#styled {{ color: rgb(1, 2, 3); }}
@page {{ size: A4; margin: 18mm 20mm }}
@font-face {{ font-family: 'ProbeFace'; src: url(data:font/woff2;base64,AAAA) format('woff2'); font-display: block }}
#faced {{ font-family: 'ProbeFace', sans-serif }}
</style></head>
<body>
<p id="styled">style</p>
<p id="faced">face</p>
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
  // Each CSS feature the exported document's own stylesheet relies on (engine/report/html.py).
  const supports = (label, property, value) => mark(label + ":" + (CSS.supports(property, value) ? "supported" : "unsupported"));
  supports("break-inside-avoid", "break-inside", "avoid");
  supports("break-after-page", "break-after", "page");
  supports("break-after-avoid", "break-after", "avoid");
  supports("color-scheme", "color-scheme", "light dark");
  supports("tabular-nums", "font-variant-numeric", "tabular-nums");
  supports("table-header-group", "display", "table-header-group");
  mark("page-rule:" + ([...document.styleSheets[0].cssRules].some((rule) => rule instanceof CSSPageRule) ? "parsed" : "dropped"));
  document.fonts.ready.then(() => {{
    const faces = [...document.fonts].filter((face) => face.family.replace(/["']/g, "") === "ProbeFace");
    mark("font-face:" + (faces.length ? faces[0].status : "absent"));
  }});
</script>
<script type="module">document.getElementById("markers").textContent += " module:ran";</script>
</body></html>
"""

#: What every browser a deliverable is claimed in has to report from the probe.
MARKERS = ("script:ran", "style:applied", "image:loaded", "module:ran")
FEATURES = (
    "break-inside-avoid:supported", "break-after-page:supported", "break-after-avoid:supported",
    "color-scheme:supported", "tabular-nums:supported", "table-header-group:supported", "page-rule:parsed",
)
#: The probe's face is four bytes that are not a font: what is measured is that the browser took the
#: data-URI face and tried it, which ends in `error`; a real subset (AC-015) will end in `loaded`.
FONT_FACE_OUTCOMES = ("font-face:error", "font-face:loaded")


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
def present() -> list[Browser]:
    found = installed()
    if not found:
        pytest.skip("no browser this test can drive is installed here; the measurements are E-218 and E-228")
    for browser in found:
        print(f"{browser.name} {browser.version()} at {browser.executable}")
    return found


class TestTheProbeRunsEverywhereADeliverableGoes:
    """Every kind of dependency an exported document may carry, opened the three ways."""

    def test_from_a_local_file(self, tmp_path: Path, present: list[Browser]) -> None:
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        for browser in present:
            dom = browser.rendered(probe.resolve().as_uri())
            for marker in MARKERS:
                assert marker in dom, f"{browser.name}: {marker} missing from a local file"

    def test_each_feature_the_document_relies_on(self, tmp_path: Path, present: list[Browser]) -> None:
        """The stylesheet the writer emits leans on these; a browser that lacks one lays the document
        out differently, and the footer's claim would be false there (E-228)."""
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        for browser in present:
            dom = browser.rendered(probe.resolve().as_uri())
            for feature in FEATURES:
                assert feature in dom, f"{browser.name} {browser.version()}: {feature} not reported"
            assert any(outcome in dom for outcome in FONT_FACE_OUTCOMES), f"{browser.name}: the data-URI font face was not tried"

    @pytest.mark.skipif(sys.platform != "win32", reason="the zone mark is an NTFS stream")
    def test_from_a_file_marked_as_downloaded(self, tmp_path: Path, present: list[Browser]) -> None:
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        plain = {browser.name: browser.rendered(probe.resolve().as_uri()) for browser in present}
        mark_as_downloaded(probe)
        for browser in present:
            dom = browser.rendered(probe.resolve().as_uri())
            for marker in MARKERS:
                assert marker in dom, f"{browser.name}: {marker} missing from a file marked as downloaded"
            assert dom == plain[browser.name], f"{browser.name}: the marked file rendered differently from the plain one"

    def test_through_a_network_share(self, tmp_path: Path, present: list[Browser]) -> None:
        probe = tmp_path / "probe.html"
        probe.write_text(PROBE, encoding="utf-8")
        through = administrative_share(probe)
        if through is None:
            pytest.skip("no administrative share reachable here; the share measurement is E-218")
        for browser in present:
            dom = browser.rendered(through.as_uri())
            for marker in MARKERS:
                assert marker in dom, f"{browser.name}: {marker} missing through the share"


class TestTheExportedDocumentOpensTheSame:
    def test_local_marked_and_shared_render_identically(self, tmp_path: Path, present: list[Browser]) -> None:
        deliverable = a_deliverable(tmp_path)
        plain = {browser.name: browser.rendered(deliverable.resolve().as_uri()) for browser in present}
        for name, dom in plain.items():
            assert "Run 1 の最大応力" in dom and "制約" in dom and "MPa" in dom, f"{name}: the document did not render"
            assert "<script" not in dom.lower(), "this build's document carries no script; the probe above is for the one that will"
            assert "確認しています" in dom, f"{name}: the footer naming the verified browsers is missing"
        if sys.platform == "win32":
            mark_as_downloaded(deliverable)
            for browser in present:
                assert browser.rendered(deliverable.resolve().as_uri()) == plain[browser.name], f"{browser.name}: the downloaded mark changed the document"
        through = administrative_share(deliverable)
        if through is not None:
            for browser in present:
                assert browser.rendered(through.as_uri()) == plain[browser.name], f"{browser.name}: the share changed the document"


class TestTheDocumentClaimsWhatWasMeasured:
    """XC-309: the footer's list is the gate's own measurement and nothing more."""

    def test_the_footer_names_each_verified_browser_with_its_version(self, tmp_path: Path) -> None:
        text = a_deliverable(tmp_path).read_text(encoding="utf-8")
        for name, major in VERIFIED_BROWSERS:
            assert f"{name} {major}" in text
        assert "確認していません" in text, "what was not measured is said, not implied"

    def test_every_browser_measured_here_is_claimed_no_newer_than_measured(self, present: list[Browser]) -> None:
        claimed = dict(VERIFIED_BROWSERS)
        # Said as a warning so that a run's summary carries the versions it measured, whatever else
        # it prints: the runner's own set is read from there and recorded (E-228).
        warnings.warn("browsers measured here (E-228): " + "; ".join(f"{one.product} {one.version()}" for one in present), stacklevel=1)
        for browser in present:
            major = browser.major()
            if browser.product not in claimed:
                warnings.warn(
                    f"{browser.product} {browser.version()} was measured here and is not claimed in VERIFIED_BROWSERS (XC-309): "
                    "a measurement to record, then a name to add",
                    stacklevel=1,
                )
                continue
            assert major is not None, f"{browser.product}: version unknown, so the claim cannot be checked"
            assert major >= claimed[browser.product], (
                f"{browser.product} {major} measured here is older than the {claimed[browser.product]} the document claims; "
                "the claim is the oldest version measured, so lower it"
            )
