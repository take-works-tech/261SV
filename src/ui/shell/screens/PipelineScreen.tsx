/* Pipeline (automation) screen - mockup 2 design states (XC-256; composition follows mockup 1).
 *
 * The canvas is the ordered unit list, top to bottom, with bounded zones around loop and condition.
 * Every unit carries its accumulated target-case count (XC-099): the target set accumulates down
 * the list and is invisible unless it is computed and drawn on every unit, including the ones
 * inside a zone. A dry run previews cases, nesting, artefacts and skips and writes nothing
 * (AC-008). An output unit names the item it produces or the run is refused (XC-211). A
 * destructive unit runs only after its affected set is shown and accepted, once per run (XC-094).
 * While a run is live the workspace is view-only and cancel lands on a unit boundary
 * (pipeline/AC-040). All of it is a design catalogue: every action dispatches through submit()
 * and nothing here is evidence of implemented behaviour.
 */
import { Fragment } from "react";
import { ProgressAndCancel } from "../../shared/ProgressAndCancel";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { QuantityChip } from "../../shared/QuantityChip";
import { RunOutcomeTable, type Outcome } from "../../shared/RunOutcomeTable";
import { ScopeConfirmation } from "../../shared/ScopeConfirmation";
import { UnresolvedList } from "../../shared/UnresolvedList";
import { submit } from "../../client/operations";
import { session } from "../../state/session";
import { disabledBecause, formatBytes, formatValue } from "../../logic/format";
import "./pipeline.css";

/* ---- the one pipeline this catalogue shows -------------------------------------------------- */

type UnitKind =
  | "case" | "view" | "graph" | "report" | "table" | "export"
  | "tag" | "clear" | "loop" | "variable" | "formula" | "condition";

type UnitMeta = { label: string; detail: string; glyph: string; zone?: true; destructive?: true };

const UNIT_META: Record<UnitKind, UnitMeta> = {
  case: { label: "ケース", detail: "対象セットへケースを追加", glyph: "⧉" },
  view: { label: "ビュー", detail: "可視化を生成", glyph: "◻" },
  graph: { label: "グラフ", detail: "図を生成", glyph: "∿" },
  report: { label: "レポート", detail: "文書を生成", glyph: "≣" },
  table: { label: "テーブル", detail: "数表を生成", glyph: "▦" },
  export: { label: "出力", detail: "ファイルへ書き出し", glyph: "⇥" },
  tag: { label: "タグ", detail: "ケースへ明示的に付与", glyph: "⌗" },
  clear: { label: "クリア", detail: "対象データを解放", glyph: "⌫", destructive: true },
  loop: { label: "ループ", detail: "有限回の反復", glyph: "↻", zone: true },
  variable: { label: "変数", detail: "以降のユニットへ束縛", glyph: "≔" },
  formula: { label: "数式", detail: "単位付き式を評価", glyph: "∑" },
  condition: { label: "条件", detail: "式による分岐", glyph: "◇", zone: true },
};

type FlowUnit = {
  id: string;
  kind: UnitKind;
  title: string;
  detail: string;
  adds?: number;
  /** XC-211: which item an output unit produces, pinned by identifier and revision. */
  reference?: { item: string; identifier: string; revision: number; comparison?: boolean };
  children?: FlowUnit[];
};

const FLOW: FlowUnit[] = [
  { id: "u-case", kind: "case", title: "ケース選択", detail: "基準ケース・板厚変更・荷重変更を明示的に追加（＋3）", adds: 3 },
  { id: "u-var", kind: "variable", title: "変数・設計許容応力", detail: "以降のユニットと式から参照できる値を束縛" },
  {
    id: "u-loop", kind: "loop", title: "ループ・material_variant", detail: "値リスト3要素・有限反復",
    children: [
      { id: "u-view", kind: "view", title: "ビュー・比較図", detail: "比較図をケースごとに生成", reference: { item: "比較「ケース比較」", identifier: "cmp-0004", revision: 12, comparison: true } },
      { id: "u-graph", kind: "graph", title: "グラフ・応力履歴", detail: "図をケースごとに生成", reference: { item: "グラフ「応力履歴グラフ」", identifier: "gr-0003", revision: 7 } },
    ],
  },
  {
    id: "u-cond", kind: "condition", title: "条件・許容応力の超過", detail: "式：最大応力 > 設計許容応力",
    children: [
      { id: "u-report", kind: "report", title: "レポート・設計レビュー", detail: "条件成立のケースのみ文書を生成", reference: { item: "レポート「設計レビューレポート」", identifier: "rp-0002", revision: 4 } },
    ],
  },
  { id: "u-export", kind: "export", title: "出力・実行フォルダー", detail: "新しい実行フォルダーへ書き出し・上書きなし" },
  { id: "u-clear", kind: "clear", title: "クリア・データ解放", detail: "読み込み済み結果データを解放し対象セットを空にする" },
];

const FLAT: FlowUnit[] = FLOW.flatMap((unit) => [unit, ...(unit.children ?? [])]);
const FLAT_TITLES: string[] = FLAT.map((unit) => unit.title);

function unitById(id: string): FlowUnit | null {
  return FLAT.find((unit) => unit.id === id) ?? null;
}
function titleOf(id: string): string {
  return unitById(id)?.title ?? id;
}

/** XC-099: accumulate the target set down the list; a clear empties it after acting on it. */
type Annotated = { unit: FlowUnit; acts: number };
type FlowRow = Annotated & { children: Annotated[] };
function annotate(units: FlowUnit[]): FlowRow[] {
  let targets = 0;
  return units.map((unit) => {
    if (unit.kind === "case") targets += unit.adds ?? 0;
    const row: FlowRow = {
      unit,
      acts: targets,
      children: (unit.children ?? []).map((child) => ({ unit: child, acts: targets })),
    };
    if (unit.kind === "clear") targets = 0;
    return row;
  });
}

/* ---- illustrative run data (units, provenance and digits honoured - INV-014, XC-003) -------- */

const ALLOWABLE_SHOWN = "235.0"; // declared design allowable, MPa - digits as declared

const CASE_EVAL = [
  { kase: "基準ケース", maxMpa: 212.36, exceeds: false },
  { kase: "板厚変更", maxMpa: 248.09, exceeds: true },
  { kase: "荷重変更", maxMpa: 251.88, exceeds: true },
] as const;
const CASES: string[] = CASE_EVAL.map((row) => row.kase);

/** The value a condition evaluated to, with units - a refused unit without it reads the same as
 * one that was never reached. */
function evalNote(kase: string): string {
  const row = CASE_EVAL.find((entry) => entry.kase === kase);
  if (!row) return "評価値の記録がありません";
  const shown = formatValue(row.maxMpa, 4);
  return row.exceeds
    ? `評価値 true（最大応力 ${shown} MPa > 許容 ${ALLOWABLE_SHOWN} MPa）`
    : `評価値 false（最大応力 ${shown} MPa ≦ 許容 ${ALLOWABLE_SHOWN} MPa）`;
}

const RUN_FILES = [
  { name: "比較図_基準ケース.png", bytes: 1_912_832 },
  { name: "比較図_板厚変更.png", bytes: 1_876_411 },
  { name: "比較図_荷重変更.png", bytes: 1_903_552 },
  { name: "応力履歴_基準ケース.png", bytes: 244_120 },
  { name: "応力履歴_板厚変更.png", bytes: 251_004 },
  { name: "応力履歴_荷重変更.png", bytes: 248_733 },
  { name: "設計レビュー_板厚変更.html", bytes: 3_481_600 },
  { name: "設計レビュー_荷重変更.html", bytes: 3_512_320 },
] as const;
const FAILED_RUN_FILES = RUN_FILES.filter((file) => !file.name.includes("板厚変更"));

const CLEAR_BYTES = [1_503_238_554, 1_610_612_736, 1_557_135_360] as const;

/** Outcome of the completed run (history of default): the condition's evaluated value is recorded
 * on the condition, and the refused report says why it was not produced. */
function outcomeCompleted(unit: string, kase: string): { kind: Outcome; note?: string } {
  if (unit === titleOf("u-cond")) return { kind: "applied", note: evalNote(kase) };
  if (unit === titleOf("u-report") && kase === "基準ケース") {
    return { kind: "refused", note: "条件不成立のため生成しません" };
  }
  return { kind: "applied" };
}

/** Outcome of the failed run: the failure is named on unit × case, and only that case's dependent
 * units are skipped - the other cases continue. */
function outcomeFailed(unit: string, kase: string): { kind: Outcome; note?: string } {
  if (kase === "板厚変更") {
    const at = FLAT_TITLES.indexOf(unit);
    const graphAt = FLAT_TITLES.indexOf(titleOf("u-graph"));
    if (at === graphAt) return { kind: "failed", note: "参照した数量「応力履歴」がこのケースにありません" };
    if (at > graphAt) return { kind: "skipped", note: "先行ユニットの失敗によりこのケースのみ未実行" };
    return { kind: "applied" };
  }
  return outcomeCompleted(unit, kase);
}

/* ---- per-variant canvas state --------------------------------------------------------------- */

const SELECTED_UNIT: Record<string, string> = {
  default: "u-view",
  "dry-run": "u-cond",
  failed: "u-graph",
  running: "u-graph",
  "unit-reference": "u-report",
  "scope-confirmation": "u-clear",
};

const EDIT_LOCK_REASON = "実行中はパイプラインを編集できません（pipeline/AC-040）";

function unitStateBadge(variant: string, id: string) {
  if (variant === "failed") {
    if (id === "u-graph") return <span className="pi-badge err">失敗・板厚変更</span>;
    if (id === "u-report" || id === "u-export" || id === "u-clear") {
      return <span className="pi-badge warn">板厚変更をスキップ</span>;
    }
    return null;
  }
  if (variant === "running") {
    if (id === "u-case" || id === "u-var" || id === "u-view") return <span className="pi-badge good">完了</span>;
    if (id === "u-graph") {
      return (
        <span className="run-chip">
          <span className="spinner" aria-hidden />実行中・ケース2/3
        </span>
      );
    }
    if (id === "u-loop") {
      return (
        <span className="run-chip">
          <span className="spinner" aria-hidden />実行中
        </span>
      );
    }
    return <span className="pi-badge">待機</span>;
  }
  if (variant === "unit-reference") {
    if (id === "u-report") return <span className="pi-badge err">未解決・項目未選択</span>;
    if (id === "u-graph") return <span className="pi-badge warn">リビジョン消失</span>;
    return null;
  }
  if (variant === "scope-confirmation" && id === "u-clear") {
    return <span className="pi-badge warn">範囲確認が必要</span>;
  }
  return null;
}

function refLine(unit: FlowUnit, variant: string) {
  if (unit.id === "u-var") {
    return <span className="pi-ref">値 {ALLOWABLE_SHOWN} MPa・宣言 — 単位ごと束縛します</span>;
  }
  const ref = unit.reference;
  if (!ref) return null;
  if (variant === "unit-reference" && unit.id === "u-report") {
    return <span className="pi-ref pi-err">参照：未選択 — 解決するまで実行を拒否（XC-211）</span>;
  }
  if (variant === "unit-reference" && unit.id === "u-graph") {
    return (
      <span className="pi-ref pi-warn" title={`${ref.item}・${ref.identifier}・リビジョン${ref.revision}（固定）`}>
        参照：{ref.item}・リビジョン{ref.revision}（固定）— このリビジョンは存在しません
      </span>
    );
  }
  return (
    <span className="pi-ref" title={`${ref.item}・${ref.identifier}・リビジョン${ref.revision}（固定）`}>
      参照：{ref.item}・{ref.identifier}・リビジョン{ref.revision}（固定）{ref.comparison ? "・比較項目" : ""}
    </span>
  );
}

function UnitControls(props: { title: string; running: boolean }) {
  const lock = props.running ? disabledBecause(EDIT_LOCK_REASON) : null;
  const act = (action: string) => () =>
    submit({ operation: "pipeline.update", parameters: { pipeline: "pl-0001", unit: props.title, action } });
  return (
    <span className="pi-controls">
      <button type="button" aria-label={`${props.title}を上へ移動`} {...(lock ?? {})} title={lock?.title ?? "上へ移動"} onClick={act("move-up")}>▲</button>
      <button type="button" aria-label={`${props.title}を下へ移動`} {...(lock ?? {})} title={lock?.title ?? "下へ移動"} onClick={act("move-down")}>▼</button>
      <button type="button" aria-label={`${props.title}を削除`} {...(lock ?? {})} title={lock?.title ?? "削除（Undo可能）"} onClick={act("remove")}>✕</button>
    </span>
  );
}

function UnitRow(props: { unit: FlowUnit; acts: number; variant: string }) {
  const { unit, acts, variant } = props;
  const meta = UNIT_META[unit.kind];
  const selected = SELECTED_UNIT[variant] === unit.id;
  const failedHere = variant === "failed" && unit.id === "u-graph";
  const classes = [
    "pi-unit",
    selected ? "selected" : "",
    failedHere ? "failed" : "",
    meta.destructive ? "destructive" : "",
  ].filter(Boolean).join(" ");
  return (
    <div className={classes} role="listitem" aria-current={selected ? "true" : undefined}>
      <span className="pi-glyph" aria-hidden>{meta.glyph}</span>
      <span className="pi-main">
        <b title={unit.title}>{unit.title}</b>
        <small title={unit.detail}>{unit.detail}</small>
        {refLine(unit, variant)}
        {meta.destructive ? (
          <span className="pi-ref pi-warn">破壊的 — 実行前に範囲確認（XC-094）・承認は実行1回限り</span>
        ) : null}
      </span>
      <span className="pi-side">
        {unitStateBadge(variant, unit.id)}
        <span className="pi-count" title="このユニットが作用する累積対象ケース数">対象 {acts}ケース</span>
      </span>
      <UnitControls title={unit.title} running={variant === "running"} />
    </div>
  );
}

function ZoneRow(props: { row: FlowRow; variant: string }) {
  const { row, variant } = props;
  const meta = UNIT_META[row.unit.kind];
  const selected = SELECTED_UNIT[variant] === row.unit.id;
  return (
    <section
      className={selected ? "pi-zone selected" : "pi-zone"}
      role="listitem"
      aria-current={selected ? "true" : undefined}
      aria-label={`${row.unit.title}（境界付きゾーン）`}
    >
      <div className="pi-zone-head">
        <span className="pi-glyph" aria-hidden>{meta.glyph}</span>
        <span className="pi-main">
          <b title={row.unit.title}>{row.unit.title}</b>
          <small title={row.unit.detail}>{row.unit.detail}</small>
        </span>
        <span className="pi-side">
          {unitStateBadge(variant, row.unit.id)}
          <span className="pi-count" title="このユニットが作用する累積対象ケース数">対象 {row.acts}ケース</span>
        </span>
        <UnitControls title={row.unit.title} running={variant === "running"} />
      </div>
      <div className="pi-zone-children" role="list" aria-label={`${row.unit.title}の内側ユニット`}>
        {row.children.map((child) => (
          <UnitRow key={child.unit.id} unit={child.unit} acts={child.acts} variant={variant} />
        ))}
      </div>
      <p className="pi-zone-foot">
        {row.unit.kind === "loop"
          ? "ループ終端 — 反復ごとに内側を上から実行します"
          : "条件終端 — 不成立のケースは内側をスキップし、評価値を記録します"}
      </p>
    </section>
  );
}

/* ---- canvas --------------------------------------------------------------------------------- */

function FlowHeader(props: { variant: string }) {
  const { variant } = props;
  const running = variant === "running";
  const dryLock = running ? disabledBecause("実行中です — 中止はユニット境界で反映されます") : null;
  const runLock = running
    ? disabledBecause("実行中です")
    : variant === "unit-reference"
      ? disabledBecause("未解決の参照が2件あります（XC-211）— 解決するまで実行しません")
      : null;
  return (
    <header className="pi-header">
      <div className="pi-title">
        <span className="pi-eyebrow">パイプライン</span>
        <b>全ケース書き出し</b>
        <small>上から順に実行 — 対象セットは下へ累積し、各ユニットの「対象」に表示します</small>
      </div>
      <div className="pi-actions">
        <button
          className="btn"
          {...(dryLock ?? {})}
          title={dryLock?.title ?? "実行せずに対象と生成物を確認します — 書込なし（AC-008）"}
          onClick={() => {
            submit({ operation: "pipeline.dryRun", parameters: { pipeline: "pl-0001" } });
            session.navigate("pipeline", "dry-run");
          }}
        >
          ドライラン
        </button>
        <button
          className="btn primary"
          {...(runLock ?? {})}
          title={runLock?.title ?? "クリアユニットの影響範囲を確認してから実行します（XC-094）"}
          onClick={() => session.navigate("pipeline", "scope-confirmation")}
        >
          実行
        </button>
      </div>
    </header>
  );
}

function Banner(props: { variant: string }) {
  const { variant } = props;
  if (variant === "running") {
    return (
      <>
        <ProgressAndCancel
          label="パイプライン実行中"
          detail="run-2026-08-29_01 — ユニット5/9・ケース2/3（板厚変更）"
          fraction={0.5}
          onCancel={() => submit({ operation: "pipeline.cancel", parameters: { run: "run-2026-08-29_01" } })}
          cancelNote="中止はユニット境界で反映されます — 処理中のユニットは完了まで実行されます"
        />
        <p className="notice warn pi-note" role="status">
          <b>編集はロック中です</b>
          <span className="why">実行の対象が途中で変わらないよう、実行中はこのワークスペースを編集できません（pipeline/AC-040）。閲覧は可能です。</span>
        </p>
      </>
    );
  }
  if (variant === "failed") {
    return (
      <p className="notice error pi-note" role="alert">
        <b>1ケースが失敗しました — グラフ・応力履歴 ×「板厚変更」</b>
        <span className="why">参照した数量「応力履歴」がこのケースにありません。近傍の数量では代用せず、このケースの後続ユニットだけをスキップしました。他2ケースは完了しています。失敗は通知履歴にも残ります。</span>
      </p>
    );
  }
  if (variant === "dry-run") {
    return (
      <p className="notice pi-note" role="status">
        <b>ドライラン結果 — 何も書き込んでいません（AC-008）</b>
        <span className="why">3ケース × ユニット9件：生成予定 8件・スキップ 1件・ファイル書込 0件。累積対象数は各ユニットの「対象」に、入れ子と生成物は下の表に表示します。</span>
      </p>
    );
  }
  if (variant === "unit-reference") {
    return (
      <UnresolvedList
        title="未解決の参照 — 解決するまで実行しません"
        items={[
          { what: "レポートユニット「レポート・設計レビュー」", missing: "作成する項目が未選択です（XC-211）。既定の項目では代用しません" },
          { what: "グラフユニット「グラフ・応力履歴」", missing: "固定したリビジョン7がワークスペースにありません。新しいリビジョン9へ自動では進みません" },
        ]}
      />
    );
  }
  return null;
}

function DryRunTable() {
  return (
    <section className="pi-run-record" aria-label="ドライラン・プレビュー">
      <h3 className="pi-record-title">プレビュー — ケース・入れ子・生成物・スキップ</h3>
      <div className="table-scroll">
        <table className="value-table pi-drytable">
          <thead>
            <tr>
              <th scope="col">ユニット</th>
              <th scope="col">ケース</th>
              <th scope="col">生成物（予定）</th>
              <th scope="col">動作</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{titleOf("u-case")}</td>
              <td>基準ケース・板厚変更・荷重変更</td>
              <td><span className="pi-nest">生成物なし</span></td>
              <td>対象セットへ追加（累積3ケース）</td>
            </tr>
            <tr>
              <td>{titleOf("u-var")}</td>
              <td>全3ケース</td>
              <td><span className="pi-nest">生成物なし</span></td>
              <td>{ALLOWABLE_SHOWN} MPa（宣言）を束縛</td>
            </tr>
            <tr>
              <td>{titleOf("u-loop")}</td>
              <td>全3ケース</td>
              <td><span className="pi-nest">生成物なし</span></td>
              <td>3反復 — 内側を各ケースで実行</td>
            </tr>
            {CASE_EVAL.map((row) => (
              <tr key={`view-${row.kase}`}>
                <td>{titleOf("u-view")}<span className="pi-nest">ループ内・material_variant</span></td>
                <td>{row.kase}</td>
                <td><span className="pi-mono">比較図_{row.kase}.png</span></td>
                <td>生成</td>
              </tr>
            ))}
            {CASE_EVAL.map((row) => (
              <tr key={`graph-${row.kase}`}>
                <td>{titleOf("u-graph")}<span className="pi-nest">ループ内・material_variant</span></td>
                <td>{row.kase}</td>
                <td><span className="pi-mono">応力履歴_{row.kase}.png</span></td>
                <td>生成</td>
              </tr>
            ))}
            <tr>
              <td>{titleOf("u-cond")}</td>
              <td>全3ケース</td>
              <td><span className="pi-nest">生成物なし</span></td>
              <td>ケースごとに評価 — 評価値は下の各行</td>
            </tr>
            {CASE_EVAL.map((row) => (
              <tr key={`report-${row.kase}`}>
                <td>{titleOf("u-report")}<span className="pi-nest">条件内・許容応力の超過</span></td>
                <td>{row.kase}</td>
                <td>
                  {row.exceeds
                    ? <span className="pi-mono">設計レビュー_{row.kase}.html</span>
                    : <span className="pi-nest">生成物なし</span>}
                </td>
                <td>
                  {row.exceeds
                    ? <>生成 — {evalNote(row.kase)}</>
                    : <span className="pi-warn">スキップ — {evalNote(row.kase)}</span>}
                </td>
              </tr>
            ))}
            <tr>
              <td>{titleOf("u-export")}</td>
              <td>全3ケース</td>
              <td>実行フォルダー「run-2026-08-29_01」へ 8ファイル</td>
              <td>計画のみ・書込なし（AC-008）</td>
            </tr>
            <tr>
              <td>{titleOf("u-clear")}</td>
              <td>全3ケース</td>
              <td><span className="pi-nest">生成物なし</span></td>
              <td>実行時のみ・範囲確認が必要（XC-094）— ドライランでは解放しません</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="prop-note">ドライランは何も書き込まず、クリアユニットの解放も行いません。同じ累積対象数が実行前確認にも表示されます。</p>
    </section>
  );
}

function FailedRunTable() {
  return (
    <section className="pi-run-record" aria-label="実行結果">
      <h3 className="pi-record-title">実行結果 — run-2026-08-28_01（ケース × ユニット）</h3>
      <RunOutcomeTable units={FLAT_TITLES} cases={CASES} outcome={outcomeFailed} />
      <p className="prop-note">「板厚変更」の生成物は書き込んでいません。拒否には条件の評価値を併記します。</p>
    </section>
  );
}

function EmptyPipeline() {
  return (
    <div className="empty-state">
      <h2>パイプラインが空です</h2>
      <p>
        右のパレット（ユニットタブ）から処理ユニットを追加します。実行の前にドライランが対象ケース・入れ子・生成物を表示し、ファイルは書き込みません（AC-008）。
      </p>
      <div className="actions">
        <button
          className="btn primary"
          onClick={() => submit({ operation: "pipeline.update", parameters: { pipeline: "pl-0001", add: "case" } })}
        >
          ＋ ケースユニットを追加
        </button>
        <button className="btn ghost" {...disabledBecause("ユニットがないためドライランを実行できません")}>
          ドライラン
        </button>
      </div>
      <p className="prop-note">最初のユニットは通常ケースユニットです — 対象セットへケースを明示的に追加します。</p>
    </div>
  );
}

export function PipelineScreen(props: { variant: string }) {
  const { variant } = props;
  if (variant === "empty") return <EmptyPipeline />;
  const rows = annotate(FLOW);
  const running = variant === "running";
  const insertLock = running ? disabledBecause(EDIT_LOCK_REASON) : null;
  return (
    <div className="pi-canvas">
      <div className="pi-flow">
        <Banner variant={variant} />
        <FlowHeader variant={variant} />
        {variant === "default" ? (
          <p className="notice pi-note" role="note">
            <b>クリアユニットは範囲確認まで実行できません</b>
            <span className="why">実行を押すと影響する対象セット（3ケース）を確認します（XC-094）。同じ数はドライランでも確認できます。</span>
          </p>
        ) : null}
        <div className="pi-units" role="list" aria-label="パイプラインのユニット（上から順に実行）">
          <div className="pi-boundary"><b>開始</b><span>対象セット 0ケース</span></div>
          {rows.map((row) => (
            <Fragment key={row.unit.id}>
              <div className="pi-link" aria-hidden />
              {UNIT_META[row.unit.kind].zone
                ? <ZoneRow row={row} variant={variant} />
                : <UnitRow unit={row.unit} acts={row.acts} variant={variant} />}
            </Fragment>
          ))}
          <div className="pi-link" aria-hidden />
          <button
            className="pi-insert"
            type="button"
            {...(insertLock ?? {})}
            title={insertLock?.title ?? "右のパレットで種類を選び、ここに追加します"}
            onClick={() => submit({ operation: "pipeline.update", parameters: { pipeline: "pl-0001", insert: "end" } })}
          >
            ＋ ユニットをここに追加（右のパレットから選択）
          </button>
          <div className="pi-link" aria-hidden />
          <div className="pi-boundary"><b>完了</b><span>生成物を実行記録へ — クリア後の対象セット 0ケース</span></div>
        </div>
        {variant === "dry-run" ? <DryRunTable /> : null}
        {variant === "failed" ? <FailedRunTable /> : null}
      </div>
      {variant === "scope-confirmation" ? (
        <ScopeConfirmation
          operation="クリアユニット「クリア・データ解放」の実行"
          affected={CASE_EVAL.map((row, index) =>
            `${row.kase} — 読み込み済み結果データ ${formatBytes(CLEAR_BYTES[index] ?? 0)} を解放（書込済みファイルは削除しません）`,
          )}
          onAccept={() => {
            submit({ operation: "pipeline.run", parameters: { pipeline: "pl-0001", authorised: ["u-clear"] } });
            session.navigate("pipeline", "running");
          }}
          onCancel={() => session.navigate("pipeline", "default")}
        />
      ) : null}
    </div>
  );
}

/* ---- rail: unit palette / settings / history ------------------------------------------------ */

const PALETTE_ORDER: UnitKind[] = [
  "case", "view", "graph", "report", "table", "export",
  "tag", "clear", "loop", "variable", "formula", "condition",
];

function RailUnitPalette(props: { variant: string }) {
  const locked = props.variant === "running";
  const lock = locked ? disabledBecause(EDIT_LOCK_REASON) : null;
  return (
    <div className="prop-section">
      <h3>ユニットを追加</h3>
      {props.variant === "empty" ? (
        <p className="prop-note" style={{ margin: "0 0 8px" }}>
          ここから開始します。追加したら、実行の前にドライランで対象ケースと生成物を確認します（AC-008）。
        </p>
      ) : null}
      <div className="pi-palette" role="list" aria-label="ユニットパレット">
        {PALETTE_ORDER.map((kind) => {
          const meta = UNIT_META[kind];
          return (
            <button
              key={kind}
              type="button"
              role="listitem"
              {...(lock ?? {})}
              title={lock?.title ?? `${meta.label}ユニットを末尾に追加（Undo可能）`}
              onClick={() => submit({ operation: "pipeline.update", parameters: { pipeline: "pl-0001", add: kind } })}
            >
              <span className="pi-glyph" aria-hidden>{meta.glyph}</span>
              <span className="pi-main"><b>{meta.label}</b><small title={meta.detail}>{meta.detail}</small></span>
              {meta.zone
                ? <span className="pi-tag">境界付き</span>
                : meta.destructive
                  ? <span className="pi-tag warn">破壊的</span>
                  : <span className="pi-tag">追加</span>}
            </button>
          );
        })}
      </div>
      <p className="prop-note">挿入位置は中央のリストへのドラッグでも指定できます。追加は1操作＝Undo1段階です。</p>
      {locked ? <p className="prop-note">実行中のため追加できません。中止はユニット境界で反映されます。</p> : null}
    </div>
  );
}

const REFERENCE_CHOICES: Record<string, string[]> = {
  view: ["比較「ケース比較」", "ビュー「標準ビュー」", "ビュー「最大応力・等角」"],
  graph: ["グラフ「応力履歴グラフ」", "グラフ「ケース間比較」"],
  report: ["レポート「設計レビューレポート」", "レポート「週次まとめ」"],
};

function RailSettings(props: { variant: string }) {
  const { variant } = props;
  const locked = variant === "running";
  const lock = locked ? disabledBecause(EDIT_LOCK_REASON) : null;
  const selectedId = SELECTED_UNIT[variant];
  const unit = selectedId !== undefined ? unitById(selectedId) : null;

  if (!unit) {
    return (
      <div className="prop-section">
        <h3>設定</h3>
        <p className="prop-note" style={{ marginTop: 0 }}>ユニットが選択されていません。中央のパイプラインでユニットを選ぶと、その条件をここで編集します。</p>
        {variant === "empty" ? (
          <p className="prop-note">パイプラインが空です。ユニットタブから最初のユニットを追加します。</p>
        ) : null}
      </div>
    );
  }

  const meta = UNIT_META[unit.kind];
  const ref = unit.reference;
  const refUnselected = variant === "unit-reference" && unit.id === "u-report";
  const update = (field: string) => () =>
    submit({ operation: "pipeline.update", parameters: { pipeline: "pl-0001", unit: unit.id, field } });

  return (
    <>
      <div className="prop-section">
        <h3>選択中のユニット</h3>
        <div className="pi-selected-unit">
          <span className="pi-glyph" aria-hidden>{meta.glyph}</span>
          <span className="pi-main"><b title={unit.title}>{unit.title}</b><small>{meta.label}ユニット</small></span>
        </div>
        {locked ? (
          <p className="notice warn pi-note" role="status" style={{ marginTop: 8 }}>
            <b>実行中は編集できません</b>
            <span className="why">実行の対象が途中で変わらないためです（pipeline/AC-040）。閲覧は可能です。</span>
          </p>
        ) : null}
      </div>

      <div className="prop-section">
        <h3>定義</h3>
        <div className="prop-row">
          <label htmlFor="pi-unit-name">名前</label>
          <input id="pi-unit-name" className="field-input" defaultValue={unit.title} {...(lock ?? {})} onChange={update("title")} />
        </div>
        <div className="prop-row">
          <label htmlFor="pi-unit-kind">種類</label>
          <input id="pi-unit-kind" className="field-input" value={`${meta.label}ユニット`} readOnly title="種類は変更できません — 削除して追加し直します" />
        </div>
        {unit.kind === "case" ? (
          <div className="prop-row">
            <label htmlFor="pi-unit-adds">追加ケース数</label>
            <input id="pi-unit-adds" className="field-input" type="number" min={0} max={9} defaultValue={unit.adds ?? 0} {...(lock ?? {})} onChange={update("adds")} />
          </div>
        ) : null}
      </div>

      {ref ? (
        <div className="prop-section">
          <h3>参照（識別子・リビジョンで固定）</h3>
          <div className="prop-row">
            <label htmlFor="pi-ref-item">項目</label>
            <select
              id="pi-ref-item"
              className="field-input"
              defaultValue={refUnselected ? "" : ref.item}
              {...(lock ?? {})}
              onChange={update("reference")}
            >
              <option value="">選択してください</option>
              {(REFERENCE_CHOICES[unit.kind] ?? []).map((choice) => (
                <option key={choice} value={choice}>{choice}</option>
              ))}
            </select>
          </div>
          <div className="prop-row">
            <label>識別子</label>
            {refUnselected
              ? <span className="missing-value">未定（項目未選択）</span>
              : <span className="pi-mono">{ref.identifier}</span>}
          </div>
          <div className="prop-row">
            <label>リビジョン</label>
            {refUnselected
              ? <span className="missing-value">未定（項目未選択）</span>
              : <span>{ref.revision}（固定）</span>}
          </div>
          {refUnselected ? (
            <p className="notice warn pi-note" role="status" style={{ marginTop: 8 }}>
              <b>参照する項目が未選択です</b>
              <span className="why">どの項目を作るかが決まるまで、このユニットは実行できません（XC-211）。既定の項目では代用しません。</span>
            </p>
          ) : (
            <p className="prop-note">参照先が更新されても、固定したリビジョンは自動では進みません。</p>
          )}
          {ref.comparison && !refUnselected ? (
            <p className="prop-note">この参照は比較項目です。ケースごとに同じ軸・同じカラーマップで並置図を生成します。</p>
          ) : null}
          {variant === "failed" && unit.id === "u-graph" ? (
            <p className="notice error pi-note" role="status" style={{ marginTop: 8 }}>
              <b>直近の実行：「板厚変更」で失敗</b>
              <span className="why">参照した数量「応力履歴」がこのケースにありません。近傍の数量では代用しません。</span>
            </p>
          ) : null}
        </div>
      ) : null}

      {variant === "unit-reference" ? (
        <div className="prop-section">
          <h3>参照の解決状態（出力ユニット）</h3>
          <div className="pi-refstates">
            <p className="notice good pi-note">
              <b>ビュー・比較図</b>
              <span className="why">比較「ケース比較」・cmp-0004・リビジョン12（固定）— 解決済み</span>
            </p>
            <p className="notice warn pi-note">
              <b>グラフ・応力履歴</b>
              <span className="why">gr-0003・リビジョン7（固定）— ワークスペースに存在しません。最新はリビジョン9ですが、自動では進みません。</span>
            </p>
            <p className="notice error pi-note">
              <b>レポート・設計レビュー</b>
              <span className="why">項目未選択 — 解決するまで実行を拒否します（XC-211）。</span>
            </p>
          </div>
        </div>
      ) : null}

      {unit.kind === "condition" ? (
        <div className="prop-section">
          <h3>条件式</h3>
          <div className="prop-row">
            <label htmlFor="pi-expr">式</label>
            <input id="pi-expr" className="field-input" defaultValue="最大応力 > 設計許容応力" {...(lock ?? {})} onChange={update("expression")} />
          </div>
          <p className="prop-note">単位付きで評価します。両辺の単位が合わない式は評価前に拒否します。</p>
          <div className="prop-row">
            <label>右辺の現在値</label>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <QuantityChip value={ALLOWABLE_SHOWN} unit="MPa" />
              <ProvenanceBadge origin="declared" />
            </span>
          </div>
          <p className="prop-note">評価値はケースごとにドライラン結果と実行記録へ残ります。</p>
        </div>
      ) : null}

      {meta.destructive ? (
        <div className="prop-section">
          <h3>破壊的ユニット</h3>
          <p className="notice warn pi-note" role="status" style={{ marginTop: 0 }}>
            <b>実行前に影響範囲の確認が必要です（XC-094）</b>
            <span className="why">承認はこの実行1回に限られ、単一キーのショートカットはありません。</span>
          </p>
          <p className="prop-note">
            影響の見積り：対象3ケース・読み込み済みデータ {formatBytes(CLEAR_BYTES.reduce((sum, bytes) => sum + bytes, 0))}（ドライランと同じ数）。書込済みファイルは削除しません。
          </p>
        </div>
      ) : null}

      <div className="prop-section">
        <h3>実行条件</h3>
        <label className="pi-check">
          <input type="checkbox" defaultChecked {...(lock ?? {})} onChange={update("continue-on-failure")} />
          失敗時も他ケースを続行
        </label>
        {variant === "failed" ? (
          <p className="prop-note">直近の実行では「板厚変更」の失敗後も他ケースを継続しました。失敗したケースの後続ユニットのみスキップします。</p>
        ) : null}
      </div>
    </>
  );
}

function RailFiles(props: { title: string; note: string; files: readonly { name: string; bytes: number }[] }) {
  return (
    <div className="prop-section">
      <h3>{props.title}</h3>
      <p className="prop-note" style={{ marginTop: 0 }}>{props.note}</p>
      <ul className="pi-files">
        {props.files.map((file) => (
          <li key={file.name}>
            <span className="name" title={file.name}>{file.name}</span>
            <span className="size">{formatBytes(file.bytes)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RailHistory(props: { variant: string }) {
  const { variant } = props;
  if (variant === "failed") {
    return (
      <>
        <div className="prop-section">
          <h3>直近の実行</h3>
          <p className="notice error pi-note" role="status" style={{ marginTop: 0 }}>
            <b>run-2026-08-28_01 — 1ケース失敗</b>
            <span className="why">グラフ・応力履歴が「板厚変更」で失敗。このケースの後続ユニットのみスキップし、他2ケースは完了しました。</span>
          </p>
          <RunOutcomeTable units={FLAT_TITLES} cases={CASES} outcome={outcomeFailed} />
        </div>
        <RailFiles
          title="書き込んだファイル"
          note={`実行フォルダー run-2026-08-28_01 — 上書きなし・${FAILED_RUN_FILES.length}件・合計 ${formatBytes(FAILED_RUN_FILES.reduce((sum, file) => sum + file.bytes, 0))}`}
          files={FAILED_RUN_FILES}
        />
        <div className="prop-section">
          <p className="prop-note" style={{ marginTop: 0 }}>失敗したケースの生成物は書き込みません。書込済みの生成物は実行記録から削除できます。</p>
        </div>
      </>
    );
  }
  if (variant === "running") {
    return (
      <>
        <div className="prop-section">
          <h3>実行中</h3>
          <ProgressAndCancel
            label="run-2026-08-29_01"
            detail="ユニット5/9・ケース2/3（板厚変更）"
            fraction={0.5}
            onCancel={() => submit({ operation: "pipeline.cancel", parameters: { run: "run-2026-08-29_01" } })}
            cancelNote="中止はユニット境界で反映されます"
          />
          <p className="prop-note">中止した場合、どのユニットの前で停止したかを実行記録に残します。</p>
        </div>
        <RailFiles
          title="書き込み済みのファイル"
          note="実行中のため増えます — 上書きなし"
          files={RUN_FILES.slice(0, 3)}
        />
      </>
    );
  }
  if (variant === "default" || variant === "scope-confirmation") {
    return (
      <>
        <div className="prop-section">
          <h3>直近の実行</h3>
          <p className="prop-note" style={{ marginTop: 0 }}>
            run-2026-08-27_02 — 完了・3ケース・失敗なし。レポートは条件成立の2ケースのみ生成しました。
          </p>
          <RunOutcomeTable units={FLAT_TITLES} cases={CASES} outcome={outcomeCompleted} />
        </div>
        <RailFiles
          title="書き込んだファイル"
          note={`実行フォルダー run-2026-08-27_02 — 上書きなし・${RUN_FILES.length}件・合計 ${formatBytes(RUN_FILES.reduce((sum, file) => sum + file.bytes, 0))}`}
          files={RUN_FILES}
        />
      </>
    );
  }
  return (
    <div className="prop-section">
      <h3>実行履歴</h3>
      <p className="prop-note" style={{ marginTop: 0 }}>
        実行履歴はありません。ドライランはファイルを書き込まないため、ここには残りません（AC-008）。
      </p>
    </div>
  );
}

export function PipelineRail(props: { tab: string; variant: string }) {
  if (props.tab === "unit") return <RailUnitPalette variant={props.variant} />;
  if (props.tab === "settings") return <RailSettings variant={props.variant} />;
  if (props.tab === "history") return <RailHistory variant={props.variant} />;
  return (
    <p className="prop-note" style={{ padding: 10 }}>
      タブ「{props.tab}」の内容は定義されていません。
    </p>
  );
}
