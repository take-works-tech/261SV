/* What the shell keeps under its profile, and where (XC-262, XC-263, XC-297, XC-300).
 *
 * Three things outlive a session: the engine's transient root, where every session directory lives
 * (XC-262); the log directory, where the engine's diagnostic log and the shell's notes sit beside
 * each other (XC-263); and the recent-workspace list (XC-297). The list carries a customer's names
 * in its paths, so it is kept beside the other two and inside neither: nothing the engine is told
 * about - its root, its logs - contains it, and a bundle that one day packages a directory cannot
 * pick it up by accident (XC-300). This module is the one place the arrangement is written, so
 * `profile.test.ts` can hold it. No Electron here: the root is given, so it runs under plain Node.
 */
import { isAbsolute, join, relative, sep } from "node:path";

export interface ProfileLayout {
  /** The profile itself: `userData` in the product, a root of its own under temp for the smoke. */
  readonly root: string;
  /** Everything transient: session directories named by the shell's pid (XC-262). */
  readonly engineRoot: string;
  /** The engine's diagnostic log and the shell's own notes, beside each other (XC-263). */
  readonly logDirectory: string;
  /** The recent-workspace list (XC-297): beside the two above and inside neither (XC-300). */
  readonly recentFile: string;
}

export function layoutUnder(root: string): ProfileLayout {
  return {
    root,
    engineRoot: join(root, "engine"),
    logDirectory: join(root, "logs"),
    recentFile: join(root, "recent.json"),
  };
}

/** Whether `file` lies under `directory` - by path arithmetic and not by the filesystem, so it
 *  answers for a layout that does not exist yet. A directory is not inside itself. */
export function isInside(file: string, directory: string): boolean {
  const between = relative(directory, file);
  if (between === "" || isAbsolute(between)) return false;
  return between !== ".." && !between.startsWith(`..${sep}`);
}
