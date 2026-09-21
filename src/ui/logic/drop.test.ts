/* What a drop means before anything is read (XC-301): one workspace, one result into the case its
 * record names or the case on screen, several results each into the case that records that very
 * file, or a refusal that names why. Nothing is guessed from a name. */
import { describe, expect, test } from "vitest";

import { dropPlan, fileName, inspectionAllowsLoad, samePath, type DropContext } from "./drop";

const ONE: DropContext = { workspaceOpen: true, cases: [{ id: "case:1", name: "baseline" }], caseId: null, records: [] };
const TWO: DropContext = {
  workspaceOpen: true,
  cases: [{ id: "case:1", name: "荷重 100 N" }, { id: "case:2", name: "荷重 150 N" }],
  caseId: "case:1",
  records: [
    { caseId: "case:1", path: "D:\\studies\\beam.data\\cantilever_100N.vtu" },
    { caseId: "case:2", path: "D:\\studies\\beam.data\\cantilever_150N.vtu" },
  ],
};

describe("one file", () => {
  test("a workspace file opens the workspace, whatever else is open", () => {
    expect(dropPlan(["D:\\studies\\beam.svw"], { ...ONE, workspaceOpen: false })).toEqual({ kind: "openWorkspace", path: "D:\\studies\\beam.svw" });
  });

  test("one result file loads into the one case of the open workspace", () => {
    expect(dropPlan(["/runs/cube.vtu"], ONE)).toEqual({ kind: "load", path: "/runs/cube.vtu", caseId: "case:1", because: "only" });
  });

  test("with several cases, the one on screen is the target, and none is a refusal by name", () => {
    const two = { ...TWO, caseId: null, records: [] };
    const refused = dropPlan(["/runs/cube.vtu"], two);
    expect(refused.kind).toBe("refused");
    if (refused.kind === "refused") expect(refused.reason).toContain("荷重 100 N（case:1）、荷重 150 N（case:2）");
    expect(dropPlan(["/runs/cube.vtu"], { ...two, caseId: "case:2" })).toEqual({ kind: "load", path: "/runs/cube.vtu", caseId: "case:2", because: "shown" });
  });

  test("a file the document records goes to the case that records it, whichever case is on screen", () => {
    // Recorded under the second case, dropped while the first is shown: the record wins, and says so.
    expect(dropPlan(["D:\\studies\\beam.data\\cantilever_150N.vtu"], TWO)).toEqual({
      kind: "load", path: "D:\\studies\\beam.data\\cantilever_150N.vtu", caseId: "case:2", because: "recorded",
    });
    // The same file by another spelling of its path is the same file.
    expect(dropPlan(["d:/studies/other/../beam.data/CANTILEVER_150N.vtu"], TWO)).toMatchObject({ kind: "load", caseId: "case:2", because: "recorded" });
    // A file that only shares its name with a recorded one is not sent anywhere on that account.
    expect(dropPlan(["E:\\copy\\cantilever_150N.vtu"], TWO)).toEqual({ kind: "load", path: "E:\\copy\\cantilever_150N.vtu", caseId: "case:1", because: "shown" });
  });

  test("a file two cases record goes to the shown one if it is among them, and is otherwise refused naming both", () => {
    const shared = { ...TWO, records: [...TWO.records, { caseId: "case:2", path: "D:\\studies\\beam.data\\cantilever_100N.vtu" }] };
    expect(dropPlan(["D:\\studies\\beam.data\\cantilever_100N.vtu"], shared)).toMatchObject({ kind: "load", caseId: "case:1", because: "shown" });
    const elsewhere = dropPlan(["D:\\studies\\beam.data\\cantilever_100N.vtu"], { ...shared, caseId: null });
    expect(elsewhere.kind).toBe("refused");
    if (elsewhere.kind === "refused") expect(elsewhere.reason).toContain("荷重 100 N（case:1）、荷重 150 N（case:2）");
  });

  test("no workspace and nothing are each refused with the reason", () => {
    const closed = dropPlan(["/runs/cube.vtu"], { ...ONE, workspaceOpen: false });
    expect(closed.kind === "refused" && closed.reason).toContain("ワークスペースが開いていません");
    expect(dropPlan([], ONE).kind).toBe("refused");
  });
});

describe("several files", () => {
  test("each recorded under one case: loaded each into its case, in the document's order and not the drop's", () => {
    expect(dropPlan(["D:\\studies\\beam.data\\cantilever_150N.vtu", "D:\\studies\\beam.data\\cantilever_100N.vtu"], TWO)).toEqual({
      kind: "loadEach",
      loads: [
        { path: "D:\\studies\\beam.data\\cantilever_100N.vtu", caseId: "case:1" },
        { path: "D:\\studies\\beam.data\\cantilever_150N.vtu", caseId: "case:2" },
      ],
    });
  });

  test("one file no case records: nothing is loaded, and the file is named with why", () => {
    const plan = dropPlan(["D:\\studies\\beam.data\\cantilever_100N.vtu", "E:\\copy\\cube.vtu"], TWO);
    expect(plan.kind).toBe("refused");
    if (plan.kind === "refused") {
      expect(plan.reason).toContain("cube.vtu：どのケースの記録にもありません");
      expect(plan.reason).not.toContain("cantilever_100N.vtu：");
      expect(plan.reason).toContain("何も読み込みません");
    }
  });

  test("two files for one case, and a file two cases record, are each named", () => {
    const shared = { ...TWO, records: [...TWO.records, { caseId: "case:1", path: "D:\\studies\\beam.data\\extra.vtu" }, { caseId: "case:2", path: "D:\\studies\\beam.data\\extra.vtu" }] };
    const twice = dropPlan(["D:\\studies\\beam.data\\cantilever_100N.vtu", "D:\\studies\\beam.data\\cantilever_100N.vtu"], TWO);
    expect(twice.kind === "refused" && twice.reason).toContain("cantilever_100N.vtu：cantilever_100N.vtu と同じケース 荷重 100 N（case:1）に当たります");
    const both = dropPlan(["D:\\studies\\beam.data\\cantilever_150N.vtu", "D:\\studies\\beam.data\\extra.vtu"], shared);
    expect(both.kind === "refused" && both.reason).toContain("extra.vtu：複数のケースの記録にあります（荷重 100 N（case:1）、荷重 150 N（case:2））");
  });

  test("a workspace among result files, and several files with no workspace open, are refused by name", () => {
    const mixed = dropPlan(["D:\\studies\\beam.svw", "D:\\studies\\beam.data\\cantilever_100N.vtu"], TWO);
    expect(mixed.kind === "refused" && mixed.reason).toContain("ワークスペース（beam.svw）と結果ファイルは一緒には落とせません");
    const closed = dropPlan(["/runs/a.vtu", "/runs/b.vtu"], { ...TWO, workspaceOpen: false });
    expect(closed.kind === "refused" && closed.reason).toContain("a.vtu、b.vtu を読み込む先のワークスペースが開いていません");
  });
});

describe("one path as another", () => {
  test("separators, dots and - on a Windows path - case are one file; on another system case is not", () => {
    expect(samePath("D:\\a\\b\\cube.vtu", "d:/a/./b/cube.VTU")).toBe(true);
    expect(samePath("D:\\a\\x\\..\\b\\cube.vtu", "D:\\a\\b\\cube.vtu")).toBe(true);
    expect(samePath("/runs/cube.vtu", "/runs/CUBE.vtu")).toBe(false);
    expect(samePath("/runs/./cube.vtu", "/runs/cube.vtu")).toBe(true);
    expect(samePath("/runs/cube.vtu", "/runs/bar.vtu")).toBe(false);
  });

  test("the file name is the last segment on either separator", () => {
    expect(fileName("D:\\a\\b\\cube.vtu")).toBe("cube.vtu");
    expect(fileName("/a/b/cube.vtu")).toBe("cube.vtu");
  });
});

describe("what the inspection allows", () => {
  test("an unsupported format is refused in the engine's terms and a missing file by name", () => {
    expect(inspectionAllowsLoad({ exists: true, supportLevel: "Absent", format: "sim", gaps: [] }, "/runs/x.sim")).toContain("'.sim'");
    expect(inspectionAllowsLoad({ exists: false, supportLevel: "Verified", format: "vtu", gaps: [] }, "/runs/gone.vtu")).toContain("gone.vtu がありません");
    expect(inspectionAllowsLoad({ exists: true, supportLevel: "Verified", format: "vtu", gaps: [] }, "/runs/cube.vtu")).toBeNull();
    // The engine's own refusal of a path its library cannot take is the drop's refusal (XC-293).
    expect(inspectionAllowsLoad({ exists: true, supportLevel: "Verified", format: "ex2", gaps: [], refusal: "ケース.ex2 はこの経路からは読めません：…" }, "D:\\解析\\ケース.ex2")).toBe("ケース.ex2 はこの経路からは読めません：…");
  });
});
