/* The left sidebar (MOD-009): case tree, variables and reference material in the work areas; the
 * conversation list in chat (XC-150). Case search sits inside the case section, above its tag
 * filter (XC-217). Resizable by pointer and keyboard alike. */
import { useCallback } from "react";
import { session, useSession } from "../state/session";
import { CaseTree, type CaseNode } from "../shared/CaseTree";
import { VariableRow } from "../shared/VariableRow";

const CASES: CaseNode[] = [
  {
    id: "study-a", name: "ブラケット改訂C", tags: ["構造"],
    children: [
      { id: "case-011", name: "Run 11（基準）", axis: "時間 21", tags: ["基準"] },
      { id: "case-012", name: "Run 12", axis: "時間 21" },
      { id: "case-013", name: "Run 13（荷重1.5倍）", axis: "時間 21" },
    ],
  },
  {
    id: "study-b", name: "熱連成", tags: ["熱"],
    children: [
      { id: "case-021", name: "Run 21", axis: "定常" },
      { id: "case-022", name: "Run 22", axis: "定常" },
    ],
  },
];

const CONVERSATIONS = [
  { id: "c1", name: "最大応力のビューを作る", meta: "10:21" },
  { id: "c2", name: "五ケースの比較グラフ", meta: "昨日" },
];

export function LeftSidebar() {
  const s = useSession();

  const onSplitterKey = useCallback((event: React.KeyboardEvent) => {
    if (event.key === "ArrowLeft") session.setLeftWidth(s.leftWidth - 12);
    if (event.key === "ArrowRight") session.setLeftWidth(s.leftWidth + 12);
  }, [s.leftWidth]);

  const onSplitterPointer = useCallback((event: React.PointerEvent) => {
    const startX = event.clientX;
    const startWidth = s.leftWidth;
    const onMove = (move: PointerEvent) => session.setLeftWidth(startWidth + (move.clientX - startX));
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }, [s.leftWidth]);

  return (
    <aside className="left-sidebar" aria-label="ナビゲータ">
      <div className="sidebar-scroll">
        {s.screen === "chat" ? (
          <section className="side-section">
            <header>会話</header>
            {CONVERSATIONS.map((conversation) => (
              <button key={conversation.id} className="tree-row" aria-selected={conversation.id === "c1"}>
                <span className="label">{conversation.name}</span>
                <span className="meta">{conversation.meta}</span>
              </button>
            ))}
          </section>
        ) : (
          <>
            <section className="side-section">
              <header>ケース</header>
              <CaseTree
                cases={CASES}
                selectedId={s.selectedCaseId}
                onSelect={(id) => session.selectCase(id)}
              />
            </section>
            <section className="side-section">
              <header>変数</header>
              <VariableRow name="降伏応力" value="250" unit="MPa" origin="declared" />
              <VariableRow name="最大応力（保持）" value="241.7" unit="MPa" origin="computed" />
              <VariableRow name="供試体温度" value="23.4" unit="degC" origin="measured" />
              <VariableRow name="密度" value="7850" unit={null} origin="dataset" />
            </section>
            <section className="side-section">
              <header>資料</header>
              <button className="tree-row">
                <span className="label">設計基準_2026.pdf</span>
                <span className="meta">参照</span>
              </button>
              <p className="prop-note" style={{ padding: "0 10px 8px" }}>
                資料は講評の根拠になり、数値を上書きしません（INV-008）
              </p>
            </section>
          </>
        )}
      </div>
      <button
        className="dock-splitter splitter-left"
        role="separator"
        aria-orientation="vertical"
        aria-label="左パネルの幅"
        onKeyDown={onSplitterKey}
        onPointerDown={onSplitterPointer}
      />
    </aside>
  );
}
