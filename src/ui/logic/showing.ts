/* The View area's footer (16_application_model §3, §4; XC-276): what the area is showing now, and why
 * what it shows may be incomplete - every clause an engine answer the store already holds, none of
 * it computed here. No React and no transport. */
import type { EngineState } from "../state/engine";
import { absentParts } from "./parts";

/** The engine's own word for a picture that left nothing out (engine/visualization/render.py). A
 *  `reduced` statement that starts otherwise names what the picture dropped (INV-001). */
const NOTHING_REDUCED = "全三角形";

/** The reduction the picture carries, or null where it carries none. One test of the engine's
 *  statement, for the pane's marker and the footer alike. */
export function reducedNote(reduced: string | null): string | null {
  return reduced && !reduced.startsWith(NOTHING_REDUCED) ? reduced : null;
}

export interface Showing {
  /** One line: workspace, case, dataset, field with its unit, whether the look is the saved one. */
  showing: string;
  /** Each a reason the picture or the numbers may be less than the file holds, in the order a
   *  reader should weigh them. Empty when nothing is missing. */
  incomplete: string[];
}

/** What the View area shows and why it may be incomplete, or null where there is no engine to say
 *  (the design states keep their own mock label, 11_ui.md). `undeclared` is the interface's marker
 *  for a unit nobody declared (XC-003). */
export function viewFooter(state: EngineState, undeclared: string): Showing | null {
  if (state.reachability.kind !== "reachable") return null;
  if (!state.workspaceId) return { showing: "ワークスペースが開いていません", incomplete: [] };

  const showing: string[] = [`ワークスペース ${state.workspaceId}`];
  if (state.caseId) showing.push(`ケース ${state.caseId}`);
  showing.push(state.sourceName ? `データセット ${state.sourceName}` : "データセット未読込");
  if (state.fieldName) {
    const unit = state.fields.find((one) => one.name === state.fieldName)?.unit ?? null;
    showing.push(`場 ${state.fieldName}（${unit ?? undeclared}）・${state.colourMap}`);
  }
  if (state.viewId) showing.push(state.savedCamera ? "向き：保存済み" : "向き：未保存（回しただけ）");

  const incomplete: string[] = [];
  const reduced = reducedNote(state.reduced);
  if (reduced) incomplete.push(`縮約表示：${reduced}（報告値は完全データから・INV-001）`);
  if (state.partial) {
    const absent = absentParts(state.parts);
    incomplete.push(absent.length > 0 ? `不完全なケース：欠け ${absent.length} 件（${absent.join("、")}）` : "不完全なケース");
  }
  const hidden = Object.entries(state.partVisibility)
    .filter(([, shown]) => shown === false)
    .map(([name]) => name);
  if (hidden.length > 0) incomplete.push(`非表示のパート ${hidden.length} 件（${hidden.join("、")}）`);
  const withoutUnit = state.fields.filter((one) => one.unit === null).map((one) => one.name);
  if (withoutUnit.length > 0) incomplete.push(`単位未宣言の場：${withoutUnit.join("、")}（換算しない・XC-003）`);
  if (state.readOnly) incomplete.push("読み取り専用で開いています：保存は拒まれます");
  if (state.datasetId && !state.imageUrl) incomplete.push("絵はまだありません");
  return { showing: showing.join("・"), incomplete };
}
