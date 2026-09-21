/* The log area's four lists from the store and the engine's answers (XC-286, 16_application_model
 * §7.12, §12): the notices this window raised and kept after dismissal, the engine's operation record,
 * the communication audit as rows a spreadsheet takes, and the diagnostic log read back with the
 * statement of whether it outlives the window. Sentences are built here from facts the engine
 * answered; nothing is inferred. No React and no transport. */
import type { Results } from "../client/engine";
import type { Notice } from "../state/engine";
import type { AuditLine } from "./egress";
import { describeRecorded } from "./time";

export type LogAnswer = Results["system.log"];
export type LogEntry = LogAnswer["entries"][number];

/** Newest first; a dismissed notice stays in the list and is shown only when asked for (§12). */
export function visibleNotices(notices: readonly Notice[], showDismissed: boolean): Notice[] {
  return [...notices].reverse().filter((one) => showDismissed || !one.dismissedAt);
}

export function dismissedCount(notices: readonly Notice[]): number {
  return notices.filter((one) => Boolean(one.dismissedAt)).length;
}

/** A command's outcome as the record and the log both say it (XC-023): defined once, here. */
export const COMMAND_OUTCOME_LABEL: Record<string, string> = { applied: "適用", answered: "応答", refused: "拒否", failed: "失敗" };

const LEVEL_LABEL: Record<LogEntry["level"], string> = { debug: "詳細", info: "情報", warning: "警告", error: "エラー" };
const EVENT_LABEL: Record<string, string> = { command: "命令", warning: "注意", egress: "外部要求", "engine.start": "エンジン起動" };
const OUTCOME_LABEL: Record<string, string> = { sent: "送信", refused: "拒否", awaitingConfirmation: "確認待ち" };

export interface LogRow {
  id: string;
  at: string;
  level: LogEntry["level"];
  levelLabel: string;
  event: string;
  text: string;
}

function word(context: LogEntry["context"], key: string): string {
  const value = context[key];
  return value === null || value === undefined ? "" : String(value);
}

/** One line's context as a sentence, by what the event was: a command with its outcome and reason,
 *  a warning as said, an egress decision by purpose, host and outcome - and any other event as its
 *  names and counts in order, so nothing the engine wrote is hidden. */
export function describeEntry(entry: LogEntry): string {
  const context = entry.context;
  if (entry.event === "command") {
    const status = word(context, "status");
    const reason = word(context, "reason");
    return `${word(context, "operation")} → ${COMMAND_OUTCOME_LABEL[status] ?? status}${reason ? `：${reason}` : ""}${context.dryRun === true ? "（試算）" : ""}`;
  }
  if (entry.event === "warning") return `${word(context, "operation")}：${word(context, "text")}`;
  if (entry.event === "egress") {
    const outcome = word(context, "outcome");
    const reason = word(context, "reason");
    const withheld = Number(context.withheld ?? 0);
    return `${word(context, "purpose")} → ${word(context, "host")}：${OUTCOME_LABEL[outcome] ?? outcome}${reason ? `（${reason}）` : ""}${withheld > 0 ? `・伏せた語 ${withheld} 件` : ""}`;
  }
  return Object.entries(context)
    .map(([key, value]) => `${key}=${value === null ? "なし" : String(value)}`)
    .join("、");
}

/** The log as rows, newest first: the question a person opens it with is "what just happened". */
export function logRows(answer: LogAnswer, readerOffsetMinutes?: number): LogRow[] {
  return answer.entries
    .map((entry, index): LogRow => ({
      id: `${entry.at.utc}:${index}`,
      at: describeRecorded(entry.at, readerOffsetMinutes),
      level: entry.level,
      levelLabel: LEVEL_LABEL[entry.level] ?? entry.level,
      event: EVENT_LABEL[entry.event] ?? entry.event,
      text: describeEntry(entry),
    }))
    .reverse();
}

/** Whether this log outlives the window, in the engine's own facts (XC-263, XC-286). */
export function retentionSentence(answer: LogAnswer): string {
  if (answer.source === "file" && answer.logDirectory) {
    return `ファイルに残ります：${answer.logDirectory}（${answer.files} ファイル・回転分は ${answer.retainDays} 日保持・XC-263）。窓を閉じても読めます`;
  }
  return "このエンジンはログをメモリにだけ持っています（--log-directory なしで起動）。窓を閉じると消えます";
}

/** What the read left out, or null where nothing was. */
export function omittedSentence(answer: LogAnswer): string | null {
  const parts: string[] = [];
  if (answer.omitted > 0) parts.push(`上限で省略した古い行 ${answer.omitted} 件（since で絞れます）`);
  if (answer.unreadable > 0) parts.push(`読めなかった行 ${answer.unreadable} 件（途中で切れた書き込み・推測はしません）`);
  return parts.length > 0 ? parts.join("・") : null;
}

export const AUDIT_HEADER: readonly string[] = ["時刻", "目的", "宛先", "結果", "内容", "注記"];
const AUDIT_OUTCOME: Record<AuditLine["outcome"], string> = { sent: "送信", refused: "拒否", awaiting: "確認待ち" };

/** The audit as a spreadsheet takes it - the export 16_application_model §7.12 names (XC-279). */
export function auditCopyRows(lines: readonly AuditLine[]): string[][] {
  return [[...AUDIT_HEADER], ...lines.map((one) => [one.at, one.purpose, one.host, AUDIT_OUTCOME[one.outcome], one.content, one.note])];
}
