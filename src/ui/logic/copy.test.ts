/* Values as a spreadsheet takes them: the engine's digits, the unit or the marker, the provenance,
 * and a missing value said as one (XC-279). */
import { describe, expect, test } from "vitest";

import { HEADER, probeRows, reportedRow, statisticsRows, structureRows, tsv } from "./copy";
import type { InformationView } from "./information";
import type { Reported } from "../state/engine";
import type { Results } from "../client/engine";

const LABELS = { undeclared: "単位未宣言", provenance: { dataset: "データ", computed: "計算", declared: "宣言" } };

const EIGHT: Reported = { value: 8, unit: "K", digits: 6, provenance: "dataset", location: "GlobalNodeId 7" };
const NONE: Reported = { value: null, unit: null, digits: 1, provenance: "computed", missingBecause: "モデルの外" };

const STATISTICS: Results["field.statistics"] = {
  minimum: { value: 1, unit: "K", digits: 6, provenance: "dataset" },
  maximum: { value: 8, unit: "K", digits: 6, provenance: "dataset", location: "GlobalNodeId 7" },
  mean: { value: 4.5, unit: "K", digits: 6, provenance: "computed", formula: "volume-weighted mean", caveats: ["不完全なケース"] },
  missingCount: 0,
  association: "point",
  reduction: "none",
  weighting: "dualVolume",
  scope: "whole model",
};

describe("one value as a row", () => {
  test("the value at its digits, the unit, the provenance label and the location travel together", () => {
    expect(reportedRow("temperature", EIGHT, LABELS)).toEqual(["temperature", "8", "K", "6", "データ", "GlobalNodeId 7", ""]);
  });

  test("a missing value is the stated absence, never a blank, and no unit is the marker", () => {
    expect(reportedRow("stress", NONE, LABELS)).toEqual(["stress", "値なし（モデルの外）", "単位未宣言", "1", "計算", "", ""]);
  });

  test("a provenance the labels do not know is written as the contract's own word", () => {
    expect(reportedRow("x", { ...EIGHT, provenance: "measured" }, LABELS)[4]).toBe("measured");
  });
});

describe("the tables", () => {
  test("statistics: header, three values, and the missing count as an integer with the scope beside it", () => {
    const rows = statisticsRows("temperature", STATISTICS, LABELS);

    expect(rows[0]).toEqual([...HEADER]);
    expect(rows.map((row) => row[0])).toEqual(["項目", "temperature（最大）", "temperature（最小）", "temperature（平均）", "temperature（欠損数）"]);
    expect(rows[3]).toEqual(["temperature（平均）", "4.5", "K", "6", "計算", "", "不完全なケース；式：volume-weighted mean"]);
    expect(rows[4]).toEqual(["temperature（欠損数）", "0", "件", "整数", "計算", "", "範囲：whole model・重み：dualVolume・点の上"]);
  });

  test("probe: the readout's location fills in where the value carries none", () => {
    expect(probeRows("temperature", { ...EIGHT, location: undefined }, "節点（番号なし）", LABELS)[1]?.[5]).toBe("節点（番号なし）");
    expect(probeRows("temperature", EIGHT, "elsewhere", LABELS)[1]?.[5]).toBe("GlobalNodeId 7");
  });

  test("structure: counts as integers, bounds as the engine gave them, an absent part as a stated absence", () => {
    const view: InformationView = {
      file: { name: "cube.vtu", path: null, format: ".vtu", supportLevel: "verified", supportLabel: "検証済み", supportNote: "", gaps: [] },
      structure: { points: 8, cells: 1, bounds: [{ axis: "X", min: 0, max: 1.25 }], partial: true },
      parts: [
        { name: "cube", present: true, reason: null, points: 8, cells: 1 },
        { name: "asm / Ghost", present: false, reason: "要素なし", points: 0, cells: 0 },
      ],
      fields: [],
      axis: null,
      notAnswered: [],
    };
    const rows = structureRows(view, LABELS);

    expect(rows[1]).toEqual(["節点数", "8", "件", "整数", "データ", "cube.vtu", ""]);
    expect(rows[3]).toEqual(["範囲 X（最小）", "0", "m", "答えのまま", "計算", "正準フレーム", ""]);
    expect(rows[4]?.[1]).toBe("1.25");
    expect(rows[7]).toEqual(["パート asm / Ghost（節点数）", "値なし（要素なし）", "件", "整数", "データ", "asm / Ghost", "欠け"]);
  });
});

describe("the text", () => {
  test("tab-separated lines, with a tab or a line break inside a cell made a space", () => {
    expect(tsv([["a", "b"], ["c\td", "e\nf"]])).toBe("a\tb\nc d\te f");
  });
});
