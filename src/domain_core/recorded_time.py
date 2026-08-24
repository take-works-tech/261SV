"""Every recorded time is UTC with the local offset beside it, and is shown in the reader's own zone.

XC-142's rationale is the whole of it: a study run in two offices, or across a daylight-saving change,
produces run records that **cannot be ordered** if each carries only a local time. Keeping the offset as
well means the local moment is still recoverable, which is what somebody reconstructing what happened
actually wants - "17:00" in a record is only useful if you know whose five o'clock it was.

So a recorded time is two facts, not one: the instant, and where the person who caused it was standing.
Storing only the instant loses the second; storing only the local time loses the first.

Specification: XC-142, workspace/AC-054.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

#: How a stored time is written. UTC with a trailing Z, and the offset as a separate field - not folded
#: into the timestamp, because a reader parsing `2026-08-24T12:00:00+09:00` has to decide whether that
#: is the instant or the local moment, and different readers decide differently.
STORED_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True, slots=True)
class RecordedTime:
    """One instant, and the local offset where it was recorded."""

    utc: str
    #: Minutes east of UTC at the moment of writing. Minutes rather than hours because several zones
    #: are not whole hours, and a field that cannot hold +05:45 is a field that quietly rounds somebody.
    offset_minutes: int

    def __post_init__(self) -> None:
        try:
            datetime.strptime(self.utc, STORED_FORMAT)
        except ValueError:
            raise ValueError(
                f"{self.utc!r} は UTC の形（{STORED_FORMAT}）ではありません。"
                "ローカル時刻をそのまま保存すると、二つの事務所の記録を並べられなくなります（XC-142）"
            ) from None
        if not -1440 < self.offset_minutes < 1440:
            raise ValueError("オフセットは ±24 時間の範囲です")

    @property
    def instant(self) -> datetime:
        return datetime.strptime(self.utc, STORED_FORMAT).replace(tzinfo=timezone.utc)

    @property
    def local(self) -> datetime:
        """The moment as the person who caused it saw it - the second fact, recoverable."""
        return self.instant.astimezone(timezone(timedelta(minutes=self.offset_minutes)))

    def displayed_in(self, offset_minutes: int) -> datetime:
        """The same instant in the reader's own zone (XC-142).

        The reader's, not the writer's: somebody in Osaka reading a run made in Stuttgart wants to know
        when it happened for them, and the record still says where it was made.
        """
        return self.instant.astimezone(timezone(timedelta(minutes=offset_minutes)))

    def describe(self, offset_minutes: int) -> str:
        shown = self.displayed_in(offset_minutes).strftime("%Y-%m-%d %H:%M")
        if offset_minutes == self.offset_minutes:
            return shown
        # The recording zone is named whenever it differs, because a time silently restated in another
        # zone is a time two people will disagree about while both reading the same record.
        return f"{shown}（記録時は {_offset_text(self.offset_minutes)}）"

    def as_stored(self) -> dict[str, object]:
        return {"utc": self.utc, "offsetMinutes": self.offset_minutes}


def _offset_text(minutes: int) -> str:
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"UTC{sign}{minutes // 60:02d}:{minutes % 60:02d}"


def record(moment: datetime) -> RecordedTime:
    """Turn an aware moment into a stored time. Refuses a naive one.

    A naive datetime is a local time with the zone forgotten, which is precisely the record XC-142
    exists to prevent: it looks complete and cannot be ordered against another office's.
    """
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(
            "タイムゾーンのない時刻は保存しません。ゾーンを忘れたローカル時刻は、"
            "完全に見えて他の事務所の記録と並べられません（XC-142）"
        )
    offset = moment.utcoffset() or timedelta()
    return RecordedTime(
        utc=moment.astimezone(timezone.utc).strftime(STORED_FORMAT),
        offset_minutes=int(offset.total_seconds() // 60),
    )


def from_stored(stored: dict[str, object]) -> RecordedTime:
    return RecordedTime(utc=str(stored["utc"]), offset_minutes=int(stored["offsetMinutes"]))  # type: ignore[arg-type]
