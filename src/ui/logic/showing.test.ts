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
  test("a case of several steps says which one is shown; a steady one says nothing about steps", () => {
    const described = {
      pointCount: 4, cellCount: 2, boundsM: { minM: [0, 0, 0], maxM: [1, 1, 0] }, partial: false,
      resultAxis: { kind: "undeclared" as const, positions: [0, 0.5], count: 2, unit: null },
    };
    // The engine's sentence where it answered for this step, and the ordinal alone where it has not.
    expect(viewFooter({ ...LOADED, described, step: 1 }, "単位未宣言")?.showing).toContain("・ステップ 2/2・");
    const stated = { step: 1, count: 2, kind: "undeclared" as const, value: 0.5, unit: null, stated: "ステップ 2/2（位置 0.5・軸の種類は宣言なし）" };
    const statistics = { ...(LOADED.statistics as object), resultPosition: stated } as NonNullable<EngineState["statistics"]>;
    expect(viewFooter({ ...LOADED, described, step: 1, statistics }, "単位未宣言")?.showing).toContain(
      "・ステップ 2/2（位置 0.5・軸の種類は宣言なし）・",
    );
    const steady = { ...described, resultAxis: { kind: "none" as const, unit: null } };
    expect(viewFooter({ ...LOADED, described: steady }, "単位未宣言")?.showing).not.toContain("ステップ");
  });

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
