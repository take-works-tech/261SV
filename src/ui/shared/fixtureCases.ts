/* The case tree the design states show (11_ui.md): one definition, so the navigator, the subject
 * badge and any screen naming a fixture case agree. Fixture, never evidence: with an engine the tree
 * is the document's, from `workspace.open` (XC-292). */
import type { CaseNode } from "./CaseTree";
import type { CaseSummary } from "../logic/subject";

export const FIXTURE_CASE_TREE: CaseNode[] = [
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

function flatten(nodes: readonly CaseNode[], parentId?: string): CaseSummary[] {
  return nodes.flatMap((node) => [
    { id: node.id, name: node.name, ...(parentId ? { parentId } : {}) },
    ...flatten(node.children ?? [], node.id),
  ]);
}

/** The same tree flat, in the form the subject rule takes. */
export const FIXTURE_CASES: readonly CaseSummary[] = flatten(FIXTURE_CASE_TREE);
