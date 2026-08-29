/* Case tree (11_ui.md): the cases of the open workspace - two levels expanded by default, with the
 * incremental search and tag filter inside the section (XC-217, LIM-005). Selection here is a
 * subject change (transition class 2): every context-following area re-renders. */
import { useState } from "react";

export type CaseNode = {
  id: string;
  name: string;
  tags?: string[];
  axis?: string;
  children?: CaseNode[];
};

export function CaseTree(props: {
  cases: CaseNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const q = query.trim();

  const matches = (node: CaseNode): boolean =>
    q === "" ||
    node.name.includes(q) ||
    (node.tags ?? []).some((t) => t.includes(q)) ||
    (node.children ?? []).some(matches);

  const renderNode = (node: CaseNode, depth: number) => {
    if (!matches(node)) return null;
    return (
      <div key={node.id}>
        <button
          className="tree-row"
          style={{ ["--indent" as string]: `${depth * 14}px` }}
          aria-selected={props.selectedId === node.id}
          onClick={() => props.onSelect(node.id)}
        >
          <span className="label">{node.name}</span>
          {node.axis ? <span className="meta">{node.axis}</span> : null}
          {(node.tags ?? []).length > 0 ? <span className="meta">{(node.tags ?? []).join("・")}</span> : null}
        </button>
        {(node.children ?? []).map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div>
      <div className="side-search">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="ケースを検索"
          aria-label="ケースを検索"
        />
      </div>
      {props.cases.length === 0 ? (
        <p className="prop-note" style={{ padding: "0 10px 8px" }}>
          ケースがありません。ファイルを読み込むとここに並びます
        </p>
      ) : (
        props.cases.map((node) => renderNode(node, 0))
      )}
    </div>
  );
}
