/* Settings (MOD-009, XC-165): a full-width application page with its own category navigation -
 * no workspace sidebars, no instruction bar. Workspace-scoped preferences are a named scope group
 * rather than borrowed panels whose scope would be ambiguous.
 *
 * Variants (catalog.ts):
 * - default:        単位・座標系・描画・アシスタント・ライブラリの各カテゴリ。表示単位は宣言単位を書き換えない。
 * - invalid:        無効値は入力された欄で拒否され、直前の値が維持される（11_ui.md settings.invalid）。
 * - shortcuts:      コマンドとキーの編集。破壊的コマンドは キーなし + 確認経路で、割り当てを拒否する（XC-193）。衝突は列挙され、順序では解決しない。
 * - support-bundle: バンドルの内容を作成前に列挙する - 含める / 確認が必要 / 含めない顧客データ（XC-055b）。 */
import { useState } from "react";
import type { KeyboardEvent } from "react";
import { QuantityChip } from "../../shared/QuantityChip";
import { UnitLabel } from "../../shared/UnitLabel";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { MissingDataStyle } from "../../shared/MissingDataStyle";
import { ScopeConfirmation } from "../../shared/ScopeConfirmation";
import { formatBytes, disabledBecause } from "../../logic/format";
import { submit } from "../../client/operations";
import { session } from "../../state/session";
import "./settings.css";

type Category = "単位" | "座標系" | "描画" | "アシスタント" | "ライブラリ" | "ショートカット" | "診断";

const NAV_GROUPS: { scope: string; items: { id: Category; note: string }[] }[] = [
  {
    scope: "アプリ全体",
    items: [
      { id: "描画", note: "描画経路と対応状況" },
      { id: "アシスタント", note: "モデル提供元と鍵の保管" },
      { id: "ショートカット", note: "コマンドとキーの一覧" },
      { id: "診断", note: "ローカルログとサポートバンドル" },
    ],
  },
  {
    scope: "現在のワークスペース",
    items: [
      { id: "単位", note: "宣言単位と表示単位" },
      { id: "座標系", note: "成分座標系の宣言" },
      { id: "ライブラリ", note: "資産の保存先と解決" },
    ],
  },
];

function scopeOf(category: Category): string {
  for (const group of NAV_GROUPS) {
    if (group.items.some((item) => item.id === category)) return group.scope;
  }
  return "アプリ全体";
}

function initialCategory(variant: string): Category {
  if (variant === "shortcuts") return "ショートカット";
  if (variant === "support-bundle") return "診断";
  return "単位"; // default と invalid は単位カテゴリから始まる
}

export function SettingsScreen(props: { variant: string }) {
  const variant = props.variant;
  // The variant is the deep link; a local choice overrides it only until the variant changes.
  const [chosen, setChosen] = useState<{ forVariant: string; category: Category } | null>(null);
  const category = chosen !== null && chosen.forVariant === variant ? chosen.category : initialCategory(variant);

  return (
    <div className="se-canvas">
      <aside className="se-nav" aria-label="設定カテゴリ">
        <header className="se-nav-header">
          <b>設定</b>
          <small>アプリと作業環境</small>
        </header>
        {NAV_GROUPS.map((group) => (
          <nav className="se-nav-group" key={group.scope} aria-label={group.scope}>
            <small>{group.scope}</small>
            {group.items.map((item) => (
              <button
                key={item.id}
                aria-current={item.id === category}
                title={item.note}
                onClick={() => setChosen({ forVariant: variant, category: item.id })}
              >
                {item.id}
              </button>
            ))}
          </nav>
        ))}
        <p className="se-nav-note">
          設定はこの端末に保存されます。ワークスペース欄の項目は、開いているワークスペースにだけ効きます（XC-165）。
        </p>
      </aside>
      <div className="se-content">
        {/* keyed so a variant/category change resets panel-local state, as a deep link expects */}
        <div className="se-form" key={`${variant}/${category}`}>
          <span className="se-scope">{scopeOf(category)}</span>
          <h2>{category}</h2>
          {category === "単位" ? <UnitsPanel invalid={variant === "invalid"} /> : null}
          {category === "座標系" ? <FramesPanel /> : null}
          {category === "描画" ? <RenderPanel /> : null}
          {category === "アシスタント" ? <AssistantPanel /> : null}
          {category === "ライブラリ" ? <LibraryPanel /> : null}
          {category === "ショートカット" ? <ShortcutsPanel /> : null}
          {category === "診断" ? <DiagnosticsPanel openBundle={variant === "support-bundle"} /> : null}
        </div>
      </div>
    </div>
  );
}

/* ---- 単位: declared vs display - display never overwrites declared (XC-003, INV-014) --------- */

const STRESS_DISPLAY_UNITS = ["MPa", "kPa", "Pa", "GPa", "N/mm^2"] as const;

function UnitsPanel({ invalid }: { invalid: boolean }) {
  const [applied, setApplied] = useState("MPa"); // the last accepted display unit for stress
  const [draft, setDraft] = useState(invalid ? "psi2" : "MPa");
  const trimmed = draft.trim();
  const valid = (STRESS_DISPLAY_UNITS as readonly string[]).includes(trimmed);
  const shown = trimmed === "" ? "（空欄）" : trimmed;

  return (
    <>
      <p className="se-lead">
        CAEファイルは単位を運びません。単位は利用者が宣言するか、未宣言のまま示します（XC-003）。
        表示単位は換算表示だけを変え、宣言単位と保存値を書き換えません。
      </p>

      <section className="se-section">
        <h3>フィールドごとの単位</h3>
        <div className="table-scroll">
          <table className="value-table">
            <thead>
              <tr>
                <th>物理量</th>
                <th>宣言単位</th>
                <th>表示単位</th>
                <th>表示例</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>応力（stress）</td>
                <td><span className="se-unit-cell"><UnitLabel unit="MPa" /><ProvenanceBadge origin="declared" /></span></td>
                <td>{applied}</td>
                <td>
                  <span className="se-unit-cell">
                    <QuantityChip value="241.7" unit={applied} title="全データセット・正準座標系で計算した値（INV-001）" />
                    <ProvenanceBadge origin="computed" />
                  </span>
                </td>
              </tr>
              <tr>
                <td>変位（displacement）</td>
                <td><span className="se-unit-cell"><UnitLabel unit="mm" /><ProvenanceBadge origin="declared" /></span></td>
                <td>mm</td>
                <td>
                  <span className="se-unit-cell">
                    <QuantityChip value="0.482" unit="mm" />
                    <ProvenanceBadge origin="dataset" />
                  </span>
                </td>
              </tr>
              <tr>
                <td>温度（temperature）</td>
                <td><span className="se-unit-cell"><UnitLabel unit="K" /><ProvenanceBadge origin="declared" /></span></td>
                <td>°C</td>
                <td>
                  <span className="se-unit-cell">
                    <QuantityChip value="23.6" unit="°C" title="宣言値 296.7 K の換算表示 - 絶対精度と同じ桁数（INV-014）" />
                    <ProvenanceBadge origin="dataset" />
                  </span>
                </td>
              </tr>
              <tr>
                <td>圧力（p）</td>
                <td><UnitLabel unit={null} /></td>
                <td>
                  <select
                    className="field-input"
                    defaultValue=""
                    {...disabledBecause("単位が宣言されるまで表示単位は選べません（XC-003）")}
                  >
                    <option value="">選択不可 - 宣言待ち</option>
                  </select>
                </td>
                <td>
                  <span className="se-unit-cell">
                    <QuantityChip value="0.8821" unit={null} />
                    <ProvenanceBadge origin="dataset" />
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="prop-note">
          宣言単位は取込後に利用者が宣言したものです。大きさ・フィールド名・書き出したソルバーのいずれからも推測していません（XC-003）。
        </p>
      </section>

      <section className="se-section">
        <h3>応力の表示単位</h3>
        <div className="se-field-grid">
          <label htmlFor="se-display-unit">表示単位</label>
          <div className="se-inline">
            <input
              id="se-display-unit"
              className="field-input"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              aria-invalid={!valid}
              aria-describedby="se-display-unit-status"
            />
            <button
              className="btn primary"
              {...(valid ? { disabled: false } : disabledBecause("認識できる単位のみ保存できます"))}
              onClick={() => {
                setApplied(trimmed);
                submit({ operation: "field.setDisplayUnit", parameters: { field: "stress", unit: trimmed } });
              }}
            >
              保存
            </button>
          </div>
        </div>
        {valid ? (
          <p className="notice good" id="se-display-unit-status">
            <b>「{trimmed}」は宣言単位（MPa）と次元が一致します。</b>
            <span className="why">換算は表示だけに作用します。保存値・宣言単位・来歴は変わりません。</span>
          </p>
        ) : (
          <p className="notice error" id="se-display-unit-status" role="alert">
            <b>「{shown}」を拒否しました - 認識できる単位ではありません。</b>
            <span className="why">
              表示は直前の値「{applied}」のままです。宣言単位（MPa）も変更されていません。使用できる例：MPa・kPa・N/mm^2。
            </span>
          </p>
        )}
      </section>
    </>
  );
}

/* ---- 座標系: declared frames only - an unresolvable frame is refused, not guessed ------------ */

function FramesPanel() {
  return (
    <>
      <p className="se-lead">
        表示に使う座標と、成分を数える座標は別のものです。成分座標系は宣言されたフレームだけを使い、
        解決できないフレームへの変換は実行せず、拒否として示します（XC-001）。
      </p>

      <section className="se-section">
        <h3>既定の成分座標系</h3>
        <div className="se-field-grid">
          <label htmlFor="se-frame">既定フレーム</label>
          <select
            id="se-frame"
            className="field-input"
            defaultValue="global"
            onChange={(event) => submit({ operation: "frame.declare", parameters: { frame: event.target.value } })}
          >
            <option value="global">グローバル直交（X・Y・Z）</option>
            <option value="bearing">軸受中心 R-θ-Z（円筒）</option>
            <option value="sensor23" disabled>センサ23 ローカル - 定義が未宣言のため選択不可</option>
          </select>
        </div>
        <p className="prop-note">既定はワークスペースに保存され、各ビュー・グラフはフレームを個別に上書きできます。</p>
      </section>

      <section className="se-section">
        <h3>宣言済みフレーム</h3>
        <div className="table-scroll">
          <table className="value-table">
            <thead>
              <tr>
                <th>名前</th>
                <th>種別</th>
                <th>由来</th>
                <th>変換</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>グローバル直交</td>
                <td>直交</td>
                <td><ProvenanceBadge origin="declared" /></td>
                <td>可</td>
              </tr>
              <tr>
                <td>軸受中心 R-θ-Z</td>
                <td>円筒</td>
                <td><ProvenanceBadge origin="declared" /></td>
                <td>可</td>
              </tr>
              <tr>
                <td>センサ23 ローカル</td>
                <td><MissingDataStyle because="フレーム定義が未宣言" /></td>
                <td><ProvenanceBadge origin="dataset" /></td>
                <td><span className="missing-value">拒否 - 宣言まで変換しません</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="prop-note">
          ファイルが参照するだけのフレームは定義を持ちません。定義を宣言すると変換が有効になります。
        </p>
      </section>
    </>
  );
}

/* ---- 描画: renderer paths with availability - exact / baked / unsupported, never approximated - */

function RenderPanel() {
  return (
    <>
      <p className="se-lead">
        描画経路ごとに機能を exact / baked / unsupported として判定します。未対応の機能は暗黙に近似せず、
        「未対応」と表示します。数値は表示ジオメトリからは計測しません（INV-001）。
      </p>

      <section className="se-section">
        <h3>経路と状態</h3>
        <div>
          <div className="se-avail-row">
            <div className="se-avail-head">
              <span className="se-status good"><span className="dot" />利用可能</span>
              <b>ローカル3D（VTK 9.3）</b>
            </div>
            <small>GPU検出済み - このセッションの既定経路です。</small>
          </div>
          <div className="se-avail-row">
            <div className="se-avail-head">
              <span className="se-status good"><span className="dot" />利用可能</span>
              <b>Web（vtk.js）</b>
            </div>
            <small>配布ビューア用。一部機能は baked（事前計算）として判定されます。</small>
          </div>
          <div className="se-avail-row">
            <div className="se-avail-head">
              <span className="se-status warn"><span className="dot" />未接続</span>
              <b>フォトリアル（パストレース）</b>
            </div>
            <small>接続設定がありません。未接続の経路の対応状況は推測せず、接続時に実測します。</small>
          </div>
        </div>
      </section>

      <section className="se-section">
        <h3>既定の描画経路</h3>
        <div className="se-field-grid">
          <label htmlFor="se-renderer">既定経路</label>
          <select id="se-renderer" className="field-input" defaultValue="vtk">
            <option value="vtk">ローカル3D（VTK 9.3）</option>
            <option value="web">Web（vtk.js）</option>
            <option value="photoreal" disabled>フォトリアル - 未接続のため選択不可</option>
          </select>
        </div>
      </section>

      <section className="se-section">
        <h3>機能の判定</h3>
        <div className="table-scroll">
          <table className="value-table">
            <thead>
              <tr>
                <th>機能</th>
                <th>ローカル3D</th>
                <th>Web</th>
                <th>フォトリアル</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>コンター表示</td>
                <td>exact</td>
                <td>exact</td>
                <td><span className="se-cap">未接続</span></td>
              </tr>
              <tr>
                <td>変形表示（倍率描き込み）</td>
                <td>exact</td>
                <td>exact</td>
                <td><span className="se-cap">未接続</span></td>
              </tr>
              <tr>
                <td>レイトレース影</td>
                <td><span className="missing-value">未対応</span></td>
                <td><span className="missing-value">未対応</span></td>
                <td><span className="se-cap">未接続</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="prop-note">未対応の機能は近似表示に置き換えません。成果物には判定のとおりに記録されます。</p>
      </section>
    </>
  );
}

/* ---- アシスタント: provider and key - the key lives in the OS credential store, never shown --- */

function AssistantPanel() {
  const [keyPresent, setKeyPresent] = useState(true);
  const [provider, setProvider] = useState("external");
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <>
      <p className="se-lead">
        アシスタントは画面と同じコマンド面だけを通ります（INV-006）。モデルを構成しなくても、全操作を画面から利用できます。
      </p>

      <section className="se-section">
        <h3>モデル提供元</h3>
        <div className="se-field-grid">
          <label htmlFor="se-provider">提供元</label>
          <select
            id="se-provider"
            className="field-input"
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          >
            <option value="local">ローカルモデル（既定）</option>
            <option value="external" disabled={!keyPresent}>
              {keyPresent ? "外部プロバイダ（構成済み）" : "外部プロバイダ - 鍵が未登録のため選択不可"}
            </option>
          </select>
          <span className="se-field-label">APIキー</span>
          <div className="se-inline">
            <div className="se-keybox">
              <span>
                {keyPresent
                  ? "OS資格情報ストアに保存済み - 本文はこの画面にも表示されません"
                  : "鍵は保存されていません - 「置き換える」で登録します"}
              </span>
            </div>
            <button className="btn ghost" onClick={() => setKeyPresent(true)}>置き換える…</button>
            <button
              className="btn ghost"
              {...(keyPresent ? { disabled: false } : disabledBecause("保存された鍵がありません"))}
              onClick={() => setConfirmDelete(true)}
            >
              削除…
            </button>
          </div>
        </div>
        <p className="prop-note">
          鍵はOSの資格情報ストアだけに保存され、設定ファイル・ワークスペース・ログ・サポートバンドルのいずれにも含まれません（XC-055b）。
        </p>
      </section>

      <section className="se-section">
        <h3>外部送信</h3>
        <p className="notice">
          <b>外部モデルへの要求は、送信前に内容を確認します。</b>
          <span className="why">
            送信の可否と許可ホストはネットワーク画面が持ち、要求・日時・判断はローカル監査に記録されます（XC-106）。
          </span>
        </p>
        <div>
          <button className="btn ghost" onClick={() => session.navigate("network")}>ネットワーク画面を開く</button>
        </div>
      </section>

      {confirmDelete ? (
        <ScopeConfirmation
          operation="外部プロバイダのAPIキーを削除"
          affected={["OS資格情報ストア内の鍵 1件（本文は表示されません）", "外部プロバイダの構成 - 未構成に戻ります"]}
          onAccept={() => {
            setKeyPresent(false);
            setProvider("local"); // 鍵のない外部プロバイダは選択できない - 既定に戻る
            setConfirmDelete(false);
          }}
          onCancel={() => setConfirmDelete(false)}
        />
      ) : null}
    </>
  );
}

/* ---- ライブラリ: workspace vs shared, resolved offline only (INV-007) ------------------------ */

const SHARED_LIBRARY_PATH = "\\\\fs-eng-01\\solvia\\shared-library\\製品評価グループ\\2026年度\\approved-assets";

function LibraryPanel() {
  return (
    <>
      <p className="se-lead">
        資産はワークスペース内と共有ライブラリを区別し、移動はコピーで行います。参照はオフラインで解決できるものだけです（INV-007）。
      </p>

      <section className="se-section">
        <h3>保存先</h3>
        <div className="se-field-grid">
          <label htmlFor="se-library-scope">既定の保存先</label>
          <select id="se-library-scope" className="field-input" defaultValue="workspace">
            <option value="workspace">このワークスペース</option>
            <option value="shared">共有ライブラリ</option>
          </select>
          <span className="se-field-label">共有ライブラリの場所</span>
          <span className="se-path" title={SHARED_LIBRARY_PATH}>{SHARED_LIBRARY_PATH}</span>
        </div>
        <p className="prop-note">
          共有が到達できないときは、依存する資産を名前つきで「解決不可」として列挙します（XC-090）。ネットワーク越しの自動解決は行いません。
        </p>
      </section>

      <section className="se-section">
        <h3>内訳</h3>
        <div className="table-scroll">
          <table className="value-table">
            <thead>
              <tr>
                <th>種類</th>
                <th>件数</th>
                <th>容量</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>マテリアル</td><td className="number-cell">24</td><td className="number-cell">{formatBytes(3481600)}</td></tr>
              <tr><td>レポートテンプレート</td><td className="number-cell">11</td><td className="number-cell">{formatBytes(831898)}</td></tr>
              <tr><td>フォント</td><td className="number-cell">6</td><td className="number-cell">{formatBytes(43229184)}</td></tr>
              <tr><td>参考資料</td><td className="number-cell">3</td><td className="number-cell">{formatBytes(12933120)}</td></tr>
            </tbody>
          </table>
        </div>
        <p className="prop-note">容量はこの端末で計測した実サイズです（1024進・表記どおり）。</p>
      </section>
    </>
  );
}

/* ---- ショートカット: the command list editor (XC-193) ---------------------------------------- */

type ShortcutCommand = {
  name: string;
  area: string;
  key: string | null; // null = destructive - refused a binding at registration (XC-193)
  confirmPath?: string;
};

const KEYMAPS: { scope: string; note: string; commands: ShortcutCommand[] }[] = [
  {
    scope: "グローバル",
    note: "全領域で同じキー。領域キーマップが同じキーを持つときはそちらが優先し、解決結果をこの一覧に示します。",
    commands: [
      { name: "指示バーへフォーカス", area: "全領域", key: "Ctrl + K" },
      { name: "ワークスペースを保存", area: "全領域", key: "Ctrl + S" },
      { name: "左サイドバーの表示切替", area: "全領域", key: "Ctrl + B" },
      { name: "右サイドバーの表示切替", area: "全領域", key: "Ctrl + Alt + B" },
    ],
  },
  {
    scope: "ケースツリー",
    note: "検索は常設の入力欄で、ダイアログではありません。",
    commands: [
      { name: "ケースを上下に移動", area: "ケースツリー", key: "↑ / ↓" },
      { name: "ケースを折りたたむ・展開する", area: "ケースツリー", key: "← / →" },
      { name: "ケースを文字入力で検索", area: "ケースツリー", key: "文字キー" },
    ],
  },
  {
    scope: "ビュー",
    note: "変形表示の切替があるからこそ、倍率は常に描き込まれます（INV-024）。",
    commands: [
      { name: "全体を表示", area: "ビュー", key: "F" },
      { name: "変形倍率を1.0と設定値で切替", area: "ビュー", key: "D" },
      { name: "カーソル位置をプローブ", area: "ビュー", key: "P" },
      { name: "プローブ値を変数として保持", area: "ビュー", key: "Ctrl + P" },
    ],
  },
  {
    scope: "結果軸",
    note: "軸が時刻・モード・周波数のいずれでも同じキーです（XC-131）。",
    commands: [
      { name: "再生／一時停止", area: "結果軸", key: "Space" },
      { name: "前へ／次へ", area: "結果軸", key: "← / →" },
    ],
  },
  {
    scope: "破壊的な操作",
    note: "単一キーの割り当ては登録時に拒否されます。確認を経由してのみ実行できます（XC-193・XC-094）。",
    commands: [
      { name: "ケースを削除", area: "全領域", key: null, confirmPath: "影響するケース数を示す確認から実行" },
      { name: "対象集合をクリア", area: "全領域", key: null, confirmPath: "対象範囲を示す確認から実行" },
      { name: "破壊的パイプラインユニットを実行", area: "自動化", key: null, confirmPath: "影響範囲の確認から実行" },
    ],
  },
];

const MODIFIER_KEYS = ["Control", "Shift", "Alt", "Meta"];

function ShortcutsPanel() {
  const [query, setQuery] = useState("");
  // One pre-existing user change, so 変更済み and 既定に戻す are visible states, not hypotheses.
  const [overrides, setOverrides] = useState<Record<string, string>>({
    "変形倍率を1.0と設定値で切替": "Shift + D",
  });
  const [capturing, setCapturing] = useState<string | null>(null);
  const [confirmRestoreAll, setConfirmRestoreAll] = useState(false);

  const needle = query.trim();
  const resolvedKey = (command: ShortcutCommand): string | null => overrides[command.name] ?? command.key;
  const matches = (command: ShortcutCommand): boolean => {
    if (needle === "") return true;
    const key = resolvedKey(command);
    return (
      command.name.includes(needle) ||
      (key !== null && key.toLowerCase().includes(needle.toLowerCase()))
    );
  };
  const groups = KEYMAPS
    .map((keymap) => ({ ...keymap, commands: keymap.commands.filter(matches) }))
    .filter((keymap) => keymap.commands.length > 0);
  const changedNames = Object.keys(overrides);

  const captureKey = (name: string) => (event: KeyboardEvent<HTMLButtonElement>) => {
    event.preventDefault();
    if (event.key === "Escape") {
      setCapturing(null);
      return;
    }
    if (MODIFIER_KEYS.includes(event.key)) return; // wait for the non-modifier key
    const mods = [
      event.ctrlKey ? "Ctrl" : null,
      event.altKey ? "Alt" : null,
      event.shiftKey ? "Shift" : null,
    ].filter((one): one is string => one !== null);
    const label = event.key.length === 1 ? event.key.toUpperCase() : event.key;
    setOverrides({ ...overrides, [name]: [...mods, label].join(" + ") });
    setCapturing(null);
  };

  return (
    <>
      <p className="se-lead">
        同じ操作はどのモードでも同じキーです。モードが変わるのは対象ではなく道具です。
        キーの解決結果は領域ごとのキーマップから求め、この一覧に示します（XC-193）。
      </p>

      <div className="se-shortcut-toolbar">
        <input
          className="field-input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="コマンド名またはキーで検索（例：ケース、Ctrl）"
          aria-label="コマンドを検索"
        />
        <button
          className="btn ghost"
          {...(changedNames.length > 0
            ? { disabled: false }
            : disabledBecause("変更された割り当てがありません"))}
          onClick={() => setConfirmRestoreAll(true)}
        >
          すべて既定に戻す…
        </button>
        <button className="btn ghost" title="キーマップ一式をファイルとして保存します">スキームを書き出し…</button>
        <button className="btn ghost" title="キーマップ一式をファイルから読み込みます">スキームを読み込み…</button>
      </div>

      {groups.length === 0 ? (
        <div className="se-empty" role="status">
          <b>「{needle}」に一致するコマンドはありません</b>
          <p>コマンド名の一部（例：ケース）またはキー（例：Ctrl）で検索できます。</p>
        </div>
      ) : (
        groups.map((keymap) => (
          <section className="se-shortcut-group" key={keymap.scope}>
            <header>
              <b>{keymap.scope}</b>
              <small>{keymap.note}</small>
            </header>
            {keymap.commands.map((command) => (
              <div className="se-shortcut-row" key={command.name}>
                <span className="se-cmd">
                  <b>{command.name}</b>
                  <small>{command.area}</small>
                </span>
                {command.key === null ? (
                  <span className="se-nokey">
                    キーなし
                    <small>{command.confirmPath}</small>
                  </span>
                ) : capturing === command.name ? (
                  <button
                    className="se-capture"
                    autoFocus
                    onKeyDown={captureKey(command.name)}
                    onBlur={() => setCapturing(null)}
                  >
                    キーを押してください… <small>Esc で取消</small>
                  </button>
                ) : (
                  <span className="se-key">
                    <kbd className="se-kbd">{resolvedKey(command)}</kbd>
                    {overrides[command.name] !== undefined ? (
                      <em className="se-changed">変更済み（既定：{command.key}）</em>
                    ) : null}
                  </span>
                )}
                <span className="se-row-actions">
                  {command.key === null ? (
                    <button
                      className="btn ghost"
                      {...disabledBecause("破壊的コマンドへの割り当ては登録時に拒否されます（XC-193）")}
                    >
                      変更
                    </button>
                  ) : capturing === command.name ? null : (
                    <>
                      <button className="btn ghost" onClick={() => setCapturing(command.name)}>変更</button>
                      {overrides[command.name] !== undefined ? (
                        <button
                          className="btn ghost"
                          onClick={() => {
                            const next = { ...overrides };
                            delete next[command.name];
                            setOverrides(next);
                          }}
                        >
                          既定に戻す
                        </button>
                      ) : null}
                    </>
                  )}
                </span>
              </div>
            ))}
          </section>
        ))
      )}

      <section className="se-section">
        <h3>コマンド衝突</h3>
        <p className="prop-note">
          起動時とこの画面で列挙します。定義順では解決しません - どちらかを変更するまで、両方を挙げたままにします。
        </p>
        <div className="notice warn">
          <b>1つのキーに2つのコマンド - ビュー スコープの H</b>
          <span className="why">
            「表示・非表示を切り替え」と「ハイライトを保持」の両方に割り当てられています。ビュー内では後勝ちにせず、どちらも実行しません。
          </span>
        </div>
        <div className="notice warn">
          <b>1つのコマンドに2つのキー - 「全体を表示」</b>
          <span className="why">
            ビュー では F、グラフ では Shift + F。動作は同じですが、学習を妨げるため差異として列挙します。
          </span>
        </div>
      </section>

      {confirmRestoreAll ? (
        <ScopeConfirmation
          operation="ショートカットをすべて既定に戻す"
          affected={changedNames.map((name) => `${name} - 既定へ戻します`)}
          onAccept={() => {
            setOverrides({});
            setConfirmRestoreAll(false);
          }}
          onCancel={() => setConfirmRestoreAll(false)}
        />
      ) : null}
    </>
  );
}

/* ---- 診断: local logs, and the support bundle listed before it exists (XC-055b) -------------- */

const BUNDLE_INCLUDED: { name: string; detail: string; bytes: number | null }[] = [
  { name: "アプリログ（直近7日）", detail: "操作と失敗理由コードのみ - フィールド値・形状を含みません", bytes: 2516582 },
  { name: "製品版とビルド識別子", detail: "r1 プロトタイプ・ビルド 2026-08-27", bytes: 1189 },
  { name: "設定（鍵を除く）", detail: "資格情報ストアの鍵は収録対象外です", bytes: 19034 },
  { name: "失敗理由コードの一覧", detail: "直近の拒否・失敗の理由コードのみ", bytes: 3172 },
  { name: "環境情報（OS・GPU・メモリ）", detail: "収集が完了するまでサイズは示しません", bytes: null },
];

const BUNDLE_REVIEW: { id: string; name: string; detail: string; sample: string }[] = [
  {
    id: "case-names",
    name: "ケース名の一覧（12件）",
    detail: "名称に案件・顧客情報が含まれる場合があります",
    sample: "Run 12 強度確認、Run 11 ベースライン、荷重感度 L1〜L8 ほか",
  },
  {
    id: "input-paths",
    name: "入力ファイルのパス（4件）",
    detail: "ディレクトリ名に案件名が含まれる場合があります",
    sample: "D:\\projects\\2026-04\\bracket\\run12.vtu ほか3件",
  },
];

const BUNDLE_EXCLUDED = ["形状・メッシュ", "フィールド値・測定値", "参考資料の本文", "資格情報ストアの鍵"];

const LOG_DIR = "%LOCALAPPDATA%\\SOLVIA\\logs";

function DiagnosticsPanel({ openBundle }: { openBundle: boolean }) {
  const [bundleOpen, setBundleOpen] = useState(openBundle);
  const [includeCaseNames, setIncludeCaseNames] = useState(false);
  const [includeInputPaths, setIncludeInputPaths] = useState(false);
  const [createdTo, setCreatedTo] = useState<string | null>(null);

  return (
    <>
      <p className="se-lead">
        ログはこの端末に残り、フィールド値を含めません。サポートバンドルは内容の一覧を確認してから作成し、
        端末を離れるのは明示的な送信操作だけです（XC-055b）。
      </p>

      {createdTo !== null ? (
        <p className="notice good">
          <b>サポートバンドルを作成しました</b>
          <span className="why">
            保存先：{createdTo} - 送信していません。送信は別操作で、送信先と内容を監査に記録します（XC-126）。
          </span>
        </p>
      ) : null}

      <section className="se-section">
        <h3>ローカルログ</h3>
        <div className="se-field-grid">
          <span className="se-field-label">場所</span>
          <span className="se-path" title={LOG_DIR}>{LOG_DIR}</span>
          <span className="se-field-label">容量</span>
          <span>{formatBytes(2516582)}（7日で入れ替え）</span>
          <span className="se-field-label">収録内容</span>
          <span>操作・失敗理由コード - フィールド値なし</span>
        </div>
      </section>

      <section className="se-section">
        <h3>サポートバンドル</h3>
        <button className="se-action" onClick={() => setBundleOpen(true)}>
          <b>サポートバンドルを作成…</b>
          <small>内容の一覧を確認してからローカルに保存します</small>
        </button>
        <button className="se-action">
          <b>ローカルログを開く</b>
          <small>既定のフォルダで開きます - 外部送信なし</small>
        </button>
      </section>

      {bundleOpen ? (
        <div className="dialog-scrim" role="dialog" aria-modal="true" aria-label="サポートバンドルの内容確認">
          <div className="dialog">
            <header>
              <h2>サポートバンドルの内容 - 作成前の確認</h2>
            </header>
            <div className="body">
              <p className="se-group-label">含める（常に）</p>
              <div className="se-manifest">
                {BUNDLE_INCLUDED.map((item) => (
                  <div className="se-manifest-row" key={item.name}>
                    <b>{item.name}</b>
                    {item.bytes === null ? (
                      <span className="se-loading"><span className="se-spinner" aria-hidden="true" />収集中…</span>
                    ) : (
                      <span className="se-manifest-size">{formatBytes(item.bytes)}</span>
                    )}
                    <small>{item.detail}</small>
                  </div>
                ))}
              </div>

              <p className="se-group-label">確認が必要（既定では含めません）</p>
              <div>
                {BUNDLE_REVIEW.map((item) => (
                  <label className="se-check-row" key={item.id}>
                    <input
                      type="checkbox"
                      checked={item.id === "case-names" ? includeCaseNames : includeInputPaths}
                      onChange={(event) => {
                        if (item.id === "case-names") setIncludeCaseNames(event.target.checked);
                        else setIncludeInputPaths(event.target.checked);
                      }}
                    />
                    <span className="se-check-body">
                      <b>{item.name}</b>
                      <small>{item.detail}</small>
                      <span className="se-path" title={item.sample}>{item.sample}</span>
                    </span>
                  </label>
                ))}
              </div>

              <p className="se-group-label">含めない（顧客データ）</p>
              <div className="se-manifest">
                {BUNDLE_EXCLUDED.map((name) => (
                  <div className="se-manifest-row" key={name}>
                    <b>{name}</b>
                    <span className="se-manifest-size">収録しません</span>
                  </div>
                ))}
              </div>

              <p className="prop-note">
                作成先はローカルです。送信は別操作で、送信先と内容を再確認し、ローカル監査に記録します（XC-126）。
              </p>
            </div>
            <footer>
              <button className="btn ghost" onClick={() => setBundleOpen(false)}>キャンセル - 何も作成しません</button>
              <button
                className="btn primary"
                onClick={() => {
                  submit({
                    operation: "system.supportBundle",
                    parameters: { caseNames: includeCaseNames, inputPaths: includeInputPaths },
                  });
                  setCreatedTo("C:\\Users\\eng-04\\Documents\\solvia-support-2026-08-29.zip");
                  setBundleOpen(false);
                }}
              >
                ローカルに作成
              </button>
            </footer>
          </div>
        </div>
      ) : null}
    </>
  );
}
