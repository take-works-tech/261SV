/* The recent-workspace list the shell keeps (XC-297): what a person opened, where, and when, so the
 * Workspace list can offer it again. Kept by the shell because it is the shell's knowledge - the
 * engine holds one document at a time and remembers nothing across sessions - and kept as one JSON
 * file under the profile, written whole beside itself and moved into place (XC-055's rule for files
 * that must be whole or absent). No Electron in this module, so it is tested under plain Node.
 *
 * Nothing here is a claim about a workspace: a name and tags are what the engine answered when the
 * document was opened, and the path is where it was then. A file that has since gone is found out
 * when it is opened again, and the entry is removed only when a person asks. */
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

import type { RecentWorkspace } from "../ui/client/shell.js";

/** How many entries the list keeps. More than the Workspace list shows on one screen, and few
 *  enough that "recent" still means recent; a list of every document ever opened is a history, and
 *  the document's own folder is where a person keeps that. */
export const RECENT_LIMIT = 20;

function sameFile(one: string, another: string): boolean {
  // Windows paths compare without case; elsewhere a path is its exact characters.
  return process.platform === "win32" ? one.toLowerCase() === another.toLowerCase() : one === another;
}

function isEntry(value: unknown): value is RecentWorkspace {
  if (typeof value !== "object" || value === null) return false;
  const one = value as Record<string, unknown>;
  return (
    typeof one.path === "string" && one.path !== ""
    && typeof one.name === "string"
    && Array.isArray(one.tags) && one.tags.every((tag) => typeof tag === "string")
    && typeof one.openedAt === "object" && one.openedAt !== null
  );
}

/** The list as the file holds it, newest first. A file that is missing, unreadable or not the shape
 *  this module writes reads as an empty list: the list is a convenience, and a corrupt one is not a
 *  reason to refuse to start. */
export function readRecent(file: string): RecentWorkspace[] {
  if (!existsSync(file)) return [];
  try {
    const parsed: unknown = JSON.parse(readFileSync(file, "utf-8"));
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isEntry).slice(0, RECENT_LIMIT);
  } catch {
    return [];
  }
}

function writeRecent(file: string, entries: readonly RecentWorkspace[]): void {
  mkdirSync(dirname(file), { recursive: true });
  const temporary = join(dirname(file), `.${Date.now()}-${process.pid}.recent.writing`);
  writeFileSync(temporary, JSON.stringify(entries, null, 2) + "\n", "utf-8");
  renameSync(temporary, file);
}

/** The list with `entry` at its head: the same path already listed is replaced, not doubled. */
export function remember(file: string, entry: RecentWorkspace): RecentWorkspace[] {
  const kept = readRecent(file).filter((one) => !sameFile(one.path, entry.path));
  const next = [entry, ...kept].slice(0, RECENT_LIMIT);
  writeRecent(file, next);
  return next;
}

/** The list without `path`. Removing is a person's choice (XC-262's rule for files that are theirs). */
export function forget(file: string, path: string): RecentWorkspace[] {
  const next = readRecent(file).filter((one) => !sameFile(one.path, path));
  writeRecent(file, next);
  return next;
}
