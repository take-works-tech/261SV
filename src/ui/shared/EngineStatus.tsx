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

export function EngineStatus(props: { reachability: Reachability; busy?: boolean; refusal?: string | null }) {
  const { reachability } = props;
  const label =
    reachability.kind === "reachable"
      ? `エンジン接続中（protocol ${reachability.protocols.join(", ")}）`
      : reachability.kind === "absent"
        ? "エンジン未接続：画面は設計状態です"
        : "エンジン未確認";
  return (
    <span className="engine-status" title={reachability.kind === "absent" ? reachability.because : undefined}>
      <span className={`engine-dot ${reachability.kind}`} aria-hidden="true" />
      <span>{label}</span>
      {props.busy ? <span className="engine-busy">…</span> : null}
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
