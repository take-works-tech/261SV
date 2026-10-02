"""The recovery file beside a workspace document (workspace/AC-026, AC-027; XC-311; #431).

A document is written when a person saves (XC-055). Everything applied since then lived in the
engine's memory, and an engine that ends - a crash, a driver fault, a kill - took it with it; XC-259
had the interface say what was lost, and nothing gave it back. Now every applied write leaves the
document as it stands in `<name>.recovery` beside the file, with the list of writes since the last
save, and a save removes it. Opening a document that has one beside it says so and offers it;
nothing is taken until the person says `recover`, and the saved file is untouched until they save.

**An offer is never overwritten by the session it was made to.** A session that keeps working while
an offer stands unanswered moves the offer to `<name>.recovery.earlier` with its first write and
writes its own file; the earlier offer is what `recover` takes and what the next open offers once
the newer file is gone. One slot: a third unanswered generation replaces the oldest, and the log
says so. Each file names the session that wrote it, which is how a session tells its own file from
an offer.

One file rewritten whole and atomically (`.writing`, then `os.replace`) rather than a physical
append: the engine cannot replay a command of a session that is gone - its dataset ids and handles
died with it - so what restores the work is the state, and the list of writes is what names it. The
file is never a document: its top level is `recovery` and `document`, so a loader handed it refuses
it (CT-001 requires `formatVersion` at the top) and nothing mistakes it for the file it stands beside.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from domain_core.recorded_time import record

#: Beside the document, named after it: `study.svw` keeps `study.svw.recovery`.
RECOVERY_SUFFIX = ".recovery"
#: An offer set aside by a session that worked on while it stood: one slot.
EARLIER_SUFFIX = ".recovery.earlier"
#: How many of the writes since the last save are listed by name; the count is kept whole.
MAX_WRITES_LISTED = 200


class RecoveryUnreadable(Exception):
    """A file at a recovery path that is not a recovery file: said, never taken."""


@dataclass(frozen=True, slots=True)
class Recovery:
    """What a recovery file holds: the document as it stood, and what had been applied to it."""

    path: Path
    document_id: str
    session_id: str
    written_at: dict[str, Any]
    #: The document file's size and modification time when this was written, so a file saved by
    #: somebody else since can be told apart from the one the writes were made on.
    base_size: int | None
    base_modified_ns: int | None
    product_version: str
    count: int
    writes: tuple[dict[str, Any], ...]
    document: dict[str, Any]

    def base_changed(self, document_path: Path) -> bool:
        """Whether the document on disk is no longer the one these writes were applied to."""
        if not document_path.exists():
            return self.base_size is not None
        stat = document_path.stat()
        return (stat.st_size, stat.st_mtime_ns) != (self.base_size, self.base_modified_ns)

    def as_answer(self, document_path: Path, *, older_offer: bool) -> dict[str, Any]:
        return {
            "writtenAt": self.written_at,
            "count": self.count,
            "writes": list(self.writes),
            "baseChanged": self.base_changed(document_path),
            "productVersion": self.product_version,
            "olderOffer": older_offer,
        }


def recovery_path(document_path: Path) -> Path:
    return document_path.with_name(document_path.name + RECOVERY_SUFFIX)


def earlier_path(document_path: Path) -> Path:
    return document_path.with_name(document_path.name + EARLIER_SUFFIX)


def write_recovery(
    document_raw: Mapping[str, Any],
    document_path: Path,
    *,
    writes: list[dict[str, Any]],
    now: datetime,
    product_version: str,
    session_id: str,
) -> Path:
    """The document as it stands and the writes since the last save, written beside the document.

    Written and flushed under a temporary name, then moved into place, as the document itself is
    (XC-055): a recovery file cut short by the next crash would be a second loss.
    """
    path = recovery_path(document_path)
    stat = document_path.stat() if document_path.exists() else None
    body = {
        "recovery": {
            "of": document_path.name,
            "documentId": str(document_raw.get("id", "")),
            "sessionId": session_id,
            "writtenAt": record(now).as_stored(),
            "baseSize": stat.st_size if stat else None,
            "baseModifiedNs": stat.st_mtime_ns if stat else None,
            "productVersion": product_version,
            "count": len(writes),
            "writes": writes[-MAX_WRITES_LISTED:],
        },
        "document": document_raw,
    }
    temporary = path.with_name(path.name + ".writing")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(body, handle, ensure_ascii=False, indent=None, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return path


def read_recovery(path: Path) -> Recovery:
    """The recovery file at `path`, or `RecoveryUnreadable` naming why it is not one."""
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RecoveryUnreadable(f"{path.name} を復旧ファイルとして読めません（{error}）") from None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("recovery"), dict) or not isinstance(parsed.get("document"), dict):
        raise RecoveryUnreadable(f"{path.name} は復旧ファイルの形をしていません（recovery と document の二つの節が要ります）")
    header = parsed["recovery"]
    document = parsed["document"]
    writes = header.get("writes") or []
    return Recovery(
        path=path,
        document_id=str(header.get("documentId") or document.get("id", "")),
        session_id=str(header.get("sessionId", "")),
        written_at=dict(header.get("writtenAt") or {}),
        base_size=header.get("baseSize") if isinstance(header.get("baseSize"), int) else None,
        base_modified_ns=header.get("baseModifiedNs") if isinstance(header.get("baseModifiedNs"), int) else None,
        product_version=str(header.get("productVersion", "")),
        count=int(header.get("count") or len(writes)),
        writes=tuple(one for one in writes if isinstance(one, dict)),
        document=document,
    )


@dataclass(frozen=True, slots=True)
class Offer:
    """What the files beside a document offer a session: the newest recovery file that is not the
    session's own, whether an older one waits behind it, and what was found that is not an offer."""

    recovery: Recovery | None
    older_offer: bool
    warnings: tuple[str, ...]


def find_offer(document_path: Path, document_id: str, session_id: str) -> Offer:
    """The newest recovery file beside `document_path` that belongs to this document and was not
    written by this session. A file that is not a recovery file, or another document's, is said
    and left alone."""
    warnings: list[str] = []
    found: list[Recovery] = []
    for candidate in (recovery_path(document_path), earlier_path(document_path)):
        if not candidate.exists():
            continue
        try:
            one = read_recovery(candidate)
        except RecoveryUnreadable as error:
            warnings.append(f"{error}。復旧できるものはありません。消すには workspace.discardRecovery を使ってください")
            continue
        if one.document_id and one.document_id != document_id:
            warnings.append(
                f"{candidate.name} は別の文書（id {one.document_id}）の復旧ファイルです。この文書のものではないので使いません。"
                "消すには workspace.discardRecovery を使ってください"
            )
            continue
        if one.session_id == session_id:
            continue
        found.append(one)
    return Offer(found[0] if found else None, len(found) > 1, tuple(warnings))


def set_aside(document_path: Path) -> bool:
    """Move the offer in `<name>.recovery` to the earlier slot, so this session's own file can take
    its place; an offer already in the slot is replaced. True where something was moved."""
    current = recovery_path(document_path)
    if not current.exists():
        return False
    os.replace(current, earlier_path(document_path))
    return True


def discard_offer(document_path: Path, offer: Recovery) -> tuple[bytes, bool]:
    """Remove an offered file; the bytes removed, so the removal can be undone, and whether an
    earlier offer was moved up into its place."""
    kept = offer.path.read_bytes()
    offer.path.unlink()
    promoted = False
    if offer.path == recovery_path(document_path) and earlier_path(document_path).exists():
        os.replace(earlier_path(document_path), recovery_path(document_path))
        promoted = True
    return kept, promoted


def remove_own(document_path: Path, session_id: str) -> dict[Path, bytes]:
    """Remove the files beside the document that this session wrote, or that name no session (an
    older build's), and leave every offer of another session where it is. The bytes removed, by
    path, so a save's undo can put them back."""
    removed: dict[Path, bytes] = {}
    for candidate in (recovery_path(document_path), earlier_path(document_path)):
        if not candidate.exists():
            continue
        try:
            one = read_recovery(candidate)
        except RecoveryUnreadable:
            continue
        if one.session_id and one.session_id != session_id:
            continue
        removed[candidate] = candidate.read_bytes()
        candidate.unlink()
    return removed


__all__ = [
    "EARLIER_SUFFIX",
    "MAX_WRITES_LISTED",
    "RECOVERY_SUFFIX",
    "Offer",
    "Recovery",
    "RecoveryUnreadable",
    "discard_offer",
    "earlier_path",
    "find_offer",
    "read_recovery",
    "recovery_path",
    "remove_own",
    "set_aside",
    "write_recovery",
]
