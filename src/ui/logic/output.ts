/* What the runs left behind, as a person reads it before deciding what to prune (MOD-015, XC-141,
 * XC-268). The engine answers `output.list` and `output.plan`; these turn the answers into the lines
 * the settings page shows. The rule kept here is AC-053's: every file by name, never a total in its
 * place - "freed 4.2 GB" tells a person a number and not what it cost them. */
import type { Results } from "../client/engine";
import { formatBytes } from "./format";
import { describeRecorded } from "./time";

export type OutputListing = Results["output.list"];
export type OutputRun = OutputListing["runs"][number];
export type OutputPlan = Results["output.plan"];

/** One run as the table shows it. */
export interface RunLine {
  id: string;
  /** The pipeline or report the run belongs to: the first segment of `output/<name>/<stamp>/`. */
  name: string;
  stamp: string;
  started: string;
  /** Where the time came from - said, because a time whose origin is not stated cannot be checked. */
  startedNote: string;
  files: number;
  size: string;
  hasRecord: boolean;
  /** Whether pruning oldest-first to get under the limit would take this run. */
  suggested: boolean;
}

/** The runs, newest first: the one a person is most likely looking at is the one they must not
 *  delete by mistake, so it is at the top and never suggested. */
export function runLines(listing: OutputListing, readerOffsetMinutes?: number): RunLine[] {
  const suggested = new Set(listing.suggestedRunIds);
  return [...listing.runs]
    .sort((a, b) => (a.started.utc < b.started.utc ? 1 : a.started.utc > b.started.utc ? -1 : a.id < b.id ? 1 : -1))
    .map((run) => {
      const cut = run.id.indexOf("/");
      return {
        id: run.id,
        name: cut < 0 ? run.id : run.id.slice(0, cut),
        stamp: cut < 0 ? "" : run.id.slice(cut + 1),
        started: describeRecorded(run.started, readerOffsetMinutes),
        startedNote: run.startedFrom === "record" ? "実行の記録から" : "フォルダの更新時刻から（記録なし）",
        files: run.artefactFiles,
        size: formatBytes(run.artefactBytes),
        hasRecord: run.hasRecord,
        suggested: suggested.has(run.id),
      };
    });
}

/** The total against LIM-012, as an ask and never a refusal (XC-141). */
export function describeTotal(listing: OutputListing): string {
  const line = `出力は ${formatBytes(listing.totalBytes)}（${listing.runs.length} 実行分）。上限 ${formatBytes(listing.limitBytes)}`;
  if (!listing.overLimit) return line;
  return `${line}。上限を超えています — 古い実行から順に整理できます。拒否ではなく、確認のお願いです（LIM-012）`;
}

/** What the plan would do, as the confirmation shows it: every file, then what stays. */
export function describePlan(plan: OutputPlan): { files: string[]; summary: string; kept: string } {
  return {
    files: [...plan.files],
    summary: `${plan.runIds.length} 実行分から ${plan.files.length} ファイル、${formatBytes(plan.freedBytes)} を削除します`,
    kept: `実行の記録 ${plan.keptRecords.length} 件は残します — 作り方の記録が残っていれば、消した成果物は作り直せます（XC-046）`,
  };
}
