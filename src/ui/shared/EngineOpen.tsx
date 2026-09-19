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
import { engineState, useEngine, type Inspection } from "../state/engine";
import { shellApi } from "../client/shell";
import { formatBytes } from "../logic/format";

export function EngineOpen() {
  const e = useEngine();
  const [workspace, setWorkspace] = useState("");
  const [result, setResult] = useState("");
  const [caseId, setCaseId] = useState("case:1");

  if (e.reachability.kind !== "reachable") return null;
  const shell = shellApi();

  // Open the workspace, then **inspect** the file rather than load it: the review states the
  // format's support level and the reader's gaps before anything is read (ingest/AC-032, XC-049),
  // and the load happens on the person's word in the review.
  const open = async () => {
    if (workspace && !(await engineState.openWorkspace(workspace))) return;
    if (result) await engineState.inspect(result);
  };
  const load = async () => {
    const inspection = e.inspection;
    if (!inspection) return;
    if (!(await engineState.loadDataset(caseId, inspection.path))) return;
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
          {e.busy ? "確認中…" : "取込前確認へ"}
        </button>
      </div>
      {e.inspection ? (
        <ConnectedImportReview
          inspection={e.inspection}
          busy={e.busy}
          onLoad={() => void load()}
          onCancel={() => engineState.cancelInspection()}
        />
      ) : null}
      {e.fields.length > 0 ? (
        <p className="prop-note">
          {e.sourceName}：{e.fields.map((one) => `${one.name}（${one.unit ?? "単位未宣言"}）`).join("、")}
        </p>
      ) : null}
    </section>
  );
}

/** The import review with an engine behind it. What it shows is what `dataset.inspect` answered -
 *  the format, the support level this build promises for it, and what the reader is known not to
 *  read - and nothing about the file's contents, because nothing has read them (XC-049). The
 *  design state of the same dialog shows fields and frames; those are known after loading and are
 *  not invented here. */
function ConnectedImportReview(props: { inspection: Inspection; busy: boolean; onLoad: () => void; onCancel: () => void }) {
  const { inspection } = props;
  const name = inspection.path.split(/[\\/]/).pop() ?? inspection.path;
  const readable = inspection.exists && inspection.supportLevel !== "Absent";
  return (
    <div className="dialog-scrim">
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="engine-import-review-title">
        <header>
          <h2 id="engine-import-review-title">取込前確認</h2>
          <button className="icon-button" aria-label="取込を取りやめて閉じる" onClick={props.onCancel}>✕</button>
        </header>
        <div className="body">
          <p className="ho-trust ho-review-lead">
            まだ何も読み込んでいません。ここにあるのは、拡張子から決まる形式と、この版がその形式に約束する対応水準、
            読み手が読まないと分かっているものだけです。元ファイルは変更しません。
          </p>
          <section className="ho-review-section" aria-label="ファイルと対応レベル">
            <h3>ファイルと対応レベル</h3>
            <div className="ho-file-row wrap">
              <span className="ho-file-name" title={inspection.path}>{name}</span>
              <span className={inspection.supportLevel === "Verified" ? "ho-tier verified" : "ho-tier"}>{inspection.supportLevel}</span>
              <span className="ho-file-meta">
                {inspection.exists ? `${formatBytes(inspection.sizeBytes)}・更新 ${inspection.modifiedIso}` : "ファイルが見つかりません"}
              </span>
              <p className="ho-file-note">
                {inspection.supportLevel === "Absent"
                  ? `この版は .${inspection.format} を読みません。`
                  : inspection.gaps.length > 0
                    ? `読み手の既知の欠け：${inspection.gaps.join("；")}`
                    : "読み手に既知の欠けはありません。"}
              </p>
            </div>
          </section>
          <section className="ho-review-section" aria-label="単位と座標">
            <h3>単位と座標</h3>
            <p className="ho-review-note">
              単位はファイルから読み取りません（XC-003）。読み込むと各フィールドは単位未宣言で現れ、宣言するまで換算も比較も無効です。
              フィールドの関連と成分は読み込んだ後にファイル記載のまま表示します。
            </p>
          </section>
        </div>
        <footer>
          <small className="ho-footer-note">この画面では何も適用していません。取り込むとファイルを読み、ケースに記録します。</small>
          <button className="btn ghost" onClick={props.onCancel}>取りやめ</button>
          <button className="btn primary" onClick={props.onLoad} disabled={props.busy || !readable} title={readable ? undefined : "読めない形式か、ファイルがありません"}>
            {props.busy ? "読み込み中…" : "取り込む"}
          </button>
        </footer>
      </div>
    </div>
  );
}
