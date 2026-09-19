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
import type { AppliedWrite, Reachability } from "../state/engine";
import { shellApi, type Orphan } from "../client/shell";
import { formatBytes } from "../logic/format";

export function EngineStatus(props: {
  reachability: Reachability;
  busy?: boolean;
  refusal?: string | null;
  /** Offered only where a shell can do it (XC-259); a browser build has nothing to restart. */
  onRestart?: () => void;
  /** Applied writes not yet in the saved document, and the way to save them. */
  unsaved?: number;
  onSave?: () => void;
}) {
  const { reachability } = props;
  const label =
    reachability.kind === "reachable"
      ? `エンジン接続中（protocol ${reachability.protocols.join(", ")}）`
      : reachability.kind === "absent"
        ? "エンジン未接続：画面は設計状態です"
        : reachability.kind === "exited"
          ? `エンジン停止（${reachability.because}）：表示は停止前のものです`
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
      {reachability.kind === "reachable" && (props.unsaved ?? 0) > 0 && props.onSave ? (
        <button type="button" className="btn ghost" onClick={props.onSave} title="文書に書き戻します。直前の版は隣に残ります">
          未保存 {props.unsaved} 件 - 保存
        </button>
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
                {group.count > 1 ? ` ×${group.count}` : ""}、最後は {group.lastAt.slice(11, 19)}）
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
function grouped(lost: readonly AppliedWrite[]): { operation: string; count: number; lastSummary: string; lastAt: string }[] {
  const groups = new Map<string, { operation: string; count: number; lastSummary: string; lastAt: string }>();
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
  return (
    <div className="notice" role="status">
      <div>
        <b>前回までの異常終了が残した一時ファイル：{orphans.length} セッション</b>
        <span className="why">
          {files} ファイル・{formatBytes(bytes)}。エンジンが落ちるか、シェルが待たずに終わったときの作業領域です。ワークスペースの文書とは別で、消しても何も失われません。
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
