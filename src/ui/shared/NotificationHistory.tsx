/* Notification history (11_ui.md): notifications kept after dismissal. A failure appears where it
 * happened AND here; dismissal hides, it never deletes - a dismissed refusal is still the answer to
 * "why did nothing happen" (16_application_model §12). */

export type Notice = {
  id: string;
  at: string;
  severity: "info" | "warning" | "error" | "refusal";
  title: string;
  detail: string;
};

const SEVERITY_LABEL = { info: "情報", warning: "警告", error: "エラー", refusal: "拒否" } as const;

export function NotificationHistory(props: { notices: Notice[] }) {
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
            {notice.at} — {notice.detail}
          </span>
        </div>
      ))}
    </div>
  );
}
