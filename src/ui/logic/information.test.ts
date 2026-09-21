/* The information view: the engine's answers as the area's facts, and what the contract does not
 * carry named rather than filled (XC-273). No engine: the store's empty state is the starting point. */
import { describe, expect, test } from "vitest";

import { snapshot } from "../state/engine";
import { informationOf, NOT_ANSWERED } from "./information";

const LOADED = {
  ...snapshot(),
  datasetId: "dataset:0001",
  sourceName: "cube.vtu",
  opened: { workspacePath: "D:/studies/beam.svw", loads: [{ caseId: "case:1", filePath: "D:/studies/cube.vtu" }] },
  caseId: "case:1",
  loaded: {
    "case:1": {
      caseId: "case:1", datasetId: "dataset:0001", filePath: "D:/studies/cube.vtu", sourceName: "cube.vtu", supportLevel: "verified",
      gaps: [], fields: [], derived: {}, described: null, parts: null, partial: false, bounds: null, fieldName: null,
    },
  },
  supportLevel: "verified",
  gaps: [],
  fields: [
    { name: "temperature", association: "point" as const, unit: null },
    { name: "stress", association: "cell" as const, unit: "MPa" },
  ],
  described: {
    pointCount: 8,
    cellCount: 1,
    boundsM: { minM: [0, 0, 0], maxM: [1, 1, 1] },
    partial: false,
    resultAxis: { kind: "time" as const, positions: [0, 0.5, 1], unit: "s" },
  },
  parts: [
    { name: "cube", type: "part", path: ["cube"], pointCount: 8, cellCount: 1 },
    { name: "assembly / Base / Ghost", type: "absent", path: ["assembly", "Base", "Ghost"], parentId: "assembly / Base", reason: "要素なし", pointCount: 0, cellCount: 0 },
  ],
};

describe("what the loaded dataset holds", () => {
  test("nothing loaded is no view, not an empty one", () => {
    expect(informationOf(snapshot())).toBeNull();
  });

  test("the file, the structure, the parts, the fields and the axis come from the engine's answers", () => {
    const view = informationOf(LOADED);

    expect(view?.file).toMatchObject({ name: "cube.vtu", format: ".vtu", supportLabel: "検証済み", path: "D:/studies/cube.vtu" });
    expect(view?.structure).toMatchObject({ points: 8, cells: 1, partial: false });
    expect(view?.structure?.bounds?.map((one) => `${one.axis}:${one.min}..${one.max}`)).toEqual(["X:0..1", "Y:0..1", "Z:0..1"]);
    expect(view?.parts.map((one) => `${one.present}/${one.reason ?? "-"}`)).toEqual(["true/-", "false/要素なし"]);
    expect(view?.fields.map((one) => `${one.name}/${one.associationLabel}/${one.unit ?? "未宣言"}`)).toEqual([
      "temperature/点/未宣言",
      "stress/要素/MPa",
    ]);
    expect(view?.axis).toMatchObject({ kind: "time", label: "時刻", positions: 3, first: 0, last: 1, unit: "s" });
  });

  test("what the contract does not carry is named, never filled", () => {
    const view = informationOf(LOADED);

    expect(view?.notAnswered).toEqual(NOT_ANSWERED);
    expect(view?.notAnswered.map((one) => one.what)).toContain("元ファイルのチェックサム");
    expect(JSON.stringify(view)).not.toContain("vtkEnSightGoldBinaryReader");
  });

  test("a support level the engine did not say is said to be missing, and an unknown axis kind is shown as given", () => {
    const view = informationOf({ ...LOADED, supportLevel: null, described: { ...LOADED.described, resultAxis: { kind: "none" as const } } });

    expect(view?.file.supportLabel).toBe("不明");
    expect(view?.axis).toMatchObject({ kind: "none", label: "結果軸なし", positions: null, first: null, last: null });
  });
});
