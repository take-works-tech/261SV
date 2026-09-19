/* How a recorded time is written for a person to read (MOD-015, XC-142): in the reader's own zone,
 * with the recording zone named when it differs, and "unknown" said where a record written before the
 * offset was kept has none (XC-266). Mirrors RecordedTime.describe and describe_where_recorded in
 * src/domain_core/recorded_time.py: the two produce the same text for the same time, and time.test.ts
 * holds the same cases the Python tests hold - the reader's zone is known only here, in the browser,
 * which is why this one display rule lives on both sides. */
import type { RecordedTime } from "../client/generated";
import { offsetMinutesAt, offsetText } from "../client/time";

/** The same instant in the reader's own zone - the reader's, not the writer's: somebody in Osaka
 *  reading a run made in Stuttgart wants to know when it happened for them, and the record still
 *  says where it was made. */
export function describeRecorded(time: RecordedTime, readerOffsetMinutes: number = offsetMinutesAt()): string {
  const shown = inZone(time.utc, readerOffsetMinutes);
  if (time.offsetMinutes === null) return `${shown}（記録時のゾーンは不明）`;
  if (time.offsetMinutes === readerOffsetMinutes) return shown;
  // The recording zone is named whenever it differs, because a time silently restated in another
  // zone is a time two people will disagree about while both reading the same record.
  return `${shown}（記録時は ${offsetText(time.offsetMinutes)}）`;
}

/** The moment where it was recorded, with that zone named - for a line copied out of the product,
 *  where the reader is unknown. */
export function describeWhereRecorded(time: RecordedTime): string {
  if (time.offsetMinutes === null) return `${time.utc}（記録時のゾーンは不明）`;
  return `${inZone(time.utc, time.offsetMinutes)}（${offsetText(time.offsetMinutes)}）`;
}

function inZone(utc: string, offsetMinutes: number): string {
  const instant = Date.parse(utc);
  // Said rather than rendered as a date: a string that is not a time shown as a time is a plausible
  // value in place of a missing one (XC-001).
  if (Number.isNaN(instant)) return `${utc}（時刻として読めません）`;
  const shifted = new Date(instant + offsetMinutes * 60_000);
  return (
    `${shifted.getUTCFullYear()}-${pad(shifted.getUTCMonth() + 1)}-${pad(shifted.getUTCDate())}` +
    ` ${pad(shifted.getUTCHours())}:${pad(shifted.getUTCMinutes())}`
  );
}

const pad = (value: number): string => String(value).padStart(2, "0");
