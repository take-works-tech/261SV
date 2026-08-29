/* The View screen (mockup 2): every catalogued design state of the 3D work area (XC-256).
 *
 * 45 variants, grouped: split-* force a pane count, comparison-* lay a swept grid over one axis
 * (XC-202/XC-205/XC-212), object-* select one view object and switch the rail's selection tabs,
 * library-* annotate the shelf state the shell renders. Numbers are illustrative but honest:
 * unit or the undeclared marker, provenance, digits per INV-014. A missing value is a stated
 * absence (XC-001); a rule that does not resolve refuses BY NAME and moves nothing (XC-197).
 */
import { useState, type ReactNode } from "react";
import "./view.css";
import { session, useSession } from "../../state/session";
import { submit } from "../../client/operations";
import { disabledBecause } from "../../logic/format";
import { SplitLayout } from "../../shared/SplitLayout";
import { ViewportPlaceholder } from "../../shared/ViewportPlaceholder";
import { ProbeReadout } from "../../shared/ProbeReadout";
import { Outliner, type OutlinerNode } from "../../shared/Outliner";
import { UnresolvedList } from "../../shared/UnresolvedList";
import { WorkspaceItemList } from "../../shared/WorkspaceItemList";
import { ColourMapControl, type ColourMapId } from "../../shared/ColourMapControl";
import { FieldSelector } from "../../shared/FieldSelector";
import { QuantityChip } from "../../shared/QuantityChip";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { MissingDataStyle } from "../../shared/MissingDataStyle";

/* ---- shared illustrative data ------------------------------------------------------------- */

const BASE_VIEW = "全体外観";

const CASE_LABEL: Record<string, string> = {
  "case-012": "Run 12",
  "case-011": "Run 11",
  "case-009": "Run 09",
  "case-007": "Run 07",
};

const RUNS4 = ["Run 12", "Run 11", "Run 09", "Run 07"];
const RUNS6 = ["Run 12", "Run 11", "Run 09", "Run 08", "Run 07", "Run 05"];

/* The field the panes contour. The averaged peak carries its spread in the real product
 * (INV-033); here the label at least says which number it is (INV-032). */
const FIELD_LABEL = "ミーゼス応力 [MPa]・節点平均";
const LEGEND_TICKS = ["241.7", "181.3", "120.9", "60.4", "0.0"];
const SHARED_RANGE = "0.0〜241.7 MPa";

const PANE_CAMERAS = ["等角・全体", "最大応力へ寄せる", "正面・全体", "治具アップ"];

/* ---- result axes (XC-160): named, with stored positions - a bookmark never lands between --- */

type AxisId = "time" | "mode" | "frequency";
const AXIS_IDS = ["time", "mode", "frequency"] as const;
const AXIS_SHORT: Record<AxisId, string> = { time: "時間", mode: "モード", frequency: "周波数" };

type AxisDef = { name: string; min: number; max: number; step: number; format: (v: number) => string };
const AXES: Record<AxisId, AxisDef> = {
  time: { name: "時間軸「荷重ステップ」", min: 0, max: 30, step: 2, format: (v) => `${v.toFixed(1)} s` },
  mode: { name: "モード軸「固有モード」", min: 1, max: 7, step: 1, format: (v) => `モード ${v.toFixed(0)}` },
  frequency: { name: "周波数軸「掃引」", min: 10, max: 2010, step: 50, format: (v) => `${v.toFixed(1)} Hz` },
};

function axisValue(axis: AxisDef, fraction: number): number {
  const raw = axis.min + fraction * (axis.max - axis.min);
  const snapped = axis.min + Math.round((raw - axis.min) / axis.step) * axis.step;
  return Math.min(axis.max, Math.max(axis.min, snapped));
}

/* ---- result-axis bookmarks (XC-197): a rule, resolved per case, honest about snapping ------ */

type BookmarkCaseRes = {
  kase: string;
  position: string | null;
  value: string | null;
  unit: string | null;
  snapped: boolean;
  missing?: string;
};
type Bookmark = { id: string; name: string; rule: string; frac: number | null; perCase: BookmarkCaseRes[] };

const BOOKMARKS: Bookmark[] = [
  {
    id: "hold", name: "保持時間", rule: "固定した位置・12.0 s", frac: 12 / 30,
    perCase: [
      { kase: "Run 12", position: "12.0 s", value: "216.9", unit: "MPa", snapped: false },
      { kase: "Run 11", position: "12.0 s", value: "205.2", unit: "MPa", snapped: false },
    ],
  },
  {
    id: "peak", name: "最大応力時", rule: "規則：ミーゼス応力が最大", frac: 16 / 30,
    perCase: [
      { kase: "Run 12", position: "16.0 s", value: "241.7", unit: "MPa", snapped: true },
      { kase: "Run 11", position: "18.0 s", value: "228.4", unit: "MPa", snapped: false },
    ],
  },
  {
    id: "yield", name: "許容超過", rule: "規則：ミーゼス応力が 235 MPa を上昇方向に横切る", frac: 6 / 30,
    perCase: [
      { kase: "Run 12", position: "6.0 s", value: "235.8", unit: "MPa", snapped: true },
      { kase: "Run 11", position: null, value: null, unit: null, snapped: false, missing: "235 MPa に達しません" },
    ],
  },
  {
    id: "residual", name: "残留変形の回復", rule: "規則：残留変形が 0.1 mm を下回る", frac: null,
    perCase: [
      { kase: "Run 12", position: null, value: null, unit: null, snapped: false, missing: "数量「残留変形」がこのケースにありません" },
      { kase: "Run 11", position: null, value: null, unit: null, snapped: false, missing: "数量「残留変形」がこのケースにありません" },
    ],
  },
];

/* ---- playback presets (XC-200): a preset answers only "when" ------------------------------- */

const MOTION_PRESETS = [
  { id: "full", name: "全区間", detail: "軸の先頭 → 軸の末尾・1.0×・30 fps" },
  { id: "hold-peak", name: "保持〜最大応力", detail: "保持時間 → 最大応力時・0.5×・60 fps" },
  { id: "peak-loop", name: "最大付近ループ", detail: "最大応力時の前後 2.0 s・0.25×・30 fps・繰り返し" },
];

/* ---- comparisons (XC-202): one base view, one swept axis, everything else shared ----------- */

type ComparisonMember = { label: string; flag?: "snapped" | "duplicate" };
type ComparisonSpec = {
  axisChip: string;
  axisRow: string;
  members: ComparisonMember[];
  columns: number;
  overlay: boolean;
  positionAxis: boolean;
  rangeDivision: number | null;
};

function comparisonSpec(variant: string): ComparisonSpec | null {
  if (!variant.startsWith("comparison")) return null;
  if (variant === "comparison-columns") {
    return {
      axisChip: "ケースで比較・6 メンバー・3 列 × 2 行",
      axisRow: "ケース",
      members: RUNS6.map((label) => ({ label })),
      columns: 3, overlay: false, positionAxis: false, rangeDivision: null,
    };
  }
  if (variant === "comparison-overlay") {
    return {
      axisChip: "ケースで比較・重ね合わせ・4 メンバー",
      axisRow: "ケース",
      members: RUNS4.map((label) => ({ label })),
      columns: 1, overlay: true, positionAxis: false, rangeDivision: null,
    };
  }
  if (variant === "comparison-range") {
    return {
      axisChip: "結果位置で比較・7 メンバー（時間軸「荷重ステップ」を等分）",
      axisRow: "結果位置（時間軸「荷重ステップ」）",
      members: [
        { label: "Run 12・0.0 s" },
        { label: "Run 12・6.0 s", flag: "snapped" },
        { label: "Run 12・12.0 s", flag: "snapped" },
        { label: "Run 12・12.0 s", flag: "duplicate" },
        { label: "Run 12・18.0 s", flag: "snapped" },
        { label: "Run 12・24.0 s", flag: "snapped" },
        { label: "Run 12・30.0 s" },
      ],
      columns: 4, overlay: false, positionAxis: false, rangeDivision: 7,
    };
  }
  if (variant === "comparison-output") {
    return {
      axisChip: "結果位置で比較・4 メンバー",
      axisRow: "結果位置（時間軸「荷重ステップ」）",
      members: [
        { label: "Run 12・0.0 s" },
        { label: "Run 12・12.0 s（保持時間）" },
        { label: "Run 12・16.0 s（最大応力時）", flag: "snapped" },
        { label: "Run 12・30.0 s" },
      ],
      columns: 2, overlay: false, positionAxis: true, rangeDivision: null,
    };
  }
  // "comparison" and "comparison-borrowed": the baseline grid over the case axis.
  return {
    axisChip: "ケースで比較・4 メンバー",
    axisRow: "ケース",
    members: RUNS4.map((label) => ({ label })),
    columns: 2, overlay: false, positionAxis: false, rangeDivision: null,
  };
}

/* ---- view objects (16_application_model): per-kind property taxonomies --------------------- */

const OBJECT_KINDS = [
  "analysis-mesh", "reference-mesh", "point-cloud", "scalar-field",
  "vector-field", "trajectory", "annotation", "effect",
] as const;
type ObjectKind = (typeof OBJECT_KINDS)[number];
function isObjectKind(value: string): value is ObjectKind {
  return (OBJECT_KINDS as readonly string[]).includes(value);
}

const OBJECT_META: Record<ObjectKind, { name: string; label: string }> = {
  "analysis-mesh": { name: "解析メッシュ「ブラケット」", label: "解析メッシュ" },
  "reference-mesh": { name: "参照メッシュ「治具 CAD」", label: "参照メッシュ" },
  "point-cloud": { name: "点群「計測点・スキャン 04」", label: "点群" },
  "scalar-field": { name: "スカラー場「ミーゼス応力」", label: "スカラー場" },
  "vector-field": { name: "ベクトル場「変位」", label: "ベクトル場" },
  trajectory: { name: "流線「冷却流路」", label: "流線・軌跡" },
  annotation: { name: "注釈「最大応力ラベル」", label: "テキスト注釈" },
  effect: { name: "エフェクト「溶接部の強調」", label: "エフェクト" },
};

function objectKindOf(variant: string): ObjectKind | null {
  if (variant === "material-composition") return "analysis-mesh";
  if (!variant.startsWith("object-")) return null;
  const kind = variant.slice("object-".length);
  return isObjectKind(kind) ? kind : null;
}

/* ---- outliner: what the file holds, never an invented hierarchy ---------------------------- */

function outlinerRoots(variant: string): OutlinerNode[] {
  if (variant === "outliner-empty") return [];
  if (variant === "outliner-flat") {
    // The source file has no parent-child relations: siblings directly under the dataset.
    return [
      {
        id: "ds", name: "［元ファイルのルート名］", kind: "データセット",
        children: [
          { id: "p1", name: "［元ファイルの部品名 01］", kind: "部品" },
          { id: "p2", name: "［元ファイルの部品名 02］", kind: "部品" },
          { id: "rg", name: "［元ファイルの領域名］", kind: "領域", visible: false },
        ],
      },
    ];
  }
  return [
    {
      id: "ds", name: "Run 12（データセット）", kind: "データセット",
      children: [
        {
          id: "asm", name: "［元ファイルのアセンブリ名］", kind: "アセンブリ",
          children: [
            { id: "src-1", name: "［元ファイルの部品名 01］", kind: "部品" },
            { id: "src-2", name: "［元ファイルの部品名 02］", kind: "部品", visible: false },
          ],
        },
      ],
    },
    {
      id: "view-objects", name: "ビューのオブジェクト", kind: "ビュー",
      children: [
        { id: "object-analysis-mesh", name: "解析メッシュ「ブラケット」", kind: "解析メッシュ" },
        { id: "object-scalar-field", name: "スカラー場「ミーゼス応力」", kind: "スカラー場" },
        { id: "object-annotation", name: "注釈「最大応力ラベル」", kind: "注釈" },
      ],
    },
  ];
}

/* ---- library shelf states (the shell draws the shelf; the canvas states the rule) ---------- */

const LIBRARY_NOTE: Record<string, { title: string; detail: string }> = {
  "library-collapsed": { title: "素材ライブラリ：閉じた状態", detail: "入力欄の直上に細い見出しだけを残し、中央表示の縦幅を優先しています。見出しから 1 行表示へ戻せます。" },
  "library-one-row": { title: "素材ライブラリ：1 行表示", detail: "適用可能な素材を、サムネイルを途中で切らずに完全な 1 行で表示しています。" },
  "library-expanded": { title: "素材ライブラリ：拡張表示", detail: "ライブラリを縦に拡張して複数行を閲覧しています。右側の編集領域の高さは維持されます。" },
  "library-narrow": { title: "素材ライブラリ：狭幅表示", detail: "幅が足りないため、中央画面を押し縮めず、入力欄の上に重なる下部ドロワーとして開きます。" },
  "library-searching": { title: "素材ライブラリ：検索中", detail: "サンプル／オリジナルの別、文字列、タグ、並び順を分けて絞り込んでいます。" },
  "library-selected": { title: "素材ライブラリ：選択中", detail: "クリックは選択と確認までです。現在の対象への反映は、ドラッグか明示的な適用操作で行います。" },
};

function forcedPaneCount(variant: string): 1 | 2 | 3 | 4 | null {
  if (variant === "split-two" || variant === "split-output") return 2;
  if (variant === "split-three") return 3;
  if (variant === "split-four") return 4;
  if (variant === "cameras" || variant === "camera-unresolved") return 2;
  return null;
}

/* ================================ canvas ==================================================== */

export function ViewScreen(props: { variant: string }) {
  // Keyed remount per variant: each design state gets a fresh instance, so per-variant seed
  // state (selected camera, grade, axis) never leaks between deep links.
  return <ViewCanvas key={props.variant} variant={props.variant} />;
}

function ViewCanvas({ variant }: { variant: string }) {
  const s = useSession();
  const [axisId, setAxisId] = useState<AxisId>("time");
  const caseName = CASE_LABEL[s.selectedCaseId ?? ""] ?? "ケース未選択";

  if (variant === "empty") return <EmptyCanvas />;
  if (variant === "renderer-error") return <RendererErrorCanvas />;

  const spec = comparisonSpec(variant);
  const paneCount = forcedPaneCount(variant) ?? s.paneCount;
  const overlayAxis: AxisId | null =
    variant === "temporal-axis" ? axisId
      : variant === "axis-error" ? "mode"
        : variant === "result-bookmarks" || variant === "output-motion" ? "time"
          : null;
  const libNote = LIBRARY_NOTE[variant];
  const notices = canvasNotices(variant);

  return (
    <div className="vi-canvas">
      {spec ? (
        <ComparisonCanvas spec={spec} borrowed={variant === "comparison-borrowed"} />
      ) : (
        <SplitLayout panes={buildPanes(variant, caseName, paneCount)} />
      )}

      {notices.length > 0 || variant === "unresolved-template" ? (
        <div className="vi-overlays">
          {variant === "unresolved-template" ? <TemplateResolution /> : null}
          {notices}
        </div>
      ) : null}

      {variant === "probe" ? (
        <ProbeReadout
          field="ミーゼス応力"
          value="182.4"
          unit="MPa"
          origin="dataset"
          location="GlobalNodeId 20481・未変形座標・時刻 12.0 s・節点値（平均なし）"
          onHold={() => submit({ operation: "variable.declare", parameters: { name: "プローブ応力", source: "probe" } })}
        />
      ) : null}

      {overlayAxis !== null ? (
        <PlaybackOverlay
          axisId={overlayAxis}
          switchable={variant === "temporal-axis"}
          onSwitch={setAxisId}
          markers={variant === "result-bookmarks" ? bookmarkMarkers() : []}
        />
      ) : null}

      {variant === "result-bookmarks" ? <BookmarkPanel caseName={caseName} /> : null}
      {variant === "output-motion" ? <PresetPanel /> : null}
      {variant === "assistant-drawer" ? <AssistantDrawer /> : null}
      {variant === "output-preflight" ? <PreflightDialog /> : null}

      {libNote ? (
        <div className="vi-canvas-note" role="note">
          <b>{libNote.title}</b>
          <small>{libNote.detail}</small>
        </div>
      ) : paneCount > 1 && s.cameraSync && !spec ? (
        <div className="vi-canvas-note" role="note">
          <b>カメラ同期：オン</b>
          <small>操作はすべての画面へ同じカメラ移動として適用されます。分割は書き出しに含まれません（XC-210）。</small>
        </div>
      ) : null}
    </div>
  );
}

function buildPanes(variant: string, caseName: string, count: number): ReactNode[] {
  const others = variant === "camera-unresolved" ? ["Run 09"] : ["Run 11", "Run 09", "Run 07"];
  return Array.from({ length: count }, (_, index) => {
    const name = index === 0 ? caseName : others[index - 1] ?? "Run 07";
    const label = count > 1 && index === 0 ? `${name}・ツリー選択` : name;
    const showCamera = count > 1 || variant === "cameras";
    const camera = PANE_CAMERAS[index] ?? "等角・全体";
    const cameraNote =
      variant === "camera-unresolved" && index === 1
        ? "最大応力へ寄せる・未解決（動かしていません）"
        : camera;
    return (
      <ViewportPlaceholder
        key={index}
        caseName={label}
        fieldLabel={index === 0 ? FIELD_LABEL : undefined}
        map="viridis"
        legendTicks={index === 0 ? LEGEND_TICKS : undefined}
        reducedNote={variant === "reduced" && index === 0 ? "要素 1,244 万 → 156 万に間引き" : undefined}
      >
        {showCamera ? (
          <div className="pane-badge" style={{ left: "auto", right: 8 }} title="この画面が覗くカメラ">
            ◉ {cameraNote}
          </div>
        ) : null}
        {variant === "deformation" ? (
          /* INV-024: the factor is drawn into the picture - an exported image has no rail. */
          <span className="vi-stamp">変形倍率 ×50・値は未変形形状から</span>
        ) : null}
      </ViewportPlaceholder>
    );
  });
}

function ComparisonCanvas({ spec, borrowed }: { spec: ComparisonSpec; borrowed: boolean }) {
  return (
    <>
      <div className="vi-comparison-bar">
        <span className="axis-chip">{spec.axisChip}</span>
        <small>
          全ペインが同じカラーマップと同じ範囲（{SHARED_RANGE}・計算）。基準ビュー「{BASE_VIEW}」の設定を共有
        </small>
        {borrowed ? (
          <button className="btn ghost" onClick={() => session.navigate("view", "default")}>
            基準ビューを開く
          </button>
        ) : null}
      </div>
      {spec.overlay ? (
        <SplitLayout
          panes={[
            <ViewportPlaceholder key="overlay" caseName="重ね合わせ・4 メンバー" fieldLabel={FIELD_LABEL} map="viridis" legendTicks={LEGEND_TICKS}>
              <div className="pane-badge" style={{ top: "auto", bottom: 8, left: 8 }}>
                結果色：Run 12／参照形状：Run 11・Run 09・Run 07
              </div>
            </ViewportPlaceholder>,
          ]}
        />
      ) : (
        <div className="vi-comparison-grid" style={{ gridTemplateColumns: `repeat(${spec.columns}, minmax(0, 1fr))` }}>
          {spec.members.map((member, index) => (
            <ViewportPlaceholder
              key={index}
              caseName={member.label}
              fieldLabel={index === 0 ? FIELD_LABEL : undefined}
              map="viridis"
              legendTicks={index === 0 ? LEGEND_TICKS : undefined}
            >
              {member.flag ? (
                <div className="pane-badge" style={{ top: "auto", bottom: 8, left: 8 }}>
                  {member.flag === "snapped" ? "保存位置へ丸め" : "前と同じ保存位置"}
                </div>
              ) : null}
            </ViewportPlaceholder>
          ))}
        </div>
      )}
    </>
  );
}

function canvasNotices(variant: string): ReactNode[] {
  const out: ReactNode[] = [];
  const push = (key: string, tone: "" | "error" | "warn" | "good", title: string, why: string) =>
    out.push(
      <div key={key} className={tone === "" ? "notice" : `notice ${tone}`} role={tone === "error" ? "alert" : "status"}>
        <b>{title}</b>
        <span className="why">{why}</span>
      </div>,
    );
  if (variant === "reduced") {
    push("reduced", "warn", "表示形状を縮退しています",
      "画面は間引いた形状（要素 1,244 万 → 156 万）を使用します。表示値・プローブ・レポートの計算は完全データを使用します（INV-001）。");
  }
  if (variant === "deformation") {
    push("deformation", "warn", "変形を ×50 に誇張して表示しています",
      "計測・プローブ・レポートの値は未変形形状から計算します。画面上の形状を測ると誤った寸法になります（INV-024）。");
  }
  if (variant === "axis-error") {
    push("axis-error", "error", "指定した結果位置がありません",
      "要求されたモード 8 はケース「Run 12」にありません（モードは 1〜7）。近傍への丸めは行わず、表示は直前の位置のままです（view/AC-033）。");
  }
  if (variant === "camera-unresolved") {
    push("camera-unresolved", "error", "視点「最大応力へ寄せる」を解決できません",
      "規則が参照する数量「ミーゼス応力」がケース「Run 09」にありません。名指しして拒否し、カメラは動かしません。近い場所への移動も行いません。");
  }
  if (variant === "cameras") {
    push("cameras", "", "1 つのビューが 4 台のカメラを保存しています",
      "各画面は覗くカメラを名指しします。規則で決まるカメラは座標を保存せず、ケースごとに解決します。");
  }
  if (variant === "steady-result") {
    push("steady", "", "定常結果・再生する軸がありません",
      "このケースは結果軸を持ちません。再生オーバーレイは無効化ではなく非表示です（XC-160）。動画と再生プリセットは出力タブで利用不可として名指しされます。");
  }
  if (variant === "develop-grade") {
    push("grade", "", "現像プリセット「提示用」を適用中",
      "既定の「計測」は無補正です。補正を掛けた画像は、凡例も同じ補正を通すか、補正名とパラメータを成果物に記載します。");
  }
  if (variant === "comparison-overlay") {
    push("overlay", "warn", "重ね合わせでは結果色を持てるのは 1 メンバーだけです",
      "「Run 12」が結果色を持ち、残りは参照形状として描かれます。2 つのコンターを重ねた画は値を符号化しません。");
  }
  if (variant === "comparison-borrowed") {
    push("borrowed", "", `この比較の設定は基準ビュー「${BASE_VIEW}」のものです`,
      "オブジェクト・マテリアル・照明・背景は複製ではなく参照です。編集は基準ビューで行い、全メンバーへ反映されます（XC-202）。");
  }
  return out;
}

function TemplateResolution() {
  return (
    <>
      <div className="notice good" role="status">
        <b>テンプレート「技術資料・標準」リビジョン 3 — 解決できた項目</b>
        <span className="why">レイアウト・1 画面／カメラ「保存済み等角」／背景「グラデーション」は適用済みです。</span>
      </div>
      <UnresolvedList
        title="未解決の項目 — 既定値で埋めません（XC-090）"
        items={[
          { what: "フィールド「ミーゼス応力」", missing: "ケース「Run 12」に同名のフィールドがありません。代替のフィールドは使いません" },
          { what: "マテリアル「スチール・つや消し」", missing: "参照アセットのリビジョン 3 がこのワークスペースにありません" },
        ]}
      />
    </>
  );
}

function bookmarkMarkers(): { at: number; title: string }[] {
  return BOOKMARKS.flatMap((bm) => (bm.frac === null ? [] : [{ at: bm.frac, title: bm.name }]));
}

function PlaybackOverlay(props: {
  axisId: AxisId;
  switchable: boolean;
  onSwitch: (axis: AxisId) => void;
  markers: { at: number; title: string }[];
}) {
  const s = useSession();
  const axis = AXES[props.axisId];
  const span = axis.max - axis.min;
  const value = axisValue(axis, s.resultPosition);
  const pct = ((value - axis.min) / span) * 100;
  const stepBy = (direction: -1 | 1) => session.moveResultPosition(s.resultPosition + (direction * axis.step) / span);
  return (
    <div className="playback-overlay" role="toolbar" aria-label={`再生 — ${axis.name}`}>
      {props.switchable ? (
        <span role="radiogroup" aria-label="結果軸" style={{ display: "flex", gap: 2 }}>
          {AXIS_IDS.map((id) => (
            <button
              key={id}
              role="radio"
              aria-checked={props.axisId === id}
              className="icon-button"
              style={{ width: "auto", padding: "0 6px" }}
              title={AXES[id].name}
              onClick={() => props.onSwitch(id)}
            >
              {AXIS_SHORT[id]}
            </button>
          ))}
        </span>
      ) : null}
      <button className="icon-button" aria-label="先頭へ" onClick={() => session.moveResultPosition(0)}>«</button>
      <button className="icon-button" aria-label="1 つ前の保存位置へ" onClick={() => stepBy(-1)}>‹</button>
      <button
        className="icon-button"
        aria-label="再生"
        onClick={() => submit({ operation: "view.update", parameters: { playback: "start", axis: props.axisId } })}
      >
        ▶
      </button>
      <button className="icon-button" aria-label="1 つ先の保存位置へ" onClick={() => stepBy(1)}>›</button>
      <button className="icon-button" aria-label="末尾へ" onClick={() => session.moveResultPosition(1)}>»</button>
      <div
        className="axis"
        role="slider"
        tabIndex={0}
        aria-label={axis.name}
        aria-valuemin={axis.min}
        aria-valuemax={axis.max}
        aria-valuenow={value}
        aria-valuetext={axis.format(value)}
        onClick={(event) => {
          const bounds = event.currentTarget.getBoundingClientRect();
          session.moveResultPosition((event.clientX - bounds.left) / bounds.width);
        }}
        onKeyDown={(event) => {
          if (event.key === "ArrowLeft") stepBy(-1);
          if (event.key === "ArrowRight") stepBy(1);
        }}
      >
        {props.markers.map((mark) => (
          <span key={mark.title} className="vi-mark" style={{ left: `${mark.at * 100}%` }} title={mark.title} />
        ))}
        <span className="pos" style={{ left: `${pct}%` }} />
      </div>
      <span className="type-caption" style={{ color: "var(--ink-strong)", fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
        {axis.format(value)}
      </span>
      <span className="type-caption" style={{ color: "var(--ink-faint)", whiteSpace: "nowrap" }}>{axis.name}</span>
      <button className="icon-button" style={{ width: "auto", padding: "0 6px" }} title="再生速度。結果軸と実時間の対応は出力に記載されます">
        1×
      </button>
    </div>
  );
}

function BookmarkPanel({ caseName }: { caseName: string }) {
  return (
    <section className="vi-panel" style={{ left: "50%", bottom: 56, transform: "translateX(-50%)" }} aria-label="結果軸ブックマーク">
      <header>
        <b>結果軸ブックマーク</b>
        <small>規則は座標ではなく条件を保持し、ケースごとに解決します</small>
      </header>
      <div className="body">
        {BOOKMARKS.map((bm) => {
          const mine = bm.perCase.find((pc) => pc.kase === caseName) ?? bm.perCase[0];
          const blocked = mine === undefined || mine.position === null;
          return (
            <div className="vi-row" key={bm.id}>
              <b title={bm.name}>{bm.name}</b>
              <span className="rule">{bm.rule}</span>
              {bm.perCase.map((pc) => (
                <span className="line" key={pc.kase}>
                  <span className="who">{pc.kase}</span>
                  {pc.position === null ? (
                    <MissingDataStyle because={pc.missing ?? "理由未記録"} />
                  ) : (
                    <>
                      <span style={{ fontVariantNumeric: "tabular-nums" }}>{pc.position}</span>
                      {pc.value !== null ? <QuantityChip value={pc.value} unit={pc.unit} /> : null}
                      {pc.value !== null ? <ProvenanceBadge origin="computed" /> : null}
                      {pc.snapped ? (
                        <span className="type-caption" style={{ color: "var(--state-warn)" }}>保存位置へ丸め</span>
                      ) : null}
                    </>
                  )}
                </span>
              ))}
              <button
                className="btn ghost"
                style={{ justifySelf: "start" }}
                disabled={blocked}
                title={blocked ? `無効：ケース「${caseName}」で解決していません` : `ケース「${caseName}」の解決位置へ移動`}
                onClick={() => {
                  if (bm.frac !== null) session.moveResultPosition(bm.frac);
                }}
              >
                移動
              </button>
            </div>
          );
        })}
      </div>
      <footer>固定時刻・極値時刻・しきい値交差を登録できます。保存位置の間に落ちたときは丸めた事実を明示し、解決しないケースでは動かしません。</footer>
    </section>
  );
}

function PresetPanel() {
  const [openId, setOpenId] = useState("full");
  return (
    <section className="vi-panel" style={{ right: 10, bottom: 54 }} aria-label="再生プリセット">
      <header>
        <b>再生プリセット</b>
        <small>再生範囲と速度の組を複数保存します</small>
      </header>
      <div className="body">
        {MOTION_PRESETS.map((preset) => (
          <button key={preset.id} className="vi-row" aria-selected={openId === preset.id} onClick={() => setOpenId(preset.id)}>
            <b title={preset.name}>{preset.name}</b>
            <span className="rule">{preset.detail}</span>
          </button>
        ))}
      </div>
      <footer>動画はプリセット 1 つとカメラ 1 台を名指しします（XC-200）。プリセットは「いつ」だけを持ち、「どこから」は出力タブのカメラが持ちます。</footer>
    </section>
  );
}

function AssistantDrawer() {
  const [draft, setDraft] = useState("");
  return (
    <aside className="vi-drawer" aria-label="会話ドロワー">
      <header>
        <b>会話 — このワークスペース</b>
        <button className="icon-button" aria-label="ドロワーを閉じる" onClick={() => session.navigate("view", "default")}>×</button>
      </header>
      <div className="vi-thread">
        <div className="vi-turn">
          <span className="who">あなた</span>
          <p>最大応力が最も厳しいケースが分かるように、ケース比較のビューにして。</p>
        </div>
        <div className="vi-turn">
          <span className="who">アシスタント</span>
          <p>
            比較「ケース比較・ミーゼス応力」の案を作りました。軸はケース、メンバーは Run 12・Run 11・Run 09・Run 07、
            カラーマップと範囲（{SHARED_RANGE}）は共有です。まだ適用していません。内容を確認して適用してください。
          </p>
          <div className="vi-row-actions">
            <button className="btn primary" onClick={() => submit({ operation: "template.apply", parameters: { proposal: "case-comparison" } })}>
              適用
            </button>
            <button className="btn ghost" onClick={() => submit({ operation: "history.list", parameters: {} })}>差分を確認</button>
          </div>
        </div>
      </div>
      <footer>
        <form
          style={{ display: "flex", gap: 6 }}
          onSubmit={(event) => {
            event.preventDefault();
            if (draft.trim() === "") return;
            submit({ operation: "script.run", parameters: { instruction: draft.trim() } });
            setDraft("");
          }}
        >
          <input
            className="field-input"
            style={{ flex: 1, minWidth: 0 }}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="続けて指示（同じ会話）"
            aria-label="会話への指示"
          />
          <button className="btn" type="submit" disabled={draft.trim() === ""}>送る</button>
        </form>
        <p className="prop-note" style={{ margin: 0 }}>
          下の入力欄・会話画面と同じスレッドです（XC-150）。右のプロパティ欄と素材ライブラリはこのまま使えます。
        </p>
      </footer>
    </aside>
  );
}

function PreflightDialog() {
  const checks = [
    { what: "レンダラー", detail: "VTK 経路を利用可能・オフライン", verdict: "pass" as const, label: "合格" },
    { what: "保存先", detail: "output/view/run-12/ — 新規実行フォルダー・衝突なし", verdict: "pass" as const, label: "合格" },
    { what: "カメラパス", detail: "動画に使うカメラが未指定です。カメラ 1 台を名指ししてください", verdict: "blocked" as const, label: "出力不可" },
    { what: "時間対応", detail: "結果軸 0.0〜30.0 s を実時間 12.5 s に対応付け（2.4 倍速）。成果物に記載します", verdict: "warn" as const, label: "要記載" },
  ];
  return (
    <div className="dialog-scrim" role="dialog" aria-modal="true" aria-label="出力前チェック">
      <div className="dialog" style={{ width: "min(560px, calc(100vw - 48px))" }}>
        <header>
          <h2>出力前チェック — ビュー動画「{BASE_VIEW}」</h2>
        </header>
        <div className="body">
          {checks.map((check) => (
            <div className="vi-check" key={check.what}>
              <span className="what">{check.what}</span>
              <span className="detail">{check.detail}</span>
              <span className={`verdict ${check.verdict}`}>{check.label}</span>
            </div>
          ))}
          <p className="prop-note">不足を解決するまで出力を開始しません。既存の成果物は変更されません。</p>
        </div>
        <footer>
          <button className="btn ghost" onClick={() => session.navigate("view", "default")}>戻る</button>
          <button className="btn primary" {...disabledBecause("カメラパスが未指定です")}>出力を開始</button>
        </footer>
      </div>
    </div>
  );
}

function EmptyCanvas() {
  return (
    <div className="vi-canvas" style={{ overflow: "auto", display: "block" }}>
      <div className="empty-state">
        <h2>表示するケースがありません</h2>
        <p>開始プリセットを選ぶか、ワークスペースへ結果ファイルをドロップします。プリセットは絵の構成だけを持ち、数値には触れません。</p>
        <div className="actions">
          <button className="btn primary" onClick={() => submit({ operation: "view.create", parameters: { preset: "overview" } })}>全体外観</button>
          <button className="btn" onClick={() => submit({ operation: "view.create", parameters: { preset: "section-contour" } })}>断面＋コンター</button>
          <button className="btn" onClick={() => submit({ operation: "view.create", parameters: { preset: "deformation" } })}>変形の拡大表示</button>
        </div>
      </div>
      <div style={{ width: "min(520px, 100%)", margin: "0 auto", padding: "0 16px 16px" }}>
        <WorkspaceItemList
          kindLabel="このワークスペースのビュー"
          items={[
            { id: "v1", name: "全体外観", meta: "1 画面・カメラ 4 台" },
            { id: "v2", name: "最大応力クローズアップ", meta: "1 画面" },
            { id: "v3", name: "ケース比較 2×2", meta: "比較・ケース軸" },
          ]}
          openId={null}
          onOpen={() => session.navigate("view", "default")}
          onCreate={() => submit({ operation: "view.create", parameters: {} })}
        />
      </div>
    </div>
  );
}

function RendererErrorCanvas() {
  return (
    <div className="vi-canvas">
      <div className="empty-state">
        <h2>Omniverse レンダラーを開始できません</h2>
        <p>
          バックエンド「Omniverse Kit」への接続がありません。VTK 軽量経路は引き続き利用でき、黙った切り替えは行いません。
          どちらの経路で描いたかは出力の来歴に記録されます。
        </p>
        <div className="actions">
          <button className="btn primary" onClick={() => submit({ operation: "view.render", parameters: { renderer: "vtk" } })}>
            VTK 経路で続ける
          </button>
          <button className="btn ghost" onClick={() => submit({ operation: "system.capabilities", parameters: {} })}>接続を再確認</button>
        </div>
        <p className="prop-note">失敗の詳細は通知履歴に残っています。</p>
      </div>
    </div>
  );
}

/* ================================ rail ====================================================== */

export function ViewRail(props: { tab: string; variant: string }) {
  return <RailBody key={`${props.tab}:${props.variant}`} tab={props.tab} variant={props.variant} />;
}

const RAIL_TAB_LABEL: Record<string, string> = {
  camera: "カメラ",
  rendering: "描画",
  background: "背景",
  objects: "オブジェクト",
  text: "テキスト",
  materials: "マテリアル",
};

function RailBody({ tab, variant }: { tab: string; variant: string }) {
  // XC-202: a comparison owns nothing but its axis - every other tab belongs to the base view.
  if (comparisonSpec(variant) !== null && tab !== "overall" && tab !== "output") {
    return <BorrowedPanel tabLabel={RAIL_TAB_LABEL[tab] ?? "設定"} />;
  }
  switch (tab) {
    case "camera": return <CameraTab variant={variant} />;
    case "rendering": return <RenderingTab variant={variant} />;
    case "background": return <BackgroundTab />;
    case "output": return <OutputTab variant={variant} />;
    case "objects": return <ObjectsTab variant={variant} />;
    case "text": return <TextTab variant={variant} />;
    case "materials": return <MaterialsTab variant={variant} />;
    default: return <OverallTab variant={variant} />;
  }
}

function BorrowedPanel({ tabLabel }: { tabLabel: string }) {
  return (
    <div className="prop-section">
      <div className="notice">
        <b>この{tabLabel}は基準ビュー「{BASE_VIEW}」が持っています</b>
        <span className="why">
          比較は自前の{tabLabel}を持ちません。基準ビューの設定を、複製ではなく参照として全メンバーへ適用します。
          ここで直せてしまうと、ペインの差の原因を特定できなくなります（XC-202）。
        </span>
      </div>
      <button className="btn" style={{ marginTop: 8 }} onClick={() => session.navigate("view", "default")}>
        基準ビュー「{BASE_VIEW}」を編集
      </button>
    </div>
  );
}

/* ---- overall ------------------------------------------------------------------------------- */

function OverallTab({ variant }: { variant: string }) {
  const kind = objectKindOf(variant);
  const [selectedNode, setSelectedNode] = useState<string | null>(kind ? `object-${kind}` : null);
  const spec = comparisonSpec(variant);
  return (
    <div>
      <section className="prop-section">
        <h3>ビュー</h3>
        <div className="prop-row">
          <label htmlFor="vi-name">名前</label>
          <input id="vi-name" className="field-input" defaultValue={BASE_VIEW} />
        </div>
        <div className="prop-row">
          <label htmlFor="vi-desc">説明</label>
          <input id="vi-desc" className="field-input" placeholder="このビューが示す内容" />
        </div>
      </section>

      {spec ? <ComparisonGroup spec={spec} /> : null}

      <section className="prop-section">
        <h3>構成（アウトライナー）</h3>
        {variant === "outliner-flat" ? (
          <p className="prop-note" style={{ marginTop: 0 }}>元ファイルに親子関係がありません。推測せず、データセット直下の兄弟として表示します。</p>
        ) : null}
        <Outliner
          roots={outlinerRoots(variant)}
          selectedId={selectedNode}
          onSelect={setSelectedNode}
          onToggleVisible={(id) => submit({ operation: "view.update", parameters: { toggleVisible: id } })}
          emptyText="データセット未読込です。読み込むと元ファイルの構成をここに表示します。サンプル構造は作りません"
        />
      </section>

      <section className="prop-section">
        <h3>ガイド</h3>
        <div className="prop-row"><label htmlFor="vi-guide-axes">座標軸</label><input id="vi-guide-axes" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
        <div className="prop-row"><label htmlFor="vi-guide-grid">グリッド</label><input id="vi-guide-grid" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
        <div className="prop-row"><label htmlFor="vi-guide-gizmo">方位ギズモ</label><input id="vi-guide-gizmo" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
        <div className="prop-row"><label htmlFor="vi-guide-scale">スケールバー</label><input id="vi-guide-scale" type="checkbox" style={{ justifySelf: "start" }} /></div>
        <div className="prop-row"><label htmlFor="vi-guide-legend">凡例</label><input id="vi-guide-legend" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
        <p className="prop-note">ガイドは表示状態です。解析値と正規データは変更しません。</p>
      </section>
    </div>
  );
}

function ComparisonGroup({ spec }: { spec: ComparisonSpec }) {
  const rows = Math.ceil(spec.members.length / spec.columns);
  return (
    <section className="prop-section">
      <h3>比較</h3>
      <div className="prop-row">
        <label>基準ビュー</label>
        <button
          className="btn ghost"
          style={{ justifySelf: "start" }}
          title="比較は自前の設定を持ちません。基準ビューの編集が全メンバーへ反映されます"
          onClick={() => session.navigate("view", "default")}
        >
          「{BASE_VIEW}」を開く
        </button>
      </div>
      <div className="prop-row">
        <label>参照の性質</label>
        <span className="type-caption" style={{ color: "var(--ink-muted)" }}>生きた参照・編集が全ペインへ反映</span>
      </div>
      <div className="prop-row"><label>変える軸</label><span>{spec.axisRow}</span></div>
      {spec.rangeDivision !== null ? (
        <>
          <div className="prop-row">
            <label htmlFor="vi-division">分割数</label>
            <input id="vi-division" className="field-input" type="number" min={2} max={12} defaultValue={spec.rangeDivision} />
          </div>
          <p className="prop-note">生成した位置は軸上に実在する保存位置（6.0 s 刻み）へ丸め、丸めた事実をメンバーごとに示します。ブックマークを先に作る必要はありません。</p>
        </>
      ) : null}
      <div role="group" aria-label="メンバー" style={{ marginTop: 6 }}>
        {spec.members.map((member, index) => (
          <div className="vi-member" key={`${member.label}-${index}`}>
            <span className="index">{index + 1}</span>
            <b title={member.label}>{member.label}</b>
            {member.flag === "snapped" ? <span className="flag">保存位置へ丸め</span> : null}
            {member.flag === "duplicate" ? <span className="flag">前と同じ保存位置</span> : null}
          </div>
        ))}
      </div>
      {spec.members.some((member) => member.flag === "duplicate") ? (
        <div className="notice warn" style={{ marginTop: 6 }}>
          <b>同じ位置に解決するメンバーがあります</b>
          <span className="why">軸の保存位置（6.0 s 刻み）より細かく分割しています。分割数を減らすまで、同じ絵が並ぶ図は出力しません。</span>
        </div>
      ) : null}
      <div className="prop-row" style={{ marginTop: 6 }}><label>並べ方</label><span>{spec.overlay ? "重ね合わせ" : "グリッド"}</span></div>
      {spec.overlay ? (
        <div className="notice warn" style={{ marginTop: 6 }}>
          <b>結果色を持てるのは 1 メンバーだけです</b>
          <span className="why">「Run 12」に結果色を割り当て、残りは参照形状として描きます。2 つのコンターを重ねた画は値を符号化しません。</span>
        </div>
      ) : (
        <>
          <div className="prop-row">
            <label>行 × 列</label>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>{rows} 行 × {spec.columns} 列</span>
          </div>
          <p className="prop-note">
            列数は画面上部の分割メニューで選びます。行数はメンバー数（{spec.members.length} 件）から決まるため、どの列数でも絵に出ないメンバーは生まれません（XC-205）。
          </p>
        </>
      )}
      <div className="prop-row">
        <label htmlFor="vi-shared-map">カラーマップを共有</label>
        <input id="vi-shared-map" type="checkbox" defaultChecked style={{ justifySelf: "start" }} />
      </div>
      <p className="prop-note">
        全メンバーが同じカラーマップと同じ範囲（{SHARED_RANGE}・計算）で描かれます。隣り合うペインを目で比べられるのは、これが保証されているときだけです。
      </p>
    </section>
  );
}

/* ---- camera (XC-199): several named cameras; a rule refuses by name and moves nothing ------ */

type CameraRow = { id: string; name: string; rule: string; state: string; tone?: "error" };

function cameraRows(unresolved: boolean): CameraRow[] {
  return [
    { id: "cam-front", name: "正面・全体", rule: "現在の位置を固定", state: "座標を保存済み" },
    { id: "cam-iso", name: "等角・全体", rule: "現在の位置を固定", state: "座標を保存済み・表示中" },
    {
      id: "cam-peak", name: "最大応力へ寄せる", rule: "規則：ミーゼス応力の最大値へ寄せる",
      state: unresolved
        ? "未解決 — 数量「ミーゼス応力」がケース「Run 09」にありません。カメラは動かしていません"
        : "ケース「Run 12」では GlobalNodeId 20481 付近に解決",
      tone: unresolved ? "error" : undefined,
    },
    { id: "cam-fixture", name: "治具アップ", rule: "オブジェクト「治具」を画面に収める", state: "ケースごとに解決" },
  ];
}

function CameraTab({ variant }: { variant: string }) {
  const unresolved = variant === "camera-unresolved";
  const [selected, setSelected] = useState(unresolved || variant === "cameras" ? "cam-peak" : "cam-iso");
  const rows = cameraRows(unresolved);
  const current = rows.find((cam) => cam.id === selected);
  return (
    <div>
      {unresolved ? (
        <section className="prop-section">
          <div className="notice error" role="alert">
            <b>視点「最大応力へ寄せる」を解決できません</b>
            <span className="why">規則が参照する数量「ミーゼス応力」がケース「Run 09」にありません。名指しして拒否し、カメラは動かしません。</span>
          </div>
        </section>
      ) : null}
      <section className="prop-section">
        <h3>カメラ（4 台）</h3>
        <div style={{ display: "grid", gap: 4 }}>
          {rows.map((cam) => (
            <button key={cam.id} className="vi-row" aria-selected={selected === cam.id} onClick={() => setSelected(cam.id)}>
              <b title={cam.name}>{cam.name}</b>
              <span className="rule">{cam.rule}</span>
              <span className={cam.tone === "error" ? "state error" : "state"}>{cam.state}</span>
            </button>
          ))}
        </div>
        <div className="vi-row-actions" style={{ marginTop: 6 }}>
          <button className="btn ghost" onClick={() => submit({ operation: "view.update", parameters: { camera: "add" } })}>追加</button>
          <button className="btn ghost" onClick={() => submit({ operation: "view.duplicate", parameters: { camera: selected } })}>複製</button>
          <button className="btn ghost" onClick={() => submit({ operation: "view.update", parameters: { camera: "remove", id: selected } })}>削除</button>
        </div>
        <p className="prop-note">規則で位置を決めるカメラは座標を保存しません。ケースごとに解決し、解決できないときは名指しして拒否します。各画面は覗くカメラを名指しします。</p>
      </section>
      <section className="prop-section" key={selected}>
        <h3>ポーズ — {current?.name ?? "未選択"}</h3>
        <div className="prop-row">
          <label htmlFor="vi-pose">決め方</label>
          <select id="vi-pose" className="field-input" defaultValue={selected === "cam-peak" || selected === "cam-fixture" ? "framed" : "explicit"}>
            <option value="explicit">現在の位置を固定</option>
            <option value="framed">対象を画面に収める</option>
          </select>
        </div>
        {selected === "cam-peak" ? (
          <>
            <div className="prop-row">
              <label htmlFor="vi-pose-q">数量</label>
              <select id="vi-pose-q" className="field-input" defaultValue="stress">
                <option value="stress">ミーゼス応力</option>
                <option value="disp">変位</option>
              </select>
            </div>
            <div className="prop-row">
              <label htmlFor="vi-pose-s">統計</label>
              <select id="vi-pose-s" className="field-input" defaultValue="max">
                <option value="max">最大</option>
                <option value="min">最小</option>
                <option value="absmax">絶対値最大</option>
              </select>
            </div>
          </>
        ) : null}
        {selected === "cam-fixture" ? (
          <div className="prop-row"><label>対象</label><span>オブジェクト「治具」</span></div>
        ) : null}
        <div className="prop-row"><label>余白</label><span style={{ fontVariantNumeric: "tabular-nums" }}>12 %</span></div>
      </section>
      <section className="prop-section">
        <h3>レンズ</h3>
        <div className="prop-row">
          <label htmlFor="vi-projection">投影</label>
          <select id="vi-projection" className="field-input" defaultValue="perspective">
            <option value="perspective">透視投影</option>
            <option value="orthographic">平行投影</option>
          </select>
        </div>
        <div className="prop-row"><label>焦点距離</label><span style={{ fontVariantNumeric: "tabular-nums" }}>50 mm</span></div>
        <div className="prop-row"><label>クリップ</label><span style={{ fontVariantNumeric: "tabular-nums" }}>手前 0.01 / 奥 1000（モデル座標・mm 宣言）</span></div>
      </section>
    </div>
  );
}

/* ---- rendering (XC-198): renderer, lighting, grade - measurement stays uncorrected --------- */

const GRADES = [
  { id: "measurement", name: "計測（無補正）", thumb: "vi-thumb-grade-flat", exposure: "±0.0 EV（補正なし）", tone: "なし（リニア）" },
  { id: "presentation", name: "提示用", thumb: "vi-thumb-grade-present", exposure: "+0.3 EV", tone: "フィルミック" },
  { id: "contrast", name: "高コントラスト", thumb: "vi-thumb-grade-contrast", exposure: "+0.6 EV", tone: "フィルミック・強" },
] as const;
type GradeId = (typeof GRADES)[number]["id"];

function RenderingTab({ variant }: { variant: string }) {
  const failed = variant === "renderer-error";
  const [grade, setGrade] = useState<GradeId>(variant === "develop-grade" ? "presentation" : "measurement");
  const [scale, setScale] = useState(variant === "deformation" ? "50" : "1");
  const gradeDetail = GRADES.find((g) => g.id === grade) ?? GRADES[0];
  return (
    <div>
      {failed ? (
        <section className="prop-section">
          <div className="notice error" role="alert">
            <b>Omniverse バックエンドを開始できません</b>
            <span className="why">接続がありません。VTK 経路は引き続き利用でき、黙って切り替えません。</span>
          </div>
        </section>
      ) : null}
      <section className="prop-section">
        <h3>レンダラー</h3>
        <div className="prop-row">
          <label htmlFor="vi-renderer">方式</label>
          <select id="vi-renderer" className="field-input" defaultValue="vtk">
            <option value="vtk">リアルタイム・VTK</option>
            <option value="omniverse" disabled>フォトリアル・Omniverse（未接続のため選べません）</option>
          </select>
        </div>
        <div className="prop-row">
          <label>状態</label>
          <span>{failed ? "VTK のみ利用可能 — Omniverse は開始に失敗" : "VTK・利用可能・オフライン"}</span>
        </div>
        <div className="prop-row">
          <label htmlFor="vi-quality">品質</label>
          <select id="vi-quality" className="field-input" defaultValue="interactive">
            <option value="interactive">操作優先</option>
            <option value="balanced">標準</option>
            <option value="quality">品質優先</option>
          </select>
        </div>
        <p className="prop-note">未対応のレンダラーへ黙って切り替えません。どの経路で描いたかは出力の来歴に記録されます。</p>
      </section>
      <section className="prop-section">
        <h3>照明</h3>
        <div className="prop-row">
          <label htmlFor="vi-light">光源</label>
          <select id="vi-light" className="field-input" defaultValue="studio">
            <option value="studio">スタジオ</option>
            <option value="environment">背景の環境</option>
            <option value="unlit">照明なし</option>
          </select>
        </div>
        <div className="prop-row"><label>照明強度</label><span style={{ fontVariantNumeric: "tabular-nums" }}>100 %</span></div>
        <div className="prop-row"><label htmlFor="vi-shadow">影</label><input id="vi-shadow" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
      </section>
      <section className="prop-section">
        <h3>現像</h3>
        <div className="vi-sample-row" role="radiogroup" aria-label="現像プリセット">
          {GRADES.map((g) => (
            <button key={g.id} className="vi-sample" role="radio" aria-checked={grade === g.id} onClick={() => setGrade(g.id)}>
              <span className={`thumb ${g.thumb}`} aria-hidden />
              <span className="name" title={g.name}>{g.name}</span>
            </button>
          ))}
        </div>
        <div className="prop-row" style={{ marginTop: 6 }}><label>露光</label><span>{gradeDetail.exposure}</span></div>
        <div className="prop-row"><label>トーンマップ</label><span>{gradeDetail.tone}</span></div>
        {grade === "measurement" ? (
          <p className="prop-note">計測は未補正です。根拠として引用する画像はこの状態で出力し、凡例と画像の対応がそのまま保たれます。</p>
        ) : (
          <div className="notice warn">
            <b>補正を掛けた画像です</b>
            <span className="why">凡例も同じ補正を通すか、補正名とパラメータを成果物に記載します。計測・プローブの値は補正の影響を受けません。</span>
          </div>
        )}
      </section>
      <section className="prop-section">
        <h3>変形表示</h3>
        <div className="prop-row">
          <label htmlFor="vi-deformation">倍率</label>
          <select id="vi-deformation" className="field-input" value={scale} onChange={(event) => setScale(event.target.value)}>
            <option value="1">×1（実寸）</option>
            <option value="50">×50</option>
            <option value="200">×200</option>
          </select>
        </div>
        {scale !== "1" ? (
          <div className="notice warn">
            <b>変形を ×{scale} に誇張しています</b>
            <span className="why">倍率は画面内に描き込まれます。計測・プローブ・レポートの値は未変形形状から計算します（INV-024）。</span>
          </div>
        ) : (
          <p className="prop-note">倍率を上げると画面内に描き込まれ、値は未変形形状から計算されます（INV-024）。</p>
        )}
      </section>
      <section className="prop-section">
        <h3>画質</h3>
        <div className="prop-row">
          <label htmlFor="vi-aa">アンチエイリアス</label>
          <select id="vi-aa" className="field-input" defaultValue="taa">
            <option value="none">なし</option>
            <option value="fxaa">FXAA</option>
            <option value="taa">TAA</option>
          </select>
        </div>
        <div className="prop-row"><label>サンプル数</label><span style={{ fontVariantNumeric: "tabular-nums" }}>8</span></div>
      </section>
    </div>
  );
}

/* ---- background (XC-215): kinds chosen from drawn samples, names beneath ------------------- */

const BACKGROUND_KINDS = [
  { id: "solid", name: "単色", thumb: "vi-thumb-solid" },
  { id: "gradient", name: "グラデーション", thumb: "vi-thumb-gradient" },
  { id: "image", name: "画像", thumb: "vi-thumb-image" },
  { id: "environment", name: "環境", thumb: "vi-thumb-environment" },
] as const;
type BackgroundKind = (typeof BACKGROUND_KINDS)[number]["id"];

function BackgroundTab() {
  const [kind, setKind] = useState<BackgroundKind>("gradient");
  const current = BACKGROUND_KINDS.find((b) => b.id === kind) ?? BACKGROUND_KINDS[0];
  return (
    <div>
      <section className="prop-section">
        <h3>背景の種類</h3>
        <div className="vi-sample-row" role="radiogroup" aria-label="背景の種類">
          {BACKGROUND_KINDS.map((b) => (
            <button key={b.id} className="vi-sample" role="radio" aria-checked={kind === b.id} onClick={() => setKind(b.id)}>
              <span className={`thumb ${b.thumb}`} aria-hidden />
              <span className="name" title={b.name}>{b.name}</span>
            </button>
          ))}
        </div>
        <p className="prop-note">種類は名前ではなく描いた見本から選びます（XC-215）。名前は見本の下にあります。</p>
      </section>
      <section className="prop-section">
        <h3>設定 — {current.name}</h3>
        {kind === "solid" ? (
          <div className="prop-row">
            <label htmlFor="vi-bg-tone">明度</label>
            <select id="vi-bg-tone" className="field-input" defaultValue="dark">
              <option value="dark">暗い（既定）</option>
              <option value="mid">中間</option>
              <option value="light">明るい</option>
            </select>
          </div>
        ) : null}
        {kind === "gradient" ? (
          <>
            <div className="prop-row">
              <label htmlFor="vi-bg-dir">方向</label>
              <select id="vi-bg-dir" className="field-input" defaultValue="down">
                <option value="down">上から下へ暗く</option>
                <option value="up">下から上へ暗く</option>
              </select>
            </div>
            <div className="prop-row">
              <label htmlFor="vi-bg-contrast">対比</label>
              <select id="vi-bg-contrast" className="field-input" defaultValue="standard">
                <option value="weak">弱</option>
                <option value="standard">標準</option>
                <option value="strong">強</option>
              </select>
            </div>
          </>
        ) : null}
        {kind === "image" ? (
          <>
            <div className="prop-row"><label>画像</label><MissingDataStyle because="未選択" /></div>
            <div className="prop-row">
              <label htmlFor="vi-bg-fit">配置</label>
              <select id="vi-bg-fit" className="field-input" {...disabledBecause("画像が未選択です")} defaultValue="cover">
                <option value="cover">全体を覆う</option>
                <option value="contain">全体を表示</option>
                <option value="stretch">引き伸ばす</option>
              </select>
            </div>
            <div className="notice warn">
              <b>画像が未選択です</b>
              <span className="why">選ぶまで背景は既定のままです。代替の画像は使いません。</span>
            </div>
          </>
        ) : null}
        {kind === "environment" ? (
          <>
            <div className="prop-row">
              <label htmlFor="vi-bg-env">環境</label>
              <select id="vi-bg-env" className="field-input" defaultValue="studio">
                <option value="studio">スタジオ・サンプル</option>
              </select>
            </div>
            <div className="prop-row"><label>回転</label><span style={{ fontVariantNumeric: "tabular-nums" }}>0°</span></div>
            <p className="prop-note">照明に使う場合は、描画タブの光源で「背景の環境」を選びます。</p>
          </>
        ) : null}
        <div className="prop-row"><label>表示強度</label><span style={{ fontVariantNumeric: "tabular-nums" }}>100 %</span></div>
        <div className="prop-row"><label htmlFor="vi-bg-cam">カメラに表示</label><input id="vi-bg-cam" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
      </section>
      <section className="prop-section">
        <p className="prop-note" style={{ margin: 0 }}>再利用する背景は素材ライブラリから適用します。このタブは現在のビューへの配置だけを調整します。背景は表示状態で、値には触れません。</p>
      </section>
    </div>
  );
}

/* ---- output (XC-210/XC-212): what leaves the tool, and what refuses to ---------------------- */

function OutputTab({ variant }: { variant: string }) {
  const s = useSession();
  const spec = comparisonSpec(variant);
  const steady = variant === "steady-result";
  const motion = variant === "output-motion";
  const [mode, setMode] = useState<"image" | "video">(motion ? "video" : "image");
  const [presetId, setPresetId] = useState("full");
  const videoBlockedReason = steady
    ? "このケースは結果軸を持ちません"
    : spec?.positionAxis
      ? "結果位置を軸にした比較は再生する余地がありません"
      : null;
  const effectiveMode = videoBlockedReason !== null ? "image" : mode;
  const splitPanes = variant === "split-output" ? 2 : s.paneCount;
  return (
    <div>
      {(variant === "split-output" || (splitPanes > 1 && spec === null)) ? (
        <section className="prop-section">
          <div className="notice warn">
            <b>画面分割は書き出しに含まれません</b>
            <span className="why">
              いま {splitPanes} 画面に分けていますが、出力は下で選ぶカメラ 1 台の絵です。並べた図が必要な場合は、この分割を比較項目として保存します（XC-210）。
            </span>
          </div>
        </section>
      ) : null}
      <section className="prop-section">
        <h3>成果物</h3>
        <div className="prop-row">
          <label htmlFor="vi-out-kind">種類</label>
          <select
            id="vi-out-kind"
            className="field-input"
            value={effectiveMode}
            onChange={(event) => setMode(event.target.value === "video" ? "video" : "image")}
            title={videoBlockedReason !== null ? `動画は選べません：${videoBlockedReason}` : undefined}
          >
            <option value="image">画像</option>
            <option value="video" disabled={videoBlockedReason !== null}>
              動画{videoBlockedReason !== null ? "（選べません）" : ""}
            </option>
          </select>
        </div>
        {steady ? (
          <div className="notice warn">
            <b>ケース「Run 12」は定常結果です</b>
            <span className="why">再生する軸がないため、動画と再生プリセットは利用できません。画像とインタラクティブ出力は通常どおりです。</span>
          </div>
        ) : null}
        {spec?.positionAxis ? (
          <div className="notice warn">
            <b>この比較は結果位置を軸にしています</b>
            <span className="why">各ペインが別々の位置に固定されるため、再生する余地がなく動画にできません。軸をケースやカメラに変えると動画にできます（XC-212）。</span>
          </div>
        ) : null}
        {effectiveMode === "image" ? (
          <>
            <div className="prop-row">
              <label htmlFor="vi-out-format">形式</label>
              <select id="vi-out-format" className="field-input" defaultValue="png">
                <option value="png">PNG</option>
                <option value="jpeg">JPEG</option>
                <option value="tiff">TIFF</option>
              </select>
            </div>
            <div className="prop-row">
              <label htmlFor="vi-out-size">サイズ</label>
              <select id="vi-out-size" className="field-input" defaultValue="1920">
                <option value="1920">1920 × 1080</option>
                <option value="3840">3840 × 2160</option>
                <option value="viewport">現在の表示領域</option>
              </select>
            </div>
            {spec !== null ? (
              <>
                <div className="prop-row">
                  <label>カメラ</label>
                  <span className="type-caption" style={{ color: "var(--ink-muted)" }}>比較で共有 — 比較グループで設定（訊き直しません・XC-212）</span>
                </div>
                <div className="prop-row">
                  <label>結果位置</label>
                  <span className="type-caption" style={{ color: "var(--ink-muted)" }}>
                    {spec.positionAxis ? "比較の軸 — メンバーごとに固定" : "比較で共有 — 比較グループで設定"}
                  </span>
                </div>
              </>
            ) : (
              <>
                <div className="prop-row">
                  <label htmlFor="vi-out-camera">カメラ</label>
                  <select id="vi-out-camera" className="field-input" defaultValue="cam-iso">
                    <option value="cam-front">正面・全体</option>
                    <option value="cam-iso">等角・全体</option>
                    <option value="cam-peak">最大応力へ寄せる</option>
                    <option value="cam-fixture">治具アップ</option>
                  </select>
                </div>
                {steady ? (
                  /* The axis is absent, not disabled (XC-160): no position value is shown at all. */
                  <div className="prop-row"><label>結果位置</label><MissingDataStyle because="このケースは結果軸を持ちません" /></div>
                ) : (
                  <div className="prop-row">
                    <label htmlFor="vi-out-position">結果位置</label>
                    <select id="vi-out-position" className="field-input" defaultValue="current">
                      <option value="current">現在の位置（16.0 s）</option>
                      <option value="hold">ブックマーク：保持時間</option>
                      <option value="peak">ブックマーク：最大応力時</option>
                    </select>
                  </div>
                )}
              </>
            )}
          </>
        ) : (
          <>
            <div className="prop-row">
              <label htmlFor="vi-out-vformat">形式</label>
              <select id="vi-out-vformat" className="field-input" defaultValue="mp4">
                <option value="mp4">MP4</option>
                <option value="webm">WebM</option>
                <option value="frames">PNG 連番</option>
              </select>
            </div>
            <div className="prop-row">
              <label htmlFor="vi-out-vcamera">カメラ</label>
              <select id="vi-out-vcamera" className="field-input" defaultValue="cam-iso">
                <option value="cam-front">正面・全体</option>
                <option value="cam-iso">等角・全体</option>
                <option value="cam-peak">最大応力へ寄せる</option>
                <option value="cam-fixture">治具アップ</option>
              </select>
            </div>
          </>
        )}
      </section>
      {effectiveMode === "video" ? (
        <section className="prop-section">
          <h3>再生プリセット</h3>
          <div style={{ display: "grid", gap: 4 }}>
            {MOTION_PRESETS.map((preset) => (
              <button key={preset.id} className="vi-row" aria-selected={presetId === preset.id} onClick={() => setPresetId(preset.id)}>
                <b title={preset.name}>{preset.name}</b>
                <span className="rule">{preset.detail}</span>
              </button>
            ))}
          </div>
          <p className="prop-note">動画はプリセット 1 つとカメラ 1 台を名指しします（XC-200）。プリセットは「いつ」だけを持ち、「どこから」は上のカメラが持ちます。</p>
        </section>
      ) : null}
      <section className="prop-section">
        <h3>保存先</h3>
        <div className="prop-row">
          <label>パターン</label>
          <span style={{ fontFamily: "var(--family-mono)", fontSize: "var(--text-caption)", overflowWrap: "anywhere" }}>
            output/view/&lt;run&gt;/&lt;case&gt;/
          </span>
        </div>
        <div className="prop-row"><label>既存出力</label><span>上書きしない</span></div>
      </section>
      <section className="prop-section">
        <button className="btn primary" onClick={() => submit({ operation: "view.render", parameters: { mode: effectiveMode } })}>
          出力前チェックへ
        </button>
        <p className="prop-note">レンダラー・保存先・動画のカメラパス・時間対応を検査してから出力します。不足があれば開始しません。</p>
      </section>
    </div>
  );
}

/* ---- selection tabs: objects / text / materials -------------------------------------------- */

function ObjectsTab({ variant }: { variant: string }) {
  const kind = objectKindOf(variant);
  if (kind === null) {
    return (
      <div className="prop-section">
        <p className="prop-note" style={{ margin: 0 }}>
          オブジェクトが選択されていません。画面かアウトライナー（ビュータブ）で選ぶと、種類ごとの項目をここに表示します。
        </p>
      </div>
    );
  }
  const meta = OBJECT_META[kind];
  return (
    <div>
      <div className="vi-selection">
        <small>アクティブオブジェクト</small>
        <b title={meta.name}>{meta.name}</b>
        <em>{meta.label}</em>
      </div>
      <ObjectProperties kind={kind} />
      <section className="prop-section">
        <p className="prop-note" style={{ margin: 0 }}>オブジェクトの表示定義だけを編集します。元のデータセット、解析値、単位、来歴は変更しません。</p>
      </section>
    </div>
  );
}

function ObjectProperties({ kind }: { kind: ObjectKind }) {
  const [map, setMap] = useState<ColourMapId>("viridis");
  const [representation, setRepresentation] = useState("surface-edges");

  if (kind === "analysis-mesh" || kind === "reference-mesh") {
    const analysis = kind === "analysis-mesh";
    return (
      <>
        <section className="prop-section">
          <h3>メッシュ</h3>
          <div className="prop-row"><label>役割</label><span>{analysis ? "解析 — 値の器" : "参照 — 文脈の形状（解析値なし）"}</span></div>
          <div className="prop-row">
            <label>参照元</label>
            <span className="type-caption" style={{ color: "var(--ink-muted)" }}>
              {analysis ? "データセット「Run 12」・部品 2 件" : "参照形状「治具 CAD」"}
            </span>
          </div>
          {analysis ? null : (
            <div className="prop-row">
              <label htmlFor="vi-ref-role">表示役割</label>
              <select id="vi-ref-role" className="field-input" defaultValue="context">
                <option value="context">文脈（薄く描く）</option>
                <option value="silhouette">比較用シルエット</option>
              </select>
            </div>
          )}
        </section>
        <section className="prop-section">
          <h3>表示</h3>
          <div className="vi-sample-row" role="radiogroup" aria-label="表示形式">
            {[
              { id: "surface", name: "サーフェス", style: { background: "var(--surface-active)" } },
              { id: "surface-edges", name: "サーフェス＋エッジ", style: { background: "var(--surface-active)", boxShadow: "inset 0 0 0 2px var(--ink-faint)" } },
              { id: "wireframe", name: "ワイヤーフレーム", style: { boxShadow: "inset 0 0 0 2px var(--ink-faint)" } },
            ].map((rep) => (
              <button key={rep.id} className="vi-sample" role="radio" aria-checked={representation === rep.id} onClick={() => setRepresentation(rep.id)}>
                <span className="thumb" style={rep.style} aria-hidden />
                <span className="name" title={rep.name}>{rep.name}</span>
              </button>
            ))}
          </div>
          <div className="prop-row" style={{ marginTop: 6 }}>
            <label>不透明度</label>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>{analysis ? "100 %" : "35 %"}</span>
          </div>
          <div className="prop-row"><label htmlFor="vi-mesh-visible">表示する</label><input id="vi-mesh-visible" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
        </section>
        {representation !== "surface" ? (
          <section className="prop-section">
            <h3>エッジ</h3>
            <div className="prop-row"><label>幅</label><span style={{ fontVariantNumeric: "tabular-nums" }}>1 px</span></div>
            <div className="prop-row"><label>不透明度</label><span style={{ fontVariantNumeric: "tabular-nums" }}>100 %</span></div>
          </section>
        ) : null}
      </>
    );
  }

  if (kind === "point-cloud") {
    return (
      <>
        <section className="prop-section">
          <h3>点群</h3>
          <div className="prop-row">
            <label>参照元</label>
            <span style={{ display: "flex", gap: 6, alignItems: "baseline", minWidth: 0 }}>
              <span className="type-caption" style={{ color: "var(--ink-muted)", minWidth: 0 }}>計測点群「スキャン 04」・8,214 点</span>
              <ProvenanceBadge origin="measured" />
            </span>
          </div>
        </section>
        <section className="prop-section">
          <h3>表示</h3>
          <div className="prop-row"><label>点サイズ</label><span style={{ fontVariantNumeric: "tabular-nums" }}>3 px</span></div>
          <div className="prop-row">
            <label htmlFor="vi-pc-colour">色の結び付け</label>
            <select id="vi-pc-colour" className="field-input" defaultValue="uniform">
              <option value="uniform">一様色</option>
              <option value="field">値による色（フィールドを選ぶ）</option>
            </select>
          </div>
          <div className="prop-row"><label htmlFor="vi-pc-visible">表示する</label><input id="vi-pc-visible" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
        </section>
        <section className="prop-section">
          <p className="prop-note" style={{ margin: 0 }}>点群向けの項目だけを表示します。メッシュ用の表現やエッジはここに現れません。</p>
        </section>
      </>
    );
  }

  if (kind === "scalar-field") {
    return (
      <>
        <section className="prop-section">
          <h3>スカラー場</h3>
          <div className="prop-row">
            <label htmlFor="vi-sf-field">フィールド</label>
            <FieldSelector
              fields={[
                { name: "ミーゼス応力", association: "point", unit: "MPa" },
                { name: "変位", association: "point", unit: "mm" },
                { name: "要素応力", association: "cell", unit: "MPa" },
                { name: "ひずみエネルギー密度", association: "integrationPoint", unit: null },
              ]}
              value="ミーゼス応力"
              onChange={(name) => submit({ operation: "view.update", parameters: { field: name } })}
            />
          </div>
          <div className="prop-row"><label>位置</label><span>節点（ソースに従う）</span></div>
          <div className="prop-row">
            <label htmlFor="vi-sf-component">成分</label>
            <select id="vi-sf-component" className="field-input" defaultValue="magnitude">
              <option value="magnitude">大きさ</option>
              <option value="x">X</option>
              <option value="y">Y</option>
              <option value="z">Z</option>
            </select>
          </div>
          <div className="prop-row">
            <label>単位</label>
            <span style={{ display: "flex", gap: 6, alignItems: "baseline" }}>MPa <ProvenanceBadge origin="declared" /></span>
          </div>
        </section>
        <section className="prop-section">
          <h3>色と範囲</h3>
          <ColourMapControl value={map} onChange={setMap} />
          <div className="prop-row" style={{ marginTop: 6 }}>
            <label>範囲</label>
            <span style={{ display: "flex", gap: 6, alignItems: "baseline", fontVariantNumeric: "tabular-nums" }}>
              {SHARED_RANGE}（データ範囲） <ProvenanceBadge origin="computed" />
            </span>
          </div>
          <div className="prop-row"><label htmlFor="vi-sf-legend">凡例</label><input id="vi-sf-legend" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
          <p className="prop-note">フィールド・位置・成分・単位・カラーマップ・範囲・凡例で一つの結果表現です。節点平均は値を変えるため、平均か非平均かは凡例に明記されます（INV-032）。</p>
        </section>
      </>
    );
  }

  if (kind === "vector-field") {
    return (
      <>
        <section className="prop-section">
          <h3>ベクトル場</h3>
          <div className="prop-row"><label>参照元</label><span className="type-caption" style={{ color: "var(--ink-muted)" }}>変位（節点・mm 宣言）</span></div>
          <div className="prop-row">
            <label htmlFor="vi-vf-frame">成分座標系</label>
            <select id="vi-vf-frame" className="field-input" defaultValue="global">
              <option value="global">グローバル直交</option>
              <option value="local">要素ローカル</option>
              <option value="cylindrical">円筒</option>
            </select>
          </div>
        </section>
        <section className="prop-section">
          <h3>グリフ</h3>
          <div className="prop-row">
            <label htmlFor="vi-vf-glyph">形</label>
            <select id="vi-vf-glyph" className="field-input" defaultValue="arrow">
              <option value="arrow">矢印</option>
              <option value="line">線</option>
            </select>
          </div>
          <div className="prop-row">
            <label htmlFor="vi-vf-density">密度</label>
            <select id="vi-vf-density" className="field-input" defaultValue="mid">
              <option value="low">低</option>
              <option value="mid">中</option>
              <option value="high">高</option>
            </select>
          </div>
          <div className="prop-row"><label>スケール</label><span style={{ fontVariantNumeric: "tabular-nums" }}>明示・×500（画面上の長さ）</span></div>
          <p className="prop-note">スケールは表示専用です。値そのものは変わらず、プローブは元の値を返します。</p>
        </section>
      </>
    );
  }

  if (kind === "trajectory") {
    return (
      <>
        <section className="prop-section">
          <h3>積分の定義</h3>
          <div className="prop-row"><label>ベクトル場</label><MissingDataStyle because="未接続" /></div>
          <div className="prop-row"><label>シード</label><MissingDataStyle because="未定義" /></div>
          <div className="prop-row">
            <label htmlFor="vi-tr-integrator">積分器</label>
            <select id="vi-tr-integrator" className="field-input" defaultValue="rk45">
              <option value="rk45">Runge–Kutta 4/5</option>
              <option value="rk2">Runge–Kutta 2</option>
            </select>
          </div>
        </section>
        <section className="prop-section">
          <h3>表示の定義</h3>
          <div className="prop-row">
            <label htmlFor="vi-tr-rep">表現</label>
            <select id="vi-tr-rep" className="field-input" defaultValue="tube">
              <option value="tube">チューブ</option>
              <option value="line">線</option>
            </select>
          </div>
          <div className="prop-row"><label>太さ</label><span style={{ fontVariantNumeric: "tabular-nums" }}>1.0（表示単位）</span></div>
        </section>
        <section className="prop-section">
          <div className="notice warn">
            <b>描画条件が未解決です</b>
            <span className="why">ベクトル場とシードを指定するまで形状を生成しません。既定値で補いません。積分（何を計算するか）と表示（どう見せるか）は別の定義です。</span>
          </div>
        </section>
      </>
    );
  }

  if (kind === "annotation") {
    return (
      <>
        <section className="prop-section">
          <h3>注釈</h3>
          <div className="prop-row">
            <label htmlFor="vi-an-kind">種類</label>
            <select id="vi-an-kind" className="field-input" defaultValue="text">
              <option value="text">テキスト</option>
              <option value="dimension">寸法</option>
              <option value="point">点ラベル</option>
            </select>
          </div>
          <div className="prop-row"><label>アンカー</label><span>GlobalNodeId 20481（未変形座標）</span></div>
          <div className="prop-row">
            <label>来歴</label>
            <span style={{ display: "flex", gap: 6, alignItems: "baseline" }}>ユーザー入力 <ProvenanceBadge origin="declared" /></span>
          </div>
        </section>
        <section className="prop-section">
          <p className="prop-note" style={{ margin: 0 }}>内容と文字表現は、選択スコープの「テキスト」タブで編集します。</p>
        </section>
      </>
    );
  }

  // effect
  return (
    <>
      <section className="prop-section">
        <h3>エフェクト</h3>
        <div className="prop-row">
          <label htmlFor="vi-ef-kind">種類</label>
          <select id="vi-ef-kind" className="field-input" defaultValue="highlight">
            <option value="highlight">強調表示</option>
            <option value="glow">グロー</option>
            <option value="particles">パーティクル</option>
          </select>
        </div>
        <div className="prop-row"><label>対象</label><span>部品「ブラケット」</span></div>
        <div className="prop-row">
          <label htmlFor="vi-ef-strength">強さ</label>
          <select id="vi-ef-strength" className="field-input" defaultValue="mid">
            <option value="weak">弱</option>
            <option value="mid">標準</option>
            <option value="strong">強</option>
          </select>
        </div>
        <div className="prop-row"><label htmlFor="vi-ef-visible">表示する</label><input id="vi-ef-visible" type="checkbox" defaultChecked style={{ justifySelf: "start" }} /></div>
      </section>
      <section className="prop-section">
        <div className="notice">
          <b>表示専用</b>
          <span className="why">エフェクトは解析値を生成しません。強調は値の根拠にならず、出力の来歴にもそう記録されます。</span>
        </div>
      </section>
    </>
  );
}

function TextTab({ variant }: { variant: string }) {
  if (variant !== "object-annotation") {
    return (
      <div className="prop-section">
        <p className="prop-note" style={{ margin: 0 }}>
          テキストを持つオブジェクトが選択されていません。注釈を選ぶと、内容と文字表現をここで編集します。
        </p>
      </div>
    );
  }
  return (
    <div>
      <div className="vi-selection">
        <small>アクティブオブジェクト</small>
        <b title="注釈「最大応力ラベル」">注釈「最大応力ラベル」</b>
        <em>テキスト注釈</em>
      </div>
      <section className="prop-section">
        <h3>内容</h3>
        <div className="prop-row">
          <label htmlFor="vi-tx-kind">種類</label>
          <select id="vi-tx-kind" className="field-input" defaultValue="quantity">
            <option value="fixed">固定文</option>
            <option value="quantity">数量の差し込み</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="vi-tx-var">数量</label>
          <select id="vi-tx-var" className="field-input" defaultValue="probe">
            <option value="probe">変数「プローブ応力」</option>
            <option value="allow">変数「許容応力」</option>
          </select>
        </div>
        <div className="prop-row">
          <label>プレビュー</label>
          <span style={{ display: "flex", gap: 6, alignItems: "baseline", minWidth: 0 }}>
            <QuantityChip value="241.7" unit="MPa" />
            <ProvenanceBadge origin="computed" />
          </span>
        </div>
        <p className="prop-note">単位と桁は値の定義に従います。注釈側で桁を増やすことはできません（INV-014）。</p>
      </section>
      <section className="prop-section">
        <h3>文字表現</h3>
        <div className="prop-row">
          <label htmlFor="vi-tx-size">サイズ</label>
          <select id="vi-tx-size" className="field-input" defaultValue="mid">
            <option value="small">小</option>
            <option value="mid">中</option>
            <option value="large">大</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="vi-tx-place">配置</label>
          <select id="vi-tx-place" className="field-input" defaultValue="leader">
            <option value="leader">引き出し線つき</option>
            <option value="inline">その場</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="vi-tx-panel">背景</label>
          <select id="vi-tx-panel" className="field-input" defaultValue="panel">
            <option value="panel">半透明パネル</option>
            <option value="none">なし</option>
          </select>
        </div>
      </section>
    </div>
  );
}

function MaterialsTab({ variant }: { variant: string }) {
  const composition = variant === "material-composition";
  const kind = objectKindOf(variant);
  const [slotId, setSlotId] = useState(composition ? "stress-steel" : "plain");
  const [map, setMap] = useState<ColourMapId>("viridis");

  if (!composition && kind !== "analysis-mesh" && kind !== "reference-mesh") {
    return (
      <div className="prop-section">
        <p className="prop-note" style={{ margin: 0 }}>
          マテリアルを持つオブジェクトが選択されていません。画面かアウトライナーでメッシュを選ぶと、スロットと必須解析入力をここに表示します。
        </p>
      </div>
    );
  }

  if (!composition) {
    const meta = kind !== null ? OBJECT_META[kind] : OBJECT_META["analysis-mesh"];
    return (
      <div>
        <div className="vi-selection">
          <small>アクティブオブジェクト</small>
          <b title={meta.name}>{meta.name}</b>
          <em>{meta.label}</em>
        </div>
        <section className="prop-section">
          <h3>マテリアルスロット（1 件）</h3>
          <button className="vi-row" aria-selected={slotId === "plain"} onClick={() => setSlotId("plain")}>
            <b title="標準・つや消しグレー">標準・つや消しグレー</b>
            <span className="rule">対象：全体・OpenPBR Surface</span>
            <span className="state good">検証済み（構文・型・単位次元）</span>
          </button>
          <p className="prop-note">スロットを増やすと、面セットごとに別のマテリアルを割り当てられます。割り当ての狭い方が優先されます。</p>
        </section>
      </div>
    );
  }

  const slots = [
    { id: "stress-steel", name: "スチール＋応力コンター", target: "対象：全体・MaterialX（OpenPBR Surface）", state: "解析入力 stress_value・未接続", tone: "error" as const },
    { id: "brushed", name: "ブラッシュドスチール", target: "対象：面セット「機械加工面」・MaterialX", state: "検証済み（構文・型・単位次元）", tone: "good" as const },
  ];
  return (
    <div>
      <div className="vi-selection">
        <small>アクティブオブジェクト</small>
        <b title={OBJECT_META["analysis-mesh"].name}>{OBJECT_META["analysis-mesh"].name}</b>
        <em>{OBJECT_META["analysis-mesh"].label}</em>
      </div>
      <section className="prop-section">
        <h3>マテリアルスロット（2 件）</h3>
        <div style={{ display: "grid", gap: 4 }}>
          {slots.map((slot) => (
            <button key={slot.id} className="vi-row" aria-selected={slotId === slot.id} onClick={() => setSlotId(slot.id)}>
              <b title={slot.name}>{slot.name}</b>
              <span className="rule">{slot.target}</span>
              <span className={`state ${slot.tone}`}>{slot.state}</span>
            </button>
          ))}
        </div>
        <p className="prop-note">同じメッシュに複数スロットを重ねられます。割り当ての狭い方が優先されます。</p>
      </section>
      {slotId === "stress-steel" ? (
        <>
          <section className="prop-section">
            <h3>必須解析入力</h3>
            <div className="prop-row">
              <label>stress_value</label>
              <span className="type-caption" style={{ color: "var(--ink-muted)" }}>float・solvia:result/stress</span>
            </div>
            <div className="prop-row"><label>状態</label><MissingDataStyle because="ケース「Run 12」に接続されていません" /></div>
            <div className="notice error" role="alert" style={{ marginTop: 6 }}>
              <b>解析カラーを評価できません</b>
              <span className="why">
                必須入力 stress_value が未接続のため、解析カラー出力と外観プレビューは診断マゼンタで描かれます。通常の色に紛れて正しく見えることはありません（XC-175）。
              </span>
            </div>
          </section>
          <section className="prop-section">
            <h3>ベースカラー入力</h3>
            <div className="prop-row">
              <label htmlFor="vi-mat-input">入力</label>
              <select id="vi-mat-input" className="field-input" defaultValue="colormap">
                <option value="solid">単色</option>
                <option value="texture">画像</option>
                <option value="colormap">カラーマップ（解析結果）</option>
                <option value="formula">式</option>
              </select>
            </div>
            <ColourMapControl value={map} onChange={setMap} />
            <div className="prop-row" style={{ marginTop: 6 }}>
              <label>範囲</label>
              <span style={{ display: "flex", gap: 6, alignItems: "baseline", fontVariantNumeric: "tabular-nums" }}>
                {SHARED_RANGE} <ProvenanceBadge origin="computed" />
              </span>
            </div>
          </section>
        </>
      ) : (
        <section className="prop-section">
          <h3>検証</h3>
          <div className="prop-row">
            <label>構文・型・単位次元</label>
            <span style={{ color: "var(--state-good)" }}>読み込み時に検証済み</span>
          </div>
          <p className="prop-note">編集すると保存前に再検証します。検証を通らないリビジョンは保存されません。</p>
        </section>
      )}
    </div>
  );
}
