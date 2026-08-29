/* Diff (差分) - the difference of two cases as a quantity like any other, with its honesty rules
 * kept visible (16_application_model §7.9).
 *
 * The three disclosures - resampling direction, points outside the target, round-trip error - are
 * one grid with the result and cannot be separated from it (XC-038); a point the resampling could
 * not reach stays 値なし, never 0 (INV-011, XC-001). The resample target is chosen by the user and
 * never defaulted; the matching basis is recorded because array position on differing meshes is a
 * different number (INV-023). Two sides declaring different units refuse, naming both (INV-002),
 * and nothing converts by guesswork (XC-003). A difference of nearly equal values shows the digits
 * the subtraction left, not the digits its storage holds (INV-034).
 *
 * Variants: default (Run 12 − Run 11 computed), method (nothing computed - the choices and the
 * refusals), unresolved (a quantity present on one side only - named, no diff computed). */
import { useState } from "react";
import "./DiffScreen.css";
import { ViewportPlaceholder } from "../../shared/ViewportPlaceholder";
import { UnitLabel } from "../../shared/UnitLabel";
import { NumberCell } from "../../shared/NumberCell";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { MissingDataStyle } from "../../shared/MissingDataStyle";
import { UnresolvedList, type UnresolvedItem } from "../../shared/UnresolvedList";
import { FieldSelector, type FieldOption } from "../../shared/FieldSelector";
import { disabledBecause } from "../../logic/format";
import { submit } from "../../client/operations";

type DiffVariant = "default" | "method" | "unresolved";

function asVariant(variant: string): DiffVariant {
  return variant === "method" || variant === "unresolved" ? variant : "default";
}

/* Illustrative and honest (OPEN-022): every value carries unit + provenance, diff digits are the
 * digits the subtraction left (INV-034), and mesh sizes stay consistent everywhere they appear. */
const FIELDS: FieldOption[] = [
  { name: "von Mises 応力", association: "point", unit: "MPa" },
  { name: "変位量", association: "point", unit: "mm" },
  { name: "接触圧", association: "point", unit: "MPa" },
];

const SELECTED_FIELD: Record<DiffVariant, string> = {
  default: "von Mises 応力",
  method: "変位量",
  unresolved: "接触圧",
};

type DiffRow = { item: string; value: string | null; missingBecause?: string; unit: string | null; where: string };

const DIFF_ROWS: readonly DiffRow[] = [
  { item: "最大差（A − B）", value: "+18.4", unit: "MPa", where: "節点 4021（部品 bracket_arm）" },
  { item: "最小差（A − B）", value: "−12.1", unit: "MPa", where: "節点 8907（部品 base_plate）" },
  { item: "平均差", value: "+2.31", unit: "MPa", where: "対象 45,082 点（対象外 128 点を除く）" },
  { item: "RMS 差", value: "5.04", unit: "MPa", where: "対象 45,082 点（対象外 128 点を除く）" },
  { item: "対象外の点の差", value: null, missingBecause: "再標本化先（Run 12 メッシュ）の範囲外", unit: "MPa", where: "128 点（0.28 %）" },
];

type SideCell = { label: string } | { absent: string };
type QuantityRow = {
  name: string;
  a: SideCell;
  b: SideCell;
  can: true | { cannot: string };
  selected?: boolean;
};

const QUANTITY_ROWS: readonly QuantityRow[] = [
  { name: "von Mises 応力", a: { label: "節点・MPa（宣言）" }, b: { label: "節点・MPa（宣言）" }, can: true },
  { name: "変位量", a: { label: "節点・mm（宣言）" }, b: { label: "節点・mm（宣言）" }, can: true },
  { name: "接触圧", selected: true, a: { label: "節点・MPa（宣言）" }, b: { absent: "Run 11 が書き出していません" }, can: { cannot: "片側のみ" } },
  { name: "塑性ひずみ", a: { absent: "Run 12 が書き出していません" }, b: { label: "積分点・単位未宣言" }, can: { cannot: "片側のみ・単位未宣言" } },
];

/* ---------------------------------------------------------------- the screen ---- */

export function DiffScreen(props: { variant: string }) {
  const v = asVariant(props.variant);
  return (
    <div className="di-screen">
      <DefinitionStrip v={v} />
      <div className="di-result">
        <div className="di-canvas">
          {v === "default" ? <DefaultResult /> : v === "method" ? <MethodCanvas /> : <UnresolvedCanvas />}
        </div>
        {/* The disclosure column is a grid cell beside the result - XC-038's inseparability,
            drawn. While nothing is computed the three are stated absences, never hidden. */}
        <aside className="di-disclosure" aria-label="三点開示">
          <header>
            <b>三点開示</b>
            <span>XC-038 — 結果と分離できません</span>
          </header>
          <DisclosureItems computed={v === "default"} />
          <p className="di-disc-note">
            再標本化で対象の外に出た点は値なしのまま保持します — 0 での補完はしません（INV-011）。
          </p>
        </aside>
      </div>
    </div>
  );
}

function DefinitionStrip(props: { v: DiffVariant }) {
  const v = props.v;
  return (
    <div className="di-def" role="group" aria-label="差分の定義">
      <div className="di-def-item">
        <span className="k">演算</span>
        <span className="v" title="A − B をこの順で計算します">
          <b>Run 12 − Run 11</b>
          <span>（A − B・この順）</span>
        </span>
      </div>
      <div className="di-def-item">
        <span className="k">量</span>
        {v === "default" ? (
          <span className="v" title="von Mises 応力（節点・MPa・宣言）">
            <b>von Mises 応力</b>
            <span>（節点）</span>
            <UnitLabel unit="MPa" />
            <ProvenanceBadge origin="declared" />
          </span>
        ) : v === "method" ? (
          <span className="v" title="変位量 — 宣言単位が競合（Run 12: mm ／ Run 11: m）">
            <b>変位量</b>
            <span>（節点）</span>
            <span className="missing-value">mm ≠ m — 両方を名指し（INV-002）</span>
          </span>
        ) : (
          <span className="v" title="接触圧 — Run 11 に存在しません">
            <b>接触圧</b>
            <span>（節点）</span>
            <UnitLabel unit="MPa" />
            <span className="missing-value">Run 11 になし</span>
          </span>
        )}
      </div>
      <div className="di-def-item">
        <span className="k">成分フレーム</span>
        <span className="v" title="両ケースが同じ宣言フレームを共有します">
          <span>全体直交 XYZ（両ケースで共有）</span>
          <ProvenanceBadge origin="declared" />
        </span>
      </div>
      <div className="di-def-item">
        <span className="k">方法</span>
        <span className="v">
          {v === "default" ? (
            <span>再標本化：Run 11 → Run 12・ソース識別子</span>
          ) : v === "method" ? (
            <span className="missing-value">未確定（再標本化先が未選択）</span>
          ) : (
            <span className="missing-value">―（計算対象なし）</span>
          )}
        </span>
      </div>
    </div>
  );
}

/* ---- default: the computed signed difference ------------------------------------------------ */

function DefaultResult() {
  return (
    <>
      <ViewportPlaceholder
        caseName="Run 12 − Run 11"
        fieldLabel="Δ von Mises 応力 [MPa]"
        map="greys"
        legendTicks={["+18.4", "+9.2", "0.0", "−9.2", "−18.4"]}
      >
        <div className="pane-badge" style={{ top: "auto", bottom: 8, left: 8 }} role="note">
          符号付き差：明 = 正（Run 12 が大）・対象外 128 点は無塗色
        </div>
      </ViewportPlaceholder>
      <div className="di-table">
        <div className="di-table-title">
          <b>差の統計</b>
          <span>完全データ・正準フレームで計算 — 表示形状からは測りません（INV-001／INV-009）</span>
        </div>
        <div className="table-scroll">
          <table className="value-table">
            <thead>
              <tr>
                <th>項目</th>
                <th style={{ textAlign: "right" }}>値</th>
                <th>単位</th>
                <th>位置（ソースの言葉）</th>
                <th>由来</th>
              </tr>
            </thead>
            <tbody>
              {DIFF_ROWS.map((row) => (
                <tr key={row.item}>
                  <td>{row.item}</td>
                  <NumberCell value={row.value} missingBecause={row.missingBecause} />
                  <td><UnitLabel unit={row.unit} /></td>
                  <td>{row.where}</td>
                  <td><ProvenanceBadge origin="computed" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="di-foot">
          差の有効桁は減算が残した桁で表示します（INV-034）。対象外の 128 点は値なしのまま — 0 を置きません（INV-011／XC-001）。
        </p>
      </div>
    </>
  );
}

/* ---- method: nothing computed - the choices and the refusals -------------------------------- */

function MethodCanvas() {
  const [method, setMethod] = useState<"shared" | "resample">("resample");
  const [target, setTarget] = useState<"a" | "b" | null>(null);
  const [basis, setBasis] = useState<"source" | "array">("source");

  const items: UnresolvedItem[] = [];
  if (target === null) {
    items.push({ what: "再標本化先", missing: "利用者の選択（既定値は置きません）" });
  }
  items.push({ what: "量「変位量」の単位", missing: "一致する宣言 — Run 12: mm ／ Run 11: m（INV-002 により拒否）" });

  return (
    <div className="di-split">
      <div className="di-method-col" aria-label="方法の選択">
        <MethodForm
          scope="canvas"
          v="method"
          method={method}
          onMethod={setMethod}
          target={target}
          onTarget={setTarget}
          basis={basis}
          onBasis={setBasis}
        />
      </div>
      <div className="di-well">
        <div className="empty-state" style={{ maxWidth: 560 }}>
          <h2>差分は未計算</h2>
          <p>
            方法が確定するまで計算しません。右の三点開示は結果と同時に確定し、結果と常に併記されます（XC-038）。
          </p>
          <UnresolvedList title="未解決" items={items} />
        </div>
      </div>
    </div>
  );
}

/* ---- unresolved: a quantity present on one side only ---------------------------------------- */

function UnresolvedCanvas() {
  return (
    <>
      <div className="di-refusal">
        <UnresolvedList
          title="片側にない量（差分は計算されません）"
          items={[{
            what: "接触圧（節点・MPa・Run 12 のみ）",
            missing: "Run 11 の同名の量。差分は計算せず、0 も置きません（XC-001）",
          }]}
        />
      </div>
      <div className="di-well">
        <div className="empty-state" style={{ maxWidth: 560 }}>
          <h2>差分なし</h2>
          <p>
            「接触圧」は Run 12 にのみ存在します。片側にない量の差は数ではないため、この画面は何も描きません。下の対応表から両側にある量を選ぶと計算できます。
          </p>
        </div>
      </div>
      <div className="di-table">
        <div className="di-table-title">
          <b>両ケースの量の対応</b>
          <span>存在しない量は名指しのまま — 補完しません（XC-001）</span>
        </div>
        <div className="table-scroll">
          <table className="value-table">
            <thead>
              <tr>
                <th>量</th>
                <th>Run 12（A）</th>
                <th>Run 11（B）</th>
                <th>差分</th>
              </tr>
            </thead>
            <tbody>
              {QUANTITY_ROWS.map((row) => (
                <tr key={row.name} className={row.selected ? "di-row-selected" : undefined} aria-selected={row.selected ? true : undefined}>
                  <td>
                    <b>{row.name}</b>
                    {row.selected ? <span className="type-caption" style={{ color: "var(--ink-muted)" }}>（選択中）</span> : null}
                  </td>
                  <td><SideCellView cell={row.a} /></td>
                  <td><SideCellView cell={row.b} /></td>
                  <td>
                    {row.can === true
                      ? <span>可</span>
                      : <span className="missing-value">不可（{row.can.cannot}）</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="di-foot">
          単位未宣言の量は、差分の前に宣言が必要です — 推測による変換はしません（XC-003）。
        </p>
      </div>
    </>
  );
}

function SideCellView(props: { cell: SideCell }) {
  if ("absent" in props.cell) {
    return <span className="missing-value">なし（{props.cell.absent}）</span>;
  }
  return <span>{props.cell.label}</span>;
}

/* ---- the three disclosures (canvas column and rail tab share one implementation) ------------ */

function DisclosureItems(props: { computed: boolean }) {
  if (!props.computed) {
    return (
      <div className="di-disc-list">
        {(["再標本化の方向", "対象外の点", "往復誤差"] as const).map((k) => (
          <div key={k} className="di-disc-item">
            <span className="k">{k}</span>
            <span className="v"><MissingDataStyle because="差分未計算" /></span>
          </div>
        ))}
      </div>
    );
  }
  return (
    <div className="di-disc-list">
      <div className="di-disc-item">
        <span className="k">再標本化の方向</span>
        <span className="v">Run 11 → Run 12</span>
        <span className="n">B（Run 11・44,987 点）の値を A（Run 12・45,210 点）のメッシュへ。対応付けはソース識別子。</span>
      </div>
      <div className="di-disc-item">
        <span className="k">対象外の点</span>
        <span className="v">128 点 ／ 45,210 点（0.28 %）</span>
        <span className="n">再標本化先の外に出た点。値なしのまま保持します（INV-011）。</span>
      </div>
      <div className="di-disc-item">
        <span className="k">往復誤差</span>
        <span className="v">最大 0.42 <UnitLabel unit="MPa" /></span>
        <span className="n">A→B→A の往復再標本化から計算。<ProvenanceBadge origin="computed" /></span>
      </div>
    </div>
  );
}

/* ---- the method form (method-variant canvas and the rail's 方法 tab) ------------------------- */

type MethodFormProps = {
  scope: string; // radio-group namespace: canvas and rail render this form concurrently
  v: DiffVariant;
  method: "shared" | "resample";
  onMethod: (m: "shared" | "resample") => void;
  target: "a" | "b" | null;
  onTarget: (t: "a" | "b") => void;
  basis: "source" | "array";
  onBasis: (b: "source" | "array") => void;
};

function blockersFor(v: DiffVariant, target: "a" | "b" | null): string[] {
  const out: string[] = [];
  if (v === "method") {
    if (target === null) out.push("再標本化先が未選択（利用者が選びます）");
    out.push("宣言単位の競合（Run 12: mm ／ Run 11: m）");
  }
  if (v === "unresolved") out.push("選択中の量「接触圧」が Run 11 にありません");
  return out;
}

function MethodForm(props: MethodFormProps) {
  const sharedMeshReason = "点数が一致しません（Run 12: 45,210 点／Run 11: 44,987 点）";
  const direction =
    props.target === null
      ? null
      : props.target === "a"
        ? "Run 11 → Run 12 のメッシュ（B を A へ）"
        : "Run 12 → Run 11 のメッシュ（A を B へ）";
  const blockers = blockersFor(props.v, props.target);

  return (
    <>
      <div className="di-group" role="radiogroup" aria-label="方式">
        <h4>方式</h4>
        <label className="di-choice disabled" title={disabledBecause(sharedMeshReason).title}>
          <input
            type="radio"
            name={`${props.scope}-di-method`}
            disabled
            checked={props.method === "shared"}
            onChange={() => props.onMethod("shared")}
          />
          <span className="t">
            共有メッシュ（同一メッシュのときのみ）
            <span className="why">無効：{sharedMeshReason}</span>
          </span>
        </label>
        <label className="di-choice">
          <input
            type="radio"
            name={`${props.scope}-di-method`}
            checked={props.method === "resample"}
            onChange={() => props.onMethod("resample")}
          />
          <span className="t">
            再標本化
            <span className="why">片方の値をもう一方のメッシュへ移してから引き算します。</span>
          </span>
        </label>
      </div>

      <div className="di-group" role="radiogroup" aria-label="再標本化先">
        <h4>再標本化先</h4>
        <label className="di-choice">
          <input
            type="radio"
            name={`${props.scope}-di-target`}
            checked={props.target === "a"}
            onChange={() => props.onTarget("a")}
          />
          <span className="t">A のメッシュ（Run 12・45,210 点）</span>
        </label>
        <label className="di-choice">
          <input
            type="radio"
            name={`${props.scope}-di-target`}
            checked={props.target === "b"}
            onChange={() => props.onTarget("b")}
          />
          <span className="t">B のメッシュ（Run 11・44,987 点）</span>
        </label>
        {props.target === null ? (
          <div className="notice warn" role="status">
            <b>再標本化先が未選択です</b>
            <span className="why">再標本化先は利用者が選びます。この製品は既定値を置きません。</span>
          </div>
        ) : (
          <p className="prop-note">
            方向：{direction}。この方向は三点開示の 1 点目として結果に併記されます（XC-038）。
          </p>
        )}
      </div>

      <div className="di-group" role="radiogroup" aria-label="対応付けの基準">
        <h4>対応付けの基準</h4>
        <label className="di-choice">
          <input
            type="radio"
            name={`${props.scope}-di-basis`}
            checked={props.basis === "source"}
            onChange={() => props.onBasis("source")}
          />
          <span className="t">
            ソース識別子（推奨）
            <span className="why">元ファイルの節点 ID で対応付けます。</span>
          </span>
        </label>
        <label className="di-choice">
          <input
            type="radio"
            name={`${props.scope}-di-basis`}
            checked={props.basis === "array"}
            onChange={() => props.onBasis("array")}
          />
          <span className="t">
            配列位置
            <span className="why">同一メッシュのときだけ同じ点を指します。</span>
          </span>
        </label>
        {props.basis === "array" ? (
          <div className="notice warn" role="status">
            <b>配列位置での対応付け（INV-023）</b>
            <span className="why">異なるメッシュでは別の点を引き合わせ、違う数になります。選んだ基準は結果に記録されます。</span>
          </div>
        ) : (
          <p className="prop-note">選んだ基準は結果に記録されます（INV-023）。</p>
        )}
      </div>

      <div className="di-group">
        <h4>単位の確認</h4>
        {props.v === "method" ? (
          <div className="notice error" role="alert">
            <b>宣言単位が異なるため、この量の差分を拒否しました（INV-002）</b>
            <span className="why">
              Run 12「変位量」= mm（宣言）／ Run 11「変位量」= m（宣言）。どちらへも変換せず、両方を名指しします。単位は推測しません（XC-003）。
            </span>
          </div>
        ) : props.v === "unresolved" ? (
          <div className="notice warn" role="status">
            <b>「接触圧」は Run 11 にありません</b>
            <span className="why">片側にない量の差分は計算されません。両側にある量を選んでください。</span>
          </div>
        ) : (
          <div className="notice good" role="status">
            <b>宣言単位が一致しています</b>
            <span className="why">「von Mises 応力」= MPa（宣言）— 両ケースとも。</span>
          </div>
        )}
      </div>

      <div className="di-actions">
        {blockers.length === 0 ? (
          <button
            className="btn primary"
            onClick={() =>
              submit({
                operation: "diff.create",
                parameters: {
                  a: "run-12",
                  b: "run-11",
                  quantity: "von_mises",
                  method: props.method,
                  target: props.target,
                  basis: props.basis,
                },
              })
            }
          >
            再計算
          </button>
        ) : (
          <>
            <button className="btn primary" {...disabledBecause(blockers.join("／"))}>差分を計算</button>
            <p className="prop-note" role="status">計算できません：{blockers.join("／")}</p>
          </>
        )}
      </div>
    </>
  );
}

/* ---------------------------------------------------------------- the rail ---- */

export function DiffRail(props: { tab: string; variant: string }) {
  const v = asVariant(props.variant);
  const [caseA, setCaseA] = useState("run-12");
  const [caseB, setCaseB] = useState("run-11");
  const [fieldChoice, setFieldChoice] = useState<string | null>(null);
  const [shape, setShape] = useState<"signed" | "absolute">("signed");
  const [method, setMethod] = useState<"shared" | "resample">("resample");
  const [targetChoice, setTargetChoice] = useState<"a" | "b" | null>(null);
  const [basis, setBasis] = useState<"source" | "array">("source");

  // The variant sets the baseline; a user's change overrides it without a remount.
  const target = targetChoice ?? (v === "method" ? null : "a");
  const field = fieldChoice ?? SELECTED_FIELD[v];

  if (props.tab === "method") {
    return (
      <MethodForm
        scope="rail"
        v={v}
        method={method}
        onMethod={setMethod}
        target={target}
        onTarget={setTargetChoice}
        basis={basis}
        onBasis={setBasis}
      />
    );
  }

  if (props.tab === "disclosure") {
    return (
      <>
        <div className="prop-section">
          <h3>三点開示</h3>
          <p className="prop-note">
            再標本化の方向・対象外の点・往復誤差。三点は結果が現れるすべての場所に併記され、消せません（XC-038）。
          </p>
        </div>
        <div className="prop-section">
          <DisclosureItems computed={v === "default"} />
          {v !== "default" ? (
            <p className="prop-note">差分が計算されると同時に三点が確定します。</p>
          ) : null}
        </div>
      </>
    );
  }

  // 対象 (the default tab)
  return (
    <>
      <div className="prop-section">
        <h3>対象</h3>
        <div className="prop-row">
          <label>ケース A</label>
          <select
            className="field-input"
            value={caseA}
            onChange={(event) => setCaseA(event.target.value)}
            aria-label="ケース A"
          >
            <option value="run-12">Run 12（板厚 2.6 mm）</option>
            <option value="run-13">Run 13（板厚 2.8 mm）</option>
            <option value="run-10">Run 10（基準形状）</option>
          </select>
        </div>
        <div className="prop-row">
          <label>ケース B</label>
          <select
            className="field-input"
            value={caseB}
            onChange={(event) => setCaseB(event.target.value)}
            aria-label="ケース B"
          >
            <option value="run-11">Run 11（板厚 2.4 mm）</option>
            <option value="run-10">Run 10（基準形状）</option>
          </select>
        </div>
        <p className="prop-note">A − B をこの順で名指しします：Run 12 − Run 11。入れ替えは符号を反転させます。</p>
      </div>

      <div className="prop-section">
        <h3>量</h3>
        <div className="prop-row">
          <label>量</label>
          <FieldSelector fields={FIELDS} value={field} onChange={setFieldChoice} />
        </div>
        {v === "method" ? (
          <div className="notice error" role="alert">
            <b>宣言単位が異なります（INV-002）</b>
            <span className="why">Run 12「変位量」= mm（宣言）／ Run 11「変位量」= m（宣言）。差分は拒否されます。</span>
          </div>
        ) : null}
        {v === "unresolved" ? (
          <div className="notice warn" role="status">
            <b>「接触圧」は Run 11 にありません</b>
            <span className="why">片側にない量は名指しされ、差分は計算されません。</span>
          </div>
        ) : null}
        <div className="prop-row">
          <label>成分フレーム</label>
          <span style={{ display: "flex", alignItems: "baseline", gap: 5, minWidth: 0 }}>
            <span>全体直交 XYZ</span>
            <ProvenanceBadge origin="declared" />
          </span>
        </div>
        <p className="prop-note">両ケースが同じ宣言フレームを共有します — 差分の前提です。</p>
      </div>

      <div className="prop-section" role="radiogroup" aria-label="差の形">
        <h3>差の形</h3>
        <label className="di-choice">
          <input
            type="radio"
            name="rail-di-shape"
            checked={shape === "signed"}
            onChange={() => setShape("signed")}
          />
          <span className="t">
            符号付き（A − B）
            <span className="why">正は Run 12 が大。グレーの明暗が向きを保ちます。</span>
          </span>
        </label>
        <label className="di-choice">
          <input
            type="radio"
            name="rail-di-shape"
            checked={shape === "absolute"}
            onChange={() => setShape("absolute")}
          />
          <span className="t">
            絶対値 |A − B|
            <span className="why">向きを捨てます。凡例は 0 起点になります。</span>
          </span>
        </label>
      </div>
    </>
  );
}
