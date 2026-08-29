/* Script view (11_ui.md): what the interface just did, as the commands that would do it again.
 *
 * XC-046's argument is reproducibility: an action a person can perform and cannot write down is an
 * action nobody can repeat, audit or automate. So every interface action has a written form, the
 * written form is copyable, and it is the SAME command surface a script would use (INV-006) - not a
 * transcript composed for display.
 *
 * A refused command stays in the list with its reason. It is the answer to "why did nothing
 * happen", and deleting it would leave that question unanswerable (16_application_model §11).
 */

export type ScriptLine = {
  at: string;
  operation: string;
  parameters: string;
  outcome: "applied" | "answered" | "refused" | "failed";
  reason?: string;
};

const OUTCOME_LABEL = {
  applied: "適用",
  answered: "応答",
  refused: "拒否",
  failed: "失敗",
} as const;

export function ScriptView(props: { lines: ScriptLine[]; onCopy?: (text: string) => void }) {
  const asText = props.lines
    .map((line) => `${line.operation}(${line.parameters})`)
    .join("\n");

  if (props.lines.length === 0) {
    return (
      <p className="prop-note" style={{ padding: 8 }}>
        まだ操作がありません。ここには、行った操作がそのまま実行できるコマンドとして並びます（XC-046）
      </p>
    );
  }

  return (
    <div style={{ display: "grid", gap: 6, minWidth: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <b className="type-caption">直前の操作（{props.lines.length}）</b>
        <button
          className="btn ghost"
          style={{ marginLeft: "auto" }}
          onClick={() => props.onCopy?.(asText)}
          title="同じことを行うコマンド列をコピーします"
        >
          コピー
        </button>
      </div>

      <ol
        style={{
          margin: 0,
          padding: 0,
          listStyle: "none",
          display: "grid",
          gap: 4,
          minWidth: 0,
        }}
      >
        {props.lines.map((line, index) => (
          <li
            key={`${line.at}:${index}`}
            style={{
              minWidth: 0,
              border: "1px solid var(--line)",
              borderLeft: `2px solid var(${line.outcome === "refused" || line.outcome === "failed" ? "--state-error" : "--line-strong"})`,
              borderRadius: "var(--radius-s)",
              background: "var(--surface-ground)",
              padding: "5px 8px",
            }}
          >
            <code
              style={{
                display: "block",
                minWidth: 0,
                overflowX: "auto",
                fontFamily: "var(--family-mono)",
                fontSize: "var(--text-body)",
                color: "var(--ink-strong)",
                whiteSpace: "pre",
              }}
            >
              {line.operation}({line.parameters})
            </code>
            <span className="type-caption" style={{ color: "var(--ink-faint)" }}>
              {line.at} · {OUTCOME_LABEL[line.outcome]}
              {line.reason ? ` — ${line.reason}` : ""}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
