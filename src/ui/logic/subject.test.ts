/* Which case an area shows: the item's own binding, then the pin, then the tree (XC-292). */
import { describe, expect, test } from "vitest";

import { areaSubject, caseTree, FOLLOW, reportItemCases, workingView } from "./subject";

const CASES = [
  { id: "case:1", name: "baseline" },
  { id: "case:2", name: "variant", parentId: "case:1" },
  { id: "case:3", name: "orphan", parentId: "case:9" },
];

describe("the rule, in the specification's order", () => {
  test("an item that names its cases is the authority, whatever the pin and the tree say", () => {
    const subject = areaSubject({ mode: "pinned", caseId: "case:2" }, "case:3", ["case:1"], CASES);
    expect(subject).toEqual({ caseIds: ["case:1"], caseId: "case:1", source: "item", label: "ケース baseline（case:1）", because: "この項目自身の束縛（ツリーでは変わりません）" });
  });

  test("an item whose cases this session cannot resolve says so rather than falling back to the tree", () => {
    const subject = areaSubject(FOLLOW, "case:1", [], CASES);
    expect(subject.source).toBe("item");
    expect(subject.caseId).toBeNull();
    expect(subject.label).toContain("読み込まれていません");
  });

  test("a pinned area shows its case while the tree points elsewhere; a following one shows the tree's", () => {
    expect(areaSubject({ mode: "pinned", caseId: "case:2" }, "case:1", null, CASES)).toMatchObject({ caseId: "case:2", source: "pinned", label: "ケース variant（case:2）", because: "この領域に固定" });
    expect(areaSubject(FOLLOW, "case:1", null, CASES)).toMatchObject({ caseId: "case:1", source: "tree", because: "ツリーの選択に追従" });
  });

  test("nothing selected is said as nothing, and a case the document does not list keeps its id", () => {
    expect(areaSubject(FOLLOW, null, null, CASES)).toMatchObject({ caseIds: [], caseId: null, source: "none", label: "ケース未選択" });
    expect(areaSubject(FOLLOW, "case:7", null, CASES).label).toBe("ケース case:7");
  });
});

describe("the case tree", () => {
  test("nests by parent, keeps a child of an unlisted parent at the root, and marks what is loaded", () => {
    expect(caseTree(CASES, ["case:2"])).toEqual([
      { id: "case:1", name: "baseline", children: [{ id: "case:2", name: "variant", axis: "読み込み済み" }] },
      { id: "case:3", name: "orphan" },
    ]);
    expect(caseTree([], [])).toEqual([]);
  });
});

describe("the working view of a case", () => {
  const LOADED = [{ caseId: "case:1", datasetId: "d1" }, { caseId: "case:2", datasetId: "d2" }];

  test("is the saved view under the field's name where its dataset is this case's, or nobody's", () => {
    expect(workingView("temperature", "case:1", [{ id: "v1", name: "temperature", datasetId: "d1" }], LOADED)).toEqual({ name: "temperature", existing: { id: "v1", name: "temperature", datasetId: "d1" } });
    expect(workingView("temperature", "case:2", [{ id: "v1", name: "temperature", datasetId: "stale" }], LOADED)).toEqual({ name: "temperature", existing: { id: "v1", name: "temperature", datasetId: "stale" } });
    expect(workingView("temperature", "case:1", [], LOADED)).toEqual({ name: "temperature", existing: null });
  });

  test("is named with its case where another loaded case holds the field's name, and found again by that name", () => {
    const other = [{ id: "v1", name: "temperature", datasetId: "d1" }];
    expect(workingView("temperature", "case:2", other, LOADED)).toEqual({ name: "temperature（case:2）", existing: null });
    const both = [...other, { id: "v2", name: "temperature（case:2）", datasetId: "d2" }];
    expect(workingView("temperature", "case:2", both, LOADED)).toEqual({ name: "temperature（case:2）", existing: both[1] });
  });
});

describe("what a report binds", () => {
  test("names the cases of its view blocks, an unresolvable view as none, and no view block as null", () => {
    const saved = [{ id: "v1", name: "temperature", datasetId: "d1" }, { id: "v9", name: "old", datasetId: "gone" }];
    const loaded = [{ caseId: "case:1", datasetId: "d1" }];
    expect(reportItemCases([{ kind: "view", viewId: "v1" }, { kind: "valueTable" }], saved, loaded)).toEqual(["case:1"]);
    expect(reportItemCases([{ kind: "view", viewId: "v9" }], saved, loaded)).toEqual([]);
    expect(reportItemCases([{ kind: "valueTable" }], saved, loaded)).toBeNull();
  });
});
