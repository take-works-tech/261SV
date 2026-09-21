/* Session state (MOD-016): the interface's view of what is open - never the authority.
 *
 * The transition classes of 16_application_model §6 are the shape of this module:
 *   class 1 (tool):     switching screen, toggling a sidebar, changing pane count - preserves the
 *                       open workspace, the selected case, the result position and the selection,
 *                       and never enters undo;
 *   class 2 (subject):  selecting a case or moving the result position - every context-following
 *                       area re-renders;
 *   class 3 (document): opening or closing a workspace - the only class that may discard in-memory
 *                       state, and it says what it will discard first.
 *
 * Deep links: #/screen/variant. The variant is a design-state address (mockup 2 is a catalogue of
 * design states, not evidence of implemented behaviour); entering a screen with no variant lands on
 * its baseline (XC-207).
 *
 * The subject of each artefact area is here too (§8.2 `SubjectBinding`, XC-292): the tree's one
 * selection, and per area whether it follows that selection or is pinned to a case. Without a
 * window - the store's tests run under Node - there is no hash to read and nothing to listen to, and
 * the session is the same object driven by calls.
 */
import { useCallback, useSyncExternalStore } from "react";
import { FOLLOW, type Area, type SubjectBinding } from "../logic/subject";

export type ScreenId =
  | "home"
  | "simulation"
  | "view"
  | "graph"
  | "report"
  | "pipeline"
  | "chat"
  | "settings"
  | "network"
  | "information"
  | "find"
  | "diff";

export type Session = {
  screen: ScreenId;
  variant: string;
  workspaceOpen: boolean;
  selectedCaseId: string | null;
  resultPosition: number; // 0..1 along the result axis - class-2 state, survives screen switches
  leftOpen: boolean;
  rightOpen: boolean;
  leftWidth: number;
  rightWidth: number;
  paneCount: 1 | 2 | 3 | 4;
  cameraSync: boolean;
  /** Which case each artefact area shows: the tree's selection, or one it is pinned to (XC-292). */
  subjects: Readonly<Record<Area, SubjectBinding>>;
};

const FOLLOW_ALL: Readonly<Record<Area, SubjectBinding>> = { view: FOLLOW, graph: FOLLOW, report: FOLLOW };

const hasWindow = typeof window !== "undefined";

const SCREENS: ScreenId[] = [
  "home", "simulation", "view", "graph", "report", "pipeline",
  "chat", "settings", "network", "information", "find", "diff",
];

function fromHash(): { screen: ScreenId; variant: string } {
  if (!hasWindow) return { screen: "home", variant: "default" };
  const parts = window.location.hash.replace(/^#\/?/, "").split("/");
  const screen = (SCREENS as string[]).includes(parts[0] ?? "") ? (parts[0] as ScreenId) : "home";
  return { screen, variant: parts[1] && parts[1] !== "" ? parts[1] : "default" };
}

let state: Session = {
  ...fromHash(),
  workspaceOpen: fromHash().screen !== "home",
  selectedCaseId: "case-012",
  resultPosition: 0.35,
  leftOpen: true,
  rightOpen: true,
  leftWidth: 224,
  rightWidth: 288,
  paneCount: 1,
  cameraSync: false,
  subjects: FOLLOW_ALL,
};

const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function setState(patch: Partial<Session>) {
  state = { ...state, ...patch };
  emit();
}

if (hasWindow) {
  window.addEventListener("hashchange", () => {
    const { screen, variant } = fromHash();
    // A hash change is a class-1 transition: the tool changes, the subject survives.
    setState({ screen, variant, workspaceOpen: screen === "home" ? state.workspaceOpen : true });
  });
}

export const session = {
  /** Class 1: change the tool. The subject - case, result position, selection - survives. */
  navigate(screen: ScreenId, variant = "default") {
    if (!hasWindow) {
      setState({ screen, variant, workspaceOpen: screen === "home" ? state.workspaceOpen : true });
      return;
    }
    window.location.hash = `#/${screen}/${variant}`;
  },
  /** Class 2: change the subject. Context-following areas re-render. */
  selectCase(id: string | null) {
    setState({ selectedCaseId: id });
  },
  moveResultPosition(position: number) {
    setState({ resultPosition: Math.min(Math.max(position, 0), 1) });
  },
  /** Class 3: change the document. The only class that may discard in-memory state. */
  openWorkspace() {
    setState({ workspaceOpen: true });
    session.navigate("view");
  },
  closeWorkspace() {
    setState({ workspaceOpen: false, selectedCaseId: null, subjects: FOLLOW_ALL });
    session.navigate("home");
  },
  /** Pin an area to one case - it stops following the tree - or let it follow again (§8.2, XC-292).
   *  Session state: nothing of it enters the document. */
  pinArea(area: Area, caseId: string) {
    setState({ subjects: { ...state.subjects, [area]: { mode: "pinned", caseId } } });
  },
  followArea(area: Area) {
    setState({ subjects: { ...state.subjects, [area]: FOLLOW } });
  },
  /** Class 3: another document. Its pins named cases of the one that is gone. */
  resetSubjects() {
    setState({ subjects: FOLLOW_ALL });
  },
  /** The session as it stands, for a caller that is not a component: the store, or a test. */
  current(): Session {
    return state;
  },
  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  toggleLeft() { setState({ leftOpen: !state.leftOpen }); },
  toggleRight() { setState({ rightOpen: !state.rightOpen }); },
  setLeftWidth(width: number) { setState({ leftWidth: Math.min(Math.max(width, 168), 360) }); },
  setRightWidth(width: number) { setState({ rightWidth: Math.min(Math.max(width, 220), 420) }); },
  setPaneCount(count: 1 | 2 | 3 | 4) { setState({ paneCount: count }); },
  toggleCameraSync() { setState({ cameraSync: !state.cameraSync }); },
};

export function useSession(): Session {
  const subscribe = useCallback((listener: () => void) => session.subscribe(listener), []);
  return useSyncExternalStore(subscribe, () => state);
}
