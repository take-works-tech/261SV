/* What a drop means before anything is read (XC-291): one workspace, one result into one case, or
 * a refusal that names why. */
import { describe, expect, test } from "vitest";

import { dropPlan, fileName, inspectionAllowsLoad } from "./drop";

const OPEN = { workspaceOpen: true, cases: [{ id: "case:1", name: "baseline" }], caseId: null };

describe("the plan from the paths", () => {
  test("a workspace file opens the workspace, whatever else is open", () => {
    expect(dropPlan(["D:\\studies\\beam.svw"], { ...OPEN, workspaceOpen: false })).toEqual({ kind: "openWorkspace", path: "D:\\studies\\beam.svw" });
  });

  test("one result file loads into the one case of the open workspace", () => {
    expect(dropPlan(["/runs/cube.vtu"], OPEN)).toEqual({ kind: "load", path: "/runs/cube.vtu", caseId: "case:1" });
  });

  test("with several cases, the one a dataset was loaded into is the target, and none is a refusal by name", () => {
    const two = { workspaceOpen: true, cases: [{ id: "case:1", name: "baseline" }, { id: "case:2", name: "variant" }], caseId: null };
    const refused = dropPlan(["/runs/cube.vtu"], two);
    expect(refused.kind).toBe("refused");
    if (refused.kind === "refused") expect(refused.reason).toContain("baseline（case:1）、variant（case:2）");
    expect(dropPlan(["/runs/cube.vtu"], { ...two, caseId: "case:2" })).toEqual({ kind: "load", path: "/runs/cube.vtu", caseId: "case:2" });
  });

  test("no workspace, several files, and nothing are each refused with the reason", () => {
    const closed = dropPlan(["/runs/cube.vtu"], { ...OPEN, workspaceOpen: false });
    expect(closed.kind === "refused" && closed.reason).toContain("ワークスペースが開いていません");
    const several = dropPlan(["/runs/a.vtu", "/runs/b.vtu"], OPEN);
    expect(several.kind === "refused" && several.reason).toContain("1 件ずつ");
    expect(several.kind === "refused" && several.reason).toContain("a.vtu、b.vtu");
    expect(dropPlan([], OPEN).kind).toBe("refused");
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

  test("the file name is the last segment on either separator", () => {
    expect(fileName("D:\\a\\b\\cube.vtu")).toBe("cube.vtu");
    expect(fileName("/a/b/cube.vtu")).toBe("cube.vtu");
  });
});
