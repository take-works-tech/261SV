/* The Workspace list's narrowing and wording (XC-297). */
import { describe, expect, test } from "vitest";

import { describeFilters, describeOpened, filterRecent, suggestedName, tagsOf } from "./home";
import { OSAKA } from "./fixtures";

const ENTRIES = [
  { path: "D:\\studies\\beam.svw", name: "梁の検討", tags: ["構造", "基準"], openedAt: { utc: "2026-09-21T09:00:00Z", offsetMinutes: OSAKA } },
  { path: "D:\\studies\\bracket.svw", name: "ブラケット改訂C", tags: ["構造"], openedAt: { utc: "2026-09-20T09:00:00Z", offsetMinutes: OSAKA } },
  { path: "/home/a/熱連成.svw", name: "熱連成", tags: ["熱"], openedAt: { utc: "2026-09-19T09:00:00Z", offsetMinutes: OSAKA } },
];

describe("narrowing", () => {
  test("the tags offered are the ones carried, each once, in order of first appearance", () => {
    expect(tagsOf(ENTRIES)).toEqual(["構造", "基準", "熱"]);
    expect(tagsOf([])).toEqual([]);
  });

  test("a query matches the name, the path or a tag without regard to case, and every chosen tag must be carried", () => {
    expect(filterRecent(ENTRIES, "BRACKET", []).map((one) => one.name)).toEqual(["ブラケット改訂C"]);
    expect(filterRecent(ENTRIES, "熱", []).map((one) => one.name)).toEqual(["熱連成"]);
    expect(filterRecent(ENTRIES, "", ["構造"]).map((one) => one.name)).toEqual(["梁の検討", "ブラケット改訂C"]);
    expect(filterRecent(ENTRIES, "", ["構造", "基準"]).map((one) => one.name)).toEqual(["梁の検討"]);
    expect(filterRecent(ENTRIES, "梁", ["熱"])).toEqual([]);
    expect(filterRecent(ENTRIES, "  ", [])).toHaveLength(3);
  });

  test("the filters say what they did, and nothing when they did nothing", () => {
    expect(describeFilters("", [])).toBeNull();
    expect(describeFilters(" 梁 ", ["構造", "熱"])).toBe("検索「梁」、タグ「構造・熱」");
  });
});

describe("wording", () => {
  test("when it was last opened, in the reader's zone", () => {
    expect(describeOpened(ENTRIES[0]!, OSAKA)).toBe("最後に開いた：2026-09-21 18:00");
    expect(describeOpened(ENTRIES[0]!, 0)).toBe("最後に開いた：2026-09-21 09:00（記録時は UTC+09:00）");
  });

  test("a fresh document is named after its file", () => {
    expect(suggestedName("D:\\studies\\梁の検討.svw")).toBe("梁の検討");
    expect(suggestedName("/home/a/beam.SVW")).toBe("beam");
    expect(suggestedName("beam")).toBe("beam");
  });
});
