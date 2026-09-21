/* The `log` area as r1 has it: one popover from the top bar with the four lists (XC-286,
 * 16_application_model §7.12, §12). With an engine every list is the engine's answer or the notices
 * this window raised; without one the design fixtures the top bar has always shown stand in, and
 * say so. What outlives the window is the diagnostic log, and the popover says whether this engine
 * writes it to a file or holds it in memory only. */
import { useEffect, useState } from "react";
import type { Results } from "../client/engine";
import { engineState, useEngine, type Notice } from "../state/engine";
import { auditLines } from "../logic/egress";
import { auditCopyRows, dismissedCount, logRows, omittedSentence, retentionSentence, visibleNotices } from "../logic/logArea";
import { CopyValues } from "./CopyValues";
import { EngineHistory } from "./EngineHistory";
import { NotificationHistory } from "./NotificationHistory";
import { ScriptView, type ScriptLine } from "./ScriptView";

export type LogTab = "notices" | "record" | "audit" | "log";

const TABS: readonly { id: LogTab; label: string }[] = [
  { id: "notices", label: "通知" },
  { id: "record", label: "操作の記録" },
  { id: "audit", label: "通信監査" },
  { id: "log", label: "診断ログ" },
];

export function LogArea(props: {
  tab: LogTab;
  onTab: (tab: LogTab) => void;
  fixtureNotices: readonly Notice[];
  fixtureRecord: readonly ScriptLine[];
}) {
  const e = useEngine();
  const live = e.reachability.kind === "reachable";
  const [showDismissed, setShowDismissed] = useState(false);
  const [audit, setAudit] = useState<Results["system.audit"] | null>(null);
  const [level, setLevel] = useState<"warning" | "info">("warning");
  const [log, setLog] = useState<Results["system.log"] | null>(null);

  // Each list is read when its tab opens: the engine holds it, bounds it, and a copy kept here
  // would be a second record to keep in step (#315).
  useEffect(() => {
    if (props.tab === "record" && live) void engineState.history();
  }, [props.tab, live]);
  useEffect(() => {
    if (props.tab === "audit" && live) void engineState.audit().then(setAudit);
  }, [props.tab, live]);
  useEffect(() => {
    if (props.tab === "log" && live) void engineState.log({ level }).then(setLog);
  }, [props.tab, live, level]);

  const notices = live ? visibleNotices(e.notices, showDismissed) : [...props.fixtureNotices];
  const dismissed = live ? dismissedCount(e.notices) : 0;
  const auditRows = audit ? auditLines(audit.entries ?? []) : null;

  return (
    <div style={{ display: "grid", gap: 8, minWidth: 0 }}>
      <div role="tablist" aria-label="記録の種類" style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {TABS.map((tab) => (
          <button key={tab.id} role="tab" aria-selected={props.tab === tab.id} className={props.tab === tab.id ? "btn" : "btn ghost"} onClick={() => props.onTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>

      {props.tab === "notices" ? (
        <div style={{ display: "grid", gap: 6 }}>
          {live ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span className="type-caption" style={{ color: "var(--ink-muted)" }}>
                この窓が出した通知。閉じても消えず、診断ログにも残ります（16_application_model §12）
              </span>
              {dismissed > 0 ? (
                <button className="btn ghost" style={{ marginLeft: "auto" }} onClick={() => setShowDismissed(!showDismissed)}>
                  {showDismissed ? "閉じたものを隠す" : `閉じたものも表示（${dismissed}）`}
                </button>
              ) : null}
            </div>
          ) : (
            <span className="type-caption" style={{ color: "var(--ink-muted)" }}>設計状態の見本です。エンジン接続時はこの窓の通知に置き換わります</span>
          )}
          <NotificationHistory notices={notices} onDismiss={live ? (id) => engineState.dismissNotice(id) : undefined} />
        </div>
      ) : null}

      {props.tab === "record" ? (
        live ? (
          <EngineHistory history={e.history} workspaceOpen={e.workspaceId !== null} onRefresh={() => void engineState.history()} />
        ) : (
          <ScriptView lines={[...props.fixtureRecord]} onCopy={(text) => void navigator.clipboard?.writeText(text)} />
        )
      ) : null}

      {props.tab === "audit" ? (
        !live ? (
          <p className="prop-note" style={{ padding: 8 }}>エンジン接続時に、外へ出た要求の記録（system.audit）をここに表示します（XC-106）</p>
        ) : auditRows === null ? (
          <p className="prop-note" style={{ padding: 8 }}>監査を読んでいます…</p>
        ) : (
          <div style={{ display: "grid", gap: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <b className="type-caption">外へ出た要求（{auditRows.length}）</b>
              <span style={{ marginLeft: "auto" }}>
                <CopyValues rows={auditCopyRows(auditRows)} label="監査を写す" title="時刻・目的・宛先・結果・内容・注記をタブ区切りで写します（監査の書き出し）" />
              </span>
            </div>
            {auditRows.length === 0 ? (
              <p className="prop-note" style={{ padding: 8 }}>外部に出た要求はありません。記録が空であることが答えで、方針の文ではありません（#317）</p>
            ) : (
              <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 4 }}>
                {auditRows.map((row) => (
                  <li key={row.id} className={row.outcome === "sent" ? "notice" : "notice warn"}>
                    <b>{row.purpose} → {row.host}：{row.outcome === "sent" ? "送信" : row.outcome === "refused" ? "拒否" : "確認待ち"}</b>
                    <span className="why">{row.at} — {row.content}{row.note ? `（${row.note}）` : ""}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )
      ) : null}

      {props.tab === "log" ? (
        !live ? (
          <p className="prop-note" style={{ padding: 8 }}>エンジン接続時に、診断ログ（system.log）をここに読み返します。ファイルに書くエンジンなら、窓を閉じたあとも読めます（XC-263）</p>
        ) : (
          <div style={{ display: "grid", gap: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <span role="radiogroup" aria-label="水準" style={{ display: "flex", gap: 2 }}>
                <button role="radio" aria-checked={level === "warning"} className={level === "warning" ? "btn" : "btn ghost"} onClick={() => setLevel("warning")} title="拒否と失敗、注意、外部要求の可否">
                  警告以上
                </button>
                <button role="radio" aria-checked={level === "info"} className={level === "info" ? "btn" : "btn ghost"} onClick={() => setLevel("info")} title="答えた命令も含めて">
                  情報以上
                </button>
              </span>
              <button className="btn ghost" style={{ marginLeft: "auto" }} onClick={() => void engineState.log({ level }).then(setLog)} title="エンジンに読み直しを頼みます">
                更新
              </button>
            </div>
            {log === null ? (
              <p className="prop-note" style={{ padding: 8 }}>ログを読んでいます…</p>
            ) : (
              <>
                <p className="type-caption" style={{ margin: 0, color: "var(--ink-muted)" }}>{retentionSentence(log)}</p>
                {omittedSentence(log) ? <p className="type-caption" style={{ margin: 0, color: "var(--state-warn)" }}>{omittedSentence(log)}</p> : null}
                {log.entries.length === 0 ? (
                  <p className="prop-note" style={{ padding: 8 }}>この水準の行はまだありません</p>
                ) : (
                  <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 4 }}>
                    {logRows(log).map((row) => (
                      <li key={row.id} className={row.level === "error" ? "notice error" : row.level === "warning" ? "notice warn" : "notice"}>
                        <b>[{row.levelLabel}] {row.event}</b>
                        <span className="why">{row.at} — {row.text}</span>
                      </li>
                    ))}
                  </ol>
                )}
              </>
            )}
          </div>
        )
      ) : null}
    </div>
  );
}
