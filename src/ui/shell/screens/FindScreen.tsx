/* Find - condition-based point/cell selection (the screen the spec named as missing; CT-007 is
 * CASE selection, this is elements). Three ways to state a condition - expression, source ids,
 * one-field threshold - against one case / dataset / association. What comes back is honest about
 * what it is: the match count and rows are computed on the full dataset (INV-001), ids are the
 * source's own identifiers (GlobalNodeId, INV-023), node values say they are element averages
 * (INV-032), units are declared or marked undeclared and never inferred (XC-003), and an
 * unresolvable name is named at its character position with nothing selected. An empty condition
 * touches nothing. A kept selection becomes a document object shared with graph / table / diff /
 * pipeline.
 *
 * CT-003 has no selection operation yet (the area is new); actions dispatch through submit as
 * `script.run` with a find.* instruction until the contract grows the real operations. */
import { useState } from "react";
import "./FindScreen.css";
import { submit } from "../../client/operations";
import { disabledBecause } from "../../logic/format";
import { FieldSelector, type FieldOption } from "../../shared/FieldSelector";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { QuantityChip } from "../../shared/QuantityChip";
import { UnitLabel } from "../../shared/UnitLabel";
import { NumberCell } from "../../shared/NumberCell";
import { UnresolvedList } from "../../shared/UnresolvedList";
import { ViewportPlaceholder } from "../../shared/ViewportPlaceholder";

type Mode = "expression" | "ids" | "threshold";

/* Names in scope: the dataset's fields with their association - point and cell values of one
 * quantity are different numbers (INV-032), so the association is part of the name's identity. */
const FIELDS: FieldOption[] = [
  { name: "相当応力", association: "point", unit: "MPa" },
  { name: "変位量", association: "point", unit: "mm" },
  { name: "温度", association: "point", unit: null },
  { name: "接触圧", association: "cell", unit: "MPa" },
  { name: "板厚", association: "cell", unit: "mm" },
];

const EXPRESSION = "相当応力 > 180 [MPa]";
const BAD_EXPRESSION = "相当応力 > 180 [MPa] && 板圧 < 2.0 [mm]";
const BAD_NAME = "板圧";
const BAD_POSITION = 20; // 0-based index of 板圧 - shown to people as 21文字目

const MATCH_COUNT = "2,847";
const TOTAL_COUNT = "182,304";

/* First rows, value-descending. Digits per INV-014: the float32 source supports four significant
 * digits here, and the display claims no more. */
const MATCH_ROWS = [
  { id: "204812", value: "247.3", block: "溶接部A" },
  { id: "204811", value: "244.9", block: "溶接部A" },
  { id: "198406", value: "236.1", block: "溶接部B" },
  { id: "198391", value: "231.8", block: "溶接部B" },
  { id: "173025", value: "219.4", block: "フランジ" },
  { id: "172998", value: "210.6", block: "フランジ" },
  { id: "151240", value: "198.2", block: "リブ根元" },
  { id: "151233", value: "184.5", block: "リブ根元" },
] as const;

/* Kept selections are document objects: they survive this screen and are referenced elsewhere. */
const KEPT_SELECTIONS = [
  { name: "高応力領域", meta: "1,204 節点・Run 12", refs: "グラフ1・差分1" },
  { name: "溶接部近傍", meta: "312 要素・Run 12", refs: "パイプライン1" },
  { name: "フランジ穴縁（ボルト孔まわり 3mm 帯）", meta: "48 節点・Run 11", refs: "参照なし" },
] as const;

/* Where the highlighted nodes sit on the placeholder silhouette (design state, not a rendering). */
const HIGHLIGHT_DOTS: readonly (readonly [number, number])[] = [
  [204, 100], [212, 108], [220, 118], [228, 126], [214, 126],
  [206, 118], [222, 136], [232, 142], [240, 138], [216, 96],
  [226, 110], [236, 128],
] as const;

function HighlightOverlay(props: { dim: boolean }) {
  return (
    <svg
      viewBox="0 0 400 300"
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}
      aria-hidden="true"
    >
      <g fill="var(--ink-strong)" opacity={props.dim ? 0.4 : 0.9}>
        {HIGHLIGHT_DOTS.map(([x, y]) => (
          <circle key={`${x}:${y}`} cx={x} cy={y} r={2.2} />
        ))}
      </g>
      <path
        d="M198 92 Q244 96 246 144 Q232 152 210 132 Q196 112 198 92 Z"
        fill="none"
        stroke="var(--ink-strong)"
        strokeWidth={1}
        strokeDasharray="3 3"
        opacity={props.dim ? 0.35 : 0.7}
      />
    </svg>
  );
}

export function FindScreen(props: { variant: string }) {
  const variant = props.variant;
  const [modeChoice, setModeChoice] = useState<Mode | null>(null);
  const [association, setAssociation] = useState<"point" | "cell">("point");
  const [thresholdField, setThresholdField] = useState<string>("相当応力");
  const [keepName, setKeepName] = useState<string>("180MPa 超過域");

  const mode: Mode = modeChoice ?? "expression";
  const thresholdUnit = FIELDS.find((field) => field.name === thresholdField)?.unit ?? null;

  const expressionText =
    variant === "empty" ? "" : variant === "unresolvable" ? BAD_EXPRESSION : EXPRESSION;

  /* Why the run button is disabled - one wording source (disabledBecause), title and inline note. */
  const runBlocked: string | null =
    mode === "expression" && variant === "empty"
      ? "条件が空です"
      : mode === "expression" && variant === "unresolvable"
        ? `名前「${BAD_NAME}」を解決できません（${BAD_POSITION + 1}文字目）`
        : mode === "threshold" && thresholdUnit === null
          ? `「${thresholdField}」の単位が未宣言のため、しきい値の次元を検査できません`
          : null;

  const keepBlocked: string | null =
    variant === "default"
      ? null
      : variant === "empty"
        ? "新しい選択がありません（条件が空です）"
        : "選択が空です（条件が解決できません）";

  return (
    <div className="fi-canvas">
      {/* ---- query builder ---------------------------------------------------------------- */}
      <section className="fi-builder" aria-label="選択条件">
        <div className="prop-section">
          <h3>対象</h3>
          <div className="prop-row">
            <label htmlFor="fi-case">ケース</label>
            <select id="fi-case" className="field-input" defaultValue="run12">
              <option value="run12">Run 12</option>
              <option value="run11">Run 11</option>
            </select>
          </div>
          <div className="prop-row">
            <label htmlFor="fi-dataset">データセット</label>
            <select id="fi-dataset" className="field-input" defaultValue="result">
              <option value="result">run12_result.vtu</option>
              <option value="thermal">run12_thermal.vtu</option>
            </select>
          </div>
          <div className="prop-row">
            <label id="fi-assoc-label">種類</label>
            <span className="fi-seg" role="group" aria-labelledby="fi-assoc-label">
              <button
                aria-pressed={association === "point"}
                onClick={() => setAssociation("point")}
              >
                節点
              </button>
              <button
                aria-pressed={association === "cell"}
                onClick={() => setAssociation("cell")}
              >
                要素
              </button>
              <button {...disabledBecause("このデータセットにブロック定義がありません")}>
                ブロック
              </button>
            </span>
          </div>
          <p className="prop-note">run12_result.vtu：182,304 節点・96,410 要素（読み込み済み）</p>
        </div>

        <div className="prop-section">
          <h3>条件</h3>
          <div className="fi-seg" role="group" aria-label="条件の指定方法" style={{ marginBottom: 8 }}>
            <button aria-pressed={mode === "expression"} onClick={() => setModeChoice("expression")}>
              条件式
            </button>
            <button aria-pressed={mode === "ids"} onClick={() => setModeChoice("ids")}>
              ID指定
            </button>
            <button aria-pressed={mode === "threshold"} onClick={() => setModeChoice("threshold")}>
              しきい値
            </button>
          </div>

          {mode === "expression" ? (
            <div>
              <textarea
                key={variant}
                className="field-input fi-mono"
                rows={2}
                defaultValue={expressionText}
                spellCheck={false}
                aria-label="条件式"
                aria-invalid={variant === "unresolvable"}
                placeholder="例：相当応力 > 180 [MPa]"
              />
              {variant === "unresolvable" ? (
                <pre className="fi-caret" aria-hidden="true">
                  <span className="fi-ghost">{BAD_EXPRESSION.slice(0, BAD_POSITION)}</span>
                  <span className="fi-mark">{"^".repeat(BAD_NAME.length)}</span>
                </pre>
              ) : null}
              {variant === "default" ? (
                <p className="fi-status good" role="status">
                  次元検査：左辺 MPa（「相当応力」の宣言単位）＝右辺 MPa — 一致
                </p>
              ) : variant === "empty" ? (
                <p className="fi-status" role="status">
                  式が空です — 検索は行われず、前の選択には触れません
                </p>
              ) : (
                <p className="fi-status error" role="alert">
                  {BAD_POSITION + 1}文字目：名前「{BAD_NAME}」を解決できません
                </p>
              )}
              <div className="fi-scope" aria-label="スコープにある名前">
                {FIELDS.map((field) => (
                  <span className="fi-scope-chip" key={field.name}>
                    <b>{field.name}</b>
                    <span>
                      <UnitLabel unit={field.unit} />
                      ・{field.association === "point" ? "節点" : "要素"}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          ) : mode === "ids" ? (
            <div>
              <textarea
                className="field-input fi-mono"
                rows={3}
                defaultValue={"204812, 204811,\n198391-198406"}
                spellCheck={false}
                aria-label="IDの一覧"
              />
              <p className="fi-status">
                GlobalNodeId（ソースの識別子）で指定します — 読み込み順の配列添字ではありません。
                範囲は「開始-終了」。
              </p>
            </div>
          ) : (
            <div>
              <div className="prop-row">
                <label>フィールド</label>
                <FieldSelector fields={FIELDS} value={thresholdField} onChange={setThresholdField} />
              </div>
              <div className="prop-row">
                <label htmlFor="fi-comparator">比較</label>
                <select id="fi-comparator" className="field-input" defaultValue="gt">
                  <option value="gt">＞（超える）</option>
                  <option value="ge">≧（以上）</option>
                  <option value="lt">＜（未満）</option>
                  <option value="le">≦（以下）</option>
                </select>
              </div>
              <div className="prop-row">
                <label htmlFor="fi-threshold">しきい値</label>
                <span style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
                  <input
                    id="fi-threshold"
                    className="field-input"
                    defaultValue="180"
                    inputMode="decimal"
                  />
                  <UnitLabel unit={thresholdUnit} />
                </span>
              </div>
              <p className="fi-status">
                しきい値はフィールドの宣言単位で解釈されます。単位が未宣言の場合は検査できず、実行できません（XC-003）。
              </p>
            </div>
          )}
        </div>

        <div className="fi-actions">
          <button
            className="btn primary"
            {...(runBlocked ? disabledBecause(runBlocked) : {})}
            onClick={() =>
              submit({
                operation: "script.run",
                parameters: { instruction: "find.run", mode, association, expression: expressionText },
              })
            }
          >
            選択を実行
          </button>
          {runBlocked ? (
            <p className="fi-status" role="status">{disabledBecause(runBlocked).title}</p>
          ) : null}
        </div>
      </section>

      {/* ---- result: viewport highlight, count, first rows, keep-as-named ------------------ */}
      <section className="fi-result" aria-label="選択結果">
        <ViewportPlaceholder
          caseName="Run 12"
          fieldLabel="相当応力 [MPa]"
          legendTicks={["250", "200", "150", "100", "50", "0"]}
        >
          {variant !== "unresolvable" ? <HighlightOverlay dim={variant === "empty"} /> : null}
          <div className="pane-badge" style={{ top: "auto", bottom: 8, left: 8 }} role="note">
            {variant === "default"
              ? `一致 ${MATCH_COUNT} 節点をハイライト表示中（強調は輝度で示します）`
              : variant === "empty"
                ? "前の選択「高応力領域」を表示中 — 条件が空のため変更されません"
                : "ハイライトなし — 条件が解決できず、何も選択されていません"}
          </div>
        </ViewportPlaceholder>

        <div className="fi-result-panel">
          {variant === "default" ? (
            <>
              <div className="fi-result-head">
                <b>結果</b>
                <span>
                  <span className="fi-count">{MATCH_COUNT}</span>{" "}
                  <span className="fi-count-rest">節点が一致 ／ 全 {TOTAL_COUNT} 節点（1.6 %）</span>
                </span>
                <ProvenanceBadge origin="computed" />
              </div>
              <p className="fi-status" style={{ margin: "0 12px 6px" }}>
                値は完全データの節点値（要素からの平均、INV-032）。ID はソースの識別子です（INV-023）。
              </p>
              <div className="table-scroll" style={{ margin: "0 12px" }}>
                <table className="value-table">
                  <thead>
                    <tr>
                      <th title="ソースの識別子（配列添字ではありません — INV-023）">GlobalNodeId</th>
                      <th style={{ textAlign: "right" }}>
                        相当応力（<UnitLabel unit="MPa" />）
                      </th>
                      <th>ブロック</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MATCH_ROWS.map((row) => (
                      <tr key={row.id}>
                        <td className="fi-id">{row.id}</td>
                        <NumberCell value={row.value} />
                        <td>{row.block}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="fi-status" style={{ margin: "6px 12px" }}>
                値の降順で上位 8 行を表示 — 全 {MATCH_COUNT} 行は保持後にグラフ・表から参照できます。
              </p>
            </>
          ) : variant === "empty" ? (
            <div style={{ padding: "10px 12px", display: "grid", gap: 8 }}>
              <div className="notice" role="status">
                <b>条件が空です。</b>
                <span className="why">
                  前の選択「高応力領域」（1,204 節点・2026-08-24 保持）には触れません — 空の条件は選択を消去しません。
                </span>
              </div>
              <p className="fi-status" style={{ margin: 0 }}>新しい照合は行われていません。</p>
            </div>
          ) : (
            <div style={{ padding: "10px 12px", display: "grid", gap: 8 }}>
              <UnresolvedList
                title="解決できない名前"
                items={[
                  {
                    what: `${BAD_NAME}（${BAD_POSITION + 1}文字目）`,
                    missing: "スコープにこの名前のフィールド・変数がありません",
                  },
                ]}
              />
              <p className="fi-status" style={{ margin: 0 }} role="status">
                何も選択されていません — 条件は適用されませんでした。
              </p>
            </div>
          )}

          <div className="fi-keep">
            <input
              className="field-input"
              value={keepName}
              onChange={(event) => setKeepName(event.target.value)}
              aria-label="選択の名前"
              {...(keepBlocked ? disabledBecause(keepBlocked) : {})}
            />
            <button
              className="btn primary"
              {...(keepBlocked ? disabledBecause(keepBlocked) : {})}
              onClick={() =>
                submit({
                  operation: "script.run",
                  parameters: { instruction: "find.keep", name: keepName, expression: expressionText },
                })
              }
            >
              名前を付けて保持
            </button>
          </div>
          <p className="fi-status" style={{ margin: "0 12px 8px" }}>
            {keepBlocked
              ? disabledBecause(keepBlocked).title
              : "保持した選択は文書オブジェクトになり、グラフ・表・差分・パイプラインから参照できます。"}
          </p>
        </div>
      </section>
    </div>
  );
}

export function FindRail(props: { tab: string; variant: string }) {
  if (props.tab !== "condition") {
    return <p className="prop-note" style={{ padding: 10 }}>このタブの内容はありません</p>;
  }
  const variant = props.variant;
  return (
    <div>
      <div className="prop-section">
        <h3>条件の要約</h3>
        {variant === "empty" ? (
          <p className="prop-note" style={{ marginTop: 0 }}>
            条件は空です。前の選択「高応力領域」には触れません。
          </p>
        ) : (
          <pre className="fi-summary-expr">
            {variant === "unresolvable" ? BAD_EXPRESSION : EXPRESSION}
          </pre>
        )}
        {variant === "default" ? (
          <>
            <div className="prop-row" style={{ marginTop: 8 }}>
              <label>しきい値</label>
              <span style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
                <QuantityChip value="180" unit="MPa" title="式に書かれた単位" />
                <ProvenanceBadge origin="declared" />
              </span>
            </div>
            <p className="fi-status good" role="status">次元一致（MPa ＝ MPa）・一致 {MATCH_COUNT} 節点</p>
          </>
        ) : variant === "unresolvable" ? (
          <p className="fi-status error" role="alert">
            {BAD_POSITION + 1}文字目：「{BAD_NAME}」を解決できません — 何も選択されていません
          </p>
        ) : null}
      </div>

      <div className="prop-section">
        <h3>対象</h3>
        <div className="prop-row">
          <label>ケース</label>
          <span>Run 12</span>
        </div>
        <div className="prop-row">
          <label>データセット</label>
          <span
            style={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
            title="run12_result.vtu（182,304 節点・96,410 要素）"
          >
            run12_result.vtu
          </span>
        </div>
        <div className="prop-row">
          <label>種類</label>
          <span>節点</span>
        </div>
      </div>

      <div className="prop-section">
        <h3>保持した選択</h3>
        <p className="prop-note" style={{ margin: "0 0 6px" }}>
          文書オブジェクト — グラフ・表・差分・パイプラインから参照できます
        </p>
        {KEPT_SELECTIONS.map((sel) => (
          <button
            key={sel.name}
            className="fi-sel"
            title={sel.name}
            onClick={() =>
              submit({ operation: "script.run", parameters: { instruction: "find.open", name: sel.name } })
            }
          >
            <span className="name">{sel.name}</span>
            <span className="meta">
              <span>{sel.meta}</span>
              <span>参照：{sel.refs}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
