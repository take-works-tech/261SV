/* The three things XC-257's prototype asks for that a picture alone cannot do: choose the field the
 * colours mean, declare the unit they are in, and write the deliverable.
 *
 * Shown only when an engine is connected, beside the design-state rail rather than in place of it.
 * Every value here came from an answer - the field list, the unit, the range - and nothing is
 * computed: a unit this layer invented would be a unit nobody declared (XC-003).
 */
import { useState } from "react";
import { engineState, useEngine } from "../state/engine";
import { COLOUR_MAPS } from "./ColourMapControl";
import { ReportExport } from "./ReportExport";
import { formatValue } from "../logic/format";
import { statisticsRows } from "../logic/copy";
import { CopyValues } from "./CopyValues";
import { COPY_LABELS, UNDECLARED } from "./primitives";

export function EngineField() {
  const e = useEngine();
  const [unit, setUnit] = useState("");

  if (e.reachability.kind !== "reachable" || !e.datasetId) return null;
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
          {e.statistics?.averaging === "unaveraged" ? "要素値（平均なし）：" : null}
          最小 {minimum.value === null ? "値なし" : formatValue(minimum.value, minimum.digits)}・最大{" "}
          {maximum.value === null ? "値なし" : formatValue(maximum.value, maximum.digits)}{" "}
          {maximum.unit ?? UNDECLARED}
          {maximum.location ? `（${maximum.location}）` : null}
        </p>
      ) : null}
      {e.statistics?.averaged ? (
        /* The second number, never offered as the number: the averaged peak with the spread it was
         * averaged from, which is the only discretisation indicator one solve can give (INV-032, INV-033). */
        <p className="prop-note">
          節点平均：最小 {e.statistics.averaged.minimum.value === null ? "値なし" : formatValue(e.statistics.averaged.minimum.value, e.statistics.averaged.minimum.digits)}・最大{" "}
          {e.statistics.averaged.maximum.value === null ? "値なし" : formatValue(e.statistics.averaged.maximum.value, e.statistics.averaged.maximum.digits)}{" "}
          {e.statistics.averaged.maximum.unit ?? UNDECLARED}
          {e.statistics.averaged.maximum.location ? `（${e.statistics.averaged.maximum.location}）` : null}
          。その節点でのばらつき{" "}
          {e.statistics.averaged.spreadAtMaximum.value === null ? "値なし" : formatValue(e.statistics.averaged.spreadAtMaximum.value, e.statistics.averaged.spreadAtMaximum.digits)}{" "}
          {e.statistics.averaged.spreadAtMaximum.unit ?? UNDECLARED}
          {e.statistics.averaged.spreadFraction.value === null ? null : `（平均比 ${Math.round(e.statistics.averaged.spreadFraction.value * 100)}%）`}
          — メッシュ細分の目安であって、精度の保証ではありません。{e.statistics.averaged.disagreement}
        </p>
      ) : e.statistics?.averagingRefused ? (
        <p className="prop-note">節点平均は求められませんでした：{e.statistics.averagingRefused}</p>
      ) : null}
      {e.statistics && e.fieldName ? (
        <div className="prop-row">
          <label>値を写す</label>
          <CopyValues
            rows={statisticsRows(e.fieldName, e.statistics, COPY_LABELS)}
            title="最大・最小・平均・欠損数を、単位・有効桁・来歴・位置つきのタブ区切りで写します。表計算にそのまま貼れます（XC-279）"
          />
        </div>
      ) : null}

      <div className="prop-row">
        <button
          type="button"
          className="btn"
          disabled={!e.viewId || e.busy}
          onClick={() => void engineState.keepCamera()}
          title="いまの向きをビューの定義に書きます：取り消し 1 段、未保存 1 件。回すだけでは定義は変わらず、レポートは保存した向きで描きます（XC-270）"
        >
          この向きをビューに保存
        </button>
      </div>
      <ReportExport />
    </section>
  );
}
