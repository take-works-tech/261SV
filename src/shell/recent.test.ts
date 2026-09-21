/* The recent-workspace list (XC-297): remembered newest first, one entry per path, bounded, and
 * tolerant of a file that is not what it wrote; emptied whole on the person's word (XC-300). */
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, test } from "vitest";

import { clear, forget, readRecent, remember, RECENT_LIMIT } from "./recent";

let directory: string | null = null;

afterEach(() => {
  if (directory) rmSync(directory, { recursive: true, force: true });
  directory = null;
});

function fresh(): string {
  directory = mkdtempSync(join(tmpdir(), "solvia-最近-"));
  return join(directory, "state", "recent.json");
}

const at = (minute: number) => ({ utc: `2026-09-21T10:${String(minute).padStart(2, "0")}:00Z`, offsetMinutes: 540 });

describe("remembering", () => {
  test("a new file lists what was remembered, newest first, one entry per path", () => {
    const file = fresh();
    expect(readRecent(file)).toEqual([]);
    remember(file, { path: "D:\\studies\\beam.svw", name: "梁の検討", tags: ["構造"], openedAt: at(1) });
    remember(file, { path: "D:\\studies\\bracket.svw", name: "ブラケット", tags: [], openedAt: at(2) });
    const again = remember(file, { path: process.platform === "win32" ? "d:\\STUDIES\\beam.svw" : "D:\\studies\\beam.svw", name: "梁の検討（改）", tags: ["構造", "熱"], openedAt: at(3) });
    expect(again.map((one) => one.name)).toEqual(["梁の検討（改）", "ブラケット"]);
    expect(readRecent(file)).toEqual(again);
  });

  test("keeps the newest entries up to the limit", () => {
    const file = fresh();
    for (let index = 0; index < RECENT_LIMIT + 5; index += 1) {
      remember(file, { path: `D:\\s\\${index}.svw`, name: String(index), tags: [], openedAt: at(index % 60) });
    }
    const kept = readRecent(file);
    expect(kept).toHaveLength(RECENT_LIMIT);
    expect(kept[0]?.name).toBe(String(RECENT_LIMIT + 4));
  });
});

describe("forgetting and a damaged file", () => {
  test("forget removes one path and leaves the rest in order", () => {
    const file = fresh();
    remember(file, { path: "D:\\a.svw", name: "a", tags: [], openedAt: at(1) });
    remember(file, { path: "D:\\b.svw", name: "b", tags: [], openedAt: at(2) });
    expect(forget(file, "D:\\a.svw").map((one) => one.name)).toEqual(["b"]);
    expect(forget(file, "D:\\nowhere.svw").map((one) => one.name)).toEqual(["b"]);
  });

  test("a file that is not a list, or holds entries of another shape, reads as empty rather than failing", () => {
    const file = fresh();
    remember(file, { path: "D:\\seed.svw", name: "seed", tags: [], openedAt: at(0) });
    writeFileSync(file, "", "utf-8");
    expect(readRecent(file)).toEqual([]);
    writeFileSync(file, JSON.stringify({ not: "a list" }), "utf-8");
    expect(readRecent(file)).toEqual([]);
    writeFileSync(file, JSON.stringify([{ path: "D:\\ok.svw", name: "ok", tags: ["x"], openedAt: at(5) }, { path: 3 }, "junk"]), "utf-8");
    expect(readRecent(file).map((one) => one.name)).toEqual(["ok"]);
  });
});

describe("clearing (XC-300)", () => {
  test("clear empties the whole list, the file no longer holds the paths, and the list goes on being kept", () => {
    const file = fresh();
    remember(file, { path: "D:\\clients\\north\\bracket.svw", name: "ブラケット", tags: ["構造"], openedAt: at(1) });
    remember(file, { path: "D:\\clients\\south\\beam.svw", name: "梁", tags: [], openedAt: at(2) });
    expect(clear(file)).toEqual([]);
    expect(readRecent(file)).toEqual([]);
    expect(readFileSync(file, "utf-8")).not.toContain("clients");
    expect(remember(file, { path: "D:\\a.svw", name: "a", tags: [], openedAt: at(3) }).map((one) => one.name)).toEqual(["a"]);
  });

  test("clear on a list that was never written leaves an empty list, not a failure", () => {
    const file = fresh();
    expect(clear(file)).toEqual([]);
    expect(readRecent(file)).toEqual([]);
  });
});
