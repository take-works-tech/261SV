"""Work in progress survives a crash, and it never reaches the saved file on its own.

Two properties, and the second is what makes the first safe to have.

**A change is appended beside the workspace file, which is not rewritten** (AC-026). Appending is what
survives a process that stops mid-write: a line either reached the disk whole or did not reach it, and
a reader can stop at the first line that did not. Rewriting the workspace on every change would put the
one file the user cannot lose in the path of every keystroke.

**Journalled work is offered and applied only on acceptance** (AC-027). Replaying it automatically would
mean a crash silently changes a saved file - and the crash may have been caused by the very change being
replayed. So the saved file stays untouched until somebody says yes, and after that the journal is
retired rather than deleted, because the first thing anybody wants after a bad recovery is what was
there before.

A line that cannot be read stops the replay **at that line** and keeps what came before. A truncated
last line is the ordinary shape of a crash, not a corrupt journal.

Specification: workspace/AC-026, AC-027, CT-001, XC-055.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: The journal sits beside the workspace file, visibly. A user who wants to know what a recovery is
#: about should be able to read it without the product.
JOURNAL_SUFFIX = ".journal"
#: Where a journal goes once its work has been accepted. Kept rather than deleted: the first thing
#: anybody wants after a bad recovery is what was there before it.
APPLIED_SUFFIX = ".journal.applied"


class JournalError(Exception):
    """Raised when a journal cannot be read or written. Never silently skipped."""


@dataclass(frozen=True, slots=True)
class Entry:
    """One recorded change: when, what kind, and enough to replay it."""

    at: str
    action: str
    detail: dict[str, Any]

    def as_line(self) -> str:
        return json.dumps(
            {"at": self.at, "action": self.action, "detail": self.detail},
            ensure_ascii=False, sort_keys=True,
        )


@dataclass(frozen=True, slots=True)
class Recovery:
    """What a journal holds, and what could not be read from it."""

    entries: tuple[Entry, ...]
    #: The 1-based line the replay stopped at, or None where the whole journal read.
    stopped_at: int | None = None
    stopped_because: str | None = None

    @property
    def has_work(self) -> bool:
        return bool(self.entries)

    def describe(self) -> str:
        if not self.entries and self.stopped_at is None:
            return "未適用の作業はありません"
        line = f"保存されていない変更が {len(self.entries)} 件あります"
        if self.stopped_at is not None:
            line += (
                f"。{self.stopped_at} 行目より先は読めませんでした（{self.stopped_because}）— "
                "そこまでの変更だけを提示しています"
            )
        return line + "。ワークスペースのファイルはまだ変更していません"


def journal_for(workspace: str | Path) -> Path:
    return Path(str(workspace) + JOURNAL_SUFFIX)


def append(workspace: str | Path, entry: Entry) -> Path:
    """Add one change to the journal beside a workspace, leaving the workspace file alone.

    Flushed and synced per entry. An entry that is in the file but not on the platform is an entry a
    crash loses, which is the one case this exists for.
    """
    path = journal_for(workspace)
    try:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(entry.as_line() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        raise JournalError(f"変更を記録できません：{error}") from None
    return path


def read(workspace: str | Path) -> Recovery:
    """Everything the journal holds, stopping at the first line that cannot be read.

    A truncated last line is the ordinary shape of a crash rather than a corrupt journal, so what came
    before it is kept and offered.
    """
    path = journal_for(workspace)
    if not path.exists():
        return Recovery(entries=())

    entries: list[Entry] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
            entries.append(
                Entry(at=str(parsed["at"]), action=str(parsed["action"]), detail=dict(parsed["detail"]))
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            return Recovery(
                entries=tuple(entries),
                stopped_at=number,
                stopped_because=(
                    "行の途中で終わっています" if isinstance(error, json.JSONDecodeError)
                    else f"項目が足りません：{error}"
                ),
            )
    return Recovery(entries=tuple(entries))


def accept(workspace: str | Path) -> Path:
    """Mark the journal applied, keeping it. Called only after the user has said yes."""
    path = journal_for(workspace)
    if not path.exists():
        raise JournalError(f"{path.name} がありません")
    applied = Path(str(workspace) + APPLIED_SUFFIX)
    os.replace(path, applied)
    return applied


def discard(workspace: str | Path) -> Path | None:
    """Set the journal aside without applying it, keeping it under the same name as an accepted one.

    Kept rather than deleted for the same reason: a user who declines a recovery and then changes their
    mind has nowhere else to look.
    """
    path = journal_for(workspace)
    if not path.exists():
        return None
    discarded = Path(str(workspace) + APPLIED_SUFFIX)
    os.replace(path, discarded)
    return discarded
