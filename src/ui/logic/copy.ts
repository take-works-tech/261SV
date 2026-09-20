/* Values as a spreadsheet takes them (XC-279): tab-separated rows, each value at the digits it
 * honestly carries, with its unit or the undeclared marker, its provenance, its location and its
 * caveats - and a missing value as the stated absence, never a blank cell (XC-001, INV-014). The
 * labels come from the caller, so this layer names nothing the interface already names. No React
 * and no transport here. */
import type { Results } from "../client/engine";
import type { Reported } from "../state/engine";
import type { InformationView } from "./information";
import { formatValue } from "./format";

export interface CopyLabels {
  undeclared: string;
  provenance: Readonly<Record<string, string>>;
}

export const HEADER: readonly string[] = ["項目", "値", "単位", "有効桁", "来歴", "位置", "注記"];

/** One reported value as a row. The value is written at its own digits, as the screen shows it;
 *  `scope` - what the number covered - goes into the notes where the caller has one (INV-017). */
export function reportedRow(label: string, reported: Reported, labels: CopyLabels, scope?: string): string[] {
  const notes = [
    ...(reported.caveats ?? []),
    ...(reported.formula ? [`式：${reported.formula}`] : []),
    ...(scope ? [`範囲：${scope}`] : []),
  ];
  return [
    label,
    reported.value === null ? `値なし（${reported.missingBecause ?? "理由不明"}）` : formatValue(reported.value, reported.digits),
    reported.unit ?? labels.undeclared,
    String(reported.digits),
    labels.provenance[reported.provenance] ?? reported.provenance,
    reported.location ?? "",
    notes.join("；"),
  ];
}

const ASSOCIATION_WORD: Record<string, string> = { point: "点", cell: "要素" };

/** The field's statistics as rows: the three values, and the missing count as the integer it is.
 *  For a cell field both numbers travel, each labelled, the averaged ones with the spread at the
 *  peak and the sentence that says how far the maxima disagree (INV-032, XC-281). */
export function statisticsRows(fieldName: string, statistics: Results["field.statistics"], labels: CopyLabels): string[][] {
  const scope = `${statistics.scope}・重み：${statistics.weighting}・${ASSOCIATION_WORD[statistics.association] ?? statistics.association}の上`;
  const element = statistics.averaging === "unaveraged" ? "・要素値（平均なし）" : "";
  const rows = [
    [...HEADER],
    reportedRow(`${fieldName}（最大${element}）`, statistics.maximum, labels, scope),
    reportedRow(`${fieldName}（最小${element}）`, statistics.minimum, labels, scope),
    reportedRow(`${fieldName}（平均${element}）`, statistics.mean, labels, scope),
    [`${fieldName}（欠損数）`, String(statistics.missingCount), "件", "整数", labels.provenance["computed"] ?? "computed", "", `範囲：${scope}`],
  ];
  const averaged = statistics.averaged;
  if (averaged) {
    rows.push(reportedRow(`${fieldName}（最大・節点平均）`, averaged.maximum, labels, scope));
    rows.push(reportedRow(`${fieldName}（最小・節点平均）`, averaged.minimum, labels, scope));
    const spread = reportedRow(`${fieldName}（節点平均の最大でのばらつき・メッシュ細分の目安）`, averaged.spreadAtMaximum, labels, scope);
    spread[6] = [spread[6], averaged.spreadFraction.value === null ? "" : `平均比 ${Math.round(averaged.spreadFraction.value * 100)}%`, averaged.disagreement]
      .filter((one) => one !== "")
      .join("；");
    rows.push(spread);
  } else if (statistics.averagingRefused) {
    rows.push([`${fieldName}（最大・節点平均）`, `値なし（${statistics.averagingRefused}）`, statistics.maximum.unit ?? labels.undeclared, "", labels.provenance["computed"] ?? "computed", "", `範囲：${scope}`]);
  }
  return rows;
}

/** The probed value as one row, with the location the readout shows where the value carries none. */
export function probeRows(fieldName: string, reported: Reported, location: string | null, labels: CopyLabels): string[][] {
  const row = reportedRow(`${fieldName}（プローブ）`, reported, labels);
  if (location && row[5] === "") row[5] = location;
  return [[...HEADER], row];
}

/** What the file holds, as the information area shows it: counts as integers, bounds as the engine
 *  gave them (no digits were answered for them, so none are claimed). */
export function structureRows(view: InformationView, labels: CopyLabels): string[][] {
  const rows: string[][] = [[...HEADER]];
  const dataset = labels.provenance["dataset"] ?? "dataset";
  if (view.structure) {
    rows.push(["節点数", String(view.structure.points), "件", "整数", dataset, view.file.name, ""]);
    rows.push(["要素数", String(view.structure.cells), "件", "整数", dataset, view.file.name, ""]);
    for (const bound of view.structure.bounds ?? []) {
      rows.push([`範囲 ${bound.axis}（最小）`, String(bound.min), "m", "答えのまま", labels.provenance["computed"] ?? "computed", "正準フレーム", ""]);
      rows.push([`範囲 ${bound.axis}（最大）`, String(bound.max), "m", "答えのまま", labels.provenance["computed"] ?? "computed", "正準フレーム", ""]);
    }
  }
  for (const part of view.parts) {
    rows.push([
      `パート ${part.name}（節点数）`,
      part.present ? String(part.points) : `値なし（${part.reason ?? "読めなかったパート"}）`,
      "件", "整数", dataset, part.name, part.present ? "" : "欠け",
    ]);
    rows.push([
      `パート ${part.name}（要素数）`,
      part.present ? String(part.cells) : `値なし（${part.reason ?? "読めなかったパート"}）`,
      "件", "整数", dataset, part.name, part.present ? "" : "欠け",
    ]);
  }
  return rows;
}

/** Tab-separated lines. A tab or a line break inside a cell becomes a space, so the grid a
 *  spreadsheet reads is the grid these rows are. */
export function tsv(rows: readonly (readonly string[])[]): string {
  return rows.map((row) => row.map((cell) => cell.replace(/[\t\r\n]+/g, " ")).join("\t")).join("\n");
}
