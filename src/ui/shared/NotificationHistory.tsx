/* Notification history (11_ui.md): notifications kept after dismissal. A failure appears where it
 * happened AND here; dismissal hides, it never deletes - a dismissed refusal is still the answer to
 * "why did nothing happen" (16_application_model §12). */

import type { Notice } from "../state/engine";
import { describeRecorded } from "../logic/time";

export type { Notice };

const SEVERITY_LABEL = { info: "情報", warning: "警告", error: "エラー", refusal: "拒否" } as const;

export function NotificationHistory(props: { notices: readonly Notice[]; onDismiss?: (id: string) => void }) {
  if (props.notices.length === 0) {
    return <p className="prop-note" style={{ padding: 8 }}>通知はまだありません</p>;
  }
  return (
    <div style={{ display: "grid", gap: 6 }}>
      {props.notices.map((notice) => (
        <div
          key={notice.id}
          className={
            notice.severity === "error" || notice.severity === "refusal"
              ? "notice error"
              : notice.severity === "warning"
                ? "notice warn"
                : "notice"
          }
        >
          <b>
            [{SEVERITY_LABEL[notice.severity]}] {notice.title}
          </b>
          <span className="why">
            {describeRecorded(notice.at)} — {notice.detail}
            {notice.dismissedAt ? `（${describeRecorded(notice.dismissedAt)} に閉じた）` : ""}
          </span>
          {props.onDismiss && !notice.dismissedAt ? (
            <button className="btn ghost" style={{ justifySelf: "start" }} onClick={() => props.onDismiss?.(notice.id)} title="隠します。記録には残ります（16_application_model §12）">
              閉じる
            </button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
