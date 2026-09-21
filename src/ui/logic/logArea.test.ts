/* The log area's lists: notices kept after dismissal, the log read back as sentences from the
 * engine's own facts, and the audit as rows (XC-286). */
import { describe, expect, test } from "vitest";

import type { Notice } from "../state/engine";
import { auditCopyRows, describeEntry, dismissedCount, logRows, omittedSentence, retentionSentence, visibleNotices } from "./logArea";

const AT = { utc: "2026-09-21T03:00:00Z", offsetMinutes: 540 };

const NOTICES: Notice[] = [
  { id: "notice:1", at: AT, severity: "warning", title: "注意", detail: "ケースは不完全です", operation: "dataset.load" },
  { id: "notice:2", at: AT, severity: "refusal", title: "拒否", detail: "3 成分の場は一つの数ではありません", operation: "field.statistics", dismissedAt: AT },
  { id: "notice:3", at: AT, severity: "error", title: "失敗", detail: "接続が切れました" },
];

const ANSWER = {
  entries: [
    { at: AT, level: "info" as const, event: "engine.start", context: { pid: 4242, protocol: "3.11.0" } },
    { at: AT, level: "warning" as const, event: "command", context: { operation: "dataset.describe", origin: "interface", status: "refused", reason: "ない", undoId: null, dryRun: false } },
    { at: AT, level: "warning" as const, event: "warning", context: { operation: "dataset.load", origin: "interface", text: "ケースは不完全です" } },
    { at: AT, level: "warning" as const, event: "egress", context: { purpose: "webSearch", host: "search.example.test", outcome: "refused", reason: "許可なし", withheld: 2 } },
  ],
  source: "file" as const,
  logDirectory: "D:/logs",
  files: 2,
  retainDays: 7,
  omitted: 3,
  unreadable: 1,
};

describe("notices kept after dismissal", () => {
  test("a dismissed notice is hidden by default, kept, and shown when asked for", () => {
    expect(visibleNotices(NOTICES, false).map((one) => one.id)).toEqual(["notice:3", "notice:1"]);
    expect(visibleNotices(NOTICES, true).map((one) => one.id)).toEqual(["notice:3", "notice:2", "notice:1"]);
    expect(dismissedCount(NOTICES)).toBe(1);
  });
});

describe("the log read back", () => {
  test("each event is a sentence from its own names and outcomes, newest first", () => {
    const rows = logRows(ANSWER, 540);
    expect(rows.map((one) => one.event)).toEqual(["外部要求", "注意", "命令", "エンジン起動"]);
    expect(rows[0]?.text).toBe("webSearch → search.example.test：拒否（許可なし）・伏せた語 2 件");
    expect(rows[1]?.text).toBe("dataset.load：ケースは不完全です");
    expect(rows[2]?.text).toBe("dataset.describe → 拒否：ない");
    expect(rows[2]?.levelLabel).toBe("警告");
    expect(rows[3]?.text).toBe("pid=4242、protocol=3.11.0");
  });

  test("a dry run says so, and a command without a reason ends at its outcome", () => {
    expect(describeEntry({ at: AT, level: "info", event: "command", context: { operation: "view.render", status: "answered", dryRun: true } })).toBe("view.render → 応答（試算）");
  });

  test("whether the log outlives the window is the engine's fact, and what the read left out is counted", () => {
    expect(retentionSentence(ANSWER)).toContain("D:/logs");
    expect(retentionSentence(ANSWER)).toContain("7 日");
    expect(retentionSentence({ ...ANSWER, source: "memory", logDirectory: null })).toContain("閉じると消えます");
    expect(omittedSentence(ANSWER)).toBe("上限で省略した古い行 3 件（since で絞れます）・読めなかった行 1 件（途中で切れた書き込み・推測はしません）");
    expect(omittedSentence({ ...ANSWER, omitted: 0, unreadable: 0 })).toBeNull();
  });
});

describe("the audit as rows", () => {
  test("carries the header and one row per decision, the content as it was", () => {
    const rows = auditCopyRows([
      { id: "a", at: "2026-09-21 12:00", purpose: "Web検索", host: "search.example.test", outcome: "refused", content: "（送信内容なし）", note: "許可なし" },
    ]);
    expect(rows[0]).toEqual(["時刻", "目的", "宛先", "結果", "内容", "注記"]);
    expect(rows[1]).toEqual(["2026-09-21 12:00", "Web検索", "search.example.test", "拒否", "（送信内容なし）", "許可なし"]);
  });
});
