/* The report area's facts: rows from the document's block list, edits as new lists, and the trust
 * content as the engine answered it (XC-275). */
import { describe, expect, test } from "vitest";

import { OSAKA } from "./fixtures";
import { blockRows, moveBlock, removeBlock, replaceBlock, trustFacts, trustReadiness, type Provenance } from "./report";
import type { ReportDefinition } from "../state/engine";

const REPORT: ReportDefinition = {
  id: "report:0001",
  name: "cube.vtu",
  targets: ["html"],
  blocks: [
    { kind: "view", viewId: "view:0001", form: "still" },
    { kind: "valueTable", fields: ["temperature"] },
    { kind: "text", text: "  隅部の温度は  宣言された単位で示す。\n二行目。" },
    { kind: "view", viewId: "view:gone", form: "video" },
    { kind: "pageBreak" },
  ],
};

const PROVENANCE: Provenance = {
  workspaceId: "ws:1",
  caseIds: ["case:1"],
  sources: [{ path: "D:/studies/cube.vtu", modified: { utc: "2026-09-18T00:00:00Z", offsetMinutes: OSAKA } }],
  declaredUnits: { temperature: "K" },
  productVersion: "0.4.0",
  produced: { utc: "2026-09-20T03:00:00Z", offsetMinutes: OSAKA },
};

describe("the block list as rows", () => {
  test("each block names what it refers to, by the document's name where the document holds it", () => {
    const rows = blockRows(REPORT, [{ id: "view:0001", name: "temperature" }], null);

    expect(rows.map((one) => `${one.name}:${one.detail}`)).toEqual([
      "ビュー:「temperature」・静止画",
      "数値表:temperature",
      "本文:隅部の温度は 宣言された単位で示す。 二行目。",
      "ビュー:view:gone・動画",
      "改ページ:",
    ]);
  });

  test("a long passage is cut for the row, and only there", () => {
    const long = { ...REPORT, blocks: [{ kind: "text" as const, text: "あ".repeat(30) }] };
    expect(blockRows(long, [], null)[0]?.detail).toBe(`${"あ".repeat(24)}…`);
  });

  test("a view the document no longer holds is listed as unresolved, never dropped; the current view resolves", () => {
    const rows = blockRows(REPORT, [], "view:0001");

    expect(rows[0]?.unresolved).toBeNull();
    expect(rows[3]?.unresolved).toContain("view:gone");
    expect(rows).toHaveLength(5);
  });
});

describe("edits as new block lists", () => {
  test("moving swaps neighbours and leaves the list where the move falls off its end", () => {
    expect(moveBlock(REPORT.blocks, 1, -1).map((one) => one.kind)).toEqual(["valueTable", "view", "text", "view", "pageBreak"]);
    expect(moveBlock(REPORT.blocks, 0, -1)).toEqual(REPORT.blocks);
    expect(moveBlock(REPORT.blocks, 4, 1)).toEqual(REPORT.blocks);
  });

  test("removing and replacing touch one block and nothing else", () => {
    expect(removeBlock(REPORT.blocks, 2).map((one) => one.kind)).toEqual(["view", "valueTable", "view", "pageBreak"]);
    expect(replaceBlock(REPORT.blocks, 2, { kind: "text", text: "改めた。" })[2]).toEqual({ kind: "text", text: "改めた。" });
    expect(replaceBlock(REPORT.blocks, 2, { kind: "text", text: "改めた。" })[1]).toBe(REPORT.blocks[1]);
  });
});

describe("the trust content as the engine answered it", () => {
  test("every fact is the engine's, with the times in the reader's zone", () => {
    const facts = trustFacts(PROVENANCE, OSAKA);

    expect(facts).toEqual({
      workspace: "ws:1",
      cases: "case:1",
      sources: [{ path: "D:/studies/cube.vtu", modified: "2026-09-18 09:00" }],
      declaredUnits: [{ quantity: "temperature", unit: "K" }],
      produced: "2026-09-20 12:00",
      productVersion: "0.4.0",
    });
  });

  test("what cannot be produced names itself as the item that blocks the export", () => {
    expect(trustReadiness(PROVENANCE, null).ready).toBe(true);
    const blocked = trustReadiness(null, "値の表はデータセットを一つ要りますが、0 件が読み込まれています");
    expect(blocked.ready).toBe(false);
    expect(blocked.because).toContain("来歴を作れません");
    expect(blocked.because).toContain("0 件");
    expect(trustReadiness(null, null).because).toContain("まだ");
  });
});
