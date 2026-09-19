/* The three things XC-257's prototype asks for that a picture alone cannot do: choose the field the
 * colours mean, declare the unit they are in, and write the deliverable.
 *
 * Shown only when an engine is connected, beside the design-state rail rather than in place of it.
 * Every value here came from an answer - the field list, the unit, the range - and nothing is
 * computed: a unit this layer invented would be a unit nobody declared (XC-003).
 */
import { useState } from "react";
import { engineState, useEngine } from "../state/engine";
import { shellApi } from "../client/shell";
import { COLOUR_MAPS } from "./ColourMapControl";
import { formatValue } from "../logic/format";
import { UNDECLARED } from "./primitives";

export function EngineField() {
  const e = useEngine();
  const [unit, setUnit] = useState("");
  const [path, setPath] = useState("");
  const [written, setWritten] = useState<string | null>(null);

  if (e.reachability.kind !== "reachable" || !e.datasetId) return null;
  const shell = shellApi();
  const chosen = e.fields.find((one) => one.name === e.fieldName);
  const maximum = e.statistics?.maximum;
  const minimum = e.statistics?.minimum;

  return (
    <section className="prop-section" aria-label="エンジンの結果">
      <header className="prop-note">エンジン：{e.sourceName}</header>

      <div className="prop-row">
        <label htmlFor="engine-field">場</label>
        <select
          id="engine-field"
          className="field-input"
          value={e.fieldName ?? ""}
          onChange={(event) => void engineState.chooseField(event.target.value)}
        >
          {e.fields.map((one) => (
            <option key={one.name} value={one.name}>
              {one.name}（{one.association === "point" ? "節点" : one.association === "cell" ? "要素" : one.association}・
              {one.unit ?? UNDECLARED}）
            </option>
          ))}
        </select>
      </div>

      <div className="prop-row">
        <label htmlFor="engine-map">カラーマップ</label>
        <select
          id="engine-map"
          className="field-input"
          value={e.colourMap}
          onChange={(event) => void engineState.chooseColourMap(event.target.value)}
        >
          {COLOUR_MAPS.map((one) => (
            <option key={one.id} value={one.id}>
              {one.name}
            </option>
          ))}
        </select>
      </div>

      <div className="prop-row">
        <label htmlFor="engine-unit">単位を宣言</label>
        <input
          id="engine-unit"
          className="field-input"
          value={unit}
          placeholder={chosen?.unit ?? "MPa / K / mm …"}
          onChange={(event) => setUnit(event.target.value)}
        />
        <button
          type="button"
          className="btn"
          disabled={!unit || !e.fieldName || e.busy}
          onClick={() => {
            if (e.fieldName) void engineState.declareUnit(e.fieldName, unit);
          }}
        >
          宣言
        </button>
      </div>
      <p className="prop-note">
        宣言は人が行います。ファイルから推測はしません（XC-003）。
        {chosen?.unit ? `いまの宣言：${chosen.unit}` : `いまは${UNDECLARED}`}
      </p>

      {minimum && maximum ? (
        <p className="prop-note">
          最小 {minimum.value === null ? "値なし" : formatValue(minimum.value, minimum.digits)}・最大{" "}
          {maximum.value === null ? "値なし" : formatValue(maximum.value, maximum.digits)}{" "}
          {maximum.unit ?? UNDECLARED}
          {maximum.location ? `（${maximum.location}）` : null}
        </p>
      ) : null}

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
          disabled={!path || e.busy}
          onClick={async () => {
            const done = await engineState.exportReport(path);
            setWritten(done ? `${done.path}（${done.bytes} バイト）` : null);
          }}
        >
          書き出す
        </button>
      </div>
      {written ? <p className="prop-note">書き出しました：{written}</p> : null}
    </section>
  );
}
