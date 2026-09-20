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
import type { CameraDefinition, RecordedTime } from "../client/generated";
import { recordNow } from "../client/time";

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
}

/** A number the engine reported, carried whole. Never unpacked into a bare value: a value without
 *  its unit, digits and provenance is a value in whatever unit the reader assumed (XC-003). */
export type Reported = Results["dataset.probe"]["value"];

/** One write the engine applied since the document was last saved. What a crash loses is exactly
 *  this list, so it is kept as the engine answers it - operation and the engine's own summary - and
 *  never reconstructed afterwards (XC-259). */
export interface AppliedWrite {
  readonly operation: string;
  readonly summary: string;
  readonly at: RecordedTime;
}

/** What was opened, so that what was saved can be opened again after the engine is restarted. */
export interface Opened {
  readonly workspacePath: string;
  readonly caseId: string | null;
  readonly filePath: string | null;
}

/** A view the opened document already holds, as `workspace.open` answered it. */
export interface SavedView {
  readonly id: string;
  readonly name: string;
  readonly datasetId?: string;
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
  /** Whether the document may not be written back - somebody else holds its lock - and what the
   *  lock said. Read-only is drawn at the save: the window works in memory (XC-269). */
  readonly readOnly: boolean;
  readonly lock: Lock | null;
  /** What the engine's last answer warned about, in its own words, until dismissed. Dropped until
   *  2026-09-20, which is how a document lifted, a dataset closed or a lock held went unsaid. */
  readonly warnings: readonly string[];
  readonly unresolvedCases: readonly string[];
  readonly caseId: string | null;
  readonly datasetId: string | null;
  readonly sourceName: string | null;
  readonly supportLevel: string | null;
  readonly gaps: readonly string[];
  readonly fields: readonly FieldSummary[];
  readonly fieldName: string | null;
  readonly colourMap: string;
  readonly viewId: string | null;
  /** The view's own camera - what a report renders - as this session last wrote it. The live camera
   *  is the turntable and stays out of the document until `keepCamera` (XC-270). */
  readonly savedCamera: CameraDefinition | null;
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
  readonly statistics: Results["field.statistics"] | null;
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

const EMPTY: EngineState = {
  reachability: { kind: "unknown" },
  opened: null,
  inspection: null,
  savedViews: [],
  journal: [],
  lost: null,
  savedAt: null,
  history: null,
  workspaceId: null,
  readOnly: false,
  lock: null,
  warnings: [],
  unresolvedCases: [],
  caseId: null,
  datasetId: null,
  sourceName: null,
  supportLevel: null,
  gaps: [],
  fields: [],
  fieldName: null,
  colourMap: "viridis",
  viewId: null,
  savedCamera: null,
  imageUrl: null,
  reduced: null,
  partial: false,
  partVisibility: {},
  selectedPart: null,
  described: null,
  parts: null,
  probe: null,
  probeLocation: null,
  statistics: null,
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
  setState({ busy: true });
  let answer: Response<O>;
  try {
    answer = await engine.submit(operation, parameters, options);
  } catch (failure) {
    const because = failure instanceof TransportFailure ? failure.message : String(failure);
    setState({ busy: false, refusal: because, reachability: { kind: "absent", because } });
    return null;
  }
  setState({ busy: false });
  if (answer.status === "refused" || answer.status === "failed") {
    setState({ refusal: reasonText(answer.reason) || `'${operation}' は行えませんでした` });
    return null;
  }
  // What the engine had to say beside its answer is shown, not dropped: a document lifted to a
  // new version, a dataset closed by an open, a lock somebody else holds (XC-001).
  if (answer.warnings && answer.warnings.length > 0) {
    // Kept beside earlier ones until dismissed, not replaced by the next answer's: an open that found
    // a lock held is followed at once by a load and a render, and the lock is still held.
    const fresh = answer.warnings.filter((one) => !state.warnings.includes(one));
    setState({ warnings: [...state.warnings, ...fresh].slice(-20) });
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
    if (!(await engineState.openWorkspace(opened.workspacePath))) return reachability;
    if (opened.caseId && opened.filePath) {
      if (await engineState.loadDataset(opened.caseId, opened.filePath)) await engineState.refresh();
    }
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
    if (!(await engineState.openWorkspace(opened.workspacePath, { takeOverStaleLock: true }))) return false;
    if (opened.caseId && opened.filePath) {
      if (await engineState.loadDataset(opened.caseId, opened.filePath)) await engineState.refresh();
    }
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
  async openWorkspace(path: string, options: { takeOverStaleLock?: boolean } = {}): Promise<boolean> {
    setState({ refusal: null, warnings: [] });
    const opened = await ask("workspace.open", options.takeOverStaleLock ? { path, takeOverStaleLock: true } : { path });
    if (!opened) return false;
    setImage(null, null);
    setState({
      opened: { workspacePath: path, caseId: null, filePath: null },
      savedViews: (opened.items?.views ?? []) as readonly SavedView[],
      journal: [],
      savedAt: null,
      workspaceId: opened.workspaceId,
      readOnly: opened.readOnly ?? false,
      lock: opened.lock ?? null,
      unresolvedCases: opened.unresolvedCases ?? [],
      caseId: null,
      datasetId: null,
      sourceName: null,
      fields: [],
      fieldName: null,
      viewId: null,
      partial: false,
      partVisibility: {},
      selectedPart: null,
      described: null,
      parts: null,
      probe: null,
      probeLocation: null,
      statistics: null,
    });
    return true;
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
    setImage(null, null);
    setState({
      opened: state.opened ? { ...state.opened, caseId, filePath } : null,
      inspection: null,
      caseId,
      datasetId: loaded.datasetId,
      sourceName: filePath.split(/[\\/]/).pop() ?? filePath,
      supportLevel: loaded.supportLevel,
      gaps: loaded.gaps ?? [],
      fields,
      fieldName: fields[0]?.name ?? null,
      viewId: null,
      savedCamera: null,
      partial: false,
      partVisibility: {},
      selectedPart: null,
      described: null,
      parts: null,
      probe: null,
      probeLocation: null,
      statistics: null,
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
    return true;
  },

  /** Class 1: turn the model. The camera is a definition the view carries, so moving it is an
   *  update to that definition and a redraw - not a thing the interface does to a picture. */
  /** Class 1: a new look at the same view. The picture is drawn again from the new camera; nothing
   *  is written, so nothing enters the undo history or the unsaved work (XC-270). */
  async orbit(byAzimuth: number, byElevation: number): Promise<void> {
    setState({
      turntable: {
        ...state.turntable,
        azimuthDegrees: state.turntable.azimuthDegrees + byAzimuth,
        elevationDegrees: state.turntable.elevationDegrees + byElevation,
      },
    });
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
      // The camera the frame on screen was drawn with, or the pixel is read off another picture.
      camera: cameraFrom(state.turntable, state.bounds),
    });
    setState({
      probe: answer?.value ?? null,
      probeLocation: (answer?.value as { location?: string } | undefined)?.location ?? null,
      // The part under the pixel is the selection now, so the outliner follows the viewport
      // (view/AC-055). A pixel on nothing changes no selection: nothing was chosen there.
      selectedPart: answer?.part ?? state.selectedPart,
    });
  },

  /** Class 1: choose a row - a part or a block - in the outliner or by picking. Nothing is written. */
  selectPart(name: string | null): void {
    setState({ selectedPart: name });
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
    const done = await ask("field.declareUnit", { datasetId: state.datasetId, fieldName, unitSymbol });
    if (done === null && state.refusal) return false;
    setState({
      fields: state.fields.map((one) => (one.name === fieldName ? { ...one, unit: unitSymbol } : one)),
    });
    // The legend and every reported number carry the unit now, so both are asked for again rather
    // than edited here: this layer never computes, and a relabelled copy would be a second answer.
    await engineState.refresh();
    return true;
  },

  /** Class 2: choose which field the colours mean. */
  async chooseField(fieldName: string): Promise<void> {
    setState({ fieldName, probe: null, probeLocation: null });
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
    let viewId = state.viewId;
    if (!viewId) {
      // The document may already hold this view - saved in an earlier session - and a second one
      // under the same name is refused (AC-030). Updating it is what a person means by "the view",
      // and what it holds is read before it is written: the camera a person kept and the parts
      // they hid are the document's, not this window's to rebuild. Until 2026-09-20 the first
      // redraw of a session overwrote both with what the window had, which was nothing (XC-274).
      const saved = state.savedViews.find((one) => one.name === state.fieldName);
      if (saved) {
        viewId = saved.id;
        const held = await ask("view.get", { viewId });
        const kept = (held?.definition ?? {}) as {
          camera?: CameraDefinition;
          partVisibility?: Record<string, boolean>;
          colouring?: { colourMap?: string };
        };
        setState({
          viewId,
          savedCamera: kept.camera ?? null,
          partVisibility: kept.partVisibility ?? {},
          colourMap: kept.colouring?.colourMap ?? state.colourMap,
        });
      }
    }
    const definition = {
      id: viewId ?? "view:pending",
      datasetId: state.datasetId,
      representation: "surface",
      name: state.fieldName,
      colouring: { fieldName: state.fieldName, association, colourMap: state.colourMap },
      // Which parts the picture shows, as the outliner last set it (CT-004, XC-274).
      partVisibility: { ...state.partVisibility },
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
    } else {
      const created = await ask("view.create", {
        workspaceId: state.workspaceId ?? "",
        definition,
      });
      viewId = created?.id ?? null;
      // The view the document now holds, remembered beside the ones it held at open: a dataset
      // loaded again would otherwise create a second view under this name, which the document
      // refuses (AC-030) - the case that surfaced when a partial file was loaded and the cube put back.
      setState({
        viewId,
        savedViews:
          viewId && state.fieldName && state.datasetId
            ? [...state.savedViews, { id: viewId, name: state.fieldName, datasetId: state.datasetId }]
            : state.savedViews,
      });
    }
    if (!viewId) return;
    if (!state.savedCamera && definition.camera) setState({ savedCamera: definition.camera });
    await engineState.draw();
    const statistics = await ask("field.statistics", {
      datasetId: state.datasetId,
      fieldName: state.fieldName,
    });
    setState({ statistics });
  },

  /** Draw the view from the live camera. The picture, not the document: the camera goes as a
   *  parameter of `view.render` and the definition is not touched (XC-270). */
  async draw(): Promise<void> {
    const viewId = state.viewId;
    if (!viewId || !engine) return;
    // No bar inside the picture: the rail's legend carries the range with its unit, which the
    // bar cannot (E-192), and two scales for one image is one too many. A document asks for it.
    const rendered = await ask("view.render", {
      viewId,
      ...FRAME,
      format: "png",
      legend: false,
      camera: cameraFrom(state.turntable, state.bounds),
    });
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
      resultPosition: 0,
    });
    setState({
      probe: answer?.value ?? null,
      probeLocation: (answer?.value as { location?: string } | undefined)?.location ?? null,
    });
  },

  /** Write the deliverable: the values, and the picture where one was drawn. */
  async exportReport(path: string): Promise<Results["report.export"] | null> {
    if (!state.workspaceId || !state.fieldName) return null;
    const blocks: Record<string, unknown>[] = [];
    if (state.viewId) blocks.push({ kind: "view", viewId: state.viewId, form: "still" });
    blocks.push({ kind: "valueTable", fields: [state.fieldName] });
    const report = await ask("report.create", {
      workspaceId: state.workspaceId,
      definition: {
        id: "report:pending",
        name: state.sourceName ?? "レポート",
        targets: ["html"],
        blocks,
      },
    });
    if (!report) return null;
    return ask("report.export", { reportId: report.id, path });
  },

  /** What this build can do and where it keeps its log (system.capabilities). A read. */
  async capabilities(): Promise<Results["system.capabilities"] | null> {
    return ask("system.capabilities", {});
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

  clearRefusal() {
    setState({ refusal: null });
  },
};

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
