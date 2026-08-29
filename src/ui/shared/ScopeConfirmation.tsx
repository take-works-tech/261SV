/* Scope confirmation (11_ui.md): before a destructive unit runs, the affected set is shown and
 * accepted - named where the count is small, counted where it is not, and authorised once per run
 * (XC-094). A confirmation that shows no scope is a confirmation somebody clicks through. */

export function ScopeConfirmation(props: {
  operation: string;
  affected: string[];
  onAccept: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="dialog-scrim" role="dialog" aria-modal="true" aria-label="範囲の確認">
      <div className="dialog" style={{ width: "min(520px, calc(100vw - 48px))" }}>
        <header>
          <h2>{props.operation} — 影響範囲の確認</h2>
        </header>
        <div className="body">
          <p className="prop-note" style={{ marginTop: 0 }}>
            この操作は次の {props.affected.length} 件に影響します。承諾はこの実行一回に限られます（XC-094）
          </p>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {props.affected.map((one) => (
              <li key={one}>{one}</li>
            ))}
          </ul>
        </div>
        <footer>
          <button className="btn ghost" onClick={props.onCancel}>取り消し</button>
          <button className="btn primary" onClick={props.onAccept}>この範囲で実行</button>
        </footer>
      </div>
    </div>
  );
}
