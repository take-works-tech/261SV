/* Information (16_application_model 7.10): what the loaded file actually contains, readable at any
 * time - the specified-but-missing surface, given its screen here. Read-only: nothing editable,
 * nothing inferred. Sections follow the element inventory: ファイル (paths, reader, support level,
 * import, checksum), 構造 (counts, cell types, canonical-frame bounds, blocks), フィールド (the
 * per-field table), 座標 (declared frame and its resolution), 結果軸 (axis kind and positions).
 * Variants: default = verified-tier reader; empty = nothing loaded, no invented structure;
 * limited = offered-tier reader with the reader's known gaps named at load (XC-049). */
import { useState } from "react";
import { session, useSession } from "../../state/session";
import { submit } from "../../client/operations";
import { NumberCell } from "../../shared/NumberCell";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { QuantityChip } from "../../shared/QuantityChip";
import { UnitLabel } from "../../shared/UnitLabel";
import { UnresolvedList } from "../../shared/UnresolvedList";
import { disabledBecause, formatBytes, formatValue } from "../../logic/format";
import "./information.css";

/* ---- the two illustrative datasets (design states, not evidence of behaviour) --------------- */

type SupportTier = "verified" | "offered";
type FileEntry = { name: string; role: string; bytes: number };
type CellType = { label: string; count: number };
type Bound = { axis: string; min: number; max: number };
type BlockRow = { name: string; kind: string; count: number; countUnit: string; bytes: number };
type FieldRange = { min: number; max: number; digits: number } | { missingBecause: string };
type FieldMissing = { count: number; why?: string } | { missingBecause: string };
type FieldInfo = {
  name: string; // exactly as authored in the file - never renamed, never translated
  association: "節点" | "要素" | "積分点";
  components: string;
  unit: string | null; // null = the user has not declared one; nothing is inferred (XC-003)
  range: FieldRange;
  missing: FieldMissing;
};

type DatasetInfo = {
  id: string;
  fileName: string;
  format: string;
  tier: SupportTier;
  tierNote: string;
  dir: string;
  files: FileEntry[];
  reader: string;
  readerVersion: string;
  importedAt: string;
  importNote: string;
  sha256: string;
  gaps: { what: string; missing: string }[];
  cells: number;
  points: number;
  cellTypes: CellType[];
  bounds: Bound[];
  boundsNote: string;
  blocks: BlockRow[];
  fields: FieldInfo[];
  fieldsNote: string;
  frameDeclared: string;
  frameResolved: string;
  axisKind: string;
  axisPositions: number;
  axisStart: number;
  axisEnd: number;
  axisUnit: string;
  axisSpacing: string;
};

const VERIFIED: DatasetInfo = {
  id: "ds-run12-bracket",
  fileName: "bracket.case",
  format: "EnSight Gold",
  tier: "verified",
  tierNote: "この製品の回帰テストが実ファイルを開き、値を検証しています。",
  dir: "D:\\data\\bracket-2026\\run-012\\",
  files: [
    { name: "bracket.case", role: "定義", bytes: 2154 },
    { name: "bracket.geo", role: "形状", bytes: 58_252_416 },
    { name: "bracket.dis", role: "変位・節点", bytes: 1_003_510_744 },
    { name: "bracket.svm", role: "相当応力・要素", bytes: 313_319_424 },
    { name: "bracket.tmp", role: "温度・節点", bytes: 334_534_248 },
    { name: "bracket.pla", role: "塑性ひずみ・積分点", bytes: 2_151_759_872 },
    { name: "bracket.cpr", role: "接触圧・要素", bytes: 313_319_424 },
  ],
  reader: "vtkEnSightGoldBinaryReader",
  readerVersion: "VTK 9.5.2",
  importedAt: "2026-08-29 09:14",
  importNote: "所要 42.6 秒・元ファイルは変更していません",
  sha256: "9f3c1a58b2e4d7c6a01f4e8b23d95c7e6b1a0d4f8c2e5a793b6d0c1f4a8e2b57",
  gaps: [],
  cells: 1_284_096,
  points: 1_371_042,
  cellTypes: [
    { label: "六面体（hexa8）", count: 1_102_336 },
    { label: "四面体（tetra4）", count: 96_512 },
    { label: "五面体（penta6）", count: 85_248 },
  ],
  bounds: [
    { axis: "X", min: -0.125, max: 0.3475 },
    { axis: "Y", min: -0.08, max: 0.08 },
    { axis: "Z", min: 0, max: 0.21 },
  ],
  boundsNote:
    "宣言単位 mm から取込時に ×0.001 で換算。形状は元ファイルの精度に関わらず float64 で保持されます（E-142）。",
  blocks: [
    { name: "solid", kind: "体積・六面体", count: 1_102_336, countUnit: "セル", bytes: 2_791_728_742 },
    { name: "fillet", kind: "体積・四面体", count: 96_512, countUnit: "セル", bytes: 156_237_824 },
    { name: "bolts", kind: "体積・五面体", count: 85_248, countUnit: "セル", bytes: 178_956_970 },
  ],
  fields: [
    {
      name: "displacement", association: "節点", components: "3（X・Y・Z）", unit: "mm",
      range: { min: 0, max: 3.742, digits: 4 }, missing: { count: 0 },
    },
    {
      name: "stress_von_mises", association: "要素", components: "1", unit: "MPa",
      range: { min: 12.43, max: 241.7, digits: 4 }, missing: { count: 0 },
    },
    {
      name: "temperature", association: "節点", components: "1", unit: null,
      range: { min: 293.1, max: 361.8, digits: 4 }, missing: { count: 0 },
    },
    {
      name: "plastic_strain", association: "積分点", components: "1", unit: null,
      range: { missingBecause: "この結果位置では未保存 — 10 位置ごとに出力" },
      missing: { missingBecause: "配列がこの位置に無いため集計できません" },
    },
    {
      name: "contact_pressure", association: "要素", components: "1", unit: "MPa",
      range: { min: 0, max: 87.31, digits: 4 },
      missing: { count: 1_265_792, why: "接触面以外は値を持たない" },
    },
  ],
  fieldsNote: "変位の範囲は成分の合成（ノルム）です。",
  frameDeclared: "直交（右手系）・長さ mm — 利用者が取込時に宣言",
  frameResolved: "正準フレーム（m・右手系）へ ×0.001 — 回転なし・並進なし",
  axisKind: "時間",
  axisPositions: 61,
  axisStart: 0,
  axisEnd: 0.06,
  axisUnit: "s",
  axisSpacing: "等間隔 1 ms（保存された位置のみ）",
};

const LIMITED: DatasetInfo = {
  id: "ds-run12-manifold",
  fileName: "case.foam",
  format: "OpenFOAM",
  tier: "offered",
  tierNote: "ParaView と同じリーダーで開いています。リーダー既知の欠落は下に名指しされます。",
  dir: "D:\\data\\manifold-cfd\\run-034\\",
  files: [
    { name: "case.foam", role: "リーダー起動用（空）", bytes: 0 },
    { name: "constant/polyMesh/", role: "形状（メッシュ）", bytes: 1_287_913_472 },
    { name: "0 … 1.2（121 時刻ディレクトリ）", role: "時刻別フィールド", bytes: 3_657_433_088 },
  ],
  reader: "vtkOpenFOAMReader",
  readerVersion: "VTK 9.5.2",
  importedAt: "2026-08-29 10:41",
  importNote: "所要 96.2 秒・元ファイルは変更していません",
  sha256: "4e7b0d2a91c85f36b0e6d4a2c7f19e8350a6c1b4d9e2f7a08c3b5d6e1f4a2c90",
  gaps: [
    { what: "ラグランジアン粒子（cloud）", missing: "一部のフィールド型をこのリーダーは読み込みません — 粒子データは表示されません" },
    { what: "境界条件の型情報", missing: "値のみ保持され、型（fixedValue など）は失われます" },
    { what: "collated 並列書式", missing: "未対応 — decomposed 形式へ再構成してから取り込みます" },
  ],
  cells: 2_413_568,
  points: 2_650_112,
  cellTypes: [
    { label: "六面体", count: 1_894_336 },
    { label: "多面体", count: 312_447 },
    { label: "四面体", count: 206_785 },
  ],
  bounds: [
    { axis: "X", min: -0.42, max: 0.42 },
    { axis: "Y", min: -0.15, max: 0.15 },
    { axis: "Z", min: 0, max: 0.68 },
  ],
  boundsNote: "宣言単位 m — 換算なし（×1）。形状は float64 で保持されます（E-142）。",
  blocks: [
    { name: "internalMesh", kind: "内部メッシュ", count: 2_413_568, countUnit: "セル", bytes: 2_791_728_742 },
    { name: "inlet", kind: "境界パッチ", count: 4_832, countUnit: "面", bytes: 2_212_454 },
    { name: "outlet", kind: "境界パッチ", count: 4_832, countUnit: "面", bytes: 2_212_454 },
    { name: "walls", kind: "境界パッチ", count: 211_240, countUnit: "面", bytes: 96_713_318 },
  ],
  fields: [
    {
      name: "U", association: "要素", components: "3（X・Y・Z）", unit: "m/s",
      range: { min: 0, max: 24.68, digits: 4 }, missing: { count: 0 },
    },
    {
      name: "p", association: "要素", components: "1", unit: null,
      range: { min: -214.6, max: 892.4, digits: 4 }, missing: { count: 0 },
    },
    {
      name: "k", association: "要素", components: "1", unit: null,
      range: { min: 0.0012, max: 18.42, digits: 4 }, missing: { count: 0 },
    },
    {
      name: "nut", association: "要素", components: "1", unit: null,
      range: { min: 0, max: 0.0342, digits: 4 }, missing: { count: 0 },
    },
  ],
  fieldsNote:
    "OpenFOAM の dimensions 記述は単位として扱いません（XC-003）— m/s は利用者の宣言です。読めなかった項目はファイル欄に名指しされ、この表から黙って消えることはありません。",
  frameDeclared: "直交（右手系）・長さ m — 利用者が取込時に宣言",
  frameResolved: "正準フレーム（m・右手系）と一致 — 換算・回転・並進なし",
  axisKind: "時間",
  axisPositions: 121,
  axisStart: 0,
  axisEnd: 1.2,
  axisUnit: "s",
  axisSpacing: "等間隔 0.01 s（保存された位置のみ）",
};

/* ---- helpers -------------------------------------------------------------------------------- */

const group = (n: number) => n.toLocaleString("en-US");
const totalBytes = (info: DatasetInfo) => info.files.reduce((sum, f) => sum + f.bytes, 0);

/** The current result-axis position - session state (class 2), shown wherever a range claims it. */
function axisPosition(info: DatasetInfo, fraction: number): { index: number; t: string } {
  return {
    index: Math.round(fraction * (info.axisPositions - 1)) + 1,
    t: formatValue(fraction * info.axisEnd, 3),
  };
}

function SupportLevel({ tier }: { tier: SupportTier }) {
  return tier === "verified" ? (
    <span
      className="in-level in-verified"
      title="検証済み — この製品の回帰テストが実ファイルを開き、値を検証しています。ここでの不具合はこの製品の不具合です（XC-049）"
    >
      検証済み
    </span>
  ) : (
    <span
      className="in-level in-offered"
      title="提供 — ParaView と同じリーダーで開きます。リーダー既知の欠落は取込時に名指しされます（XC-049）"
    >
      提供（offered）
    </span>
  );
}

/* ---- sections (the inventory's five headings) ----------------------------------------------- */

function FileSection({ info }: { info: DatasetInfo }) {
  const [fullSum, setFullSum] = useState(false);
  const shownSum = fullSum ? info.sha256 : `${info.sha256.slice(0, 16)}…`;
  return (
    <section className="in-section">
      <h3>
        ファイル
        <span className="in-count">{info.files.length} ファイル・合計 {formatBytes(totalBytes(info))}</span>
      </h3>
      <div className="in-kv">
        <span className="in-k">場所</span>
        <span className="in-v"><span className="in-mono in-clip" title={info.dir}>{info.dir}</span></span>
      </div>
      <ul className="in-filelist">
        {info.files.map((f) => (
          <li key={f.name}>
            <span className="in-fname" title={f.name}>{f.name}</span>
            <span className="in-frole">{f.role}</span>
            <span className="in-fsize">{formatBytes(f.bytes)}</span>
          </li>
        ))}
      </ul>
      <div className="in-kv">
        <span className="in-k">リーダー</span>
        <span className="in-v"><span className="in-mono">{info.reader}</span>（{info.readerVersion}）</span>
      </div>
      <div className="in-kv">
        <span className="in-k">対応レベル</span>
        <span className="in-v"><SupportLevel tier={info.tier} /> {info.tierNote}</span>
      </div>
      {info.gaps.length > 0 ? (
        <>
          <UnresolvedList title="読めなかったもの（XC-049 — リーダー既知の欠落）" items={info.gaps} />
          <div className="in-actions">
            <button
              className="btn"
              {...disabledBecause("提供（offered）段のリーダーに実装が無いため取り込めません — XC-049")}
            >
              欠落項目を取り込む
            </button>
          </div>
          <p className="in-note">無効：提供（offered）段のリーダーに実装が無いため、名指しした項目は取り込めません。</p>
        </>
      ) : null}
      <div className="in-kv">
        <span className="in-k">取込</span>
        <span className="in-v">{info.importedAt}（{info.importNote}）</span>
      </div>
      <div className="in-kv">
        <span className="in-k">SHA-256</span>
        <span className="in-v"><span className="in-mono" title={info.sha256}>{shownSum}</span></span>
      </div>
      <div className="in-actions">
        <button className="btn ghost" onClick={() => setFullSum(!fullSum)}>
          {fullSum ? "先頭 16 桁のみ表示" : "全 64 桁を表示"}
        </button>
        <button
          className="btn ghost"
          title="取込時の値と現在のファイルを照合します — 元ファイルは変更しません"
          onClick={() => submit({ operation: "dataset.describe", parameters: { dataset: info.id, verify: "sha-256" } })}
        >
          チェックサムを照合
        </button>
      </div>
    </section>
  );
}

function StructureSection({ info }: { info: DatasetInfo }) {
  return (
    <section className="in-section">
      <h3>構造 <ProvenanceBadge origin="dataset" /></h3>
      <div className="in-kv"><span className="in-k">要素数</span><span className="in-v in-num">{group(info.cells)}</span></div>
      <div className="in-kv"><span className="in-k">節点数</span><span className="in-v in-num">{group(info.points)}</span></div>
      <div className="in-kv">
        <span className="in-k">セル種別</span>
        <span className="in-v">{info.cellTypes.map((c) => `${c.label} ${group(c.count)}`).join("・")}</span>
      </div>
      <div className="in-kv">
        <span className="in-k">範囲（正準フレーム）</span>
        <span className="in-v"><UnitLabel unit="m" /> <ProvenanceBadge origin="computed" /></span>
      </div>
      {info.bounds.map((b) => (
        <div className="in-kv" key={b.axis}>
          <span className="in-k">　{b.axis}</span>
          <span className="in-v in-num">{formatValue(b.min, 4)} … {formatValue(b.max, 4)}</span>
        </div>
      ))}
      <p className="in-note">{info.boundsNote}</p>
      <div className="table-scroll">
        <table className="value-table in-blocks">
          <thead>
            <tr><th>ブロック</th><th>種別</th><th>数</th><th>大きさ（読込後）</th></tr>
          </thead>
          <tbody>
            {info.blocks.map((b) => (
              <tr key={b.name}>
                <td><span className="in-mono">{b.name}</span></td>
                <td>{b.kind}</td>
                <NumberCell value={`${group(b.count)} ${b.countUnit}`} />
                <NumberCell value={formatBytes(b.bytes)} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FieldsSection({ info, pos }: { info: DatasetInfo; pos: { index: number; t: string } }) {
  return (
    <section className="in-section in-span">
      <h3>
        フィールド
        <span className="in-count">{info.fields.length} フィールド</span>
      </h3>
      <div className="table-scroll">
        <table className="value-table in-fields">
          <thead>
            <tr>
              <th>名称（原資料のまま）</th>
              <th>関連</th>
              <th>成分</th>
              <th>宣言単位</th>
              <th>実測範囲（現在位置） <ProvenanceBadge origin="measured" /></th>
              <th>欠損値数</th>
            </tr>
          </thead>
          <tbody>
            {info.fields.map((f) => (
              <tr key={f.name}>
                <td><span className="in-mono">{f.name}</span></td>
                <td>{f.association}</td>
                <td>{f.components}</td>
                <td>
                  {f.unit !== null
                    ? <><UnitLabel unit={f.unit} /> <ProvenanceBadge origin="declared" /></>
                    : <UnitLabel unit={null} />}
                </td>
                {"min" in f.range ? (
                  <NumberCell
                    value={`${formatValue(f.range.min, f.range.digits)} … ${formatValue(f.range.max, f.range.digits)}`}
                  />
                ) : (
                  <NumberCell value={null} missingBecause={f.range.missingBecause} />
                )}
                {"count" in f.missing ? (
                  <NumberCell
                    value={f.missing.why !== undefined ? `${group(f.missing.count)}（${f.missing.why}）` : group(f.missing.count)}
                  />
                ) : (
                  <NumberCell value={null} missingBecause={f.missing.missingBecause} />
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="in-note">
        実測範囲は現在の結果位置 t = {pos.t} {info.axisUnit}（{pos.index}/{info.axisPositions}）における値で、
        表示用の縮退形状ではなく全データを正準フレームで集計したものです（INV-001／INV-009）。
        桁は原資料が支える分のみ表示します（INV-014）。{info.fieldsNote}
      </p>
    </section>
  );
}

function FrameSection({ info }: { info: DatasetInfo }) {
  return (
    <section className="in-section">
      <h3>座標</h3>
      <div className="in-kv">
        <span className="in-k">宣言フレーム</span>
        <span className="in-v">{info.frameDeclared} <ProvenanceBadge origin="declared" /></span>
      </div>
      <div className="in-kv">
        <span className="in-k">解決</span>
        <span className="in-v">{info.frameResolved} <ProvenanceBadge origin="computed" /></span>
      </div>
      <p className="in-note">座標系も単位もファイルからは推定しません（XC-003）— 宣言が無ければ未宣言と表示されます。</p>
    </section>
  );
}

function AxisSection({ info, pos }: { info: DatasetInfo; pos: { index: number; t: string } }) {
  return (
    <section className="in-section">
      <h3>結果軸 <ProvenanceBadge origin="dataset" /></h3>
      <div className="in-kv"><span className="in-k">種類</span><span className="in-v">{info.axisKind}</span></div>
      <div className="in-kv"><span className="in-k">位置数</span><span className="in-v in-num">{group(info.axisPositions)}</span></div>
      <div className="in-kv">
        <span className="in-k">範囲</span>
        <span className="in-v">
          <QuantityChip
            value={`${formatValue(info.axisStart, 3)} … ${formatValue(info.axisEnd, 3)}`}
            unit={info.axisUnit}
          />
        </span>
      </div>
      <div className="in-kv"><span className="in-k">保存間隔</span><span className="in-v">{info.axisSpacing}</span></div>
      <div className="in-kv">
        <span className="in-k">現在位置</span>
        <span className="in-v">
          <QuantityChip value={pos.t} unit={info.axisUnit} title="セッション状態 — 結果軸オーバーレイで移動します" />
          （{pos.index}/{info.axisPositions}）
        </span>
      </div>
      <p className="in-note">保存位置以外の時刻は存在しません — 丸めも補間もしません（view/AC-033）。</p>
    </section>
  );
}

/* ---- the screen ----------------------------------------------------------------------------- */

export function InformationScreen(props: { variant: string }) {
  const s = useSession();

  if (props.variant === "empty") {
    return (
      <div className="in-root">
        <div className="empty-state">
          <h2>未読込</h2>
          <p>
            この画面は、読み込んだファイルが実際に何を含むか — 構造・フィールド・座標・結果軸 —
            をいつでも読める場所です。まだ何も読み込まれていないため、示せる中身はありません。
            見本の構造は発明しません。
          </p>
          <div className="actions">
            <button className="btn primary" onClick={() => session.navigate("home")}>
              ホームでファイルを読み込む
            </button>
          </div>
        </div>
        <footer className="in-footer">
          <span className="in-clip">何も読み込まれていません — 表示できる中身はありません。</span>
        </footer>
      </div>
    );
  }

  const info = props.variant === "limited" ? LIMITED : VERIFIED;
  const pos = axisPosition(info, s.resultPosition);
  const footer =
    `表示中：Run 12 — ${info.fileName}（${info.format}・${info.tier === "verified" ? "検証済み" : "提供段"}）。` +
    `実測範囲は現在の結果位置 t = ${pos.t} ${info.axisUnit} のもの。` +
    (info.gaps.length > 0 ? `読めなかった ${info.gaps.length} 項目を名指ししています（XC-049）。` : "") +
    "この画面は読み取り専用です。";

  return (
    <div className="in-root">
      <div className="in-scroll">
        <div className="in-grid">
          <header className="in-header">
            <span className="in-file" title={`${info.dir}${info.fileName}`}>{info.fileName}</span>
            <span className="in-sub">{info.format}・ケース Run 12</span>
            <SupportLevel tier={info.tier} />
            <span className="in-right">
              <QuantityChip
                value={pos.t}
                unit={info.axisUnit}
                title={`現在の結果位置（${pos.index}/${info.axisPositions}）— セッション状態`}
              />
              <span className="in-readonly" title="この画面は読み込んだ内容を表示するだけで、何も編集しません">
                読み取り専用
              </span>
            </span>
          </header>
          <FileSection info={info} />
          <StructureSection info={info} />
          <FieldsSection info={info} pos={pos} />
          <FrameSection info={info} />
          <AxisSection info={info} pos={pos} />
        </div>
      </div>
      <footer className="in-footer">
        <span className="in-clip" title={footer}>{footer}</span>
      </footer>
    </div>
  );
}

/* ---- the rail: file summary ------------------------------------------------------------------ */

export function InformationRail(props: { tab: string; variant: string }) {
  // The information area declares a single rail tab (ファイル); `tab` stays in the contract shape.
  if (props.variant === "empty") {
    return (
      <div className="prop-section">
        <h3>ファイル</h3>
        <p className="prop-note">
          読み込み済みのファイルはありません。読み込むと、元ファイルの要約 —
          形式、対応レベル、大きさ、チェックサム — がここに表示されます。
        </p>
        <div className="in-actions">
          <button className="btn" onClick={() => session.navigate("home")}>ホームでファイルを読み込む</button>
        </div>
      </div>
    );
  }

  const info = props.variant === "limited" ? LIMITED : VERIFIED;
  return (
    <>
      <div className="prop-section">
        <h3>ファイル</h3>
        <div className="prop-row"><label>名称</label><span className="in-mono in-clip" title={info.fileName}>{info.fileName}</span></div>
        <div className="prop-row"><label>形式</label><span>{info.format}</span></div>
        <div className="prop-row"><label>対応レベル</label><span><SupportLevel tier={info.tier} /></span></div>
        <div className="prop-row">
          <label>リーダー</label>
          <span className="in-mono in-clip" title={`${info.reader}（${info.readerVersion}）`}>{info.reader}</span>
        </div>
        <div className="prop-row"><label>構成</label><span>{info.files.length} ファイル・{formatBytes(totalBytes(info))}</span></div>
      </div>
      <div className="prop-section">
        <h3>内容の要約</h3>
        <div className="prop-row"><label>要素数</label><span>{group(info.cells)}</span></div>
        <div className="prop-row"><label>節点数</label><span>{group(info.points)}</span></div>
        <div className="prop-row"><label>フィールド</label><span>{info.fields.length}</span></div>
        <div className="prop-row"><label>結果軸</label><span>{info.axisKind}・{group(info.axisPositions)} 位置</span></div>
        <div className="prop-row"><label>取込</label><span>{info.importedAt}</span></div>
        <div className="prop-row">
          <label>SHA-256</label>
          <span className="in-mono in-clip" title={info.sha256}>{info.sha256.slice(0, 16)}…</span>
        </div>
      </div>
      {info.gaps.length > 0 ? (
        <div className="prop-section">
          <div className="notice warn">
            <b>読めなかった項目 {info.gaps.length} 件</b>
            <span className="why">提供（offered）段のリーダーによる取込 — 本文のファイル欄に名指しされています（XC-049）。</span>
          </div>
        </div>
      ) : null}
      <div className="prop-section">
        <p className="prop-note">
          この画面は読み取り専用です — 値の編集も推定もしません。単位の宣言は設定で、位置の移動は結果軸で行います。
        </p>
      </div>
    </>
  );
}
