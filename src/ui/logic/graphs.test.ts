/* A graph's data as rows and chart geometry: the engine's numbers placed, never computed (XC-290). */
import { describe, expect, test } from "vitest";

import { chartPoints, graphCopyRows, horizontal, legendLine, verticalRange } from "./graphs";

const POSITION = (step: number, count: number, value: number) => ({ step, count, kind: "undeclared" as const, value, unit: null, stated: `ステップ ${step + 1}/${count}（位置 ${value}・軸の種類は宣言なし）` });

const OVER_AXIS = {
  series: [
    {
      label: "応力の最大", unit: "Pa", declaredUnit: "MPa", provenance: "dataset" as const, reduction: "max" as const, scope: "ケース全体（1 パート）", weighting: "none", digits: 6,
      points: [
        { caseId: "case:1", x: 0, value: 90e6, resultPosition: POSITION(0, 2, 0) },
        { caseId: "case:1", x: 0.5, value: 91e6, resultPosition: POSITION(1, 2, 0.5) },
      ],
    },
  ],
  axisLabel: "Pa", cases: ["case:1"], selection: "loaded" as const, missing: [],
  resultAxisNote: "並べた結果のうち、軸の種類がファイルに宣言されていないものがあります。同じ軸である保証はありません",
};

const PER_CASE = {
  series: [
    { label: "温度の最大", unit: null, declaredUnit: null, provenance: "dataset" as const, reduction: "max" as const, scope: "ケース全体（1 パート）", weighting: "none", digits: 6, points: [{ caseId: "case:1", x: null, value: 8 }, { caseId: "case:9", x: null, value: null, reason: "ケース 'case:9' は読み込まれていません" }] },
  ],
  axisLabel: "単位未宣言", cases: ["case:1", "case:9"], selection: "given" as const, missing: ["温度の最大 / case:9：ケース 'case:9' は読み込まれていません"],
};

describe("the legend", () => {
  test("says the unit the numbers are in, the declared one beside, the reduction, the scope and the provenance", () => {
    expect(legendLine(OVER_AXIS.series[0]!, "単位未宣言")).toBe("応力の最大［Pa（宣言 MPa）］・最大・重みなし・ケース全体（1 パート）・ファイル由来");
    expect(legendLine(PER_CASE.series[0]!, "単位未宣言")).toBe("温度の最大［単位未宣言］・最大・重みなし・ケース全体（1 パート）・ファイル由来・データなし 1 点");
  });
});

describe("the horizontal axis", () => {
  test("is the result position where the points carry one, and the case otherwise", () => {
    const over = horizontal(OVER_AXIS);
    expect(over.title).toBe("結果軸の位置");
    expect(chartPoints(OVER_AXIS, OVER_AXIS.series[0]!).map((one) => [one.x, one.y, one.label])).toEqual([
      [0, 90e6, "ステップ 1/2（位置 0・軸の種類は宣言なし）"],
      [0.5, 91e6, "ステップ 2/2（位置 0.5・軸の種類は宣言なし）"],
    ]);
    const cases = horizontal(PER_CASE);
    expect(cases.title).toBe("ケース");
    expect(chartPoints(PER_CASE, PER_CASE.series[0]!).map((one) => [one.x, one.y, one.label, one.reason])).toEqual([
      [0, 8, "case:1", null],
      [1, null, "case:9", "ケース 'case:9' は読み込まれていません"],
    ]);
  });
});

describe("the vertical range and the rows", () => {
  test("the range fits every drawn value and ignores the missing ones; a flat series still has a height", () => {
    expect(verticalRange(OVER_AXIS)).toEqual([90e6 - 1e5, 91e6 + 1e5]);
    expect(verticalRange(PER_CASE)).toEqual([8 - 0.8, 8 + 0.8]);
    expect(verticalRange({ ...PER_CASE, series: [{ ...PER_CASE.series[0]!, points: [{ caseId: "case:9", x: null, value: null }] }] })).toBeNull();
  });

  test("the copy rows carry the unit, the declared unit, the reduction and a missing point as the stated absence", () => {
    const rows = graphCopyRows(PER_CASE, "単位未宣言");
    expect(rows[0]).toEqual(["系列", "ケース", "値", "単位", "宣言単位", "縮約", "範囲", "重み", "来歴", "注記"]);
    expect(rows[1]).toEqual(["温度の最大", "case:1", "8", "単位未宣言", "", "最大", "ケース全体（1 パート）", "重みなし", "ファイル由来", ""]);
    expect(rows[2]?.[2]).toBe("値なし（ケース 'case:9' は読み込まれていません）");
  });
});
