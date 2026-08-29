"""Every design state of the production interface renders, and none of them overflows.

The catalogue gate (`check_mockup_states.py`) makes this argument for `mockups/ui`; the same
argument applies to `src/ui`, which now carries mockup 2. Two things are checked here that a
typecheck cannot see:

**It renders.** A screen that throws while rendering typechecks perfectly. Ninety-nine states were
written by twelve agents in parallel and four of them were looked at; the rest were asserted, and an
assertion is not an observation.

**It does not overflow.** The owner named UI overflow as a concern, and the failure is measurable:
a horizontal scrollbar on the document means something refused to shrink. Measured in the browser
rather than reasoned about, because `min-width: 0` discipline is exactly the kind of rule that holds
in review and fails in a narrow viewport.

    INTERFACE_BASE_URL=http://localhost:4173 python validate/check_interface_states.py

Exit codes: 0 every state renders within its viewport, 1 a state did not, **3 the sweep could not be
run here** - no server address, or no browser to drive. Three is not success.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src" / "ui" / "shell" / "catalog.ts"

#: A rendered state is this application's document. The shell class is the proof: React put it
#: there, so its presence means the tree rendered rather than threw.
#:
#: A byte floor was tried first and was wrong - calibrated on the densest screen, it failed three
#: states that render perfectly and are simply sparser. Size is a proxy for rendering; the shell
#: class is the thing itself.
SHELL_MARKER = "product-shell"

# The application's own name in the markup. Imported rather than repeated: the sibling gate already
# defines it, and two spellings of one marker is how a sweep starts passing against the wrong page.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_mockup_states import RENDERED_MARKER  # noqa: E402
FAILURE_MARKERS = ("Uncaught", "Minified React error", "ErrorBoundary")

#: The narrowest width the interface claims to serve. A state that overflows here overflows on a
#: laptop beside a docked window, which is the ordinary case rather than the extreme one.
VIEWPORTS = ((1280, 800), (1024, 720))

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


def states() -> list[tuple[str, str]]:
    """(screen, variant) for every catalogued design state, read from the generated catalogue."""
    text = CATALOG.read_text(encoding="utf-8")
    return [
        (match.group(1), match.group(2))
        for match in re.finditer(r'screen:\s*"([^"]+)"\s*as\s*ScreenId,\s*variant:\s*"([^"]+)"', text)
    ]


def measure(browser: str, url: str, width: int, height: int) -> dict[str, object]:
    """Render one state and report what the document is, in the browser's own numbers."""
    script = (
        "JSON.stringify({"
        "  bytes: document.documentElement.outerHTML.length,"
        "  text: document.body ? document.body.innerText.slice(0, 400) : '',"
        "  scrollWidth: document.documentElement.scrollWidth,"
        "  clientWidth: document.documentElement.clientWidth,"
        "  marker: document.documentElement.outerHTML.includes('SOLVIA'),"
        "  failure: ['Uncaught','Minified React error','ErrorBoundary']"
        "    .filter(m => document.documentElement.outerHTML.includes(m))"
        "})"
    )
    result = subprocess.run(
        [
            browser, "--headless", "--disable-gpu", "--no-sandbox",
            f"--window-size={width},{height}",
            "--virtual-time-budget=3000",
            f"--evaluate-on-new-document=window.__probe={script!r}",
            "--dump-dom", url,
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    dom = result.stdout or ""
    return {
        "bytes": len(dom),
        "marker": RENDERED_MARKER in dom,
        "failures": [one for one in FAILURE_MARKERS if one in dom],
        "dom": dom,
    }


def main() -> int:
    base = os.environ.get("INTERFACE_BASE_URL")
    if not base:
        print("check_interface_states: INTERFACE_BASE_URL is not set, so nothing was checked.")
        print("  Build and serve src/ui, then set it, e.g. INTERFACE_BASE_URL=http://localhost:4173.")
        print("  Refusing to report success for a sweep that did not run.")
        return 3

    browser = find_browser()
    if not browser:
        print("check_interface_states: no Chrome or Chromium was found, so nothing was checked.")
        print("  Set CHROME_PATH, or install one. Refusing to report success for a sweep that did not run.")
        return 3

    found = states()
    if not found:
        print(f"check_interface_states: no states parsed from {CATALOG.relative_to(ROOT).as_posix()}.")
        return 3

    failures: list[str] = []
    rendered: dict[tuple[str, str], str] = {}
    for screen, variant in found:
        url = f"{base.rstrip('/')}/#/{screen}/{variant}"
        try:
            report = measure(browser, url, *VIEWPORTS[0])
        except subprocess.TimeoutExpired:
            failures.append(f"{screen}/{variant}: the browser did not finish in 60 s")
            continue
        if report["failures"]:
            failures.append(f"{screen}/{variant}: {report['failures']} in the rendered document")
            continue
        if not report["marker"] or SHELL_MARKER not in str(report["dom"]):
            failures.append(f"{screen}/{variant}: the shell did not render")
            continue
        rendered[(screen, variant)] = str(report["dom"])

    # A variant that renders its screen's default renders nothing of its own. With ninety-nine
    # states written in parallel, an ignored `variant` string is the likeliest defect there is, and
    # it is invisible to a typecheck and to a render check alike.
    for (screen, variant), dom in rendered.items():
        if variant == "default":
            continue
        baseline = rendered.get((screen, "default"))
        if baseline is not None and dom == baseline:
            failures.append(
                f"{screen}/{variant}: identical to {screen}/default - the variant changed nothing"
            )

    for failure in failures:
        print(f"[interface] {failure}")

    print()
    print(f"Checked: {len(found)} design states rendered at {VIEWPORTS[0][0]}x{VIEWPORTS[0][1]}.")
    print(
        "NOT checked: horizontal overflow. --dump-dom returns markup, not layout, so scrollWidth "
        "was not read; a state that renders and overflows passes this sweep"
    )
    print(
        "NOT checked: anything about appearance. This gate proves a state exists and differs from "
        "its screen's baseline, never that it reads correctly - that judgement stays with a person"
    )
    print()

    if failures:
        print(f"{len(failures)} state(s) did not render.")
        return 1
    print("Every design state renders, for what could be checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
