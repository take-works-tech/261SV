/* What the engine has, as the interface holds it (MOD-016) - and never the authority.
 *
 * The authority is the workspace, reached through the command surface (MOD-007, INV-006). This is
 * the client-side view of it, and a divergence between the two is resolved by asking rather than by
 * merging: every field here arrived in an answer, and nothing here computes a number.
 *
 * **Two modes, and the interface says which it is in.** With no engine reachable, the screens are
 * what they have been: a catalogue of design states, each labelled as one. With an engine, the same
 * screens show what it answered. Nothing in between - a screen showing fixture data while claiming
 * to be live is the failure this product exists to refuse.
 *
 * The transition classes of session.ts apply here too: loading a dataset is class 3 (it changes the
 * document), declaring a unit and choosing a field are class 2 (the subject changes and every
 * following area re-renders), and a camera move is class 1: it reaches the engine as the camera the
 * picture is drawn with (`view.render`, `view.pick`) and never as a change to the view's definition
 * (XC-270). Until 2026-09-20 every orbit was a `view.update`, one undo step and one unsaved write.
 */
import { useCallback, useSyncExternalStore } from "react";
import { Engine, TransportFailure, reasonText } from "../client/engine";
import type { Connection, Operation, Options, Parameters, Response, Results } from "../client/engine";
import { OPERATION_FACTS, type CameraDefinition, type RecordedTime } from "../client/generated";
import { recordNow } from "../client/time";
import { shellApi } from "../client/shell";
import { FIRST_PATH, withKeyframe, withoutKeyframe, type CameraPathDefinition, type Interpolation } from "../logic/cameraPath";
import { dropPlan, fileName, inspectionAllowsLoad, LOAD_REASON_WORD, type CaseRecord } from "../logic/drop";
import { areaSubject, reportItemCases, workingView, type Area, type AreaSubject, type CaseSummary } from "../logic/subject";
import { session } from "./session";

/** Whether an engine is reachable, and what it said if it is not. */
export type Reachability =
  | { kind: "unknown" }
  | { kind: "reachable"; protocols: readonly string[] }
  | { kind: "absent"; because: string }
  /** The shell's engine process was running and ended (XC-259). What is on screen came from it
   *  and is kept, labelled as from an engine that is gone; nothing is asked of it again until a
   *  person restarts it. Distinct from `absent` because a person does different things about the
   *  two: one never had an engine, the other lost one and can be told why. */
  | { kind: "exited"; because: string; exitCode: number | null; signal: string | null };

/** One field of a loaded dataset, as `dataset.load` answered it. The unit is null until a person
 *  declares one: nothing in this product infers one (XC-003). */
export interface FieldSummary {
  readonly name: string;
  readonly association: "point" | "cell" | "integrationPoint" | "field";
  readonly unit: string | null;
  /** How many numbers each entry is: 1 a scalar, 3 a vector, 6 a symmetric tensor (E-073). A
   *  field of several is coloured and summarised only through a derived quantity (XC-282). */
  readonly components?: number;
  /** How many entries the file has no value for (XC-303): said before anyone reads a number. */
  readonly missingCount?: number;
}

/** What a derived field was made by: the formula and the conventions the engine answered with
 *  `field.derive`, shown beside the field wherever it appears (INV-020). */
export interface Derivation {
  readonly source: string;
  readonly quantity: string;
  readonly formula: string;
  readonly conventions: readonly string[];
}

/** A number the engine reported, carried whole. Never unpacked into a bare value: a value without
 *  its unit, digits and provenance is a value in whatever unit the reader assumed (XC-003). */
export type Reported = Results["dataset.probe"]["value"];

/** What a person asked a graph to plot: one field, one reduction, over the cases or the result axis. */
export interface GraphSpec {
  readonly fieldName: string;
  readonly reduction: "max" | "min" | "mean";
  readonly kind: "line" | "overTime";
}
/** What the engine answered about a frame drawn from a camera path (CT-003 3.12.0). */
export type PathPreview = NonNullable<Results["view.render"]["cameraPath"]>;

/** What a drop on the window came to (XC-291). */
export type DropOutcome =
  | { kind: "opened"; path: string }
  | { kind: "loaded"; path: string; caseId: string }
  | { kind: "loadedEach"; loads: readonly { path: string; caseId: string }[] }
  | { kind: "refused"; reason: string };

/** A notice this window raised - a refusal, a failure, a warning beside an answer - kept after
 *  dismissal with the time it was dismissed (16_application_model §12, XC-286). The engine's log
 *  holds the same facts; this is the window's own list of what it showed. */
export interface Notice {
  readonly id: string;
  readonly at: RecordedTime;
  readonly severity: "info" | "warning" | "error" | "refusal";
  readonly title: string;
  readonly detail: string;
  readonly operation?: string;
  readonly dismissedAt?: RecordedTime;
}
/** Which step a number is of, as the engine states it beside every number (CT-003 3.10.0). */
export type StatedPosition = Results["field.statistics"]["resultPosition"];

/** One write the engine applied since the document was last saved. What a crash loses is exactly
 *  this list, so it is kept as the engine answers it - operation and the engine's own summary - and
 *  never reconstructed afterwards (XC-259). */
export interface AppliedWrite {
  readonly operation: string;
  readonly summary: string;
  readonly at: RecordedTime;
}

/** What was opened, so that what was saved can be opened again after the engine is restarted: the
 *  document, and every file read into a case, in the order they were read (XC-292). */
export interface Opened {
  readonly workspacePath: string;
  readonly loads: readonly { readonly caseId: string; readonly filePath: string }[];
}

/** What this session loaded for one case, kept when the View area moves to another case so that
 *  coming back is a switch and not a second read (XC-292). Every member arrived in an answer. */
export interface LoadedSummary {
  readonly caseId: string;
  readonly datasetId: string;
  readonly filePath: string;
  readonly sourceName: string;
  readonly supportLevel: string | null;
  readonly gaps: readonly string[];
  readonly fields: readonly FieldSummary[];
  readonly derived: Readonly<Record<string, Derivation>>;
  readonly described: Results["dataset.describe"] | null;
  readonly parts: Results["dataset.parts"]["parts"] | null;
  readonly partial: boolean;
  readonly bounds: readonly [number[], number[]] | null;
  /** The field the area showed for this case, so coming back shows it again. */
  readonly fieldName: string | null;
}

/** A view the opened document already holds, as `workspace.open` answered it. */
export interface SavedView {
  readonly id: string;
  readonly name: string;
  readonly datasetId?: string;
}

/** A block of the document's report, as CT-006 has it. */
export interface ReportBlock {
  readonly kind: "view" | "graph" | "valueTable" | "text" | "pageBreak";
  readonly viewId?: string;
  readonly form?: "still" | "video" | "interactive";
  readonly graphId?: string;
  readonly fields?: readonly string[];
  readonly text?: string;
  readonly authorship?: "person" | "generated";
  readonly derivedFrom?: readonly string[];
}

/** The report's definition as the document holds it (CT-006): read back with `report.get`, written
 *  whole with `report.update` (XC-275). Members this build does not edit round-trip untouched. */
export interface ReportDefinition {
  readonly id: string;
  readonly name?: string;
  readonly targets: readonly string[];
  readonly blocks: readonly ReportBlock[];
  readonly locale?: string;
  readonly [member: string]: unknown;
}

/** What running one operation by name came to (XC-278): the engine's answer as given, or its
 *  refusal as a reason. `applied` is a write the journal now holds; `answered` changed nothing. */
export interface RunOutcome {
  readonly status: "answered" | "applied" | "refused";
  readonly result: unknown;
  readonly reason: string | null;
}

/** The document's lock as `workspace.open` answered it (XC-241, XC-269). */
export type Lock = NonNullable<Results["workspace.open"]["lock"]>;

/** What `dataset.inspect` said about a file that is not loaded yet (ingest/AC-032). */
export type Inspection = Results["dataset.inspect"] & { readonly path: string };

export interface EngineState {
  readonly reachability: Reachability;
  readonly opened: Opened | null;
  /** The file under review before loading, or null. Cleared by loading it or by cancelling. */
  readonly inspection: Inspection | null;
  /** What the document held when it was opened. A working view is updated when one of these has
   *  its name, because the document refuses a second view under a name it holds (AC-030). */
  readonly savedViews: readonly SavedView[];
  /** The reports the document held when it was opened; the working report is adopted when one has
   *  its name (AC-030), as views are. */
  readonly savedReports: readonly SavedView[];
  readonly savedGraphs: readonly SavedView[];
  /** The graph this session shows, its definition as written, and the engine's data for it (XC-290). */
  readonly graphId: string | null;
  readonly graphSpec: GraphSpec | null;
  readonly graphData: Results["graph.data"] | null;
  /** The document's report this session works on: its id, its definition as last read back, and
   *  the revision the document holds (XC-275). Null until a report is made or adopted. */
  readonly reportId: string | null;
  readonly report: ReportDefinition | null;
  readonly reportRevision: number | null;
  /** The trust content as `report.provenance` answered it, or why it could not: the item that
   *  cannot be produced blocks the export and names itself (report/AC-007, AC-031). */
  readonly provenance: Results["report.provenance"] | null;
  readonly provenanceRefusal: string | null;
  /** What the last export wrote, as the engine answered it (report/AC-014). */
  readonly exported: Results["report.export"] | null;
  /** Which catalogue operations this build answers, as `system.operations` said (XC-277). Null
   *  until asked; the settings ask when they open. */
  readonly operations: Results["system.operations"] | null;
  /** Applied writes since the last save. Cleared by a save, by opening a workspace, and by an exit -
   *  into `lost`. */
  readonly journal: readonly AppliedWrite[];
  /** What the last exit lost, until a person dismisses it. Null when nothing was lost or nothing
   *  ended. */
  readonly lost: readonly AppliedWrite[] | null;
  readonly savedAt: RecordedTime | null;
  /** The engine's own record of what was asked, as `history.list` last answered it, with what
   *  the caps dropped said in numbers (LIM-014, LIM-015). Null until asked. */
  readonly history: Results["history.list"] | null;
  readonly workspaceId: string | null;
  /** The document's name and the tags of its cases as one set, as `workspace.open` answered (XC-297). */
  readonly workspaceName: string | null;
  readonly caseTags: readonly string[];
  /** Whether the document may not be written back - somebody else holds its lock - and what the
   *  lock said. Read-only is drawn at the save: the window works in memory (XC-269). */
  readonly readOnly: boolean;
  readonly lock: Lock | null;
  /** What the engine's last answer warned about, in its own words, until dismissed. Dropped until
   *  2026-09-20, which is how a document lifted, a dataset closed or a lock held went unsaid. */
  readonly warnings: readonly string[];
  /** Every notice this window raised, in order, dismissed ones included (XC-286). */
  readonly notices: readonly Notice[];
  readonly unresolvedCases: readonly string[];
  /** The cases the open document holds, as `workspace.open` listed them, with their parents (XC-291). */
  readonly cases: readonly CaseSummary[];
  /** What this session loaded, by case (XC-292). The members below are the View area's subject:
   *  the case it shows and, where one is loaded for it, that dataset. */
  readonly loaded: Readonly<Record<string, LoadedSummary>>;
  readonly caseId: string | null;
  readonly datasetId: string | null;
  readonly sourceName: string | null;
  readonly supportLevel: string | null;
  readonly gaps: readonly string[];
  readonly fields: readonly FieldSummary[];
  /** The derived fields of this dataset, by name, with what they were made by (XC-282). */
  readonly derived: Readonly<Record<string, Derivation>>;
  readonly fieldName: string | null;
  readonly colourMap: string;
  readonly viewId: string | null;
  /** The view's own camera - what a report renders - as this session last wrote it. The live camera
   *  is the turntable and stays out of the document until `keepCamera` (XC-270). */
  readonly savedCamera: CameraDefinition | null;
  /** The view's camera paths as the document holds them (CT-004 3.3.0, XC-289): read back with the
   *  view and written with every refresh. */
  readonly cameraPaths: readonly CameraPathDefinition[];
  /** The last frame drawn from a path: which path, where on it, the pose the engine's rule gave and
   *  the rule - the engine's answer, kept so the panel shows what was drawn. Null while the picture
   *  is the turntable's. */
  readonly pathPreview: PathPreview | null;
  /** An object URL for the rendered frame, or null. Revoked when it is replaced. */
  readonly imageUrl: string | null;
  readonly reduced: string | null;
  /** Whether the loaded case is partial - the file named parts that are not there - and which
   *  (ingest/AC-027). Kept, not only warned: a mark that can be dismissed is a mark that was. */
  readonly partial: boolean;
  /** The view's `partVisibility` as the document holds it (CT-004): the named parts hidden, and
   *  nothing for a shown one. Read back with the view and written with every refresh, so a toggle
   *  survives the next redraw and a saved one survives the next session (XC-274). */
  readonly partVisibility: Readonly<Record<string, boolean>>;
  /** The row a person selected, in the outliner or by picking in the viewport (view/AC-055): a
   *  part's name, or a block's. Interface state, class 1 - nothing of it reaches the document. */
  readonly selectedPart: string | null;
  /** What `dataset.describe` and `dataset.parts` answered for the loaded dataset, kept whole: the
   *  information area reads them rather than a fixture (XC-273). */
  readonly described: Results["dataset.describe"] | null;
  readonly parts: Results["dataset.parts"]["parts"] | null;
  readonly probe: Reported | null;
  readonly probeLocation: string | null;
  /** Which step the probed or picked value is of, as the engine said it (view/AC-032). */
  readonly probePosition: StatedPosition | null;
  /** The step the view is at on the case's result axis, as the view definition holds it (CT-004
   *  `resultPosition.step`): class-2 state, and a document write when moved (XC-283). Which step
   *  each shown number is of comes back with the number; this is what the next request asks for. */
  readonly step: number;
  readonly statistics: Results["field.statistics"] | null;
  /** The selected part's statistics for the field on screen, asked by the part's name and answered
   *  with the scope stated (XC-280). Null where no present part is selected. */
  readonly partStatistics: Results["field.statistics"] | null;
  readonly bounds: readonly [number[], number[]] | null;
  readonly turntable: Turntable;
  /** What the engine last refused, in its own words. Shown rather than swallowed (XC-001). */
  readonly refusal: string | null;
  readonly busy: boolean;
}

/** The size the on-screen frame is drawn at. A pick is a pixel **of a frame of this size**, so the
 *  two must agree: asking for a pick against a size the picture was not drawn at reads the value of
 *  somewhere else (CT-003 2.3.0). */
export const FRAME = { width: 1280, height: 960 } as const;

/** Where the camera is, as the three numbers a drag moves. A camera is a **definition** (CT-004),
 *  not a measurement, so the interface may hold one - but the position it becomes is computed here
 *  from the model's own bounds, which the engine reported. */
export interface Turntable {
  azimuthDegrees: number;
  elevationDegrees: number;
  /** Distance from the focal point, as a multiple of the model's bounding diagonal. */
  distance: number;
}

const START: Turntable = { azimuthDegrees: 30, elevationDegrees: 20, distance: 2.2 };

function cameraFrom(turntable: Turntable, bounds: readonly [number[], number[]] | null): CameraDefinition | undefined {
  if (!bounds) return undefined;
  const at = (side: readonly number[], index: number) => side[index] ?? 0;
  const [low, high] = bounds;
  const centre = [0, 1, 2].map((i) => (at(low, i) + at(high, i)) / 2) as [number, number, number];
  const diagonal =
    Math.hypot(at(high, 0) - at(low, 0), at(high, 1) - at(low, 1), at(high, 2) - at(low, 2)) || 1;
  const azimuth = (turntable.azimuthDegrees * Math.PI) / 180;
  const elevation = (Math.max(-85, Math.min(85, turntable.elevationDegrees)) * Math.PI) / 180;
  const radius = diagonal * turntable.distance;
  return {
    position_m: [
      centre[0] + radius * Math.cos(elevation) * Math.sin(azimuth),
      centre[1] - radius * Math.cos(elevation) * Math.cos(azimuth),
      centre[2] + radius * Math.sin(elevation),
    ],
    focalPoint_m: centre,
    viewUp: [0, 0, 1],
    projection: "perspective",
  };
}

const REDUCTION_WORD: Record<GraphSpec["reduction"], string> = { max: "最大", min: "最小", mean: "平均" };

/** How many steps the described case has: the engine's count, or the length of its positions, or
 *  one. What `moveToStep` checks a request against before the definition is written. */
function stepCount(described: Results["dataset.describe"] | null): number {
  const axis = described?.resultAxis;
  return Math.max(1, axis?.count ?? axis?.positions?.length ?? 1);
}

const EMPTY: EngineState = {
  reachability: { kind: "unknown" },
  opened: null,
  inspection: null,
  savedViews: [],
  savedReports: [],
  savedGraphs: [],
  graphId: null,
  graphSpec: null,
  graphData: null,
  reportId: null,
  report: null,
  reportRevision: null,
  provenance: null,
  provenanceRefusal: null,
  exported: null,
  operations: null,
  journal: [],
  lost: null,
  savedAt: null,
  history: null,
  workspaceId: null,
  workspaceName: null,
  caseTags: [],
  readOnly: false,
  lock: null,
  warnings: [],
  notices: [],
  unresolvedCases: [],
  cases: [],
  loaded: {},
  caseId: null,
  datasetId: null,
  sourceName: null,
  supportLevel: null,
  gaps: [],
  fields: [],
  derived: {},
  fieldName: null,
  colourMap: "viridis",
  viewId: null,
  savedCamera: null,
  cameraPaths: [],
  pathPreview: null,
  imageUrl: null,
  reduced: null,
  partial: false,
  partVisibility: {},
  selectedPart: null,
  described: null,
  parts: null,
  probe: null,
  probeLocation: null,
  probePosition: null,
  step: 0,
  statistics: null,
  partStatistics: null,
  bounds: null,
  turntable: { ...START },
  refusal: null,
  busy: false,
};

/** The viewport well, as `--g-well` in tokens.css: #0a0c0d. Written as channels because
 *  that is what the renderer takes, and kept beside the definition that uses it. */
const SCREEN_GROUND: readonly [number, number, number] = [0.039, 0.047, 0.051];

let state: EngineState = EMPTY;
let engine: Engine | null = null;
/** Which document the store is on. Bumped by an open, a disconnect and an exit, so that an answer
 *  still in flight from the previous document - a redraw a subject move started, say - is dropped
 *  rather than written over the one now open (16_application_model §6, class 3). */
let generation = 0;
let noticeCount = 0;

/** Keep what a person is about to be shown, so it can be found again after looking away (§12). */
function notice(severity: Notice["severity"], title: string, detail: string, operation?: string) {
  noticeCount += 1;
  const one: Notice = { id: `notice:${noticeCount}`, at: recordNow(), severity, title, detail, ...(operation ? { operation } : {}) };
  setState({ notices: [...state.notices, one].slice(-200) });
}
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function setState(patch: Partial<EngineState>) {
  state = { ...state, ...patch };
  emit();
}

/** Replace the frame, releasing the previous one. An object URL that is never revoked is a copy of
 *  the image kept alive for the life of the page, and a session of camera moves is a hundred of them. */
function setImage(url: string | null, reduced: string | null) {
  if (state.imageUrl && state.imageUrl !== url) URL.revokeObjectURL(state.imageUrl);
  setState({ imageUrl: url, reduced });
}

/** What was loaded, case by case, in the form the logic layer takes. */
function loadedList(): { caseId: string; datasetId: string }[] {
  return Object.values(state.loaded).map((one) => ({ caseId: one.caseId, datasetId: one.datasetId }));
}

/** Keep the View area's subject under its case, so another case can be shown and this one found
 *  again without a second read (XC-292). Called after every change to what the case holds. */
function remember(filePath?: string) {
  if (!state.caseId || !state.datasetId) return;
  const path = filePath ?? state.loaded[state.caseId]?.filePath;
  if (!path) return;
  setState({
    loaded: {
      ...state.loaded,
      [state.caseId]: {
        caseId: state.caseId,
        datasetId: state.datasetId,
        filePath: path,
        sourceName: state.sourceName ?? fileName(path),
        supportLevel: state.supportLevel,
        gaps: state.gaps,
        fields: state.fields,
        derived: state.derived,
        described: state.described,
        parts: state.parts,
        partial: state.partial,
        bounds: state.bounds,
        fieldName: state.fieldName,
      },
    },
  });
}

let showSequence = 0;

/** The View area moves to `caseId` (XC-292): the dataset this session loaded for it, with its own
 *  view found or made, or - where nothing is loaded for it - an area that says so, and never
 *  another case's picture under this case's name. A later move wins over one still in flight. */
/** What a drop is planned from (XC-301): every file the document records for a case, as the open
 *  answer gave it, and every file this session read into a case - path for path. */
function caseRecords(): CaseRecord[] {
  const records: CaseRecord[] = [];
  for (const one of state.cases) for (const source of one.sources ?? []) records.push({ caseId: one.id, path: source.path });
  for (const load of state.opened?.loads ?? []) records.push({ caseId: load.caseId, path: load.filePath });
  return records;
}

function describeCase(caseId: string): string {
  const found = state.cases.find((one) => one.id === caseId);
  return found ? `${found.name}（${found.id}）` : caseId;
}

async function showCase(caseId: string | null): Promise<void> {
  const mine = ++showSequence;
  const summary = caseId ? state.loaded[caseId] : undefined;
  setImage(null, null);
  setState({
    caseId,
    datasetId: summary?.datasetId ?? null,
    sourceName: summary?.sourceName ?? null,
    supportLevel: summary?.supportLevel ?? null,
    gaps: summary?.gaps ?? [],
    fields: summary?.fields ?? [],
    derived: summary?.derived ?? {},
    fieldName: summary?.fieldName ?? summary?.fields[0]?.name ?? null,
    viewId: null,
    savedCamera: null,
    cameraPaths: [],
    pathPreview: null,
    partial: summary?.partial ?? false,
    partVisibility: {},
    selectedPart: null,
    described: summary?.described ?? null,
    parts: summary?.parts ?? null,
    probe: null,
    probeLocation: null,
    probePosition: null,
    step: 0,
    statistics: null,
    partStatistics: null,
    bounds: summary?.bounds ?? null,
    turntable: { ...START },
    refusal: null,
  });
  if (!summary || mine !== showSequence) return;
  await engineState.refresh();
}

/** Read again every file the document had read into a case, in that order, ending on the case the
 *  View area shows - the selection the window kept across the restart (XC-292). */
async function reloadAll(loads: Opened["loads"]): Promise<boolean> {
  const shown = engineState.subjectOf("view").caseId;
  const ordered = [...loads.filter((one) => one.caseId !== shown), ...loads.filter((one) => one.caseId === shown)];
  for (const one of ordered) {
    if (!(await engineState.loadDataset(one.caseId, one.filePath))) return false;
  }
  if (shown !== state.caseId) await showCase(shown);
  else await engineState.refresh();
  return true;
}

/** The case the last graph answer was asked for, so a subject move asks again only when it moved. */
let graphContext: string | null = null;
/** What the last subject change set in motion, for a caller that must see it finished. */
let moving: Promise<unknown> = Promise.resolve();

/** Ask the engine, and put a refusal where a person can read it rather than throwing it away.
 *
 * Returns the result on an answer and null on a refusal or a transport failure - the caller decides
 * what to do about nothing, and `state.refusal` says what happened either way.
 */
async function ask<O extends Operation>(
  operation: O,
  parameters: Parameters[O],
  options: Options = {},
): Promise<Results[O] | null> {
  if (!engine) {
    setState({ refusal: "エンジンに接続していません" });
    return null;
  }
  // **The refusal is not cleared here.** It was, and that made a failure in the middle of a
  // sequence invisible: the picture failed to arrive, the next call cleared the reason, and the
  // screen showed neither an image nor why. A refusal is cleared when a person dismisses it or when
  // a new thing is asked for - not by the next step of the thing that already failed.
  const asked = generation;
  setState({ busy: true });
  let answer: Response<O>;
  try {
    answer = await engine.submit(operation, parameters, options);
  } catch (failure) {
    if (asked !== generation) {
      setState({ busy: false });
      return null;
    }
    const because = failure instanceof TransportFailure ? failure.message : String(failure);
    setState({ busy: false, refusal: because, reachability: { kind: "absent", because } });
    notice("error", `'${operation}' に答えがありません`, because, operation);
    return null;
  }
  setState({ busy: false });
  // Answered for a document that is no longer the one open: neither its refusal nor its warnings
  // nor its write belong to this one.
  if (asked !== generation) return null;
  if (answer.status === "refused" || answer.status === "failed") {
    const reason = reasonText(answer.reason) || `'${operation}' は行えませんでした`;
    setState({ refusal: reason });
    notice(answer.status === "failed" ? "error" : "refusal", `'${operation}' は${answer.status === "failed" ? "失敗しました" : "拒まれました"}`, reason, operation);
    return null;
  }
  // What the engine had to say beside its answer is shown, not dropped: a document lifted to a
  // new version, a dataset closed by an open, a lock somebody else holds (XC-001).
  if (answer.warnings && answer.warnings.length > 0) {
    // Kept beside earlier ones until dismissed, not replaced by the next answer's: an open that found
    // a lock held is followed at once by a load and a render, and the lock is still held.
    const fresh = answer.warnings.filter((one) => !state.warnings.includes(one));
    setState({ warnings: [...state.warnings, ...fresh].slice(-20) });
    for (const one of fresh) notice("warning", `'${operation}' の注意`, one, operation);
  }
  if (answer.status === "applied" && !NOT_UNSAVED_WORK.has(operation)) {
    setState({
      journal: [
        ...state.journal,
        { operation, summary: answer.effectSummary ?? operation, at: recordNow() },
      ],
    });
  }
  return (answer.result ?? null) as Results[O] | null;
}

/** The name the session's report has in the document: the dataset's, so that a person finds it by
 *  the file it reports on, and so the same report is found again next session (AC-030). */
function reportName(): string {
  return state.sourceName ?? "レポート";
}

/** Applied writes that are not unsaved work: opening and saving reset the journal, and loading a
 *  file is recoverable from the path this store remembers rather than lost. Everything else the
 *  engine applies - a declaration, a view, a report - lives in the document until saved. */
// `output.prune` changes the disk and not the document: nothing of it is waiting to be saved.
const NOT_UNSAVED_WORK = new Set<string>(["workspace.open", "workspace.save", "dataset.load", "output.prune"]);

export const engineState = {
  /** Point the interface at an engine. Called once by the shell with what the connection file said. */
  async connect(connection: Connection): Promise<Reachability> {
    engine = new Engine(connection);
    try {
      const health = await engine.health();
      const reachability: Reachability = { kind: "reachable", protocols: health.protocols };
      setState({ reachability, refusal: null });
      return reachability;
    } catch (failure) {
      const because = failure instanceof TransportFailure ? failure.message : String(failure);
      engine = null;
      const reachability: Reachability = { kind: "absent", because };
      setState({ reachability });
      return reachability;
    }
  },

  /** The shell says the engine process ended. The picture, the numbers and the probe stay as they
   *  were - they are what the engine last answered - and every further ask is refused here rather
   *  than sent to a port nothing answers on. */
  engineExited(status: { reason: string | null; exitCode: number | null; signal: string | null }) {
    engine = null;
    generation += 1;
    setState({
      reachability: {
        kind: "exited",
        because: status.reason ?? "エンジンが終了しました",
        exitCode: status.exitCode,
        signal: status.signal,
      },
      busy: false,
      // What was applied and never saved is what is gone. It is said, not rebuilt (XC-259).
      lost: state.journal.length > 0 ? state.journal : state.lost,
      journal: [],
    });
  },

  /** After a restart: connect, and open again what was saved - the document from disk and the
   *  file from its path. The unsaved writes stay in `lost`, on screen, until dismissed; nothing
   *  here re-applies them. */
  async recover(connection: Connection): Promise<Reachability> {
    const opened = state.opened;
    const reachability = await engineState.connect(connection);
    if (reachability.kind !== "reachable" || !opened) return reachability;
    const lost = state.lost;
    if (!(await engineState.openWorkspace(opened.workspacePath, { keepSubjects: true }))) return reachability;
    if (!(await reloadAll(opened.loads))) return reachability;
    setState({ lost });
    return reachability;
  },

  dismissLost() {
    setState({ lost: null });
  },

  clearWarnings() {
    setState({ warnings: [] });
  },

  /** Take over a stale or unreadable lock on a person's word (XC-241, XC-269): the document is
   *  reopened with the take-over asked for, then the case and the file are read again, as recovery
   *  does. A live holder's lock is never taken over; the engine says so and this returns false. */
  async takeOverLock(): Promise<boolean> {
    const opened = state.opened;
    if (!opened) return false;
    if (!(await engineState.openWorkspace(opened.workspacePath, { takeOverStaleLock: true, keepSubjects: true }))) return false;
    if (!(await reloadAll(opened.loads))) return false;
    return !state.readOnly;
  },

  /** Class 3: write the document back. The journal empties because the document on disk now holds
   *  what it held; the previous version is kept beside it by the engine (XC-055). */
  async save(): Promise<boolean> {
    if (!state.workspaceId) return false;
    setState({ refusal: null });
    const saved = await ask("workspace.save", { workspaceId: state.workspaceId });
    if (!saved) return false;
    setState({ journal: [], savedAt: recordNow() });
    return true;
  },

  /** No engine: the screens stay the catalogue of design states they are, and say so. */
  disconnect() {
    engine = null;
    generation += 1;
    setImage(null, null);
    state = { ...EMPTY, reachability: { kind: "absent", because: "接続していません" } };
    emit();
  },

  isConnected(): boolean {
    return engine !== null && state.reachability.kind === "reachable";
  },

  /** Class 3: open a workspace. Everything loaded from the previous one goes with it. The lock is
   *  taken for this session, or found held and the document opened read-only (XC-269); a stale or
   *  unreadable lock is taken over only when the caller says so - a person's word, never a default. */
  async openWorkspace(path: string, options: { takeOverStaleLock?: boolean; keepSubjects?: boolean } = {}): Promise<boolean> {
    setState({ refusal: null, warnings: [] });
    const opened = await ask("workspace.open", options.takeOverStaleLock ? { path, takeOverStaleLock: true } : { path });
    if (!opened) return false;
    // From here every earlier question was of the previous document.
    generation += 1;
    showSequence += 1;
    setImage(null, null);
    setState({
      opened: { workspacePath: path, loads: [] },
      savedViews: (opened.items?.views ?? []) as readonly SavedView[],
      savedReports: (opened.items?.reports ?? []) as readonly SavedView[],
      savedGraphs: (opened.items?.graphs ?? []) as readonly SavedView[],
      graphId: null,
      graphSpec: null,
      graphData: null,
      reportId: null,
      report: null,
      reportRevision: null,
      provenance: null,
      provenanceRefusal: null,
      exported: null,
      journal: [],
      savedAt: null,
      workspaceId: opened.workspaceId,
      workspaceName: opened.name ?? null,
      caseTags: opened.tags ?? [],
      readOnly: opened.readOnly ?? false,
      lock: opened.lock ?? null,
      unresolvedCases: opened.unresolvedCases ?? [],
      cases: (opened.cases ?? []).map((one) => ({
        id: one.id,
        name: one.name,
        ...(one.parentId ? { parentId: one.parentId } : {}),
        // The files the document records for the case, kept as answered: what a drop is planned
        // from, path for path (XC-298, XC-301). Absent where the document records none.
        ...(one.sources && one.sources.length > 0 ? { sources: one.sources.map((source) => ({ name: source.name, path: source.path, present: source.present })) } : {}),
      })),
      loaded: {},
      caseId: null,
      datasetId: null,
      sourceName: null,
      fields: [],
      derived: {},
      fieldName: null,
      viewId: null,
      cameraPaths: [],
      pathPreview: null,
      partial: false,
      partVisibility: {},
      selectedPart: null,
      described: null,
      parts: null,
      probe: null,
      probeLocation: null,
      probePosition: null,
      step: 0,
      statistics: null,
      partStatistics: null,
    });
    // The document's first case is the subject until a person chooses another; a document reopened
    // after a restart keeps the selection and the pins the window still holds (XC-292).
    if (!options.keepSubjects) {
      session.resetSubjects();
      session.selectCase(state.cases[0]?.id ?? null);
    }
    // The shell's list of what was opened, for the Workspace list to offer again (XC-297): as the
    // engine described the document, and only after the engine accepted the open.
    const shell = shellApi();
    if (shell && !options.keepSubjects) {
      void shell.recent.remember({ path, name: opened.name ?? fileName(path), tags: opened.tags ?? [], openedAt: recordNow() });
    }
    return true;
  },

  /** Class 3: the shipped sample, generated by the engine where the person chose and opened, with
   *  its first case's file loaded so the first thing seen is a picture (XC-129, XC-298). The
   *  engine writes the beam and declares its units as the sample's author; the store only loads what
   *  the answer says is there. */
  async openSample(path: string): Promise<boolean> {
    setState({ refusal: null, warnings: [] });
    const made = await ask("workspace.sample", { path });
    if (!made) return false;
    if (!(await engineState.openWorkspace(path))) return false;
    const first = made.cases[0];
    const source = first?.sources?.find((one) => one.present);
    if (first && source && (await engineState.loadDataset(first.id, source.path))) await engineState.refresh();
    return state.refusal === null;
  },

  /** Class 3: a new document at a path the person chose, with one case, then opened - the engine
   *  writes it and answers as it does for any open (`workspace.create`, XC-297). */
  async createWorkspace(path: string, name: string, caseName?: string): Promise<boolean> {
    setState({ refusal: null, warnings: [] });
    const created = await ask("workspace.create", { path, name, ...(caseName ? { caseName } : {}) });
    if (!created) return false;
    // The document now exists and is open in the engine; the store takes it as it takes any open,
    // by opening it again rather than by copying the answer into a second set of fields.
    return engineState.openWorkspace(path);
  },

  /** Before reading a file: the support level this build promises for its format, and what the
   *  reader is known not to read (ingest/REQ-015, XC-049). Nothing is opened; nothing is loaded. */
  async inspect(path: string): Promise<Inspection | null> {
    setState({ refusal: null });
    const inspected = await ask("dataset.inspect", { path });
    if (!inspected) {
      setState({ inspection: null });
      return null;
    }
    const inspection: Inspection = { ...inspected, path };
    setState({ inspection });
    return inspection;
  },

  cancelInspection() {
    setState({ inspection: null });
  },

  /** Class 3: read a result file into a case. The fields arrive with no unit, as the file had none. */
  async loadDataset(caseId: string, filePath: string): Promise<boolean> {
    setState({ refusal: null });
    const loaded = await ask("dataset.load", { caseId, filePaths: [filePath] });
    if (!loaded) return false;
    const fields = (loaded.fields ?? []) as readonly FieldSummary[];
    // The graph of this session is over the Graph area's case: a load into that case makes its
    // numbers those of a file no longer on screen, and it is let go; a load into another case
    // leaves it, pinned or following (XC-292).
    const graphOfThisCase = engineState.subjectOf("graph").caseId === caseId;
    setImage(null, null);
    setState({
      opened: state.opened
        ? { ...state.opened, loads: [...state.opened.loads.filter((one) => one.caseId !== caseId), { caseId, filePath }] }
        : null,
      inspection: null,
      caseId,
      datasetId: loaded.datasetId,
      sourceName: filePath.split(/[\\/]/).pop() ?? filePath,
      supportLevel: loaded.supportLevel,
      gaps: loaded.gaps ?? [],
      fields,
      derived: {},
      fieldName: fields[0]?.name ?? null,
      viewId: null,
      savedCamera: null,
      cameraPaths: [],
      pathPreview: null,
      ...(graphOfThisCase ? { graphId: null, graphSpec: null, graphData: null } : {}),
      partial: false,
      partVisibility: {},
      selectedPart: null,
      described: null,
      // The trust content is of what is loaded: read again for the new dataset (XC-275).
      provenance: null,
      provenanceRefusal: null,
      parts: null,
      probe: null,
      probeLocation: null,
      probePosition: null,
      step: 0,
      statistics: null,
      partStatistics: null,
      turntable: { ...START },
    });
    const described = await ask("dataset.describe", { datasetId: loaded.datasetId });
    setState({
      bounds: described?.boundsM ? [described.boundsM.minM as number[], described.boundsM.maxM as number[]] : null,
      partial: described?.partial ?? false,
      described,
    });
    // The parts, present and absent, with the file's own hierarchy, as the engine lists them: what
    // the outliner and the information area show, and where a partial case's missing parts are
    // named (AC-027, XC-273, XC-274). Kept as answered; the sentences are the logic layer's.
    const parts = await ask("dataset.parts", { datasetId: loaded.datasetId });
    setState({ parts: parts?.parts ?? null });
    remember(filePath);
    // The View area shows what was just read - the tree's selection moves to its case - unless the
    // area is pinned elsewhere, in which case the pinned case comes back on screen and the new
    // dataset waits under its own case (XC-292).
    const subject = engineState.subjectOf("view");
    if (subject.source === "pinned" && subject.caseId !== caseId) await showCase(subject.caseId);
    else if (subject.caseId !== caseId) session.selectCase(caseId);
    return true;
  },

  /** Class 1: turn the model. The camera is a definition the view carries, so moving it is an
   *  update to that definition and a redraw - not a thing the interface does to a picture. */
  /** Class 1: a new look at the same view. The picture is drawn again from the new camera; nothing
   *  is written, so nothing enters the undo history or the unsaved work (XC-270). */
  async orbit(byAzimuth: number, byElevation: number): Promise<void> {
    setState({
      pathPreview: null,
      turntable: {
        ...state.turntable,
        azimuthDegrees: state.turntable.azimuthDegrees + byAzimuth,
        elevationDegrees: state.turntable.elevationDegrees + byElevation,
      },
    });
    await engineState.draw();
  },

  /** A keyframe of the one path from the live look, at parameter `at` (XC-289). A document write:
   *  the definition is written with the next refresh, and the engine reads the path back from it. */
  async addPathKeyframe(at: number): Promise<boolean> {
    const camera = cameraFrom(state.turntable, state.bounds);
    if (!camera || !state.viewId) {
      setState({ refusal: "絵がまだありません：向きを取るには、先に描かれたビューが要ります" });
      return false;
    }
    const added = withKeyframe(state.cameraPaths[0] ?? null, at, camera);
    if ("refused" in added) {
      setState({ refusal: added.refused });
      return false;
    }
    setState({ cameraPaths: [added.path, ...state.cameraPaths.slice(1)], refusal: null });
    await engineState.refresh();
    return state.refusal === null;
  },

  async removePathKeyframe(at: number): Promise<void> {
    const path = state.cameraPaths[0];
    if (!path) return;
    setState({ cameraPaths: [withoutKeyframe(path, at), ...state.cameraPaths.slice(1)], pathPreview: null });
    await engineState.refresh();
  },

  async setPathInterpolation(interpolation: Interpolation): Promise<void> {
    const path = state.cameraPaths[0];
    if (!path) return;
    setState({ cameraPaths: [{ ...path, interpolation }, ...state.cameraPaths.slice(1)] });
    await engineState.refresh();
    if (state.pathPreview) await engineState.previewPath(state.pathPreview.at);
  },

  /** The frame from parameter `at` on the path, as the engine interpolates it; the answer's pose
   *  and rule are kept beside the picture. The turntable is untouched: this is a look, not a move. */
  async previewPath(at: number): Promise<boolean> {
    const path = state.cameraPaths[0];
    if (!path || !state.viewId) return false;
    setState({ refusal: null, pathPreview: { id: path.id, at, interpolation: path.interpolation, rule: "", camera: {} } });
    await engineState.draw();
    return state.pathPreview !== null && state.pathPreview.rule !== "";
  },

  async clearPathPreview(): Promise<void> {
    setState({ pathPreview: null });
    await engineState.draw();
  },

  /** Class 3, explicit: make the current look the view's own camera - what a report renders. One
   *  `view.update`, one undo step, one unsaved write (XC-270). */
  async keepCamera(): Promise<boolean> {
    const camera = cameraFrom(state.turntable, state.bounds);
    if (!camera || !state.viewId) return false;
    setState({ savedCamera: camera });
    await engineState.refresh();
    return true;
  },

  /** The value under one pixel of the frame on screen (CT-003 2.3.0). */
  async pick(x: number, y: number): Promise<void> {
    if (!state.viewId) return;
    setState({ refusal: null });
    const answer = await ask("view.pick", {
      viewId: state.viewId,
      width: FRAME.width,
      height: FRAME.height,
      x: Math.round(x),
      y: Math.round(y),
      // The camera the frame on screen was drawn with, or the pixel is read off another picture -
      // the path's pose while a path frame is on screen (XC-289).
      ...(state.pathPreview
        ? { cameraPath: { id: state.pathPreview.id, at: state.pathPreview.at } }
        : { camera: cameraFrom(state.turntable, state.bounds) }),
    });
    setState({
      probe: answer?.value ?? null,
      probeLocation: (answer?.value as { location?: string } | undefined)?.location ?? null,
      probePosition: answer?.resultPosition ?? null,
      // The part under the pixel is the selection now, so the outliner follows the viewport
      // (view/AC-055). A pixel on nothing changes no selection: nothing was chosen there.
      selectedPart: answer?.part ?? state.selectedPart,
    });
    await engineState.refreshPartStatistics();
  },

  /** Class 1: choose a row - a part or a block - in the outliner or by picking. Nothing is written;
   *  the part's statistics are read, because the Object section shows them (XC-280). */
  async selectPart(name: string | null): Promise<void> {
    setState({ selectedPart: name });
    await engineState.refreshPartStatistics();
  },

  /** The selected part's numbers for the field on screen, by the part's name (XC-280). A read; the
   *  answer carries the scope, and a row that is no present part has none. */
  async refreshPartStatistics(): Promise<void> {
    const part = state.parts?.find((one) => one.name === state.selectedPart && one.type !== "absent");
    if (!part || !state.datasetId || !state.fieldName) {
      setState({ partStatistics: null });
      return;
    }
    const before = state.refusal;
    const answered = await ask("field.statistics", {
      datasetId: state.datasetId,
      fieldName: state.fieldName,
      region: part.name,
      resultPosition: state.step,
    });
    // A refusal here is the section's to show beside the part, not the window's.
    if (!answered) setState({ refusal: before });
    setState({ partStatistics: answered });
  },

  /** Class 2, and a document write: which parts the view shows (CT-004 `partVisibility`, INV-019).
   *  The map is the definition's, written whole with the next refresh, so the engine draws and
   *  picks what the outliner says - and refuses, by name, a map that hides everything (XC-274). */
  async setPartVisibility(next: Readonly<Record<string, boolean>>): Promise<void> {
    setState({ partVisibility: { ...next } });
    await engineState.refresh();
  },

  /** Class 2: a unit is a declaration with an author. Declaring it changes labels and conversions
   *  and touches no stored number (XC-003, XC-134). */
  async declareUnit(fieldName: string, unitSymbol: string): Promise<boolean> {
    if (!state.datasetId) return false;
    // Cleared first: the answer carries no value, so a refusal is told from an answer by what this
    // ask left - and a refusal an earlier action left on screen would read as this one's.
    setState({ refusal: null });
    const done = await ask("field.declareUnit", { datasetId: state.datasetId, fieldName, unitSymbol });
    if (done === null && state.refusal) return false;
    setState({
      fields: state.fields.map((one) => (one.name === fieldName ? { ...one, unit: unitSymbol } : one)),
    });
    remember();
    // The legend and every reported number carry the unit now, so both are asked for again rather
    // than edited here: this layer never computes, and a relabelled copy would be a second answer.
    await engineState.refresh();
    return true;
  },

  /** A catalogue quantity of a field, made by the engine from canonical data and listed beside the
   *  file's own fields with its formula and conventions (INV-020, XC-282). The derived field is
   *  chosen, so the picture and the numbers move to it. A read: nothing enters the document. */
  async derive(fieldName: string, quantity: string, component?: string): Promise<boolean> {
    if (!state.datasetId) return false;
    setState({ refusal: null });
    const made = await ask("field.derive", {
      datasetId: state.datasetId,
      fieldName,
      quantity,
      ...(component ? { component } : {}),
    });
    if (!made) return false;
    const names = made.fieldNames ?? [made.fieldName];
    const association = made.association as FieldSummary["association"];
    const fresh = names
      .filter((name) => !state.fields.some((one) => one.name === name))
      .map((name) => ({ name, association, unit: made.unit ?? null, components: 1 }));
    setState({
      fields: [...state.fields, ...fresh],
      derived: {
        ...state.derived,
        ...Object.fromEntries(
          names.map((name) => [name, { source: fieldName, quantity, formula: made.formula, conventions: made.conventions }]),
        ),
      },
    });
    remember();
    await engineState.chooseField(made.fieldName);
    return true;
  },

  /** Class 2: choose which field the colours mean. */
  async chooseField(fieldName: string): Promise<void> {
    setState({ fieldName, probe: null, probeLocation: null, probePosition: null });
    remember();
    await engineState.refresh();
  },

  async chooseColourMap(colourMap: string): Promise<void> {
    setState({ colourMap });
    await engineState.refresh();
  },

  /** Draw the current field, and read its statistics. One answer feeds the picture and the other
   *  feeds the table; they are separate operations because they are separate computations. */
  async refresh(): Promise<void> {
    if (!state.datasetId || !state.fieldName || !engine) return;
    setState({ refusal: null });
    const association = state.fields.find((one) => one.name === state.fieldName)?.association;
    if (association !== "point" && association !== "cell") {
      setState({ refusal: `'${state.fieldName}' は点でも要素でもない場です。この版は色付けしません` });
      return;
    }
    const dataset = state.datasetId;
    let viewId = state.viewId;
    // The view this case works on: the document's, under the field's name or - where another loaded
    // case already holds that name - under the field's name with this case (XC-292).
    const working = workingView(state.fieldName, state.caseId ?? "", state.savedViews, loadedList());
    if (!viewId) {
      // The document may already hold this view - saved in an earlier session - and a second one
      // under the same name is refused (AC-030). Updating it is what a person means by "the view",
      // and what it holds is read before it is written: the camera a person kept and the parts
      // they hid are the document's, not this window's to rebuild. Until 2026-09-20 the first
      // redraw of a session overwrote both with what the window had, which was nothing (XC-274).
      const saved = working.existing;
      if (saved) {
        viewId = saved.id;
        const held = await ask("view.get", { viewId });
        // The subject moved while the document answered: what it holds is another case's now.
        if (state.datasetId !== dataset) return;
        const kept = (held?.definition ?? {}) as {
          camera?: CameraDefinition;
          partVisibility?: Record<string, boolean>;
          colouring?: { colourMap?: string };
          resultPosition?: { step?: number };
          cameraPaths?: CameraPathDefinition[];
        };
        setState({
          viewId,
          savedCamera: kept.camera ?? null,
          partVisibility: kept.partVisibility ?? {},
          colourMap: kept.colouring?.colourMap ?? state.colourMap,
          // The step the document kept the view at (CT-004), read before it is written (XC-283).
          step: kept.resultPosition?.step ?? 0,
          cameraPaths: kept.cameraPaths ?? [],
        });
      }
    }
    const definition = {
      id: viewId ?? "view:pending",
      datasetId: state.datasetId,
      representation: "surface",
      name: working.name,
      colouring: { fieldName: state.fieldName, association, colourMap: state.colourMap },
      // Which parts the picture shows, as the outliner last set it (CT-004, XC-274).
      partVisibility: { ...state.partVisibility },
      // The step the view is at, by its ordinal along the sequence the file declared - the one
      // member an axis of undeclared kind can take (CT-004 3.2.0, XC-240, XC-283).
      resultPosition: { step: state.step },
      // The view's camera paths, as this window last edited them (CT-004 3.3.0, XC-289).
      cameraPaths: state.cameraPaths.map((one) => ({ ...one, keyframes: [...one.keyframes] })),
      // The view's own camera, not the live one: the definition is what a report renders, and the
      // turntable stays out of it until the person keeps a look (XC-270). The first definition
      // takes the pose the model is first seen from, so a report of an unkept view is not blank.
      camera: state.savedCamera ?? cameraFrom(state.turntable, state.bounds),
      // The screen's ground, not the document's. The viewport well is the darkest surface the
      // interface has (XC-256) and a white picture inside it fights the chrome it sits in; a
      // report asks for its own ground, and the view is what says which (CT-004).
      background: { rgb: SCREEN_GROUND },
    };
    if (viewId) {
      await ask("view.update", { viewId, definition });
      if (state.datasetId !== dataset) return;
    } else {
      const created = await ask("view.create", {
        workspaceId: state.workspaceId ?? "",
        definition,
      });
      if (state.datasetId !== dataset) return;
      viewId = created?.id ?? null;
      // The view the document now holds, remembered beside the ones it held at open: a dataset
      // loaded again would otherwise create a second view under this name, which the document
      // refuses (AC-030) - the case that surfaced when a partial file was loaded and the cube put back.
      setState({
        viewId,
        savedViews:
          viewId && state.fieldName && state.datasetId
            ? [...state.savedViews, { id: viewId, name: working.name, datasetId: state.datasetId }]
            : state.savedViews,
      });
    }
    if (!viewId) return;
    if (!state.savedCamera && definition.camera) setState({ savedCamera: definition.camera });
    await engineState.draw();
    if (state.datasetId !== dataset) return;
    const statistics = await ask("field.statistics", {
      datasetId: state.datasetId,
      fieldName: state.fieldName,
      resultPosition: state.step,
    });
    if (state.datasetId !== dataset) return;
    setState({ statistics });
    await engineState.refreshPartStatistics();
  },

  /** Class 2: move along the result axis (16_application_model §6). The step is the view
   *  definition's (CT-004 `resultPosition.step`), so the picture, the numbers and the probe are all
   *  of it, and every answer says which step it is of (view/AC-032). A step the case does not have
   *  is refused before the definition is written - by the count the engine described - and nothing
   *  nearer is shown instead (view/AC-033, XC-283). */
  async moveToStep(step: number): Promise<boolean> {
    const count = stepCount(state.described);
    if (!Number.isInteger(step) || step < 0 || step >= count) {
      setState({
        refusal: `ステップ番号 ${step}（0 始まり）はこの結果にありません（あるのは 0〜${count - 1} の ${count} ステップ）。最も近いステップで代用はしません（view/AC-033）`,
      });
      return false;
    }
    setState({ step, probe: null, probeLocation: null, probePosition: null });
    await engineState.refresh();
    return state.refusal === null;
  },

  /** Draw the view from the live camera. The picture, not the document: the camera goes as a
   *  parameter of `view.render` and the definition is not touched (XC-270). */
  async draw(): Promise<void> {
    const viewId = state.viewId;
    if (!viewId || !engine) return;
    // No bar inside the picture: the rail's legend carries the range with its unit, which the
    // bar cannot (E-192), and two scales for one image is one too many. A document asks for it.
    const preview = state.pathPreview;
    const rendered = await ask("view.render", {
      viewId,
      ...FRAME,
      format: "png",
      legend: false,
      // From a position on a path while one is previewed (XC-289), else from the live look.
      ...(preview ? { cameraPath: { id: preview.id, at: preview.at } } : { camera: cameraFrom(state.turntable, state.bounds) }),
    });
    // The picture is of the view it was asked for; a subject that moved meanwhile has its own.
    if (state.viewId !== viewId) return;
    if (rendered?.cameraPath) setState({ pathPreview: rendered.cameraPath });
    else if (preview && !rendered) setState({ pathPreview: null });
    if (rendered?.handle) {
      try {
        const blob = await engine.handle(rendered.handle);
        setImage(URL.createObjectURL(blob), rendered.reduced ?? null);
      } catch (failure) {
        setState({ refusal: failure instanceof TransportFailure ? failure.message : String(failure) });
      }
    }
  },

  /** Read the value at a point, in the source's own words. */
  async probe(pointM: readonly [number, number, number]): Promise<void> {
    if (!state.datasetId || !state.fieldName) return;
    setState({ refusal: null });
    const answer = await ask("dataset.probe", {
      datasetId: state.datasetId,
      fieldName: state.fieldName,
      pointM: [...pointM],
      resultPosition: state.step,
    });
    setState({
      probe: answer?.value ?? null,
      probeLocation: (answer?.value as { location?: string } | undefined)?.location ?? null,
      probePosition: answer?.resultPosition ?? null,
    });
  },

  /** The report this session works on: the document's report under this dataset's name, adopted
   *  where the document holds one (AC-030) and made where it does not - with the picture where one
   *  is drawn and the values of the field on screen. Made once: until 2026-09-20 every export made
   *  a report, and the second was refused as a name the document already held. */
  async ensureReport(): Promise<string | null> {
    if (state.reportId) return state.reportId;
    if (!state.workspaceId) return null;
    const name = reportName();
    const saved = state.savedReports.find((one) => one.name === name);
    if (saved) {
      setState({ reportId: saved.id });
      await engineState.refreshReport();
      return saved.id;
    }
    const blocks: ReportBlock[] = [];
    if (state.viewId) blocks.push({ kind: "view", viewId: state.viewId, form: "still" });
    if (state.fieldName) blocks.push({ kind: "valueTable", fields: [state.fieldName] });
    const created = await ask("report.create", {
      workspaceId: state.workspaceId,
      definition: { id: "report:pending", name, targets: ["html"], blocks },
    });
    if (!created) return null;
    setState({ reportId: created.id, savedReports: [...state.savedReports, { id: created.id, name }] });
    await engineState.refreshReport();
    return created.id;
  },

  /** What the document holds for the report, and its trust content, read rather than remembered
   *  (XC-275). A refusal of the trust content is kept beside it - it is the item that blocks the
   *  export, and the area shows it there - and is not raised as this window's refusal. */
  async refreshReport(): Promise<void> {
    let reportId = state.reportId;
    if (!reportId) {
      const saved = state.savedReports.find((one) => one.name === reportName());
      if (!saved) return;
      reportId = saved.id;
      setState({ reportId });
    }
    const held = await ask("report.get", { reportId });
    if (held) setState({ report: held.definition as unknown as ReportDefinition, reportRevision: held.revision });
    const before = state.refusal;
    const provenance = await ask("report.provenance", { reportId });
    if (provenance) setState({ provenance, provenanceRefusal: null });
    else setState({ provenance: null, provenanceRefusal: state.refusal, refusal: before });
  },

  /** Class 2, and a document write: the report's definition, whole (CT-006), then read back. */
  async updateReport(definition: ReportDefinition): Promise<boolean> {
    if (!state.reportId) return false;
    setState({ refusal: null });
    const done = await ask("report.update", {
      reportId: state.reportId,
      definition: definition as unknown as Record<string, unknown>,
    });
    if (!done) return false;
    await engineState.refreshReport();
    return true;
  },

  /** Write the deliverable: what the document's report says, with its trust content. */
  async exportReport(path: string): Promise<Results["report.export"] | null> {
    const reportId = await engineState.ensureReport();
    if (!reportId) return null;
    setState({ refusal: null });
    const done = await ask("report.export", { reportId, path });
    setState({ exported: done });
    return done;
  },

  /** What this build can do and where it keeps its log (system.capabilities). A read. */
  async capabilities(): Promise<Results["system.capabilities"] | null> {
    return ask("system.capabilities", {});
  },

  /** Everything a support bundle would contain, listed before it exists (operations/AC-008,
   *  XC-302): the engine's list, asked with the person's choice of their own information. */
  async supportManifest(include: { caseNames: boolean; filePaths: boolean }): Promise<Results["system.supportManifest"] | null> {
    return ask("system.supportManifest", { include });
  },

  /** Class 3: the archive, written where the person chose from the list they were shown, with the
   *  same choice - the engine refuses any other (XC-302). Nothing is sent anywhere. */
  async createSupportBundle(path: string, include: { caseNames: boolean; filePaths: boolean }): Promise<Results["system.supportBundle"] | null> {
    setState({ refusal: null });
    return ask("system.supportBundle", { consent: true, path, include });
  },

  /** One operation by name, from the palette (XC-278), through the same `ask` every screen uses:
   *  a write enters the journal and a warning is kept. The refusal comes back as the outcome's
   *  reason rather than as this window's refusal - the palette shows it beside the command. */
  async run(operation: Operation, parameters: Record<string, unknown>): Promise<RunOutcome> {
    const before = state.refusal;
    setState({ refusal: null });
    const answer = await ask(operation, parameters as unknown as Parameters[Operation]);
    const reason = answer === null ? state.refusal : null;
    setState({ refusal: before });
    if (answer === null) return { status: "refused", result: null, reason: reason ?? "答えがありませんでした" };
    return { status: OPERATION_FACTS[operation].writes ? "applied" : "answered", result: answer, reason: null };
  },

  /** Which catalogue operations this build answers and which it does not (system.operations,
   *  XC-277). A read; kept, so the command list says it beside every row. */
  async operations(): Promise<Results["system.operations"] | null> {
    const answered = await ask("system.operations", {});
    if (answered) setState({ operations: answered });
    return answered;
  },

  /** The engine's record of what was asked (XC-023), read rather than kept here: the engine holds
   *  it, bounds it, and says what the bounds dropped (LIM-014, LIM-015, #315). */
  async history(): Promise<Results["history.list"] | null> {
    if (!state.workspaceId) return null;
    const listed = await ask("history.list", { workspaceId: state.workspaceId });
    if (listed) setState({ history: listed });
    return listed;
  },

  /** What has left the machine, as the gate recorded it (XC-106, XC-267): read, never kept here. */
  async audit(since?: string): Promise<Results["system.audit"] | null> {
    return ask("system.audit", since ? { since } : {});
  },

  /** The diagnostic log read back from the engine (XC-263, XC-286): what was refused, warned and
   *  sent, from the files where the engine writes them - which the answer says. Read, never kept. */
  async log(parameters: Parameters["system.log"] = {}): Promise<Results["system.log"] | null> {
    return ask("system.log", parameters);
  },

  /** A graph of one field's reduction over the loaded case - per case, or per step of the result
   *  axis - written to the document as a definition (graph/AC-004) and read back as numbers from
   *  the engine (XC-290). One graph per session under this dataset's name, updated in place. */
  async showGraph(spec: GraphSpec): Promise<boolean> {
    if (!state.workspaceId) return false;
    // The graph is of the Graph area's case - the tree's, or the one the area is pinned to - and
    // its field is that case's (XC-292). A case with nothing loaded has no field to name.
    const subject = engineState.subjectOf("graph");
    const from = subject.caseId ? state.loaded[subject.caseId] : undefined;
    if (!from) {
      setState({ refusal: `${subject.label}：このセッションで読み込んだデータセットがありません。グラフの場を選べません` });
      return false;
    }
    setState({ refusal: null, graphSpec: spec });
    const field = from.fields.find((one) => one.name === spec.fieldName);
    const name = `${from.sourceName}：${spec.fieldName}`;
    const definition = {
      id: state.graphId ?? "graph:pending",
      name,
      kind: spec.kind,
      series: [
        {
          label: `${spec.fieldName} の${REDUCTION_WORD[spec.reduction]}`,
          source: { kind: "field", datasetId: from.datasetId, fieldName: spec.fieldName, association: field?.association ?? "point", reduction: spec.reduction },
          ...(field?.unit ? { unit: field.unit, unitDeclared: true } : { unitDeclared: false }),
        },
      ],
    };
    let graphId = state.graphId;
    if (!graphId) {
      const saved = state.savedGraphs.find((one) => one.name === name);
      if (saved) graphId = saved.id;
    }
    if (graphId) {
      const updated = await ask("graph.update", { graphId, definition: { ...definition, id: graphId } });
      if (!updated) return false;
    } else {
      const created = await ask("graph.create", { workspaceId: state.workspaceId, definition });
      if (!created) return false;
      graphId = created.id;
      setState({ savedGraphs: [...state.savedGraphs, { id: graphId, name }] });
    }
    setState({ graphId });
    return engineState.refreshGraph();
  },

  /** The graph's numbers, read again from the engine: after a declaration, a step, a change. */
  async refreshGraph(): Promise<boolean> {
    if (!state.graphId) return false;
    // The Graph area's case goes with the question (CT-003 3.15.0): the definition's own cases win
    // where it names them, and the answer says which it was (XC-292).
    const subject = engineState.subjectOf("graph");
    graphContext = subject.caseId;
    const data = await ask("graph.data", { graphId: state.graphId, ...(subject.caseId ? { contextCaseIds: [subject.caseId] } : {}) });
    setState({ graphData: data });
    return data !== null;
  },

  /** Files dropped on the window (XC-301, ingest/AC-020, AC-021, AC-049): one workspace opens; one
   *  result file is inspected first - the engine names its format's support - and loaded into the
   *  case the plan decided; several go each to the case whose record holds that very file, after
   *  every one has been inspected; everything else is refused with the reason, as a notice, and
   *  nothing is read. The outcome is returned for the screen that showed the drop. */
  async dropFiles(paths: readonly string[]): Promise<DropOutcome> {
    // One file goes to the case whose record holds it, else to the case the View area shows - the
    // tree's selection or the pinned case (XC-292) - and to the one a dataset was loaded into only
    // where nothing is selected. The records are the document's sources and this session's loads.
    const shown = engineState.subjectOf("view").caseId ?? state.caseId;
    const plan = dropPlan(paths, { workspaceOpen: state.workspaceId !== null, cases: state.cases, caseId: shown, records: caseRecords() });
    if (plan.kind === "refused") {
      setState({ refusal: plan.reason });
      notice("refusal", "ドロップを受け付けません", plan.reason);
      return { kind: "refused", reason: plan.reason };
    }
    if (plan.kind === "openWorkspace") {
      const opened = await engineState.openWorkspace(plan.path);
      return opened ? { kind: "opened", path: plan.path } : { kind: "refused", reason: state.refusal ?? `${fileName(plan.path)} を開けませんでした` };
    }
    if (plan.kind === "load") {
      const inspection = await engineState.inspect(plan.path);
      if (!inspection) return { kind: "refused", reason: state.refusal ?? `${fileName(plan.path)} を調べられませんでした` };
      const because = inspectionAllowsLoad(inspection, plan.path);
      if (because) {
        setState({ refusal: because, inspection: null });
        notice("refusal", `${fileName(plan.path)} は読み込みません`, because);
        return { kind: "refused", reason: because };
      }
      const loaded = await engineState.loadDataset(plan.caseId, plan.path);
      if (!loaded) return { kind: "refused", reason: state.refusal ?? `${fileName(plan.path)} を読み込めませんでした` };
      await engineState.refresh();
      notice("info", `${fileName(plan.path)} を読み込みました`, `ケース ${describeCase(plan.caseId)}（${LOAD_REASON_WORD[plan.because]}）・対応水準 ${inspection.supportLevel}${inspection.gaps.length > 0 ? `・既知の欠け ${inspection.gaps.length} 件` : ""}`, "dataset.load");
      return { kind: "loaded", path: plan.path, caseId: plan.caseId };
    }
    // Several: every file is inspected before any is read, and one the engine will not take
    // refuses the whole drop by name - a drop is one act (XC-301).
    for (const load of plan.loads) {
      const inspection = await engineState.inspect(load.path);
      const because = inspection ? inspectionAllowsLoad(inspection, load.path) : (state.refusal ?? `${fileName(load.path)} を調べられませんでした`);
      if (because) {
        const reason = `${plan.loads.length} 件のうち ${fileName(load.path)} を読み込めないので、何も読み込みません：${because}`;
        setState({ refusal: reason, inspection: null });
        notice("refusal", "ドロップを受け付けません", reason);
        return { kind: "refused", reason };
      }
    }
    const done: { path: string; caseId: string }[] = [];
    for (const load of plan.loads) {
      const loaded = await engineState.loadDataset(load.caseId, load.path);
      if (!loaded) {
        // A load refused after its inspection passed - a file changed in between (XC-284). What was
        // read stays read, and the notice says exactly how far the drop got.
        const reason = `${fileName(load.path)} を読み込めませんでした：${state.refusal ?? "理由は示されませんでした"}`;
        notice("refusal", `${plan.loads.length} 件のうち ${done.length} 件を読み込んだところで止まりました`, `${done.map((one) => fileName(one.path)).join("、") || "なし"} は読み込み済み。${reason}`);
        setState({ refusal: reason });
        return { kind: "refused", reason };
      }
      done.push(load);
    }
    // The View area shows the case it showed before the drop if that case received a file, else
    // the first loaded case in the document's order; a pinned area was put back by each load.
    const target = done.some((one) => one.caseId === shown) && shown ? shown : done[0]!.caseId;
    if (engineState.subjectOf("view").source !== "pinned") session.selectCase(target);
    await engineState.settled();
    await engineState.refresh();
    notice("info", `${done.length} 件を読み込みました`, done.map((one) => `${fileName(one.path)} → ケース ${describeCase(one.caseId)}`).join("、"), "dataset.load");
    return { kind: "loadedEach", loads: done };
  },

  /** A drop in a browser build: the page has the files' names and not their paths, and the engine
   *  reads from disk - said rather than pretended (XC-291). */
  noteDropWithoutShell(names: readonly string[]) {
    const reason = `ブラウザで動く開発ビルドには経路が渡らないため、ドロップでは開けません（${names.join("、")}）。デスクトップのシェルで落とすか、上の欄に経路を書いてください`;
    setState({ refusal: reason });
    notice("refusal", "ドロップを受け付けません", reason);
  },

  /** Class 1: a dismissed notice is hidden, never deleted (16_application_model §12). */
  dismissNotice(id: string) {
    setState({
      notices: state.notices.map((one) => (one.id === id && !one.dismissedAt ? { ...one, dismissedAt: recordNow() } : one)),
    });
  },

  /** What the runs left behind, run by run, against LIM-012 (XC-141). */
  async outputList(): Promise<Results["output.list"] | null> {
    if (!state.workspaceId) return null;
    return ask("output.list", { workspaceId: state.workspaceId });
  },

  /** Every file that pruning the chosen runs would delete, shown before anything goes (AC-053). */
  async outputPlan(runIds: readonly string[]): Promise<Results["output.plan"] | null> {
    if (!state.workspaceId) return null;
    return ask("output.plan", { workspaceId: state.workspaceId, runsToRemove: [...runIds] });
  },

  /** Class 3, destructive: deletes exactly what the plan showed, with the person's say-so on the
   *  envelope (CT-002) and the files they saw sent back so a folder that changed is refused (XC-268). */
  async outputPrune(runIds: readonly string[], expectedFiles: readonly string[]): Promise<Results["output.prune"] | null> {
    if (!state.workspaceId) return null;
    setState({ refusal: null });
    return ask(
      "output.prune",
      { workspaceId: state.workspaceId, runsToRemove: [...runIds], expectedFiles: [...expectedFiles] },
      { authorisation: { allowDestructive: true } },
    );
  },

  /** Which case an area shows and why (XC-292): the rule is the logic layer's; what goes into it is
   *  the session's binding and selection, the document's cases, and - for the Graph and Report
   *  areas - the cases the open item names for itself, which the tree cannot override. A report
   *  with no view block reads whatever this session loaded, and that is what it says. */
  subjectOf(area: Area): AreaSubject {
    const current = session.current();
    const loaded = loadedList();
    const item =
      area === "graph"
        ? state.graphData && state.graphData.selection === "given"
          ? [...state.graphData.cases]
          : null
        : area === "report" && state.report
          ? (reportItemCases(state.report.blocks, state.savedViews, loaded) ?? loaded.map((one) => one.caseId))
          : null;
    return areaSubject(current.subjects[area], current.selectedCaseId, item, state.cases);
  },

  /** The session's selection or a binding changed (class 2): every following area moves. The View
   *  area's move is a switch of dataset; the Graph area's is a new question with its case. */
  subjectsMoved() {
    if (!engine || !state.workspaceId) return;
    const steps: Promise<unknown>[] = [];
    const view = engineState.subjectOf("view");
    if (view.caseId !== state.caseId) steps.push(showCase(view.caseId));
    if (state.graphId && engineState.subjectOf("graph").caseId !== graphContext) steps.push(engineState.refreshGraph());
    if (steps.length > 0) moving = Promise.all(steps);
  },

  /** Everything the last subject change set in motion, finished - for a test that drives the tree. */
  settled(): Promise<void> {
    return moving.then(() => undefined);
  },

  clearRefusal() {
    setState({ refusal: null });
  },
};

// Selecting a case or pinning an area is the session's; what it means for the engine is this store's.
session.subscribe(() => engineState.subjectsMoved());

/** The store as it stands, for a caller that is not a component: a test that drives the thread
 *  and reads what a screen would have been given. Read-only - the object is frozen by convention
 *  (every field is `readonly`) and every change goes through `engineState`. */
export function snapshot(): EngineState {
  return state;
}

export function useEngine(): EngineState {
  const subscribe = useCallback((listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }, []);
  return useSyncExternalStore(subscribe, () => state);
}

/** Where the shell finds the connection file's contents. The packaged shell hands it in; a
 *  development build reads it from an environment variable vite inlined at build time. Absent means
 *  no engine, which is a mode rather than an error. */
export function connectionFromEnvironment(): Connection | null {
  const raw = import.meta.env.VITE_ENGINE_CONNECTION;
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Connection;
    return parsed.host && parsed.port ? parsed : null;
  } catch {
    return null;
  }
}
