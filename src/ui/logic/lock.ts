/* What the document's lock means for the person at this window (MOD-015, XC-241, XC-269): who has it,
 * what that lets them do, and whether taking it over is theirs to decide. Mirrors LockStatus.describe
 * in src/service/workspace/lock.py, with the time shown in the reader's zone. */
import type { Lock } from "../state/engine";
import { describeRecorded } from "./time";

/** Who holds the lock, named well enough to act on: "in use by something" is not an answer. */
export function describeHolder(lock: Lock, readerOffsetMinutes?: number): string {
  const holder = lock.holder;
  if (!holder) return "不明なプロセス";
  return `${holder.host} の ${holder.user}（プロセス ${holder.processId}、${describeRecorded(holder.takenAt, readerOffsetMinutes)} 取得）`;
}

/** The lock's state as a sentence a person reads, and what it lets them do. */
export function describeLock(lock: Lock, readerOffsetMinutes?: number): string {
  switch (lock.state) {
    case "free":
      return "編集できます";
    case "held":
      return `このワークスペースは ${describeHolder(lock, readerOffsetMinutes)} が開いています。読み取り専用で開いています：保存は拒まれ、画面上の作業は文書に書き戻されません`;
    case "stale":
      return `ロックは ${describeHolder(lock, readerOffsetMinutes)} のものですが、そのプロセスは見つかりません。自動では解除しません。読み取り専用で開いています`;
    default:
      return `ロックファイルを読めません（${lock.detail ?? "理由不明"}）。読み取り専用で開いています`;
  }
}

/** Whether taking the lock over is a person's call here: only where the holder cannot be found or the
 *  file cannot be read. A live holder's lock is never offered for taking (XC-241). */
export function canTakeOver(lock: Lock): boolean {
  return lock.state === "stale" || lock.state === "unreadable";
}
