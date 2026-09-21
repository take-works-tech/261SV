/* The Workspace list with an engine (XC-297, workspace/AC-076): the workspaces this shell opened,
 * narrowed by a search and by the tags their cases carry, newest first. Nothing here is a claim about
 * a workspace's contents - the name and tags are what the engine answered when it was opened, and
 * the path is where it was then. No React and no transport. */
import type { RecentWorkspace } from "../client/shell";
import { describeRecorded } from "./time";

/** The tags the listed workspaces actually carry, each once, in order of first appearance: the
 *  filter never offers a tag no entry has. */
export function tagsOf(entries: readonly RecentWorkspace[]): string[] {
  const seen: string[] = [];
  for (const entry of entries) {
    for (const tag of entry.tags) if (!seen.includes(tag)) seen.push(tag);
  }
  return seen;
}

/** The entries a query and a tag choice leave: the query against the name, the path and the tags,
 *  case-insensitively; every chosen tag must be carried. Order is kept - the list is newest first. */
export function filterRecent(entries: readonly RecentWorkspace[], query: string, tags: readonly string[]): RecentWorkspace[] {
  const needle = query.trim().toLowerCase();
  return entries.filter((entry) => {
    const haystack = `${entry.name} ${entry.path} ${entry.tags.join(" ")}`.toLowerCase();
    if (needle !== "" && !haystack.includes(needle)) return false;
    return tags.every((tag) => entry.tags.includes(tag));
  });
}

/** What the filters say they did, for the count line and the empty state. */
export function describeFilters(query: string, tags: readonly string[]): string | null {
  const parts = [query.trim() !== "" ? `検索「${query.trim()}」` : null, tags.length > 0 ? `タグ「${tags.join("・")}」` : null].filter(
    (part): part is string => part !== null,
  );
  return parts.length > 0 ? parts.join("、") : null;
}

/** When the entry was last opened, in the reader's zone with the recorded offset beside it where it
 *  differs (XC-142). */
export function describeOpened(entry: RecentWorkspace, readerOffsetMinutes?: number): string {
  return `最後に開いた：${describeRecorded(entry.openedAt, readerOffsetMinutes)}`;
}

/** The file's name without its extension: what a fresh document is called when nobody named it. */
export function suggestedName(path: string): string {
  const base = path.split(/[\\/]/).pop() ?? path;
  return base.replace(/\.svw$/i, "");
}
