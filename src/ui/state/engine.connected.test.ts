/* The interface's half of the prototype thread, against a real engine, in CI.
 *
 * XC-257 defines the prototype as a thread a person walks: open, colour, orbit, pick, declare a unit,
 * export. The engine's half is under pytest. The interface's half was walked by hand in a browser -
 * which is evidence for one afternoon and a gate for nothing. This starts the engine the way the
 * shell would (`python -m service.transport`), drives `engineState` through the same steps, and
 * checks what the screen would show against what the file holds.
 *
 * No browser: the store is the interface's model of the engine and computes nothing, so what it
 * holds after each step is what a screen would render. What this does NOT check is the rendering of
 * those values into pixels - `validate/check_interface_states.py` sweeps the design states, and the
 * connected screens are still judged by a person.
 */
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, beforeAll, describe, expect, test } from "vitest";

import { OPERATIONS, PROTOCOL_VERSION, type Connection } from "../client/engine";
import { commandGroups } from "../logic/commands";
import { paletteRows } from "../logic/palette";
import { informationOf } from "../logic/information";
import { absentParts, visibilityAfter } from "../logic/parts";
import { moveBlock } from "../logic/report";
import { viewFooter } from "../logic/showing";
import { HEADER, probeRows, statisticsRows, tsv } from "../logic/copy";
import { engineState, FRAME, snapshot } from "./engine";

const ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const PYTHON = process.env.SOLVIA_PYTHON ?? "python";
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47]);

let directory: string;
let engine: ChildProcess | null = null;
let connection: Connection;
let workspacePath: string;
let cubePath: string;
let partialPath: string | null = null;
let engineOutput = "";

async function until(what: () => boolean, ms: number, name: string): Promise<void> {
  const started = Date.now();
  while (!what()) {
    if (Date.now() - started > ms) throw new Error(`${name} did not happen within ${ms} ms\n${engineOutput}`);
    await new Promise((r) => setTimeout(r, 200));
  }
}

beforeAll(async () => {
  directory = mkdtempSync(join(tmpdir(), "solvia-connected-"));

  // The demo case, from the one definition the Python tests also use.
  const written = spawnSync(PYTHON, [join(ROOT, "tests", "demo_case.py"), join(directory, "demo")], {
    cwd: ROOT,
    encoding: "utf-8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  if (written.status !== 0) throw new Error(`demo case not written:\n${written.stderr}`);
  const paths = JSON.parse(written.stdout.trim()) as { workspace: string; cube: string; partial: string | null };
  workspacePath = paths.workspace;
  cubePath = paths.cube;
  partialPath = paths.partial;

  // The engine, started the way a shell starts it: loopback, a port the OS chooses, the token in a
  // file the shell reads and nowhere else (XC-258).
  const runDirectory = join(directory, "run");
  engine = spawn(PYTHON, ["-m", "service.transport", "--connection-directory", runDirectory], {
    cwd: ROOT,
    env: { ...process.env, PYTHONPATH: join(ROOT, "src"), PYTHONIOENCODING: "utf-8" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  engine.stdout?.on("data", (chunk: Buffer) => (engineOutput += chunk.toString()));
  engine.stderr?.on("data", (chunk: Buffer) => (engineOutput += chunk.toString()));
  const connectionFile = join(runDirectory, "connection.json");
  await until(() => existsSync(connectionFile), 90_000, "the connection file");
  connection = JSON.parse(readFileSync(connectionFile, "utf-8")) as Connection;
  expect(engineOutput).not.toContain(connection.token);
}, 120_000);

afterAll(() => {
  engine?.kill();
  engineState.disconnect();
  rmSync(directory, { recursive: true, force: true });
});

// The camera a person kept, to be found again after the engine is restarted (XC-274).
let kept: ReturnType<typeof snapshot>["savedCamera"] = null;

describe("the prototype thread from the interface's side", () => {
  test("connect: the engine is reachable and speaks the protocol this build was generated from", async () => {
    const reachability = await engineState.connect(connection);

    expect(reachability.kind).toBe("reachable");
    if (reachability.kind === "reachable") expect(reachability.protocols).toContain(PROTOCOL_VERSION);
    expect(snapshot().refusal).toBeNull();
  });

  test("a refusal is shown, not swallowed: a file that does not exist", async () => {
    expect(await engineState.openWorkspace(workspacePath)).toBe(true);

    const loaded = await engineState.loadDataset("case:1", join(directory, "nothing-here.vtu"));

    expect(loaded).toBe(false);
    expect(snapshot().refusal).toBeTruthy();
  });

  test("inspect: the support level and the gaps are stated before the file is read", async () => {
    const inspection = await engineState.inspect(cubePath);

    expect(inspection).not.toBeNull();
    expect(inspection?.format).toBe("vtu");
    expect(inspection?.exists).toBe(true);
    expect(["Verified", "Limited", "Offered"]).toContain(inspection?.supportLevel);
    expect(snapshot().inspection?.path).toBe(cubePath);
    // Nothing was loaded by looking.
    expect(snapshot().datasetId).toBeNull();

    const absent = await engineState.inspect(join(directory, "thing.unknownformat"));
    expect(absent?.supportLevel).toBe("Absent");
    expect(absent?.exists).toBe(false);
  });

  test("open: the file is read and its field arrives with no unit, because none was declared", async () => {
    const loaded = await engineState.loadDataset("case:1", cubePath);

    expect(loaded).toBe(true);
    const s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.sourceName).toBe("cube.vtu");
    expect(s.fields).toEqual([{ name: "temperature", association: "point", unit: null }]);
    expect(s.fieldName).toBe("temperature");
    expect(s.bounds).toEqual([
      [0, 0, 0],
      [1, 1, 1],
    ]);
  });

  test("information: what the file holds is on the screen from the engine's answers, and what the contract does not carry is named (XC-273)", async () => {
    const s = snapshot();
    expect(s.described?.pointCount).toBe(8);
    expect(s.described?.cellCount).toBe(1);
    expect(s.parts?.map((one) => one.type)).toEqual(["part"]);
    // The file's own hierarchy, as a path: one step for a flat file, and no parent (INV-019).
    expect(s.parts?.[0]?.path).toEqual(["cube"]);
    expect(s.parts?.[0]?.parentId).toBeUndefined();

    const view = informationOf(s);

    expect(view?.file.name).toBe("cube.vtu");
    expect(view?.file.supportLabel).toBe("検証済み");
    expect(view?.structure?.points).toBe(8);
    expect(view?.structure?.bounds?.map((one) => one.axis)).toEqual(["X", "Y", "Z"]);
    expect(view?.fields.map((one) => one.name)).toEqual(["temperature"]);
    expect(view?.fields[0]?.unit).toBeNull();
    expect(view?.axis?.kind).toBe("none");
    expect(view?.notAnswered.length).toBeGreaterThan(0);
  });

  test("footer: what the area shows and why it may be incomplete, every clause from the store (XC-276)", async () => {
    const footer = viewFooter(snapshot(), "単位未宣言");
    expect(footer?.showing).toContain("データセット cube.vtu");
    expect(footer?.showing).toContain("場 temperature（単位未宣言）");
    // No picture yet and no unit declared: both said, nothing else - the file is whole.
    expect(footer?.incomplete).toEqual(["単位未宣言の場：temperature（換算しない・XC-003）", "絵はまだありません"]);
  });

  test("colour: a frame arrives, and the legend's numbers are the file's own at float32 digits", async () => {
    await engineState.refresh();

    const s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(s.reduced).toBe("全三角形を表示しています");
    // A statistic is `computed` even when it equals a stored value: what was done to get it is a
    // search over the dataset, and provenance names the operation, not the digits (INV-018).
    expect(s.statistics?.minimum).toMatchObject({ value: 1, digits: 6, unit: null, provenance: "computed" });
    expect(s.statistics?.maximum).toMatchObject({ value: 8, digits: 6, unit: null, provenance: "computed" });
  });

  test("the frame is a PNG of the size the pick will be asked against", async () => {
    const url = snapshot().imageUrl;
    expect(url).toBeTruthy();
    const bytes = Buffer.from(await (await fetch(url as string)).arrayBuffer());

    expect(bytes.subarray(0, 4)).toEqual(PNG_MAGIC);
    // IHDR: width and height are the two big-endian 32-bit integers after the 8-byte signature and
    // the 8-byte chunk header.
    expect(bytes.readUInt32BE(16)).toBe(FRAME.width);
    expect(bytes.readUInt32BE(20)).toBe(FRAME.height);
  });

  test("declare: the unit reaches the legend and the readout, and no stored number moves", async () => {
    const before = snapshot().statistics?.maximum?.value;

    expect(await engineState.declareUnit("temperature", "K")).toBe(true);

    const s = snapshot();
    expect(s.fields[0]?.unit).toBe("K");
    expect(s.statistics?.maximum).toMatchObject({ value: before, unit: "K" });
    expect(s.statistics?.minimum?.value).toBe(1);
    // The footer follows: the unit is on the line, and the picture is there, so nothing is missing.
    expect(viewFooter(s, "単位未宣言")?.showing).toContain("場 temperature（K）");
    expect(viewFooter(s, "単位未宣言")?.incomplete).toEqual([]);
    // The values as a spreadsheet takes them: the engine's digits, the declared unit, the provenance,
    // and the missing count as the integer it is (XC-279).
    if (!s.statistics) throw new Error("the statistics were not read");
    const copied = tsv(statisticsRows("temperature", s.statistics, { undeclared: "単位未宣言", provenance: { dataset: "データ", computed: "計算" } })).split("\n");
    expect(copied[0]).toBe(HEADER.join("\t"));
    expect(copied[1]).toMatch(/^temperature（最大）\t8\tK\t6\t/);
    expect(copied[2]).toMatch(/^temperature（最小）\t1\tK\t6\t/);
    expect(copied[3]).toMatch(/^temperature（平均）\t[0-9.]+\tK\t6\t計算\t/);
    expect(copied[4]).toMatch(/^temperature（欠損数）\t0\t件\t整数\t/);
  });

  test("pick: the pixel in the middle of the frame reads a value the file holds, with everything a number needs", async () => {
    await engineState.pick(FRAME.width / 2, FRAME.height / 2);

    const s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.probe).not.toBeNull();
    expect([1, 2, 3, 4, 5, 6, 7, 8]).toContain(s.probe?.value);
    expect(s.probe).toMatchObject({ unit: "K", digits: 6, provenance: "dataset" });
    // A node value from a file with no node numbers: the absence names the kind it lacks.
    expect(s.probeLocation).toContain("節点");
    // The part under the pixel is the selection now (view/AC-055): the outliner follows the viewport.
    expect(s.selectedPart).toBe("cube");
    // And the part's own statistics were read by its name, with the scope on the answer (XC-280):
    // the one part of a flat file has the model's numbers, and says which it covered.
    expect(s.partStatistics?.scope).toBe("パート cube");
    expect(s.partStatistics?.maximum.value).toBe(8);
    expect(s.partStatistics?.maximum.location).toContain("cube：");
    expect(s.statistics?.scope).toBe("ケース全体（1 パート）");
    // The probed value copied: the same number the readout shows, with its unit and the location.
    if (!s.probe) throw new Error("the probe was not read");
    const row = probeRows("temperature", s.probe, s.probeLocation, { undeclared: "単位未宣言", provenance: { dataset: "データ" } })[1];
    expect(row?.[0]).toBe("temperature（プローブ）");
    expect(Number(row?.[1])).toBe(s.probe.value);
    expect(row?.slice(2, 5)).toEqual(["K", "6", "データ"]);
    expect(row?.[5]).toContain("節点");
  });

  test("pick: a pixel off the model reads nothing, and says so rather than the nearest value", async () => {
    await engineState.pick(2, 2);

    const s = snapshot();
    expect(s.probe?.value).toBeNull();
    expect(s.probe?.missingBecause).toContain("モデル");
  });

  test("orbit: a drag is a new camera and a new frame, and not a document write (XC-270)", async () => {
    const before = snapshot().imageUrl;
    const writes = snapshot().journal.length;

    await engineState.orbit(35, 10);

    const s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(s.imageUrl).not.toBe(before);
    expect(s.turntable.azimuthDegrees).toBe(30 + 35);
    // Class 1: the picture changed and the document did not - no undo step, no unsaved work.
    expect(s.journal.length).toBe(writes);
    const listed = await engineState.history();
    expect(listed?.entries.at(-1)?.operation).toBe("view.render");

    // Keeping the look is the one explicit write.
    expect(await engineState.keepCamera()).toBe(true);
    expect(snapshot().journal.length).toBe(writes + 1);
    expect(snapshot().journal.at(-1)?.operation).toBe("view.update");
    expect(snapshot().savedCamera?.position_m).toHaveLength(3);
    kept = snapshot().savedCamera;
  });

  test("outliner: hiding the only part is refused by name rather than drawn empty, and showing it draws again (view/AC-055, XC-274)", async () => {
    const parts = snapshot().parts ?? [];
    await engineState.setPartVisibility(visibilityAfter(parts, {}, "cube", "toggle"));
    let s = snapshot();
    expect(s.partVisibility).toEqual({ cube: false });
    // A document write: the map went into the definition, and the engine refused to draw nothing.
    expect(s.journal.at(-1)?.operation).toBe("view.update");
    expect(s.refusal).toContain("非表示");

    await engineState.setPartVisibility(visibilityAfter(parts, s.partVisibility, "cube", "toggle"));
    s = snapshot();
    expect(s.partVisibility).toEqual({});
    expect(s.refusal).toBeNull();
    expect(s.imageUrl).toMatch(/^blob:/);
    // Isolating the one part there is shows it and hides nothing else: the minimal map again.
    expect(visibilityAfter(parts, {}, "cube", "isolate")).toEqual({});
  });

  test("a write the engine applied is unsaved work until the document is saved", async () => {
    // K was declared above and never saved: it is in the journal - beside the view writes that
    // colouring and keeping a look made, which are document writes; orbiting is not (XC-270).
    const operations = snapshot().journal.map((one) => one.operation);
    expect(operations).toContain("field.declareUnit");
    expect(operations).toContain("view.update");

    expect(await engineState.save()).toBe(true);

    expect(snapshot().journal).toEqual([]);
    expect(snapshot().savedAt).not.toBeNull();
  });

  test("history: the engine's record lists what was asked, each time as the pair, nothing dropped yet", async () => {
    const history = await engineState.history();

    expect(history).not.toBeNull();
    const s = snapshot();
    expect(s.history?.entries.length).toBeGreaterThan(0);
    for (const entry of s.history?.entries ?? []) {
      expect(entry.at.utc).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
      expect(typeof entry.at.offsetMinutes).toBe("number");
    }
    expect(s.history?.entries.map((one) => one.operation)).toContain("field.declareUnit");
    expect(s.history?.undoDropped ?? 0).toBe(0);
    expect(s.history?.omitted ?? 0).toBe(0);
    // What the interface itself recorded is the same two facts (XC-266): the save the step before
    // made, and any write since it.
    const own = [...(s.savedAt ? [s.savedAt] : []), ...s.journal.map((one) => one.at)];
    expect(own.length).toBeGreaterThan(0);
    for (const at of own) {
      expect(at.utc).toMatch(/Z$/);
      expect(typeof at.offsetMinutes).toBe("number");
    }
  });

  test("nothing has left, and it says so as a record: capabilities and an empty audit (XC-267)", async () => {
    const capabilities = await engineState.capabilities();

    expect(capabilities?.egress?.transportConfigured).toBe(false);
    expect(capabilities?.egress?.hosts).toEqual([]);
    expect(capabilities?.egress?.auditEntries).toBe(0);
    expect(await engineState.audit()).toEqual({ entries: [] });
  });

  test("commands: the engine says which operations this build answers, and the list is the whole catalogue (XC-277)", async () => {
    expect(await engineState.operations()).not.toBeNull();

    const s = snapshot();
    expect(s.operations?.registered).toContain("system.operations");
    expect(s.operations?.registered.length).toBe(27);
    expect([...(s.operations?.registered ?? []), ...(s.operations?.unimplemented ?? [])].sort()).toEqual([...OPERATIONS].sort());
    const rows = commandGroups(s.operations, "").flatMap((group) => group.rows);
    expect(rows).toHaveLength(OPERATIONS.length);
    expect(rows.find((row) => row.operation === "dataset.load")).toMatchObject({ writes: true, parameters: "caseId、filePaths", status: "answers" });
    expect(rows.find((row) => row.operation === "graph.data")?.status).toBe("unimplemented");
  });

  test("palette: what this screen can run is what its context supplies, a run answers as the engine did, and a refusal comes back as a reason (XC-278)", async () => {
    const s = snapshot();
    const rows = paletteRows(s.operations, {
      workspaceId: s.workspaceId, caseId: s.caseId, datasetId: s.datasetId, viewId: s.viewId, reportId: s.reportId, fieldName: s.fieldName,
    }, "");
    const runnable = rows.filter((row) => row.runnable).map((row) => row.operation);
    expect(runnable).toEqual(expect.arrayContaining(["dataset.describe", "dataset.parts", "field.statistics", "view.get", "history.list", "system.capabilities"]));
    expect(runnable).not.toContain("view.render");
    expect(runnable).not.toContain("output.prune");
    expect(rows.find((row) => row.operation === "view.render")?.because).toContain("width");
    expect(rows.find((row) => row.operation === "output.prune")?.because).toContain("確認");
    expect(rows.find((row) => row.operation === "graph.data")?.because).toContain("実装なし");

    const described = await engineState.run("dataset.describe", { datasetId: s.datasetId });
    expect(described.status).toBe("answered");
    expect((described.result as { pointCount?: number }).pointCount).toBe(8);
    const refused = await engineState.run("report.get", { reportId: "report:none" });
    expect(refused.status).toBe("refused");
    expect(refused.reason).toContain("report:none");
    // The reason stayed with the palette: the window's own refusal is as it was.
    expect(snapshot().refusal).toBeNull();
  });

  test("output: the demo workspace has no runs, and the answer is an empty list with the limit beside it (XC-141)", async () => {
    const listing = await engineState.outputList();

    expect(listing?.runs).toEqual([]);
    expect(listing?.totalBytes).toBe(0);
    expect(listing?.overLimit).toBe(false);
    expect(listing?.suggestedRunIds).toEqual([]);
    expect(listing?.limitBytes).toBeGreaterThan(0);

    // A run that is not there is refused by name, and the refusal is where a person reads it.
    expect(await engineState.outputPlan(["report-a/nope"])).toBeNull();
    expect(snapshot().refusal).toContain("report-a/nope");
    engineState.clearRefusal();
  });

  test("export: a self-contained document with the picture, the unit and the maximum, of the size it says", async () => {
    const target = join(directory, "from-the-interface.html");

    const done = await engineState.exportReport(target);

    expect(done).not.toBeNull();
    expect(snapshot().refusal).toBeNull();
    expect(statSync(target).size).toBe(done?.bytes);
    const html = readFileSync(target, "utf-8");
    expect(html).toContain("data:image/png;base64,");
    expect(html).toContain("静止画");
    expect(html).toContain("cube.vtu");
    expect(html).toContain(">8<");
    expect(html).toContain("K");
    const withoutData = html.replace(/data:image[^"]+/g, "");
    expect(withoutData).not.toMatch(/https?:\/\//);
  });

  test("report: the document's report is read back with its blocks and revision, a move is one write, the trust content is the engine's, and a second export writes the same report (XC-275)", async () => {
    await engineState.refreshReport();
    let s = snapshot();
    expect(s.reportId).not.toBeNull();
    expect(s.report?.blocks.map((one) => one.kind)).toEqual(["view", "valueTable"]);
    expect(s.reportRevision).toBe(1);
    expect(s.provenance?.sources[0]?.path.endsWith("cube.vtu")).toBe(true);
    expect(s.provenance?.declaredUnits).toEqual({ temperature: "K" });
    expect(s.provenance?.caseIds).toEqual(["case:1"]);
    expect(s.provenanceRefusal).toBeNull();

    const report = s.report;
    if (!report) throw new Error("the report was not read back");
    const before = s.journal.length;
    expect(await engineState.updateReport({ ...report, blocks: moveBlock(report.blocks, 0, 1) })).toBe(true);
    s = snapshot();
    expect(s.journal.length).toBe(before + 1);
    expect(s.journal.at(-1)?.operation).toBe("report.update");
    expect(s.reportRevision).toBe(2);
    expect(s.report?.blocks.map((one) => one.kind)).toEqual(["valueTable", "view"]);

    // The same report again, at another path: until 2026-09-20 every export made a report under
    // the dataset's name, and the second was refused as a name the document already held (AC-030).
    const again = join(directory, "from-the-interface-again.html");
    expect(await engineState.exportReport(again)).not.toBeNull();
    expect(snapshot().exported?.path).toBe(again);
    expect(snapshot().refusal).toBeNull();
    // Saved, so that the restart below finds the report in the document rather than making one.
    expect(await engineState.save()).toBe(true);
  });

  test("a case the reader could only partly read opens as partial, keeps the mark and names what is missing (AC-027)", async () => {
    if (!partialPath) throw new Error("the partial fixture was not written: h5py is missing from the engine environment");

    expect(await engineState.loadDataset("case:1", partialPath)).toBe(true);

    const s = snapshot();
    expect(s.partial).toBe(true);
    // The absence with its reason, as the logic layer says it from the engine's three facts.
    expect(absentParts(s.parts).some((one) => one.includes("Ghost") && one.includes("要素なし"))).toBe(true);
    expect(s.parts?.find((one) => one.type === "absent")?.path).toEqual(["assembly", "Base", "Ghost"]);
    expect(viewFooter(s, "単位未宣言")?.incomplete.some((one) => one.includes("不完全なケース") && one.includes("Ghost"))).toBe(true);
    expect(s.warnings.some((one) => one.includes("不完全"))).toBe(true);
    expect(s.fields.map((one) => one.name)).toContain("stress");
    engineState.clearWarnings();

    // The thread goes on with the cube: a second dataset in the case would reach every report
    // drawn over the session's datasets, and a partial one is refused there by design (AC-004).
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    expect(snapshot().partial).toBe(false);
    await engineState.refresh();
    expect(snapshot().refusal).toBeNull();
    expect(snapshot().imageUrl).toMatch(/^blob:/);
  });
});

describe("when the engine ends", () => {
  test("what was saved is opened again, and what was not is listed as lost - not rebuilt", async () => {
    // A second declaration, applied and not saved. MPa on a temperature is a person's choice the
    // engine does not judge; it is here so that saved (K) and lost (MPa) are told apart.
    expect(await engineState.declareUnit("temperature", "MPa")).toBe(true);
    expect(snapshot().journal.map((one) => one.operation)).toContain("field.declareUnit");
    expect(snapshot().fields[0]?.unit).toBe("MPa");

    // The engine dies. Without a shell, the test says so the way the shell would.
    engine?.kill("SIGKILL");
    await new Promise((r) => setTimeout(r, 500));
    engineState.engineExited({ reason: "エンジンが停止されました（SIGKILL）", exitCode: null, signal: "SIGKILL" });

    let s = snapshot();
    expect(s.reachability.kind).toBe("exited");
    expect(s.lost?.map((one) => one.operation)).toContain("field.declareUnit");
    expect(s.lost?.find((one) => one.operation === "field.declareUnit")?.summary).toContain("MPa");
    expect(s.journal).toEqual([]);
    // The picture and the numbers stay on screen, labelled by the topbar as from an engine that is gone.
    expect(s.imageUrl).toMatch(/^blob:/);

    // A new engine, as the shell would start one.
    const runDirectory = join(directory, "run2");
    engine = spawn(PYTHON, ["-m", "service.transport", "--connection-directory", runDirectory], {
      cwd: ROOT,
      env: { ...process.env, PYTHONPATH: join(ROOT, "src"), PYTHONIOENCODING: "utf-8" },
      stdio: ["ignore", "pipe", "pipe"],
    });
    const connectionFile = join(runDirectory, "connection.json");
    await until(() => existsSync(connectionFile), 90_000, "the second connection file");
    connection = JSON.parse(readFileSync(connectionFile, "utf-8")) as Connection;

    const reachability = await engineState.recover(connection);

    expect(reachability.kind).toBe("reachable");
    s = snapshot();
    expect(s.sourceName).toBe("cube.vtu");
    // The saved declaration came back from the document; the unsaved one did not.
    expect(s.fields[0]?.unit).toBe("K");
    // The look a person kept came back from the document too, read before the first redraw wrote
    // the view (XC-274) - until 2026-09-20 this window's turntable overwrote it here.
    expect(s.savedCamera).toEqual(kept);
    expect(s.partVisibility).toEqual({});
    // The report the document holds is adopted by its name and read back, blocks in the order
    // they were written - not made again (AC-030, XC-275).
    await engineState.refreshReport();
    expect(snapshot().report?.blocks.map((one) => one.kind)).toEqual(["valueTable", "view"]);
    expect(snapshot().savedReports.map((one) => one.name)).toContain("cube.vtu");
    expect(s.lost?.map((one) => one.operation)).toContain("field.declareUnit");
    expect(s.refusal).toBeNull();
    expect(s.imageUrl).toMatch(/^blob:/);

    // The lock the killed engine took is still there: the reopened document is read-only and says
    // so (XC-241, XC-269), the engine's warning is on screen rather than dropped, and saving is
    // refused naming what was found - until the person takes the lock over.
    expect(s.readOnly).toBe(true);
    expect(s.lock?.state).toBe("stale");
    expect(s.warnings.some((one) => one.includes("自動では解除しません"))).toBe(true);
    expect(await engineState.save()).toBe(false);
    expect(snapshot().refusal).toContain("読み取り専用");
    engineState.clearRefusal();

    expect(await engineState.takeOverLock()).toBe(true);

    s = snapshot();
    expect(s.readOnly).toBe(false);
    expect(s.lock?.state).toBe("free");
    expect(s.sourceName).toBe("cube.vtu");
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(await engineState.save()).toBe(true);

    engineState.dismissLost();
    expect(snapshot().lost).toBeNull();
  });
});
