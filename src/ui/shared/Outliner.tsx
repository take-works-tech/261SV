/* Outliner (11_ui.md): the dataset structure and the view object list, with visibility and
 * selection. It shows what the file holds and never invents hierarchy where the file has none -
 * a flat file reads flat (mockup 1's outliner-flat state is the rule, not an edge case). */
import { useState } from "react";
import type { OutlinerNode, ToggleModifiers } from "../logic/parts";

export type { OutlinerNode } from "../logic/parts";

export function Outliner(props: {
  roots: OutlinerNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** The row's visibility control, with the keys held: Ctrl isolates the branch (view/AC-055). */
  onToggleVisible?: (id: string, modifiers: ToggleModifiers) => void;
  emptyText?: string;
}) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  if (props.roots.length === 0) {
    return (
      <p className="prop-note" style={{ padding: "8px 10px" }}>
        {props.emptyText ?? "まだ何も読み込まれていません。構造はファイルを読むと現れます"}
      </p>
    );
  }

  const renderNode = (node: OutlinerNode, depth: number) => (
    <div key={node.id}>
      <div style={{ display: "flex", alignItems: "center" }}>
        {node.children && node.children.length > 0 ? (
          <button
            className="icon-button"
            style={{ width: 18, height: 18, marginLeft: depth * 12 }}
            aria-label={collapsed[node.id] ? "展開" : "折りたたみ"}
            onClick={() => setCollapsed((prev) => ({ ...prev, [node.id]: !prev[node.id] }))}
          >
            {collapsed[node.id] ? "▸" : "▾"}
          </button>
        ) : (
          <span style={{ width: 18, marginLeft: depth * 12 }} />
        )}
        <button
          className="tree-row"
          style={{ flex: 1, minWidth: 0 }}
          aria-selected={props.selectedId === node.id}
          onClick={() => props.onSelect(node.id)}
        >
          <span className="label">{node.name}</span>
          <span className="meta">{node.kind}</span>
        </button>
        {props.onToggleVisible && node.toggle !== "none" ? (
          <button
            className="icon-button"
            style={{ width: 22, height: 22 }}
            aria-pressed={node.visible !== false}
            aria-label={node.visible !== false ? "表示中" : "非表示"}
            title={node.toggle === "branch" ? "この枝の部品を表示 / 非表示（Ctrl でこの枝だけを表示）" : "表示 / 非表示（Ctrl でこの部品だけを表示）"}
            onClick={(event) =>
              props.onToggleVisible?.(node.id, { shift: event.shiftKey, ctrl: event.ctrlKey || event.metaKey })
            }
          >
            {node.visible !== false ? "●" : "○"}
          </button>
        ) : node.toggle === "none" && props.onToggleVisible ? (
          <span style={{ width: 22 }} aria-hidden title="読めなかったパートに表示の切替はありません" />
        ) : null}
      </div>
      {!collapsed[node.id] ? (node.children ?? []).map((child) => renderNode(child, depth + 1)) : null}
    </div>
  );

  return <div>{props.roots.map((node) => renderNode(node, 0))}</div>;
}
