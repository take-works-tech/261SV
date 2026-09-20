/* The View area's footer from the store: what is shown and why it may be incomplete (XC-276). */
import { describe, expect, test } from "vitest";

import { snapshot, type EngineState } from "../state/engine";
import { reducedNote, viewFooter } from "./showing";

const REACHABLE: EngineState = { ...snapshot(), reachability: { kind: "reachable", protocols: ["3.6.0"] } };

const LOADED: EngineState = {
  ...REACHABLE,
  workspaceId: "ws:1",
  caseId: "case:1",
  datasetId: "dataset:0001",
  sourceName: "cube.vtu",
  fields: [
    { name: "temperature", association: "point", unit: "K" },
    { name: "stress", association: "cell", unit: null },
  ],
  fieldName: "temperature",
  colourMap: "viridis",
  viewId: "view:0001",
  imageUrl: "blob:frame",
};

describe("what the area shows", () => {
  test("no engine is no footer: the design states keep their own mock label", () => {
    expect(viewFooter(snapshot(), "単位未宣言")).toBeNull();
  });

  test("an engine with nothing open says so, and lists nothing incomplete", () => {
    expect(viewFooter(REACHABLE, "単位未宣言")).toEqual({ showing: "ワークスペースが開いていません", incomplete: [] });
  });

  test("the line names the workspace, the case, the dataset, the field with its unit and the look", () => {
    expect(viewFooter(LOADED, "単位未宣言")?.showing).toBe(
      "ワークスペース ws:1・ケース case:1・データセット cube.vtu・場 temperature（K）・viridis・向き：未保存（回しただけ）",
    );
    const kept = { ...LOADED, savedCamera: { position_m: [0, 0, 5], focalPoint_m: [0, 0, 0], viewUp: [0, 1, 0], projection: "perspective" as const } };
    expect(viewFooter(kept, "単位未宣言")?.showing).toContain("向き：保存済み");
    const noUnit = { ...LOADED, fieldName: "stress" };
    expect(viewFooter(noUnit, "単位未宣言")?.showing).toContain("場 stress（単位未宣言）");
  });
});

describe("why it may be incomplete", () => {
  test("nothing missing is an empty list, and each reason is an engine fact the store holds", () => {
    const whole = { ...LOADED, fields: [{ name: "temperature", association: "point" as const, unit: "K" }] };
    expect(viewFooter(whole, "単位未宣言")?.incomplete).toEqual([]);

    const less: EngineState = {
      ...LOADED,
      reduced: "表示は 1,000 三角形に縮約",
      partial: true,
      parts: [
        { name: "asm / Base / Zone", type: "part", path: ["asm", "Base", "Zone"], pointCount: 8, cellCount: 1 },
        { name: "asm / Base / Ghost", type: "absent", path: ["asm", "Base", "Ghost"], reason: "要素なし", pointCount: 0, cellCount: 0 },
      ],
      partVisibility: { "asm / Base / Zone": false },
      readOnly: true,
      imageUrl: null,
    };
    expect(viewFooter(less, "単位未宣言")?.incomplete).toEqual([
      "縮約表示：表示は 1,000 三角形に縮約（報告値は完全データから・INV-001）",
      "不完全なケース：欠け 1 件（asm / Base / Ghost（要素なし））",
      "非表示のパート 1 件（asm / Base / Zone）",
      "単位未宣言の場：stress（換算しない・XC-003）",
      "読み取り専用で開いています：保存は拒まれます",
      "絵はまだありません",
    ]);
  });

  test("the engine's statement that nothing was reduced is no reduction", () => {
    expect(reducedNote("全三角形を描画")).toBeNull();
    expect(reducedNote(null)).toBeNull();
    expect(reducedNote("表示は 1,000 三角形に縮約")).toBe("表示は 1,000 三角形に縮約");
  });
});
