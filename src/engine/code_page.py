"""The code page this engine process handles narrow strings in (XC-293, E-216).

A Windows process takes narrow-string paths in its active code page. Under the ANSI page of a
Japanese desktop (932) the toolkit's Exodus library, handed a path with a character outside that
page, ends the process; under the UTF-8 page (65001) - what `packaging/engine.manifest` gives the
frozen engine - it reads and writes there. This module is the one place that fact is asked, and it
imports nothing of the toolkit, so the frozen engine can answer `--code-page-probe` before it loads
anything. Elsewhere than Windows there is no code page to ask about, and the answer is None.
"""

from __future__ import annotations

import json
import sys

#: The code page a process handles narrow strings in when it is UTF-8: the one the frozen engine's
#: manifest declares (`activeCodePage`), honoured by Windows 10 1903 and later.
UTF8_CODE_PAGE = 65001

#: The argument the frozen engine answers with its code page, for the freeze check (XC-261).
CODE_PAGE_PROBE_ARGUMENT = "--code-page-probe"


def active_code_page() -> int | None:
    """The code page this process's narrow-string calls are in, on Windows; None elsewhere."""
    if sys.platform != "win32":
        return None
    import ctypes

    return int(ctypes.windll.kernel32.GetACP())


def code_page_probe_main() -> None:
    """Print the code page as one JSON line, for a caller that started this process to ask."""
    page = active_code_page()
    print(json.dumps({"activeCodePage": page, "utf8": page == UTF8_CODE_PAGE}))
