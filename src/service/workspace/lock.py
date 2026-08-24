"""A workspace open twice is opened read-only the second time, and told who has it.

AC-028 rules out the two answers a product usually gives. **Refusing** leaves a user who knows the other
window is theirs, on the other monitor, with nothing to do. **Opening it twice for editing** loses
whichever save happens second, and loses it silently.

So the second open succeeds, read-only, and says which process holds it. That requires the lock to
record who took it - a lock file holding nothing is a lock that can only produce "in use by something".

AC-029 covers the case that actually happens: the lock cannot be read, or names a process that is gone.
A stale lock is **reported and read-only is offered**, never broken automatically. Breaking it silently
is how two editors end up open on a network share where the first machine simply went quiet.

Specification: workspace/AC-028, AC-029.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

LOCK_SUFFIX = ".lock"


class LockState(str, Enum):
    """What was found when the lock was looked at."""

    FREE = "free"          # nothing holds it
    HELD = "held"          # another live process holds it
    STALE = "stale"        # a lock naming a process that is gone
    UNREADABLE = "unreadable"  # a lock file that cannot be understood


@dataclass(frozen=True, slots=True)
class LockHolder:
    """Who took a lock. Recorded because "in use by something" is not an answer anyone can act on."""

    process_id: int
    host: str
    user: str
    taken_at: str

    def describe(self) -> str:
        return f"{self.host} の {self.user}（プロセス {self.process_id}、{self.taken_at} 取得）"


@dataclass(frozen=True, slots=True)
class LockStatus:
    """The state of a workspace's lock, and what to offer because of it."""

    state: LockState
    holder: LockHolder | None = None
    detail: str | None = None

    @property
    def may_edit(self) -> bool:
        """Only a free lock permits editing. A stale one does **not**: a process that stopped answering
        is not the same as a process that stopped, and on a network share the difference is a second
        editor."""
        return self.state is LockState.FREE

    def describe(self) -> str:
        if self.state is LockState.FREE:
            return "編集できます"
        if self.state is LockState.HELD:
            return (
                f"このワークスペースは {self.holder.describe() if self.holder else '別のプロセス'} が"
                "開いています。読み取り専用で開きます"
            )
        if self.state is LockState.STALE:
            return (
                f"ロックは {self.holder.describe() if self.holder else '不明なプロセス'} のものですが、"
                "そのプロセスは見つかりません。自動では解除しません — "
                "応答しなくなっただけのプロセスと、終了したプロセスは違います。読み取り専用で開けます"
            )
        return f"ロックファイルを読めません（{self.detail}）。読み取り専用で開けます"


def lock_for(workspace: str | Path) -> Path:
    return Path(str(workspace) + LOCK_SUFFIX)


#: The Windows error for "no such process", measured rather than looked up: `os.kill(pid, 0)` on a
#: pid that does not exist raises `OSError` with this code and **not** `ProcessLookupError`, and on a
#: protected process (pid 4) it raises `SystemError` (E-139). A probe written for POSIX and run here
#: would find every lock alive.
WINDOWS_NO_SUCH_PROCESS = 87


def _alive(process_id: int) -> bool:
    """Whether a process id belongs to something running on this machine.

    **Anything not clearly dead counts as alive.** Liveness cannot be established reliably from a pid -
    ids are reused, protected processes cannot be signalled, and the error a missing one produces
    differs by platform - so the only safe direction is the one where a wrong answer keeps a lock. A
    lock wrongly called stale is the failure that opens a second editor.

    Only meaningful for a lock this machine took. A pid from another host says nothing about this one,
    which is why `inspect` never asks about one.
    """
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except OSError as error:
        return getattr(error, "winerror", None) != WINDOWS_NO_SUCH_PROCESS
    except SystemError:
        return True  # a process that exists and cannot be signalled
    return True


def inspect(workspace: str | Path, *, this_host: str | None = None) -> LockStatus:
    """What holds this workspace, if anything."""
    path = lock_for(workspace)
    if not path.exists():
        return LockStatus(LockState.FREE)

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        holder = LockHolder(
            process_id=int(parsed["processId"]),
            host=str(parsed["host"]),
            user=str(parsed["user"]),
            taken_at=str(parsed["takenAt"]),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return LockStatus(LockState.UNREADABLE, detail=str(error)[:120])

    host = this_host if this_host is not None else os.environ.get("COMPUTERNAME", "")
    if holder.host == host and not _alive(holder.process_id):
        return LockStatus(LockState.STALE, holder=holder)
    return LockStatus(LockState.HELD, holder=holder)


def take(
    workspace: str | Path, *, process_id: int, host: str, user: str, at: str
) -> LockStatus:
    """Take the lock, or report what is holding it. Never breaks an existing one."""
    found = inspect(workspace, this_host=host)
    if found.state is not LockState.FREE:
        return found

    path = lock_for(workspace)
    body = json.dumps(
        {"processId": process_id, "host": host, "user": user, "takenAt": at},
        ensure_ascii=False, sort_keys=True,
    )
    try:
        # Exclusive creation: two processes racing here, one loses and reads the other's lock rather
        # than both believing they took it.
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        return inspect(workspace, this_host=host)
    except OSError as error:
        return LockStatus(LockState.UNREADABLE, detail=str(error)[:120])
    return LockStatus(LockState.FREE, holder=LockHolder(process_id, host, user, at))


def release(workspace: str | Path, *, process_id: int, host: str) -> bool:
    """Give up a lock this process took. Returns whether there was one of ours to give up.

    Refuses to remove somebody else's, which is the same rule as `take`: a lock is broken by a person
    who knows what is going on, not by a process that would like the file.
    """
    found = inspect(workspace, this_host=host)
    if found.holder is None:
        return False
    if found.holder.process_id != process_id or found.holder.host != host:
        return False
    lock_for(workspace).unlink(missing_ok=True)
    return True
