/* The latency budgets as numbers (XC-305): within the budget a switch says nothing; over it, the
 * time and the budget, never silence. */
import { describe, expect, test } from "vitest";

import { describeReflection, LAUNCH_BUDGET_SECONDS, SELECTION_BUDGET_MS } from "./budgets";
import { describeStartup } from "./startup";

describe("the latency budgets", () => {
  test("a switch within the budget says nothing, and one over it names the time and the budget", () => {
    expect(describeReflection(108)).toBeNull();
    expect(describeReflection(SELECTION_BUDGET_MS)).toBeNull();
    const over = describeReflection(SELECTION_BUDGET_MS + 234.6);
    expect(over).toContain(`${SELECTION_BUDGET_MS + 235} ms`);
    expect(over).toContain(`予算 ${SELECTION_BUDGET_MS} ms`);
    expect(over).toContain("LIM-011");
  });

  test("a launch past its budget says so on the starting page, with the budget named", () => {
    const within = describeStartup({ kind: "starting", since: null }, LAUNCH_BUDGET_SECONDS - 1);
    expect(within.overBudget).toBe(false);
    expect(within.detail).not.toContain("予算");
    const over = describeStartup({ kind: "starting", since: null }, LAUNCH_BUDGET_SECONDS + 0.2);
    expect(over.overBudget).toBe(true);
    expect(over.detail).toContain(`予算（${LAUNCH_BUDGET_SECONDS} 秒`);
    expect(over.detail).toContain("LIM-010");
  });
});
