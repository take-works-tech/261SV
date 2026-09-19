/* MOD-017 (client): the shape of the desktop shell's bridge.
 *
 * Declared here, in the interface, because the interface is what depends on it; the shell (MOD-018)
 * implements it, so the dependency points down. Nothing above `client` learns whether a shell exists
 * from anywhere but `shellApi()`: in a browser it answers null and every screen behaves as it did.
 *
 * The bridge carries **what the shell alone can know or do**: whether the engine process is up, the
 * connection it wrote, and the operating system's file dialogs. It carries no data and computes
 * nothing; a value that reaches a screen still comes from the engine's answer (XC-252).
 */
/** What the shell reads from the engine's connection file and hands to the interface (XC-258). The
 *  token travels here and nowhere else - never a URL, never an argument. */
export interface Connection {
  readonly host: string;
  readonly port: number;
  readonly token: string;
  readonly protocol: string;
}

export type EngineProcessState = "starting" | "running" | "exited";

/** What the shell knows about the engine process, pushed whenever it changes (XC-259). */
export interface EngineProcessStatus {
  readonly state: EngineProcessState;
  readonly pid: number | null;
  /** When this state began, ISO 8601 with offset. */
  readonly since: string;
  /** The exit code when the process ended on its own; null otherwise. */
  readonly exitCode: number | null;
  /** The signal that ended it; null otherwise. One of exitCode and signal is set once exited. */
  readonly signal: string | null;
  /** A sentence for a person, in the shell's words, or null while nothing is wrong. */
  readonly reason: string | null;
}

export interface ShellApi {
  readonly kind: "electron";
  readonly engine: {
    /** The connection the running engine wrote, or null while starting or after it exited. */
    connection(): Promise<Connection | null>;
    status(): Promise<EngineProcessStatus>;
    /** Every change of state, until the returned function is called. */
    onStatus(listener: (status: EngineProcessStatus) => void): () => void;
    /** Stop what is running, if anything, and start again. Resolves with the new status. */
    restart(): Promise<EngineProcessStatus>;
  };
  readonly dialog: {
    /** A path the person chose, or null if they cancelled. The path is the shell's to obtain: a page
     *  in a browser gets a File and never a path, and the engine reads from disk (XC-259). */
    openWorkspace(): Promise<string | null>;
    openResult(): Promise<string | null>;
    saveReport(suggestedName: string): Promise<string | null>;
  };
}

declare global {
  interface Window {
    solvia?: ShellApi;
  }
}

/** The shell's bridge if this page runs inside the desktop shell, else null. */
export function shellApi(): ShellApi | null {
  if (typeof window === "undefined") return null;
  return window.solvia ?? null;
}
