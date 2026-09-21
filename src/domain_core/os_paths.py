"""A path as the operating system takes it, and as a person reads it (XC-294, E-217).

Windows stops at 260 characters unless a program asks otherwise, and a folder on a Japanese desktop
gets there with no wrongdoing: a user's name, a project, a study, a run, a step. The policy that lifts
the limit is off by default and an administrator's to set, so this product lifts it for itself: a
path longer than the limit is handed to the operating system - and to every library, which was
measured to take it - in the **extended-length form** `\\\\?\\C:\\...`. That form is a wire detail of
the call, never a name: what a document records and an answer carries is the plain path, and
`for_people` is the inverse that makes it so. Elsewhere than Windows both functions are the identity.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

#: Where the extended form starts to be needed: MAX_PATH (260) less the twelve characters Windows
#: keeps for an 8.3 name when a directory is created - the documented bound of CreateDirectoryW,
#: and so the bound below which every plain path is safe (E-217).
WINDOWS_PATH_LIMIT = 260 - 12

_PREFIX = "\\\\?\\"
_UNC_PREFIX = "\\\\?\\UNC\\"


def for_os(path: str | Path) -> Path:
    """The path to hand to the operating system: extended-length on Windows where the plain
    absolute form is longer than the limit, and the plain absolute form otherwise. Idempotent."""
    text = os.fspath(path)
    if sys.platform != "win32":
        return Path(text)
    if text.startswith(_PREFIX):
        return Path(text)
    absolute = os.path.abspath(text)
    if len(absolute) <= WINDOWS_PATH_LIMIT:
        return Path(absolute)
    if absolute.startswith("\\\\"):
        return Path(_UNC_PREFIX + absolute[2:])
    return Path(_PREFIX + absolute)


def for_people(path: str | Path) -> Path:
    """The path as a document records it and an answer states it: the extended prefix removed."""
    text = os.fspath(path)
    if text.startswith(_UNC_PREFIX):
        return Path("\\\\" + text[len(_UNC_PREFIX):])
    if text.startswith(_PREFIX):
        return Path(text[len(_PREFIX):])
    return Path(text)
