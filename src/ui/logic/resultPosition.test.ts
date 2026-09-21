/* The result position as the interface handles it: the steps from the engine's description, the
 * sentence from the engine's answer, and only an ordinal built here (XC-283). */
import { describe, expect, test } from "vitest";

import { snapshot } from "../state/engine";
import { axisSteps, currentStep, describeStep, endReason, hasSteps } from "./resultPosition";

const TRANSIENT = {
  pointCount: 4,
  cellCount: 2,
  boundsM: { minM: [0, 0, 0], maxM: [1, 1, 0] },
  partial: false,
  resultAxis: { kind: "undeclared" as const, positions: [0, 0.5], count: 2, unit: null },
};

const STEADY = { ...TRANSIENT, resultAxis: { kind: "none" as const, unit: null } };

const STATED = { step: 1, count: 2, kind: "undeclared" as const, value: 0.5, unit: null, stated: "ステップ 2/2（位置 0.5・軸の種類は宣言なし）" };

describe("the steps the file declared", () => {
  test("come from the description, with the count the engine gave", () => {
    expect(axisSteps(TRANSIENT)).toEqual({ count: 2, positions: [0, 0.5], kind: "undeclared" });
    expect(hasSteps(axisSteps(TRANSIENT))).toBe(true);
  });

  test("a steady result is one step and nothing to move along", () => {
    expect(axisSteps(STEADY)).toEqual({ count: 1, positions: null, kind: "none" });
    expect(hasSteps(axisSteps(STEADY))).toBe(false);
    expect(hasSteps(axisSteps(null))).toBe(false);
  });

  test("a count the engine did not give is the length of the positions, never more", () => {
    const described = { ...TRANSIENT, resultAxis: { kind: "undeclared" as const, positions: [0, 1, 2], unit: null } };
    expect(axisSteps(described)?.count).toBe(3);
  });
});

describe("the step as a sentence", () => {
  test("built here is the ordinal from 1 and no value: the value is the engine's to say", () => {
    const steps = axisSteps(TRANSIENT);
    if (!steps) throw new Error("described");
    expect(describeStep(steps, 0)).toBe("ステップ 1/2");
    expect(describeStep(steps, 1)).toBe("ステップ 2/2");
  });

  test("the current step is the engine's sentence once it has answered for that step", () => {
    const base = { ...snapshot(), described: TRANSIENT };
    expect(currentStep({ ...base, step: 1, statistics: null })).toBe("ステップ 2/2");
    const statistics = { ...(snapshot().statistics as object), resultPosition: STATED } as NonNullable<ReturnType<typeof snapshot>["statistics"]>;
    expect(currentStep({ ...base, step: 1, statistics })).toBe("ステップ 2/2（位置 0.5・軸の種類は宣言なし）");
    // An answer for another step is not this step's sentence.
    expect(currentStep({ ...base, step: 0, statistics })).toBe("ステップ 1/2");
    expect(currentStep({ ...base, described: STEADY, step: 0, statistics })).toBeNull();
  });
});

describe("the ends of the axis", () => {
  test("say why there is nowhere further to go, and nothing else is refused", () => {
    const steps = axisSteps(TRANSIENT);
    if (!steps) throw new Error("described");
    expect(endReason(steps, 0, -1)).toBe("先頭のステップです");
    expect(endReason(steps, 0, 1)).toBeNull();
    expect(endReason(steps, 1, 1)).toBe("末尾のステップです");
    expect(endReason(steps, 1, -1)).toBeNull();
  });
});
