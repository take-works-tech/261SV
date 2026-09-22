/* Which mode the interface is in, said plainly.
 *
 * Two are possible and they are not alike. **Connected**: what the screens show came from the
 * engine. **Not connected**: the screens are the catalogue of design states they have always been,
 * each already labelled as one - useful for looking at, and evidence of nothing.
 *
 * A person must be able to tell which without guessing, because a screen showing fixture data while
 * looking live is the failure this product exists to refuse (XC-001). So the state is named in the
 * topbar, in words, always - not by a coloured dot, which says "something" and not "what".
 */
import { useEffect, useState } from "react";
import type { AppliedWrite, Lock, Reachability } from "../state/engine";
import { shellApi, type Orphan } from "../client/shell";
import type { RecordedTime } from "../client/generated";
import { formatBytes } from "../logic/format";
import { describeRecorded } from "../logic/time";
import { canTakeOver, describeLock } from "../logic/lock";

export function EngineStatus(props: {
  reachability: Reachability;
  busy?: boolean;
  refusal?: string | null;
  /** Offered only where a shell can do it (XC-259); a browser build has nothing to restart. */
  onRestart?: () => void;
  /** Applied writes not yet in the saved document, and the way to save them. */
  unsaved?: number;
  onSave?: () => void;
  /** When the document was last written back, or null; shown once nothing is unsaved. */
  savedAt?: RecordedTime | null;
  /** Whether the document may not be written back, and what the lock said (XC-241, XC-269). */
  readOnly?: boolean;
  lock?: Lock | null;
  /** Offered only where the lock is stale or unreadable: a person's call, never a default. */
  onTakeOver?: () => void;
}) {
  const { reachability } = props;
  const label =
    reachability.kind === "reachable"
      ? `エンジン接続中（protocol ${reachability.protocols.join(", ")}）`
      : reachability.kind === "absent"
        ? "エンジン未接続：画面は設計状態です"
        : reachability.kind === "exited"
          ? `エンジン停止（${reachability.because}）：表示は停止前のものです`
          : reachability.kind === "starting"
            ? "エンジン起動中"
            : "エンジン未確認";
  const detail =
    reachability.kind === "absent" || reachability.kind === "exited" ? reachability.because : undefined;
  return (
    <span className="engine-status" title={detail}>
      <span className={`engine-dot ${reachability.kind}`} aria-hidden="true" />
      <span>{label}</span>
      {props.busy ? <span className="engine-busy">…</span> : null}
      {reachability.kind === "exited" && props.onRestart ? (
        <button type="button" className="btn ghost" onClick={props.onRestart}>
          再起動
        </button>
      ) : null}
      {reachability.kind === "reachable" && props.readOnly && props.lock ? (
        <span className="engine-readonly" title={describeLock(props.lock)}>
          読み取り専用{props.lock.holder ? `：${props.lock.holder.host} の ${props.lock.holder.user}` : ""}
        </span>
      ) : null}
      {reachability.kind === "reachable" && props.readOnly && props.lock && canTakeOver(props.lock) && props.onTakeOver ? (
        <button
          type="button"
          className="btn ghost"
          onClick={props.onTakeOver}
          title="持ち主のプロセスが見つからないか、ロックを読めません。引き継ぐかどうかは人の判断で、生きているロックは壊しません（XC-241）"
        >
          ロックを引き継ぐ
        </button>
      ) : null}
      {reachability.kind === "reachable" && (props.unsaved ?? 0) > 0 && props.onSave ? (
        props.readOnly ? (
          <span className="type-caption" style={{ color: "var(--state-warn)" }} title="読み取り専用のため、この作業は文書に書き戻せません">
            未保存 {props.unsaved} 件・読み取り専用のため保存できません
          </span>
        ) : (
          <button type="button" className="btn ghost" onClick={props.onSave} title="文書に書き戻します。直前の版は隣に残ります">
            未保存 {props.unsaved} 件 - 保存
          </button>
        )
      ) : null}
      {reachability.kind === "reachable" && (props.unsaved ?? 0) === 0 && props.savedAt ? (
        <span className="type-caption" style={{ color: "var(--ink-faint)" }} title="この文書を最後に書き戻した時刻。読み手のゾーンで表示し、記録時のゾーンが違えば添えます（XC-142）">
          保存済み {describeRecorded(props.savedAt)}
        </span>
      ) : null}
    </span>
  );
}

/** What the last exit lost: the writes the engine had applied and the document had not yet been
 *  saved with. Listed in the engine's own words, never re-applied (XC-259). */
export function EngineLost(props: { lost: readonly AppliedWrite[] | null; onDismiss?: () => void }) {
  if (!props.lost || props.lost.length === 0) return null;
  return (
    <div className="notice error" role="status">
      <div>
        <b>エンジンの終了で失われた変更：{props.lost.length} 件</b>
        <span className="why">保存済みの文書とファイルは開き直しました。次は保存前のものです - 作り直してはいません。</span>
        <ul className="lost-list">
          {grouped(props.lost).map((group) => (
            <li key={group.operation}>
              {group.lastSummary}
              <small>
                （{group.operation}
                {group.count > 1 ? ` ×${group.count}` : ""}、最後は {describeRecorded(group.lastAt)}）
              </small>
            </li>
          ))}
        </ul>
      </div>
      {props.onDismiss ? (
        <button type="button" className="btn ghost" onClick={props.onDismiss}>
          閉じる
        </button>
      ) : null}
    </div>
  );
}

/** What the engine warned about beside an answer, in its own words, until dismissed (XC-001). A
 *  warning dropped is a document lifted, a dataset closed or a lock held that nobody was told of. */
export function EngineWarnings(props: { warnings: readonly string[]; onDismiss?: () => void }) {
  if (props.warnings.length === 0) return null;
  return (
    <div className="notice warn" role="status">
      <div>
        <b>エンジンからの注意：{props.warnings.length} 件</b>
        <ul className="lost-list">
          {props.warnings.map((one, index) => (
            <li key={`${index}:${one.slice(0, 24)}`}>{one}</li>
          ))}
        </ul>
      </div>
      {props.onDismiss ? (
        <button type="button" className="btn ghost" onClick={props.onDismiss}>
          閉じる
        </button>
      ) : null}
    </div>
  );
}

/** What the engine refused, where the person who asked can read it. Never swallowed: a refusal a
 *  caller drops is an operation the user believes happened (CT-002, XC-001). */
export function EngineRefusal(props: { refusal: string | null; onDismiss?: () => void }) {
  if (!props.refusal) return null;
  return (
    <div className="notice error" role="status">
      <span>{props.refusal}</span>
      {props.onDismiss ? (
        <button type="button" className="btn ghost" onClick={props.onDismiss}>
          閉じる
        </button>
      ) : null}
    </div>
  );
}

/** The loss, one line per operation: a drag is many `view.update`s, and a list that repeats them
 *  hides the one declaration among them. The count is kept; the last summary stands for the group. */
function grouped(lost: readonly AppliedWrite[]): { operation: string; count: number; lastSummary: string; lastAt: RecordedTime }[] {
  const groups = new Map<string, { operation: string; count: number; lastSummary: string; lastAt: RecordedTime }>();
  for (const one of lost) {
    const group = groups.get(one.operation);
    if (group) {
      group.count += 1;
      group.lastSummary = one.summary;
      group.lastAt = one.at;
    } else {
      groups.set(one.operation, { operation: one.operation, count: 1, lastSummary: one.summary, lastAt: one.at });
    }
  }
  return [...groups.values()];
}

/** Transient directories a dead session left behind, and the choice (#313, XC-262). Shown only
 *  inside the shell, which is the only thing that can know; removed only when a person says so,
 *  and kept otherwise - "残す" is the default, because a file nobody chose to delete is not this
 *  product's to delete. */
export function OrphanNotice() {
  const [orphans, setOrphans] = useState<readonly Orphan[]>([]);
  const [decided, setDecided] = useState<"kept" | "removed" | null>(null);
  useEffect(() => {
    const shell = shellApi();
    if (!shell) return;
    void shell.app.orphans().then(setOrphans);
  }, []);
  if (orphans.length === 0 || decided !== null) return null;
  const bytes = orphans.reduce((sum, one) => sum + one.bytes, 0);
  const files = orphans.reduce((sum, one) => sum + one.files, 0);
  // The most recent file among them, so a person can tell last night's crash from last month's.
  const newest = orphans
    .map((one) => one.modified)
    .filter((one): one is RecordedTime => one !== null)
    .sort((a, b) => (a.utc < b.utc ? 1 : a.utc > b.utc ? -1 : 0))[0] ?? null;
  return (
    <div className="notice" role="status">
      <div>
        <b>前回までの異常終了が残した一時ファイル：{orphans.length} セッション</b>
        <span className="why">
          {files} ファイル・{formatBytes(bytes)}{newest ? `・最終更新 ${describeRecorded(newest)}` : ""}。エンジンが落ちるか、シェルが待たずに終わったときの作業領域です。ワークスペースの文書とは別で、消しても何も失われません。
        </span>
      </div>
      <button
        type="button"
        className="btn"
        onClick={() => {
          const shell = shellApi();
          if (!shell) return;
          void shell.app.removeOrphans(orphans.map((one) => one.id)).then(() => setDecided("removed"));
        }}
      >
        消す
      </button>
      <button type="button" className="btn ghost" onClick={() => setDecided("kept")}>
        残す
      </button>
    </div>
  );
}
