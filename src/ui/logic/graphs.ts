/* A graph's data as the interface draws it (XC-290): the engine's series - numbers in the internal unit
 * with the declared one beside, reduction, scope, weighting, digits, and each point's case or step -
 * turned into rows and chart geometry. Nothing is computed here beyond placing what the engine answered
 * on a canvas; a missing point is a gap with its reason, never a bridge (XC-001). No React, no transport. */
import type { Results } from "../client/engine";
import { formatValue } from "./format";

export type GraphData = Results["graph.data"];
export type GraphSeries = GraphData["series"][number];
export type GraphPoint = GraphSeries["points"][number];

export const REDUCTION_LABEL: Record<string, string> = { max: "最大", min: "最小", mean: "平均" };
/** How the engine chose the cases, as `graph.data` states it (graph/AC-008, XC-292). */
export const SELECTION_LABEL: Record<string, string> = { given: "グラフ自身の束縛", context: "この領域の対象ケース", loaded: "読み込まれた全ケース" };
const WEIGHTING_LABEL: Record<string, string> = { none: "重みなし", volume: "体積重み", dualVolume: "節点まわりの体積重み" };
const PROVENANCE_LABEL: Record<string, string> = { declared: "宣言値", dataset: "ファイル由来", computed: "計算値", measured: "実測値", reference: "参考資料由来" };

/** The legend line of one series: what it plots, in what unit, from where, reduced how (INV-013, INV-017). */
export function legendLine(series: GraphSeries, undeclared: string): string {
  const unit = series.unit ?? undeclared;
  const declared = series.declaredUnit && series.declaredUnit !== series.unit ? `（宣言 ${series.declaredUnit}）` : "";
  const reduction = series.reduction ? `・${REDUCTION_LABEL[series.reduction] ?? series.reduction}` : "";
  const weighting = series.weighting ? `・${WEIGHTING_LABEL[series.weighting] ?? series.weighting}` : "";
  const scope = series.scope ? `・${series.scope}` : "";
  const missing = series.points.filter((one) => one.value === null).length;
  // Entries the plotted numbers left out because they were missing, over the series (XC-303).
  const leftOut = series.points.reduce((sum, one) => sum + (one.missingCount ?? 0), 0);
  return `${series.label}［${unit}${declared}］${reduction}${weighting}${scope}・${PROVENANCE_LABEL[series.provenance] ?? series.provenance}` + (missing > 0 ? `・データなし ${missing} 点` : "") + (leftOut > 0 ? `・欠測 ${leftOut} 件を除いた値` : "");
}

/** Where a point sits on the horizontal axis: the result position for a graph over the axis, and
 *  the case's ordinal otherwise. Stated per graph, so the axis title says which. */
export function horizontal(data: GraphData): { title: string; of: (point: GraphPoint, index: number) => number; tick: (point: GraphPoint, index: number) => string } {
  const overAxis = data.series.some((series) => series.points.some((point) => point.resultPosition !== undefined));
  if (overAxis) {
    return {
      title: "結果軸の位置",
      of: (point, index) => (point.x === null || point.x === undefined ? index : point.x),
      tick: (point, index) => (point.resultPosition ? point.resultPosition.stated : point.x === null || point.x === undefined ? String(index) : String(point.x)),
    };
  }
  return { title: "ケース", of: (_point, index) => index, tick: (point) => point.caseId };
}

export interface ChartPoint {
  x: number;
  y: number | null;
  label: string;
  reason: string | null;
  /** What the drawn number left out, when it left anything out (XC-303). */
  note: string | null;
}

/** The point's own note: the entries its number left out, in the words the rail and the table use. */
export function pointNote(point: { missingCount?: number }): string | null {
  return point.missingCount ? `欠測 ${point.missingCount} 件を除く` : null;
}

/** One series as chart points in the order the engine gave them. */
export function chartPoints(data: GraphData, series: GraphSeries): ChartPoint[] {
  const axis = horizontal(data);
  return series.points.map((point, index) => ({
    x: axis.of(point, index),
    y: point.value === null || point.value === undefined ? null : point.value,
    label: axis.tick(point, index),
    reason: point.reason ?? null,
    note: pointNote(point),
  }));
}

/** The vertical range every drawn value fits, or null where nothing is drawn. Padded by a tenth so a
 *  flat series is a line and not the frame's edge; never invented from a missing point. */
export function verticalRange(data: GraphData): [number, number] | null {
  const values = data.series.flatMap((series) => series.points.map((point) => point.value)).filter((one): one is number => typeof one === "number" && Number.isFinite(one));
  if (values.length === 0) return null;
  const low = Math.min(...values);
  const high = Math.max(...values);
  const pad = high === low ? (Math.abs(high) || 1) * 0.1 : (high - low) * 0.1;
  return [low - pad, high + pad];
}

/** A value on the vertical axis at the digits its series carries (INV-014). */
export function tickValue(value: number, series: GraphSeries): string {
  return formatValue(value, series.digits ?? 6);
}

/** The rows a spreadsheet takes: one per point, with the unit, the reduction and the case or step. */
export function graphCopyRows(data: GraphData, undeclared: string): string[][] {
  const axis = horizontal(data);
  const rows: string[][] = [["系列", axis.title, "値", "単位", "宣言単位", "縮約", "範囲", "重み", "来歴", "注記"]];
  for (const series of data.series) {
    series.points.forEach((point, index) => {
      rows.push([
        series.label,
        axis.tick(point, index),
        point.value === null || point.value === undefined ? `値なし（${point.reason ?? "理由不明"}）` : tickValue(point.value, series),
        series.unit ?? undeclared,
        series.declaredUnit ?? "",
        series.reduction ? REDUCTION_LABEL[series.reduction] ?? series.reduction : "",
        series.scope ?? "",
        series.weighting ? WEIGHTING_LABEL[series.weighting] ?? series.weighting : "",
        PROVENANCE_LABEL[series.provenance] ?? series.provenance,
        [point.reason ?? null, pointNote(point)].filter((one): one is string => one !== null).join("；"),
      ]);
    });
  }
  return rows;
}
