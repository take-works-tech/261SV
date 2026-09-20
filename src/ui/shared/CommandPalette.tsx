/* The command palette (XC-278): every operation of the contract by name, and for each whether this
 * screen can run it now with the parameters the interface holds. A run goes through the same store
 * call every screen uses, so a write enters the journal, and the answer is shown as the engine gave
 * it - never formatted into a number this layer computed (INV-001). The console half of `script`,
 * as a popover, until the editor exists (16_application_model §7.12). */
import { useEffect, useState } from "react";
import { engineState, useEngine, type RunOutcome } from "../state/engine";
import { describeParameters, paletteRows, type PaletteRow } from "../logic/palette";

const STATUS_WORD: Record<RunOutcome["status"], string> = { answered: "応答", applied: "適用", refused: "拒否" };

export function CommandPalette() {
  const e = useEngine();
  const [query, setQuery] = useState("");
  const [chosen, setChosen] = useState<string | null>(null);
  const [ran, setRan] = useState<{ operation: string; outcome: RunOutcome } | null>(null);
  const reachable = e.reachability.kind === "reachable";
  useEffect(() => {
    // Which operations answer is the engine's to say, asked once when the palette opens.
    if (reachable && !e.operations) void engineState.operations();
  }, [reachable, e.operations]);

  const rows = paletteRows(
    reachable ? e.operations : null,
    { workspaceId: e.workspaceId, caseId: e.caseId, datasetId: e.datasetId, viewId: e.viewId, reportId: e.reportId, fieldName: e.fieldName },
    query,
  );
  const selected = rows.find((row) => row.operation === chosen) ?? null;
  const runnable = rows.filter((row) => row.runnable).length;

  const run = async (row: PaletteRow) => {
    const outcome = await engineState.run(row.operation, row.parameters);
    setRan({ operation: row.operation, outcome });
  };

  return (
    <div style={{ display: "grid", gap: 6, minWidth: 0 }}>
      <input
        className="field-input"
        autoFocus
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="操作名で検索（例：describe）"
        aria-label="操作を検索"
      />
      <p className="prop-note" style={{ margin: 0 }}>
        {reachable
          ? `${runnable} / ${rows.length} 操作をこの画面の文脈で実行できます。`
          : "エンジンに接続すると、この画面の文脈で実行できる操作が分かります。"}
        引数は開いているワークスペース・ケース・データセット・ビュー・レポート・場から埋め、それ以外の引数が要る操作は実行しません。キーは割り当てていません。
      </p>
      <div role="listbox" aria-label="操作" style={{ maxHeight: 180, overflow: "auto", display: "grid", gap: 2, minWidth: 0 }}>
        {rows.map((row) => (
          <button
            key={row.operation}
            className="tree-row"
            role="option"
            aria-selected={row.operation === chosen}
            title={row.because ?? describeParameters(row)}
            onClick={() => setChosen(row.operation)}
          >
            <span className="label" style={{ fontFamily: "var(--family-mono)" }}>{row.operation}</span>
            <span className="meta">{row.writes ? "書く" : "読む"}・{row.runnable ? "実行可" : "不可"}</span>
          </button>
        ))}
        {rows.length === 0 ? <p className="prop-note" style={{ margin: 0 }}>「{query}」に一致する操作はありません</p> : null}
      </div>
      {selected ? (
        <div className="notice" role="status">
          <b style={{ fontFamily: "var(--family-mono)" }}>{selected.operation}</b>
          <span className="why">
            {describeParameters(selected)}
            {selected.writes ? "。書く操作：取り消し 1 段・未保存 1 件になります" : "。読む操作：文書は変わりません"}
          </span>
          {selected.because ? <span className="why">実行しません：{selected.because}</span> : null}
          <div style={{ marginTop: 6 }}>
            <button className="btn primary" disabled={!selected.runnable || e.busy} onClick={() => void run(selected)}>
              実行
            </button>
          </div>
        </div>
      ) : null}
      {ran ? (
        <div className={`notice ${ran.outcome.status === "refused" ? "error" : "good"}`} role="status">
          <b>
            <span style={{ fontFamily: "var(--family-mono)" }}>{ran.operation}</span>：{STATUS_WORD[ran.outcome.status]}
          </b>
          {ran.outcome.reason ? <span className="why">{ran.outcome.reason}</span> : null}
          {ran.outcome.result !== null ? (
            <pre
              style={{ margin: "6px 0 0", maxHeight: 180, overflow: "auto", fontFamily: "var(--family-mono)", fontSize: "var(--text-caption)", whiteSpace: "pre-wrap", wordBreak: "break-all" }}
            >
              {JSON.stringify(ran.outcome.result, null, 2)}
            </pre>
          ) : null}
          <span className="why">答えはエンジンが返したままです。数値はこの層で成形していません（INV-001）。</span>
        </div>
      ) : null}
    </div>
  );
}
