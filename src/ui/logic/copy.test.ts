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
    // Every row says what it covered, so a pasted number is never a part's taken for the model's (INV-017).
    expect(rows[1]?.[6]).toBe("範囲：whole model・重み：dualVolume・点の上");
    expect(rows[3]).toEqual(["temperature（平均）", "4.5", "K", "6", "計算", "", "不完全なケース；式：volume-weighted mean；範囲：whole model・重み：dualVolume・点の上"]);
    expect(rows[4]).toEqual(["temperature（欠損数）", "0", "件", "整数", "計算", "", "範囲：whole model・重み：dualVolume・点の上"]);
  });

  test("a cell field's statistics carry both numbers, each labelled, and the spread with the disagreement", () => {
    const cell: Results["field.statistics"] = {
      ...STATISTICS,
      association: "cell",
      averaging: "unaveraged",
      maximum: { value: 200, unit: "MPa", digits: 6, provenance: "computed", formula: "extremum(stress)", location: "bar：cell 3" },
      averaged: {
        maximum: { value: 110, unit: "MPa", digits: 6, provenance: "computed", formula: "max(nodal-average(stress))", caveats: ["averaged"], location: "bar：point 12" },
        minimum: { value: 10, unit: "MPa", digits: 6, provenance: "computed", formula: "min(nodal-average(stress))", caveats: ["averaged"], location: "bar：point 0" },
        spreadAtMaximum: { value: 180, unit: "MPa", digits: 6, provenance: "computed", formula: "max - min at the node", location: "bar：point 12" },
        spreadFraction: { value: 180 / 110, unit: "1", digits: 6, provenance: "computed", formula: "spread / |average|" },
        disagreement: "節点平均と要素値で 90 MPa 違います（大きいほうの 45%）。どちらも正しく、答えている問いが違います",
      },
    };
    const rows = statisticsRows("stress", cell, LABELS);

    expect(rows.map((row) => row[0])).toEqual([
      "項目", "stress（最大・要素値（平均なし））", "stress（最小・要素値（平均なし））", "stress（平均・要素値（平均なし））", "stress（欠損数）",
      "stress（最大・節点平均）", "stress（最小・節点平均）", "stress（節点平均の最大でのばらつき・メッシュ細分の目安）",
    ]);
    expect(rows[1]?.[1]).toBe("200");
    expect(rows[5]?.slice(1, 3)).toEqual(["110", "MPa"]);
    expect(rows[5]?.[6]).toContain("averaged");
    expect(rows[7]?.[1]).toBe("180");
    expect(rows[7]?.[6]).toContain("平均比 164%");
    expect(rows[7]?.[6]).toContain("90 MPa");
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
