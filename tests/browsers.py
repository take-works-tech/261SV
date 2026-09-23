"""The browsers a deliverable is opened and printed in, where this machine has them (XC-309, E-228).

One place for what the two browser tests share: which browsers are looked for and how, the version
each answers with, the document a browser rendered with its scripts run, and the PDF it printed.
Chromium's two forms - Microsoft Edge and Google Chrome - are driven through their own command line
(`--dump-dom`, `--print-to-pdf`). Firefox has neither and is driven through geckodriver's WebDriver
endpoint over plain HTTP, with no library between. Nothing is downloaded to make a browser appear:
where one is absent the tests skip by name, and the set a machine has is what the gate measures
there - the development machine's Edge and Chrome, the runner's Edge, Chrome and Firefox.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

#: The browsers looked for, each by the places its installer uses and the command its package
#: registers. The product name is what the deliverable's footer says (XC-309).
CANDIDATES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Edge", "Microsoft Edge", (
        os.environ.get("EDGE_PATH", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "microsoft-edge", "microsoft-edge-stable",
    )),
    ("Chrome", "Google Chrome", (
        os.environ.get("CHROME_PATH", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    )),
    ("Firefox", "Mozilla Firefox", (
        os.environ.get("FIREFOX_PATH", ""),
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "firefox", "firefox-esr",
    )),
)

#: Firefox is driven through geckodriver; without it a Firefox found here is not driven, and the
#: skip says so.
GECKODRIVER_CANDIDATES = (os.environ.get("GECKODRIVER_PATH", ""), "geckodriver")

#: How long a page is given to finish: the probe's image load and module script, a document's font.
SETTLE_SECONDS = 5.0


def _resolve(candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if not candidate:
            continue
        resolved = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if resolved:
            return resolved
    return None


@dataclass(frozen=True)
class Browser:
    name: str        # Edge, Chrome, Firefox
    product: str     # what the deliverable's footer calls it
    executable: str
    driver: str | None = None   # geckodriver, for Firefox

    @property
    def is_chromium(self) -> bool:
        return self.name in ("Edge", "Chrome")

    def version(self) -> str:
        """The version, from the versioned folder Chromium installs beside its executable on Windows,
        or from `--version` elsewhere; `?` where neither answers. Recorded so the evidence says which
        browsers answered."""
        if sys.platform == "win32" and self.is_chromium:
            folders = sorted(one.name for one in Path(self.executable).parent.iterdir() if one.is_dir() and one.name[:1].isdigit())
            return folders[-1] if folders else "?"
        try:
            said = subprocess.run([self.executable, "--version"], capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            return "?"
        found = re.search(r"\d+(\.\d+)+", said)
        return found.group(0) if found else "?"

    def major(self) -> int | None:
        head = self.version().split(".")[0]
        return int(head) if head.isdigit() else None

    def rendered(self, url: str) -> str:
        """The document as the browser rendered it, scripts run."""
        if self.is_chromium:
            return _chromium_dom(self.executable, url)
        with _Gecko(self) as gecko:
            gecko.open(url)
            return gecko.settled_dom()

    def printed(self, url: str) -> bytes:
        """The document as the browser prints it: a PDF with no header or footer of the browser's own,
        and nothing scaled to fit - the document's own `@page` rules are what is measured."""
        if self.is_chromium:
            return _chromium_pdf(self.executable, url)
        with _Gecko(self) as gecko:
            gecko.open(url)
            gecko.settled_dom()
            return gecko.print_pdf()


def installed() -> list[Browser]:
    """Every browser this machine has that these tests can drive, in the order of CANDIDATES."""
    found: list[Browser] = []
    for name, product, candidates in CANDIDATES:
        executable = _resolve(candidates)
        if executable is None:
            continue
        if name == "Firefox":
            driver = _resolve(GECKODRIVER_CANDIDATES)
            if driver is None:
                continue
            found.append(Browser(name, product, executable, driver))
        else:
            found.append(Browser(name, product, executable))
    return found


# ---- Chromium, through its command line --------------------------------------------------------------

def _chromium_command(executable: str, profile: str) -> list[str]:
    command = [
        executable, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--disable-extensions",
        f"--user-data-dir={profile}",
    ]
    if sys.platform != "win32":
        command.insert(1, "--no-sandbox")
    return command


def _chromium_dom(executable: str, url: str) -> str:
    """What `--dump-dom` prints. A profile of its own each time: a Chromium started without one
    hands the request to a browser already running under the same profile and exits with nothing
    printed, which is what Edge did here with a window open (E-218)."""
    profile = tempfile.mkdtemp(prefix="solvia-browser-")
    command = _chromium_command(executable, profile) + ["--virtual-time-budget=5000", "--dump-dom", url]
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    assert done.returncode == 0, f"{executable} exited {done.returncode}: {done.stderr[-500:]}"
    return done.stdout


def _chromium_pdf(executable: str, url: str) -> bytes:
    profile = tempfile.mkdtemp(prefix="solvia-browser-")
    out = Path(profile) / "printed.pdf"
    command = _chromium_command(executable, profile) + ["--no-pdf-header-footer", f"--print-to-pdf={out}", url]
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        assert done.returncode == 0, f"{executable} exited {done.returncode}: {done.stderr[-500:]}"
        data = out.read_bytes()
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    assert data.startswith(b"%PDF"), "not a PDF"
    return data


# ---- Firefox, through geckodriver's WebDriver endpoint ----------------------------------------------------

class _Gecko:
    """One headless Firefox session: geckodriver started on a free port, the WebDriver calls this
    module needs - navigate, execute a script, print - as plain HTTP, and everything stopped after."""

    def __init__(self, browser: Browser) -> None:
        self.browser = browser
        self.process: subprocess.Popen[bytes] | None = None
        self.base = ""
        self.session = ""
        self.capabilities: dict[str, object] = {}

    def __enter__(self) -> _Gecko:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert self.browser.driver
        self.process = subprocess.Popen(
            [self.browser.driver, "--port", str(port), "--binary", self.browser.executable, "--log", "error"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.base = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 30
        while True:
            try:
                self._call("GET", "/status")
                break
            except (urllib.error.URLError, ConnectionError, OSError):
                if time.monotonic() > deadline:
                    self.__exit__(None, None, None)
                    raise AssertionError("geckodriver did not answer within 30 s")
                time.sleep(0.2)
        answer = self._call("POST", "/session", {"capabilities": {"alwaysMatch": {
            "browserName": "firefox",
            "moz:firefoxOptions": {"binary": self.browser.executable, "args": ["-headless"]},
        }}})
        value = answer["value"]
        self.session = str(value["sessionId"])
        self.capabilities = dict(value.get("capabilities", {}))
        return self

    def __exit__(self, *_: object) -> None:
        if self.session:
            try:
                self._call("DELETE", f"/session/{self.session}")
            except (urllib.error.URLError, ConnectionError, OSError, AssertionError):
                pass
            self.session = ""
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def _call(self, method: str, path: str, body: dict[str, object] | None = None) -> dict[str, object]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise AssertionError(f"geckodriver {method} {path}: {error.code} {error.read().decode('utf-8', 'replace')[:500]}") from None

    def version(self) -> str:
        return str(self.capabilities.get("browserVersion", "?"))

    def open(self, url: str) -> None:
        self._call("POST", f"/session/{self.session}/url", {"url": url})
        deadline = time.monotonic() + SETTLE_SECONDS
        while self.execute("return document.readyState") != "complete" and time.monotonic() < deadline:
            time.sleep(0.1)

    def execute(self, script: str, *args: object) -> object:
        return self._call("POST", f"/session/{self.session}/execute/sync", {"script": script, "args": list(args)})["value"]

    def settled_dom(self) -> str:
        """The document once it stops changing: a probe's markers arrive after the image and the
        module script, so the serialisation is taken twice and returned when the two agree."""
        deadline = time.monotonic() + SETTLE_SECONDS
        previous = ""
        while True:
            current = str(self.execute("return document.documentElement.outerHTML"))
            if current == previous or time.monotonic() > deadline:
                return current
            previous = current
            time.sleep(0.25)

    def print_pdf(self) -> bytes:
        """WebDriver's own print: no page size given, so the document's `@page` decides or the
        browser's default does - which of the two is the measurement (E-228)."""
        answer = self._call("POST", f"/session/{self.session}/print", {"background": True, "shrinkToFit": False})
        data = base64.b64decode(str(answer["value"]))
        assert data.startswith(b"%PDF"), "not a PDF"
        return data


__all__ = ["CANDIDATES", "Browser", "SETTLE_SECONDS", "installed"]
