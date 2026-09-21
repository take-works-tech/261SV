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
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
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
import { session } from "./session";

const ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const PYTHON = process.env.SOLVIA_PYTHON ?? "python";
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47]);

let directory: string;
let engine: ChildProcess | null = null;
let connection: Connection;
let workspacePath: string;
let cubePath: string;
let partialPath: string | null = null;
let barPath: string;
let fieldsPath: string;
let transientPath: string | null = null;
let engineOutput = "";

async function until(what: () => boolean, ms: number, name: string): Promise<void> {
  const started = Date.now();
  while (!what()) {
    if (Date.now() - started > ms) throw new Error(`${name} did not happen within ${ms} ms\n${engineOutput}`);
    await new Promise((r) => setTimeout(r, 200));
  }
}

beforeAll(async () => {
  // Under a directory named as a Japanese desktop names one: the workspace, the files and the
  // run directory all carry characters outside ASCII through Node, the engine and its readers (#253).
  directory = mkdtempSync(join(tmpdir(), "solvia-接続 (試験)-"));

  // The demo case, from the one definition the Python tests also use.
  const written = spawnSync(PYTHON, [join(ROOT, "tests", "demo_case.py"), join(directory, "demo")], {
    cwd: ROOT,
    encoding: "utf-8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  if (written.status !== 0) throw new Error(`demo case not written:\n${written.stderr}`);
  const paths = JSON.parse(written.stdout.trim()) as {
    workspace: string; cube: string; partial: string | null; bar: string; fields: string; transient: string | null;
  };
  workspacePath = paths.workspace;
  cubePath = paths.cube;
  partialPath = paths.partial;
  barPath = paths.bar;
  fieldsPath = paths.fields;
  transientPath = paths.transient;

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
    expect(s.fields).toEqual([{ name: "temperature", association: "point", unit: null, components: 1 }]);
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
    expect(s.operations?.registered.length).toBe(35);
    expect([...(s.operations?.registered ?? []), ...(s.operations?.unimplemented ?? [])].sort()).toEqual([...OPERATIONS].sort());
    const rows = commandGroups(s.operations, "").flatMap((group) => group.rows);
    expect(rows).toHaveLength(OPERATIONS.length);
    expect(rows.find((row) => row.operation === "dataset.load")).toMatchObject({ writes: true, parameters: "caseId、filePaths", status: "answers" });
    expect(rows.find((row) => row.operation === "graph.duplicate")?.status).toBe("unimplemented");
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
    expect(rows.find((row) => row.operation === "graph.duplicate")?.because).toContain("実装なし");

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

  test("a cell field's statistics are two numbers, each labelled, the averaged one with its spread - 110 against 200 (INV-032, XC-281)", async () => {
    expect(await engineState.loadDataset("case:1", barPath)).toBe(true);
    await engineState.refresh();
    let s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.fields.map((one) => `${one.name}/${one.association}`)).toEqual(["stress/cell"]);
    expect(s.statistics?.averaging).toBe("unaveraged");
    expect(s.statistics?.maximum.value).toBe(200);
    expect(s.statistics?.averaged?.maximum.value).toBeCloseTo(110, 6);
    expect(s.statistics?.averaged?.maximum.caveats).toContain("averaged");
    expect(s.statistics?.averaged?.spreadAtMaximum.value).toBeCloseTo(180, 6);
    expect(s.statistics?.averaged?.disagreement).toContain("45%");
    // Copied, both numbers travel with their labels.
    if (!s.statistics) throw new Error("the statistics were not read");
    const labels = statisticsRows("stress", s.statistics, { undeclared: "単位未宣言", provenance: { computed: "計算" } }).map((row) => row[0]);
    expect(labels).toContain("stress（最大・要素値（平均なし））");
    expect(labels).toContain("stress（最大・節点平均）");

    // The thread goes on with the cube, as after the partial case.
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.statistics?.averaging).toBeUndefined();
    expect(s.imageUrl).toMatch(/^blob:/);
  });

  test("derived: a vector is never one number, and its magnitude and a tensor's von Mises come from the engine with their formulas (XC-282)", async () => {
    expect(await engineState.loadDataset("case:1", fieldsPath)).toBe(true);
    let s = snapshot();
    expect(s.fields.map((one) => `${one.name}/${one.components}`)).toEqual(["displacement/3", "stress6/6"]);
    // Colouring by the vector as loaded is refused by name - the store chose it, the engine said no.
    await engineState.refresh();
    expect(snapshot().refusal).toContain("3 成分");

    expect(await engineState.derive("displacement", "magnitude")).toBe(true);
    s = snapshot();
    expect(s.fieldName).toBe("displacement.magnitude");
    expect(s.fields.some((one) => one.name === "displacement.magnitude" && one.components === 1)).toBe(true);
    expect(s.derived["displacement.magnitude"]?.formula).toBe("sqrt(X^2 + Y^2 + Z^2)");
    expect(s.derived["displacement.magnitude"]?.conventions.some((one) => one.includes("global Cartesian"))).toBe(true);
    expect(s.statistics?.maximum.value).toBe(7);
    expect(s.statistics?.maximum.digits).toBe(6);
    expect(s.refusal).toBeNull();
    expect(s.imageUrl).toMatch(/^blob:/);

    expect(await engineState.derive("stress6", "principal")).toBe(true);
    s = snapshot();
    expect(s.fieldName).toBe("stress6.principal1");
    expect(Object.keys(s.derived).filter((name) => name.startsWith("stress6.principal"))).toHaveLength(3);
    expect(s.derived["stress6.principal3"]?.conventions.some((one) => one.includes("大きい順"))).toBe(true);
    expect(s.statistics?.maximum.value).toBe(200);

    expect(await engineState.derive("stress6", "vonMises")).toBe(true);
    s = snapshot();
    expect(s.statistics?.maximum.value).toBeCloseTo(173.205, 2);

    // What the build does not derive is refused by name, and the refusal is on screen.
    expect(await engineState.derive("stress6", "invariants")).toBe(false);
    expect(snapshot().refusal).toContain("二乗");

    // The thread goes on with the cube.
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.derived).toEqual({});
    expect(s.imageUrl).toMatch(/^blob:/);
  });

  test("result position: the second step's numbers are the second step's, every answer says which step, and a step the file lacks is refused (XC-283)", async () => {
    if (!transientPath) throw new Error("the transient fixture was not written: h5py is missing from the engine environment");
    expect(await engineState.loadDataset("case:1", transientPath)).toBe(true);
    await engineState.refresh();
    let s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.described?.resultAxis).toMatchObject({ kind: "undeclared", positions: [0, 0.5], count: 2 });
    expect(s.step).toBe(0);
    expect(s.statistics?.maximum.value).toBe(90);
    expect(s.statistics?.resultPosition).toEqual({
      step: 0, count: 2, kind: "undeclared", value: 0, unit: null, stated: "ステップ 1/2（位置 0・軸の種類は宣言なし）",
    });
    expect(viewFooter(s, "単位未宣言")?.showing).toContain("・ステップ 1/2（位置 0・軸の種類は宣言なし）・");

    expect(await engineState.moveToStep(1)).toBe(true);
    s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.step).toBe(1);
    expect(s.statistics?.maximum.value).toBe(91);
    expect(s.statistics?.scope).toBe("ケース全体（1 パート）・ステップ 2/2（位置 0.5・軸の種類は宣言なし）");
    expect(s.statistics?.resultPosition.step).toBe(1);
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(viewFooter(s, "単位未宣言")?.showing).toContain("ステップ 2/2（位置 0.5・軸の種類は宣言なし）");
    await engineState.probe([0, 1, 0]);
    s = snapshot();
    expect(s.probe?.value).toBe(91);
    expect(s.probePosition).toMatchObject({ step: 1, count: 2, kind: "undeclared", value: 0.5, unit: null });

    // A step that is not there is refused by name, nothing nearer is shown, and the view stays
    // where it was (view/AC-033).
    expect(await engineState.moveToStep(2)).toBe(false);
    s = snapshot();
    expect(s.refusal).toContain("ステップ番号 2");
    expect(s.step).toBe(1);
    expect(s.statistics?.maximum.value).toBe(91);

    // The thread goes on with the cube: steady, one step, nothing to move along.
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.step).toBe(0);
    expect(s.statistics?.resultPosition).toEqual({
      step: 0, count: 1, kind: "none", value: null, unit: null, stated: "定常（結果軸なし・ステップ 1/1）",
    });
    expect(viewFooter(s, "単位未宣言")?.showing).not.toContain("ステップ");
  });
});

describe("a drop on the window (XC-301)", () => {
  test("one result file is inspected, then loaded into the one case; an unsupported one and two at once are refused by name", async () => {
    expect(snapshot().cases.map((one) => one.id)).toEqual(["case:1"]);

    const loaded = await engineState.dropFiles([cubePath]);
    expect(loaded).toEqual({ kind: "loaded", path: cubePath, caseId: "case:1" });
    let s = snapshot();
    expect(s.datasetId).toBeTruthy();
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(s.notices.some((one) => one.severity === "info" && one.title.includes("cube.vtu"))).toBe(true);

    writeFileSync(join(directory, "result.sim"), "not a mesh");
    const unsupported = await engineState.dropFiles([join(directory, "result.sim")]);
    expect(unsupported.kind).toBe("refused");
    if (unsupported.kind === "refused") expect(unsupported.reason).toContain("'.sim'");
    s = snapshot();
    expect(s.datasetId).toBeTruthy();
    expect(s.notices.some((one) => one.severity === "refusal" && one.detail.includes("'.sim'"))).toBe(true);

    // Two at once: the cube is recorded under the one case by this session's load, the bar under
    // none, so nothing is loaded and the bar is named (XC-301).
    const two = await engineState.dropFiles([cubePath, barPath]);
    expect(two.kind === "refused" && two.reason).toContain("bar.vtu：どのケースの記録にもありません");
    expect(snapshot().datasetId).toBeTruthy();

    const opened = await engineState.dropFiles([workspacePath]);
    expect(opened).toEqual({ kind: "opened", path: workspacePath });
    expect(snapshot().datasetId).toBeNull();
    // The thread goes on with the cube.
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
  });
});

describe("a graph over the result axis (XC-290)", () => {
  test("one field's maximum per step, in the engine's numbers, and the definition read back", async () => {
    if (!transientPath) throw new Error("the transient fixture was not written: h5py is missing from the engine environment");
    expect(await engineState.loadDataset("case:1", transientPath)).toBe(true);

    expect(await engineState.showGraph({ fieldName: "stress", reduction: "max", kind: "overTime" })).toBe(true);
    let s = snapshot();
    expect(s.graphId).toBeTruthy();
    expect(s.graphData?.series[0]?.points.map((one) => [one.x, one.value])).toEqual([[0, 90], [0.5, 91]]);
    expect(s.graphData?.series[0]?.points[1]?.resultPosition?.stated).toBe("ステップ 2/2（位置 0.5・軸の種類は宣言なし）");
    expect(s.graphData?.axisLabel).toBe("単位未宣言");
    expect(s.graphData?.series[0]?.reduction).toBe("max");
    expect(s.graphData?.resultAxisNote).toContain("宣言されていない");

    // A declaration changes the axis and the numbers, read again rather than relabelled.
    expect(await engineState.declareUnit("stress", "MPa")).toBe(true);
    expect(await engineState.showGraph({ fieldName: "stress", reduction: "mean", kind: "overTime" })).toBe(true);
    s = snapshot();
    expect(s.graphData?.series[0]?.unit).toBe("Pa");
    expect(s.graphData?.series[0]?.declaredUnit).toBe("MPa");
    expect(s.graphData?.series[0]?.reduction).toBe("mean");
    // The same graph, updated in place: one item under this dataset's name.
    expect(s.savedGraphs.filter((one) => one.id === s.graphId)).toHaveLength(1);

    // The thread goes on with the cube.
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    expect(snapshot().graphData).toBeNull();
  });
});

describe("a camera path (XC-289)", () => {
  test("keyframes from the live look are written to the view, read back, and a frame on the path carries the engine's pose and rule", async () => {
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    expect(snapshot().imageUrl).toMatch(/^blob:/);

    expect(await engineState.addPathKeyframe(0)).toBe(true);
    await engineState.orbit(90, 0);
    expect(await engineState.addPathKeyframe(1)).toBe(true);
    let s = snapshot();
    expect(s.cameraPaths[0]?.keyframes.map((one) => one.at)).toEqual([0, 1]);
    expect(s.cameraPaths[0]?.interpolation).toBe("linear");
    // The same parameter twice is refused before anything is written.
    expect(await engineState.addPathKeyframe(1)).toBe(false);
    expect(snapshot().refusal).toContain("既にキーフレーム");

    expect(await engineState.previewPath(0.5)).toBe(true);
    s = snapshot();
    expect(s.pathPreview?.id).toBe("path:1");
    expect(s.pathPreview?.at).toBe(0.5);
    expect(s.pathPreview?.rule).toContain("直線補間");
    expect(s.pathPreview?.camera.position_m).toHaveLength(3);
    expect(s.imageUrl).toMatch(/^blob:/);

    await engineState.setPathInterpolation("smooth");
    s = snapshot();
    expect(s.cameraPaths[0]?.interpolation).toBe("smooth");
    expect(s.pathPreview?.interpolation).toBe("smooth");

    // The document holds the path: a fresh read of the view brings it back.
    const before = s.cameraPaths[0];
    await engineState.clearPathPreview();
    expect(snapshot().pathPreview).toBeNull();
    await engineState.refresh();
    expect(snapshot().cameraPaths[0]).toEqual(before);
  });
});

describe("the log area (XC-286)", () => {
  test("a refusal is a notice kept after dismissal, and the engine's log reads it back with where it lives", async () => {
    expect(await engineState.loadDataset("case:1", fieldsPath)).toBe(true);
    expect(await engineState.derive("stress6", "invariants")).toBe(false);
    let s = snapshot();
    const raised = s.notices.find((one) => one.severity === "refusal" && one.operation === "field.derive");
    expect(raised?.detail).toContain("二乗");
    expect(raised?.dismissedAt).toBeUndefined();

    engineState.dismissNotice(raised?.id ?? "");
    s = snapshot();
    const dismissed = s.notices.find((one) => one.id === raised?.id);
    expect(dismissed?.dismissedAt?.utc).toBeTruthy();
    expect(s.notices.length).toBeGreaterThanOrEqual(1);

    const log = await engineState.log({ level: "warning" });
    expect(log?.source).toBe("memory");
    expect(log?.logDirectory).toBeNull();
    const refused = log?.entries.find((one) => one.event === "command" && one.context.operation === "field.derive" && one.context.status === "refused");
    expect(refused?.level).toBe("warning");
    expect(String(refused?.context.reason)).toContain("二乗");

    // The thread goes on with the cube.
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    expect(snapshot().refusal).toBeNull();
  });
});

describe("each area says which case it shows (XC-292)", () => {
  test("the tree is the document's; selecting a case moves the following areas, a pinned one stays, and a drop goes to the case on screen", async () => {
    // A document with two cases: the demo's, and a variant under it.
    const twoCasesPath = join(directory, "two-cases.svw");
    const document = JSON.parse(readFileSync(workspacePath, "utf-8")) as { cases: unknown[] };
    document.cases = [{ id: "case:1", name: "baseline", children: [{ id: "case:2", name: "variant" }] }];
    writeFileSync(twoCasesPath, JSON.stringify(document));
    expect(await engineState.openWorkspace(twoCasesPath)).toBe(true);
    let s = snapshot();
    expect(s.cases).toEqual([{ id: "case:1", name: "baseline" }, { id: "case:2", name: "variant", parentId: "case:1" }]);
    // Opening selects the first case, and every area follows it: nothing is loaded, and it says so.
    expect(session.current().selectedCaseId).toBe("case:1");
    expect(engineState.subjectOf("view")).toMatchObject({ caseId: "case:1", source: "tree", label: "ケース baseline（case:1）", because: "ツリーの選択に追従" });
    expect(s.caseId).toBe("case:1");
    expect(s.datasetId).toBeNull();

    // A drop goes to the case the View area shows.
    const dropped = await engineState.dropFiles([cubePath]);
    expect(dropped).toEqual({ kind: "loaded", path: cubePath, caseId: "case:1" });
    s = snapshot();
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(Object.keys(s.loaded)).toEqual(["case:1"]);
    const cubeDataset = s.datasetId;

    // A graph over the area's case: asked with that case as the context, and the answer says so.
    expect(await engineState.showGraph({ fieldName: "temperature", reduction: "max", kind: "line" })).toBe(true);
    expect(snapshot().graphData?.selection).toBe("context");
    expect(snapshot().graphData?.cases).toEqual(["case:1"]);
    expect(snapshot().graphData?.series[0]?.points[0]?.value).toBe(8);

    // Pin the Graph area to the first case, then select the second in the tree.
    session.pinArea("graph", "case:1");
    session.selectCase("case:2");
    await engineState.settled();
    s = snapshot();
    // The View area follows: nothing is loaded for the variant, and the area says so - no picture
    // and no numbers, rather than the first case's under the variant's name.
    expect(engineState.subjectOf("view")).toMatchObject({ caseId: "case:2", source: "tree", label: "ケース variant（case:2）" });
    expect(s.caseId).toBe("case:2");
    expect(s.datasetId).toBeNull();
    expect(s.imageUrl).toBeNull();
    expect(s.statistics).toBeNull();
    expect(viewFooter(s, "単位未宣言")?.showing).toContain("ケース variant（case:2）・データセット未読込");
    // The Graph area is pinned: its numbers are still the first case's.
    expect(engineState.subjectOf("graph")).toMatchObject({ caseId: "case:1", source: "pinned", because: "この領域に固定" });
    expect(s.graphData?.cases).toEqual(["case:1"]);
    // The first case's dataset is kept, not dropped.
    expect(Object.keys(s.loaded)).toEqual(["case:1"]);

    // A file dropped now goes to the variant, and the View area shows it; the pinned graph is unmoved.
    const second = await engineState.dropFiles([barPath]);
    expect(second).toEqual({ kind: "loaded", path: barPath, caseId: "case:2" });
    s = snapshot();
    expect(s.caseId).toBe("case:2");
    expect(s.sourceName).toBe("bar.vtu");
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(Object.keys(s.loaded).sort()).toEqual(["case:1", "case:2"]);
    expect(s.graphData?.cases).toEqual(["case:1"]);

    // Back to the first case: its dataset comes back as a switch, not a second read.
    session.selectCase("case:1");
    await engineState.settled();
    s = snapshot();
    expect(s.caseId).toBe("case:1");
    expect(s.datasetId).toBe(cubeDataset);
    expect(s.sourceName).toBe("cube.vtu");
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(s.statistics?.maximum?.value).toBe(8);

    // The Graph area follows again; the variant has no temperature, so its point is no data with
    // the reason, in the legend - never the first case's number under the variant's name.
    session.followArea("graph");
    session.selectCase("case:2");
    await engineState.settled();
    s = snapshot();
    expect(engineState.subjectOf("graph")).toMatchObject({ caseId: "case:2", source: "tree" });
    expect(s.graphData?.selection).toBe("context");
    expect(s.graphData?.cases).toEqual(["case:2"]);
    expect(s.graphData?.series[0]?.points[0]?.value).toBeNull();
    expect(s.graphData?.series[0]?.points[0]?.reason).toContain("temperature");
    expect(s.graphData?.missing).toHaveLength(1);

    // Pin the View area to the variant: selecting the first case moves the tree and not the picture.
    session.pinArea("view", "case:2");
    session.selectCase("case:1");
    await engineState.settled();
    s = snapshot();
    expect(engineState.subjectOf("view")).toMatchObject({ caseId: "case:2", source: "pinned" });
    expect(s.caseId).toBe("case:2");
    expect(s.sourceName).toBe("bar.vtu");
    expect(s.graphData?.cases).toEqual(["case:1"]);
    // The Report area's binding is its view block's case, which the tree cannot override.
    expect(await engineState.ensureReport()).toBeTruthy();
    expect(engineState.subjectOf("report")).toMatchObject({ source: "item", caseIds: ["case:2"], because: "この項目自身の束縛（ツリーでは変わりません）" });

    // The thread goes on with the demo workspace and the cube.
    session.followArea("view");
    await engineState.settled();
    expect(snapshot().sourceName).toBe("cube.vtu");
    expect(await engineState.openWorkspace(workspacePath)).toBe(true);
    expect(session.current().subjects.view).toEqual({ mode: "follow" });
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    expect(snapshot().imageUrl).toMatch(/^blob:/);
  });
});

describe("a new workspace (XC-297)", () => {
  test("is written where it was asked for, with one case, opened, and refused where a file already is", async () => {
    const folder = join(directory, "新しい検討");
    mkdirSync(folder);
    const made = join(folder, "made.svw");
    expect(await engineState.createWorkspace(made, "作った検討", "基準")).toBe(true);
    let s = snapshot();
    expect(s.workspaceName).toBe("作った検討");
    expect(s.cases.map((one) => one.name)).toEqual(["基準"]);
    expect(s.caseTags).toEqual([]);
    expect(existsSync(made)).toBe(true);
    expect(session.current().selectedCaseId).toBe(s.cases[0]?.id ?? null);
    // A second document under the same name is refused, and the first is untouched.
    const before = readFileSync(made, "utf-8");
    expect(await engineState.createWorkspace(made, "二つ目")).toBe(false);
    expect(snapshot().refusal).toContain("すでにあります");
    expect(readFileSync(made, "utf-8")).toBe(before);
    engineState.clearRefusal();

    // The thread goes on with the demo workspace and the cube.
    expect(await engineState.openWorkspace(workspacePath)).toBe(true);
    s = snapshot();
    expect(s.workspaceName).toBe("梁の検討");
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    expect(snapshot().imageUrl).toMatch(/^blob:/);
  });
});

describe("the shipped sample (XC-298)", () => {
  test("is generated where it was asked for, opened, and its first case is on screen with its declared units", async () => {
    const folder = join(directory, "サンプル");
    mkdirSync(folder);
    const started = performance.now();
    expect(await engineState.openSample(join(folder, "片持ち梁.svw"))).toBe(true);
    const elapsed = performance.now() - started;
    const s = snapshot();
    expect(s.workspaceName).toBe("片持ち梁（サンプル）");
    expect(s.cases.map((one) => one.name)).toEqual(["荷重 100 N", "荷重 150 N"]);
    expect(s.caseTags).toEqual(["1.5 倍", "静荷重"]);
    expect(s.caseId).toBe(s.cases[0]?.id);
    expect(s.sourceName).toBe("cantilever_100N.vtu");
    expect(s.fields.map((one) => `${one.name}:${one.unit ?? "-"}`)).toEqual(["stress:Pa", "displacement:m", "element_stress:Pa"]);
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(s.statistics?.maximum?.value).toBeCloseTo(1.2e6, 0);
    expect(s.statistics?.maximum?.unit).toBe("Pa");
    expect(existsSync(join(folder, "片持ち梁.data", "cantilever_150N.vtu"))).toBe(true);
    console.log(`sample: asked for, written, opened, loaded and drawn in ${elapsed.toFixed(0)} ms (this machine, not a launch)`);

    // Several files at once (XC-301): each recorded under one case, dropped in an order not the
    // document's, loaded in the document's order; the View area keeps the case it showed.
    const first = s.cases[0]!;
    const second = s.cases[1]!;
    const path100 = first.sources?.[0]?.path;
    const path150 = second.sources?.[0]?.path;
    expect(path100 && path150).toBeTruthy();
    const dropped = await engineState.dropFiles([path150!, path100!]);
    expect(dropped).toEqual({ kind: "loadedEach", loads: [{ path: path100, caseId: first.id }, { path: path150, caseId: second.id }] });
    let after = snapshot();
    expect(Object.keys(after.loaded).sort()).toEqual([first.id, second.id].sort());
    expect(after.caseId).toBe(first.id);
    expect(after.sourceName).toBe("cantilever_100N.vtu");
    expect(after.notices.some((one) => one.severity === "info" && one.title === "2 件を読み込みました")).toBe(true);
    // The variant's numbers are its own: the maximum stress under 150 N is 1.5 times the 100 N one.
    session.selectCase(second.id);
    await engineState.settled();
    after = snapshot();
    expect(after.caseId).toBe(second.id);
    expect(after.sourceName).toBe("cantilever_150N.vtu");
    expect(after.statistics?.maximum?.value).toBeCloseTo(1.8e6, 0);
    // A file the document does not record, dropped with one it does, loads nothing and is named.
    const stray = await engineState.dropFiles([path100!, cubePath]);
    expect(stray.kind).toBe("refused");
    if (stray.kind === "refused") expect(stray.reason).toContain("cube.vtu：どのケースの記録にもありません");
    expect(Object.keys(snapshot().loaded).sort()).toEqual([first.id, second.id].sort());
    // One recorded file alone goes to the case that records it, whichever case is on screen.
    session.selectCase(first.id);
    await engineState.settled();
    expect(snapshot().caseId).toBe(first.id);
    const alone = await engineState.dropFiles([path150!]);
    expect(alone).toEqual({ kind: "loaded", path: path150, caseId: second.id });
    expect(snapshot().caseId).toBe(second.id);
    expect(snapshot().statistics?.maximum?.value).toBeCloseTo(1.8e6, 0);
    engineState.clearRefusal();
    // Asked again at the same place, nothing is written over.
    expect(await engineState.openSample(join(folder, "片持ち梁.svw"))).toBe(false);
    expect(snapshot().refusal).toContain("すでにあります");
    engineState.clearRefusal();

    // The thread goes on with the demo workspace and the cube.
    expect(await engineState.openWorkspace(workspacePath)).toBe(true);
    expect(await engineState.loadDataset("case:1", cubePath)).toBe(true);
    await engineState.refresh();
    expect(snapshot().imageUrl).toMatch(/^blob:/);
  });
});

describe("when the engine ends", () => {
  test("what was saved is opened again, and what was not is listed as lost - not rebuilt", async () => {
    // A second declaration, applied and not saved. MPa on a temperature is a person's choice the
    // engine does not judge; it is here so that saved (K) and lost (MPa) are told apart.
    expect({ refusal: snapshot().refusal, dataset: snapshot().datasetId, readOnly: snapshot().readOnly, subject: engineState.subjectOf("view").caseId }).toEqual({ refusal: null, dataset: expect.any(String), readOnly: false, subject: "case:1" });
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
