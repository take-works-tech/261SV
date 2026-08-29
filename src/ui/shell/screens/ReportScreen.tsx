/* Report screen (mockup 2): the canvas is the recipient's document as pages (GL-013), the rail is
 * the tool that assembles it. Eight design states from catalog.ts:
 *
 *   default          - the document: view still, value table, prose, and the mandatory trust
 *                      appendix (来歴・宣言単位・制約・製品版) visible and not removable (AC-007, AC-031)
 *   blank            - bundled templates and the deliberate empty document
 *   drafting         - mechanical summary vs generated commentary; the sequence
 *                      未作成 → 確認待ち → 取り込み済み is an order, not settings (XC-214);
 *                      an unset model blocks the generated path and says why
 *   commentary-review- direction, depth, model, payload and cost fixed BEFORE generation (XC-104)
 *   theme            - page, palette and type as ONE theme; typefaces shown in themselves (XC-215)
 *   exporting        - cancellable progress; no second export to the same target (XC-060)
 *   export-error     - format and reason named; the previous artefact untouched
 *   output-preflight - required info / fonts / substitutions / unresolved / destination, one check
 *
 * Numbers are illustrative (OPEN-022) but honest: digits via formatValue (INV-014), units declared
 * or marked undeclared (XC-003), provenance beside the value (INV-013), absence stated (XC-001).
 */
import { useState, type ReactNode } from "react";
import { session, useSession } from "../../state/session";
import { submit } from "../../client/operations";
import { formatValue, formatBytes, disabledBecause } from "../../logic/format";
import { QuantityChip } from "../../shared/QuantityChip";
import { UnitLabel } from "../../shared/UnitLabel";
import { NumberCell } from "../../shared/NumberCell";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { ProgressAndCancel } from "../../shared/ProgressAndCancel";
import { UnresolvedList } from "../../shared/UnresolvedList";
import "./ReportScreen.css";

/* ---- the illustrative values, formatted once so every surface carries the same digits -------- */

const V = {
  unavg: formatValue(214.62, 4),
  avg: formatValue(187.31, 4),
  spread: formatValue(12.4, 3),
  disp: formatValue(0.82143, 4),
  reaction: formatValue(12.468, 4),
  temp: formatValue(342.08, 4),
} as const;

const PPTX_SIZE = formatBytes(4404019);
const EXPORT_TARGET = "output/report/run-012/";

type DraftStatement = { text: string; kind: string; source: string };

/* XC-104: a drafted sentence enters the report only after its kind and source have been seen. */
const DRAFT_STATEMENTS: DraftStatement[] = [
  {
    text: `最大ミーゼス応力（非平均）は ${V.unavg} MPa で、ケース C-012 の隅部 R2 の要素に生じる。`,
    kind: "数値の引用",
    source: "Run 12・応力場統計",
  },
  {
    text: `節点平均での最大は ${V.avg} MPa で、平均幅 ±${V.spread} MPa を伴う。`,
    kind: "数値の引用",
    source: "Run 12・応力場統計（INV-033）",
  },
  {
    text: `最大変位は ${V.disp} mm、反力合計は ${V.reaction} kN で荷重入力と釣り合う。`,
    kind: "数値の引用",
    source: "Run 12・変位場・反力集計",
  },
  {
    text: "温度は単位が未宣言のため、換算と他ケースとの比較は行っていない。",
    kind: "注意",
    source: "フィールド一覧・XC-003",
  },
];

const DRAFT_EXCLUDED = [
  { what: "疲労安全率についての文", missing: "値（ケース C-014 に結果なし）。欠損のまま示し、文は作らない（XC-001）" },
  { what: "Run 11 との比較文", missing: "参照（Run 11 のワークスペースが閉じられている）。参照は保持され、脱落しない" },
];

/* ============================================================================================= */
/* The document                                                                                  */
/* ============================================================================================= */

type ThemeId = "standard" | "mono" | "screen";

function DocumentPages(props: { theme?: ThemeId; dimmed?: boolean; commentaryTaken?: boolean }) {
  const theme = props.theme ?? "standard";
  const map = theme === "mono" ? "greys" : "viridis";
  const pageClass = [
    "re-page",
    theme === "screen" ? "re-page--landscape re-page--sans" : "",
    props.dimmed ? "re-doc-dim" : "",
  ].filter(Boolean).join(" ");
  const secondClass = [pageClass, "re-page--second"].join(" ");

  return (
    <>
      <article className={pageClass} aria-label="レポート 1ページ目">
        <div>
          <span className="re-eyebrow">設計レビュー・Run 12</span>
          <h1>強度確認レポート</h1>
        </div>
        <p className="re-lede">
          この文書は受け取った人がそのまま開ける自己完結の成果物です。数値は単位・桁・来歴とともに示し、欠損は欠損のまま明示します。
        </p>

        {/* ビュー（静止画）ブロック */}
        <section className="re-block" aria-label="ビューブロック">
          <div className="re-block-chrome">
            <span className="re-chip">ビュー（静止画）</span>
            <span className="re-chip" title="参照先：ビュー「全体外観」・ケース C-012">参照：全体外観</span>
          </div>
          <div className="re-figure">
            <div className="re-fig-canvas">
              <svg viewBox="0 0 400 220" role="img" aria-label="部品の外観（設計状態の仮置き・実描画ではありません）">
                <g fill="var(--re-paper)" stroke="var(--re-paper-muted)" strokeWidth="1">
                  <path d="M96 176 L172 62 L286 96 L268 176 L156 192 Z" />
                </g>
                <g fill="none" stroke="var(--re-paper-muted)" strokeWidth="1">
                  <path d="M172 62 L188 112 L286 96" />
                  <path d="M188 112 L164 168 L156 192" />
                  <path d="M164 168 L268 176" />
                  <path d="M96 176 L164 168" />
                </g>
                {/* 応力集中部 R2 のマーク - 位置の指示であり、値の主張ではない */}
                <circle cx="188" cy="112" r="10" fill="none" stroke="var(--re-paper-ink)" strokeWidth="1" strokeDasharray="3 2" />
              </svg>
              <span className="re-fig-standin">静止画プレースホルダー・実描画ではありません</span>
              {/* INV-024: 変形倍率は絵の中に刻む */}
              <span className="re-fig-stamp">変形表示 ×1.8（表示上の誇張）</span>
            </div>
            <div className="re-fig-legend" aria-label="凡例">
              <span className="re-fig-legend-title">ミーゼス応力（MPa・節点平均）</span>
              <span className="re-fig-bar" style={{ backgroundImage: `var(--map-${map})` }} />
              <span className="re-fig-ticks"><span>250</span><span>125</span><span>0</span></span>
            </div>
            <p className="re-fig-caption">
              図1　全体外観・ミーゼス応力（節点平均・平均幅は表1）・ケース C-012。表示ジオメトリは簡略化されており、報告値は完全データから計算しています（INV-001）。
            </p>
          </div>
        </section>

        {/* 数値表ブロック */}
        <section className="re-block" aria-label="数値表ブロック">
          <div className="re-block-chrome">
            <span className="re-chip">数値表</span>
            <span className="re-chip" title="参照先：Run 12 の統計（完全データ・正準座標系）">参照：Run 12 統計</span>
          </div>
          <div className="re-doc-table">
            <table>
              <thead>
                <tr><th scope="col">項目</th><th scope="col">値</th><th scope="col">来歴</th><th scope="col">備考</th></tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">最大ミーゼス応力（非平均）</th>
                  <td className="number-cell"><QuantityChip value={V.unavg} unit="MPa" title="有効4桁（INV-014）" /></td>
                  <td><ProvenanceBadge origin="computed" /></td>
                  <td>隅部 R2・要素値のまま</td>
                </tr>
                <tr>
                  <th scope="row">最大ミーゼス応力（節点平均）</th>
                  <td className="number-cell"><QuantityChip value={V.avg} unit="MPa" title="有効4桁（INV-014）" /></td>
                  <td><ProvenanceBadge origin="computed" /></td>
                  <td>平均幅 ±{V.spread} MPa を併記（INV-033）</td>
                </tr>
                <tr>
                  <th scope="row">最大変位</th>
                  <td className="number-cell"><QuantityChip value={V.disp} unit="mm" /></td>
                  <td><ProvenanceBadge origin="computed" /></td>
                  <td>正準座標系・完全データ</td>
                </tr>
                <tr>
                  <th scope="row">反力合計</th>
                  <td className="number-cell"><QuantityChip value={V.reaction} unit="kN" /></td>
                  <td><ProvenanceBadge origin="computed" /></td>
                  <td>荷重入力と釣り合い</td>
                </tr>
                <tr>
                  <th scope="row">温度（入口）</th>
                  <td className="number-cell"><QuantityChip value={V.temp} unit={null} title="単位はファイルから推定しない（XC-003）" /></td>
                  <td><ProvenanceBadge origin="dataset" /></td>
                  <td>宣言されるまで換算しない</td>
                </tr>
                <tr>
                  <th scope="row">疲労安全率</th>
                  <NumberCell value={null} missingBecause="ケース C-014 に該当結果なし" />
                  <td><span className="re-doc-na" title="値が欠損のため来歴もありません">—</span></td>
                  <td>欠損のまま示す（XC-001）</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="re-fig-caption">表1　主要値。桁は元データが支える有効桁のみ（INV-014）。</p>
        </section>

        {/* 本文ブロック */}
        <section className="re-block" aria-label="本文ブロック">
          <div className="re-block-chrome"><span className="re-chip">本文（機械的要約）</span></div>
          <div className={theme === "mono" ? "re-two-col" : undefined}>
            <h2>判明事項</h2>
            <p>
              最大ミーゼス応力（非平均）は {V.unavg} MPa で、隅部 R2 の要素に生じる。節点平均では {V.avg} MPa（平均幅 ±{V.spread} MPa）。
              最大変位は {V.disp} mm、反力合計は {V.reaction} kN で荷重入力と釣り合う。
            </p>
            <h2>未判明事項</h2>
            <p>
              温度は単位が宣言されるまで換算・比較しない。疲労安全率はケース C-014 に結果がなく、欠損のまま示す。
            </p>
          </div>
        </section>

        {props.commentaryTaken ? (
          <section className="re-block" aria-label="取り込み済みの下書き">
            <div className="re-block-chrome">
              <span className="re-chip" title="下書きから取り込んだ本文。各文は種別と出典を保持します（XC-104）">本文（取り込み済みの下書き）</span>
            </div>
            <h2>考察</h2>
            {DRAFT_STATEMENTS.map((one) => (
              <p key={one.text}>
                {one.text} <span className="re-doc-ref">［{one.kind}・{one.source}］</span>
              </p>
            ))}
          </section>
        ) : null}

        <footer className="re-page-foot">
          <span>強度確認レポート・Run 12</span>
          <span>ページ 1 / 2</span>
        </footer>
      </article>

      {/* 2ページ目：必須情報。AC-007/AC-031 - 表示されたまま、取り除けない */}
      <article className={secondClass} aria-label="レポート 2ページ目（必須情報）">
        <section className="re-block" aria-label="必須情報">
          <div className="re-block-chrome">
            <span className="re-chip re-chip--lock" title="必須情報のため削除できません（AC-007・AC-031）。作れない場合は出力が停止し、理由が示されます">省略不可</span>
          </div>
          <h2>付録：必須情報</h2>
          <p className="re-fig-caption" style={{ marginBottom: 8 }}>
            この節はレポートから取り除けません。作れない項目があるときは出力が停止し、その項目が名指しされます。
          </p>
          <div className="re-trust">
            <section aria-label="来歴">
              <header><h3>来歴</h3><span className="re-chip re-chip--lock">省略不可</span></header>
              <dl className="re-kv">
                <dt>入力ファイル</dt><dd>run-012.op2（{formatBytes(15204352)}・SHA-256 先頭 9f3a41d0…）</dd>
                <dt>読み込み</dt><dd>2026-08-27 09:14・リーダー完全対応</dd>
                <dt>ワークスペース</dt><dd>bracket-2026・改訂 r48</dd>
                <dt>抽出</dt><dd>mises-v2・集計は float64・対和加算（INV-031）</dd>
              </dl>
            </section>
            <section aria-label="宣言単位">
              <header><h3>宣言単位</h3><span className="re-chip re-chip--lock">省略不可</span></header>
              <div className="re-doc-table">
                <table>
                  <thead><tr><th scope="col">物理量</th><th scope="col">単位</th><th scope="col">宣言</th></tr></thead>
                  <tbody>
                    <tr><td>応力</td><td><UnitLabel unit="MPa" /></td><td>利用者宣言・2026-08-25</td></tr>
                    <tr><td>変位</td><td><UnitLabel unit="mm" /></td><td>利用者宣言・2026-08-25</td></tr>
                    <tr><td>力</td><td><UnitLabel unit="kN" /></td><td>利用者宣言・2026-08-25</td></tr>
                    <tr><td>温度</td><td><UnitLabel unit={null} /></td><td>宣言されるまで換算しない（XC-003）</td></tr>
                  </tbody>
                </table>
              </div>
            </section>
            <section aria-label="制約">
              <header><h3>制約</h3><span className="re-chip re-chip--lock">省略不可</span></header>
              <ul>
                <li>表示ジオメトリは間引き・スケール調整されており、報告値は完全データから別経路で計算している（INV-001・INV-009）。</li>
                <li>節点平均の極値は平均幅を併記する。平滑化した山だけを示さない（INV-032・INV-033）。</li>
                <li>欠損値は代入せず欠損のまま示す。ゼロ・前回値・補間で埋めない（XC-001）。</li>
              </ul>
            </section>
            <section aria-label="製品版">
              <header><h3>製品版</h3><span className="re-chip re-chip--lock">省略不可</span></header>
              <dl className="re-kv">
                <dt>製品</dt><dd>SOLVIA 0.4（開発版・walking skeleton）</dd>
                <dt>リーダー</dt><dd>VTK 9.3.1</dd>
                <dt>出力</dt><dd>html-export 0.4・オフライン完結</dd>
              </dl>
            </section>
          </div>
        </section>
        <footer className="re-page-foot">
          <span>強度確認レポート・Run 12</span>
          <span>ページ 2 / 2</span>
        </footer>
      </article>
    </>
  );
}

/* ============================================================================================= */
/* Variant canvases                                                                              */
/* ============================================================================================= */

function DefaultCanvas() {
  return (
    <div className="re-canvas">
      <p className="re-note">プレビューの値は例示です（設計状態・OPEN-022）。単位・桁・来歴・欠損の表示規則のみを示します。ページ内は成果物の書体（GL-013）、周囲が道具です。</p>
      <DocumentPages />
    </div>
  );
}

/* blank: bundled templates and the deliberate empty document */
const TEMPLATES = [
  { id: "paper", name: "学術論文", note: "同梱サンプル・2段組", deck: false, blank: false },
  { id: "memo", name: "技術メモ", note: "同梱サンプル・1段", deck: false, blank: false },
  { id: "onepager", name: "1ページ要約", note: "同梱サンプル・A4×1", deck: false, blank: false },
  { id: "deck", name: "設計レビューデッキ", note: "同梱サンプル・横型", deck: true, blank: false },
  { id: "compare", name: "ケース間比較", note: "同梱サンプル・表中心", deck: false, blank: false },
  { id: "blank", name: "空文書", note: "意図的に空から始める", deck: false, blank: true },
];

function TemplateChoices() {
  return (
    <div className="re-choices">
      <h2>レポートを作成</h2>
      <p>
        テンプレートを選ぶか、意図的に空文書から始めます。テンプレートは値を持ち込みません -
        参照は開いているワークスペースから解決され、解決できないものは未解決として名指しされます（XC-090）。
      </p>
      <div className="re-choice-grid">
        {TEMPLATES.map((one) => (
          <button
            key={one.id}
            type="button"
            className="re-choice"
            onClick={() => {
              submit({ operation: "report.create", parameters: { template: one.id } });
              session.navigate("report", "default");
            }}
          >
            <span className={["re-thumb", one.deck ? "re-thumb--deck" : "", one.blank ? "re-thumb--blank" : ""].filter(Boolean).join(" ")} aria-hidden>
              {one.blank ? <i /> : <><i /><i /><i /><i /></>}
            </span>
            <b>{one.name}</b>
            <small>{one.note}</small>
          </button>
        ))}
      </div>
      <p className="re-note" style={{ textAlign: "center", marginTop: 12 }}>
        空文書にも必須情報（来歴・宣言単位・制約・製品版）は含まれます（AC-031）。
      </p>
    </div>
  );
}

/* drafting: method choice, then the XC-214 sequence */
function DraftingCanvas() {
  const [method, setMethod] = useState<"mechanical" | "generated">("mechanical");
  const [stage, setStage] = useState<"none" | "review" | "applied">("review");
  const generationBlocked = method === "generated";

  return (
    <div className="re-canvas">
      <div className="re-stages" aria-label="下書きの進行">
        <span className={stage === "none" ? "re-stage" : "re-stage re-stage--done"} aria-current={stage === "none" ? "step" : undefined}>未作成</span>
        <span className="re-stage-arrow" aria-hidden>→</span>
        <span className={stage === "applied" ? "re-stage re-stage--done" : "re-stage"} aria-current={stage === "review" ? "step" : undefined}>確認待ち</span>
        <span className="re-stage-arrow" aria-hidden>→</span>
        <span className="re-stage" aria-current={stage === "applied" ? "step" : undefined}>取り込み済み</span>
      </div>
      <p className="re-note">これは順序であり、設定ではありません（XC-214）。確認して取り込むまで、下書きは本文に入りません。</p>

      <div className="re-strip">
        <div className="re-methods" role="group" aria-label="書き方の方式">
          <button type="button" className="re-method" aria-pressed={method === "mechanical"} onClick={() => setMethod("mechanical")}>
            <b>機械的要約</b>
            <small>モデル不使用。読み取った値と単位を定型文で並べ、ケースが変わっても文形は同じです。</small>
          </button>
          <button type="button" className="re-method" aria-pressed={method === "generated"} onClick={() => setMethod("generated")}>
            <b>生成コメント</b>
            <small>方針とモデルを決めて生成し、各文を種別・出典つきで確認してから取り込みます（XC-104）。</small>
          </button>
        </div>
        {generationBlocked ? (
          <div className="notice warn" role="status">
            <b>生成コメントは現在利用できません</b>
            <span className="why">モデルが未設定です。右の「執筆」タブで設定し、送信内容と費用を確認するまで、下書きの生成は開始されません。</span>
          </div>
        ) : null}
      </div>

      {stage === "none" ? (
        <div className="re-card">
          <header><h2>下書き</h2><small>未作成</small></header>
          <div className="re-card-body">
            <p className="prop-note" style={{ margin: 0 }}>下書きはまだ作られていません。方式を選んで作成すると、ここに各文が種別・出典つきで並びます。</p>
          </div>
          <footer>
            {generationBlocked ? (
              <button type="button" className="btn primary" {...disabledBecause("モデルが未設定のため生成できません")}>下書きを作る</button>
            ) : (
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  submit({ operation: "report.update", parameters: { action: "draft.create", method } });
                  setStage("review");
                }}
              >
                下書きを作る
              </button>
            )}
          </footer>
        </div>
      ) : null}

      {stage === "review" ? (
        <div className="re-card">
          <header><h2>下書きの確認</h2><small>機械的要約・4文＋除外2件</small></header>
          <div className="re-card-body">
            <div className="re-statements">
              {DRAFT_STATEMENTS.map((one) => (
                <article className="re-statement" key={one.text}>
                  <p>{one.text}</p>
                  <footer>
                    <span className="re-kind">種別：{one.kind}</span>
                    <span>出典：{one.source}</span>
                  </footer>
                </article>
              ))}
            </div>
            <UnresolvedList title="除外された記述（2件・脱落ではなく明示）" items={DRAFT_EXCLUDED} />
          </div>
          <footer>
            <button type="button" className="btn ghost" onClick={() => setStage("none")}>破棄</button>
            <button
              type="button"
              className="btn primary"
              onClick={() => {
                submit({ operation: "report.update", parameters: { action: "draft.accept", statements: DRAFT_STATEMENTS.length } });
                setStage("applied");
              }}
            >
              4文を取り込む
            </button>
          </footer>
        </div>
      ) : null}

      {stage === "applied" ? (
        <div className="re-strip">
          <div className="notice good" role="status">
            <b>取り込み済み</b>
            <span className="why">4文を本文ブロック「考察」として保存しました。各文は種別と出典を保持し、対象ケースが変わると再確認が必要になります。</span>
          </div>
          <div className="re-actions">
            <button type="button" className="btn ghost" onClick={() => setStage("none")}>破棄して作り直す</button>
          </div>
        </div>
      ) : null}

      <p className="re-note">{stage === "review" ? "下書きは取り込むまで本文に入りません。下の文書は現在の状態のままです。" : "現在の文書："}</p>
      <DocumentPages dimmed={stage === "review"} commentaryTaken={stage === "applied"} />
    </div>
  );
}

/* commentary-review: everything that will be sent, fixed before generation starts */
function CommentaryReviewCanvas() {
  const facts: { label: string; value: ReactNode }[] = [
    { label: "方向（観点）", value: <span className="re-fact-strong">「安全率の余裕と、隅部 R2 の応力集中の妥当性を短く議論する」</span> },
    { label: "深さ", value: "標準（本文 4〜6文）" },
    { label: "モデル", value: "外部モデル「commentary-l」・構成済み（送信先 api.example.co）" },
    { label: "検索", value: "行わない（この生成に外部検索はありません）" },
    { label: "送信内容", value: <>統計値の表（12行）・ケース名・宣言単位・テンプレート見出し。合計 {formatBytes(18944)}・約9,400トークン</> },
    { label: "送信しない情報", value: "ジオメトリ、フィールド生データ、ファイルパス、ワークスペース外の情報" },
    { label: "費用見積", value: <span className="re-fact-strong">約 ¥14 / 回（概算・上限 ¥40 で自動停止）</span> },
    { label: "生成後の扱い", value: "各文は種別と出典を伴って「確認待ち」に入り、取り込むまで本文に入りません（XC-104・XC-214）" },
  ];
  return (
    <div className="re-canvas">
      <div className="re-card" role="region" aria-label="生成コメントの利用確認">
        <header><h2>生成コメントの利用確認</h2><small>生成はまだ開始されていません</small></header>
        <div className="re-card-body">
          <div className="re-facts">
            {facts.map((one) => (
              <div className="re-fact" key={one.label}>
                <b>{one.label}</b>
                <div>{one.value}</div>
              </div>
            ))}
          </div>
          <div className="notice" role="note">
            <b>確定するまで何も送信されません</b>
            <span className="why">開始すると上記の送信内容だけを1回送ります。ホスト・日時・判断はローカル監査に記録されます（XC-106）。</span>
          </div>
        </div>
        <footer>
          <button type="button" className="btn ghost" onClick={() => session.navigate("report", "drafting")}>中止</button>
          <button
            type="button"
            className="btn primary"
            onClick={() => {
              submit({ operation: "report.update", parameters: { action: "commentary.generate" } });
              session.navigate("report", "drafting");
            }}
          >
            この内容で生成
          </button>
        </footer>
      </div>
      <p className="re-note">対象の文書（現在の状態）：</p>
      <DocumentPages dimmed />
    </div>
  );
}

/* theme: one choice fixes page, palette and type together; faces shown in themselves */
const THEMES: { id: ThemeId; name: string; page: string; face: string; faceStack: string; grey: boolean; note: string }[] = [
  { id: "standard", name: "技術資料・標準", page: "A4縦・1段", face: "Noto Serif JP", faceStack: "'Noto Serif JP', 'Yu Mincho', serif", grey: false, note: "図は識別性優先の配色" },
  { id: "mono", name: "モノクロ印刷", page: "A4縦・2段", face: "Georgia", faceStack: "Georgia, 'Times New Roman', serif", grey: true, note: "図の色も濃淡に置き換え" },
  { id: "screen", name: "画面向け", page: "横長・1段", face: "IBM Plex Sans JP", faceStack: "var(--family-ui)", grey: false, note: "横長ページ・ゴシック本文" },
];

const SPECIMENS: { face: string; stack: string; sample: string }[] = [
  { face: "Georgia（欧文セリフ）", stack: "Georgia, 'Times New Roman', serif", sample: `Max von Mises stress ${V.unavg} MPa — Design Review 12` },
  { face: "Noto Serif JP（和文明朝）", stack: "'Noto Serif JP', 'Yu Mincho', serif", sample: `最大応力 ${V.unavg} MPa・設計レビュー 第12回` },
  { face: "IBM Plex Sans JP（ゴシック）", stack: "var(--family-ui)", sample: `最大応力 ${V.unavg} MPa・設計レビュー 第12回` },
  { face: "IBM Plex Mono（等幅・数表）", stack: "var(--family-mono)", sample: `${V.unavg}   ${V.disp}   ${V.reaction}` },
];

function ThemeCanvas() {
  const [themeId, setThemeId] = useState<ThemeId>("standard");
  return (
    <div className="re-canvas">
      <span className="re-canvas-label">テーマ（1つの選択がページ・配色・書体をまとめて決めます・XC-214）</span>
      <div className="re-theme-grid" role="group" aria-label="テーマ">
        {THEMES.map((one) => (
          <button
            key={one.id}
            type="button"
            className="re-theme-card"
            aria-pressed={themeId === one.id}
            onClick={() => {
              setThemeId(one.id);
              submit({ operation: "report.update", parameters: { theme: one.id } });
            }}
          >
            <b style={{ fontFamily: one.faceStack }}>{one.name}</b>
            <small>{one.page}・本文 {one.face}</small>
            <span className="re-swatches" aria-hidden>
              <span className="re-swatch" style={{ backgroundImage: one.grey ? "var(--map-greys)" : "var(--map-viridis)" }} />
              <span className="re-swatch" style={{ background: "var(--g-ink-strong)" }} />
              <span className="re-swatch" style={{ background: one.grey ? "var(--g-ink-muted)" : "var(--g-ink)" }} />
              <span className="re-swatch" style={{ background: "var(--g-well)" }} />
            </span>
            <small>{one.note}</small>
          </button>
        ))}
      </div>
      <span className="re-canvas-label">書体見本（書体自身で表示・XC-215）</span>
      <div className="re-specimens">
        {SPECIMENS.map((one) => (
          <div className="re-specimen" key={one.face}>
            <b>{one.face}</b>
            <span style={{ fontFamily: one.stack }} title={one.sample}>{one.sample}</span>
          </div>
        ))}
      </div>
      <p className="re-note">テーマはページ・配色・書体・図表表現だけに適用され、値と文章は変わりません。下のプレビューが選択を反映します（モノクロ印刷では凡例が濃淡になります）。</p>
      <DocumentPages theme={themeId} />
    </div>
  );
}

/* exporting: cancellable progress, and no second export to the same target (XC-060) */
function ExportingCanvas() {
  const [cancelled, setCancelled] = useState(false);
  return (
    <div className="re-canvas">
      <div className="re-strip">
        {cancelled ? (
          <>
            <div className="notice" role="status">
              <b>出力を中断しました</b>
              <span className="why">ページ境界（3/5）で停止し、書きかけの一時ファイルは削除しました。前回の成果物は変更されていません。</span>
            </div>
            <div className="re-actions">
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  submit({ operation: "report.export", parameters: { format: "html", target: EXPORT_TARGET } });
                  setCancelled(false);
                }}
              >
                再出力
              </button>
            </div>
          </>
        ) : (
          <>
            <ProgressAndCancel
              label="自己完結HTMLを出力中"
              detail={`${EXPORT_TARGET}design-review.html・ページ 3/5`}
              fraction={0.62}
              onCancel={() => {
                submit({ operation: "report.export", parameters: { action: "cancel", target: EXPORT_TARGET } });
                setCancelled(true);
              }}
              cancelNote="中断はページ境界で反映されます"
            />
            <div className="notice" role="note">
              <b>同じ対象への再出力は停止中（XC-060）</b>
              <span className="why">進行中の出力が完了または中断されるまで、同じ保存先への出力は開始できません。別の保存先への出力は妨げません。</span>
            </div>
            <div className="re-actions">
              <button type="button" className="btn" {...disabledBecause("同じ対象への出力が進行中（XC-060）")}>再出力</button>
            </div>
          </>
        )}
      </div>
      <DocumentPages />
    </div>
  );
}

/* export-error: format and reason named; the previous artefact untouched */
function ExportErrorCanvas() {
  return (
    <div className="re-canvas">
      <div className="re-strip">
        <div className="notice error" role="alert">
          <b>PowerPoint出力を利用できません</b>
          <span className="why">保存先 {EXPORT_TARGET} が読取専用です（EACCES）。フォルダーの書き込み権限を確認してください。</span>
        </div>
        <div className="notice good" role="status">
          <b>前回の成果物は変更されていません</b>
          <span className="why">design-review.pptx（2026-08-27 14:02・{PPTX_SIZE}）はそのまま残っています。出力は一時ファイルに書き、完了時にのみ置き換えます。</span>
        </div>
        <div className="re-actions">
          <button type="button" className="btn" onClick={() => submit({ operation: "report.update", parameters: { action: "output.retarget" } })}>保存先を変更</button>
          <button type="button" className="btn primary" onClick={() => submit({ operation: "report.export", parameters: { format: "pptx", target: EXPORT_TARGET } })}>再試行</button>
        </div>
      </div>
      <DocumentPages />
    </div>
  );
}

/* output-preflight: required info / fonts / substitutions / unresolved / destination, one check */
function PreflightCanvas() {
  const longTarget = "D:/projects/bracket-2026/output/report/run-012/design-review-strength-confirmation/";
  const checks: { id: string; status: "pass" | "warn" | "block"; label: string; detail: ReactNode }[] = [
    { id: "required", status: "pass", label: "必須情報", detail: "来歴・宣言単位・制約・製品版の4ブロックを収録できます。" },
    { id: "fonts", status: "pass", label: "字体", detail: "使用グリフ 1,842。Noto Serif JP / IBM Plex Sans JP を使用分のみ埋め込みます。表示できない文字はありません。" },
    { id: "substitution", status: "warn", label: "置換", detail: "PowerPoint はインタラクティブ3Dを保持できないため、静止画へ置換し、置換した旨を文書内に記載します。" },
    {
      id: "unresolved", status: "block", label: "未解決",
      detail: (
        <>
          <UnresolvedList items={[
            { what: "グラフ「ケース横断 最大応力」系列2", missing: "温度の宣言単位（XC-003）" },
            { what: "参考資料「材料試験成績書」", missing: "ファイル（移動または削除）。参照は保持され、脱落しません" },
          ]} />
          <span>2件が解決するまで出力を開始できません（XC-090）。</span>
        </>
      ),
    },
    { id: "destination", status: "pass", label: "保存先", detail: <><span className="re-path" title={longTarget}>{longTarget}</span> 書き込み可・既存出力は上書きしません。</> },
  ];
  const mark = { pass: "○", warn: "△", block: "✕" } as const;
  const markTitle = { pass: "合格", warn: "注意", block: "停止" } as const;
  return (
    <div className="re-canvas">
      <div className="re-card" role="region" aria-label="出力前チェック">
        <header><h2>出力前チェック</h2><small>形式：PowerPoint</small></header>
        <div className="re-card-body">
          <div className="re-checks">
            {checks.map((one) => (
              <div className={`re-check re-check--${one.status}`} key={one.id}>
                <span className="re-check-mark" title={markTitle[one.status]} aria-label={markTitle[one.status]}>{mark[one.status]}</span>
                <b>{one.label}</b>
                <div className="re-check-detail">{one.detail}</div>
              </div>
            ))}
          </div>
        </div>
        <footer>
          <button type="button" className="btn ghost" onClick={() => session.navigate("report", "default")}>閉じる</button>
          <button type="button" className="btn primary" {...disabledBecause("未解決2件が解決されるまで出力を開始できません")}>出力を開始</button>
        </footer>
      </div>
      <p className="re-note">検査対象の文書（現在の状態）：</p>
      <DocumentPages dimmed />
    </div>
  );
}

export function ReportScreen(props: { variant: string }) {
  switch (props.variant) {
    case "blank": return <TemplateChoices />;
    case "drafting": return <DraftingCanvas />;
    case "commentary-review": return <CommentaryReviewCanvas />;
    case "theme": return <ThemeCanvas />;
    case "exporting": return <ExportingCanvas />;
    case "export-error": return <ExportErrorCanvas />;
    case "output-preflight": return <PreflightCanvas />;
    default: return <DefaultCanvas />;
  }
}

/* ============================================================================================= */
/* The property rail: レポート / 内容 / 執筆 / スタイル / 出力                                       */
/* ============================================================================================= */

function RailOverall(props: { variant: string }) {
  const lastOutput =
    props.variant === "exporting" ? "出力中（3/5ページ・HTML）"
    : props.variant === "export-error" ? "失敗・前回成果物は保持"
    : "2026-08-27 14:02・HTML";
  return (
    <div>
      <div className="prop-section">
        <h3>レポート</h3>
        <div className="prop-row">
          <label htmlFor="re-name">名前</label>
          <input id="re-name" className="field-input" defaultValue="設計レビュー Run 12" />
        </div>
        <div className="prop-row">
          <label htmlFor="re-title">表題</label>
          <input id="re-title" className="field-input" defaultValue="強度確認レポート" />
        </div>
        <div className="prop-row">
          <label htmlFor="re-lang">言語</label>
          <select id="re-lang" className="field-input" defaultValue="ja">
            <option value="ja">日本語</option>
            <option value="en">English</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-template">テンプレート</label>
          <input id="re-template" className="field-input" readOnly value="技術メモ・改訂 r3（同梱サンプル）" title="技術メモ・改訂 r3（同梱サンプル）。改訂を固定して参照しています" />
        </div>
      </div>
      <div className="prop-section">
        <h3>必須情報（省略不可）</h3>
        {[
          { id: "re-req-prov", label: "来歴" },
          { id: "re-req-unit", label: "宣言単位" },
          { id: "re-req-limit", label: "制約" },
          { id: "re-req-ver", label: "製品版" },
        ].map((one) => (
          <div className="prop-row" key={one.id}>
            <label htmlFor={one.id}>{one.label}</label>
            <input id={one.id} type="checkbox" checked disabled readOnly style={{ justifySelf: "start" }} title="必須のため外せません（AC-031）" />
          </div>
        ))}
        <p className="prop-note">必須情報は削除できません（AC-007・AC-031）。作れない項目があるときは出力が停止し、その項目が名指しされます。</p>
      </div>
      <div className="prop-section">
        <h3>状態</h3>
        <div className="prop-row">
          <label htmlFor="re-last">最終出力</label>
          <input id="re-last" className="field-input" readOnly value={lastOutput} />
        </div>
      </div>
    </div>
  );
}

type RailBlock = { id: string; name: string; detail: string; locked?: boolean };

function RailContents() {
  const s = useSession();
  const [blocks, setBlocks] = useState<RailBlock[]>([
    { id: "view", name: "ビュー", detail: "全体外観・静止画" },
    { id: "table", name: "数値表", detail: "主要値・Run 12 統計" },
    { id: "text", name: "本文", detail: "判明事項・未判明事項" },
    { id: "trust", name: "必須情報", detail: "来歴・宣言単位・制約・製品版", locked: true },
  ]);

  const move = (index: number, delta: number) => {
    setBlocks((current) => {
      const next = [...current];
      const a = next[index];
      const b = next[index + delta];
      if (a === undefined || b === undefined) return current;
      next[index] = b;
      next[index + delta] = a;
      return next;
    });
  };

  return (
    <div>
      <div className="prop-section">
        <h3>参照範囲</h3>
        <div className="prop-row">
          <label htmlFor="re-ws">ワークスペース</label>
          <select id="re-ws" className="field-input" defaultValue="current">
            <option value="current">現在（bracket-2026）</option>
            <option value="multiple">複数を選択…</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-case">ケース</label>
          <select id="re-case" className="field-input" defaultValue="selected">
            <option value="selected">選択中（{s.selectedCaseId ?? "未選択"}）</option>
            <option value="saved">保存済み選択「超過ケース」</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-refs">参考資料</label>
          <input id="re-refs" className="field-input" readOnly value="2件（うち1件未解決）" />
        </div>
      </div>
      <div className="prop-section">
        <h3>収録項目（順序どおり）</h3>
        <div className="re-rail-blocks" aria-label="レポートブロック">
          {blocks.map((block, index) => (
            <div className="re-rail-block" key={block.id}>
              <span>
                <b>{block.name}</b>
                <small>{block.detail}</small>
              </span>
              <span className="re-rail-tools">
                <button
                  type="button"
                  aria-label={`${block.name}を上へ移動`}
                  onClick={() => move(index, -1)}
                  {...(index === 0 ? disabledBecause("先頭のため上へ移動できません") : {})}
                >↑</button>
                <button
                  type="button"
                  aria-label={`${block.name}を下へ移動`}
                  onClick={() => move(index, 1)}
                  {...(index === blocks.length - 1 ? disabledBecause("末尾のため下へ移動できません") : {})}
                >↓</button>
              </span>
              {block.locked ? (
                <span className="re-lock" title="必須のため削除できません（AC-031）">必須</span>
              ) : (
                <span className="re-rail-tools">
                  <button
                    type="button"
                    aria-label={`${block.name}を削除`}
                    onClick={() => setBlocks((current) => current.filter((one) => one.id !== block.id))}
                  >✕</button>
                </span>
              )}
            </div>
          ))}
        </div>
        <div className="prop-row" style={{ marginTop: 8 }}>
          <label htmlFor="re-add">追加</label>
          <select
            id="re-add"
            className="field-input"
            value="choose"
            onChange={(event) => {
              const kind = event.target.value;
              if (kind === "choose") return;
              const labels: Record<string, string> = { view: "ビュー", graph: "グラフ", table: "数値表", text: "本文", references: "参考資料" };
              setBlocks((current) => [
                ...current,
                { id: `${kind}-${current.length}`, name: labels[kind] ?? kind, detail: "参照先を選択してください" },
              ]);
            }}
          >
            <option value="choose">ブロックを選択…</option>
            <option value="view">ビュー</option>
            <option value="graph">グラフ</option>
            <option value="table">数値表</option>
            <option value="text">本文</option>
            <option value="references">参考資料</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-viewform">ビュー形式</label>
          <select id="re-viewform" className="field-input" defaultValue="still">
            <option value="still">静止画</option>
            <option value="interactive">インタラクティブ3D</option>
            <option value="video">動画</option>
          </select>
        </div>
      </div>
      <div className="prop-section">
        <h3>未解決の参照</h3>
        <UnresolvedList items={[{ what: "参考資料「材料試験成績書」", missing: "ファイル（移動または削除）。参照は保持され、一覧から脱落しません" }]} />
      </div>
    </div>
  );
}

function RailDrafting(props: { variant: string }) {
  const modelConfigured = props.variant === "commentary-review";
  const [method, setMethod] = useState<"mechanical" | "generated">(
    props.variant === "commentary-review" ? "generated" : "mechanical",
  );
  const draftState =
    props.variant === "drafting" ? "確認待ち・4文＋除外2件"
    : props.variant === "commentary-review" ? "未作成（生成の確認中）"
    : "未作成";
  const createBlocked = method === "generated" && !modelConfigured;

  return (
    <div>
      <div className="prop-section">
        <h3>書き方</h3>
        <div className="prop-row">
          <label htmlFor="re-method">方式</label>
          <select id="re-method" className="field-input" value={method} onChange={(event) => setMethod(event.target.value === "generated" ? "generated" : "mechanical")}>
            <option value="mechanical">機械的要約のみ</option>
            <option value="generated">生成コメント</option>
          </select>
        </div>
        {method === "mechanical" ? (
          <p className="prop-note">モデルは使いません。読み取った値と単位を定型文で並べ、ケースが変わっても文形は同じです。</p>
        ) : null}
      </div>
      {method === "generated" ? (
        <div className="prop-section">
          <h3>方針</h3>
          <div className="prop-row" style={{ alignItems: "start" }}>
            <label htmlFor="re-direction">観点</label>
            <textarea id="re-direction" className="field-input" rows={3} placeholder="議論してほしい観点" defaultValue="安全率の余裕と、隅部 R2 の応力集中の妥当性" />
          </div>
          <div className="prop-row">
            <label htmlFor="re-depth">深さ</label>
            <select id="re-depth" className="field-input" defaultValue="standard">
              <option value="brief">簡潔</option>
              <option value="standard">標準</option>
              <option value="detailed">詳細</option>
            </select>
          </div>
          <div className="prop-row">
            <label htmlFor="re-model">モデル</label>
            <input id="re-model" className="field-input" readOnly value={modelConfigured ? "外部「commentary-l」構成済み" : "未設定"} title={modelConfigured ? "送信先 api.example.co" : "設定するまで生成は開始されません"} />
          </div>
          <div className="prop-row">
            <label htmlFor="re-search">検索の可否</label>
            <select id="re-search" className="field-input" defaultValue="off">
              <option value="off">検索しない</option>
              <option value="ask">要求ごとに許可を確認</option>
            </select>
          </div>
          {createBlocked ? (
            <div className="notice warn" role="status" style={{ marginTop: 8 }}>
              <b>生成コメントは利用できません</b>
              <span className="why">モデルが未設定です。設定し、送信内容と費用を確認するまで生成は開始されません。</span>
            </div>
          ) : (
            <p className="prop-note">生成前に、送信内容と費用の確認が中央に表示されます。確定するまで何も送信されません。</p>
          )}
        </div>
      ) : null}
      <div className="prop-section">
        <h3>下書き（順序：未作成 → 確認待ち → 取り込み済み）</h3>
        <div className="prop-row">
          <label htmlFor="re-draft-state">状態</label>
          <input id="re-draft-state" className="field-input" readOnly value={draftState} />
        </div>
        <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
          {createBlocked ? (
            <button type="button" className="btn primary" {...disabledBecause("モデルが未設定のため生成できません")}>下書きを作る</button>
          ) : (
            <button type="button" className="btn primary" onClick={() => submit({ operation: "report.update", parameters: { action: "draft.create", method } })}>下書きを作る</button>
          )}
          {props.variant === "drafting" ? (
            <button type="button" className="btn ghost" onClick={() => submit({ operation: "report.update", parameters: { action: "draft.discard" } })}>破棄</button>
          ) : (
            <button type="button" className="btn ghost" {...disabledBecause("破棄する下書きがありません")}>破棄</button>
          )}
        </div>
        <p className="prop-note">これは設定ではなく順序です（XC-214）。各文を種別・出典つきで確認して取り込むまで、本文は変わりません（XC-104）。</p>
      </div>
    </div>
  );
}

const RAIL_FACES = {
  "noto-serif": { label: "Noto Serif JP", stack: "'Noto Serif JP', 'Yu Mincho', serif" },
  georgia: { label: "Georgia", stack: "Georgia, 'Times New Roman', serif" },
  "plex-sans": { label: "IBM Plex Sans JP", stack: "var(--family-ui)" },
} as const;
type RailFaceId = keyof typeof RAIL_FACES;

function RailStyle() {
  const [bodyFace, setBodyFace] = useState<RailFaceId>("noto-serif");
  const face = RAIL_FACES[bodyFace];
  return (
    <div>
      <div className="prop-section">
        <h3>ページ</h3>
        <div className="prop-row">
          <label htmlFor="re-paper-size">用紙</label>
          <select id="re-paper-size" className="field-input" defaultValue="a4">
            <option value="a4">A4</option>
            <option value="letter">Letter</option>
            <option value="screen">画面向け（16:9）</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-orient">向き</label>
          <select id="re-orient" className="field-input" defaultValue="portrait">
            <option value="portrait">縦</option>
            <option value="landscape">横</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-margin">余白</label>
          <select id="re-margin" className="field-input" defaultValue="standard">
            <option value="narrow">狭い</option>
            <option value="standard">標準</option>
            <option value="wide">広い</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-columns">段組み</label>
          <select id="re-columns" className="field-input" defaultValue="single">
            <option value="single">1段</option>
            <option value="double">2段</option>
          </select>
        </div>
      </div>
      <div className="prop-section">
        <h3>共通要素</h3>
        {[
          { id: "re-style-header", label: "ヘッダー" },
          { id: "re-style-footer", label: "フッター" },
          { id: "re-style-pageno", label: "ページ番号" },
        ].map((one) => (
          <div className="prop-row" key={one.id}>
            <label htmlFor={one.id}>{one.label}</label>
            <input id={one.id} type="checkbox" defaultChecked style={{ justifySelf: "start" }} />
          </div>
        ))}
        <div className="prop-row">
          <label htmlFor="re-figwidth">図の幅</label>
          <select id="re-figwidth" className="field-input" defaultValue="column">
            <option value="column">段幅</option>
            <option value="page">ページ幅</option>
          </select>
        </div>
      </div>
      <div className="prop-section">
        <h3>配色</h3>
        <div className="prop-row">
          <label htmlFor="re-palette">図の配色</label>
          <select id="re-palette" className="field-input" defaultValue="accessible">
            <option value="accessible">識別性優先</option>
            <option value="mono">モノクロ印刷（濃淡）</option>
            <option value="print">印刷向け</option>
          </select>
        </div>
        <p className="prop-note">モノクロ印刷は図の色も濃淡に置き換えた変種を出力します。値と文章は変わりません。</p>
      </div>
      <div className="prop-section">
        <h3>文字表現</h3>
        <div className="prop-row">
          <label htmlFor="re-bodyface">本文</label>
          <select
            id="re-bodyface"
            className="field-input"
            value={bodyFace}
            style={{ fontFamily: face.stack }}
            onChange={(event) => {
              const next = event.target.value;
              if (next === "noto-serif" || next === "georgia" || next === "plex-sans") setBodyFace(next);
            }}
          >
            {(Object.keys(RAIL_FACES) as RailFaceId[]).map((id) => (
              <option key={id} value={id} style={{ fontFamily: RAIL_FACES[id].stack }}>{RAIL_FACES[id].label}</option>
            ))}
          </select>
        </div>
        <span className="re-specimen-inline" style={{ fontFamily: face.stack }} title="書体見本（書体自身で表示・XC-215）">
          最大応力 {V.unavg} MPa — Run 12
        </span>
        <div className="prop-row" style={{ marginTop: 6 }}>
          <label htmlFor="re-headface">見出し</label>
          <select id="re-headface" className="field-input" defaultValue="same">
            <option value="same">本文と同じ</option>
            <option value="sans">IBM Plex Sans JP</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-bodysize">本文サイズ</label>
          <select id="re-bodysize" className="field-input" defaultValue="10">
            <option value="9">9 pt</option>
            <option value="10">10 pt</option>
            <option value="11">11 pt</option>
          </select>
        </div>
      </div>
      <div className="prop-section">
        <h3>埋め込み</h3>
        <div className="prop-row">
          <label htmlFor="re-embed">範囲</label>
          <input id="re-embed" className="field-input" readOnly value="使用グリフのみを埋め込み" />
        </div>
        <p className="prop-note">ページ・配色・書体は1つのテーマです（XC-214）。表示できない文字は空の四角で出力せず、要素と文字を特定して報告します。</p>
      </div>
    </div>
  );
}

const FORMATS = [
  { id: "html", label: "インタラクティブHTML" },
  { id: "pptx", label: "PowerPoint" },
  { id: "docx", label: "Word" },
  { id: "xlsx", label: "Excel" },
  { id: "csv", label: "CSV" },
  { id: "image", label: "画像" },
  { id: "video", label: "動画" },
  { id: "text", label: "プレーンテキスト" },
  { id: "markdown", label: "Markdown" },
] as const;
type FormatId = (typeof FORMATS)[number]["id"];

function threeDNote(format: FormatId): string {
  switch (format) {
    case "html": return "インタラクティブのまま収録";
    case "video": return "動画として収録（カメラとタイムラインを1つずつ指定）";
    case "csv":
    case "xlsx":
    case "text":
      return "図は収録しない（数表・本文のみ）";
    default: return "静止画へ置換し、置換した旨を文書内に記載";
  }
}

function RailOutput(props: { variant: string }) {
  const [format, setFormat] = useState<FormatId>(props.variant === "export-error" ? "pptx" : "html");
  return (
    <div>
      {props.variant === "exporting" ? (
        <div className="prop-section">
          <h3>進行中</h3>
          <ProgressAndCancel
            label="HTMLを出力中"
            detail="ページ 3/5"
            fraction={0.62}
            onCancel={() => submit({ operation: "report.export", parameters: { action: "cancel", target: EXPORT_TARGET } })}
            cancelNote="中断はページ境界で反映されます"
          />
          <p className="prop-note">同じ対象への再出力は、完了または中断まで開始できません（XC-060）。</p>
        </div>
      ) : null}
      {props.variant === "export-error" ? (
        <div className="prop-section">
          <h3>前回の出力</h3>
          <div className="notice error">
            <b>PowerPoint出力が失敗</b>
            <span className="why">保存先が読取専用（EACCES）。前回の成果物（{PPTX_SIZE}）は変更されていません。</span>
          </div>
        </div>
      ) : null}
      <div className="prop-section">
        <h3>形式</h3>
        <div className="prop-row">
          <label htmlFor="re-format">出力</label>
          <select
            id="re-format"
            className="field-input"
            value={format}
            onChange={(event) => {
              const next = FORMATS.find((one) => one.id === event.target.value);
              if (next) setFormat(next.id);
            }}
          >
            {FORMATS.map((one) => <option key={one.id} value={one.id}>{one.label}</option>)}
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="re-3d">3D表現</label>
          <input id="re-3d" className="field-input" readOnly value={threeDNote(format)} title={threeDNote(format)} />
        </div>
        <div className="prop-row">
          <label htmlFor="re-offline">オフライン完結</label>
          <input id="re-offline" type="checkbox" checked disabled readOnly style={{ justifySelf: "start" }} title="成果物は受け取った人がオフラインで開けます。この方針は固定です（INV-007）" />
        </div>
        <div className="prop-row">
          <label htmlFor="re-fontembed">フォント埋め込み</label>
          <input id="re-fontembed" type="checkbox" checked disabled readOnly style={{ justifySelf: "start" }} title="使用グリフのみ埋め込み。外せば受け手の環境で崩れるため固定です" />
        </div>
      </div>
      <div className="prop-section">
        <h3>保存先</h3>
        <div className="prop-row">
          <label htmlFor="re-pattern">パターン</label>
          <input id="re-pattern" className="field-input" readOnly value="output/report/<run>/<case>/" title="output/report/<run>/<case>/" />
        </div>
        <div className="prop-row">
          <label htmlFor="re-overwrite">既存出力</label>
          <input id="re-overwrite" className="field-input" readOnly value="上書きしない" />
        </div>
        <div className="prop-row">
          <label htmlFor="re-preflight-state">事前検査</label>
          <input id="re-preflight-state" className="field-input" readOnly value={props.variant === "output-preflight" ? "実行中（中央に表示）" : "未実行"} />
        </div>
        <div style={{ marginTop: 8 }}>
          {props.variant === "exporting" ? (
            <button type="button" className="btn primary" {...disabledBecause("同じ対象への出力が進行中（XC-060）")}>出力前チェック</button>
          ) : (
            <button type="button" className="btn primary" onClick={() => session.navigate("report", "output-preflight")}>出力前チェック</button>
          )}
        </div>
        <p className="prop-note">出力は事前検査（必須情報・字体・置換・未解決・保存先）を通ってから開始されます。</p>
      </div>
    </div>
  );
}

export function ReportRail(props: { tab: string; variant: string }) {
  if (props.variant === "blank") {
    return (
      <div className="prop-section">
        <h3>レポート</h3>
        <p className="prop-note">
          まだレポートがありません。中央でテンプレートを選ぶか、意図的に空文書から始めます。どちらでも必須情報（来歴・宣言単位・制約・製品版）は含まれます（AC-031）。
        </p>
      </div>
    );
  }
  switch (props.tab) {
    case "overall": return <RailOverall variant={props.variant} />;
    case "contents": return <RailContents />;
    case "drafting": return <RailDrafting variant={props.variant} />;
    case "style": return <RailStyle />;
    case "output": return <RailOutput variant={props.variant} />;
    default: return <p className="prop-note" style={{ padding: 10 }}>このタブ（{props.tab}）の内容は未設計です。</p>;
  }
}
