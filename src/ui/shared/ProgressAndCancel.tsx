/* Progress and cancel (11_ui.md): the one way a wait looks. A wait without progress is
 * indistinguishable from a hang, and a long operation without cancel is a hostage situation.
 * Cancel is honest about where it takes effect (a unit boundary, a case boundary). */

export function ProgressAndCancel(props: {
  label: string;
  detail?: string;
  fraction?: number;
  onCancel?: () => void;
  cancelNote?: string;
}) {
  return (
    <div className="notice" role="status" style={{ display: "grid", gap: 6 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span className="run-chip">
          <span className="spinner" aria-hidden />
          {props.label}
        </span>
        {props.detail ? <span className="type-caption" style={{ color: "var(--ink-muted)" }}>{props.detail}</span> : null}
        {props.onCancel ? (
          <button className="btn ghost" onClick={props.onCancel} style={{ marginLeft: "auto" }} title={props.cancelNote}>
            中断
          </button>
        ) : null}
      </div>
      {props.fraction !== undefined ? (
        <div style={{ height: 3, borderRadius: 2, background: "var(--surface-active)" }}>
          <div
            style={{
              width: `${Math.round(Math.min(Math.max(props.fraction, 0), 1) * 100)}%`,
              height: "100%",
              borderRadius: 2,
              background: "var(--ink-strong)",
            }}
          />
        </div>
      ) : null}
    </div>
  );
}
