"""Every recorded time is UTC with the local offset beside it, and is shown in the reader's own zone.

XC-142's rationale is the whole of it: a study run in two offices, or across a daylight-saving change,
produces run records that **cannot be ordered** if each carries only a local time. Keeping the offset as
well means the local moment is still recoverable, which is what somebody reconstructing what happened
actually wants - "17:00" in a record is only useful if you know whose five o'clock it was.

So a recorded time is two facts, not one: the instant, and where the person who caused it was standing.
Storing only the instant loses the second; storing only the local time loses the first.

**One wire form, everywhere** (XC-266): `{"utc": "...Z", "offsetMinutes": n}` - what `as_stored` writes
and `from_stored` reads - in every contract that carries a time, whether it is a document on disk, an
answer over the API, a run record or a log line. Never a bare string under a name ending in `Iso` or
`Utc`: that was the form the contracts had carried since 2026-08-20, and it had dropped the second fact
in every one of them while the engine held both in memory (#318). A record written before the offset
was kept has **no** offset and says so with null; it is never given zero, because zero is a claim that
the writer stood in Greenwich (XC-001).

Specification: XC-142, XC-266, workspace/AC-054.
"""

from __future__ import annotations

from collections.abc import Mapping
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
    #: None where the record was written before the offset was kept - a version-4 document's source
    #: and detachment times - which is unknown, and is shown as unknown rather than as zero.
    offset_minutes: int | None

    def __post_init__(self) -> None:
        try:
            datetime.strptime(self.utc, STORED_FORMAT)
        except ValueError:
            raise ValueError(
                f"{self.utc!r} は UTC の形（{STORED_FORMAT}）ではありません。"
                "ローカル時刻をそのまま保存すると、二つの事務所の記録を並べられなくなります（XC-142）"
            ) from None
        if self.offset_minutes is not None and not -1440 < self.offset_minutes < 1440:
            raise ValueError("オフセットは ±24 時間の範囲です")

    @property
    def instant(self) -> datetime:
        return datetime.strptime(self.utc, STORED_FORMAT).replace(tzinfo=timezone.utc)

    @property
    def local(self) -> datetime | None:
        """The moment as the person who caused it saw it - the second fact, recoverable; None where
        the record never kept it."""
        if self.offset_minutes is None:
            return None
        return self.displayed_in(self.offset_minutes)

    def displayed_in(self, offset_minutes: int) -> datetime:
        """The same instant in the reader's own zone (XC-142).

        The reader's, not the writer's: somebody in Osaka reading a run made in Stuttgart wants to know
        when it happened for them, and the record still says where it was made.
        """
        return self.instant.astimezone(timezone(timedelta(minutes=offset_minutes)))

    def describe(self, offset_minutes: int) -> str:
        shown = self.displayed_in(offset_minutes).strftime("%Y-%m-%d %H:%M")
        if self.offset_minutes is None:
            return f"{shown}（記録時のゾーンは不明）"
        if offset_minutes == self.offset_minutes:
            return shown
        # The recording zone is named whenever it differs, because a time silently restated in another
        # zone is a time two people will disagree about while both reading the same record.
        return f"{shown}（記録時は {_offset_text(self.offset_minutes)}）"

    def describe_where_recorded(self) -> str:
        """The moment where it was recorded, with that zone named.

        For a document that has no reader's zone to show it in - an exported deliverable read by
        whoever receives it, a log line read by whoever opens the file. Unambiguous rather than
        local: `2026-08-24 21:00（UTC+09:00）` is the same moment to every reader.
        """
        if self.offset_minutes is None:
            return f"{self.utc}（記録時のゾーンは不明）"
        shown = self.displayed_in(self.offset_minutes).strftime("%Y-%m-%d %H:%M")
        return f"{shown}（{_offset_text(self.offset_minutes)}）"

    def as_stored(self) -> dict[str, object]:
        """The one wire form (XC-266): CT-001 `$defs.recordedTime`, referenced by every contract."""
        return {"utc": self.utc, "offsetMinutes": self.offset_minutes}


def _offset_text(minutes: int) -> str:
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"UTC{sign}{minutes // 60:02d}:{minutes % 60:02d}"


def _offset_of(moment: datetime) -> int:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError(
            "タイムゾーンのない時刻は保存しません。ゾーンを忘れたローカル時刻は、"
            "完全に見えて他の事務所の記録と並べられません（XC-142）"
        )
    return int((moment.utcoffset() or timedelta()).total_seconds() // 60)


def record(moment: datetime) -> RecordedTime:
    """Turn an aware moment into a stored time. Refuses a naive one.

    A naive datetime is a local time with the zone forgotten, which is precisely the record XC-142
    exists to prevent: it looks complete and cannot be ordered against another office's.
    """
    return RecordedTime(
        utc=moment.astimezone(timezone.utc).strftime(STORED_FORMAT),
        offset_minutes=_offset_of(moment),
    )


def record_instant(instant: datetime, *, where: datetime) -> RecordedTime:
    """An instant that happened elsewhere - a file's modification time - recorded with the offset of
    whoever is recording it now.

    `where` is an aware moment from the recorder's clock. XC-142's offset is "at the moment of
    writing": the record's, not the file's, which no filesystem keeps. A file's time built in UTC and
    passed to `record` would carry offset zero, which is a claim about where the recorder stood and
    a false one everywhere but Greenwich (XC-266).
    """
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("瞬間にはゾーンが要ります（XC-142）")
    return RecordedTime(
        utc=instant.astimezone(timezone.utc).strftime(STORED_FORMAT),
        offset_minutes=_offset_of(where),
    )


def from_stored(stored: object) -> RecordedTime:
    """Read the wire form back. Both keys must be there: an offset that is **absent** is a shape this
    build does not recognise, while one that is **null** is a record that never kept it."""
    if not isinstance(stored, Mapping) or "utc" not in stored or "offsetMinutes" not in stored:
        raise ValueError(
            f"記録された時刻は {{utc, offsetMinutes}} の形です（XC-142、XC-266）：{stored!r}"
        )
    offset = stored["offsetMinutes"]
    return RecordedTime(utc=str(stored["utc"]), offset_minutes=None if offset is None else int(offset))  # type: ignore[arg-type]
