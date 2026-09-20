/* The report area's facts from the engine's answers (16_application_model §7.5, XC-275): the block
 * list as rows a person edits, the edits as new block lists, and the trust content as sentences.
 * Nothing here computes a value: what a block will show is either an engine answer already held or
 * "computed at export", said as such (INV-001). No React and no transport. */
import type { ReportBlock, ReportDefinition, SavedView } from "../state/engine";
import type { Results } from "../client/engine";
import { describeRecorded } from "./time";

export type Provenance = Results["report.provenance"];

export const BLOCK_LABEL: Record<ReportBlock["kind"], string> = {
  view: "ビュー",
  graph: "グラフ",
  valueTable: "数値表",
  text: "本文",
  pageBreak: "改ページ",
};

/** One row of the contents rail: the block, what it refers to, and whether that resolves. */
export interface BlockRow {
  index: number;
  kind: ReportBlock["kind"];
  name: string;
  detail: string;
  /** Why the reference does not resolve, or null. A block is never dropped for it (§7.5). */
  unresolved: string | null;
}

/** The rows of the block list. A view block names the view by its document name where the document
 *  holds it; a block whose view the document no longer holds is listed as unresolved. */
export function blockRows(
  definition: ReportDefinition,
  savedViews: readonly SavedView[],
  currentViewId: string | null,
): BlockRow[] {
  return definition.blocks.map((block, index) => {
    const kind = block.kind;
    switch (kind) {
      case "view": {
        const saved = savedViews.find((one) => one.id === block.viewId);
        const known = saved !== undefined || (currentViewId !== null && block.viewId === currentViewId);
        return {
          index,
          kind,
          name: BLOCK_LABEL.view,
          detail: `${saved ? `「${saved.name}」` : block.viewId ?? "（参照なし）"}・${FORM_LABEL[block.form ?? "still"] ?? block.form ?? ""}`,
          unresolved: known ? null : `ビュー ${block.viewId ?? "（未指定）"} は文書にありません`,
        };
      }
      case "valueTable":
        return {
          index,
          kind,
          name: BLOCK_LABEL.valueTable,
          detail: (block.fields ?? []).length > 0 ? (block.fields ?? []).join("、") : "（場の指定なし）",
          unresolved: (block.fields ?? []).length > 0 ? null : "場が指定されていません",
        };
      case "text":
        return { index, kind, name: BLOCK_LABEL.text, detail: excerpt(block.text ?? ""), unresolved: null };
      case "graph":
        return { index, kind, name: BLOCK_LABEL.graph, detail: block.graphId ?? "（参照なし）", unresolved: "この版はグラフを描きません" };
      default:
        return { index, kind, name: BLOCK_LABEL.pageBreak, detail: "", unresolved: null };
    }
  });
}

const FORM_LABEL: Record<string, string> = { still: "静止画", video: "動画", interactive: "インタラクティブ 3D" };

function excerpt(text: string): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > 24 ? `${flat.slice(0, 24)}…` : flat || "（空）";
}

/** The block list with one block moved by `delta` places; unchanged where the move leaves the list. */
export function moveBlock(blocks: readonly ReportBlock[], index: number, delta: number): ReportBlock[] {
  const target = index + delta;
  if (index < 0 || index >= blocks.length || target < 0 || target >= blocks.length) return [...blocks];
  const next = [...blocks];
  const moved = next[index];
  const other = next[target];
  if (moved === undefined || other === undefined) return next;
  next[index] = other;
  next[target] = moved;
  return next;
}

export function removeBlock(blocks: readonly ReportBlock[], index: number): ReportBlock[] {
  return blocks.filter((_, at) => at !== index);
}

export function replaceBlock(blocks: readonly ReportBlock[], index: number, block: ReportBlock): ReportBlock[] {
  return blocks.map((one, at) => (at === index ? block : one));
}

/** One line per fact of the trust content, as the engine answered it (report/AC-007). The times are
 *  shown in the reader's zone with the recording zone named where it differs (XC-266). */
export interface TrustFacts {
  workspace: string;
  cases: string;
  sources: { path: string; modified: string }[];
  declaredUnits: { quantity: string; unit: string }[];
  produced: string;
  productVersion: string;
}

export function trustFacts(provenance: Provenance, readerOffsetMinutes?: number): TrustFacts {
  return {
    workspace: provenance.workspaceId || "（ワークスペースなし）",
    cases: provenance.caseIds.length > 0 ? provenance.caseIds.join("、") : "（ケースなし）",
    sources: provenance.sources.map((one) => ({ path: one.path, modified: describeRecorded(one.modified, readerOffsetMinutes) })),
    // The contract types the map's values as strings; the generated type keeps them open.
    declaredUnits: Object.entries(provenance.declaredUnits).map(([quantity, unit]) => ({ quantity, unit: String(unit) })),
    produced: describeRecorded(provenance.produced, readerOffsetMinutes),
    productVersion: provenance.productVersion,
  };
}

/** Whether the mandatory content can be produced now, and why not where it cannot: the item that
 *  cannot be produced blocks the export and names itself (§7.5, report/AC-031). */
export function trustReadiness(provenance: Provenance | null, refusal: string | null): { ready: boolean; because: string } {
  if (provenance) return { ready: true, because: "来歴・宣言単位・製品版はエンジンが答えました。制約は書き出し時に文書へ記録されます" };
  return { ready: false, because: refusal ? `来歴を作れません：${refusal}` : "来歴をまだエンジンに問い合わせていません" };
}
