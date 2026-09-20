/* The outliner's rows from the engine's parts (view/AC-055, AC-056, XC-274): the file's own hierarchy
 * from each part's path and never an inferred one; an absent part where the file put it, with the
 * reader's reason; and what a visibility control does to the view's `partVisibility` - the row's
 * branch, or that branch alone. No React and no transport here. */
import type { Results } from "../client/engine";

/** One row of `dataset.parts`, as the engine answered it. */
export type PartRow = Results["dataset.parts"]["parts"][number];

/** The one-line form of a path, as the engine writes a part's `name` and `parentId`. Mirrors
 *  `SEPARATOR` in src/domain_core/parts.py: the engine joins, this layer only ever reads. */
export const PATH_SEPARATOR = " / ";

export type OutlinerNode = {
  id: string;
  name: string;
  kind: string;
  visible?: boolean;
  children?: OutlinerNode[];
  /** What the row's visibility control is: a part's own, a branch's (every part under it), or
   *  none - an absent part has nothing to show. Absent means a part's own, for the design states. */
  toggle?: "part" | "branch" | "none";
};

export type ToggleModifiers = { shift: boolean; ctrl: boolean };

/** "toggle" flips the row's branch; "isolate" shows that branch and hides every other part. Shift is
 *  the same as a plain click here: a block has no visibility of its own, so its control already
 *  reaches its descendants, and a part has none. */
export type ToggleMode = "toggle" | "isolate";

/** The absence as one line: the file's name and the reader's reason, kept as two facts by the engine
 *  and joined here for a sentence (XC-272). */
export function describeAbsence(part: PartRow): string {
  return part.reason ? `${part.name}（${part.reason}）` : part.name;
}

/** What is missing from a partial case, by name and reason, for the mark on the pane (AC-027). */
export function absentParts(parts: readonly PartRow[] | null): string[] {
  return (parts ?? []).filter((one) => one.type === "absent").map(describeAbsence);
}

/** Shown unless the map says hidden: the map carries only the hidden parts (CT-004). */
export function isShown(visibility: Readonly<Record<string, boolean>>, name: string): boolean {
  return visibility[name] !== false;
}

function isPresent(part: PartRow): boolean {
  return part.type !== "absent";
}

/** The present parts under a row: the part itself, or every part whose path continues the block's. */
function branchOf(parts: readonly PartRow[], id: string): string[] {
  return parts
    .filter(isPresent)
    .map((one) => one.name)
    .filter((name) => name === id || name.startsWith(id + PATH_SEPARATOR));
}

/** The rows: a block for every step of a path the file has, and each part as a leaf under its
 *  own. A flat file reads flat, and an absent part sits where the file put it, marked and without
 *  a control (AC-056). */
export function outlinerTree(parts: readonly PartRow[], visibility: Readonly<Record<string, boolean>>): OutlinerNode[] {
  const roots: OutlinerNode[] = [];
  const blocks = new Map<string, OutlinerNode>();
  for (const part of parts) {
    let siblings = roots;
    for (let depth = 1; depth < part.path.length; depth += 1) {
      const id = part.path.slice(0, depth).join(PATH_SEPARATOR);
      let block = blocks.get(id);
      if (!block) {
        block = { id, name: part.path[depth - 1] ?? id, kind: "ブロック", children: [], toggle: "branch" };
        blocks.set(id, block);
        siblings.push(block);
      }
      siblings = block.children ?? (block.children = []);
    }
    const present = isPresent(part);
    siblings.push({
      id: part.name,
      name: part.path[part.path.length - 1] ?? part.name,
      kind: present ? "部品" : `欠け${part.reason ? `（${part.reason}）` : ""}`,
      visible: present ? isShown(visibility, part.name) : undefined,
      toggle: present ? "part" : "none",
    });
  }
  // A block is shown while anything under it is: its control reads as the branch's state.
  const settle = (node: OutlinerNode): boolean => {
    if (!node.children) return node.visible !== false && node.toggle !== "none";
    const shown = node.children.map(settle).some(Boolean);
    node.visible = shown;
    return shown;
  };
  for (const root of roots) settle(root);
  return roots;
}

/** The view's `partVisibility` after a control on `id` is used. The map stays minimal - a shown part
 *  has no entry - so the document says only what differs from the file (CT-004, XC-274). */
export function visibilityAfter(
  parts: readonly PartRow[],
  current: Readonly<Record<string, boolean>>,
  id: string,
  mode: ToggleMode,
): Record<string, boolean> {
  const branch = branchOf(parts, id);
  const next: Record<string, boolean> = { ...current };
  if (branch.length === 0) return next;
  if (mode === "isolate") {
    for (const part of parts.filter(isPresent)) next[part.name] = branch.includes(part.name);
  } else {
    const target = !branch.every((name) => isShown(current, name));
    for (const name of branch) next[name] = target;
  }
  for (const name of Object.keys(next)) {
    if (next[name] === true) delete next[name];
  }
  return next;
}
