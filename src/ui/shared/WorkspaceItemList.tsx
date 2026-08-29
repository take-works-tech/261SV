/* Workspace-item list (11_ui.md): the open-item library of one area - the saved views, graphs,
 * reports or pipelines of the workspace, searched and opened. Opening is a tool change (class 1):
 * the subject survives it. */

export type WorkspaceItem = {
  id: string;
  name: string;
  meta?: string;
};

export function WorkspaceItemList(props: {
  kindLabel: string;
  items: WorkspaceItem[];
  openId: string | null;
  onOpen: (id: string) => void;
  onCreate?: () => void;
}) {
  return (
    <div style={{ padding: 8, display: "grid", gap: 4 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <b className="type-caption" style={{ letterSpacing: "var(--tracking-wide)", color: "var(--ink-strong)" }}>
          {props.kindLabel}
        </b>
        {props.onCreate ? (
          <button className="btn ghost" style={{ marginLeft: "auto" }} onClick={props.onCreate}>
            ＋ 新規
          </button>
        ) : null}
      </div>
      {props.items.length === 0 ? (
        <p className="prop-note">まだありません。「＋ 新規」から作成します</p>
      ) : (
        props.items.map((item) => (
          <button
            key={item.id}
            className="tree-row"
            aria-selected={props.openId === item.id}
            onClick={() => props.onOpen(item.id)}
          >
            <span className="label">{item.name}</span>
            {item.meta ? <span className="meta">{item.meta}</span> : null}
          </button>
        ))
      )}
    </div>
  );
}
