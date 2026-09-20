/* What may leave the machine, and what did, as a person reads it (MOD-015, XC-267). The engine
 * answers both - `system.capabilities` says what may leave and whether anything can, `system.audit`
 * says what did - and these turn the answers into the lines the settings and network pages show.
 * No React and no transport: a mapping that can only be exercised by rendering is a mapping nobody
 * tests. The rule the mapping keeps is XC-106's: the exact content, never a summary of it. */
import type { Results } from "../client/engine";
import { describeRecorded } from "./time";

export type Egress = NonNullable<Results["system.capabilities"]["egress"]>;
export type AuditEntry = Results["system.audit"]["entries"][number];

/** One line of the network page's table: what the audit holds, in the page's own columns. */
export interface AuditLine {
  id: string;
  at: string;
  purpose: string;
  host: string;
  outcome: "sent" | "refused" | "awaiting";
  /** The exact content that went or would have gone (XC-106) - or, where the gate refused before a
   *  request was even composed, a sentence saying so rather than an empty cell. */
  content: string;
  note: string;
}

const PURPOSE_LABEL: Record<string, string> = {
  languageModel: "言語モデル",
  webSearch: "Web検索",
  updateCheck: "更新確認",
  supportBundle: "サポートバンドル",
};

/** The audit as table lines, newest first: the question a person opens the page with is "what just
 *  happened", and an empty list stays an empty list - the page says what that means. */
export function auditLines(entries: readonly AuditEntry[], readerOffsetMinutes?: number): AuditLine[] {
  return entries
    .map((entry, index): AuditLine => {
      const withheld = entry.withheld && entry.withheld.length > 0 ? `伏せた語 ${entry.withheld.length} 件：${entry.withheld.join("、")}` : null;
      const note = [entry.reason ?? null, withheld].filter((one): one is string => one !== null).join("・");
      return {
        id: `${entry.at.utc}:${index}`,
        at: describeRecorded(entry.at, readerOffsetMinutes),
        purpose: PURPOSE_LABEL[entry.purpose] ?? entry.purpose,
        host: entry.host,
        outcome: entry.outcome === "awaitingConfirmation" ? "awaiting" : entry.outcome,
        content: entry.sent ?? "（送信内容なし：要求が組み立てられる前に拒まれました）",
        note: note || (entry.outcome === "sent" ? "送信済み・全文は左のとおり" : ""),
      };
    })
    .reverse();
}

/** One fact of the sending policy, as the settings page lists them. */
export interface EgressFact {
  key: string;
  label: string;
  value: string;
  note: string;
}

const on = (flag: boolean): string => (flag ? "有効" : "無効");

/** What the engine says may leave, as facts a person can check against - not the policy's sentence
 *  (XC-267). The first fact is the one that settles the rest in a build with no way out. */
export function egressFacts(egress: Egress): EgressFact[] {
  return [
    {
      key: "transport",
      label: "送信経路",
      value: egress.transportConfigured ? "あり" : "なし",
      note: egress.transportConfigured
        ? "外へ出る手段があります。出るかどうかは下の許可が決めます"
        : "この版は外部に送る手段を持ちません。何も出られず、試みは拒否として監査に残ります",
    },
    {
      key: "offline",
      label: "オフライン",
      value: egress.offline ? "有効：何も試みません" : "未設定：許可の有無が決めます",
      note: "既定は何も許可しません（INV-007、XC-106）",
    },
    {
      key: "scope",
      label: "対象",
      value: egress.workspaceId ?? "既定",
      note: egress.workspaceId ? "このワークスペースの許可" : "ワークスペースが開いていないので既定：何も許可しません",
    },
    {
      key: "search",
      label: "Web検索",
      value: on(egress.search),
      note: egress.search
        ? egress.withoutAsking
          ? "毎回の確認なしで送ります"
          : "送る前に毎回、送る全文を確認します"
        : "要求は送られず、答えられなかった問いとして残ります",
    },
    {
      key: "languageModel",
      label: "言語モデル",
      value: on(egress.languageModel),
      note: "許可の有無にかかわらず、データセットの値は届きません（XC-229）",
    },
    {
      key: "updateCheck",
      label: "更新確認",
      value: on(egress.updateCheck),
      note: "照会するのは製品の版だけです",
    },
    {
      key: "hosts",
      label: "許可ホスト",
      value: egress.hosts.length === 0 ? "なし" : `${egress.hosts.length}件`,
      note: egress.hosts.length === 0 ? "空は「どこにも」であり「どこでも」ではありません" : egress.hosts.join("、"),
    },
    {
      key: "workspaceContent",
      label: "ワークスペースの内容",
      value: on(egress.workspaceContent),
      note: "値・ケース名・ファイルパスが検索語に入ってよいか。検索ごとに上書きできます",
    },
    {
      key: "audit",
      label: "監査",
      value: `${egress.auditEntries}件（うち送信 ${egress.sentEntries}件）`,
      note: egress.auditEntries === 0 ? "外部要求はまだ一件も記録されていません" : "全文はネットワーク画面で読めます",
    },
  ];
}
