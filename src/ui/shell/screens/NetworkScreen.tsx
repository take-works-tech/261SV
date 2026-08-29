/* Network and audit (XC-106, 11_ui.md "Network and audit").
 *
 * What may leave the machine, and what has. The centre owns the permission-state summary and the
 * local audit record; the right rail owns the controls that change them (permissions: workspace
 * toggles and the revocable per-host allow list; audit: scope and storage) and never restates the
 * summary as read-only text. One audit dataset feeds both, so they cannot contradict each other.
 *
 * Honesty rules made visible here: a request that was not sent is a stated record with its exact
 * content, never a silent nothing (XC-106); refusal names the host and the request; a review shows
 * the full content before anything leaves, with sensitive items (case names, values, file paths)
 * individually redactable; the audit stays local and leaves only by explicit export.
 *
 * Variants: default (permission state + audit table), offline (search not permitted by default and
 * how to permit it), refused (the refused host and request, nothing sent), request-review (one
 * request reviewed in full before a judgement).
 */
import { useState } from "react";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import type { Provenance } from "../../shared/primitives";
import { submit } from "../../client/operations";
import { formatBytes, disabledBecause } from "../../logic/format";
import "./NetworkScreen.css";

/* ---- the one audit dataset (centre and rail both read it) --------------------------------- */

type Outcome = "sent" | "refused" | "awaiting" | "not-sent";

const outcomeLabel: Record<Outcome, string> = {
  sent: "送信",
  refused: "拒否",
  awaiting: "確認待ち",
  "not-sent": "未送信",
};

type AuditRow = {
  id: string;
  at: string; // local time to the second - the audit is a record, not an estimate
  purpose: string;
  host: string;
  outcome: Outcome;
  content: string; // the exact content, verbatim (XC-106)
  note: string;
};

const baseRows: readonly AuditRow[] = [
  {
    id: "a-0912",
    at: "2026-08-29 09:12:05",
    purpose: "文書検索",
    host: "docs.example.org",
    outcome: "not-sent",
    content: "検索語「SUS304 板厚3 mm 疲労限度 平均応力補正」",
    note: "記録時点で外部通信が未許可・端末外へ出た情報はありません",
  },
  {
    id: "a-1703",
    at: "2026-08-28 17:03:41",
    purpose: "更新確認",
    host: "update.example.org",
    outcome: "not-sent",
    content: "照会内容：アプリのバージョン 0.4.1（それ以外の情報を含まない）",
    note: "記録時点で外部通信が未許可・確認は行われていません",
  },
];

const refusedRow: AuditRow = {
  id: "a-1102",
  at: "2026-08-29 11:02:36",
  purpose: "文書検索",
  host: "example.invalid",
  outcome: "refused",
  content: "検索語「アルミブラケット 溶接部 応力評価 手順」",
  note: "許可ホスト一覧に未登録・要求は送信していません",
};

const sentRow: AuditRow = {
  id: "a-1108",
  at: "2026-08-29 11:08:52",
  purpose: "文書検索",
  host: "docs.example.org",
  outcome: "sent",
  content: "検索語「JIS G 4305 SUS304 機械的性質」",
  note: "機密項目なし・許可（今回）で送信",
};

const awaitingRow: AuditRow = {
  id: "a-1124",
  at: "2026-08-29 11:24:09",
  purpose: "文書検索",
  host: "docs.example.org",
  outcome: "awaiting",
  content:
    "検索語「SUS304 板厚3 mm 疲労限度 平均応力補正」＋文脈3項目（ケース名・計算値・ファイルパス）",
  note: "機密3項目が確認待ち・確認が済むまで送信しません",
};

function auditRowsFor(variant: string): readonly AuditRow[] {
  if (variant === "offline") return [];
  if (variant === "refused") return [refusedRow, ...baseRows];
  if (variant === "request-review") return [awaitingRow, sentRow, ...baseRows];
  return baseRows;
}

/** Permission state per design state. Granted variants show the audit of a workspace where
 *  external communication was enabled after the morning's refused-by-default records. */
function permissionFor(variant: string): { external: boolean; hosts: readonly string[] } {
  const granted = variant === "refused" || variant === "request-review";
  return { external: granted, hosts: granted ? ["docs.example.org"] : [] };
}

function countByOutcome(rows: readonly AuditRow[]): Record<Outcome, number> {
  const counts: Record<Outcome, number> = { sent: 0, refused: 0, awaiting: 0, "not-sent": 0 };
  for (const row of rows) counts[row.outcome] += 1;
  return counts;
}

/* ---- the request under review (request-review variant) ------------------------------------ */

type Decision = "allow-once" | "allow-always" | "refuse";

type ReviewItem = {
  id: string;
  kind: "ケース名" | "計算値" | "ファイルパス";
  /** The exact string that would be sent for this item - shown verbatim, highlighted. */
  preview: string;
  origin: Provenance;
};

const reviewItems: readonly ReviewItem[] = [
  { id: "case-name", kind: "ケース名", preview: "Run 12（荷重 2.5倍）", origin: "declared" },
  {
    id: "value",
    kind: "計算値",
    preview: "最大 von Mises 応力 241.7 MPa（未平均・完全データから計算）",
    origin: "computed",
  },
  { id: "path", kind: "ファイルパス", preview: "D:\\projects\\bracket\\run12_result.vtu", origin: "dataset" },
];

/* ---- shared checklist: what granting external communication means -------------------------- */

function GrantChecklist() {
  return (
    <ul className="ne-grant-list">
      <li>
        <b>既定</b>
        <span>要求ごとに、正確な送信内容と宛先を送信前に表示します</span>
      </li>
      <li>
        <b>機密情報</b>
        <span>ケース名・値・ファイルパスは、要求ごとの追加許可が必要です</span>
      </li>
      <li>
        <b>監査</b>
        <span>送信内容・ホスト・日時・判断をローカルにのみ記録します</span>
      </li>
    </ul>
  );
}

/* ---- centre: offline ----------------------------------------------------------------------- */

function OfflineState() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [granted, setGranted] = useState(false);

  if (granted) {
    return (
      <div className="empty-state ne-offline">
        <span className="offline-chip">
          <span className="dot" />
          外部通信 — 有効（要求ごとに確認）
        </span>
        <h2>まだ何も送信していません</h2>
        <p>
          許可は送信そのものではありません。要求が発生すると、正確な内容と宛先を表示してから
          判断を求めます。宛先が許可ホスト一覧に無い要求は送信されません。
        </p>
      </div>
    );
  }

  return (
    <div className="empty-state ne-offline">
      <span className="offline-chip">
        <span className="dot" />
        オフライン — 既定
      </span>
      <h2>検索は許可されていません</h2>
      <p>
        既定では何も端末外へ送りません。文書検索とリモートアシスタント要求は実行されず、
        実行しようとした要求は「未送信」として、その全文がローカル監査に残ります。
      </p>
      <ol className="ne-steps">
        <li>
          右の<b>「許可」タブ</b>でワークスペース権限「外部通信」を有効にします —
          確認が先に、この許可が何を意味するかを示します。
        </li>
        <li>
          必要なら<b>Web検索</b>を有効にし、宛先を<b>許可ホスト一覧</b>へ追加します。
          未登録の宛先への要求は送信されません。
        </li>
        <li>
          許可後も<b>要求ごとに正確な送信内容を確認</b>してから送信されます。
          ケース名・値・ファイルパスは毎回の追加許可が必要です。
        </li>
      </ol>
      <div className="actions">
        <button className="btn primary" onClick={() => setConfirmOpen(true)}>
          外部通信の許可を確認する
        </button>
      </div>
      {confirmOpen ? (
        <div className="dialog-scrim" role="presentation">
          <div className="dialog ne-grant-dialog" role="dialog" aria-modal="true" aria-labelledby="ne-grant-title">
            <header>
              <h2 id="ne-grant-title">外部通信を許可しますか？</h2>
            </header>
            <div className="body">
              <GrantChecklist />
            </div>
            <footer>
              <button className="btn ghost" onClick={() => setConfirmOpen(false)}>
                オフラインを維持
              </button>
              <button
                className="btn primary"
                onClick={() => {
                  setGranted(true);
                  setConfirmOpen(false);
                }}
              >
                確認を必須にして許可
              </button>
            </footer>
          </div>
        </div>
      ) : null}
    </div>
  );
}

/* ---- centre: the review dialog (request-review) -------------------------------------------- */

function ReviewDialog(props: { onDecide: (decision: Decision, redactedCount: number) => void }) {
  const [redacted, setRedacted] = useState<readonly string[]>([]);
  const isRedacted = (id: string) => redacted.includes(id);
  const toggle = (id: string) =>
    setRedacted(isRedacted(id) ? redacted.filter((item) => item !== id) : [...redacted, id]);

  return (
    <div className="dialog-scrim" role="presentation">
      <div className="dialog ne-review-dialog" role="dialog" aria-modal="true" aria-labelledby="ne-review-title">
        <header>
          <h2 id="ne-review-title">外部送信の確認 — 要求 1件</h2>
          <span className="ne-host">{awaitingRow.host}</span>
        </header>
        <div className="body">
          <div className="ne-review-meta">
            <div>
              <span>要求元</span>
              <b>レポート「Run 12 強度確認」の生成コメント下書き</b>
            </div>
            <div>
              <span>目的</span>
              <b>文書検索（Web検索）</b>
            </div>
            <div>
              <span>宛先</span>
              <b className="ne-host">{awaitingRow.host}</b>
              <em>許可ホスト一覧に登録済み</em>
            </div>
            <div>
              <span>要求日時・送信サイズ</span>
              <b>{awaitingRow.at}</b>
              <em>{formatBytes(412)}（本文のみ・伏せると減ります）</em>
            </div>
          </div>

          <div className="ne-review-block" aria-label="送信内容の全文">
            <div className="ne-review-line">
              <span className="ne-line-label">検索語</span>
              <span className="ne-line-body">「SUS304 板厚3 mm 疲労限度 平均応力補正」</span>
            </div>
            {reviewItems.map((item, index) => (
              <div className="ne-review-line" key={item.id}>
                <span className="ne-line-label">
                  文脈{index + 1}・{item.kind}
                </span>
                <span className="ne-line-body">
                  {isRedacted(item.id) ? (
                    <span className="ne-redacted">〔伏せました — この項目は送信されません〕</span>
                  ) : (
                    <mark className="ne-sensitive">{item.preview}</mark>
                  )}
                </span>
                <span className="ne-line-tools">
                  <ProvenanceBadge origin={item.origin} />
                  <button
                    className="btn ghost ne-redact"
                    aria-pressed={isRedacted(item.id)}
                    onClick={() => toggle(item.id)}
                  >
                    {isRedacted(item.id) ? "戻す" : "伏せる"}
                  </button>
                </span>
              </div>
            ))}
          </div>
          <p className="ne-review-note">
            ハイライトは機密扱いの項目（ケース名・値・ファイルパス）です。「伏せる」で送信内容から
            除外できます。伏せた事実と全文はローカル監査に残ります。
          </p>

          <div className="ne-withheld">
            <b>この要求で送信しないもの</b>
            <ul>
              <li>認証情報・端末識別子</li>
              <li>選択していないケースと、その値</li>
              <li>ワークスペースのファイル本体</li>
            </ul>
          </div>
        </div>
        <footer>
          <button className="btn ghost" onClick={() => props.onDecide("refuse", redacted.length)}>
            拒否
          </button>
          <span className="ne-foot-note">拒否しても下書きは保持され、判断は監査に残ります</span>
          <button
            className="btn"
            title="このホストとこの目的の組を常に許可します。機密項目は毎回確認します。"
            onClick={() => props.onDecide("allow-always", redacted.length)}
          >
            許可（常に）
          </button>
          <button className="btn primary" onClick={() => props.onDecide("allow-once", redacted.length)}>
            許可（今回）
          </button>
        </footer>
      </div>
    </div>
  );
}

/* ---- centre: summary + audit table ---------------------------------------------------------- */

function AuditCanvas({ variant }: { variant: string }) {
  const [filter, setFilter] = useState<"all" | Outcome>("all");
  const [decision, setDecision] = useState<Decision | null>(null);
  const [redactedCount, setRedactedCount] = useState(0);

  const permission = permissionFor(variant);
  const baseline = auditRowsFor(variant);

  // The awaiting record follows the reviewer's judgement - the audit reflects what was decided.
  const rows: readonly AuditRow[] = baseline.map((row): AuditRow => {
    if (variant !== "request-review" || row.outcome !== "awaiting" || decision === null) return row;
    if (decision === "refuse") {
      return { ...row, outcome: "refused", note: "利用者が拒否・要求は送信していません" };
    }
    const label = decision === "allow-once" ? "許可（今回）" : "許可（常に）";
    return {
      ...row,
      outcome: "sent",
      note: `${label}・機密${reviewItems.length}項目中${redactedCount}項目を伏せて送信`,
    };
  });
  const visible = rows.filter((row) => filter === "all" || row.outcome === filter);
  const filterLabel = filter === "all" ? "すべて" : outcomeLabel[filter];

  const summary = [
    { key: "default", label: "既定", value: "何も送らない", note: "許可されるまで通信を試行しません" },
    {
      key: "external",
      label: "外部通信",
      value: permission.external ? "有効（要求ごとに確認）" : "無効",
      note: permission.external ? "送信前に正確な内容を表示します" : "変更は右の「許可」タブから",
    },
    {
      key: "hosts",
      label: "許可ホスト",
      value: permission.hosts.length === 0 ? "なし" : `${permission.hosts.length}件`,
      note:
        permission.hosts.length === 0
          ? "登録なし・宛先が未登録の要求は送信しません"
          : permission.hosts.join("、"),
    },
    { key: "audit", label: "監査", value: "ローカル保存", note: `記録 ${rows.length}件・書き出しは明示操作` },
  ];

  return (
    <div className="ne-canvas">
      <div className="ne-summary" role="group" aria-label="送信の既定と現在の許可状態">
        {summary.map((cell) => (
          <div className="ne-summary-cell" key={cell.key}>
            <small>{cell.label}</small>
            <b>{cell.value}</b>
            <span>{cell.note}</span>
          </div>
        ))}
      </div>

      {variant === "refused" ? (
        <div className="notice error" role="alert">
          <b>外部要求を拒否しました — 何も送信していません。</b>
          <span className="why">
            ホスト <span className="ne-host">{refusedRow.host}</span> は許可ホスト一覧に未登録です。
            拒否した要求（全文）：{refusedRow.content}。この判断は下の監査に記録済みです。
            送信するには、右の「許可」タブでこのホストを許可一覧へ追加してから要求をやり直します。
          </span>
        </div>
      ) : null}

      {variant === "request-review" && decision !== null ? (
        <div className="notice" role="status">
          {decision === "refuse" ? (
            <>
              <b>拒否を記録しました — 要求は送信していません。</b>
              <span className="why">
                要求の全文はローカル監査に残っています。生成コメントの下書きは検索なしで続行できます。
              </span>
            </>
          ) : (
            <>
              <b>{decision === "allow-once" ? "許可（今回）" : "許可（常に）"}を記録し、送信しました。</b>
              <span className="why">
                機密{reviewItems.length}項目のうち{redactedCount}項目を伏せて送信しました。
                送信した全文と判断はローカル監査に残ります。
                {decision === "allow-always"
                  ? `以後 ${awaitingRow.host} への文書検索は、機密項目の確認のみ行います。`
                  : ""}
              </span>
            </>
          )}
        </div>
      ) : null}

      <section className="ne-audit" aria-label="ローカル監査">
        <header className="ne-audit-head">
          <div>
            <span className="ne-eyebrow">ローカル監査</span>
            <h2>外部要求の記録</h2>
          </div>
          <div className="ne-audit-tools">
            <label className="ne-filter-label" htmlFor="ne-outcome-filter">
              結果で絞り込み
            </label>
            <select
              id="ne-outcome-filter"
              className="field-input"
              value={filter}
              onChange={(event) => setFilter(event.target.value as "all" | Outcome)}
            >
              <option value="all">すべて（{rows.length}件）</option>
              {(Object.keys(outcomeLabel) as Outcome[]).map((outcome) => (
                <option key={outcome} value={outcome}>
                  {outcomeLabel[outcome]}（{rows.filter((row) => row.outcome === outcome).length}件）
                </option>
              ))}
            </select>
            <button
              className="btn"
              title="監査記録をファイルとして書き出します。書き出しは端末内で完結します。"
              onClick={() =>
                submit({ operation: "system.audit", parameters: { scope: "workspace", format: "jsonl" } })
              }
            >
              監査記録を書き出し
            </button>
          </div>
        </header>
        <div className="table-scroll ne-table-scroll">
          <table className="value-table ne-table">
            <thead>
              <tr>
                <th scope="col">日時</th>
                <th scope="col">目的</th>
                <th scope="col">宛先ホスト</th>
                <th scope="col">結果</th>
                <th scope="col">送信内容（正確な内容）</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr
                  key={row.id}
                  className={
                    row.outcome === "awaiting"
                      ? "ne-row-awaiting"
                      : row.outcome === "refused"
                        ? "ne-row-refused"
                        : undefined
                  }
                >
                  <td className="ne-cell-time">{row.at}</td>
                  <td>{row.purpose}</td>
                  <td className="ne-cell-host">
                    <span className="ne-host" title={row.host}>
                      {row.host}
                    </span>
                  </td>
                  <td>
                    <span className={`ne-outcome ne-outcome-${row.outcome}`}>{outcomeLabel[row.outcome]}</span>
                  </td>
                  <td className="ne-cell-content">
                    <span className="ne-content">{row.content}</span>
                    <span className="ne-content-note">{row.note}</span>
                  </td>
                </tr>
              ))}
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={5} className="ne-empty-row">
                    該当する記録はありません — 絞り込み「{filterLabel}」に一致する要求がまだ無いためです。
                    「すべて」に戻すと {rows.length}件が表示されます。
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
        <p className="ne-audit-foot">
          端末内で完結した処理（アシスタント評価など）は外部要求ではないため、この記録には現れません。
          記録は自動では端末外へ出ません。
        </p>
      </section>

      {variant === "request-review" && decision === null ? (
        <ReviewDialog
          onDecide={(nextDecision, count) => {
            setDecision(nextDecision);
            setRedactedCount(count);
          }}
        />
      ) : null}
    </div>
  );
}

export function NetworkScreen(props: { variant: string }) {
  if (props.variant === "offline") return <OfflineState />;
  return <AuditCanvas variant={props.variant} />;
}

/* ---- rail: permissions ----------------------------------------------------------------------- */

function PermissionsRail({ variant }: { variant: string }) {
  const seed = permissionFor(variant);
  const [external, setExternal] = useState(seed.external);
  const [webSearch, setWebSearch] = useState(seed.external);
  const [commentary, setCommentary] = useState(false);
  const [hosts, setHosts] = useState<readonly string[]>(seed.hosts);
  const [draft, setDraft] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  const offline = disabledBecause("外部通信が無効です");
  const later = disabledBecause("後続リリースで提供予定です");
  const emptyDraft = disabledBecause("ホスト名が未入力です");

  return (
    <div>
      <div className="prop-section">
        <h3>ワークスペース権限</h3>
        <label className="ne-toggle">
          <span>外部通信</span>
          <input
            type="checkbox"
            checked={external}
            onChange={() => {
              if (external) {
                setExternal(false);
                setWebSearch(false);
                setConfirmOpen(false);
              } else {
                setConfirmOpen(true);
              }
            }}
          />
        </label>
        {confirmOpen && !external ? (
          <div className="ne-confirm" role="group" aria-label="外部通信の許可確認">
            <GrantChecklist />
            <div className="ne-confirm-actions">
              <button className="btn ghost" onClick={() => setConfirmOpen(false)}>
                オフラインを維持
              </button>
              <button
                className="btn primary"
                onClick={() => {
                  setExternal(true);
                  setConfirmOpen(false);
                }}
              >
                確認を必須にして許可
              </button>
            </div>
          </div>
        ) : null}
        <label className="ne-toggle">
          <span>Web検索</span>
          <input
            type="checkbox"
            checked={webSearch}
            disabled={!external}
            title={external ? undefined : offline.title}
            onChange={(event) => setWebSearch(event.target.checked)}
          />
        </label>
        <label className="ne-toggle">
          <span>生成コメント（外部モデル）</span>
          <input
            type="checkbox"
            checked={commentary && external}
            disabled={!external}
            title={external ? undefined : offline.title}
            onChange={(event) => setCommentary(event.target.checked)}
          />
        </label>
        <label className="ne-toggle">
          <span>詳細調査</span>
          <input type="checkbox" checked={false} disabled title={later.title} readOnly />
        </label>
        {!external ? (
          <p className="prop-note">外部通信が無効のため、Web検索と生成コメントは切り替えできません。</p>
        ) : null}
        <p className="prop-note">詳細調査は後続リリースで提供予定です。</p>
      </div>

      <div className="prop-section">
        <h3>許可ホスト（このワークスペース）</h3>
        {hosts.length === 0 ? (
          <p className="prop-note">登録なし。要求ごとの確認でも、宛先が未登録であれば送信しません。</p>
        ) : (
          <ul className="ne-host-list">
            {hosts.map((host) => (
              <li key={host}>
                <span className="ne-host" title={host}>
                  {host}
                </span>
                <button
                  className="btn ghost ne-revoke"
                  title={`${host} の許可を取り消します。以後この宛先への要求は送信されません。`}
                  onClick={() => setHosts(hosts.filter((item) => item !== host))}
                >
                  取り消し
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="ne-host-add">
          <input
            className="field-input"
            placeholder="例：docs.example.org"
            aria-label="追加するホスト名"
            value={draft}
            disabled={!external}
            title={external ? undefined : offline.title}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button
            className="btn"
            disabled={!external || draft.trim() === ""}
            title={!external ? offline.title : draft.trim() === "" ? emptyDraft.title : undefined}
            onClick={() => {
              setHosts([...hosts, draft.trim()]);
              setDraft("");
            }}
          >
            追加
          </button>
        </div>
        {!external ? (
          <p className="prop-note">外部通信が無効のため追加できません。上の「外部通信」を有効にしてください。</p>
        ) : null}
      </div>

      <div className="prop-section">
        <p className="prop-note">
          許可されるまで通信を試行しません。許可後も、ケース名・値・ファイルパスを含む送信は
          要求ごとに確認します。
        </p>
      </div>
    </div>
  );
}

/* ---- rail: audit ------------------------------------------------------------------------------ */

function AuditRail({ variant }: { variant: string }) {
  const rows = auditRowsFor(variant);
  const counts = countByOutcome(rows);

  return (
    <div>
      <div className="prop-section">
        <h3>通信記録</h3>
        <div className="prop-row">
          <label htmlFor="ne-audit-scope">期間</label>
          <select id="ne-audit-scope" className="field-input" defaultValue="workspace">
            <option value="workspace">このワークスペース</option>
            <option value="session">このセッション</option>
          </select>
        </div>
        <div className="prop-row">
          <label htmlFor="ne-audit-store">保存先</label>
          <input
            id="ne-audit-store"
            className="field-input"
            value="ローカルのみ"
            readOnly
            title="監査は端末内に保存されます。端末外への書き出しはありません。"
          />
        </div>
        <p className="prop-note">記録は自動では端末外へ出ません。書き出しは中央の明示操作だけです。</p>
      </div>
      <div className="prop-section">
        <h3>記録 {rows.length}件</h3>
        {rows.length === 0 ? (
          <p className="prop-note">
            外部要求はまだありません。要求が発生すると、送信の有無にかかわらず全文がここに残ります。
          </p>
        ) : (
          <ul className="ne-count-list">
            {(Object.keys(outcomeLabel) as Outcome[]).map((outcome) => (
              <li key={outcome}>
                <span>{outcomeLabel[outcome]}</span>
                <em>{counts[outcome]}件</em>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export function NetworkRail(props: { tab: string; variant: string }) {
  if (props.tab === "audit") return <AuditRail variant={props.variant} />;
  return <PermissionsRail variant={props.variant} />;
}
