/* Settings > ライセンス: every component this build ships, the terms each states for itself, and where
 * it is - XC-025's "viewable in the application".
 *
 * The list is not written here. It is `notices.json`, generated from the build closure by
 * packaging/notices.py and placed in the application's resources; the shell hands it over through the
 * bridge. A browser build has no closure and therefore no list, and says so rather than showing an
 * example that looks like one (XC-001): a licence list that is a fixture is exactly the kind of
 * plausible thing this product refuses to display.
 */
import { useEffect, useMemo, useState } from "react";
import { shellApi, type NoticeComponent, type Notices } from "../../client/shell";

type Loading = { kind: "loading" } | { kind: "absent"; because: string } | { kind: "loaded"; notices: Notices };

export function NoticesPanel() {
  const [state, setState] = useState<Loading>({ kind: "loading" });
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    const shell = shellApi();
    if (!shell) {
      setState({
        kind: "absent",
        because: "通知はパッケージ版が同梱します（実行ファイルの隣の THIRD-PARTY-NOTICES.txt と resources/notices.json）。ブラウザで動く開発ビルドには閉包がなく、一覧もありません。",
      });
      return;
    }
    let cancelled = false;
    void shell.notices().then((notices) => {
      if (cancelled) return;
      if (!notices) {
        setState({ kind: "absent", because: "このビルドには notices.json がありません。packaging/notices.py が生成し、パッケージが同梱します。" });
      } else {
        setState({ kind: "loaded", notices });
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const shown = useMemo(() => {
    if (state.kind !== "loaded") return [];
    const needle = query.trim().toLowerCase();
    if (!needle) return state.notices.components;
    return state.notices.components.filter(
      (one) => one.name.toLowerCase().includes(needle) || one.licence.toLowerCase().includes(needle),
    );
  }, [state, query]);

  return (
    <>
      <p className="se-lead">
        この製品が同梱する全ての構成要素と、それぞれが自ら述べる条件、そして置き場所。手で書いた一覧ではなく、
        ビルドの閉包（凍結したエンジンと展開したアプリ）を一ファイルずつ帰属させて生成します。帰属できない
        ファイルが一つでもあれば、生成は失敗します（XC-025）。
      </p>

      {state.kind === "loading" ? <p className="se-empty"><b>読み込み中…</b></p> : null}

      {state.kind === "absent" ? (
        <div className="se-empty">
          <b>この画面に出せる一覧がありません</b>
          <p>{state.because}</p>
        </div>
      ) : null}

      {state.kind === "loaded" ? (
        <>
          <section className="se-section">
            <div className="se-field-grid">
              <span className="se-field-label">構成要素</span>
              <span>{state.notices.components.length} 件</span>
              <span className="se-field-label">未帰属のファイル</span>
              <span>
                {state.notices.unattributed.length === 0
                  ? "なし - 出荷された全ファイルがいずれかの構成要素に帰属しています"
                  : `${state.notices.unattributed.length} 件（この一覧は不完全です）`}
              </span>
              <span className="se-field-label">ファイル</span>
              <span>実行ファイルの隣の THIRD-PARTY-NOTICES.txt に同じ内容を全文で</span>
            </div>
          </section>

          <section className="se-section">
            <label className="se-inline">
              <span className="se-field-label">絞り込み</span>
              <input
                className="field-input"
                value={query}
                placeholder="名前かライセンスで"
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <ol className="se-notices">
              {shown.map((one) => (
                <NoticeRow key={one.name} component={one} open={open === one.name} onToggle={() => setOpen(open === one.name ? null : one.name)} />
              ))}
            </ol>
            {shown.length === 0 ? <p className="se-empty"><b>該当なし</b></p> : null}
          </section>
        </>
      ) : null}
    </>
  );
}

function NoticeRow(props: { component: NoticeComponent; open: boolean; onToggle: () => void }) {
  const { component } = props;
  return (
    <li className="se-notice">
      <button type="button" className="se-notice-head" onClick={props.onToggle} aria-expanded={props.open}>
        <b>{component.name}</b>
        <span className="se-notice-meta">
          {component.version} ・ {component.licence}
          {component.files.length > 0 ? ` ・ ${component.files.length} ファイル` : ""}
        </span>
      </button>
      {props.open ? (
        <div className="se-notice-body">
          {component.note ? <p className="se-notice-note">{component.note}</p> : null}
          {component.files.length > 0 ? (
            <details>
              <summary>ファイル（{component.files.length}）</summary>
              <ul className="se-notice-files">
                {component.files.map((file) => (
                  <li key={file}>{file}</li>
                ))}
              </ul>
            </details>
          ) : null}
          {component.texts.map((text) => (
            <details key={text.source} open={component.texts.length === 1}>
              <summary>{text.source}</summary>
              <pre className="se-notice-text">{text.text}</pre>
            </details>
          ))}
          {component.texts.length === 0 ? <p className="se-notice-note">本文なし：上の注記が条件の所在です。</p> : null}
        </div>
      ) : null}
    </li>
  );
}
