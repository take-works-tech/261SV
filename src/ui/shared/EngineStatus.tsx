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
import type { Reachability } from "../state/engine";

export function EngineStatus(props: {
  reachability: Reachability;
  busy?: boolean;
  refusal?: string | null;
  /** Offered only where a shell can do it (XC-259); a browser build has nothing to restart. */
  onRestart?: () => void;
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
    </span>
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
