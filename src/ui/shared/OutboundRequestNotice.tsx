/* Outbound request notice (11_ui.md): the exact thing that would leave the machine, shown before it
 * does (XC-106).
 *
 * Not a summary of the request - the request. A notice that said "searching the web" would be a
 * notice nobody could object to, and the objection is the entire point: the customer's part name in
 * a query string is the thing they would have refused, and they can only refuse what they can read.
 * `withheld` names what was deliberately removed, so silence never has to be trusted.
 *
 * Nothing here sends anything. The decision travels back to the caller (INV-006, MOD-014).
 */

export type OutboundDecision = "once" | "always" | "refuse";

export function OutboundRequestNotice(props: {
  purpose: string;
  host: string;
  /** Verbatim. Whatever would go on the wire, not a paraphrase of it. */
  content: string;
  withheld?: string[];
  /** Set once the decision is made, so the notice becomes a record rather than a question. */
  outcome?: "sent" | "refused" | "awaiting";
  onDecide?: (decision: OutboundDecision) => void;
}) {
  const outcome = props.outcome ?? "awaiting";
  return (
    <section
      className={outcome === "refused" ? "notice error" : outcome === "sent" ? "notice" : "notice warn"}
      role="group"
      aria-label="外部への要求"
    >
      <b>
        {outcome === "awaiting"
          ? "この内容が機械の外に出ようとしています"
          : outcome === "sent"
            ? "この内容を送信しました"
            : "この要求は送信していません"}
      </b>
      <span className="why">
        目的：{props.purpose} ／ 送信先：{props.host}
      </span>

      <pre
        style={{
          margin: "8px 0 0",
          padding: "8px 10px",
          border: "1px solid var(--line-strong)",
          borderRadius: "var(--radius-s)",
          background: "var(--surface-ground)",
          color: "var(--ink-strong)",
          fontFamily: "var(--family-mono)",
          fontSize: "var(--text-body)",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          maxHeight: 180,
          overflow: "auto",
        }}
      >
        {props.content}
      </pre>

      {props.withheld && props.withheld.length > 0 ? (
        <p className="prop-note" style={{ marginBottom: 0 }}>
          伏せた語：{props.withheld.join("、")}（送信内容には含まれていません）
        </p>
      ) : (
        <p className="prop-note" style={{ marginBottom: 0 }}>
          伏せた語はありません — 上の内容がそのまま全部です
        </p>
      )}

      {outcome === "awaiting" && props.onDecide ? (
        <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
          <button className="btn" onClick={() => props.onDecide?.("once")}>
            今回だけ許可
          </button>
          <button className="btn" onClick={() => props.onDecide?.("always")}>
            この送信先を常に許可
          </button>
          <button className="btn primary" onClick={() => props.onDecide?.("refuse")}>
            送らない
          </button>
        </div>
      ) : null}
    </section>
  );
}
