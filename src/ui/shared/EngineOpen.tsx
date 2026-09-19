/* The way in, while the shell that would provide one does not exist yet.
 *
 * A packaged build opens a file through the operating system's dialog and hands the engine a path
 * (XC-040's Electron shell). A page in a browser cannot: it gets a `File`, never a path, and the
 * engine reads from disk. So until the shell is built this asks for the two paths in words.
 *
 * It is **shown only when an engine is connected**, and it says what it is. A development
 * affordance pretending to be product is how a demonstration becomes a claim.
 */
import { useState } from "react";
import { engineState, useEngine } from "../state/engine";
import { shellApi } from "../client/shell";

export function EngineOpen() {
  const e = useEngine();
  const [workspace, setWorkspace] = useState("");
  const [result, setResult] = useState("");
  const [caseId, setCaseId] = useState("case:1");

  if (e.reachability.kind !== "reachable") return null;
  const shell = shellApi();

  const open = async () => {
    if (workspace && !(await engineState.openWorkspace(workspace))) return;
    if (result && !(await engineState.loadDataset(caseId, result))) return;
    await engineState.refresh();
  };

  return (
    <section className="prop-section" aria-label="エンジンで開く">
      <header className="prop-note">
        {shell
          ? "エンジンで開く（経路はシェルのファイルダイアログから）"
          : "エンジンで開く（開発用：製品版はシェルのファイルダイアログが経路を渡します）"}
      </header>
      <div className="prop-row">
        <label htmlFor="engine-workspace">ワークスペース</label>
        <div className="field-with-action">
          <input
            id="engine-workspace"
            className="field-input"
            value={workspace}
            placeholder="…/beam.svw"
            onChange={(event) => setWorkspace(event.target.value)}
          />
          {shell ? (
            <button
                type="button"
                className="btn"
                onClick={() => void shell.dialog.openWorkspace().then((path) => path && setWorkspace(path))}
            >
                選ぶ…
            </button>
          ) : null}
        </div>
      </div>
      <div className="prop-row">
        <label htmlFor="engine-case">ケース</label>
        <input
          id="engine-case"
          className="field-input"
          value={caseId}
          onChange={(event) => setCaseId(event.target.value)}
        />
      </div>
      <div className="prop-row">
        <label htmlFor="engine-result">結果ファイル</label>
        <div className="field-with-action">
          <input
            id="engine-result"
            className="field-input"
            value={result}
            placeholder="…/cube.vtu"
            onChange={(event) => setResult(event.target.value)}
          />
          {shell ? (
            <button
                type="button"
                className="btn"
                onClick={() => void shell.dialog.openResult().then((path) => path && setResult(path))}
            >
                選ぶ…
            </button>
          ) : null}
        </div>
      </div>
      <div className="prop-row">
        <button type="button" className="btn primary" onClick={() => void open()} disabled={e.busy}>
          {e.busy ? "読み込み中…" : "開いて描画する"}
        </button>
      </div>
      {e.fields.length > 0 ? (
        <p className="prop-note">
          {e.sourceName}：{e.fields.map((one) => `${one.name}（${one.unit ?? "単位未宣言"}）`).join("、")}
        </p>
      ) : null}
    </section>
  );
}
