/* The engine's answers about sending, as the pages show them: the exact content, never a summary,
 * and an empty audit that stays an empty list (XC-106, XC-267). */
import { describe, expect, test } from "vitest";

import { OSAKA } from "./fixtures";
import { auditLines, egressFacts, type Egress } from "./egress";

const NOTHING: Egress = {
  transportConfigured: false,
  offline: false,
  workspaceId: null,
  search: false,
  languageModel: false,
  updateCheck: false,
  hosts: [],
  withoutAsking: false,
  workspaceContent: false,
  auditEntries: 0,
  sentEntries: 0,
};

describe("the audit as table lines", () => {
  test("each entry keeps its exact content, its host and its time in the reader's zone, newest first", () => {
    const lines = auditLines(
      [
        { at: { utc: "2026-08-25T00:00:00Z", offsetMinutes: OSAKA }, purpose: "webSearch", host: "search.example.test", outcome: "refused", sent: "疲労限度", reason: "送信経路が構成されていません" },
        { at: { utc: "2026-08-25T01:00:00Z", offsetMinutes: OSAKA }, purpose: "webSearch", host: "search.example.test", outcome: "sent", sent: "JIS G 4305" },
      ],
      OSAKA,
    );

    expect(lines.map((one) => one.content)).toEqual(["JIS G 4305", "疲労限度"]);
    expect(lines[1]).toMatchObject({ at: "2026-08-25 09:00", purpose: "Web検索", host: "search.example.test", outcome: "refused", note: "送信経路が構成されていません" });
    expect(lines[0]?.note).toContain("送信済み");
  });

  test("a request refused before it was composed says so rather than showing an empty cell", () => {
    const [line] = auditLines([{ at: { utc: "2026-08-25T00:00:00Z", offsetMinutes: OSAKA }, purpose: "updateCheck", host: "update.example.test", outcome: "refused", reason: "許可がありません" }], OSAKA);

    expect(line?.content).toContain("送信内容なし");
    expect(line?.purpose).toBe("更新確認");
  });

  test("a query waiting for confirmation names what it withheld", () => {
    const [line] = auditLines([{ at: { utc: "2026-08-25T00:00:00Z", offsetMinutes: OSAKA }, purpose: "webSearch", host: "h", outcome: "awaitingConfirmation", sent: "［伏せた語］ の疲労限度", withheld: ["Run 12", "241.7"] }], OSAKA);

    expect(line?.outcome).toBe("awaiting");
    expect(line?.note).toBe("伏せた語 2 件：Run 12、241.7");
  });

  test("an empty audit is an empty list", () => {
    expect(auditLines([], OSAKA)).toEqual([]);
  });
});

describe("the sending policy as facts", () => {
  test("a build with no way out says so first, and everything else is what would be allowed", () => {
    const facts = Object.fromEntries(egressFacts(NOTHING).map((one) => [one.key, one]));

    expect(facts.transport?.value).toBe("なし");
    expect(facts.transport?.note).toContain("何も出られず");
    expect(facts.hosts?.value).toBe("なし");
    expect(facts.scope?.value).toBe("既定");
    expect(facts.audit?.value).toBe("0件（うち送信 0件）");
    expect(facts.audit?.note).toContain("一件も記録されていません");
  });

  test("a permitted workspace lists its hosts and how it confirms", () => {
    const facts = Object.fromEntries(
      egressFacts({ ...NOTHING, transportConfigured: true, workspaceId: "ws:1", search: true, hosts: ["docs.example.org"], auditEntries: 3, sentEntries: 1 }).map((one) => [one.key, one]),
    );

    expect(facts.transport?.value).toBe("あり");
    expect(facts.scope?.value).toBe("ws:1");
    expect(facts.search?.value).toBe("有効");
    expect(facts.search?.note).toContain("毎回");
    expect(facts.hosts?.value).toBe("1件");
    expect(facts.hosts?.note).toBe("docs.example.org");
    expect(facts.audit?.value).toBe("3件（うち送信 1件）");
  });
});
