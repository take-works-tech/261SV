/* Home (mockup 2, design states - never evidence of implemented behaviour).
 *
 * The application page outside any workspace (XC-165): the workspace list, the first-run state,
 * and the import path. Five variants (catalog.ts):
 *   default         - search, tag filter, grid/list of workspace cards, 開く / 新規作成
 *   first-run       - the bundled samples first, then the empty workspace with a drop zone
 *   import-review   - before anything loads: support level (Verified/Offered, XC-049), field
 *                     associations as the file states them, units named undeclared (XC-003),
 *                     coordinate frame, and proposed grouping/tags applied only on accept (XC-120)
 *   importing       - a cancellable read with the file named; the source is never modified
 *   unreadable-file - the named rejection with its reason; no partial case exists (XC-007)
 */
import { useState } from "react";
import { session } from "../../state/session";
import { submit } from "../../client/operations";
import { formatBytes, disabledBecause } from "../../logic/format";
import { UnitLabel } from "../../shared/UnitLabel";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { ProgressAndCancel } from "../../shared/ProgressAndCancel";
import "./HomeScreen.css";

/* ---- illustrative data (design states; counts and dates are examples, not measurements) ------ */

type WorkspaceCard = {
  id: string;
  name: string;
  description: string;
  tag: string;
  scope: "ローカル" | "共有";
  cases: number;
  updated: string;
};

const WORKSPACES: readonly WorkspaceCard[] = [
  {
    id: "ws-bracket",
    name: "冷却ブラケット検討",
    description: "静解析 12 ケースの設計比較。ケース、ビュー、レポートを 1 つにまとめた設計スタディ。",
    tag: "構造",
    scope: "ローカル",
    cases: 12,
    updated: "2026-08-27 14:02",
  },
  {
    id: "ws-manifold",
    name: "マニホールド流量検証",
    description: "入口条件を振った定常流れの流量検証。グラフとパイプラインを含む。",
    tag: "流体",
    scope: "ローカル",
    cases: 8,
    updated: "2026-08-25 09:41",
  },
  {
    id: "ws-housing",
    name: "筐体熱解析",
    description: "発熱条件ごとの温度分布と、提出用レポートの構成を管理。",
    tag: "熱",
    scope: "ローカル",
    cases: 5,
    updated: "2026-08-21 17:26",
  },
  {
    id: "ws-airfoil",
    name: "翼型空力検討",
    description: "迎角スイープ 24 ケースの比較ビューと係数グラフ。",
    tag: "流体",
    scope: "ローカル",
    cases: 24,
    updated: "2026-08-18 11:03",
  },
  {
    id: "ws-weld",
    name: "溶接継手の疲労評価（M8 ボルト締結・熱サイクル併用の長期評価シリーズ）",
    description: "長期シリーズの継続ワークスペース。名称が長いため一覧では省略表示になる。",
    tag: "構造",
    scope: "ローカル",
    cases: 31,
    updated: "2026-07-30 16:48",
  },
  {
    id: "ws-correlation",
    name: "試験相関スタディ",
    description: "実測データと解析結果の相関確認。実測値は由来つきで保持。",
    tag: "実測相関",
    scope: "共有",
    cases: 4,
    updated: "2026-08-26 08:15",
  },
];

const SCOPE_FILTERS = ["すべて", "ローカル", "共有"] as const;
type ScopeFilter = (typeof SCOPE_FILTERS)[number];

type ImportFile = {
  name: string;
  bytes: number;
  tierLabel: "Verified" | "Offered";
  tierNote: string;
};

const IMPORT_FILES: readonly ImportFile[] = [
  {
    name: "bracket_run12.cgns",
    bytes: 25795000,
    tierLabel: "Verified",
    tierNote: "回帰テストが実ファイルを開き、値を検証している形式です。",
  },
  {
    name: "manifold_v3_0012.foam",
    bytes: 851870000,
    tierLabel: "Offered",
    tierNote: "VTK の OpenFOAM リーダーで読み込みます。既知の制限：ラグランジュ粒子データは読み込まれません。",
  },
];

type ImportField = {
  field: string;
  file: string;
  assoc: "点" | "セル" | "積分点";
  components: string;
};

const IMPORT_FIELDS: readonly ImportField[] = [
  { field: "Displacement", file: "bracket_run12.cgns", assoc: "点", components: "3 成分" },
  { field: "VonMisesStress", file: "bracket_run12.cgns", assoc: "積分点", components: "1 成分" },
  { field: "p", file: "manifold_v3_0012.foam", assoc: "セル", components: "1 成分" },
  { field: "U", file: "manifold_v3_0012.foam", assoc: "セル", components: "3 成分" },
];

const TAG_PROPOSALS: readonly { tag: string; basis: string }[] = [
  { tag: "Run 12", basis: "ファイル名の連番と更新日時から" },
  { tag: "静解析", basis: "CGNS の SimulationType（NonTimeAccurate）から" },
  { tag: "1.2M セル", basis: "ヘッダー記載の要素数 1,204,318 から" },
];

const SAMPLES: readonly { id: string; name: string; meta: string; description: string }[] = [
  {
    id: "sample-bracket",
    name: "冷却ブラケット（サンプル）",
    meta: "静解析・ケース 3件",
    description: "画面と操作を確認するための一般化データ。",
  },
  {
    id: "sample-manifold",
    name: "マニホールド（サンプル）",
    meta: "定常流れ・ケース 2件",
    description: "比較ビューとグラフの操作を確認するサンプル。",
  },
];

/* ---- small inline glyphs (monochrome, stroke = currentColor) -------------------------------- */

function SearchGlyph() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="m20.5 20.5-4.2-4.2" />
    </svg>
  );
}

function GridGlyph() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <rect x="4" y="4" width="7" height="7" /><rect x="13" y="4" width="7" height="7" />
      <rect x="4" y="13" width="7" height="7" /><rect x="13" y="13" width="7" height="7" />
    </svg>
  );
}

function ListGlyph() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function DropGlyph() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 15V4m0 11-4-4m4 4 4-4" />
      <path d="M4 19h16" />
    </svg>
  );
}

/* ---- default: the workspace list ------------------------------------------------------------ */

function WorkspaceList() {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<ScopeFilter>("すべて");
  const [tags, setTags] = useState<string[]>([]);
  const [layout, setLayout] = useState<"grid" | "list">("grid");
  const [filterOpen, setFilterOpen] = useState(false);

  /* The tags offered are the ones the listed workspaces actually carry - the picker never
   * proposes a tag no card has (same honesty rule as a filter that quietly returns everything). */
  const availableTags = Array.from(new Set(WORKSPACES.map((workspace) => workspace.tag)));

  const visible = WORKSPACES
    .filter((workspace) => `${workspace.name} ${workspace.description} ${workspace.tag}`.includes(query.trim()))
    .filter((workspace) => scope === "すべて" || workspace.scope === scope)
    .filter((workspace) => tags.length === 0 || tags.includes(workspace.tag));

  const filtersActive = query.trim() !== "" || scope !== "すべて" || tags.length > 0;

  const openWorkspace = (id: string) => {
    submit({ operation: "workspace.open", parameters: { workspace: id } });
    session.openWorkspace();
  };
  /* CT-003 has no workspace.create operation yet; the design state dispatches the open
   * operation with a create parameter so the action still goes through the one path (INV-006). */
  const createWorkspace = () => {
    submit({ operation: "workspace.open", parameters: { create: true } });
  };

  return (
    <div className="ho-page">
      <div className="ho-inner">
        <header className="ho-head">
          <div>
            <h1>ワークスペース一覧</h1>
            <p className="ho-sub">解析プロジェクトを整理・検索して開きます。</p>
          </div>
          <div className="ho-tools">
            <label className="ho-search">
              <SearchGlyph />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="名前・説明・タグで検索"
                aria-label="ワークスペースを検索"
              />
            </label>
            <div className="ho-filter-anchor">
              <button
                className="btn ghost"
                aria-expanded={filterOpen}
                aria-haspopup="listbox"
                onClick={() => setFilterOpen((open) => !open)}
              >
                タグで絞り込み{tags.length > 0 ? `（${tags.length}）` : ""}
              </button>
              {filterOpen ? (
                <div className="popover ho-filter-pop">
                  <header>
                    <b>タグで絞り込み</b>
                    {tags.length > 0 ? (
                      <button className="btn ghost" style={{ marginLeft: "auto" }} onClick={() => setTags([])}>
                        すべて解除
                      </button>
                    ) : null}
                  </header>
                  <div className="body">
                    <ul className="ho-tag-listbox" role="listbox" aria-label="ワークスペースのタグ" aria-multiselectable="true">
                      {availableTags.map((tag) => {
                        const selected = tags.includes(tag);
                        return (
                          <li key={tag} role="option" aria-selected={selected}>
                            <button
                              onClick={() =>
                                setTags((current) =>
                                  current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag],
                                )
                              }
                            >
                              <span>{tag}</span>
                              {selected ? <span aria-hidden>✓</span> : null}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </div>
              ) : null}
            </div>
            <div className="ho-seg" role="group" aria-label="表示形式">
              <button aria-label="グリッド表示" aria-pressed={layout === "grid"} onClick={() => setLayout("grid")}>
                <GridGlyph />
              </button>
              <button aria-label="リスト表示" aria-pressed={layout === "list"} onClick={() => setLayout("list")}>
                <ListGlyph />
              </button>
            </div>
            <button className="btn primary" onClick={createWorkspace}>＋ 新規作成</button>
          </div>
        </header>

        <div className="ho-filters">
          {SCOPE_FILTERS.map((item) => (
            <button key={item} className="ho-chip" aria-pressed={scope === item} onClick={() => setScope(item)}>
              {item}
            </button>
          ))}
          {tags.map((tag) => (
            <button
              key={tag}
              className="ho-chip"
              aria-pressed
              aria-label={`タグ「${tag}」の絞り込みを解除`}
              onClick={() => setTags((current) => current.filter((item) => item !== tag))}
            >
              {tag} ✕
            </button>
          ))}
          <span className="ho-result-count">{visible.length} / {WORKSPACES.length} 件</span>
        </div>

        {visible.length > 0 ? (
          <div className={layout === "list" ? "ho-cards ho-list" : "ho-cards"}>
            {visible.map((workspace) => (
              <button key={workspace.id} className="ho-card" title={workspace.name} onClick={() => openWorkspace(workspace.id)}>
                <span className="ho-card-kind">ワークスペース</span>
                <h2 className="ho-card-name">{workspace.name}</h2>
                <p className="ho-card-desc">{workspace.description}</p>
                <span className="ho-card-tags">
                  <span className="ho-tag">{workspace.tag}</span>
                  <span className="ho-tag">{workspace.scope}</span>
                </span>
                <span className="ho-card-meta">
                  <span>ケース {workspace.cases}件</span>
                  <span>更新 {workspace.updated}</span>
                  <span className="ho-open">開く ↗</span>
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="ho-empty">
            <h2>一致するワークスペースがありません</h2>
            <p>
              {[
                query.trim() !== "" ? `検索「${query.trim()}」` : null,
                scope !== "すべて" ? `範囲「${scope}」` : null,
                tags.length > 0 ? `タグ「${tags.join("・")}」` : null,
              ]
                .filter((part): part is string => part !== null)
                .join("、")}
              の条件に一致するものはありません。条件を変更するか、解除してください。
            </p>
            {filtersActive ? (
              <button
                className="btn"
                onClick={() => {
                  setQuery("");
                  setScope("すべて");
                  setTags([]);
                }}
              >
                検索と絞り込みを解除
              </button>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- first-run: samples first, then the empty workspace with a drop zone -------------------- */

function FirstRun() {
  const openSample = (id: string) => {
    submit({ operation: "workspace.open", parameters: { workspace: id } });
    session.openWorkspace();
  };
  const pickFiles = () => {
    submit({ operation: "dataset.describe", parameters: { source: "file-picker" } });
    session.navigate("home", "import-review");
  };

  return (
    <div className="ho-page">
      <div className="ho-inner ho-narrow">
        <span className="ho-eyebrow">初回起動</span>
        <header className="ho-head">
          <h1>最初のワークスペースを開く</h1>
        </header>
        <p className="ho-lead">
          サンプルで画面と操作を確認するか、空のワークスペースに解析結果を取り込みます。
        </p>

        <section className="ho-section" aria-label="サンプルから始める">
          <h2>サンプルから始める</h2>
          <p className="ho-section-note">サンプルの数値は操作確認用の一般化データで、実測・実解析の結果ではありません。</p>
          <div className="ho-samples">
            {SAMPLES.map((sample) => (
              <button key={sample.id} className="ho-card" title={sample.name} onClick={() => openSample(sample.id)}>
                <span className="ho-card-kind">サンプル</span>
                <h2 className="ho-card-name">{sample.name}</h2>
                <p className="ho-card-desc">{sample.description}</p>
                <span className="ho-card-meta">
                  <span>{sample.meta}</span>
                  <span className="ho-open">開く ↗</span>
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="ho-section" aria-label="空のワークスペースに取り込む">
          <h2>空のワークスペースに取り込む</h2>
          <button className="ho-drop" onClick={pickFiles}>
            <DropGlyph />
            <b>結果ファイルをここへドロップ</b>
            <span>またはクリックしてファイルを選択</span>
            <small>対応可否は読み込む前に、形式ごとに表示します。</small>
          </button>
          <p className="ho-trust">元ファイルは変更せず、単位・座標系・階層をファイル名から推測しません。</p>
        </section>
      </div>
    </div>
  );
}

/* ---- import-review: everything stated before anything loads --------------------------------- */

function ImportReviewDialog() {
  const [groupingAccepted, setGroupingAccepted] = useState<boolean | null>(null);
  const [acceptedTags, setAcceptedTags] = useState<string[]>([]);
  const [rejectedTags, setRejectedTags] = useState<string[]>([]);

  const visibleProposals = TAG_PROPOSALS.filter((proposal) => !rejectedTags.includes(proposal.tag));

  const cancel = () => session.navigate("home", "default");
  const load = () => {
    submit({
      operation: "dataset.load",
      parameters: {
        files: IMPORT_FILES.map((file) => file.name),
        tags: acceptedTags,
        grouping: groupingAccepted === true,
      },
    });
    session.navigate("home", "importing");
  };

  return (
    <div className="dialog-scrim">
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="ho-import-review-title">
        <header>
          <h2 id="ho-import-review-title">取込前確認</h2>
          <button className="icon-button" aria-label="取込を取りやめて閉じる" onClick={cancel}>✕</button>
        </header>
        <div className="body">
          <p className="ho-trust ho-review-lead">まだ何も読み込んでいません。元ファイルは変更せず、単位・座標系をファイル名から推測しません。</p>

          <section className="ho-review-section" aria-label="ファイルと対応レベル">
            <h3>ファイルと対応レベル</h3>
            {IMPORT_FILES.map((file) => (
              <div key={file.name} className="ho-file-row wrap">
                <span className="ho-file-name" title={file.name}>{file.name}</span>
                <span className={file.tierLabel === "Verified" ? "ho-tier verified" : "ho-tier"}>{file.tierLabel}</span>
                <span className="ho-file-meta">{formatBytes(file.bytes)}</span>
                <p className="ho-file-note">{file.tierNote}</p>
              </div>
            ))}
          </section>

          <section className="ho-review-section" aria-label="フィールドの関連">
            <h3>フィールドの関連</h3>
            <p className="ho-review-note">
              <ProvenanceBadge origin="dataset" /> 関連（点・セル・積分点）と成分はファイル記載のまま表示し、推測や平均化は行いません。
            </p>
            <div className="table-scroll">
              <table className="value-table">
                <thead>
                  <tr>
                    <th>フィールド</th>
                    <th>ファイル</th>
                    <th>関連</th>
                    <th>成分</th>
                    <th>単位</th>
                  </tr>
                </thead>
                <tbody>
                  {IMPORT_FIELDS.map((row) => (
                    <tr key={`${row.file}/${row.field}`}>
                      <td><span className="ho-code">{row.field}</span></td>
                      <td><span className="ho-code">{row.file}</span></td>
                      <td>{row.assoc}</td>
                      <td>{row.components}</td>
                      <td><UnitLabel unit={null} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="ho-actions">
              <button className="btn" {...disabledBecause("単位の宣言は取込後に、フィールドごとに行います")}>
                単位を宣言
              </button>
              <span className="ho-review-note">
                単位はファイルから読み取れないため未宣言のままです。宣言するまで換算・比較は無効です。
              </span>
            </div>
          </section>

          <section className="ho-review-section" aria-label="座標フレーム">
            <h3>座標フレーム</h3>
            <div className="ho-frame-row">
              <span className="ho-file-name">bracket_run12.cgns</span>
              <span className="missing-value">記載なし</span>
              <span className="ho-review-note">取込後に宣言するまで、座標は変換なしで表示します。</span>
            </div>
            <div className="ho-frame-row">
              <span className="ho-file-name">manifold_v3_0012.foam</span>
              <span>右手系・Z 上（OpenFOAM の規約）</span>
              <ProvenanceBadge origin="reference" />
              <span className="ho-review-note">規約からの参考表示で、宣言ではありません。確定は取込後の宣言で行います。</span>
            </div>
          </section>

          <section className="ho-review-section" aria-label="提案された分類とタグ">
            <h3>提案された分類とタグ</h3>
            <p className="ho-review-note">読み取れた内容からの提案です。受け入れるまで何も適用しません。</p>
            <div className="ho-proposal">
              <span className="ho-proposal-kind">分類</span>
              <p>選択した 2 ファイルを 1 つの設計スタディとしてまとめる（根拠：同一フォルダー・連続する更新日時）</p>
              <div className="ho-proposal-actions">
                <button className="btn" aria-pressed={groupingAccepted === true} onClick={() => setGroupingAccepted(true)}>
                  受け入れる
                </button>
                <button className="btn ghost" aria-pressed={groupingAccepted === false} onClick={() => setGroupingAccepted(false)}>
                  今回は使わない
                </button>
              </div>
            </div>
            <ul className="ho-tag-proposals">
              {visibleProposals.map((proposal) => (
                <li key={proposal.tag}>
                  <label>
                    <input
                      type="checkbox"
                      checked={acceptedTags.includes(proposal.tag)}
                      onChange={(event) =>
                        setAcceptedTags((current) =>
                          event.target.checked ? [...current, proposal.tag] : current.filter((tag) => tag !== proposal.tag),
                        )
                      }
                    />
                    <b>{proposal.tag}</b>
                    <small>{proposal.basis}</small>
                  </label>
                  <button
                    className="ho-dismiss"
                    aria-label={`「${proposal.tag}」の提案をこのセッションでは出さない`}
                    onClick={() => {
                      setRejectedTags((current) => [...current, proposal.tag]);
                      setAcceptedTags((current) => current.filter((tag) => tag !== proposal.tag));
                    }}
                  >
                    ✕
                  </button>
                </li>
              ))}
              {visibleProposals.length === 0 ? (
                <li>
                  <p className="ho-review-note">提案はすべて却下しました。このセッションでは再提案しません。</p>
                </li>
              ) : null}
            </ul>
          </section>
        </div>
        <footer>
          <small className="ho-footer-note">
            この画面では何も適用していません。取り込むと、受け入れた提案（タグ {acceptedTags.length} 件・分類{" "}
            {groupingAccepted === true ? 1 : 0} 件）のみ適用します。
          </small>
          <button className="btn ghost" onClick={cancel}>取りやめ</button>
          <button className="btn primary" onClick={load}>取り込む</button>
        </footer>
      </div>
    </div>
  );
}

/* ---- importing: a cancellable read, the source untouched ------------------------------------ */

const IMPORT_STEPS = [
  { name: "ヘッダーと構造の読取", state: "完了", now: false },
  { name: "データ配列の完全性検証", state: "実行中", now: true },
  { name: "ケースの作成", state: "未着手（検証完了後）", now: false },
] as const;

function ImportingState() {
  /* CT-003 has no dedicated cancel operation for a dataset load yet; the design state
   * dispatches the load operation with a cancel parameter through the one path (INV-006). */
  const cancelRead = () => {
    submit({ operation: "dataset.load", parameters: { file: "bracket_run12.cgns", action: "cancel" } });
    session.navigate("home", "default");
  };

  return (
    <div className="ho-state">
      <div className="ho-state-card">
        <h2>データセットの取込</h2>
        <ProgressAndCancel
          label="読み込み中"
          detail="2 ファイル中 1 件目 — 62%"
          fraction={0.62}
          onCancel={cancelRead}
          cancelNote="キャンセルはケース境界で停止し、部分ケースを残しません"
        />
        <div className="ho-file-row">
          <span className="ho-file-name" title="bracket_run12.cgns">bracket_run12.cgns</span>
          <span className="ho-file-meta">検証中 — {formatBytes(16040000)} / {formatBytes(25795000)}</span>
        </div>
        <div className="ho-file-row">
          <span className="ho-file-name" title="manifold_v3_0012.foam">manifold_v3_0012.foam</span>
          <span className="ho-file-meta">待機中 — {formatBytes(851870000)}</span>
        </div>
        <ul className="ho-steps">
          {IMPORT_STEPS.map((step) => (
            <li key={step.name} className={step.now ? "now" : undefined}>
              <span className="st">{step.state}</span>
              <span>{step.name}</span>
            </li>
          ))}
        </ul>
        <p className="ho-trust">元ファイルは変更しません。キャンセルしても部分ケースは残りません。</p>
      </div>
    </div>
  );
}

/* ---- unreadable-file: the named rejection, and no partial case (XC-007) --------------------- */

function UnreadableFileState() {
  const pickAnother = () => {
    submit({ operation: "dataset.describe", parameters: { source: "file-picker" } });
    session.navigate("home", "import-review");
  };

  return (
    <div className="ho-state">
      <div className="ho-state-card">
        <h2>データセットの取込</h2>
        <div className="notice error" role="alert">
          <b>ファイルを読み込めませんでした</b>
          <span className="why">読み取れた範囲から不確かなケースは作りません。拒否した内容は下に記載しています。</span>
        </div>
        <dl className="ho-facts">
          <dt>ファイル</dt>
          <dd><span className="ho-code">bracket_run12_partial.cgns</span>（{formatBytes(25795000)}）</dd>
          <dt>認識した形式</dt>
          <dd>CGNS（対応レベル Verified）</dd>
          <dt>理由</dt>
          <dd>
            ノード <span className="ho-code">/Base/Zone1/FlowSolution/Pressure</span> の DataArray が、
            宣言サイズ 3,145,728 バイトに対し 1,048,576 バイトで終了しています（転送の中断が疑われます）。
          </dd>
          <dt>作成されたケース</dt>
          <dd>なし — 部分ケースは作成しません。</dd>
          <dt>元ファイル</dt>
          <dd>変更していません。</dd>
        </dl>
        <div className="ho-actions">
          <button className="btn primary" onClick={pickAnother}>別のファイルを選ぶ</button>
          <button className="btn ghost" onClick={() => session.navigate("home", "default")}>
            ワークスペース一覧へ戻る
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---- the screen ----------------------------------------------------------------------------- */

export function HomeScreen(props: { variant: string }) {
  switch (props.variant) {
    case "first-run":
      return <FirstRun />;
    case "importing":
      return <ImportingState />;
    case "unreadable-file":
      return <UnreadableFileState />;
    case "import-review":
      return (
        <>
          <WorkspaceList />
          <ImportReviewDialog />
        </>
      );
    default:
      return <WorkspaceList />;
  }
}
