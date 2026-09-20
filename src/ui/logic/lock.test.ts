/* The lock as a person reads it: who has it, what that means here, and whether taking it over is
 * theirs to decide (XC-241, XC-269). */
import { describe, expect, test } from "vitest";

import { OSAKA } from "./fixtures";
import { canTakeOver, describeHolder, describeLock } from "./lock";

const HANAKO = { processId: 4321, host: "pc9", user: "hanako", takenAt: { utc: "2026-09-18T00:00:00Z", offsetMinutes: OSAKA } };
const FILE = "D:/studies/bracket.svw.lock";

describe("the lock as a sentence", () => {
  test("a holder is named well enough to act on, with the time in the reader's zone", () => {
    expect(describeHolder({ state: "held", lockFile: FILE, holder: HANAKO }, OSAKA)).toBe("pc9 の hanako（プロセス 4321、2026-09-18 09:00 取得）");
  });

  test("held: read-only, and what that means", () => {
    const said = describeLock({ state: "held", lockFile: FILE, holder: HANAKO }, OSAKA);
    expect(said).toContain("hanako");
    expect(said).toContain("読み取り専用");
    expect(said).toContain("保存は拒まれ");
  });

  test("stale: the holder cannot be found, and nothing is broken on its own", () => {
    const said = describeLock({ state: "stale", lockFile: FILE, holder: HANAKO }, OSAKA);
    expect(said).toContain("見つかりません");
    expect(said).toContain("自動では解除しません");
  });

  test("unreadable: what could not be read is named", () => {
    expect(describeLock({ state: "unreadable", lockFile: FILE, detail: "Expecting value" })).toContain("Expecting value");
    expect(describeLock({ state: "free", lockFile: FILE })).toBe("編集できます");
  });
});

describe("whether taking over is a person's call here", () => {
  test("only a stale or unreadable lock is offered; a live holder's never", () => {
    expect(canTakeOver({ state: "stale", lockFile: FILE, holder: HANAKO })).toBe(true);
    expect(canTakeOver({ state: "unreadable", lockFile: FILE })).toBe(true);
    expect(canTakeOver({ state: "held", lockFile: FILE, holder: HANAKO })).toBe(false);
    expect(canTakeOver({ state: "free", lockFile: FILE })).toBe(false);
  });
});
