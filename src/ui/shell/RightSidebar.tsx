/* The right sidebar (MOD-009): an icon rail and one property section for the current item or
 * selection - the rail's tab set belongs to the screen, and a selection-scoped tab appears below a
 * divider (11_ui.md). The section content is each screen's own; the shell provides the frame. */
import { useCallback, useState, type ReactNode } from "react";
import { session, useSession, type ScreenId } from "../state/session";

export type RailTab = { id: string; label: string; glyph: string; scope?: "selection" };

const TABS: Partial<Record<ScreenId, RailTab[]>> = {
  view: [
    { id: "overall", label: "ビュー", glyph: "◻" },
    { id: "camera", label: "カメラ", glyph: "◉" },
    { id: "rendering", label: "描画", glyph: "▦" },
    { id: "background", label: "背景", glyph: "▤" },
    { id: "output", label: "出力", glyph: "⇥" },
    { id: "objects", label: "オブジェクト", glyph: "◆", scope: "selection" },
    { id: "text", label: "テキスト", glyph: "T", scope: "selection" },
    { id: "materials", label: "マテリアル", glyph: "●", scope: "selection" },
  ],
  graph: [
    { id: "overall", label: "グラフ", glyph: "◻" },
    { id: "series", label: "系列", glyph: "≡" },
    { id: "axes", label: "軸", glyph: "⊥" },
    { id: "style", label: "スタイル", glyph: "▤" },
    { id: "output", label: "出力", glyph: "⇥" },
  ],
  report: [
    { id: "overall", label: "レポート", glyph: "◻" },
    { id: "contents", label: "内容", glyph: "≡" },
    { id: "drafting", label: "執筆", glyph: "✎" },
    { id: "style", label: "スタイル", glyph: "▤" },
    { id: "output", label: "出力", glyph: "⇥" },
  ],
  pipeline: [
    { id: "unit", label: "ユニット", glyph: "◻" },
    { id: "settings", label: "設定", glyph: "⚙" },
    { id: "history", label: "履歴", glyph: "◷" },
  ],
  simulation: [{ id: "solver", label: "ソルバ", glyph: "◻" }],
  network: [
    { id: "permissions", label: "許可", glyph: "◻" },
    { id: "audit", label: "監査", glyph: "◷" },
  ],
  information: [{ id: "file", label: "ファイル", glyph: "◻" }],
  find: [{ id: "condition", label: "条件", glyph: "◻" }],
  diff: [
    { id: "target", label: "対象", glyph: "◻" },
    { id: "method", label: "方法", glyph: "⚙" },
    { id: "disclosure", label: "開示", glyph: "≡" },
  ],
};

/* Variants whose design state lives in the rail rather than the canvas. Deep-linking one of them
 * has to land on its tab: a catalogue whose state is real and unreachable is a catalogue that
 * cannot be reviewed, and eight states failed exactly that way before this map existed. A variant
 * whose name IS a tab id needs no entry - that case is handled by the name match below. */
const VARIANT_TAB: Record<string, string> = {
  "object-analysis-mesh": "objects",
  "object-reference-mesh": "objects",
  "object-point-cloud": "objects",
  "object-scalar-field": "objects",
  "object-vector-field": "objects",
  "object-trajectory": "objects",
  "object-annotation": "objects",
  "object-effect": "objects",
  "material-composition": "materials",
  "develop-grade": "rendering",
  cameras: "camera",
  "camera-unresolved": "camera",
  theme: "style",
};

export function RightSidebar(props: { render: (tab: string) => ReactNode }) {
  const s = useSession();
  const tabs = TABS[s.screen] ?? [];
  const wanted = tabs.some((tab) => tab.id === s.variant)
    ? s.variant
    : (VARIANT_TAB[s.variant] ?? null);
  const [active, setActive] = useState<string | null>(null);
  // The variant chooses the tab until a person does; after that the person's choice holds, because
  // a rail that jumped back on every re-render would be a rail nobody could use.
  const chosen = active ?? wanted ?? tabs[0]?.id ?? "overall";
  const current = tabs.some((tab) => tab.id === chosen) ? chosen : (tabs[0]?.id ?? "overall");

  const onSplitterKey = useCallback((event: React.KeyboardEvent) => {
    if (event.key === "ArrowLeft") session.setRightWidth(s.rightWidth + 12);
    if (event.key === "ArrowRight") session.setRightWidth(s.rightWidth - 12);
  }, [s.rightWidth]);

  const onSplitterPointer = useCallback((event: React.PointerEvent) => {
    const startX = event.clientX;
    const startWidth = s.rightWidth;
    const onMove = (move: PointerEvent) => session.setRightWidth(startWidth - (move.clientX - startX));
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }, [s.rightWidth]);

  const viewScoped = tabs.filter((tab) => tab.scope !== "selection");
  const selectionScoped = tabs.filter((tab) => tab.scope === "selection");

  return (
    <aside className="right-sidebar" aria-label="プロパティ">
      <button
        className="dock-splitter splitter-right"
        role="separator"
        aria-orientation="vertical"
        aria-label="右パネルの幅"
        onKeyDown={onSplitterKey}
        onPointerDown={onSplitterPointer}
      />
      <div className="right-body">
        <nav className="rail-tabs" role="tablist" aria-label="プロパティのタブ">
          {viewScoped.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={current === tab.id}
              title={tab.label}
              onClick={() => setActive(tab.id)}
            >
              <span aria-hidden>{tab.glyph}</span>
            </button>
          ))}
          {selectionScoped.length > 0 ? <div className="rail-split" role="presentation" /> : null}
          {selectionScoped.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={current === tab.id}
              title={`${tab.label}（選択中の項目）`}
              onClick={() => setActive(tab.id)}
            >
              <span aria-hidden>{tab.glyph}</span>
            </button>
          ))}
        </nav>
        <div className="rail-content">{props.render(current)}</div>
      </div>
    </aside>
  );
}
