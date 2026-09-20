/* Writing the deliverable from the interface: a destination a person chooses, the export, and what
 * the engine said it wrote - the path, the size, the reductions it applied and the elements it could
 * not carry (report/AC-014). One implementation, used by the View screen's rail and the report
 * area's output tab, so the two never disagree about what an export is. */
import { useState } from "react";
import { engineState, useEngine } from "../state/engine";
import { shellApi } from "../client/shell";
import { UnresolvedList } from "./UnresolvedList";

export function ReportExport() {
  const e = useEngine();
  const [path, setPath] = useState("");
  const shell = shellApi();
  const written = e.exported;

  return (
    <>
      <div className="prop-row">
        <label htmlFor="engine-export">書き出し先</label>
        <input
          id="engine-export"
          className="field-input"
          value={path}
          placeholder="…/report.html"
          onChange={(event) => setPath(event.target.value)}
        />
        {shell ? (
          <button
            type="button"
            className="btn"
            onClick={() =>
              void shell.dialog
                .saveReport(`${(e.sourceName ?? "report").replace(/\.[^.]+$/, "")}.html`)
                .then((chosenPath) => chosenPath && setPath(chosenPath))
            }
          >
            保存先を選ぶ…
          </button>
        ) : null}
        <button
          type="button"
          className="btn primary"
          disabled={!path || e.busy || !e.workspaceId}
          title="文書が持つレポート定義を、来歴・宣言単位・製品版とともに一つの HTML に書きます。既存のファイルは上書きしません"
          onClick={() => void engineState.exportReport(path)}
        >
          書き出す
        </button>
      </div>
      {written ? (
        <>
          <p className="prop-note">
            書き出しました：{written.path}（{written.bytes.toLocaleString("en-US")} バイト）
            {written.reductions.length > 0 ? `。${written.reductions.join("。")}` : ""}
          </p>
          <UnresolvedList
            title="文書が運べなかったもの（文書自身も同じことを述べます・AC-014）"
            items={written.omitted.map((one) => ({ what: one, missing: "この版の文書は表せません" }))}
          />
        </>
      ) : null}
    </>
  );
}
