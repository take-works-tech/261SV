"""The saved form of a @Workspace: reading it without losing anything, writing it without risking it.

Two properties do the work here, and both are structural rather than careful.

**Nothing is dropped, at any depth.** CT-001's strictness is that unknown fields are *preserved* - not
rejected, not silently discarded. The contract sets out why the third option is the only one that
survives a user with two machines on two versions, which is the normal case for a desktop product. So
this holds the document as **the parsed mapping itself** and reads through it, rather than unpacking
into typed fields and repacking on save. Unpacking is how a field nobody wrote an attribute for
disappears, and it disappears silently, in a file the user believes they saved.

**The only copy is never absent.** A save writes a temporary file beside the target, and only then moves
the existing file aside and the new one into place. Between those two moves the data exists twice - once
as the previous version and once as the temporary - and at no point zero times. XC-055 requires the
previous good version to be kept beside the new one; this is that requirement as a sequence of renames
rather than as an intention.

A damaged file is **never written to**. Loading opens read-only and reports what could not be read, so
the bytes on disk after a failed open are the bytes that were there before (workspace/AC-013).

Specification: CT-001, XC-055, workspace/AC-011, AC-012, AC-013.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any

#: What this build writes. A document declaring a **newer major** may be opened - every field it holds
#: is kept - and may not be written back under this version, because writing it would mean claiming to
#: understand a shape that changed (CT-001 compatibility).
FORMAT_VERSION = "5.0.0"

#: The major this build lifts to its own on open. Version 4 wrote a source's modification time and a
#: variable's detachment time as bare UTC strings (`modifiedIso`, `detachedIso`); version 5 writes
#: every recorded time as `{utc, offsetMinutes}` (XC-266), and a time version 4 wrote gets a null
#: offset - unknown, not zero (XC-001). Version 3 is not lifted by this build, as before.
LIFTED_MAJOR = 4

#: The fields CT-001 requires. Their absence is a damaged document rather than an old one: a file
#: without `cases` is not a workspace missing a feature, it is not a workspace.
REQUIRED_FIELDS = ("formatVersion", "id", "cases", "variables", "workspaceItems")

#: The previous good version, kept beside the file it replaced. A suffix rather than a hidden directory
#: so that XC-055's restore procedure - "a file operation the user can perform without the product" -
#: is one a user can actually find.
PREVIOUS_SUFFIX = ".previous"


class WorkspaceFileError(Exception):
    """Raised when a document cannot be read. Says what could not be read, and touches nothing."""


class WorkspaceVersionError(Exception):
    """Raised when this build is asked to write a document whose shape it does not own."""


def _major(version: str) -> int:
    try:
        return int(str(version).split(".", 1)[0])
    except (ValueError, AttributeError):
        raise WorkspaceFileError(
            f"formatVersion {version!r} is not a version this product can compare against "
            f"{FORMAT_VERSION}; refusing to guess whether it is older or newer"
        ) from None


@dataclass(slots=True)
class WorkspaceDocument:
    """One saved workspace, held as what was read rather than as what this build understands."""

    #: The parsed document, entire. Typed access goes through the properties below; everything else
    #: rides along untouched, which is the whole of "unknown fields are preserved".
    raw: dict[str, Any] = dataclass_field(default_factory=dict)
    #: Where it was read from, where one exists. A document built in memory has none.
    origin: Path | None = None
    #: The version the file declared where this build lifted it to its own on open, so the open can
    #: say so; None where the file was already this build's shape.
    migrated_from: str | None = None

    @property
    def format_version(self) -> str:
        return str(self.raw.get("formatVersion", ""))

    @property
    def is_newer_than_this_build(self) -> bool:
        return _major(self.format_version) > _major(FORMAT_VERSION)

    @property
    def identifier(self) -> str:
        return str(self.raw.get("id", ""))

    @property
    def cases(self) -> list[dict[str, Any]]:
        return list(self.raw.get("cases", []))

    @property
    def unknown_fields(self) -> tuple[str, ...]:
        """Top-level fields this build has no opinion about, named so a user can be told they are kept.

        Nested unknowns are preserved too and are not listed: naming them would mean walking a schema
        this build does not have for a version it does not know.
        """
        known = set(REQUIRED_FIELDS) | {
            "name", "createdBy", "templates", "referenceMaterial", "displayUnits",
            "componentFrames", "pipelines",
        }
        return tuple(sorted(set(self.raw) - known))


def load(path: str | Path) -> WorkspaceDocument:
    """Read a workspace document, or refuse and leave the file exactly as it was."""
    location = Path(path)
    if not location.exists():
        raise WorkspaceFileError(f"{location} がありません")

    # Read-only, and read entirely before anything is parsed. Nothing in this function opens the file
    # for writing, which is what makes AC-013's "leaves the original untouched" true by construction
    # rather than by the absence of a bug.
    try:
        text = location.read_text(encoding="utf-8")
    except OSError as error:
        raise WorkspaceFileError(f"{location.name} を読めません：{error}") from None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise WorkspaceFileError(
            f"{location.name} は {error.lineno} 行 {error.colno} 桁で読めなくなりました：{error.msg}。"
            "ファイルには手を触れていません。前の版が残っていれば "
            f"{location.name}{PREVIOUS_SUFFIX} にあります"
        ) from None

    if not isinstance(parsed, dict):
        raise WorkspaceFileError(
            f"{location.name} の中身は {type(parsed).__name__} で、ワークスペース文書ではありません"
        )

    missing = [name for name in REQUIRED_FIELDS if name not in parsed]
    if missing:
        raise WorkspaceFileError(
            f"{location.name} に必須の項目がありません：{', '.join(missing)}。"
            "機能の欠けたワークスペースではなく、ワークスペースではないものとして扱います"
        )

    return WorkspaceDocument(raw=parsed, origin=location, migrated_from=lift_in_place(parsed))


def lift_in_place(parsed: dict[str, Any]) -> str | None:
    """Lift a version-4 document to this build's shape, field by field, and say which version it was.

    Two known fields move - a source's `modifiedIso` and a variable state's `detachedIso`, each into
    the `{utc, offsetMinutes}` a recorded time has everywhere (XC-266) with the offset **null**,
    because the file never kept it and zero would be a claim (XC-001). Everything else, known or not,
    stays where it is. The document is then what this build would have written, so a save writes
    it as this version - and the open's answer says so, because a file that changes version on the
    next save is a thing a person shares with somebody on the version before.
    """
    declared = str(parsed.get("formatVersion", ""))
    if _major(declared) != LIFTED_MAJOR:
        return None

    def lift(holder: dict[str, Any], old: str, new: str) -> None:
        if old in holder and new not in holder:
            holder[new] = {"utc": str(holder.pop(old)), "offsetMinutes": None}

    remaining = [one for one in (parsed.get("cases") or []) if isinstance(one, dict)]
    while remaining:
        case = remaining.pop()
        for source in case.get("sources") or []:
            if isinstance(source, dict):
                lift(source, "modifiedIso", "modified")
        for state in (case.get("variableStates") or {}).values():
            if isinstance(state, dict):
                lift(state, "detachedIso", "detached")
        remaining += [one for one in (case.get("children") or []) if isinstance(one, dict)]
    parsed["formatVersion"] = FORMAT_VERSION
    return declared


def save(document: WorkspaceDocument, path: str | Path) -> Path:
    """Write a document, keeping the previous good version beside it (XC-055).

    Returns the path of the previous version where one was kept, or the target where there was nothing
    to keep. Refuses to write a document whose format is newer than this build's.
    """
    location = Path(path)
    if document.raw.get("formatVersion") and document.is_newer_than_this_build:
        raise WorkspaceVersionError(
            f"この文書の形式は {document.format_version} で、この版が書けるのは {FORMAT_VERSION} "
            "です。読むことはでき、失わずに保持していますが、書き戻すと理解していない形を"
            "理解したと主張することになります（CT-001）"
        )

    temporary = location.with_name(location.name + ".writing")
    previous = location.with_name(location.name + PREVIOUS_SUFFIX)

    # Written and flushed to the platform before anything existing is moved. A rename that follows an
    # unflushed write moves a file whose contents the operating system has not yet committed.
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document.raw, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())

    kept = location
    if location.exists():
        # Move aside rather than copy: between this line and the next the data exists as `previous` and
        # as `temporary`, twice rather than never. A copy would spend the same moment with two names for
        # bytes that may not both be on disk.
        os.replace(location, previous)
        kept = previous
    os.replace(temporary, location)
    return kept
