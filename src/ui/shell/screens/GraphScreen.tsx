/* Graph screen (mockup 2, XC-256): the design-state catalogue's graph work area.
 *
 * Composition follows mockup 1's graph canvas and property editor; colours follow tokens.css.
 * The rules this screen exists to show:
 *   XC-221  which cases the graph covers is a property of the graph, not of one series;
 *           a series' look defaults to the theme, and the theme's sample is its first choice.
 *   XC-213  one axis is edited at a time; a fixed range that cuts data says so on the figure.
 *   XC-228  two series on one axis declaring different units: the axis prints 単位混在 and the
 *           units move to the legend - the axis never prints either (XC-003: no inference).
 *   XC-215  choices about appearance are drawn, with the name under the sample.
 *   XC-001  a missing point is a stated absence in the figure, never a bridge or a zero;
 *           XC-090: what did not resolve is named, and the preflight refuses it by name.
 * Values are illustrative but honest: unit or 単位未宣言, provenance, digits per INV-014.
 */
import { useState, type ReactNode } from "react";
import { session } from "../../state/session";
import { submit } from "../../client/operations";
import { formatValue, disabledBecause } from "../../logic/format";
import { QuantityChip } from "../../shared/QuantityChip";
import { UnitLabel } from "../../shared/UnitLabel";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { MissingDataStyle } from "../../shared/MissingDataStyle";
import { UnresolvedList } from "../../shared/UnresolvedList";
import { FieldSelector, type FieldOption } from "../../shared/FieldSelector";
import { PROVENANCE_LABEL, type Provenance } from "../../shared/primitives";
import "./GraphScreen.css";

/* ---- the illustrative graph definition ----------------------------------------------------- */

type LineKind = "solid" | "dashed" | "dotted" | "none";
type MarkerKind = "circle" | "square" | "triangle" | "none";

type SeriesPt = { x: number; v: number | null; caseName: string; missingBecause?: string };

type SeriesDef = {
  id: string;
  label: string;
  /** The full quantity name - legend rows truncate and carry this as the readable full text. */
  quantityLong?: string;
  srcKind: "dataset" | "reference" | "unresolved";
  quantityName: string | null;
  unit: string | null;
  provenance: Provenance | null;
  digits: number;
  axis: "y" | "y2";
  missingPolicy: string;
  line: LineKind;
  marker: MarkerKind;
  /** true = the look is the theme's default, not an override (XC-221). */
  themed: boolean;
  stroke: string;
  /** A constant reference value, shown in the legend with its digits. */
  constant?: { value: string };
  /** Present only while units are mixed on one axis: this series keeps its own scale, which is
   *  exactly why the shared axis cannot print a unit (XC-228). */
  yScale?: [number, number];
  pts: SeriesPt[];
};

const S_STRESS: SeriesDef = {
  id: "s-stress",
  label: "最大応力",
  quantityLong: "最大応力（von Mises・要素値の節点平均）",
  srcKind: "dataset",
  quantityName: "最大応力",
  unit: "MPa",
  provenance: "dataset",
  digits: 4,
  axis: "y",
  missingPolicy: "欠損として表示・凡例に残す",
  line: "solid",
  marker: "circle",
  themed: true,
  stroke: "var(--ink-strong)",
  pts: [
    { x: 8, v: 241.7, caseName: "Run12-T08" },
    { x: 10, v: 228.4, caseName: "Run12-T10" },
    { x: 12, v: 214.9, caseName: "Run12-T12" },
    { x: 14, v: null, caseName: "Run12-T14", missingBecause: "結果ファイルにフィールドなし" },
    { x: 16, v: 198.2, caseName: "Run12-T16" },
  ],
};

const S_ALLOW: SeriesDef = {
  id: "s-allow",
  label: "設計許容応力",
  quantityLong: "設計許容応力（設計ノートの記載値）",
  srcKind: "reference",
  quantityName: null,
  unit: "MPa",
  provenance: "reference",
  digits: 3,
  axis: "y",
  missingPolicy: "欠損として表示・凡例に残す",
  line: "dashed",
  marker: "none",
  themed: false,
  stroke: "var(--ink-muted)",
  constant: { value: "235" },
  pts: [
    { x: 8, v: 235, caseName: "設計ノート" },
    { x: 16, v: 235, caseName: "設計ノート" },
  ],
};

const S_DEFLECTION: SeriesDef = {
  id: "s-defl",
  label: "最大たわみ",
  quantityLong: "最大たわみ（節点変位の最大値）",
  srcKind: "dataset",
  quantityName: "最大たわみ",
  unit: "mm",
  provenance: "dataset",
  digits: 3,
  axis: "y",
  missingPolicy: "欠損として表示・凡例に残す",
  line: "dotted",
  marker: "square",
  themed: true,
  stroke: "var(--ink)",
  yScale: [0, 20],
  pts: [
    { x: 8, v: 5.71, caseName: "Run12-T08" },
    { x: 10, v: 4.83, caseName: "Run12-T10" },
    { x: 12, v: 4.12, caseName: "Run12-T12" },
    { x: 14, v: 3.58, caseName: "Run12-T14" },
    { x: 16, v: 3.14, caseName: "Run12-T16" },
  ],
};

const S_UNRESOLVED: SeriesDef = {
  id: "s-temp",
  label: "系列 3（参考温度）",
  srcKind: "unresolved",
  quantityName: null,
  unit: null,
  provenance: null,
  digits: 0,
  axis: "y",
  missingPolicy: "欠損として表示・凡例に残す",
  line: "solid",
  marker: "none",
  themed: true,
  stroke: "var(--ink-faint)",
  pts: [],
};

function seriesFor(variant: string): SeriesDef[] {
  if (variant === "axis-unit-conflict") return [S_STRESS, S_ALLOW, S_DEFLECTION];
  if (variant === "series-unresolved" || variant === "output-preflight")
    return [S_STRESS, S_ALLOW, S_UNRESOLVED];
  return [S_STRESS, S_ALLOW];
}

/** The dataset's fields, with association - point and cell values are different numbers (INV-032). */
const FIELDS: FieldOption[] = [
  { name: "最大応力", association: "point", unit: "MPa" },
  { name: "最大応力（未平均）", association: "cell", unit: "MPa" },
  { name: "最大たわみ", association: "point", unit: "mm" },
  { name: "温度", association: "point", unit: null },
];

const GRAPH_ID = "graph-cross-thickness";

function update(field: string, value: unknown): void {
  // Every action dispatches through the one command path (INV-006); design states log only.
  submit({ operation: "graph.update", parameters: { graph: GRAPH_ID, [field]: value } });
}

/* ---- chart geometry (an SVG placeholder drawn with tokens - the chart is chrome) ------------ */

const PX = { x0: 64, x1: 620, y0: 30, y1: 292 } as const;
const X_DOMAIN: [number, number] = [7.5, 16.5];
const X_TICKS = [8, 10, 12, 14, 16];

function xPix(v: number): number {
  return PX.x0 + ((v - X_DOMAIN[0]) / (X_DOMAIN[1] - X_DOMAIN[0])) * (PX.x1 - PX.x0);
}
function yPix(v: number, domain: [number, number]): number {
  return PX.y1 - ((v - domain[0]) / (domain[1] - domain[0])) * (PX.y1 - PX.y0);
}

const DASH: Record<LineKind, string | undefined> = {
  solid: undefined,
  dashed: "7 5",
  dotted: "1.5 4",
  none: undefined,
};

type SeriesGeometry = {
  drawn: { px: number; py: number; v: number; pt: SeriesPt }[];
  excluded: SeriesPt[];
  missing: SeriesPt[];
  segments: string[];
};

function seriesGeometry(s: SeriesDef, axisDomain: [number, number]): SeriesGeometry {
  const domain = s.yScale ?? axisDomain;
  const drawn: SeriesGeometry["drawn"] = [];
  const excluded: SeriesPt[] = [];
  const missing: SeriesPt[] = [];
  const segments: string[] = [];
  let current: string[] = [];
  const flush = () => {
    if (current.length > 0) segments.push(current.join(" "));
    current = [];
  };
  for (const pt of s.pts) {
    if (pt.v === null) {
      missing.push(pt);
      flush(); // an honest gap - never a bridge across a missing value (XC-001)
      continue;
    }
    if (!s.yScale && (pt.v < axisDomain[0] || pt.v > axisDomain[1])) {
      excluded.push(pt);
      flush();
      continue;
    }
    const px = xPix(pt.x);
    const py = yPix(pt.v, domain);
    drawn.push({ px, py, v: pt.v, pt });
    current.push(`${px.toFixed(1)},${py.toFixed(1)}`);
  }
  flush();
  return { drawn, excluded, missing, segments };
}

function ChartSvg(props: {
  series: SeriesDef[];
  yDomain: [number, number];
  yTicks: number[];
  yTitle: string;
  yTitleWarn?: boolean;
  hideYTickLabels?: boolean;
}): ReactNode {
  const geometries = props.series
    .filter((s) => s.srcKind !== "unresolved")
    .map((s) => ({ s, geo: seriesGeometry(s, props.yDomain) }));
  return (
    <svg
      className="gr-svg"
      viewBox="0 0 680 340"
      role="img"
      aria-label={`グラフのプレビュー：${props.yTitle}・横軸 板厚［mm］`}
    >
      <rect
        x={PX.x0}
        y={PX.y0}
        width={PX.x1 - PX.x0}
        height={PX.y1 - PX.y0}
        fill="var(--surface-well)"
      />
      {props.yTicks.map((t) => (
        <g key={`y-${t}`}>
          <line
            x1={PX.x0}
            x2={PX.x1}
            y1={yPix(t, props.yDomain)}
            y2={yPix(t, props.yDomain)}
            stroke="var(--line)"
          />
          {props.hideYTickLabels ? null : (
            <text className="gr-tick" x={PX.x0 - 6} y={yPix(t, props.yDomain) + 3} textAnchor="end">
              {formatValue(t, 3)}
            </text>
          )}
        </g>
      ))}
      {X_TICKS.map((t) => (
        <g key={`x-${t}`}>
          <line x1={xPix(t)} x2={xPix(t)} y1={PX.y0} y2={PX.y1} stroke="var(--line)" />
          <text className="gr-tick" x={xPix(t)} y={PX.y1 + 16} textAnchor="middle">
            {formatValue(t, 2)}
          </text>
        </g>
      ))}
      <line x1={PX.x0} x2={PX.x0} y1={PX.y0} y2={PX.y1} stroke="var(--line-strong)" />
      <line x1={PX.x0} x2={PX.x1} y1={PX.y1} y2={PX.y1} stroke="var(--line-strong)" />
      <text
        className={props.yTitleWarn ? "gr-axis-title warn" : "gr-axis-title"}
        x={PX.x0}
        y={14}
        textAnchor="start"
      >
        {props.yTitle}
      </text>
      <text
        className="gr-axis-title"
        x={(PX.x0 + PX.x1) / 2}
        y={332}
        textAnchor="middle"
      >
        板厚［mm］
      </text>
      {geometries.map(({ s, geo }) => (
        <g key={s.id}>
          <title>
            {`${s.quantityLong ?? s.label}・${s.unit ?? "単位未宣言"}・来歴：${
              s.provenance ? PROVENANCE_LABEL[s.provenance] : "未確定"
            }`}
          </title>
          {s.line !== "none"
            ? geo.segments.map((points) => (
                <polyline
                  key={points}
                  points={points}
                  fill="none"
                  stroke={s.stroke}
                  strokeWidth={s.line === "solid" ? 2 : 1.5}
                  strokeDasharray={DASH[s.line]}
                  strokeLinecap="round"
                />
              ))
            : null}
          {geo.drawn.map(({ px, py, v, pt }) => {
            if (s.marker === "none") return null;
            // Hover shows the value with its unit, case and provenance - never the value alone.
            const hover = `${s.label}：${formatValue(v, s.digits)} ${s.unit ?? "単位未宣言"}・${
              pt.caseName
            }・板厚 ${formatValue(pt.x, 2)} mm・来歴：${
              s.provenance ? PROVENANCE_LABEL[s.provenance] : "未確定"
            }`;
            return (
              <g key={`${s.id}-${pt.x}`}>
                <title>{hover}</title>
                {s.marker === "circle" ? (
                  <circle cx={px} cy={py} r={4} fill={s.stroke} />
                ) : s.marker === "square" ? (
                  <rect x={px - 3.5} y={py - 3.5} width={7} height={7} fill={s.stroke} />
                ) : (
                  <path
                    d={`M${px} ${py - 4.5} L${px + 4} ${py + 3.5} L${px - 4} ${py + 3.5} Z`}
                    fill={s.stroke}
                  />
                )}
              </g>
            );
          })}
          {geo.missing.map((pt) => (
            <g key={`${s.id}-missing-${pt.x}`}>
              <title>
                {`${pt.caseName}・板厚 ${formatValue(pt.x, 2)} mm：値なし（${
                  pt.missingBecause ?? "理由未記録"
                }）・置換なし`}
              </title>
              <text className="gr-missing-t" x={xPix(pt.x)} y={PX.y1 - 10} textAnchor="middle">
                値なし
              </text>
            </g>
          ))}
        </g>
      ))}
    </svg>
  );
}

/* ---- shared drawn samples (XC-215: the appearance is the option; the name stays under it) --- */

function SeriesSample(props: { line: LineKind; marker: MarkerKind; stroke?: string }): ReactNode {
  const stroke = props.stroke ?? "var(--ink)";
  return (
    <svg className="gr-mini" viewBox="0 0 34 12" aria-hidden="true">
      {props.line !== "none" ? (
        <line
          x1={1}
          y1={6}
          x2={33}
          y2={6}
          stroke={stroke}
          strokeWidth={props.line === "solid" ? 2 : 1.5}
          strokeDasharray={DASH[props.line]}
          strokeLinecap="round"
        />
      ) : null}
      {props.marker === "circle" ? <circle cx={17} cy={6} r={3} fill={stroke} /> : null}
      {props.marker === "square" ? <rect x={14} y={3} width={6} height={6} fill={stroke} /> : null}
      {props.marker === "triangle" ? <path d="M17 1.5 L20.5 9 L13.5 9 Z" fill={stroke} /> : null}
    </svg>
  );
}

function SampleButton(props: {
  name: string;
  selected: boolean;
  onSelect: () => void;
  title?: string;
  children: ReactNode;
}): ReactNode {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={props.selected}
      className="gr-sample"
      title={props.title ?? props.name}
      onClick={props.onSelect}
    >
      <span className="thumb">{props.children}</span>
      <span className="name">{props.name}</span>
    </button>
  );
}

function Row(props: { label: string; children: ReactNode }): ReactNode {
  return (
    <div className="prop-row">
      <label>{props.label}</label>
      {props.children}
    </div>
  );
}

/* ---- canvas -------------------------------------------------------------------------------- */

export function GraphScreen(props: { variant: string }): ReactNode {
  if (props.variant === "empty") return <GraphEmpty />;
  if (props.variant === "no-points") return <GraphNoPoints />;
  return <GraphFigure variant={props.variant} />;
}

function GraphFigure({ variant }: { variant: string }): ReactNode {
  const conflict = variant === "axis-unit-conflict";
  const fixedRange = variant === "axes";
  const [preflightDismissed, setPreflightDismissed] = useState(false);

  const series = seriesFor(variant);
  const yDomain: [number, number] = fixedRange ? [200, 260] : [180, 260];
  const yTicks = fixedRange ? [200, 220, 240, 260] : [180, 200, 220, 240, 260];
  const excluded = series
    .filter((s) => s.srcKind !== "unresolved" && !s.yScale)
    .flatMap((s) =>
      s.pts
        .filter((pt) => pt.v !== null && (pt.v < yDomain[0] || pt.v > yDomain[1]))
        .map((pt) => ({ s, pt })),
    );
  const unresolved = series.filter((s) => s.srcKind === "unresolved");

  return (
    <div className="gr-canvas">
      <header className="gr-head">
        <span className="gr-eyebrow">グラフ</span>
        <h2 className="gr-title">{conflict ? "板厚と最大応力・最大たわみ" : "板厚と最大応力"}</h2>
        <p className="gr-sub">
          ケース：明示選択（Run 12・板厚スイープ・5件）・集約：なし・種類：折れ線
        </p>
      </header>

      <div className="gr-figure">
        {/* XC-213: a fixed range that cuts data says so ON the figure, and in its exports. */}
        {fixedRange && excluded.length > 0 ? (
          <div className="notice warn">
            <b>Y軸は固定範囲 200–260 MPa</b>
            <span className="why">
              範囲外 {excluded.length}点（
              {excluded
                .map(
                  ({ s, pt }) =>
                    `${pt.caseName}・${pt.v === null ? "値なし" : `${formatValue(pt.v, s.digits)} ${s.unit ?? "単位未宣言"}`}`,
                )
                .join("、")}
              ）は描かれていません。この注記は図と書き出しの両方に入ります。
            </span>
          </div>
        ) : null}
        {/* XC-228: mixed units on one axis - the axis prints neither unit and no shared numerals. */}
        {conflict ? (
          <div className="notice warn">
            <b>この軸の系列が異なる単位を宣言しています（単位混在）</b>
            <span className="why">
              「最大応力」は MPa、「最大たわみ」は mm
              です。どちらかを軸に書くと、もう一方の目盛が誤って読まれるため、軸には「単位混在」と表示し、共通の目盛数値は表示しません。単位は凡例にあります。
            </span>
          </div>
        ) : null}

        <div className="gr-plotrow">
          <div className="gr-svgwrap">
            <ChartSvg
              series={series}
              yDomain={yDomain}
              yTicks={yTicks}
              yTitle={conflict ? "値［単位混在・単位は凡例］" : "応力［MPa］"}
              yTitleWarn={conflict}
              hideYTickLabels={conflict}
            />
          </div>
          <ul className="gr-legend" aria-label="凡例">
            {series.map((s) => (
              <li key={s.id} className="gr-legend-row" title={s.quantityLong ?? s.label}>
                <SeriesSample line={s.line} marker={s.marker} stroke={s.stroke} />
                <span className="gr-legend-text">
                  <span className="gr-legend-label">{s.label}</span>
                  <span className="gr-legend-sub">
                    {s.srcKind === "unresolved" ? (
                      // A no-quantity series is listed as no-data - never dropped from the legend.
                      <span className="missing-value">データなし（数量未選択）</span>
                    ) : s.constant ? (
                      <>
                        <QuantityChip
                          value={s.constant.value}
                          unit={s.unit}
                          title="出典：設計ノート・数値根拠には未使用"
                        />
                        {s.provenance ? <ProvenanceBadge origin={s.provenance} /> : null}
                      </>
                    ) : (
                      <>
                        <UnitLabel unit={s.unit} />
                        {s.provenance ? <ProvenanceBadge origin={s.provenance} /> : null}
                      </>
                    )}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="gr-prov">
          <span>ケース：明示選択・5件（Run 12 板厚スイープ）</span>
          <span>X：パラメーター「板厚」・宣言 mm</span>
          <span>
            欠損：Run12-T14 の最大応力は
            <MissingDataStyle because="結果ファイルにフィールドなし" />
            ・間隙として表示・置換なし
          </span>
        </div>
      </div>

      {variant === "output-preflight" && !preflightDismissed ? (
        <PreflightDialog unresolved={unresolved} onClose={() => setPreflightDismissed(true)} />
      ) : null}
    </div>
  );
}

/* graph.empty - manual / recommended / assistant offers; nothing is applied without confirmation */
function GraphEmpty(): ReactNode {
  return (
    <div className="gr-entry">
      <h2>グラフを開始</h2>
      <p>
        開始方法を選びます。どの方法も、内容を確認するまでグラフを作成せず、ワークスペースを変更しません。
      </p>
      <div className="gr-entry-grid">
        <button
          type="button"
          className="gr-entry-card"
          onClick={() => submit({ operation: "graph.create", parameters: { start: "manual" } })}
        >
          <b>手動</b>
          <p>物理量とケースを明示的に選んで、空の定義から組み立てます。</p>
          <p className="gr-entry-note">単位と来歴は選んだ数量から表示されます。</p>
        </button>
        <button
          type="button"
          className="gr-entry-card"
          onClick={() => submit({ operation: "graph.create", parameters: { start: "recommended" } })}
        >
          <b>推奨</b>
          <p>開いているデータから候補を提示します。プレビューのみ・自動適用しません。</p>
          <span className="gr-candidates">
            <span className="gr-candidate">板厚 × 最大応力（Run 12・5ケース）</span>
            <span className="gr-candidate">結果軸 × 最大たわみ（Run12-T16）</span>
          </span>
          <p className="gr-entry-note">選ぶまで作成されません。</p>
        </button>
        <button type="button" className="gr-entry-card" onClick={() => session.navigate("chat")}>
          <b>アシスタント提案</b>
          <p>会話で意図を伝えると、安全なグラフ定義を提案します。適用は確認後です。</p>
          <p className="gr-entry-note">会話画面へ移動します。</p>
        </button>
      </div>
      <p className="prop-note">
        推奨とアシスタント提案は定義を提示するだけで、確認するまで何も適用しません。
      </p>
    </div>
  );
}

/* graph.no-points - the emptying condition is named; an empty plot is never drawn (XC-001) */
function GraphNoPoints(): ReactNode {
  return (
    <div className="empty-state gr-nopoints">
      <span className="gr-warnglyph" aria-hidden="true">
        ⚠
      </span>
      <h2>選択条件に一致する点がありません</h2>
      <p>
        条件が 0
        点に解決したため、空のグラフは描画していません。直前の選択と既存の成果物は変更されていません。
      </p>
      <div className="gr-cond" aria-label="条件の解決過程">
        <div className="step">
          <span>選択領域「フランジ」</span>
          <span className="count">1,204 点</span>
        </div>
        <div className="step">
          <span>かつ フィールド「疲労寿命」に有効値</span>
          <span className="count warn">0 点</span>
        </div>
        <p className="prop-note">
          「疲労寿命」はこのケースでは未計算のため、全点が値なしです。ゼロや近傍値では補いません。
        </p>
      </div>
      <div className="actions">
        <button type="button" className="btn primary" onClick={() => session.navigate("find")}>
          選択条件を編集
        </button>
        <button
          type="button"
          className="btn ghost"
          onClick={() => update("pointCondition", null)}
          title="条件を外します。選択は空のままです。"
        >
          条件を解除
        </button>
      </div>
    </div>
  );
}

/* graph.output-preflight - refuse by name; existing artefacts stay untouched */
function PreflightDialog(props: { unresolved: SeriesDef[]; onClose: () => void }): ReactNode {
  const blockedNames = props.unresolved.map((s) => `「${s.label}」`).join("・");
  return (
    <div className="dialog-scrim" role="presentation">
      <div className="dialog" role="dialog" aria-modal="true" aria-label="グラフ出力前チェック">
        <header>
          <h2>グラフ出力前チェック（画像・PNG）</h2>
        </header>
        <div className="body gr-checks">
          <div className="notice error">
            <b>系列：未解決</b>
            <span className="why">{blockedNames}のY数量が未選択です。未解決のまま出力しません。</span>
          </div>
          <div className="notice warn">
            <b>単位：検証待ち</b>
            <span className="why">数量の選択後に、軸ごとの単位互換性を検証します。</span>
          </div>
          <div className="notice good">
            <b>ケース選択：解決済み</b>
            <span className="why">明示選択・5ケースすべてが解決しています。</span>
          </div>
          <div className="notice good">
            <b>保存先：output/graph/run-012/</b>
            <span className="why">新規実行フォルダーに書き込み、既存の成果物は変更しません。</span>
          </div>
          <p className="prop-note">
            未解決が残る間は開始できません。系列タブで数量を選ぶと、このチェックは自動で再評価されます。
          </p>
        </div>
        <footer>
          <button type="button" className="btn ghost" onClick={props.onClose}>
            閉じる
          </button>
          <button
            type="button"
            className="btn primary"
            {...disabledBecause(`${blockedNames}のY数量が未選択のため`)}
          >
            出力を開始
          </button>
        </footer>
      </div>
    </div>
  );
}

/* ---- rail ---------------------------------------------------------------------------------- */

const TAB_LABEL: Record<string, string> = {
  overall: "グラフ",
  series: "系列",
  axes: "軸",
  style: "スタイル",
  output: "出力",
};

export function GraphRail(props: { tab: string; variant: string }): ReactNode {
  const { tab, variant } = props;
  const series = seriesFor(variant);
  // The series and style tabs edit the same selection - one active series, held here so switching
  // tabs follows it (mockup 1's E-125 note: the panel follows the selected element).
  const [activeSeriesId, setActiveSeriesId] = useState<string | null>(null);

  if (variant === "empty") {
    return (
      <section className="prop-section">
        <h3>{TAB_LABEL[tab] ?? "プロパティ"}</h3>
        <p className="prop-note">
          このグラフはまだ作成されていません。中央の開始方法（手動・推奨・アシスタント提案）で作成すると、ここに設定が表示されます。
        </p>
      </section>
    );
  }

  const preferUnresolved = variant === "series-unresolved" || variant === "output-preflight";
  const fallback = preferUnresolved
    ? (series.find((s) => s.srcKind === "unresolved") ?? series[0])
    : series[0];
  const active = series.find((s) => s.id === activeSeriesId) ?? fallback;
  if (!active) return null;

  switch (tab) {
    case "overall":
      return <OverallTab variant={variant} />;
    case "series":
      return <SeriesTab series={series} active={active} onSelect={setActiveSeriesId} />;
    case "axes":
      return <AxesTab variant={variant} />;
    case "style":
      return <StyleTab series={series} active={active} onSelect={setActiveSeriesId} />;
    case "output":
      return <OutputTab variant={variant} series={series} />;
    default:
      return null;
  }
}

/* 全体 - name/title, drawn kind, and case selection: the graph's property, not a series' (XC-221) */
function OverallTab({ variant }: { variant: string }): ReactNode {
  const [kind, setKind] = useState("line");
  const noPoints = variant === "no-points";
  return (
    <div>
      <section className="prop-section">
        <h3>グラフ</h3>
        <Row label="名前">
          <input
            className="field-input"
            defaultValue="ケース横断 最大応力"
            aria-label="グラフ名"
            onChange={(event) => update("name", event.target.value)}
          />
        </Row>
        <Row label="表題">
          <input
            className="field-input"
            defaultValue="板厚と最大応力"
            aria-label="図の表題"
            onChange={(event) => update("title", event.target.value)}
          />
        </Row>
        <Row label="副題">
          <input
            className="field-input"
            placeholder="任意（書き出しに含まれます）"
            aria-label="図の副題"
            onChange={(event) => update("subtitle", event.target.value)}
          />
        </Row>
      </section>
      <section className="prop-section">
        <h3>種類</h3>
        {/* XC-215: the shape of a chart is the thing being chosen, so it is drawn. */}
        <div className="gr-samples" role="radiogroup" aria-label="グラフの種類">
          <SampleButton
            name="折れ線"
            selected={kind === "line"}
            onSelect={() => {
              setKind("line");
              update("kind", "line");
            }}
          >
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <polyline
                points="5,20 19,10 33,14 47,6 55,9"
                fill="none"
                stroke="var(--ink)"
                strokeWidth={1.5}
              />
              <circle cx={19} cy={10} r={2} fill="var(--ink-strong)" />
              <circle cx={47} cy={6} r={2} fill="var(--ink-strong)" />
            </svg>
          </SampleButton>
          <SampleButton
            name="散布図"
            selected={kind === "scatter"}
            onSelect={() => {
              setKind("scatter");
              update("kind", "scatter");
            }}
          >
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <circle cx={10} cy={18} r={2} fill="var(--ink)" />
              <circle cx={20} cy={9} r={2} fill="var(--ink)" />
              <circle cx={29} cy={14} r={2} fill="var(--ink)" />
              <circle cx={40} cy={6} r={2} fill="var(--ink)" />
              <circle cx={50} cy={11} r={2} fill="var(--ink)" />
            </svg>
          </SampleButton>
          <SampleButton
            name="棒"
            selected={kind === "bar"}
            onSelect={() => {
              setKind("bar");
              update("kind", "bar");
            }}
          >
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <rect x={8} y={12} width={8} height={11} fill="var(--ink-muted)" />
              <rect x={22} y={6} width={8} height={17} fill="var(--ink-muted)" />
              <rect x={36} y={15} width={8} height={8} fill="var(--ink-muted)" />
            </svg>
          </SampleButton>
        </div>
        <p className="prop-note">種類を変えても、数量の参照と単位の検証は維持されます。</p>
      </section>
      <section className="prop-section">
        <h3>ケース選択</h3>
        {/* XC-221: which cases the graph covers belongs to the graph - every series spans it. */}
        <Row label="対象">
          <select
            className="field-input"
            defaultValue="explicit"
            aria-label="ケース選択の対象"
            onChange={(event) => update("caseSelection", event.target.value)}
          >
            <option value="explicit">明示選択（このグラフが保持）</option>
            <option value="saved">保存済み選択</option>
            <option value="rule">宣言的な条件</option>
          </select>
        </Row>
        <Row label="解決結果">
          <input
            className="field-input"
            readOnly
            value={noPoints ? "0点（条件が空に解決）" : "Run 12・板厚スイープ・5ケース"}
            aria-label="ケース選択の解決結果"
          />
        </Row>
        {noPoints ? (
          <p className="prop-note">
            点の選択条件が空に解決しています。中央の表示が条件を名指ししています。
          </p>
        ) : null}
        <Row label="反復">
          <select
            className="field-input"
            defaultValue="separate"
            aria-label="反復の扱い"
            onChange={(event) => update("iterations", event.target.value)}
          >
            <option value="separate">反復ごとに表示</option>
            <option value="combined">反復を集約</option>
          </select>
        </Row>
      </section>
      <section className="prop-section">
        <h3>集約</h3>
        <Row label="方法">
          <select
            className="field-input"
            defaultValue="none"
            aria-label="集約方法"
            onChange={(event) => update("reduction", event.target.value)}
          >
            <option value="none">集約しない</option>
            <option value="weighted">関連量で重み付け</option>
            <option value="unweighted">単純平均（重みなし）</option>
          </select>
        </Row>
        <p className="prop-note">集約値は表示用形状ではなく、完全データから計算されます（INV-009）。</p>
      </section>
      <p className="prop-note gr-tabfoot">
        グラフは値のコピーではなく、数量・単位・来歴への参照として保存されます。
      </p>
    </div>
  );
}

/* 系列 - one row per series: what it plots; the look's first choice is the theme's sample (XC-221) */
function SeriesTab(props: {
  series: SeriesDef[];
  active: SeriesDef;
  onSelect: (id: string) => void;
}): ReactNode {
  const { series, active } = props;
  const unresolved = series.filter((s) => s.srcKind === "unresolved");
  return (
    <div>
      <section className="prop-section">
        <h3>系列</h3>
        <div className="gr-serieslist" role="listbox" aria-label="グラフの系列">
          {series.map((s) => (
            <button
              type="button"
              role="option"
              aria-selected={active.id === s.id}
              className="gr-series-row"
              key={s.id}
              title={s.quantityLong ?? s.label}
              onClick={() => props.onSelect(s.id)}
            >
              <SeriesSample line={s.line} marker={s.marker} stroke={s.stroke} />
              <span className="gr-srtext">
                <b>{s.label}</b>
                {s.srcKind === "unresolved" ? (
                  <small className="missing-value">数量未選択</small>
                ) : s.srcKind === "reference" ? (
                  <small>参考資料の値・235 MPa・資料</small>
                ) : (
                  <small>{`${s.quantityName ?? ""}・${s.unit ?? "単位未宣言"}・データ`}</small>
                )}
              </span>
              {s.srcKind === "unresolved" ? (
                <span className="gr-flag" aria-label="未解決">
                  ⚠
                </span>
              ) : null}
            </button>
          ))}
        </div>
        <div className="gr-listops">
          <button
            type="button"
            className="btn ghost"
            onClick={() => submit({ operation: "graph.update", parameters: { graph: GRAPH_ID, addSeries: true } })}
          >
            系列を追加
          </button>
          <button
            type="button"
            className="btn ghost"
            onClick={() => update("removeSeries", active.id)}
            title={`選択中の系列「${active.label}」を削除します`}
          >
            削除
          </button>
        </div>
      </section>
      {unresolved.length > 0 ? (
        <section className="prop-section">
          {/* XC-090: what did not resolve is named, and what is missing with it. */}
          <UnresolvedList
            title="未解決の系列"
            items={unresolved.map((s) => ({ what: s.label, missing: "Y数量の選択" }))}
          />
        </section>
      ) : null}
      <section className="prop-section">
        <h3>選択中：{active.label}</h3>
        <Row label="ラベル">
          <input
            className="field-input"
            defaultValue={active.label}
            key={active.id}
            aria-label="系列のラベル"
            onChange={(event) => update("seriesLabel", event.target.value)}
          />
        </Row>
        <Row label="X">
          <select
            className="field-input"
            defaultValue="parameter"
            aria-label="Xの参照元"
            onChange={(event) => update("xSource", event.target.value)}
          >
            <option value="parameter">パラメーター「板厚」</option>
            <option value="result-axis">結果軸（時間）</option>
            <option value="index">ケース番号</option>
          </select>
        </Row>
        <Row label="参照元">
          <select
            className="field-input"
            value={active.srcKind === "unresolved" ? "" : active.srcKind}
            aria-label="Yの参照元"
            onChange={(event) => update("ySource", event.target.value)}
          >
            {active.srcKind === "unresolved" ? <option value="">（未選択）</option> : null}
            <option value="dataset">データセットの数量</option>
            <option value="reference">参考資料の値</option>
            <option value="expression">計算・式</option>
            <option value="measurement">測定値</option>
          </select>
        </Row>
        {active.srcKind === "reference" ? (
          <>
            <Row label="値">
              <span className="gr-readout">
                <QuantityChip value="235" unit="MPa" title="設計ノートの記載値" />
                <ProvenanceBadge origin="reference" />
              </span>
            </Row>
            <p className="prop-note">出典：設計ノート。参考として描画し、数値根拠には使いません。</p>
          </>
        ) : (
          <Row label="数量">
            <FieldSelector
              fields={FIELDS}
              value={active.quantityName}
              onChange={(name) => update("quantity", name)}
            />
          </Row>
        )}
        <Row label="単位">
          {active.srcKind === "unresolved" ? (
            <span className="gr-pending">数量の選択後に確定（推測しません）</span>
          ) : (
            <span className="gr-readout">
              <UnitLabel unit={active.unit} />
            </span>
          )}
        </Row>
        <Row label="来歴">
          {active.provenance ? (
            <span className="gr-readout">
              <ProvenanceBadge origin={active.provenance} />
            </span>
          ) : (
            <span className="gr-pending">数量の選択後に表示</span>
          )}
        </Row>
        <Row label="使用する軸">
          <select
            className="field-input"
            value={active.axis}
            aria-label="この系列を描く軸"
            onChange={(event) => update("seriesAxis", event.target.value)}
          >
            <option value="y">Y（左）</option>
            <option value="y2">第2Y（右）</option>
          </select>
        </Row>
        <Row label="欠損">
          <select
            className="field-input"
            defaultValue="gap"
            aria-label="欠損値の方針"
            onChange={(event) => update("missingPolicy", event.target.value)}
          >
            <option value="gap">欠損として表示・凡例に残す</option>
            <option value="drop">系列を除外（凡例に明記）</option>
          </select>
        </Row>
        <Row label="見え方">
          <span className="gr-readout">
            <SeriesSample line={active.line} marker={active.marker} stroke={active.stroke} />
            <small>
              {active.themed
                ? "テーマの既定（第一選択）"
                : "この系列で上書き済み"}
              ・変更はスタイルタブ
            </small>
          </span>
        </Row>
        {active.srcKind === "unresolved" ? (
          <p className="prop-note">
            未選択のままでは描画されず、凡例に「データなし」として残ります。
          </p>
        ) : null}
      </section>
      <p className="prop-note gr-tabfoot">
        未選択・未宣言・欠損はそのまま表示し、ゼロや近傍値へ置き換えません。補間の選択肢は提供しません。
      </p>
    </div>
  );
}

/* 軸 - choose ONE axis to edit (XC-213); the unit comes from the series' declarations (XC-228) */
function AxesTab({ variant }: { variant: string }): ReactNode {
  const conflict = variant === "axis-unit-conflict";
  const [axis, setAxis] = useState<"x" | "y">("y");
  const [range, setRange] = useState<"auto" | "fixed">(variant === "axes" ? "fixed" : "auto");
  const axisNames = { x: "X（横）", y: "Y（左）" } as const;
  return (
    <div>
      <section className="prop-section">
        <h3>設定する軸</h3>
        {/* Which axis a series is DRAWN against is on the series; this picks the axis being EDITED. */}
        <div className="gr-axis-picker" role="tablist" aria-label="設定する軸">
          {(["x", "y"] as const).map((value) => (
            <button
              type="button"
              role="tab"
              aria-selected={axis === value}
              key={value}
              onClick={() => setAxis(value)}
            >
              {axisNames[value]}
            </button>
          ))}
          <button type="button" role="tab" aria-selected={false} {...disabledBecause("第2Y軸に置かれた系列がありません")}>
            第2Y（右）
          </button>
        </div>
      </section>
      <section className="prop-section">
        <h3>表題</h3>
        <Row label="表題">
          <input
            className="field-input"
            key={axis}
            defaultValue={axis === "x" ? "板厚" : conflict ? "値" : "応力"}
            aria-label={`${axisNames[axis]}の表題`}
            onChange={(event) => update(`axis.${axis}.title`, event.target.value)}
          />
        </Row>
        <Row label="単位の併記">
          {axis === "x" ? (
            <span className="gr-readout">
              <UnitLabel unit="mm" />
              <small>系列の宣言から</small>
            </span>
          ) : conflict ? (
            <span className="gr-readout">
              <span className="missing-value">単位混在</span>
              <small>単位は凡例に表示</small>
            </span>
          ) : (
            <span className="gr-readout">
              <UnitLabel unit="MPa" />
              <small>系列の宣言から・推測なし</small>
            </span>
          )}
        </Row>
        {axis === "y" && conflict ? (
          <div className="notice warn">
            <b>この軸の系列が異なる単位を宣言しています</b>
            <span className="why">
              「最大応力」は MPa、「最大たわみ」は mm
              です。軸にはどちらも書かず「単位混在」と表示します。系列タブで「最大たわみ」を第2Y軸へ移すと解消します。
            </span>
          </div>
        ) : null}
      </section>
      <section className="prop-section">
        <h3>範囲</h3>
        <Row label="範囲">
          <select
            className="field-input"
            value={range}
            aria-label="軸範囲の決め方"
            onChange={(event) => {
              const next = event.target.value === "fixed" ? "fixed" : "auto";
              setRange(next);
              update(`axis.${axis}.range`, next);
            }}
          >
            <option value="auto">自動（データに適合）</option>
            <option value="fixed">固定</option>
          </select>
        </Row>
        {range === "fixed" ? (
          <>
            <Row label="最小">
              <input
                className="field-input"
                defaultValue={axis === "x" ? "8" : "200"}
                inputMode="decimal"
                aria-label="範囲の最小値"
                onChange={(event) => update(`axis.${axis}.min`, event.target.value)}
              />
            </Row>
            <Row label="最大">
              <input
                className="field-input"
                defaultValue={axis === "x" ? "16" : "260"}
                inputMode="decimal"
                aria-label="範囲の最大値"
                onChange={(event) => update(`axis.${axis}.max`, event.target.value)}
              />
            </Row>
            {/* XC-001 applied to a picture: cutting data is allowed, and it is stated. */}
            <div className="notice warn">
              <b>固定範囲の外にある点は描かれません</b>
              <span className="why">
                範囲外の点があるとき、その旨を図とすべての書き出しに記載します。現在：範囲外
                1点（Run12-T16・198.2 MPa）。
              </span>
            </div>
          </>
        ) : null}
        <Row label="対数目盛">
          <input
            type="checkbox"
            aria-label="対数目盛"
            onChange={(event) => update(`axis.${axis}.log`, event.target.checked)}
          />
        </Row>
      </section>
      <section className="prop-section">
        <h3>目盛</h3>
        <Row label="間隔">
          <select
            className="field-input"
            defaultValue="auto"
            aria-label="目盛の間隔"
            onChange={(event) => update(`axis.${axis}.ticks`, event.target.value)}
          >
            <option value="auto">自動</option>
            <option value="custom">指定</option>
          </select>
        </Row>
        <Row label="表記">
          <select
            className="field-input"
            defaultValue="auto"
            aria-label="目盛の表記"
            onChange={(event) => update(`axis.${axis}.notation`, event.target.value)}
          >
            <option value="auto">自動</option>
            <option value="fixed">小数固定</option>
            <option value="scientific">指数</option>
          </select>
        </Row>
        <Row label="桁数">
          <select
            className="field-input"
            defaultValue="3"
            aria-label="目盛の桁数"
            onChange={(event) => update(`axis.${axis}.digits`, event.target.value)}
          >
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
          </select>
        </Row>
      </section>
      <section className="prop-section">
        <h3>グリッド</h3>
        <Row label="主グリッド">
          <input
            type="checkbox"
            defaultChecked
            aria-label="主グリッド"
            onChange={(event) => update(`axis.${axis}.grid`, event.target.checked)}
          />
        </Row>
        <Row label="副グリッド">
          <input
            type="checkbox"
            aria-label="副グリッド"
            onChange={(event) => update(`axis.${axis}.minorGrid`, event.target.checked)}
          />
        </Row>
      </section>
      <p className="prop-note gr-tabfoot">
        この設定は{axisNames[axis]}にだけ適用されます。単位は系列の宣言から取り、ここでは推測しません。
      </p>
    </div>
  );
}

/* スタイル - drawn samples with names under them (XC-215); series overrides per series (XC-226) */
function StyleTab(props: {
  series: SeriesDef[];
  active: SeriesDef;
  onSelect: (id: string) => void;
}): ReactNode {
  const { series, active } = props;
  const [palette, setPalette] = useState("shade");
  const [background, setBackground] = useState("light");
  const [lineOverride, setLineOverride] = useState<"theme" | LineKind>("theme");
  const [markerOverride, setMarkerOverride] = useState<"theme" | MarkerKind>("theme");
  const [font, setFont] = useState("deliverable");
  const fontStacks: Record<string, string> = {
    deliverable: "var(--family-deliverable)",
    ui: "var(--family-ui)",
    mono: "var(--family-mono)",
  };
  return (
    <div>
      <section className="prop-section">
        <h3>スタイル</h3>
        <Row label="適用中">
          <select
            className="field-input"
            defaultValue="technical"
            aria-label="適用中のスタイル資産"
            onChange={(event) => update("styleAsset", event.target.value)}
          >
            <option value="technical">技術文書（モノクロ）</option>
            <option value="presentation">発表資料</option>
          </select>
        </Row>
        <Row label="系列の既定">
          <span className="gr-readout">
            <SeriesSample line="solid" marker="circle" />
            <small>実線・円・2 px（テーマから）。上書きは下の「系列の外観」。</small>
          </span>
        </Row>
        <span className="gr-caption">配色</span>
        <div className="gr-samples" role="radiogroup" aria-label="配色">
          <SampleButton name="濃淡（グレー）" selected={palette === "shade"} onSelect={() => { setPalette("shade"); update("palette", "shade"); }}>
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <line x1={6} y1={7} x2={54} y2={7} stroke="var(--ink-strong)" strokeWidth={2} />
              <line x1={6} y1={13} x2={54} y2={13} stroke="var(--ink-muted)" strokeWidth={2} />
              <line x1={6} y1={19} x2={54} y2={19} stroke="var(--ink-faint)" strokeWidth={2} />
            </svg>
          </SampleButton>
          <SampleButton name="線種で区別" selected={palette === "linestyle"} onSelect={() => { setPalette("linestyle"); update("palette", "linestyle"); }}>
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <line x1={6} y1={7} x2={54} y2={7} stroke="var(--ink)" strokeWidth={1.5} />
              <line x1={6} y1={13} x2={54} y2={13} stroke="var(--ink)" strokeWidth={1.5} strokeDasharray="5 3" />
              <line x1={6} y1={19} x2={54} y2={19} stroke="var(--ink)" strokeWidth={1.5} strokeDasharray="1.5 3" />
            </svg>
          </SampleButton>
          <SampleButton name="白黒・印刷" selected={palette === "print"} onSelect={() => { setPalette("print"); update("palette", "print"); }}>
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <line x1={6} y1={9} x2={54} y2={9} stroke="var(--ink-strong)" strokeWidth={1} />
              <circle cx={18} cy={9} r={2.5} fill="var(--ink-strong)" />
              <line x1={6} y1={18} x2={54} y2={18} stroke="var(--ink-strong)" strokeWidth={1} />
              <rect x={38} y={15.5} width={5} height={5} fill="var(--ink-strong)" />
            </svg>
          </SampleButton>
        </div>
        <span className="gr-caption">背景</span>
        <div className="gr-samples" role="radiogroup" aria-label="図の背景">
          <SampleButton name="明るい" selected={background === "light"} onSelect={() => { setBackground("light"); update("background", "light"); }}>
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <rect x={4} y={3} width={52} height={20} fill="var(--ink-strong)" rx={2} />
            </svg>
          </SampleButton>
          <SampleButton name="透過" selected={background === "transparent"} onSelect={() => { setBackground("transparent"); update("background", "transparent"); }}>
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <rect x={4} y={3} width={52} height={20} fill="var(--surface-panel)" rx={2} />
              <rect x={4} y={3} width={13} height={10} fill="var(--surface-raise)" />
              <rect x={30} y={3} width={13} height={10} fill="var(--surface-raise)" />
              <rect x={17} y={13} width={13} height={10} fill="var(--surface-raise)" />
              <rect x={43} y={13} width={13} height={10} fill="var(--surface-raise)" />
            </svg>
          </SampleButton>
          <SampleButton name="暗い" selected={background === "dark"} onSelect={() => { setBackground("dark"); update("background", "dark"); }}>
            <svg viewBox="0 0 60 26" aria-hidden="true">
              <rect x={4} y={3} width={52} height={20} fill="var(--surface-well)" rx={2} />
            </svg>
          </SampleButton>
        </div>
        <p className="prop-note">図の背景は成果物の設定で、画面のテーマとは独立です。</p>
      </section>
      <section className="prop-section">
        <h3>系列の外観</h3>
        {/* XC-226: what a series IS stays in 系列; how it LOOKS is here - same selection. */}
        <div className="gr-serieslist" role="radiogroup" aria-label="外観を編集する系列">
          {series.map((s) => (
            <button
              type="button"
              role="radio"
              aria-checked={active.id === s.id}
              className="gr-series-row"
              key={s.id}
              onClick={() => props.onSelect(s.id)}
            >
              <SeriesSample line={s.line} marker={s.marker} stroke={s.stroke} />
              <span className="gr-srtext">
                <b>{s.label}</b>
              </span>
            </button>
          ))}
        </div>
        <span className="gr-caption">線</span>
        {/* XC-221: the first option is the theme's, drawn as the theme resolves it. */}
        <div className="gr-samples cols4" role="radiogroup" aria-label={`${active.label}の線`}>
          <SampleButton name="テーマ" title="テーマの既定（実線）に従う" selected={lineOverride === "theme"} onSelect={() => { setLineOverride("theme"); update("seriesLine", "theme"); }}>
            <SeriesSample line="solid" marker="none" />
          </SampleButton>
          <SampleButton name="破線" selected={lineOverride === "dashed"} onSelect={() => { setLineOverride("dashed"); update("seriesLine", "dashed"); }}>
            <SeriesSample line="dashed" marker="none" />
          </SampleButton>
          <SampleButton name="点線" selected={lineOverride === "dotted"} onSelect={() => { setLineOverride("dotted"); update("seriesLine", "dotted"); }}>
            <SeriesSample line="dotted" marker="none" />
          </SampleButton>
          <SampleButton name="なし" selected={lineOverride === "none"} onSelect={() => { setLineOverride("none"); update("seriesLine", "none"); }}>
            <SeriesSample line="none" marker="circle" />
          </SampleButton>
        </div>
        <span className="gr-caption">マーカー</span>
        <div className="gr-samples cols4" role="radiogroup" aria-label={`${active.label}のマーカー`}>
          <SampleButton name="テーマ" title="テーマの既定（円）に従う" selected={markerOverride === "theme"} onSelect={() => { setMarkerOverride("theme"); update("seriesMarker", "theme"); }}>
            <SeriesSample line="solid" marker="circle" />
          </SampleButton>
          <SampleButton name="四角" selected={markerOverride === "square"} onSelect={() => { setMarkerOverride("square"); update("seriesMarker", "square"); }}>
            <SeriesSample line="solid" marker="square" />
          </SampleButton>
          <SampleButton name="三角" selected={markerOverride === "triangle"} onSelect={() => { setMarkerOverride("triangle"); update("seriesMarker", "triangle"); }}>
            <SeriesSample line="solid" marker="triangle" />
          </SampleButton>
          <SampleButton name="なし" selected={markerOverride === "none"} onSelect={() => { setMarkerOverride("none"); update("seriesMarker", "none"); }}>
            <SeriesSample line="solid" marker="none" />
          </SampleButton>
        </div>
        <Row label="線幅">
          <select
            className="field-input"
            defaultValue="theme"
            aria-label={`${active.label}の線幅`}
            onChange={(event) => update("seriesWidth", event.target.value)}
          >
            <option value="theme">テーマに従う（2 px）</option>
            <option value="1">1 px</option>
            <option value="3">3 px</option>
            <option value="4">4 px</option>
          </select>
        </Row>
      </section>
      <section className="prop-section">
        <h3>書体</h3>
        <Row label="フォント">
          <select
            className="field-input"
            value={font}
            aria-label="図の書体"
            style={{ fontFamily: fontStacks[font] }}
            onChange={(event) => {
              setFont(event.target.value);
              update("font", event.target.value);
            }}
          >
            <option value="deliverable">本文書体（セリフ）</option>
            <option value="ui">UIと同じ（サンセリフ）</option>
            <option value="mono">等幅</option>
          </select>
        </Row>
        <Row label="見本">
          <span className="gr-specimen" style={{ fontFamily: fontStacks[font] }}>
            最大応力 241.7 MPa
          </span>
        </Row>
        <p className="prop-note">出力時に使用文字を検査し、必要な字体をライセンス条件に従って埋め込みます。</p>
      </section>
    </div>
  );
}

/* 出力 - preflight refuses unresolved series by name; existing artefacts are never touched */
function OutputTab(props: { variant: string; series: SeriesDef[] }): ReactNode {
  const unresolved = props.series.filter((s) => s.srcKind === "unresolved");
  const conflict = props.variant === "axis-unit-conflict";
  const blocked = unresolved.length > 0;
  const blockedNames = unresolved.map((s) => `「${s.label}」`).join("・");
  const [kind, setKind] = useState<"image" | "vector" | "data" | "animation">("image");
  return (
    <div>
      <section className="prop-section">
        <h3>成果物</h3>
        <Row label="種類">
          <select
            className="field-input"
            value={kind}
            aria-label="成果物の種類"
            onChange={(event) => {
              const next = event.target.value;
              if (next === "image" || next === "vector" || next === "data") setKind(next);
              update("outputKind", next);
            }}
          >
            <option value="image">画像</option>
            <option value="vector">ベクター</option>
            <option value="data">表データ</option>
            <option value="animation" disabled>
              動画（X軸が結果軸ではないため不可）
            </option>
          </select>
        </Row>
        {kind === "image" ? (
          <>
            <Row label="形式">
              <select className="field-input" defaultValue="png" aria-label="画像形式" onChange={(event) => update("format", event.target.value)}>
                <option value="png">PNG</option>
                <option value="tiff">TIFF</option>
              </select>
            </Row>
            <Row label="サイズ">
              <select className="field-input" defaultValue="1600" aria-label="画像サイズ" onChange={(event) => update("size", event.target.value)}>
                <option value="1600">1600 × 900</option>
                <option value="2400">2400 × 1350</option>
              </select>
            </Row>
          </>
        ) : null}
        {kind === "vector" ? (
          <Row label="形式">
            <select className="field-input" defaultValue="svg" aria-label="ベクター形式" onChange={(event) => update("format", event.target.value)}>
              <option value="svg">SVG</option>
              <option value="pdf">PDF</option>
            </select>
          </Row>
        ) : null}
        {kind === "data" ? (
          <>
            <Row label="形式">
              <select className="field-input" defaultValue="csv" aria-label="表データ形式" onChange={(event) => update("format", event.target.value)}>
                <option value="csv">CSV</option>
                <option value="xlsx">Excel</option>
              </select>
            </Row>
            <Row label="来歴列">
              <input type="checkbox" defaultChecked aria-label="来歴列を含める" onChange={(event) => update("provenanceColumns", event.target.checked)} />
            </Row>
            <p className="prop-note">値には単位列と来歴列が付きます。欠損は空欄ではなく「値なし」と理由で出ます。</p>
          </>
        ) : null}
        <p className="prop-note">動画は、結果軸をXにした系列があるときに選べるようになります。</p>
      </section>
      <section className="prop-section">
        <h3>保存先</h3>
        <Row label="パターン">
          <input className="field-input" readOnly value="output/graph/<run>/<case>/" aria-label="保存先パターン" />
        </Row>
        <Row label="既存出力">
          <input className="field-input" readOnly value="上書きしない（新規実行フォルダー）" aria-label="既存出力の扱い" />
        </Row>
      </section>
      <section className="prop-section">
        <h3>事前チェック</h3>
        <div className="gr-checks">
          {blocked ? (
            <div className="notice error">
              <b>系列：未解決</b>
              <span className="why">{blockedNames}のY数量が未選択です。未解決のまま出力しません。</span>
            </div>
          ) : (
            <div className="notice good">
              <b>系列：解決済み</b>
              <span className="why">{props.series.length}系列すべてに数量が選ばれています。</span>
            </div>
          )}
          {blocked ? (
            <div className="notice warn">
              <b>単位：検証待ち</b>
              <span className="why">数量の選択後に、軸ごとの単位互換性を検証します。</span>
            </div>
          ) : conflict ? (
            <div className="notice warn">
              <b>単位：軸で混在</b>
              <span className="why">
                図には「単位混在」、凡例に系列ごとの単位を記載して出力します。
              </span>
            </div>
          ) : (
            <div className="notice good">
              <b>単位：宣言済み</b>
              <span className="why">全系列 MPa・宣言済み。図と書き出しに併記します。</span>
            </div>
          )}
          <div className="notice good">
            <b>保存先：衝突なし</b>
            <span className="why">既存の成果物には書き込みません。</span>
          </div>
        </div>
      </section>
      <section className="prop-section gr-actions">
        <button
          type="button"
          className="btn ghost"
          onClick={() => submit({ operation: "graph.data", parameters: { graph: GRAPH_ID, preflight: true } })}
        >
          出力前チェック
        </button>
        {blocked ? (
          <button type="button" className="btn primary" {...disabledBecause(`${blockedNames}のY数量が未選択のため`)}>
            出力を開始
          </button>
        ) : (
          <button
            type="button"
            className="btn primary"
            onClick={() => submit({ operation: "graph.data", parameters: { graph: GRAPH_ID, artefact: kind } })}
          >
            出力を開始
          </button>
        )}
        {blocked ? (
          <p className="prop-note">
            {blockedNames}が未解決のため開始できません。系列タブで数量を選ぶと再評価されます。
          </p>
        ) : (
          <p className="prop-note">出力は画面と同じ定義から生成し、既存の成果物を変更しません。</p>
        )}
      </section>
    </div>
  );
}
