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
 */
import { useCallback, useSyncExternalStore } from "react";

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
};

const SCREENS: ScreenId[] = [
  "home", "simulation", "view", "graph", "report", "pipeline",
  "chat", "settings", "network", "information", "find", "diff",
];

function fromHash(): { screen: ScreenId; variant: string } {
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
};

const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function setState(patch: Partial<Session>) {
  state = { ...state, ...patch };
  emit();
}

window.addEventListener("hashchange", () => {
  const { screen, variant } = fromHash();
  // A hash change is a class-1 transition: the tool changes, the subject survives.
  setState({ screen, variant, workspaceOpen: screen === "home" ? state.workspaceOpen : true });
});

export const session = {
  /** Class 1: change the tool. The subject - case, result position, selection - survives. */
  navigate(screen: ScreenId, variant = "default") {
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
    setState({ workspaceOpen: false, selectedCaseId: null });
    session.navigate("home");
  },
  toggleLeft() { setState({ leftOpen: !state.leftOpen }); },
  toggleRight() { setState({ rightOpen: !state.rightOpen }); },
  setLeftWidth(width: number) { setState({ leftWidth: Math.min(Math.max(width, 168), 360) }); },
  setRightWidth(width: number) { setState({ rightWidth: Math.min(Math.max(width, 220), 420) }); },
  setPaneCount(count: 1 | 2 | 3 | 4) { setState({ paneCount: count }); },
  toggleCameraSync() { setState({ cameraSync: !state.cameraSync }); },
};

export function useSession(): Session {
  const subscribe = useCallback((listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }, []);
  return useSyncExternalStore(subscribe, () => state);
}
