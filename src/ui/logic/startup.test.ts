/* What the page says while the engine starts (XC-304): counted seconds, a slow start named as
 * slow without a promised time, and a failed start as its reason. */
import { describe, expect, test } from "vitest";

import { describeStartup, SLOW_AFTER_SECONDS } from "./startup";

describe("what the page says while the engine starts", () => {
  test("the seconds are counted down to the whole second, and an early wait promises nothing", () => {
    const early = describeStartup({ kind: "starting", since: null }, 1.9);
    expect(early.title).toBe("エンジンを起動しています（1 秒）");
    expect(early.slow).toBe(false);
    expect(early.failed).toBe(false);
    expect(early.detail).toContain("応答を待っています");
    expect(early.detail).not.toMatch(/以内|秒で起動/);
    expect(describeStartup({ kind: "unknown" }, -3).title).toBe("エンジンを起動しています（0 秒）");
  });

  test("past the slow mark the detail names what can take the time, and still promises no time", () => {
    const late = describeStartup({ kind: "unknown" }, SLOW_AFTER_SECONDS + 0.5);
    expect(late.slow).toBe(true);
    expect(late.detail).toContain("数百 MB");
    expect(late.detail).not.toMatch(/以内/);
    expect(describeStartup({ kind: "starting", since: null }, SLOW_AFTER_SECONDS - 1).slow).toBe(false);
  });

  test("a start that ended without an engine is its reason and nothing else", () => {
    const failed = describeStartup({ kind: "absent", because: "ポート 51234 に応答がありません" }, 12);
    expect(failed.failed).toBe(true);
    expect(failed.detail).toBe("ポート 51234 に応答がありません");
    const died = describeStartup({ kind: "exited", because: "起動中に終了コード 3 で終了しました", exitCode: 3, signal: null }, 2);
    expect(died.failed).toBe(true);
    expect(died.title).toContain("終了");
    expect(died.detail).toContain("終了コード 3");
  });
});
