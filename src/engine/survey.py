"""What a path contains, before anything is read into memory.

A @Case may be one file, a manifest naming pieces, or a directory of numbered steps (GL-002), and the
interface has to be able to say which and how many before the load (ingest/AC-026). Surveying is
therefore separate from reading: it answers "what is here" from names and manifests, and `reader.read`
answers "what is in it".

**No VTK here, deliberately.** The manifest is XML and the series is filenames, so this is stdlib work -
and it is then verifiable on a machine with no engine environment, which is where it was written. The
piece manifest is read here rather than taken from the toolkit for one reason: to report a *missing*
part (AC-027) this product has to know what the file **claimed**, and a reader that returns the pieces
it managed to open cannot tell you about the one it did not.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

from domain_core.case_contents import AxisKind, CaseContents, ResultAxis

# A trailing run of digits, with the separator that usually precedes it. `case_0007.vtu` and
# `case.0007.vtu` are both a seventh step of `case`; `mesh2d.vtu` is not a step of `mesh`, which is why
# the separator is required rather than optional.
_STEP_SUFFIX = re.compile(r"^(?P<stem>.+?)[._-](?P<index>\d+)$")


def _pieces(manifest: Path) -> tuple[list[str], list[str]]:
    """The piece files a `.pvtu` names, split into those present and those absent.

    A piece with no `Source` is a malformed manifest, and it is reported as a missing part rather than
    skipped: the file said there was a piece there.
    """
    root = ElementTree.parse(manifest).getroot()
    present: list[str] = []
    absent: list[str] = []
    for piece in root.iter("Piece"):
        source = piece.get("Source")
        if not source:
            absent.append("<Piece> with no Source attribute")
            continue
        (present if (manifest.parent / source).exists() else absent).append(source)
    return present, absent


def _series_members(path: Path) -> list[Path]:
    """Files that are numbered steps of the same stem as `path`, in numeric order.

    Returns an empty list when `path` is not part of a numbered series, so a single file stays a single
    file rather than becoming a one-step series by another name.
    """
    match = _STEP_SUFFIX.match(path.stem)
    if match is None:
        return []
    stem, suffix = match.group("stem"), path.suffix
    numbered: list[tuple[int, Path]] = []
    for sibling in path.parent.glob(f"{stem}*{suffix}"):
        found = _STEP_SUFFIX.match(sibling.stem)
        if found and found.group("stem") == stem:
            numbered.append((int(found.group("index")), sibling))
    return [member for _, member in sorted(numbered)]


def survey(path: str | Path) -> CaseContents:
    """How many steps and parts this path holds, and what indexes the steps.

    Nothing here converts an ordinal into a value: a directory of numbered files declares an order and
    not a time, so the axis comes back `UNDECLARED` with no positions until a format that declares one
    is read (GL-036, E-130).
    """
    location = Path(path)

    if location.suffix.lower() == ".pvtu":
        present, absent = _pieces(location)
        return CaseContents(
            steps=1,
            parts=max(len(present), 1),
            axis=ResultAxis(AxisKind.NONE),
            missing_parts=tuple(absent),
        )

    members = _series_members(location)
    if len(members) > 1:
        return CaseContents(
            steps=len(members),
            parts=1,
            axis=ResultAxis(AxisKind.UNDECLARED),
        )

    return CaseContents(steps=1, parts=1, axis=ResultAxis(AxisKind.NONE))
