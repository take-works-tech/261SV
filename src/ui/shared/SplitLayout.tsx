/* Split layout (11_ui.md): one to four panes of the same area kind. Pane count and camera sync are
 * session state on the work-area bar, never part of a definition (XC-204); each pane keeps its own
 * case identity on its badge (XC-202). */
import type { ReactNode } from "react";

export function SplitLayout(props: { panes: ReactNode[] }) {
  const count = Math.min(Math.max(props.panes.length, 1), 4);
  const columns = count === 1 ? "1fr" : count === 2 ? "1fr 1fr" : "1fr 1fr";
  const rows = count <= 2 ? "1fr" : "1fr 1fr";
  return (
    <div className="viewport-grid" style={{ gridTemplateColumns: columns, gridTemplateRows: rows }}>
      {props.panes.slice(0, count)}
    </div>
  );
}
