/* The outliner from the engine's parts: the file's hierarchy and nothing inferred (AC-056), the
 * absence where the file put it, and what a control does to the view's partVisibility (AC-055). */
import { describe, expect, test } from "vitest";

import { absentParts, describeAbsence, outlinerTree, visibilityAfter, type PartRow } from "./parts";

const CUBE: PartRow[] = [{ name: "cube", type: "part", path: ["cube"], pointCount: 8, cellCount: 1 }];

const ASSEMBLY: PartRow[] = [
  { name: "asm / Base / Zone", type: "part", path: ["asm", "Base", "Zone"], parentId: "asm / Base", pointCount: 8, cellCount: 1 },
  { name: "asm / Base / Zone2", type: "part", path: ["asm", "Base", "Zone2"], parentId: "asm / Base", pointCount: 8, cellCount: 1 },
  { name: "asm / Base / Ghost", type: "absent", path: ["asm", "Base", "Ghost"], parentId: "asm / Base", reason: "要素なし", pointCount: 0, cellCount: 0 },
  { name: "asm / bolt", type: "part", path: ["asm", "bolt"], parentId: "asm", pointCount: 4, cellCount: 1 },
];

describe("the rows", () => {
  test("a flat file reads flat: one row, no block invented above it", () => {
    expect(outlinerTree(CUBE, {})).toEqual([{ id: "cube", name: "cube", kind: "部品", visible: true, toggle: "part" }]);
  });

  test("a nested file reads as its own blocks, with the absence where the file put it and no control on it", () => {
    const [asm] = outlinerTree(ASSEMBLY, {});

    expect(asm?.id).toBe("asm");
    expect(asm?.children?.map((one) => one.id)).toEqual(["asm / Base", "asm / bolt"]);
    const base = asm?.children?.[0];
    expect(base?.children?.map((one) => `${one.name}:${one.kind}:${one.toggle}`)).toEqual([
      "Zone:部品:part",
      "Zone2:部品:part",
      "Ghost:欠け（要素なし）:none",
    ]);
  });

  test("a block reads as shown while anything under it is, and hidden once nothing is", () => {
    const hidden = { "asm / Base / Zone": false, "asm / Base / Zone2": false };
    const [asm] = outlinerTree(ASSEMBLY, hidden);

    expect(asm?.children?.[0]?.visible).toBe(false);
    expect(asm?.visible).toBe(true);
    expect(asm?.children?.[1]?.visible).toBe(true);
  });

  test("nothing loaded is no rows", () => {
    expect(outlinerTree([], {})).toEqual([]);
  });
});

describe("what a control does to the view's partVisibility", () => {
  test("a part's control hides it, and the map carries only what is hidden", () => {
    const once = visibilityAfter(CUBE, {}, "cube", "toggle");
    expect(once).toEqual({ cube: false });
    expect(visibilityAfter(CUBE, once, "cube", "toggle")).toEqual({});
  });

  test("a block's control reaches every part under it, and never the absent one", () => {
    const hidden = visibilityAfter(ASSEMBLY, {}, "asm / Base", "toggle");
    expect(hidden).toEqual({ "asm / Base / Zone": false, "asm / Base / Zone2": false });
    // Mixed under the block: the control shows the branch rather than hiding the rest of it.
    const mixed = { "asm / Base / Zone": false };
    expect(visibilityAfter(ASSEMBLY, mixed, "asm / Base", "toggle")).toEqual({});
  });

  test("isolating a branch shows it and hides every other part", () => {
    expect(visibilityAfter(ASSEMBLY, { "asm / Base / Zone": false }, "asm / Base", "isolate")).toEqual({ "asm / bolt": false });
    expect(visibilityAfter(ASSEMBLY, {}, "asm / bolt", "isolate")).toEqual({ "asm / Base / Zone": false, "asm / Base / Zone2": false });
  });

  test("a row that is no part and no block changes nothing", () => {
    expect(visibilityAfter(ASSEMBLY, { "asm / bolt": false }, "asm / Base / Ghost", "toggle")).toEqual({ "asm / bolt": false });
  });
});

describe("the absence as a sentence", () => {
  test("the name and the reason are the engine's two facts, joined here", () => {
    expect(describeAbsence(ASSEMBLY[2] as PartRow)).toBe("asm / Base / Ghost（要素なし）");
    expect(describeAbsence({ name: "asm / washer", type: "absent", path: ["asm", "washer"], pointCount: 0, cellCount: 0 })).toBe("asm / washer");
    expect(absentParts(ASSEMBLY)).toEqual(["asm / Base / Ghost（要素なし）"]);
    expect(absentParts(null)).toEqual([]);
  });
});
