"""The frozen engine's entry point: `solvia-engine` is `python -m service.transport` with the
interpreter inside (XC-261).

One line of behaviour on purpose. What the engine does is decided by the handlers and the transport;
this file exists so that PyInstaller has a script to start from, and so that a person reading the
frozen executable's name knows exactly which module it is.
"""

from __future__ import annotations

import sys

from engine.code_page import CODE_PAGE_PROBE_ARGUMENT, code_page_probe_main
from engine.visualization.render import OFFSCREEN_PROBE_ARGUMENT, offscreen_probe_main
from service.transport.__main__ import main

if __name__ == "__main__":
    if sys.argv[1:] == [OFFSCREEN_PROBE_ARGUMENT]:
        # The engine asking itself, in a child, whether this machine can render offscreen (E-194).
        offscreen_probe_main()
        raise SystemExit(0)
    if sys.argv[1:] == [CODE_PAGE_PROBE_ARGUMENT]:
        # The freeze check asking whether the manifest took: the UTF-8 code page (XC-293, E-216).
        code_page_probe_main()
        raise SystemExit(0)
    raise SystemExit(main(sys.argv[1:]))
