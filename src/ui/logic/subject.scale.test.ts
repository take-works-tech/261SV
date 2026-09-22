/* The case tree at the sizes LIM-005 is about (E-225): built for hundreds and thousands of cases,
 * with the time printed - a shared runner's number is not this machine's, so nothing here holds a
 * time to a limit; the shape is what is held. */
import { describe, expect, test } from "vitest";

import { caseTree, type CaseSummary } from "./subject";

/** A two-level tree of sweeps, ten cases each - the shape spike/measure_workspace_cases.py builds. */
function sweeps(count: number): CaseSummary[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `case:${index}`,
    name: `荷重 ${100 + index} N`,
    ...(index % 10 === 0 ? {} : { parentId: `case:${index - (index % 10)}` }),
  }));
}

describe("the case tree at scale", () => {
  test("a tree of sweeps is built whole at every size, and the time is said", () => {
    const timings: string[] = [];
    for (const count of [500, 2000, 5000, 20000]) {
      const cases = sweeps(count);
      const started = performance.now();
      const tree = caseTree(cases, ["case:0", `case:${count - 1}`]);
      const ms = performance.now() - started;
      expect(tree).toHaveLength(Math.ceil(count / 10));
      expect(tree[0]?.children).toHaveLength(9);
      expect(tree[0]?.axis).toBe("読み込み済み");
      expect(tree.flatMap((one) => [one, ...(one.children ?? [])])).toHaveLength(count);
      timings.push(`${count} cases in ${ms.toFixed(1)} ms`);
    }
    console.log(`case tree: ${timings.join("; ")} (this machine)`);
  });
});
