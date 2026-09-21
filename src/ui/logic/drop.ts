/* What a drop on the window means before anything is read (XC-301, ingest/AC-020, AC-021, AC-049): a
 * plan from the paths and the document's records alone - one workspace to open, one result file into
 * a case, several files each into the case whose record holds that very file, or a refusal that names
 * why - decided here so the store executes and the screen reports. A record is a path and never a
 * name: a file that merely shares its name with a recorded one is not sent anywhere on that account.
 * The format's support is not judged here: the engine's `dataset.inspect` says it, and a file it
 * names as unsupported is refused with the engine's own words. No React and no transport. */

export const WORKSPACE_SUFFIX = ".svw";

export interface DroppedCase {
  readonly id: string;
  readonly name: string;
}

/** A file a case is known to hold: recorded in the document when it was opened, or read into the
 *  case in this session. Path for path, never by name (XC-301). */
export interface CaseRecord {
  readonly caseId: string;
  readonly path: string;
}

export interface DropContext {
  readonly workspaceOpen: boolean;
  readonly cases: readonly DroppedCase[];
  /** The case the View area shows, or null when nothing is selected. */
  readonly caseId: string | null;
  readonly records: readonly CaseRecord[];
}

/** Why one file goes where it goes: its record, the case on screen, or the only case there is. */
export type LoadReason = "recorded" | "shown" | "only";

export type DropPlan =
  | { kind: "openWorkspace"; path: string }
  | { kind: "load"; path: string; caseId: string; because: LoadReason }
  | { kind: "loadEach"; loads: readonly { path: string; caseId: string }[] }
  | { kind: "refused"; reason: string };

export const LOAD_REASON_WORD: Readonly<Record<LoadReason, string>> = {
  recorded: "この文書がこのファイルを記録しているケース",
  shown: "表示中のケース",
  only: "唯一のケース",
};

export function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

function isWorkspace(path: string): boolean {
  return path.toLowerCase().endsWith(WORKSPACE_SUFFIX);
}

/** One path in one form: separators either way, `.` and `..` folded, and case ignored where the
 *  path is a Windows one (a drive or a backslash), because that is where the filesystem ignores it. */
function normalise(path: string): string {
  const windows = /^[A-Za-z]:/.test(path) || path.includes("\\");
  const parts: string[] = [];
  for (const segment of path.replace(/\\/g, "/").split("/")) {
    if (segment === "" || segment === ".") {
      if (parts.length === 0 && segment === "") parts.push("");
      continue;
    }
    if (segment === ".." && parts.length > 0 && parts[parts.length - 1] !== "" && parts[parts.length - 1] !== "..") {
      parts.pop();
      continue;
    }
    parts.push(segment);
  }
  const joined = parts.join("/");
  return windows ? joined.toLowerCase() : joined;
}

/** Whether two paths name one file, as far as the paths alone can say. */
export function samePath(one: string, another: string): boolean {
  return normalise(one) === normalise(another);
}

/** The cases whose records hold this very file, each once. */
function recordedCases(path: string, records: readonly CaseRecord[]): string[] {
  const ids: string[] = [];
  for (const record of records) {
    if (samePath(record.path, path) && !ids.includes(record.caseId)) ids.push(record.caseId);
  }
  return ids;
}

function describeCase(id: string, cases: readonly DroppedCase[]): string {
  const found = cases.find((one) => one.id === id);
  return found ? `${found.name}（${found.id}）` : id;
}

function refused(reason: string): DropPlan {
  return { kind: "refused", reason };
}

/** What a drop asks for, or why it asks for nothing (XC-301). */
export function dropPlan(paths: readonly string[], context: DropContext): DropPlan {
  if (paths.length === 0) return refused("落とされたものにファイルがありません");
  const workspaces = paths.filter(isWorkspace);
  if (paths.length === 1 && workspaces.length === 1) return { kind: "openWorkspace", path: paths[0]! };
  if (workspaces.length > 0) {
    return refused(`ワークスペース（${workspaces.map(fileName).join("、")}）と結果ファイルは一緒には落とせません。先にワークスペースを落としてから、結果ファイルを落としてください`);
  }
  if (!context.workspaceOpen) {
    return refused(`${paths.map(fileName).join("、")} を読み込む先のワークスペースが開いていません。先にワークスペース（${WORKSPACE_SUFFIX}）を開くか落としてください`);
  }
  return paths.length === 1 ? planOne(paths[0]!, context) : planEach(paths, context);
}

/** One file: the case whose record holds it, else the case on screen, else the only case, else a
 *  refusal naming the cases. A file two cases record goes to the shown one if it is among them. */
function planOne(path: string, context: DropContext): DropPlan {
  const recorded = recordedCases(path, context.records);
  if (recorded.length === 1) return { kind: "load", path, caseId: recorded[0]!, because: "recorded" };
  if (recorded.length > 1) {
    if (context.caseId && recorded.includes(context.caseId)) return { kind: "load", path, caseId: context.caseId, because: "shown" };
    return refused(`${fileName(path)} は複数のケースの記録にあります（${recorded.map((id) => describeCase(id, context.cases)).join("、")}）。ツリーでそのどれかを選んでから落としてください`);
  }
  if (context.caseId) return { kind: "load", path, caseId: context.caseId, because: "shown" };
  if (context.cases.length === 1) return { kind: "load", path, caseId: context.cases[0]!.id, because: "only" };
  const names = context.cases.map((one) => `${one.name}（${one.id}）`).join("、");
  return refused(context.cases.length === 0 ? "このワークスペースにケースがありません" : `どのケースに読み込むか決まっていません（あるのは ${names}）。先に一つのケースへ読み込んでから落としてください`);
}

/** Several files: each must be recorded under exactly one case, and no two under the same; otherwise
 *  nothing is loaded and every file that fails is named with why. The loads come out in the
 *  document's order of cases, not the drop's - the order the operating system hands files over is
 *  the order nobody chose. */
function planEach(paths: readonly string[], context: DropContext): DropPlan {
  const loads: { path: string; caseId: string }[] = [];
  const problems: string[] = [];
  const taken = new Map<string, string>();
  for (const path of paths) {
    const recorded = recordedCases(path, context.records);
    if (recorded.length === 0) {
      problems.push(`${fileName(path)}：どのケースの記録にもありません`);
      continue;
    }
    if (recorded.length > 1) {
      problems.push(`${fileName(path)}：複数のケースの記録にあります（${recorded.map((id) => describeCase(id, context.cases)).join("、")}）`);
      continue;
    }
    const caseId = recorded[0]!;
    const earlier = taken.get(caseId);
    if (earlier !== undefined) {
      problems.push(`${fileName(path)}：${earlier} と同じケース ${describeCase(caseId, context.cases)}に当たります`);
      continue;
    }
    taken.set(caseId, fileName(path));
    loads.push({ path, caseId });
  }
  if (problems.length > 0) {
    return refused(`複数のファイルは、どれもがこの文書の記録から一意にケースへ決まるときだけ読み込みます。決まらないので何も読み込みません：${problems.join("；")}。1 件ずつ落とせば表示中のケースへ読み込みます`);
  }
  const order = new Map(context.cases.map((one, index) => [one.id, index] as const));
  loads.sort((one, another) => (order.get(one.caseId) ?? Number.MAX_SAFE_INTEGER) - (order.get(another.caseId) ?? Number.MAX_SAFE_INTEGER));
  return { kind: "loadEach", loads };
}

/** Whether an inspection lets a load proceed: the engine names the level; `Absent` is a format this
 *  build has no reader for, and a file that is not there is not a file (AC-021). */
export function inspectionAllowsLoad(inspection: { exists: boolean; supportLevel: string; format: string; gaps: readonly string[]; refusal?: string }, path: string): string | null {
  if (!inspection.exists) return `${fileName(path)} がありません`;
  // The engine already knows the load would be refused - a path its library cannot take (XC-293).
  if (inspection.refusal) return inspection.refusal;
  if (inspection.supportLevel.toLowerCase() === "absent") {
    return `'.${inspection.format}' はこの版が読む形式ではありません（対応水準 ${inspection.supportLevel}）。部分的なケースは作りません（ingest/AC-021）`;
  }
  return null;
}
