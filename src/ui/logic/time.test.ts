/* The display of a recorded time, held to the same cases src/domain_core/recorded_time.py is held
 * to (tests/test_output_and_time.py): the two sides show the same text for the same time, and a
 * case added on one side is a case added on both. No engine, no browser - a rule that can only be
 * exercised by rendering a component is a rule nobody tests. */
import { describe, expect, test } from "vitest";

import { OSAKA } from "./fixtures";
import { offsetText, recordInstant, recordNow } from "../client/time";
import { describeRecorded, describeWhereRecorded } from "./time";

const NOON_UTC = { utc: "2026-08-24T12:00:00Z", offsetMinutes: OSAKA };

describe("a recorded time, as a person here reads it (XC-142, XC-266)", () => {
  test("in the reader's own zone, with nothing added when it is the recording zone", () => {
    expect(describeRecorded(NOON_UTC, OSAKA)).toBe("2026-08-24 21:00");
  });

  test("the recording zone is named when the reader's differs", () => {
    expect(describeRecorded(NOON_UTC, 120)).toBe("2026-08-24 14:00（記録時は UTC+09:00）");
  });

  test("a zone that is not a whole hour survives", () => {
    expect(describeRecorded({ utc: "2026-08-24T12:00:00Z", offsetMinutes: 345 }, 345)).toBe("2026-08-24 17:45");
    expect(offsetText(345)).toBe("UTC+05:45");
    expect(offsetText(-210)).toBe("UTC-03:30");
    expect(offsetText(0)).toBe("UTC+00:00");
  });

  test("a record that never kept its zone says so, and is never shown as Greenwich", () => {
    const unknown = { utc: "2026-08-24T12:00:00Z", offsetMinutes: null };
    expect(describeRecorded(unknown, OSAKA)).toBe("2026-08-24 21:00（記録時のゾーンは不明）");
    expect(describeWhereRecorded(unknown)).toBe("2026-08-24T12:00:00Z（記録時のゾーンは不明）");
  });

  test("where it was recorded, for a line read by anyone", () => {
    expect(describeWhereRecorded(NOON_UTC)).toBe("2026-08-24 21:00（UTC+09:00）");
  });

  test("a day boundary moves with the zone", () => {
    expect(describeRecorded({ utc: "2026-08-24T20:00:00Z", offsetMinutes: OSAKA }, OSAKA)).toBe("2026-08-25 05:00");
    expect(describeRecorded({ utc: "2026-08-24T02:00:00Z", offsetMinutes: -300 }, -300)).toBe("2026-08-23 21:00");
  });

  test("a string that is not a time is shown as what it is, not as a date", () => {
    expect(describeRecorded({ utc: "yesterday", offsetMinutes: 0 }, 0)).toBe("yesterday（時刻として読めません）");
  });
});

describe("what the interface and the shell record themselves", () => {
  test("now is UTC to the second, with this zone's offset beside it", () => {
    const at = new Date("2026-09-20T03:00:00.456Z");

    const recorded = recordNow(at);

    expect(recorded.utc).toBe("2026-09-20T03:00:00Z");
    expect(recorded.offsetMinutes).toBe(-at.getTimezoneOffset());
  });

  test("an instant from elsewhere takes the recorder's offset, not the instant's", () => {
    const where = new Date("2026-09-20T03:00:00Z");

    const recorded = recordInstant(new Date("2026-08-24T12:00:00.999Z"), where);

    expect(recorded.utc).toBe("2026-08-24T12:00:00Z");
    expect(recorded.offsetMinutes).toBe(-where.getTimezoneOffset());
  });
});
