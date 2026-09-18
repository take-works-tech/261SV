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
 * following area re-renders), and a camera move is class 1.
 */
import { useCallback, useSyncExternalStore } from "react";
import { Engine, TransportFailure, reasonText } from "../client/engine";
import type { Connection, Operation, Parameters, Response, Results } from "../client/engine";

/** Whether an engine is reachable, and what it said if it is not. */
export type Reachability =
  | { kind: "unknown" }
  | { kind: "reachable"; protocols: readonly string[] }
  | { kind: "absent"; because: string };

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

export interface EngineState {
  readonly reachability: Reachability;
  readonly workspaceId: string | null;
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
  /** An object URL for the rendered frame, or null. Revoked when it is replaced. */
  readonly imageUrl: string | null;
  readonly reduced: string | null;
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

function cameraFrom(turntable: Turntable, bounds: readonly [number[], number[]] | null) {
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
  workspaceId: null,
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
  imageUrl: null,
  reduced: null,
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
    answer = await engine.submit(operation, parameters);
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
  return (answer.result ?? null) as Results[O] | null;
}

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

  /** Class 3: open a workspace. Everything loaded from the previous one goes with it. */
  async openWorkspace(path: string): Promise<boolean> {
    setState({ refusal: null });
    const opened = await ask("workspace.open", { path });
    if (!opened) return false;
    setImage(null, null);
    setState({
      workspaceId: opened.workspaceId,
      unresolvedCases: opened.unresolvedCases ?? [],
      caseId: null,
      datasetId: null,
      sourceName: null,
      fields: [],
      fieldName: null,
      viewId: null,
      probe: null,
      probeLocation: null,
      statistics: null,
    });
    return true;
  },

  /** Class 3: read a result file into a case. The fields arrive with no unit, as the file had none. */
  async loadDataset(caseId: string, filePath: string): Promise<boolean> {
    setState({ refusal: null });
    const loaded = await ask("dataset.load", { caseId, filePaths: [filePath] });
    if (!loaded) return false;
    const fields = (loaded.fields ?? []) as readonly FieldSummary[];
    setImage(null, null);
    setState({
      caseId,
      datasetId: loaded.datasetId,
      sourceName: filePath.split(/[\\/]/).pop() ?? filePath,
      supportLevel: loaded.supportLevel,
      gaps: loaded.gaps ?? [],
      fields,
      fieldName: fields[0]?.name ?? null,
      viewId: null,
      probe: null,
      probeLocation: null,
      statistics: null,
      turntable: { ...START },
    });
    const described = await ask("dataset.describe", { datasetId: loaded.datasetId });
    setState({
      bounds: described?.boundsM ? [described.boundsM.minM as number[], described.boundsM.maxM as number[]] : null,
    });
    return true;
  },

  /** Class 1: turn the model. The camera is a definition the view carries, so moving it is an
   *  update to that definition and a redraw - not a thing the interface does to a picture. */
  async orbit(byAzimuth: number, byElevation: number): Promise<void> {
    setState({
      turntable: {
        ...state.turntable,
        azimuthDegrees: state.turntable.azimuthDegrees + byAzimuth,
        elevationDegrees: state.turntable.elevationDegrees + byElevation,
      },
    });
    await engineState.refresh();
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
    });
    setState({
      probe: answer?.value ?? null,
      probeLocation: (answer?.value as { location?: string } | undefined)?.location ?? null,
    });
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
    const definition = {
      id: state.viewId ?? "view:pending",
      datasetId: state.datasetId,
      representation: "surface",
      name: state.fieldName,
      colouring: { fieldName: state.fieldName, association, colourMap: state.colourMap },
      camera: cameraFrom(state.turntable, state.bounds),
      // The screen's ground, not the document's. The viewport well is the darkest surface the
      // interface has (XC-256) and a white picture inside it fights the chrome it sits in; a
      // report asks for its own ground, and the view is what says which (CT-004).
      background: { rgb: SCREEN_GROUND },
    };
    let viewId = state.viewId;
    if (viewId) {
      await ask("view.update", { viewId, definition });
    } else {
      const created = await ask("view.create", {
        workspaceId: state.workspaceId ?? "",
        definition,
      });
      viewId = created?.id ?? null;
      setState({ viewId });
    }
    if (!viewId) return;
    const rendered = await ask("view.render", { viewId, ...FRAME, format: "png" });
    if (rendered?.handle) {
      try {
        const blob = await engine.handle(rendered.handle);
        setImage(URL.createObjectURL(blob), rendered.reduced ?? null);
      } catch (failure) {
        setState({ refusal: failure instanceof TransportFailure ? failure.message : String(failure) });
      }
    }
    const statistics = await ask("field.statistics", {
      datasetId: state.datasetId,
      fieldName: state.fieldName,
    });
    setState({ statistics });
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

  clearRefusal() {
    setState({ refusal: null });
  },
};

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
