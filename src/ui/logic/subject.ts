/* Which case an area shows, and why (11_ui.md "Which cases an area is showing", 16_application_model
 * §8.2, XC-292): the rule in one place, so the badge in every area's header, the store's choice of
 * dataset and the graph's context all read the same answer. The order is the specification's: an item
 * that names its own cases is the authority and the tree cannot override it; otherwise the area is
 * pinned to a case a person chose; otherwise it follows the tree's selection. No React, no transport,
 * and nothing here reads the engine - the store hands in what the engine answered. */

export type Area = "view" | "graph" | "report";

/** An area's binding (16_application_model §8.2): follow the tree, or pinned to one case. Session
 *  state - a pin that must survive the session is an explicit binding on the item, not this. */
export type SubjectBinding = { readonly mode: "follow" } | { readonly mode: "pinned"; readonly caseId: string };

export const FOLLOW: SubjectBinding = { mode: "follow" };

/** A case of the open document, as `workspace.open` lists them (CT-003 3.14.0). */
export interface CaseSummary {
  readonly id: string;
  readonly name: string;
  readonly parentId?: string;
}

export type SubjectSource = "item" | "pinned" | "tree" | "none";

export interface AreaSubject {
  /** Every case the area shows; several only where the item names several. */
  readonly caseIds: readonly string[];
  /** The one a single-case area works on, or null where nothing is selected. */
  readonly caseId: string | null;
  readonly source: SubjectSource;
  /** `ケース baseline（case:1）` - the document's own name, the id beside it. */
  readonly label: string;
  /** Why this case: in the words the badge shows beside the label. */
  readonly because: string;
}

export const AREA_LABEL: Readonly<Record<Area, string>> = { view: "ビュー", graph: "グラフ", report: "レポート" };

export const SOURCE_WORD: Readonly<Record<SubjectSource, string>> = {
  tree: "ツリーの選択に追従",
  pinned: "この領域に固定",
  item: "この項目自身の束縛（ツリーでは変わりません）",
  none: "ツリーで選ぶと、この領域はそれを表示します",
};

/** The document's name for a case with its id beside, or the id alone where the document does not
 *  list it - never a name made up here. */
export function caseName(cases: readonly CaseSummary[], id: string): string {
  const found = cases.find((one) => one.id === id);
  return found ? `${found.name}（${found.id}）` : id;
}

/** What the area shows. `itemCaseIds` is null where the open item names no cases of its own, and a
 *  list - possibly empty, when the item names cases this session cannot resolve - where it does. */
export function areaSubject(
  binding: SubjectBinding,
  selectedCaseId: string | null,
  itemCaseIds: readonly string[] | null,
  cases: readonly CaseSummary[],
): AreaSubject {
  if (itemCaseIds !== null) {
    const label =
      itemCaseIds.length > 0
        ? `ケース ${itemCaseIds.map((id) => caseName(cases, id)).join("、")}`
        : "この項目が参照するデータセットは、このセッションに読み込まれていません";
    return { caseIds: itemCaseIds, caseId: itemCaseIds[0] ?? null, source: "item", label, because: SOURCE_WORD.item };
  }
  if (binding.mode === "pinned") {
    return { caseIds: [binding.caseId], caseId: binding.caseId, source: "pinned", label: `ケース ${caseName(cases, binding.caseId)}`, because: SOURCE_WORD.pinned };
  }
  if (selectedCaseId !== null) {
    return { caseIds: [selectedCaseId], caseId: selectedCaseId, source: "tree", label: `ケース ${caseName(cases, selectedCaseId)}`, because: SOURCE_WORD.tree };
  }
  return { caseIds: [], caseId: null, source: "none", label: "ケース未選択", because: SOURCE_WORD.none };
}

/** A row of the case tree: the document's case, with what this session loaded for it said beside. */
export interface CaseTreeNode {
  readonly id: string;
  readonly name: string;
  readonly axis?: string;
  readonly children?: CaseTreeNode[];
}

export const LOADED_WORD = "読み込み済み";

/** The document's cases as a tree, by the parent each names. A parent the document does not list
 *  leaves its child at the root rather than dropped: a case hidden by a broken reference is a case the
 *  reader cannot find (XC-001). */
export function caseTree(cases: readonly CaseSummary[], loadedCaseIds: readonly string[]): CaseTreeNode[] {
  const known = new Set(cases.map((one) => one.id));
  const build = (parent: string | undefined): CaseTreeNode[] =>
    cases
      .filter((one) => (parent === undefined ? one.parentId === undefined || !known.has(one.parentId) : one.parentId === parent))
      .map((one) => {
        const children = build(one.id);
        return {
          id: one.id,
          name: one.name,
          ...(loadedCaseIds.includes(one.id) ? { axis: LOADED_WORD } : {}),
          ...(children.length > 0 ? { children } : {}),
        };
      });
  return build(undefined);
}

export interface SavedViewLike {
  readonly id: string;
  readonly name: string;
  readonly datasetId?: string;
}

export interface LoadedCase {
  readonly caseId: string;
  readonly datasetId: string;
}

/** The working view of a case for a field: the saved view to update, or the name to create one under.
 *
 *  A view is named by its field, and the document refuses two items under one name (workspace/AC-030).
 *  A saved view under the field's name is this case's own where its dataset is this case's, and is
 *  adopted where its dataset is nobody's this session - a view saved last session, whose dataset id
 *  died with that session. Where the name belongs to **another loaded case**, this case's view is
 *  named with its case, so two cases showing one field are two views the document can hold. */
export function workingView(
  fieldName: string,
  caseId: string,
  savedViews: readonly SavedViewLike[],
  loaded: readonly LoadedCase[],
): { name: string; existing: SavedViewLike | null } {
  const qualified = `${fieldName}（${caseId}）`;
  const own = savedViews.find((one) => one.name === qualified);
  if (own) return { name: qualified, existing: own };
  const plain = savedViews.find((one) => one.name === fieldName);
  if (!plain) return { name: fieldName, existing: null };
  const holder = loaded.find((one) => one.datasetId === plain.datasetId);
  if (holder && holder.caseId !== caseId) return { name: qualified, existing: null };
  return { name: fieldName, existing: plain };
}

/** The cases a report names through its view blocks, or null where it has none: a report's binding
 *  is its blocks' views, each bound to the dataset it was made from (11_ui.md). A view whose dataset
 *  is not loaded this session names no case, and the empty list says so. */
export function reportItemCases(
  blocks: readonly { readonly kind: string; readonly viewId?: string }[],
  savedViews: readonly SavedViewLike[],
  loaded: readonly LoadedCase[],
): string[] | null {
  const views = blocks.filter((one) => one.kind === "view");
  if (views.length === 0) return null;
  const found: string[] = [];
  for (const block of views) {
    const saved = savedViews.find((one) => one.id === block.viewId);
    const holder = loaded.find((one) => one.datasetId === saved?.datasetId);
    if (holder && !found.includes(holder.caseId)) found.push(holder.caseId);
  }
  return found;
}
