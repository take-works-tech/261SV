"""Every catalogue state renders.

The mockup CI job typechecks the catalogue, which catches a reference to a component that does not
exist and catches nothing about a state that throws while rendering. That gap did not matter while a
person ran the sweep before every push; it matters the moment a workflow is allowed to merge on CI's
word (XC-218), because CI is then the only thing between a change and `main`.

**This drives a browser, not an HTTP client.** The catalogue is client-rendered: fetching a state over
HTTP returns the same 6 KB shell for all of them, so a check built on `urllib` passes while every state
throws. Written that way first, and caught by running it - the whole point of the gate is the render.

    MOCKUP_BASE_URL=http://localhost:3000 python validate/check_mockup_states.py

Exit codes: 0 every state renders, 1 a state did not, **3 the sweep could not be run here** - no server
address, or no browser to drive. Three is not success: `.githooks/pre-push` reports it as skipped rather
than silently passing, and in CI - which starts the server and where Chrome is installed - it is a
failure like any other, because a sweep CI stopped running is exactly what this gate exists to prevent.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "mockups" / "ui" / "lib" / "screen-catalog.json"

# A rendered state is a full document, and it is *this* application's document. The size floor alone is
# not enough: Chrome's own network-error page is 187 KB, so a sweep run against a server that never
# started reported all 88 states green. Measured, not reasoned about - it is why the marker is here.
MINIMUM_DOCUMENT_BYTES = 20_000
RENDERED_MARKER = "SOLVIA"
FAILURE_MARKERS = ("client-side exception", "Application error", "__NEXT_ERROR")

BROWSER_CANDIDATES = (
    os.environ.get("CHROME_PATH"),
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)


def find_browser() -> str | None:
    for candidate in BROWSER_CANDIDATES:
        if not candidate:
            continue
        found = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if found:
            return found
    return None


def render(browser: str, url: str) -> tuple[str, str | None]:
    """The DOM after the page has run, or the reason it could not be obtained."""
    try:
        result = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=6000", "--dump-dom", url],
            # The DOM is UTF-8 and this runs on a machine whose console is cp932; decoding it with
            # the locale's codec raises on the first Japanese label. Named, not left to the default.
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
        )
    except subprocess.TimeoutExpired:
        return "", "the browser did not finish within 90 s"
    if result.returncode != 0:
        return "", f"the browser exited {result.returncode}"
    return result.stdout, None


def main() -> int:
    base = os.environ.get("MOCKUP_BASE_URL")
    if not base:
        print("check_mockup_states: MOCKUP_BASE_URL is not set, so nothing was checked.")
        print("  Start the built mockup and set it, e.g. MOCKUP_BASE_URL=http://localhost:3000.")
        print("  Refusing to report success for a sweep that did not run.")
        return 3

    browser = find_browser()
    if browser is None:
        print("check_mockup_states: no Chrome or Chromium found, so nothing was checked.")
        print("  Set CHROME_PATH, or install one. The states are client-rendered, so an HTTP fetch")
        print("  returns the same empty shell for every one of them and would check nothing.")
        return 3

    scenarios = json.loads(CATALOG.read_text(encoding="utf-8"))["scenarios"]
    findings: list[str] = []
    for scenario in scenarios:
        url = f"{base.rstrip('/')}/?screen={scenario['screen']}&variant={scenario['variant']}"
        body, error = render(browser, url)
        if error:
            findings.append(f"{scenario['id']}: {error}")
            continue
        if RENDERED_MARKER not in body:
            findings.append(f"{scenario['id']}: the document is not this application - no {RENDERED_MARKER!r} in it")
            # The first state already says there is nothing to sweep. Eighty-seven more browser launches
            # against the same address add no information and take four minutes to say so.
            if scenario is scenarios[0]:
                print(f"[mockup state] {findings[0]}")
                print()
                print(f"Stopped at the first state: {base} is not serving this application.")
                return 1
        elif len(body) < MINIMUM_DOCUMENT_BYTES:
            findings.append(f"{scenario['id']}: {len(body)} bytes, below the {MINIMUM_DOCUMENT_BYTES} floor")
        for marker in FAILURE_MARKERS:
            if marker in body:
                findings.append(f"{scenario['id']}: rendered an error containing {marker!r}")

    if findings:
        for finding in findings:
            print(f"[mockup state] {finding}")
        print(f"\n{len(findings)} finding(s) across {len(scenarios)} states.")
        return 1
    print(f"All {len(scenarios)} catalogue states render, driven through {Path(browser).name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
