"""Output that grows for ever, and times that can be ordered across offices.

XC-141: every run writes a new folder and never overwrites one, so output grows without limit. The
answer is to report the size and offer pruning by run - naming what would go, keeping the record, and
never touching input data.

XC-142: a study run in two offices, or across a daylight-saving change, produces run records that
**cannot be ordered** if each carries only a local time.

Verifies: workspace/AC-052, AC-053, AC-054, workspace/TASK-051 to TASK-053.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from domain_core.recorded_time import RecordedTime, from_stored, record
from engine.limits import MAX_OUTPUT_BYTES
from service.workspace.output import (
    RECORD_NAMES,
    Run,
    plan_pruning,
    prune,
    size_of,
)


def a_run(root: Path, identifier: str, at: str, *, artefacts: int, size: int = 100) -> Run:
    directory = root / identifier
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.json").write_text('{"how": "it was made"}', encoding="utf-8")
    for number in range(artefacts):
        (directory / f"figure-{number}.png").write_bytes(b"x" * size)
    return Run(identifier, at, directory)


class TestHowMuchSpaceIsInUse:
    def test_it_counts_the_artefacts_of_every_run(self, tmp_path: Path) -> None:
        runs = [
            a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=2),
            a_run(tmp_path, "run-2", "2026-08-02T00:00:00Z", artefacts=3),
        ]

        size = size_of(runs)

        assert size.run_count == 2
        assert size.total_bytes == 5 * 100

    def test_the_run_record_is_not_counted_as_output(self, tmp_path: Path) -> None:
        """It is what makes a deleted artefact reproducible, so it is not the thing being measured for
        deletion."""
        runs = [a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=1)]

        assert size_of(runs).total_bytes == 100

    def test_passing_the_limit_is_an_ask_rather_than_a_refusal(self, tmp_path: Path) -> None:
        runs = [a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=3)]

        size = size_of(runs, limit_bytes=100)

        assert size.over_limit
        assert "拒否ではなく" in size.describe()

    def test_the_limit_comes_from_the_one_place_that_holds_it(self) -> None:
        """LIM-012 named no source of truth until 2026-08-24, which is one step from the defect
        `limits.py` itself records: `MAX_DATASET_BYTES = 8` against a specification that also said 8."""
        assert size_of([]).limit_bytes == MAX_OUTPUT_BYTES


class TestPruningNamesEverythingItWouldRemove:
    def test_it_takes_the_oldest_first(self, tmp_path: Path) -> None:
        runs = [
            a_run(tmp_path, "run-3", "2026-08-03T00:00:00Z", artefacts=1),
            a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=1),
            a_run(tmp_path, "run-2", "2026-08-02T00:00:00Z", artefacts=1),
        ]

        plan = plan_pruning(runs, target_bytes=100)

        assert [run.identifier for run in plan.runs] == ["run-1", "run-2"]

    def test_every_file_is_listed_rather_than_totalled(self, tmp_path: Path) -> None:
        """AC-053. "Freed 4.2 GB" tells the user a number and not what it cost them."""
        runs = [
            a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=2),
            a_run(tmp_path, "run-2", "2026-08-02T00:00:00Z", artefacts=1),
        ]

        line = plan_pruning(runs, target_bytes=100).describe()

        assert "figure-0.png" in line
        assert "figure-1.png" in line

    def test_the_run_record_is_kept(self, tmp_path: Path) -> None:
        """A deleted artefact stays reproducible because the record of how it was made survives
        (XC-046)."""
        runs = [
            a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=2),
            a_run(tmp_path, "run-2", "2026-08-02T00:00:00Z", artefacts=1),
        ]

        plan = plan_pruning(runs, target_bytes=100)
        prune(plan)

        assert (tmp_path / "run-1" / "run.json").exists()
        assert not (tmp_path / "run-1" / "figure-0.png").exists()
        assert "run.json" in RECORD_NAMES

    def test_the_newest_run_is_never_pruned_by_size(self, tmp_path: Path) -> None:
        """Not an optimisation: a size-driven rule that removes it is a rule that deletes the thing
        somebody just made."""
        runs = [a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=5)]

        assert plan_pruning(runs, target_bytes=0).runs == ()

    def test_pruning_deletes_exactly_what_the_plan_named(self, tmp_path: Path) -> None:
        """`prune` takes the plan rather than the runs, so what is deleted is what was shown. A
        function that recomputed the list would be free to delete something the user never saw."""
        runs = [
            a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=2),
            a_run(tmp_path, "run-2", "2026-08-02T00:00:00Z", artefacts=1),
        ]
        plan = plan_pruning(runs, target_bytes=100)

        assert prune(plan) == len(plan.files)

    def test_nothing_to_prune_says_so(self, tmp_path: Path) -> None:
        runs = [
            a_run(tmp_path, "run-1", "2026-08-01T00:00:00Z", artefacts=1),
            a_run(tmp_path, "run-2", "2026-08-02T00:00:00Z", artefacts=1),
        ]

        assert plan_pruning(runs, target_bytes=1_000_000).describe() == "整理するものはありません"


class TestARecordedTimeIsTwoFacts:
    def test_it_stores_the_instant_and_where_it_was_recorded(self) -> None:
        moment = datetime(2026, 8, 24, 21, 0, tzinfo=timezone(timedelta(hours=9)))

        stored = record(moment)

        assert stored.utc == "2026-08-24T12:00:00Z"
        assert stored.offset_minutes == 540

    def test_a_time_with_no_zone_is_refused(self) -> None:
        """A naive datetime is a local time with the zone forgotten - the record XC-142 exists to
        prevent, because it looks complete and cannot be ordered against another office's."""
        with pytest.raises(ValueError) as refusal:
            record(datetime(2026, 8, 24, 21, 0))
        assert "並べられません" in str(refusal.value)

    def test_two_offices_order_by_instant_and_not_by_the_clock_on_the_wall(self) -> None:
        """The whole point of the decision, and the numbers make it themselves.

        Osaka's run says 21:00 and Stuttgart's says 15:00, so a record holding only local times orders
        Stuttgart first. It is actually **an hour later**: 21:00 JST is 12:00 UTC and 15:00 CEST is
        13:00. Two records, plausible either way round, and only the instant settles it.
        """
        osaka = record(datetime(2026, 8, 24, 21, 0, tzinfo=timezone(timedelta(hours=9))))
        stuttgart = record(datetime(2026, 8, 24, 15, 0, tzinfo=timezone(timedelta(hours=2))))

        assert osaka.local.hour > stuttgart.local.hour  # what a local-only record would order by
        assert osaka.instant < stuttgart.instant  # what actually happened

    def test_the_local_moment_stays_recoverable(self) -> None:
        """"17:00" in a record is only useful if you know whose five o'clock it was."""
        stored = record(datetime(2026, 8, 24, 21, 0, tzinfo=timezone(timedelta(hours=9))))

        assert stored.local.hour == 21

    def test_a_reader_sees_it_in_their_own_zone(self) -> None:
        stored = record(datetime(2026, 8, 24, 21, 0, tzinfo=timezone(timedelta(hours=9))))

        assert stored.displayed_in(120).hour == 14

    def test_a_zone_that_is_not_a_whole_hour_survives(self) -> None:
        """A field that cannot hold +05:45 is a field that quietly rounds somebody."""
        stored = record(datetime(2026, 8, 24, 17, 45, tzinfo=timezone(timedelta(minutes=345))))

        assert stored.offset_minutes == 345

    def test_a_time_shown_in_another_zone_says_where_it_was_made(self) -> None:
        """A time silently restated in another zone is a time two people will disagree about while
        both reading the same record."""
        stored = record(datetime(2026, 8, 24, 21, 0, tzinfo=timezone(timedelta(hours=9))))

        assert "UTC+09:00" in stored.describe(120)
        assert "（" not in stored.describe(540)

    def test_it_round_trips_through_storage(self) -> None:
        stored = record(datetime(2026, 8, 24, 21, 0, tzinfo=timezone(timedelta(hours=9))))

        assert from_stored(stored.as_stored()) == stored

    def test_a_stored_local_time_is_refused_on_the_way_back_in(self) -> None:
        with pytest.raises(ValueError):
            RecordedTime(utc="2026-08-24T21:00:00+09:00", offset_minutes=540)
