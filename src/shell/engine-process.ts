/* The engine as a process the shell owns (XC-259).
 *
 * Pure Node: no Electron in here, so a test can start, crash and stop a real engine without a
 * window. The shell's main process is a thin caller of this.
 *
 * Three rules, each from a measurement or a document:
 *   - **The connection file is a hint, not proof.** A crash leaves it behind (E-197), so a file found
 *     at start belongs to a previous life: if the pid it names still answers `/health`, that engine
 *     is ours and is stopped; the file is removed either way. Nothing is "connected" until `/health`
 *     has answered for the process this shell started.
 *   - **A crash is an event.** Node's 'exit' carries a code or a signal and one of the two is always
 *     set (E-200); the status pushed to the interface carries both, so a person reads "exit code 1"
 *     or "SIGSEGV" and not "the engine stopped responding".
 *   - **The token is never printed.** The child's output is handed to a caller that asked for it and
 *     nowhere else; the engine itself never writes the token to stdout (tested on the Python side).
 */
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { join } from "node:path";

import type { Connection } from "../ui/client/engine";
import { CONNECTION_FILE, type RecordedTime } from "../ui/client/generated.js";
import { recordInstant, recordNow } from "../ui/client/time.js";
// The bridge's types are the one definition of what crosses it (XC-015); the shell fills them.
import type { EngineProcessStatus, Orphan } from "../ui/client/shell";

export type { Orphan };

export { CONNECTION_FILE };

export interface EngineOptions {
  /** The engine executable: an interpreter in development, the frozen `solvia-engine` when packaged
   *  (XC-261). What follows it is `args`; the connection directory is appended here. */
  readonly command: string;
  readonly args?: readonly string[];
  /** Where the engine writes its diagnostic log, rotated and retained (XC-263). Omitted, the log
   *  stays in the engine's memory. */
  readonly logDirectory?: string;
  readonly logLevel?: "debug" | "info" | "warning" | "error";
  /** The working directory the engine starts in. */
  readonly cwd: string;
  /** Environment added to the shell's own: PYTHONPATH in development, nothing when packaged. */
  readonly environment?: Readonly<Record<string, string>>;
  /** Where the engine writes its connection file - the shell's own directory, never a shared one. */
  readonly directory: string;
  /** The renderer's origin, for the engine's CORS header (XC-260). */
  readonly allowOrigin?: string;
  /** How long a start may take before it is a failure. A cold VTK import on a slow disk is seconds,
   *  not minutes; the default is generous because a timeout that fires on a slow laptop is a bug
   *  report about a product that works. */
  readonly readyTimeoutMs?: number;
  readonly onStatus?: (status: EngineProcessStatus) => void;
  /** The child's stdout and stderr, line by line, for a log. Never printed by this module. */
  readonly output?: (line: string) => void;
}

export interface Engine {
  /** The connection while running; null once exited. */
  readonly connection: Connection | null;
  readonly child: ChildProcess;
  status(): EngineProcessStatus;
  onStatus(listener: (status: EngineProcessStatus) => void): () => void;
  /** SIGTERM, then SIGKILL if it does not leave, then the connection file if it is still there. */
  stop(): Promise<EngineProcessStatus>;
}

export class EngineStartError extends Error {
  constructor(
    message: string,
    readonly status: EngineProcessStatus,
  ) {
    super(message);
    this.name = "EngineStartError";
  }
}

/** Now, as the shell records it: the same two facts the engine writes (XC-142, XC-266). */
const now = (): RecordedTime => recordNow();

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

function processAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function health(connection: Connection, timeoutMs: number): Promise<string[] | null> {
  try {
    const answer = await fetch(`http://${connection.host}:${connection.port}/health`, {
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!answer.ok) return null;
    const body = (await answer.json()) as { protocols?: unknown };
    return Array.isArray(body.protocols) ? body.protocols.map(String) : null;
  } catch {
    return null;
  }
}

/** The engine as development runs it: an interpreter, `-m service.transport`, `src/` on its path. */
export function developmentEngine(python: string, root: string): Pick<EngineOptions, "command" | "args" | "cwd" | "environment"> {
  return {
    command: python,
    args: ["-m", "service.transport"],
    cwd: root,
    environment: { PYTHONPATH: join(root, "src") },
  };
}

/** The engine as a package carries it: the frozen executable in its own directory (XC-261). */
export function packagedEngine(resources: string): Pick<EngineOptions, "command" | "args" | "cwd" | "environment"> {
  const directory = join(resources, "engine");
  return {
    command: join(directory, process.platform === "win32" ? "solvia-engine.exe" : "solvia-engine"),
    args: [],
    cwd: directory,
    environment: {},
  };
}

// ---- where transient files live, and what is left of sessions that died (XC-262, #313) -------

/** One engine session's directory: everything transient the engine writes for that session, under
 *  the root the shell owns, named by the shell's own pid. Nothing transient goes anywhere else. */
export function sessionDirectory(root: string, pid: number = process.pid): string {
  return join(root, "sessions", String(pid));
}

function walkSize(directory: string): { bytes: number; files: number; newest: number } {
  let bytes = 0;
  let files = 0;
  let newest = 0;
  const stack = [directory];
  while (stack.length > 0) {
    const current = stack.pop() as string;
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const full = join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(full);
      } else {
        const stat = statSync(full);
        bytes += stat.size;
        files += 1;
        newest = Math.max(newest, stat.mtimeMs);
      }
    }
  }
  return { bytes, files, newest };
}

/** Session directories whose shell no longer runs. Detected, never removed here: what to do with
 *  them is a person's choice, and the default is to keep (#313). The current session and any
 *  session whose pid is alive are not orphans, whatever they hold. */
export function findOrphans(root: string): Orphan[] {
  const sessions = join(root, "sessions");
  if (!existsSync(sessions)) return [];
  const orphans: Orphan[] = [];
  for (const entry of readdirSync(sessions, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const pid = /^\d+$/.test(entry.name) ? Number(entry.name) : null;
    if (pid !== null && (pid === process.pid || processAlive(pid))) continue;
    const path = join(sessions, entry.name);
    const size = walkSize(path);
    orphans.push({
      id: entry.name,
      path,
      pid,
      bytes: size.bytes,
      files: size.files,
      modified: size.newest ? recordInstant(new Date(size.newest)) : null,
    });
  }
  return orphans;
}

/** Remove the named orphans - only ones `findOrphans` would still name, so a session that came
 *  alive in between is not removed from under it. Returns what was removed. */
export function removeOrphans(root: string, ids: readonly string[]): Orphan[] {
  const current = new Map(findOrphans(root).map((one) => [one.id, one]));
  const removed: Orphan[] = [];
  for (const id of ids) {
    const orphan = current.get(id);
    if (!orphan) continue;
    rmSync(orphan.path, { recursive: true, force: true });
    removed.push(orphan);
  }
  return removed;
}

/** What a connection file left by a previous life is, and what was done about it. */
export async function clearStale(directory: string): Promise<string | null> {
  const file = join(directory, CONNECTION_FILE);
  if (!existsSync(file)) return null;
  let note = "a connection file from a previous run was found";
  try {
    const stale = JSON.parse(readFileSync(file, "utf-8")) as Partial<Connection> & { pid?: number };
    const pid = typeof stale.pid === "number" ? stale.pid : null;
    if (pid !== null && processAlive(pid) && stale.host && stale.port && stale.token) {
      const answered = await health(stale as Connection, 1500);
      if (answered) {
        // An engine of ours, orphaned by a shell that died: XC-259 says one engine per instance.
        try {
          process.kill(pid);
        } catch {
          /* it may have left between the two calls */
        }
        for (let waited = 0; waited < 3000 && processAlive(pid); waited += 100) await sleep(100);
        note = `an orphaned engine (pid ${pid}) from a previous run was stopped`;
      } else {
        note = `the file named pid ${pid}, which is alive but is not answering as an engine; left alone`;
      }
    } else if (pid !== null) {
      note = `the file named pid ${pid}, which is no longer running`;
    }
  } catch {
    note = "a connection file from a previous run could not be read";
  }
  rmSync(file, { force: true });
  return `${note}; the file was removed`;
}

export async function startEngine(options: EngineOptions): Promise<Engine> {
  const directory = options.directory;
  mkdirSync(directory, { recursive: true });
  const stale = await clearStale(directory);
  if (stale && options.output) options.output(`shell: ${stale}`);

  const listeners = new Set<(status: EngineProcessStatus) => void>();
  if (options.onStatus) listeners.add(options.onStatus);
  let status: EngineProcessStatus = {
    state: "starting",
    pid: null,
    since: now(),
    exitCode: null,
    signal: null,
    reason: null,
  };
  let connection: Connection | null = null;
  // The engine's own pid, from the file it wrote. Not `child.pid`: on Windows a virtual
  // environment's python.exe is a launcher that starts the real interpreter as its child, so the
  // process this shell spawned and the process that is the engine differ (measured 2026-09-19, and
  // the reason XC-259 put the pid in the file at all).
  let enginePid: number | null = null;
  const file = join(directory, CONNECTION_FILE);

  const set = (next: EngineProcessStatus) => {
    status = next;
    for (const listener of listeners) listener(next);
  };

  const args = [...(options.args ?? []), "--connection-directory", directory];
  if (options.allowOrigin) args.push("--allow-origin", options.allowOrigin);
  if (options.logDirectory) args.push("--log-directory", options.logDirectory);
  if (options.logLevel) args.push("--log-level", options.logLevel);
  const child = spawn(options.command, args, {
    cwd: options.cwd,
    env: {
      ...process.env,
      ...(options.environment ?? {}),
      PYTHONIOENCODING: "utf-8",
    },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  set({ ...status, pid: child.pid ?? null });

  const forward = (chunk: Buffer) => {
    if (!options.output) return;
    for (const line of chunk.toString().split(/\r?\n/)) if (line) options.output(line);
  };
  child.stdout?.on("data", forward);
  child.stderr?.on("data", forward);

  let spawnError: Error | null = null;
  child.on("error", (error) => {
    spawnError = error;
  });

  const exited = new Promise<EngineProcessStatus>((resolve) => {
    child.on("exit", (code, signal) => {
      connection = null;
      // The engine removes its file on a clean stop and cannot on a crash; whichever it was, a file
      // that outlives its process would send the next start to a port nothing answers on.
      rmSync(file, { force: true });
      // If what died was a launcher and the engine is still running, it is an orphan of ours.
      if (enginePid !== null && processAlive(enginePid)) {
        try {
          process.kill(enginePid);
        } catch {
          /* it left between the two calls */
        }
      }
      const reason =
        signal !== null
          ? `エンジンが停止されました（${signal}）`
          : `エンジンが終了しました（終了コード ${code}）`;
      const next: EngineProcessStatus = {
        state: "exited",
        pid: status.pid,
        since: now(),
        exitCode: code,
        signal,
        reason: status.state === "starting" ? `起動中に${reason}` : reason,
      };
      set(next);
      resolve(next);
    });
  });

  // Wait for the file the engine writes, or for the process to leave, or for the clock.
  const deadline = Date.now() + (options.readyTimeoutMs ?? 90_000);
  while (!existsSync(file)) {
    if (status.state === "exited") {
      throw new EngineStartError(status.reason ?? "エンジンが起動中に終了しました", status);
    }
    if (spawnError) {
      const failed: EngineProcessStatus = {
        ...status,
        state: "exited",
        since: now(),
        reason: `エンジンを起動できません（${(spawnError as Error).message}）`,
      };
      set(failed);
      throw new EngineStartError(failed.reason ?? "", failed);
    }
    if (Date.now() > deadline) {
      child.kill("SIGKILL");
      const timedOut: EngineProcessStatus = {
        ...status,
        state: "exited",
        since: now(),
        reason: `エンジンが ${Math.round((options.readyTimeoutMs ?? 90_000) / 1000)} 秒以内に接続ファイルを書きませんでした`,
      };
      set(timedOut);
      throw new EngineStartError(timedOut.reason ?? "", timedOut);
    }
    await sleep(50);
  }
  const written = JSON.parse(readFileSync(file, "utf-8")) as Connection & { pid?: number };

  // "Connected" means /health answered for this process, not that a file exists.
  const protocols = await health(written, 10_000);
  if (!protocols) {
    child.kill("SIGKILL");
    const mute: EngineProcessStatus = {
      ...status,
      state: "exited",
      since: now(),
      reason: "エンジンは接続ファイルを書きましたが /health に応答しません",
    };
    set(mute);
    throw new EngineStartError(mute.reason ?? "", mute);
  }
  connection = written;
  enginePid = typeof written.pid === "number" ? written.pid : (child.pid ?? null);
  set({ ...status, state: "running", pid: enginePid, since: now(), reason: null });

  return {
    get connection() {
      return connection;
    },
    child,
    status: () => status,
    onStatus(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    async stop() {
      if (status.state === "exited") return status;
      child.kill();
      const left = await Promise.race([exited, sleep(5_000).then(() => null)]);
      if (!left) {
        child.kill("SIGKILL");
        await Promise.race([exited, sleep(2_000)]);
      }
      // The engine itself, if the child was only its launcher.
      if (enginePid !== null) {
        for (let waited = 0; waited < 3_000 && processAlive(enginePid); waited += 100) {
          if (waited === 0) {
            try {
              process.kill(enginePid);
            } catch {
              break;
            }
          }
          await sleep(100);
        }
      }
      rmSync(file, { force: true });
      return status;
    },
  };
}
