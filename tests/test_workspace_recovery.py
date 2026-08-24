"""Work in progress survives a crash, and a workspace is never edited twice at once.

Two things the specification rules out by name. Journalled work is **offered**, never replayed
automatically: the crash may have been caused by the change being replayed. And a workspace already
open elsewhere is opened **read-only with the holder named**, rather than refused - a user who knows
the other window is theirs on the other monitor has nothing to do with a refusal.

Verifies: workspace/AC-026 to AC-029, workspace/TASK-025 to TASK-028.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from conftest import FIXED_INSTANT

from service.workspace.journal import (
    APPLIED_SUFFIX,
    Entry,
    JournalError,
    accept,
    append,
    discard,
    journal_for,
    read,
)
from service.workspace.lock import LockState, inspect, lock_for, release, take

WHEN = FIXED_INSTANT


def a_workspace(tmp_path: Path) -> Path:
    path = tmp_path / "w.svw"
    path.write_text('{"formatVersion": "4.0.0"}', encoding="utf-8")
    return path


def change(number: int) -> Entry:
    return Entry(at=WHEN, action="rename", detail={"id": f"case:{number:03d}", "name": f"n{number}"})


class TestTheJournalSitsBesideTheFile:
    def test_appending_leaves_the_workspace_file_untouched(self, tmp_path: Path) -> None:
        """AC-026. Rewriting the workspace on every change would put the one file the user cannot lose
        in the path of every keystroke."""
        workspace = a_workspace(tmp_path)
        before = workspace.read_bytes()

        append(workspace, change(1))

        assert workspace.read_bytes() == before
        assert journal_for(workspace).exists()

    def test_it_is_beside_the_file_and_readable_without_the_product(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        append(workspace, change(1))

        line = json.loads(journal_for(workspace).read_text(encoding="utf-8").splitlines()[0])

        assert line["action"] == "rename"

    def test_entries_come_back_in_the_order_they_were_written(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        for number in (1, 2, 3):
            append(workspace, change(number))

        recovery = read(workspace)

        assert [entry.detail["name"] for entry in recovery.entries] == ["n1", "n2", "n3"]

    def test_no_journal_means_no_work_rather_than_an_error(self, tmp_path: Path) -> None:
        recovery = read(a_workspace(tmp_path))

        assert recovery.has_work is False
        assert "未適用の作業はありません" in recovery.describe()


class TestATruncatedJournalIsTheOrdinaryShapeOfACrash:
    def test_the_replay_stops_at_the_bad_line_and_keeps_what_came_before(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        append(workspace, change(1))
        append(workspace, change(2))
        with journal_for(workspace).open("a", encoding="utf-8") as handle:
            handle.write('{"at": "2026-08-24T12:00:00Z", "action": "ren')  # a process that stopped

        recovery = read(workspace)

        assert len(recovery.entries) == 2
        assert recovery.stopped_at == 3
        assert "行の途中で終わっています" in (recovery.stopped_because or "")

    def test_it_says_so_rather_than_reporting_a_clean_recovery(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        append(workspace, change(1))
        with journal_for(workspace).open("a", encoding="utf-8") as handle:
            handle.write("{oh dear\n")

        assert "より先は読めませんでした" in read(workspace).describe()

    def test_a_line_missing_a_field_stops_it_too(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        with journal_for(workspace).open("w", encoding="utf-8") as handle:
            handle.write('{"at": "now", "action": "rename"}\n')  # no detail

        assert read(workspace).stopped_at == 1


class TestJournalledWorkIsOfferedAndNotApplied:
    def test_reading_it_changes_nothing(self, tmp_path: Path) -> None:
        """AC-027. Replaying automatically would mean a crash silently changes a saved file - and the
        crash may have been caused by the change being replayed."""
        workspace = a_workspace(tmp_path)
        before = workspace.read_bytes()
        append(workspace, change(1))

        read(workspace)

        assert workspace.read_bytes() == before
        assert journal_for(workspace).exists()
        assert "ファイルはまだ変更していません" in read(workspace).describe()

    def test_accepting_retires_the_journal_rather_than_deleting_it(self, tmp_path: Path) -> None:
        """The first thing anybody wants after a bad recovery is what was there before it."""
        workspace = a_workspace(tmp_path)
        append(workspace, change(1))

        applied = accept(workspace)

        assert applied.name.endswith(APPLIED_SUFFIX)
        assert not journal_for(workspace).exists()
        assert applied.exists()

    def test_declining_keeps_it_too(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        append(workspace, change(1))

        discarded = discard(workspace)

        assert discarded is not None and discarded.exists()

    def test_accepting_nothing_is_refused_rather_than_silently_fine(self, tmp_path: Path) -> None:
        with pytest.raises(JournalError):
            accept(a_workspace(tmp_path))


class TestASecondOpenIsReadOnlyAndSaysWhoHasIt:
    def test_taking_a_free_lock_permits_editing(self, tmp_path: Path) -> None:
        status = take(a_workspace(tmp_path), process_id=os.getpid(), host="pc1", user="taro", at=WHEN)

        assert status.may_edit

    def test_a_second_take_reports_the_holder_rather_than_refusing(self, tmp_path: Path) -> None:
        """AC-028. Refusing leaves a user who knows the other window is theirs with nothing to do."""
        workspace = a_workspace(tmp_path)
        take(workspace, process_id=os.getpid(), host="pc1", user="taro", at=WHEN)

        second = take(workspace, process_id=os.getpid(), host="pc1", user="taro", at=WHEN)

        assert second.state is LockState.HELD
        assert second.may_edit is False
        assert "読み取り専用" in second.describe()

    def test_the_holder_is_named_well_enough_to_act_on(self, tmp_path: Path) -> None:
        """"In use by something" is not an answer anyone can act on."""
        workspace = a_workspace(tmp_path)
        take(workspace, process_id=4321, host="pc9", user="hanako", at=WHEN)

        line = inspect(workspace, this_host="pc1").describe()

        assert "pc9" in line and "hanako" in line and "4321" in line

    def test_releasing_our_own_lock_frees_it(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        take(workspace, process_id=os.getpid(), host="pc1", user="taro", at=WHEN)

        assert release(workspace, process_id=os.getpid(), host="pc1") is True
        assert inspect(workspace, this_host="pc1").state is LockState.FREE

    def test_another_process_lock_is_not_released(self, tmp_path: Path) -> None:
        """A lock is broken by a person who knows what is going on, not by a process that would like
        the file."""
        workspace = a_workspace(tmp_path)
        take(workspace, process_id=4321, host="pc9", user="hanako", at=WHEN)

        assert release(workspace, process_id=os.getpid(), host="pc1") is False
        assert lock_for(workspace).exists()


class TestAStaleOrUnreadableLock:
    def test_a_lock_from_a_dead_process_on_this_host_is_stale(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        lock_for(workspace).write_text(
            json.dumps({"processId": 999999, "host": "pc1", "user": "taro", "takenAt": WHEN}),
            encoding="utf-8",
        )

        status = inspect(workspace, this_host="pc1")

        assert status.state is LockState.STALE
        assert status.may_edit is False

    def test_a_stale_lock_is_reported_and_not_broken(self, tmp_path: Path) -> None:
        """AC-029. Breaking it silently is how two editors end up open on a network share where the
        first machine simply went quiet."""
        workspace = a_workspace(tmp_path)
        lock_for(workspace).write_text(
            json.dumps({"processId": 999999, "host": "pc1", "user": "taro", "takenAt": WHEN}),
            encoding="utf-8",
        )

        line = inspect(workspace, this_host="pc1").describe()

        assert "自動では解除しません" in line
        assert lock_for(workspace).exists()

    def test_a_dead_looking_process_on_another_host_is_not_called_stale(self, tmp_path: Path) -> None:
        """A process id from another machine says nothing about this one, and treating it as dead is
        exactly what opens a second editor on a share."""
        workspace = a_workspace(tmp_path)
        lock_for(workspace).write_text(
            json.dumps({"processId": 999999, "host": "pc9", "user": "hanako", "takenAt": WHEN}),
            encoding="utf-8",
        )

        assert inspect(workspace, this_host="pc1").state is LockState.HELD

    def test_an_unreadable_lock_offers_read_only_rather_than_failing(self, tmp_path: Path) -> None:
        workspace = a_workspace(tmp_path)
        lock_for(workspace).write_text("not json at all", encoding="utf-8")

        status = inspect(workspace, this_host="pc1")

        assert status.state is LockState.UNREADABLE
        assert "読み取り専用で開けます" in status.describe()
