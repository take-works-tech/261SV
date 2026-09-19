/* The wire form of a time the interface or the shell itself records (XC-142, XC-266): the same two
 * facts the engine writes - the UTC instant to the second, and the offset of the zone it was recorded
 * in - in the shape CT-001's $defs.recordedTime defines and generated.ts carries. Beside the generated
 * type rather than in ui-logic because the shell may reach the client layer and nothing above it
 * (01_boundaries.md); how a recorded time is *shown* to a person is ui-logic (logic/time.ts). */
import type { RecordedTime } from "./generated.js";

/** Minutes east of UTC where this process stands, as the platform reports it for that moment. */
export function offsetMinutesAt(now: Date = new Date()): number {
  return -now.getTimezoneOffset();
}

/** Now, as a recorded time: UTC to the second, with this zone's offset beside it. */
export function recordNow(now: Date = new Date()): RecordedTime {
  return recordInstant(now, now);
}

/** An instant that happened elsewhere - a file's modification time - recorded with the offset of
 *  whoever records it now. The file's own zone no filesystem keeps; the offset is "at the moment of
 *  writing" (XC-142), which is the recorder's (XC-266). */
export function recordInstant(instant: Date, where: Date = new Date()): RecordedTime {
  return { utc: instant.toISOString().replace(/\.\d{3}Z$/, "Z"), offsetMinutes: offsetMinutesAt(where) };
}

/** An offset as a person reads it: `UTC+09:00`, `UTC+05:45`, `UTC-03:30`. */
export function offsetText(minutes: number): string {
  const sign = minutes >= 0 ? "+" : "-";
  const absolute = Math.abs(minutes);
  return `UTC${sign}${String(Math.floor(absolute / 60)).padStart(2, "0")}:${String(absolute % 60).padStart(2, "0")}`;
}
