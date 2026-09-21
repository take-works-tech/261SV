/* What a drop on the window means before anything is read (XC-291, ingest/AC-020, AC-021): a plan
 * from the paths alone - one workspace to open, one result file to inspect and then load into a case,
 * or a refusal that names why - decided here so the store executes and the screen reports. The
 * format's support is not judged here: the engine's `dataset.inspect` says it, and a file it names
 * as unsupported is refused with the engine's own words. No React and no transport. */

export const WORKSPACE_SUFFIX = ".svw";

export interface DroppedCase {
  readonly id: string;
  readonly name: string;
}

export type DropPlan =
  | { kind: "openWorkspace"; path: string }
  | { kind: "load"; path: string; caseId: string }
  | { kind: "refused"; reason: string };

export function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

function isWorkspace(path: string): boolean {
  return path.toLowerCase().endsWith(WORKSPACE_SUFFIX);
}

/** The one thing a drop asks for, or why it asks for nothing. One file at a time: a session reads
 *  one dataset into one case, and several files dropped together would load in an order nobody chose. */
export function dropPlan(paths: readonly string[], context: { workspaceOpen: boolean; cases: readonly DroppedCase[]; caseId: string | null }): DropPlan {
  if (paths.length === 0) return { kind: "refused", reason: "落とされたものにファイルがありません" };
  if (paths.length > 1) {
    return { kind: "refused", reason: `ファイルは 1 件ずつ落としてください（${paths.length} 件：${paths.map(fileName).join("、")}）。読む順は推測しません` };
  }
  const path = paths[0]!;
  if (isWorkspace(path)) return { kind: "openWorkspace", path };
  if (!context.workspaceOpen) {
    return { kind: "refused", reason: `${fileName(path)} を読み込む先のワークスペースが開いていません。先にワークスペース（${WORKSPACE_SUFFIX}）を開くか落としてください` };
  }
  const caseId = context.caseId ?? (context.cases.length === 1 ? context.cases[0]!.id : null);
  if (!caseId) {
    const names = context.cases.map((one) => `${one.name}（${one.id}）`).join("、");
    return { kind: "refused", reason: context.cases.length === 0 ? "このワークスペースにケースがありません" : `どのケースに読み込むか決まっていません（あるのは ${names}）。先に一つのケースへ読み込んでから落としてください` };
  }
  return { kind: "load", path, caseId };
}

/** Whether an inspection lets a load proceed: the engine names the level; `Absent` is a format this
 *  build has no reader for, and a file that is not there is not a file (AC-021). */
export function inspectionAllowsLoad(inspection: { exists: boolean; supportLevel: string; format: string; gaps: readonly string[]; refusal?: string }, path: string): string | null {
  if (!inspection.exists) return `${fileName(path)} がありません`;
  // The engine already knows the load would be refused - a path its library cannot take (XC-293).
  if (inspection.refusal) return inspection.refusal;
  if (inspection.supportLevel.toLowerCase() === "absent") {
    return `'.${inspection.format}' はこの版が読む形式ではありません（対応水準 ${inspection.supportLevel}）。部分的なケースは作りません（ingest/AC-021）`;
  }
  return null;
}
