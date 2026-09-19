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

import { PROTOCOL_VERSION, type Connection } from "../client/engine";
import { engineState, FRAME, snapshot } from "./engine";

const ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const PYTHON = process.env.SOLVIA_PYTHON ?? "python";
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47]);

let directory: string;
let engine: ChildProcess | null = null;
let connection: Connection;
let workspacePath: string;
let cubePath: string;
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
  const paths = JSON.parse(written.stdout.trim()) as { workspace: string; cube: string };
  workspacePath = paths.workspace;
  cubePath = paths.cube;

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
  });

  test("pick: a pixel off the model reads nothing, and says so rather than the nearest value", async () => {
    await engineState.pick(2, 2);

    const s = snapshot();
    expect(s.probe?.value).toBeNull();
    expect(s.probe?.missingBecause).toContain("モデル");
  });

  test("orbit: a drag is a new camera and a new frame", async () => {
    const before = snapshot().imageUrl;

    await engineState.orbit(35, 10);

    const s = snapshot();
    expect(s.refusal).toBeNull();
    expect(s.imageUrl).toMatch(/^blob:/);
    expect(s.imageUrl).not.toBe(before);
    expect(s.turntable.azimuthDegrees).toBe(30 + 35);
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
});
