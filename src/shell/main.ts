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
import { app, BrowserWindow, dialog, ipcMain, net, powerMonitor, protocol, screen } from "electron";
import { appendFileSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import type { EngineProcessStatus } from "../ui/client/shell";
import { offsetMinutesAt, offsetText, recordNow } from "../ui/client/time.js";
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
import { layoutUnder, type ProfileLayout } from "./profile.js";
import { clear, forget, readRecent, remember } from "./recent.js";

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
const levelIndex = argv.indexOf("--log-level");
const LOG_LEVEL = (levelIndex >= 0 ? argv[levelIndex + 1] : undefined) as "debug" | "info" | "warning" | "error" | undefined;
// `--measure-launch` prints the launch timeline as one JSON line once the engine is running and the
// interface has loaded, then quits: what spike/measure_launch.py reads (#307). `--profile <dir>`
// keeps a launch out of the person's profile, for that measurement and for a test.
const MEASURE_LAUNCH = argv.includes("--measure-launch");
const profileIndex = argv.indexOf("--profile");
const PROFILE = profileIndex >= 0 ? argv[profileIndex + 1] ?? null : null;
if (PROFILE) app.setPath("userData", resolve(PROFILE));

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

/** The zone the shell stands in, named beside every UTC stamp it writes (XC-142): `UTC+09:00`. */
function zoneOfNow(): string {
  return offsetText(offsetMinutesAt());
}

const SHELL_LOG_MAX_BYTES = 1_000_000;

function note(line: string): void {
  log.push(line);
  if (log.length > 500) log.shift();
  // The shell's own notes, to disk beside the engine's log, capped the simple way: past the cap the
  // file is moved to `.1` and a new one begun. The engine's log is the one with levels and retention.
  try {
    const directory = logDirectory();
    mkdirSync(directory, { recursive: true });
    const file = join(directory, "shell.log");
    if (existsSync(file) && statSync(file).size > SHELL_LOG_MAX_BYTES) renameSync(file, join(directory, "shell.log.1"));
    appendFileSync(file, `${new Date().toISOString()} ${zoneOfNow()} ${line}\n`);
  } catch {
    /* a note that cannot be written is not a reason to stop */
  }
}

function broadcast(status: EngineProcessStatus): void {
  for (const each of BrowserWindow.getAllWindows()) each.webContents.send("engine:status", status);
}

/** What a laptop does to a window, noted and passed on (XC-310): sleep and resume through the power
 *  monitor; a display added, removed or changed in its metrics - its scale among them - through the
 *  screen module; a child process of Chromium's gone, the GPU process among them. A resume
 *  re-announces the engine's status, so the interface checks its connection and draws again rather
 *  than waiting for a click to find out. Nothing here restarts anything: the engine's own exit
 *  arrives as its own status, and the interface offers the restart (XC-259). */
function watchTheMachine(): void {
  powerMonitor.on("suspend", () => note("power: suspend"));
  powerMonitor.on("resume", () => {
    note("power: resume");
    if (engine) broadcast(engine.status());
  });
  screen.on("display-metrics-changed", (_event, display, changed) => {
    note(`display ${display.id}: ${changed.join(", ")} changed; scale ${display.scaleFactor}, ${display.size.width}x${display.size.height}`);
  });
  screen.on("display-added", (_event, display) => note(`display ${display.id} added: scale ${display.scaleFactor}, ${display.size.width}x${display.size.height}`));
  screen.on("display-removed", (_event, display) => note(`display ${display.id} removed`));
  app.on("child-process-gone", (_event, details) => {
    note(`child process gone: ${details.type} (${details.reason}${details.exitCode === undefined ? "" : `, exit ${details.exitCode}`})`);
  });
}

/** The launch as this process saw it, in milliseconds after its own start (#307, XC-304): the
 *  window created, the interface loaded, the engine reachable - or the start failed, and why.
 *  Written to the shell's notes at every launch, so a slow machine's number is on that machine;
 *  and, under `--measure-launch`, printed as one JSON line before the shell quits itself. */
const launch: { windowCreatedMs?: number; interfaceLoadedMs?: number; engineReadyMs?: number; engineFailed?: string } = {};

function uptimeMs(): number {
  return Math.round(process.uptime() * 1000);
}

function launchSettled(): void {
  if (launch.windowCreatedMs === undefined || launch.interfaceLoadedMs === undefined) return;
  if (launch.engineReadyMs === undefined && launch.engineFailed === undefined) return;
  const engine = launch.engineReadyMs !== undefined ? `engine ${launch.engineReadyMs} ms` : `engine failed (${launch.engineFailed})`;
  note(`startup: window ${launch.windowCreatedMs} ms, interface ${launch.interfaceLoadedMs} ms, ${engine} after the shell's start`);
  if (MEASURE_LAUNCH) {
    process.stdout.write(JSON.stringify({ ...launch, packaged: PACKAGED }) + "\n");
    setTimeout(() => app.quit(), 200);
  }
}

/** What the shell keeps under its profile, laid out by `profile.ts` so the arrangement is one a
 *  test holds to (XC-300): the engine's transient root, the log directory, and the recent list
 *  beside them. The smoke stands in a root of its own under temp and removes it whole. */
function layout(): ProfileLayout {
  return layoutUnder(SMOKE ? join(app.getPath("temp"), `solvia-smoke-${process.pid}`) : app.getPath("userData"));
}

/** Where logs go: the engine's diagnostic log and the shell's own notes, beside each other, in a
 *  directory a person can open (XC-263). */
function logDirectory(): string {
  return layout().logDirectory;
}

async function start(directory: string): Promise<Engine> {
  const started = await startEngine({
    ...(PACKAGED ? packagedEngine(process.resourcesPath) : developmentEngine(PYTHON, ROOT)),
    directory,
    logDirectory: logDirectory(),
    logLevel: LOG_LEVEL,
    allowOrigin: ORIGIN,
    onStatus: broadcast,
    output: note,
  });
  engine = started;
  return started;
}

/** The root of everything transient (XC-262): the engine's session directories live under it, and
 *  nothing transient lives anywhere else. The smoke's is under its own root and goes with it when
 *  it is done - the smoke's own leftovers were the first orphans measured (E-208). */
function transientRoot(): string {
  return layout().engineRoot;
}

function engineDirectory(): string {
  return sessionDirectory(transientRoot());
}

/** The recent-workspace list, under the profile beside the engine's root and the logs and inside
 *  neither (XC-297, XC-300): it is the shell's own, it outlives every session, and nothing the
 *  engine is told about contains it. */
function recentFile(): string {
  return layout().recentFile;
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
        since: recordNow(),
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
  ipcMain.handle("dialog:saveWorkspace", async (_event, suggestedName: unknown) => {
    const name = typeof suggestedName === "string" && suggestedName ? suggestedName : "workspace.svw";
    if (SMOKE) {
      // No person to answer a dialog: the sample goes under the smoke's own root, which goes with it.
      const chosen = join(transientRoot(), "smoke-sample", name.endsWith(".svw") ? name : `${name}.svw`);
      mkdirSync(join(transientRoot(), "smoke-sample"), { recursive: true });
      return chosen;
    }
    const chosen = await dialog.showSaveDialog({
      title: "新しいワークスペースを作る",
      defaultPath: name.endsWith(".svw") ? name : `${name}.svw`,
      filters: [{ name: "SOLVIA ワークスペース", extensions: ["svw"] }],
    });
    return chosen.canceled ? null : chosen.filePath ?? null;
  });
  ipcMain.handle("recent:list", () => readRecent(recentFile()));
  ipcMain.handle("recent:remember", (_event, entry: unknown) => {
    // What the interface hands over is checked by shape: the bridge is not a place to trust a value.
    if (typeof entry !== "object" || entry === null) return readRecent(recentFile());
    const one = entry as { path?: unknown; name?: unknown; tags?: unknown; openedAt?: unknown };
    if (typeof one.path !== "string" || typeof one.name !== "string" || !Array.isArray(one.tags) || typeof one.openedAt !== "object" || one.openedAt === null) {
      return readRecent(recentFile());
    }
    return remember(recentFile(), {
      path: one.path,
      name: one.name,
      tags: one.tags.filter((tag): tag is string => typeof tag === "string"),
      openedAt: one.openedAt as { utc: string; offsetMinutes: number | null },
    });
  });
  ipcMain.handle("recent:forget", (_event, path: unknown) => (typeof path === "string" ? forget(recentFile(), path) : readRecent(recentFile())));
  // The whole list, on the person's word (XC-300): the interface asks twice, the shell empties once.
  ipcMain.handle("recent:clear", () => clear(recentFile()));
  ipcMain.handle("dialog:saveSupportBundle", async (_event, suggestedName: unknown) => {
    const name = typeof suggestedName === "string" && suggestedName ? suggestedName : "solvia-support.zip";
    const chosen = await dialog.showSaveDialog({
      title: "診断情報を保存する",
      defaultPath: name.endsWith(".zip") ? name : `${name}.zip`,
      filters: [{ name: "診断情報（zip）", extensions: ["zip"] }],
    });
    return chosen.canceled ? null : chosen.filePath ?? null;
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

/** What the interface shows in its viewport: whether a drawn frame is there, its own pixels, the
 *  size it is shown at, and the page's devicePixelRatio. */
interface Picture {
  present: boolean;
  natural: [number, number];
  shown: [number, number];
  dpr: number;
}

async function picture(contents: Electron.WebContents): Promise<Picture> {
  return contents.executeJavaScript(`(() => {
    const img = document.querySelector(".viewport-pane img");
    const box = img ? img.getBoundingClientRect() : null;
    return {
      present: Boolean(img && img.naturalWidth > 0),
      natural: img ? [img.naturalWidth, img.naturalHeight] : [0, 0],
      shown: box ? [Math.round(box.width), Math.round(box.height)] : [0, 0],
      dpr: window.devicePixelRatio,
    };
  })()`) as Promise<Picture>;
}

async function pictureWithin(contents: Electron.WebContents, deadlineMs: number): Promise<Picture> {
  const started = Date.now();
  let seen = await picture(contents);
  while (!seen.present && Date.now() - started < deadlineMs) {
    await new Promise((r) => setTimeout(r, 500));
    seen = await picture(contents);
  }
  return seen;
}

/** The home screen's own button, pressed as a person presses it: the sample is written where the
 *  save dialog answers and opened, and the View draws it. Waited for, because the button is there
 *  once the engine's status has reached the page. */
async function openTheSample(contents: Electron.WebContents, deadlineMs: number): Promise<boolean> {
  const started = Date.now();
  while (Date.now() - started < deadlineMs) {
    const pressed = (await contents.executeJavaScript(`(() => {
      const button = [...document.querySelectorAll("button")].find((one) => (one.textContent || "").trim() === "サンプルを開く");
      if (!button || button.disabled) return false;
      button.click();
      return true;
    })()`)) as boolean;
    if (pressed) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

/** The measurement of XC-310 (E-229): the sample opened, a frame drawn, the zoom raised, a resume
 *  announced, the picture looked for after each. */
async function pictureThrough(contents: Electron.WebContents): Promise<Record<string, unknown>> {
  const sampleOpened = await openTheSample(contents, 30_000);
  const first = await pictureWithin(contents, 60_000);
  contents.setZoomFactor(1.5);
  await new Promise((r) => setTimeout(r, 1_500));
  const zoomed = await pictureWithin(contents, 10_000);
  powerMonitor.emit("resume");
  await new Promise((r) => setTimeout(r, 3_000));
  const resumed = await pictureWithin(contents, 10_000);
  contents.setZoomFactor(1);
  const resumeNoted = log.some((line) => line.includes("power: resume"));
  return {
    sampleOpened, first, zoomed, resumed, resumeNoted,
    ok: sampleOpened && first.present && zoomed.present && resumed.present && zoomed.dpr > first.dpr && resumeNoted,
  };
}

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

    if (existsSync(join(UI_DIST, "index.html"))) {
      if (CAPTURE) {
        // So the picture shows the choice: one more dead session, planted after the check above and
        // left for the window to report. The smoke's root is removed at the end either way.
        const shown = sessionDirectory(transientRoot(), 2147483645);
        mkdirSync(shown, { recursive: true });
        writeFileSync(join(shown, "scratch.bin"), Buffer.alloc(4096));
        orphans = findOrphans(transientRoot());
      }
      serveInterface();
      registerBridge();
      window = createWindow();
      await new Promise<void>((done) => window?.webContents.once("did-finish-load", () => done()));
      // The picture through what a laptop does to a window (XC-310, E-229): the interface opens on
      // the sample and draws a frame; the zoom factor - Chromium's devicePixelRatio, what a display
      // of another scale changes - is raised; a resume is announced as the power monitor would; and
      // the picture is looked for after each. What is recorded is the frame's own size against
      // the size it is shown at, so a scaled display is seen to scale the showing and not the frame.
      summary.display = await pictureThrough(window.webContents);
      if (CAPTURE) {
        await new Promise((r) => setTimeout(r, 1_000));
        const image = await window.webContents.capturePage();
        writeFileSync(CAPTURE, image.toPNG());
        summary.captured = { path: CAPTURE, size: image.getSize() };
      }
    } else {
      summary.display = "the interface is not built beside this shell; the picture through a zoom and a resume is measured where it is";
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
  // The engine's diagnostic log exists where the shell said, and never holds the token either.
  const engineLog = join(logDirectory(), "solvia.log");
  const logText = existsSync(engineLog) ? readFileSync(engineLog, "utf-8") : "";
  summary.diagnosticLog = {
    exists: existsSync(engineLog),
    lines: logText ? logText.trim().split("\n").length : 0,
    startsAndStops: (logText.match(/"engine\.(start|stop)"/g) ?? []).length,
    tokenInLog: Boolean(engine?.connection?.token && logText.includes(engine.connection.token)),
  };
  // The smoke's own root - engine sessions, logs and list alike - goes with it: the leftovers it
  // used to keep were the first orphans this product measured (E-208). Guarded on the flag rather
  // than on this function being the smoke, because the root outside the smoke is the profile.
  if (SMOKE) rmSync(layout().root, { recursive: true, force: true });
  summary.transientRootRemoved = !existsSync(transientRoot());
  summary.ok = summary.ok === true && summary.transientRootRemoved === true
    && (summary.orphans as { removed: string[]; remaining: number }).removed.length === 1
    && (summary.orphans as { remaining: number }).remaining === 0
    && (typeof summary.display === "string" || (summary.display as { ok: boolean }).ok === true);
  process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
  return summary.ok === true ? 0 : 1;
}

void app.whenReady().then(async () => {
  watchTheMachine();
  if (SMOKE) {
    const code = await smoke();
    app.exit(code);
    return;
  }
  serveInterface();
  registerBridge();
  orphans = findOrphans(transientRoot());
  // The window first, so the person sees the product and what it is waiting for (XC-304); the
  // interface shows the engine starting until the status says it is running.
  window = createWindow();
  launch.windowCreatedMs = uptimeMs();
  window.webContents.once("did-finish-load", () => {
    launch.interfaceLoadedMs = uptimeMs();
    launchSettled();
  });
  try {
    await start(engineDirectory());
    launch.engineReadyMs = uptimeMs();
  } catch (error) {
    // The interface hears about it through the status the failure set; nothing is thrown at a
    // person. The window is already open and says why, with a way to start again.
    launch.engineFailed = error instanceof Error ? error.message : String(error);
    note(`shell: ${launch.engineFailed}`);
  }
  launchSettled();
});
