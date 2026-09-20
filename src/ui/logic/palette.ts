/* The command palette's rows (XC-278): every operation of CT-003, and for each whether this screen
 * can run it now - its parameters filled from what the interface holds, never typed or guessed - with
 * the reason where it cannot. No React and no transport here. */
import { OPERATIONS, OPERATION_FACTS, type Operation } from "../client/generated";
import { STATUS_LABEL, type Answering } from "./commands";

/** What the interface knows now and can hand an operation, by the parameter's own name. */
export interface Context {
  workspaceId: string | null;
  caseId: string | null;
  datasetId: string | null;
  viewId: string | null;
  reportId: string | null;
  fieldName: string | null;
}

/** Operations the palette never runs: they delete, and CT-002 wants a confirmation that names what.
 *  The settings' output section is where that confirmation is. */
export const NEVER_FROM_PALETTE: readonly Operation[] = ["output.prune"];

export interface PaletteRow {
  operation: Operation;
  writes: boolean;
  /** The parameters the run would send, filled from the context. */
  parameters: Record<string, string>;
  runnable: boolean;
  /** Why the row cannot run now, or null. */
  because: string | null;
}

function valueOf(context: Context, name: string): string | null {
  switch (name) {
    case "workspaceId": return context.workspaceId;
    case "caseId": return context.caseId;
    case "datasetId": return context.datasetId;
    case "viewId": return context.viewId;
    case "reportId": return context.reportId;
    case "fieldName": return context.fieldName;
    default: return null;
  }
}

/** The rows, in catalogue order, filtered by a query against the operation's name. */
export function paletteRows(answering: Answering, context: Context, query: string): PaletteRow[] {
  const needle = query.trim().toLowerCase();
  const rows: PaletteRow[] = [];
  for (const operation of OPERATIONS) {
    if (needle !== "" && !operation.toLowerCase().includes(needle)) continue;
    const facts = OPERATION_FACTS[operation];
    const parameters: Record<string, string> = {};
    const missing: string[] = [];
    for (const name of facts.required) {
      const value = valueOf(context, name);
      if (value === null) missing.push(name);
      else parameters[name] = value;
    }
    for (const name of facts.optional) {
      const value = valueOf(context, name);
      if (value !== null) parameters[name] = value;
    }
    let because: string | null = null;
    if (NEVER_FROM_PALETTE.includes(operation)) {
      because = "破壊的な操作は、消すものを名指しする確認を経てだけ実行します（設定の出力から）";
    } else if (!answering) {
      because = "エンジンに接続していません";
    } else if (answering.unimplemented.includes(operation)) {
      because = STATUS_LABEL.unimplemented;
    } else if (!answering.registered.includes(operation)) {
      because = STATUS_LABEL.unknown;
    } else if (missing.length > 0) {
      because = `引数 ${missing.join("、")} が要ります。この画面の文脈にはありません`;
    }
    rows.push({ operation, writes: facts.writes, parameters, runnable: because === null, because });
  }
  return rows;
}

/** The parameters a run would send, as one line a person reads before running. */
export function describeParameters(row: PaletteRow): string {
  const pairs = Object.entries(row.parameters).map(([name, value]) => `${name} = ${value}`);
  return pairs.length > 0 ? pairs.join("、") : "引数なし";
}
