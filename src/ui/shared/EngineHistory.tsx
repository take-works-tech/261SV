/* The engine's own record of what was asked (XC-023), with what memory no longer holds said in
 * numbers (LIM-014, LIM-015, #315). Shown only when an engine is connected: the design state of the
 * same popover is the script view, and the two are not alike - this is a record, that is a sketch.
 *
 * What is NOT here yet: the written form of each entry, the copyable command XC-046 asks for.
 * `history.list` answers the operation, who asked, when and how it went, and not the parameters; a
 * script view of real commands waits on the contract carrying them. Saying so here rather than
 * rendering a command with the parameters left blank, which would be a written form nobody can run. */
import type { Results } from "../client/engine";
import { describeRecorded } from "../logic/time";

type History = Results["history.list"];

const ORIGIN_LABEL = { interface: "画面", assistant: "アシスタント", script: "スクリプト", pipeline: "パイプライン" } as const;
const OUTCOME_LABEL: Record<string, string> = { applied: "適用", answered: "応答", refused: "拒否", failed: "失敗" };

export function EngineHistory(props: { history: History | null; workspaceOpen: boolean; onRefresh: () => void }) {
  if (!props.workspaceOpen) {
    return <p className="prop-note" style={{ padding: 8 }}>ワークスペースを開くと、エンジンの操作記録をここに表示します</p>;
  }
  const history = props.history;
  if (!history) {
    return <p className="prop-note" style={{ padding: 8 }}>記録を読んでいます…</p>;
  }
  // Newest first: the question a person opens this with is "what just happened".
  const entries = [...history.entries].reverse();
  return (
    <div style={{ display: "grid", gap: 6, minWidth: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <b className="type-caption">エンジンの操作記録（{history.entries.length}）</b>
        <button className="btn ghost" style={{ marginLeft: "auto" }} onClick={props.onRefresh} title="エンジンに記録を問い合わせ直します">
          更新
        </button>
      </div>
      {(history.undoDropped ?? 0) > 0 ? (
        <div className="notice warn" role="status">
          <b>取り消しの上限 {history.undoLimit} 件を超えました</b>
          <span className="why">古い {history.undoDropped} 件は取り消せなくなっています（LIM-014）。</span>
        </div>
      ) : null}
      {(history.omitted ?? 0) > 0 ? (
        <div className="notice" role="status">
          <b>履歴の上限 {history.historyLimit} 件を超えました</b>
          <span className="why">古い {history.omitted} 件はこの一覧にありません（LIM-015）。ディスクの診断ログには残っています（XC-263）。</span>
        </div>
      ) : null}
      {entries.length === 0 ? (
        <p className="prop-note" style={{ padding: 8 }}>まだ操作がありません</p>
      ) : (
        <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 4, minWidth: 0 }}>
          {entries.map((entry, index) => (
            <li
              key={`${entry.at.utc}:${index}`}
              style={{
                minWidth: 0,
                border: "1px solid var(--line)",
                borderLeft: `2px solid var(${entry.outcome === "refused" || entry.outcome === "failed" ? "--state-error" : "--line-strong"})`,
                borderRadius: "var(--radius-s)",
                background: "var(--surface-ground)",
                padding: "5px 8px",
              }}
            >
              <code style={{ display: "block", fontFamily: "var(--family-mono)", fontSize: "var(--text-body)", color: "var(--ink-strong)" }}>
                {entry.operation}
              </code>
              <span className="type-caption" style={{ color: "var(--ink-faint)" }}>
                {describeRecorded(entry.at)} · {ORIGIN_LABEL[entry.origin]} · {OUTCOME_LABEL[entry.outcome] ?? entry.outcome}
                {entry.undoId ? (entry.undoable ? " · 取り消し可" : " · 取り消し不可（上限で落ちました）") : ""}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
