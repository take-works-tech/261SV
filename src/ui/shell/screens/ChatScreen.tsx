/* Chat (mockup 2): the one conversation, full width of the centre column.
 *
 * Design decisions this file holds:
 * - One thread at reading width, vertical - never left-right bubbles (catalogue chat.default).
 * - A turn shows the instruction, then the command names it was mapped to (the names come from the
 *   operation contract, client/operations - a typo there is a type error here), then results as
 *   values with unit, provenance and honest digits (XC-003, INV-013, INV-014).
 * - The shell's instruction bar is absent in chat: the composer at the bottom of this screen is the
 *   same conversation in its full form - moved, not forked (XC-150). The draft is lifted so the
 *   empty state's example questions fill it without sending anything.
 * - Nothing pretends work was done: the empty state runs no commands, the error state names what
 *   did NOT run, and the outbound review shows the exact query BEFORE anything leaves (XC-106).
 */
import { useState, type ReactNode } from "react";
import { NumberCell } from "../../shared/NumberCell";
import { OutboundRequestNotice, type OutboundDecision as NoticeDecision } from "../../shared/OutboundRequestNotice";
import { ProbeReadout } from "../../shared/ProbeReadout";
import { ProgressAndCancel } from "../../shared/ProgressAndCancel";
import { ProvenanceBadge } from "../../shared/ProvenanceBadge";
import { QuantityChip } from "../../shared/QuantityChip";
import { UnitLabel } from "../../shared/UnitLabel";
import type { Provenance } from "../../shared/primitives";
import { submit, type Operation } from "../../client/operations";
import { session } from "../../state/session";
import { disabledBecause, formatValue } from "../../logic/format";
import "./ChatScreen.css";

const FIRST_QUESTION = "ケース case-012 の最大ミーゼス応力を教えて。単位は宣言済みの MPa で。";

const SUGGESTIONS = [
  "このワークスペースで利用可能な物理量を一覧にして",
  "case-012 の最大ミーゼス応力を、平均化と非平均化の両方で教えて",
  "単位が未宣言のフィールドを探して",
] as const;

export function ChatScreen(props: { variant: string }) {
  const [draft, setDraft] = useState("");
  return (
    <div className="ch-canvas">
      <div className="ch-scroll">
        {props.variant === "empty" ? (
          <EmptyConversation onPick={setDraft} />
        ) : (
          <Thread variant={props.variant} />
        )}
      </div>
      <Composer draft={draft} onDraft={setDraft} />
    </div>
  );
}

/* ---- the thread ----------------------------------------------------------------------------- */

function Thread(props: { variant: string }) {
  if (props.variant === "assistant-error") return <ErrorThread />;
  if (props.variant === "outbound-request") return <OutboundThread />;
  return <DefaultThread />;
}

function DefaultThread() {
  return (
    <div className="ch-thread">
      <span className="ch-thread-note">今日 — この会話は端末内に保存されています。外部送信はありません。</span>

      <Turn role="user" meta="14:02">
        <p>{FIRST_QUESTION}</p>
      </Turn>

      <Turn role="assistant" meta="ローカルモデル・推論 標準・14:02">
        <MappedCommands
          label="対応付けたコマンド"
          commands={[
            { name: "field.statistics", note: "case-012 の完全データで統計を計算（表示形状からは測りません — INV-001）", ran: true },
            { name: "dataset.probe", note: "最大値の位置を元データの識別子で取得（INV-023）", ran: true },
          ]}
        />
        <p>
          case-012 のミーゼス応力の最大値です。報告値は表示用に間引いた形状ではなく、完全データを
          正準フレームで集計しています。
        </p>
        <div className="ch-results">
          <ProbeReadout
            field="ミーゼス応力・最大（非平均化）"
            value={formatValue(241.68, 4)}
            unit="MPa"
            origin="computed"
            location="節点 48211（部品「リブ下面」・元ファイルの節点番号）"
            onHold={() =>
              submit({
                operation: "variable.declare",
                parameters: { name: "σmax_case012", value: 241.7, unit: "MPa", origin: "computed" },
              })
            }
          />
          <ResultLine
            label="節点平均のピーク"
            value={formatValue(218.42, 4)}
            unit="MPa"
            origin="computed"
            title="共有節点への平均は滑らかな等高線を作りますが、数値を変えます（INV-032）"
            note={`平均に入る前の値域 ${formatValue(196.2, 4)}〜${formatValue(241.7, 4)} MPa。この幅は1回の解析から計算できる唯一の離散化指標なので、平均化ピークには常に併記します。`}
          />
          <span className="ch-result-note">読み取りのみを実行しました。ワークスペースは変更されていません。</span>
        </div>
        <div className="ch-actions">
          <button
            type="button"
            className="btn ghost"
            title="値・単位・来歴・位置をテキストとしてコピーします"
            onClick={() => {
              try {
                void navigator.clipboard
                  .writeText("ミーゼス応力 最大（非平均化） 241.7 MPa（計算・case-012・節点 48211）")
                  .catch(() => undefined);
              } catch {
                /* clipboard unavailable - the button did nothing, and nothing claimed otherwise */
              }
            }}
          >
            コピー
          </button>
        </div>
      </Turn>

      <Turn role="user" meta="14:04">
        <LongInstruction />
      </Turn>

      <Turn role="assistant" meta="ローカルモデル・推論 標準・14:04">
        <MappedCommands
          label="対応付けたコマンド"
          commands={[{ name: "dataset.describe", note: "読み込んだデータセットの実際の内容を列挙（推測なし）", ran: true }]}
        />
        <p>case-012 の主要フィールドです。単位はファイルから推測しません — 未宣言はそのまま示します。</p>
        <div className="table-scroll ch-table">
          <table className="value-table">
            <thead>
              <tr>
                <th>フィールド</th>
                <th>最大値</th>
                <th>単位</th>
                <th>来歴</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>ミーゼス応力</td>
                <NumberCell value={formatValue(241.68, 4)} />
                <td><UnitLabel unit="MPa" /></td>
                <td><ProvenanceBadge origin="computed" /></td>
              </tr>
              <tr>
                <td>変位（合成）</td>
                <NumberCell value={formatValue(0.8421, 3)} />
                <td><UnitLabel unit={null} /></td>
                <td><ProvenanceBadge origin="dataset" /></td>
              </tr>
              <tr>
                <td>塑性ひずみ</td>
                <NumberCell value={null} missingBecause="このケースには未収録" />
                <td><span className="ch-dim">収録なし</span></td>
                <td><span className="ch-dim" title="値が無いため来歴もありません">—</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <span className="ch-result-note">
          「単位未宣言」は宣言待ちの状態です。設定画面の「宣言単位」で宣言できます（XC-003）。欠けている値は欠けたまま示します（XC-001）。
        </span>
      </Turn>

      <Turn role="user" meta="14:07">
        <p>この確認をパイプラインにして、全ケースでドライランして。</p>
      </Turn>

      <Turn role="assistant" meta="ローカルモデル・推論 標準・14:07">
        <MappedCommands
          label="対応付けたコマンド"
          commands={[
            { name: "pipeline.create", note: "統計ユニット1件のパイプラインを作成（実行済み）", ran: true },
            { name: "pipeline.dryRun", note: "書き込みなしの事前確認 — 成果物は作られません", ran: true },
          ]}
        />
        <p>ドライランは何も書き込みません。対象 6 ケースをユニット境界で確認しています。</p>
        <ProgressAndCancel
          label="pipeline.dryRun を実行中"
          detail="ユニット 2／4・ケース 3／6"
          fraction={0.42}
          onCancel={() => submit({ operation: "pipeline.cancel", parameters: { at: "unit-boundary" } })}
          cancelNote="中断はユニット境界で有効になります。途中の成果物は作られません"
        />
      </Turn>
    </div>
  );
}

/* chat.assistant-error: what did NOT run, named - and the workspace untouched. */
function ErrorThread() {
  return (
    <div className="ch-thread">
      <span className="ch-thread-note">今日 — この会話は端末内に保存されています。外部送信はありません。</span>

      <Turn role="user" meta="14:02">
        <p>{FIRST_QUESTION}</p>
      </Turn>

      <Turn role="assistant" meta="ローカルモデル・14:02">
        <div className="notice error" role="alert">
          <b>アシスタントが失敗しました</b>
          <span className="why">
            ローカルモデルへの接続がタイムアウトしました（30 秒）。コマンドは 1 件も発行されていません。
          </span>
        </div>
        <MappedCommands
          label="実行されなかったコマンド"
          commands={[
            { name: "field.statistics", note: "対応付けは完了していましたが、送信前に失敗しました", ran: false },
            { name: "dataset.probe", note: "対応付けは完了していましたが、送信前に失敗しました", ran: false },
          ]}
        />
        <p>ワークスペースは変更されていません。ジャーナルにも新しい項目はありません。</p>
        <div className="ch-actions">
          <button
            type="button"
            className="btn"
            title="同じ指示をもう一度対応付けから実行します"
            onClick={() => submit({ operation: "script.run", parameters: { instruction: FIRST_QUESTION, retry: true } })}
          >
            再試行
          </button>
          <button
            type="button"
            className="btn ghost"
            title="設定のアシスタント欄でモデルの状態を確認します"
            onClick={() => session.navigate("settings")}
          >
            設定でモデルを確認
          </button>
        </div>
      </Turn>
    </div>
  );
}

/* chat.outbound-request: the exact terms and the exclusions, before anything leaves (XC-106). */
function OutboundThread() {
  return (
    <div className="ch-thread">
      <span className="ch-thread-note">今日 — この会話は端末内に保存されています。外部送信はありません。</span>

      <Turn role="user" meta="15:11">
        <p>REC-4021 形式の公式仕様書を探して。</p>
      </Turn>

      <Turn role="assistant" meta="ローカルモデル・15:11">
        <MappedCommands
          label="対応付けたコマンド"
          commands={[{ name: "system.protocols", note: "ローカルの形式対応表を確認 — 送信なし", ran: true }]}
        />
        <p>
          ローカルの対応表では REC-4021 の対応レベルは offered です。公式仕様書は端末内にありません。
          取得には外部検索が必要なため、送信前に内容の確認を求めます。
        </p>
        <OutboundRequestCard />
      </Turn>
    </div>
  );
}

type OutboundDecision = "pending" | "refused" | "once" | "workspace";

function OutboundRequestCard() {
  const [decision, setDecision] = useState<OutboundDecision>("pending");
  const host = "docs.solverformats.example";
  const query = "REC-4021 result file format official specification";
  const decide = (next: Exclude<OutboundDecision, "pending">) => {
    setDecision(next);
    // The decision itself is a workspace event: host, time and verdict go to the local audit.
    submit({ operation: "system.audit", parameters: { event: "outbound-decision", host, decision: next } });
  };

  if (decision !== "pending") {
    return (
      <div className={decision === "refused" ? "notice good" : "notice"} role="status">
        <b>
          {decision === "refused" && "送信していません。"}
          {decision === "once" && "今回だけ許可しました。"}
          {decision === "workspace" && "このホストを継続許可しました。"}
        </b>
        <span className="why">
          {decision === "refused"
            ? "検索語は端末を出ていません。判断はローカル監査に記録されました。"
            : decision === "once"
              ? `表示した検索語のみを ${host} へ 1 回送信します。ホスト・日時・判断はローカル監査に記録されます。`
              : `対象は ${host} のみです。以後の要求も 1 件ずつ記録され、取り消しはネットワーク画面から行えます。`}
        </span>
        <div className="ch-actions" style={{ marginTop: 6 }}>
          <button type="button" className="btn ghost" onClick={() => setDecision("pending")}>
            要求内容を再表示
          </button>
          {decision !== "refused" ? (
            <button type="button" className="btn ghost" onClick={() => session.navigate("network")}>
              監査を開く
            </button>
          ) : null}
        </div>
      </div>
    );
  }

  /* The shared notice (MOD-010): the verbatim request, the withheld terms, and the three
     decisions. One implementation, because the network screen shows the same thing and two
     wordings of "what leaves this machine" is one wording too many (XC-106). */
  return (
    <OutboundRequestNotice
      purpose="形式仕様書の検索"
      host={host}
      content={`GET https://${host}/search?q=${encodeURIComponent(query)}`}
      withheld={[
        "ケース名",
        "ファイルパス",
        "形状",
        "節点値・要素値",
        "ワークスペース名",
        "この会話の本文",
      ]}
      outcome="awaiting"
      onDecide={(next: NoticeDecision) =>
        decide(next === "refuse" ? "refused" : next === "always" ? "workspace" : "once")
      }
    />
  );
}

/* chat.empty: example questions fill the composer - nothing runs until the person sends. */
function EmptyConversation(props: { onPick: (text: string) => void }) {
  return (
    <div className="empty-state">
      <h2>新しい会話</h2>
      <p>
        質問と操作は、この 1 つの会話で続けられます。まだコマンドは実行されておらず、ワークスペースはそのままです。
      </p>
      <div className="ch-suggestions">
        {SUGGESTIONS.map((text) => (
          <button key={text} type="button" className="ch-suggestion" onClick={() => props.onPick(text)}>
            {text}
          </button>
        ))}
      </div>
      <p className="ch-result-note">例を選ぶと入力欄に入ります。送信するまで何も実行されません。</p>
    </div>
  );
}

/* ---- turn scaffolding ------------------------------------------------------------------------ */

function Turn(props: { role: "user" | "assistant"; meta?: string; children: ReactNode }) {
  return (
    <article className={props.role === "user" ? "ch-turn ch-turn-user" : "ch-turn ch-turn-assistant"}>
      <header className="ch-turn-head">
        <span className="ch-role-mark" aria-hidden>
          {props.role === "user" ? "あ" : "S"}
        </span>
        <b>{props.role === "user" ? "あなた" : "SOLVIA"}</b>
        {props.meta ? <small>{props.meta}</small> : null}
      </header>
      <div className="ch-turn-body">{props.children}</div>
    </article>
  );
}

type MappedCommand = { name: Operation; note: string; ran: boolean };

function MappedCommands(props: { label: string; commands: MappedCommand[] }) {
  return (
    <div className="ch-cmds" role="group" aria-label={props.label}>
      <small>{props.label}</small>
      {props.commands.map((command, index) => (
        <code
          key={`${command.name}:${index}`}
          className={command.ran ? "ch-cmd" : "ch-cmd ch-cmd-notrun"}
          title={command.note}
        >
          {command.name}
          {!command.ran ? <span className="ch-cmd-state">未実行</span> : null}
        </code>
      ))}
    </div>
  );
}

function ResultLine(props: {
  label: string;
  value: string;
  unit: string | null;
  origin: Provenance;
  title?: string;
  note?: string;
}) {
  return (
    <div style={{ display: "grid", gap: 4, minWidth: 0 }}>
      <div className="ch-result-line" title={props.title}>
        <span className="ch-result-label">{props.label}</span>
        <QuantityChip value={props.value} unit={props.unit} />
        <ProvenanceBadge origin={props.origin} />
      </div>
      {props.note ? <p className="ch-result-note">{props.note}</p> : null}
    </div>
  );
}

/* The second user instruction is long on purpose: the truncated state clamps it to two lines and
 * keeps a way to read the full text. */
function LongInstruction() {
  const [expanded, setExpanded] = useState(false);
  return (
    <>
      <p className={expanded ? undefined : "ch-clamp"}>
        主要フィールドの一覧も出して。単位が未宣言のものは未宣言と明示して、欠けているフィールドは欠けている理由ごと見せて。
        あとで報告書に貼るから、来歴の列も必ず付けて。表示用に丸めた形状から測った値は一つも混ぜないで、
        すべて完全データ側の集計だけにして。
      </p>
      <button type="button" className="ch-inline-btn" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>
        {expanded ? "折りたたむ" : "全文を表示"}
      </button>
    </>
  );
}

/* ---- the composer: the same conversation, moved here (XC-150) -------------------------------- */

function Composer(props: { draft: string; onDraft: (draft: string) => void }) {
  const canSend = props.draft.trim() !== "";
  return (
    <form
      className="ch-composer"
      onSubmit={(event) => {
        event.preventDefault();
        if (!canSend) return;
        submit({ operation: "script.run", parameters: { instruction: props.draft.trim() } });
        props.onDraft("");
      }}
    >
      <div className="ch-composer-inner">
        <span className="ch-seam-note">
          各画面下の指示バーと同じ 1 つの会話です — 入力欄がここへ移っただけで、会話は分岐しません（XC-150）。
        </span>
        <textarea
          rows={2}
          value={props.draft}
          onChange={(event) => props.onDraft(event.target.value)}
          placeholder="ワークスペースへの質問または操作（例：case-012 の最大応力を教えて）"
          aria-label="アシスタントへの指示"
        />
        <div className="ch-composer-row">
          <label>
            <span className="ch-dim" style={{ marginRight: 4 }}>モデル</span>
            <select className="field-input" defaultValue="local" aria-label="モデル">
              <option value="local">ローカルモデル</option>
              <option value="remote" disabled title="無効：外部モデルは未構成です">
                外部モデル（未構成）
              </option>
            </select>
          </label>
          <label>
            <span className="ch-dim" style={{ marginRight: 4 }}>推論</span>
            <select className="field-input" defaultValue="standard" aria-label="推論の深さ">
              <option value="brief">簡潔</option>
              <option value="standard">標準</option>
              <option value="deep">詳細</option>
            </select>
          </label>
          <button
            type="button"
            className="btn ghost"
            aria-pressed={false}
            title="検索は要求ごとに、送信内容を表示してから確認します。許可と監査はネットワーク画面（XC-106）"
            onClick={() => session.navigate("network", "request-review")}
          >
            検索：オフ（要求ごとに確認）
          </button>
          <button type="button" className="btn ghost" {...disabledBecause("要求数と費用見積を取得できるまで詳細調査は送信しません")}>
            詳細調査
          </button>
          <span className="ch-spacer" />
          <button
            type="submit"
            className="btn primary"
            {...(canSend ? {} : disabledBecause("送信する内容がありません。質問または操作を入力してください"))}
          >
            送る
          </button>
        </div>
        <span className="ch-fineprint">回答は誤る可能性があります。値・単位・来歴は元データで確認してください。</span>
      </div>
    </form>
  );
}
