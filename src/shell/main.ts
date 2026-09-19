/* The desktop shell's main process (MOD-018, XC-259, XC-260).
 *
 * It does four things and computes nothing: it owns the engine process, it owns the window, it
 * answers the operating system's file dialogs, and it hands the interface the connection through a
 * bridge the preload exposes. Every number a screen shows still comes from the engine.
 *
 * The renderer is served from `solvia://app/`, a privileged scheme backed by the interface's built
 * files, and not from `file://` (E-198, E-199 item 18). The engine is told that origin and no other.
 * The renderer runs with context isolation, the sandbox and no Node integration (E-199 items 2-4).
 *
 * `--smoke` runs the same wiring with no person present: start the engine, verify it, kill it the
 * way a crash would, see the exit arrive as an event, restart, and stop - printing one JSON object
 * with no token in it. `--capture <png>` additionally opens the window on the built interface and
 * writes what it shows, so a picture of the shell exists that a person can look at.
 */
import { app, BrowserWindow, dialog, ipcMain, net, protocol } from "electron";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import type { EngineProcessStatus } from "../ui/client/shell";
import {
  developmentEngine,
  findOrphans,
  packagedEngine,
  removeOrphans,
  sessionDirectory,
  startEngine,
  type Engine,
  type Orphan,
} from "./engine-process.js";

const HERE = fileURLToPath(new URL(".", import.meta.url)); // <package>/dist/shell/
const PACKAGE = resolve(HERE, "..", "..");
const ROOT = resolve(PACKAGE, "..", "..");
// Packaged, the interface and the engine sit in the application's resources; in development they
// are the repository's own build outputs (XC-261). Nothing else differs between the two.
const PACKAGED = app.isPackaged;
const UI_DIST = PACKAGED ? join(process.resourcesPath, "ui") : join(ROOT, "src", "ui", "dist");
const SCHEME = "solvia";
const ORIGIN = `${SCHEME}://app`;
const PYTHON = process.env.SOLVIA_PYTHON ?? "python";

const argv = process.argv.slice(1);
const SMOKE = argv.includes("--smoke");
const captureIndex = argv.indexOf("--capture");
const CAPTURE = captureIndex >= 0 ? argv[captureIndex + 1] ?? null : null;
const routeIndex = argv.indexOf("--route");
const ROUTE = routeIndex >= 0 ? argv[routeIndex + 1] ?? "" : "";

// ---- one instance, one engine (E-195) ---------------------------------------------------------

if (!SMOKE && !app.requestSingleInstanceLock()) {
  app.quit();
}

protocol.registerSchemesAsPrivileged([
  { scheme: SCHEME, privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true } },
]);

let engine: Engine | null = null;
let window: BrowserWindow | null = null;
let stopping = false;
const log: string[] = [];

function note(line: string): void {
  log.push(line);
  if (log.length > 500) log.shift();
}

function broadcast(status: EngineProcessStatus): void {
  for (const each of BrowserWindow.getAllWindows()) each.webContents.send("engine:status", status);
}

async function start(directory: string): Promise<Engine> {
  const started = await startEngine({
    ...(PACKAGED ? packagedEngine(process.resourcesPath) : developmentEngine(PYTHON, ROOT)),
    directory,
    allowOrigin: ORIGIN,
    onStatus: broadcast,
    output: note,
  });
  engine = started;
  return started;
}

/** The root of everything transient (XC-262): the engine's session directories live under it, and
 *  nothing transient lives anywhere else. The smoke uses a root of its own under temp and removes
 *  it when it is done - the smoke's own leftovers were the first orphans measured (E-208). */
function transientRoot(): string {
  return SMOKE ? join(app.getPath("temp"), `solvia-smoke-${process.pid}`) : join(app.getPath("userData"), "engine");
}

function engineDirectory(): string {
  return sessionDirectory(transientRoot());
}

/** Orphans found at start: sessions of shells that are gone. Reported to the interface, removed
 *  only when a person says so, and never touched otherwise (#313). */
let orphans: Orphan[] = [];

// ---- the renderer's origin (E-198) -------------------------------------------------------------

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".ico": "image/x-icon",
};

function serveInterface(): void {
  protocol.handle(SCHEME, async (request) => {
    const url = new URL(request.url);
    const relative = decodeURIComponent(url.pathname);
    const wanted = relative === "/" || relative === "" ? "index.html" : relative.replace(/^\/+/, "");
    const file = normalize(join(UI_DIST, wanted));
    if (!file.startsWith(normalize(UI_DIST))) return new Response("forbidden", { status: 403 });
    if (!existsSync(file)) return new Response(`not found: ${wanted}`, { status: 404 });
    const answer = await net.fetch(pathToFileURL(file).toString());
    const type = MIME[extname(file).toLowerCase()];
    if (!type) return answer;
    const headers = new Headers(answer.headers);
    headers.set("Content-Type", type);
    return new Response(answer.body, { status: answer.status, headers });
  });
}

function createWindow(): BrowserWindow {
  const created = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: "#101314",
    title: "SOLVIA",
    show: !SMOKE,
    webPreferences: {
      preload: join(HERE, "preload.cjs"),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
    },
  });
  void created.loadURL(`${ORIGIN}/index.html${ROUTE ? `#${ROUTE.replace(/^#/, "")}` : ""}`);
  created.on("closed", () => {
    window = null;
  });
  return created;
}

// ---- the bridge's other side --------------------------------------------------------------------

/** The notices generated for this build (XC-025): beside the other resources when packaged, in
 *  build/notices in development if the generator has run, otherwise nothing - never a substitute. */
function readNotices(): unknown {
  const file = PACKAGED ? join(process.resourcesPath, "notices.json") : join(ROOT, "build", "notices", "notices.json");
  if (!existsSync(file)) return null;
  try {
    return JSON.parse(readFileSync(file, "utf-8"));
  } catch (error) {
    note(`shell: notices.json could not be read: ${error instanceof Error ? error.message : String(error)}`);
    return null;
  }
}

function registerBridge(): void {
  ipcMain.handle("notices", () => readNotices());
  ipcMain.handle("app:orphans", () => orphans);
  ipcMain.handle("app:removeOrphans", (_event, ids: unknown) => {
    const wanted = Array.isArray(ids) ? ids.filter((one): one is string => typeof one === "string") : [];
    const removed = removeOrphans(transientRoot(), wanted);
    orphans = findOrphans(transientRoot());
    return removed;
  });
  ipcMain.handle("engine:connection", () => engine?.connection ?? null);
  ipcMain.handle("engine:status", (): EngineProcessStatus => {
    return (
      engine?.status() ?? {
        state: "starting",
        pid: null,
        since: new Date().toISOString(),
        exitCode: null,
        signal: null,
        reason: null,
      }
    );
  });
  ipcMain.handle("engine:restart", async (): Promise<EngineProcessStatus> => {
    if (engine) await engine.stop();
    const restarted = await start(engineDirectory());
    return restarted.status();
  });
  ipcMain.handle("dialog:openWorkspace", async () => {
    const chosen = await dialog.showOpenDialog({
      title: "ワークスペースを開く",
      properties: ["openFile"],
      filters: [
        { name: "SOLVIA ワークスペース", extensions: ["svw"] },
        { name: "すべてのファイル", extensions: ["*"] },
      ],
    });
    return chosen.canceled ? null : chosen.filePaths[0] ?? null;
  });
  ipcMain.handle("dialog:openResult", async () => {
    const chosen = await dialog.showOpenDialog({
      title: "結果ファイルを開く",
      properties: ["openFile"],
      filters: [
        { name: "解析結果（読める三形式、XC-257）", extensions: ["vtu", "ex2", "cgns"] },
        { name: "すべてのファイル", extensions: ["*"] },
      ],
    });
    return chosen.canceled ? null : chosen.filePaths[0] ?? null;
  });
  ipcMain.handle("dialog:saveReport", async (_event, suggestedName: unknown) => {
    const name = typeof suggestedName === "string" && suggestedName ? suggestedName : "report.html";
    const chosen = await dialog.showSaveDialog({
      title: "成果物を書き出す",
      defaultPath: name.endsWith(".html") ? name : `${name}.html`,
      filters: [{ name: "自己完結 HTML", extensions: ["html"] }],
    });
    return chosen.canceled ? null : chosen.filePath ?? null;
  });
}

// ---- lifetime -------------------------------------------------------------------------------------

app.on("second-instance", () => {
  if (window) {
    if (window.isMinimized()) window.restore();
    window.focus();
  }
});

app.on("before-quit", (event) => {
  if (stopping) return;
  event.preventDefault();
  stopping = true;
  // The interface gets the chance to save first, bounded: a quit that waits forever on a renderer
  // that will not answer is a hang, and a quit that does not wait loses what a crash would have.
  const windows = BrowserWindow.getAllWindows();
  const waitForSave = new Promise<void>((resolve) => {
    if (windows.length === 0 || !engine || engine.status().state !== "running") {
      resolve();
      return;
    }
    const timer = setTimeout(resolve, 3_000);
    ipcMain.once("app:quit-ready", () => {
      clearTimeout(timer);
      resolve();
    });
    for (const each of windows) each.webContents.send("app:will-quit");
  });
  void waitForSave
    .then(() => (engine && engine.status().state !== "exited" ? engine.stop() : Promise.resolve(null)))
    .then(() => app.quit());
});

app.on("window-all-closed", () => {
  app.quit();
});

async function smoke(): Promise<number> {
  const summary: Record<string, unknown> = {
    packaged: PACKAGED,
    route: ROUTE || null,
    transientRoot: transientRoot(),
    engine: PACKAGED ? packagedEngine(process.resourcesPath).command : `${PYTHON} -m service.transport`,
    version: app.getVersion(),
  };
  const directory = engineDirectory();
  mkdirSync(directory, { recursive: true });
  try {
    // A session left by a shell that is gone: planted with a pid nothing runs under, found at
    // start, removed on the word this smoke stands in for (#313).
    const planted = sessionDirectory(transientRoot(), 2147483646);
    mkdirSync(planted, { recursive: true });
    writeFileSync(join(planted, "connection.json"), "{}");
    orphans = findOrphans(transientRoot());
    const removed = removeOrphans(transientRoot(), orphans.map((one) => one.id));
    summary.orphans = {
      found: orphans.map((one) => ({ id: one.id, files: one.files })),
      removed: removed.map((one) => one.id),
      remaining: findOrphans(transientRoot()).length,
      currentSessionKept: existsSync(directory),
    };

    const first = await start(directory);
    // From this process's own start to the engine answering /health: what a person waits for after
    // the icon is clicked, less the window itself (#307).
    summary.started = {
      pid: first.status().pid,
      protocol: first.connection?.protocol ?? null,
      afterMs: Math.round(process.uptime() * 1000),
    };

    // A crash, as a crash would arrive: the process is gone and 'exit' says so (E-200).
    const crashed = new Promise<EngineProcessStatus>((resolveStatus) => {
      first.onStatus((status) => {
        if (status.state === "exited") resolveStatus(status);
      });
    });
    first.child.kill("SIGKILL");
    const seen = await Promise.race([crashed, new Promise<null>((r) => setTimeout(() => r(null), 10_000))]);
    summary.crashDetected = seen
      ? { exitCode: seen.exitCode, signal: seen.signal, reason: seen.reason, connectionAfter: first.connection }
      : "NOT DETECTED within 10 s";

    const second = await start(directory);
    summary.restarted = { pid: second.status().pid, differentPid: second.status().pid !== first.status().pid };

    if (CAPTURE) {
      // So the picture shows the choice: one more dead session, planted after the check above and
      // left for the window to report. The smoke's root is removed at the end either way.
      const shown = sessionDirectory(transientRoot(), 2147483645);
      mkdirSync(shown, { recursive: true });
      writeFileSync(join(shown, "scratch.bin"), Buffer.alloc(4096));
      orphans = findOrphans(transientRoot());
      serveInterface();
      registerBridge();
      window = createWindow();
      await new Promise<void>((done) => window?.webContents.once("did-finish-load", () => done()));
      await new Promise((r) => setTimeout(r, 4_000));
      const image = await window.webContents.capturePage();
      writeFileSync(CAPTURE, image.toPNG());
      summary.captured = { path: CAPTURE, size: image.getSize() };
    }

    const stopped = await second.stop();
    summary.stopped = { state: stopped.state, exitCode: stopped.exitCode, signal: stopped.signal };
    summary.connectionFileAfterStop = existsSync(join(directory, "connection.json"));
    summary.ok = Boolean(seen) && summary.connectionFileAfterStop === false;
  } catch (error) {
    summary.error = error instanceof Error ? error.message : String(error);
    summary.ok = false;
  }
  summary.tokenInLog = log.some((line) => engine?.connection?.token && line.includes(engine.connection.token));
  // The smoke's own transient root goes with it: the leftovers it used to keep were the first
  // orphans this product measured (E-208).
  rmSync(transientRoot(), { recursive: true, force: true });
  summary.transientRootRemoved = !existsSync(transientRoot());
  summary.ok = summary.ok === true && summary.transientRootRemoved === true
    && (summary.orphans as { removed: string[]; remaining: number }).removed.length === 1
    && (summary.orphans as { remaining: number }).remaining === 0;
  process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
  return summary.ok === true ? 0 : 1;
}

void app.whenReady().then(async () => {
  if (SMOKE) {
    const code = await smoke();
    app.exit(code);
    return;
  }
  serveInterface();
  registerBridge();
  orphans = findOrphans(transientRoot());
  window = createWindow();
  try {
    await start(engineDirectory());
  } catch (error) {
    // The interface hears about it through the status the failure set; nothing is thrown at a
    // person. The window is already open and says "エンジン停止" with the reason.
    note(`shell: ${error instanceof Error ? error.message : String(error)}`);
  }
});
