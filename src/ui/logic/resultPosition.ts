/* The result position as the interface handles it (XC-283): the steps the file declared, as
 * `dataset.describe` listed them, and the step a value is of, as the engine's answers state it beside
 * every number (CT-003 3.10.0, view/AC-032). A step is an ordinal along the declared sequence, counted
 * from 0 in every request and from 1 in every sentence. The sentence that carries the declared value
 * is the engine's (`stated`), so one number is spelled one way everywhere; what is built here names
 * the step and no value. No React and no transport. */
import type { Results } from "../client/engine";
import type { EngineState, StatedPosition } from "../state/engine";

export type Described = Results["dataset.describe"] | null;

export interface AxisSteps {
  /** How many steps there are to move between: 1 for a steady result. */
  count: number;
  /** The value the file declared at each step, or null where it declared none. */
  positions: readonly number[] | null;
  kind: string;
}

/** The steps of the loaded case from the engine's description, or null where nothing is described. */
export function axisSteps(described: Described): AxisSteps | null {
  const axis = described?.resultAxis;
  if (!axis) return null;
  const positions = axis.positions ?? null;
  return { count: Math.max(1, axis.count ?? positions?.length ?? 1), positions, kind: axis.kind };
}

/** Whether there is anything to move along: more than one step. */
export function hasSteps(steps: AxisSteps | null): steps is AxisSteps {
  return steps !== null && steps.count > 1;
}

/** A step by its ordinal, counted from 1, and nothing else: the value the file declared there is
 *  said by the engine, in the answer that carries the number (view/AC-032). */
export function describeStep(steps: AxisSteps, step: number): string {
  return `ステップ ${step + 1}/${steps.count}`;
}

/** The step the view is at, in the engine's words where it has answered for that step - the
 *  statistics are asked for at every move - and by its ordinal alone while it has not. */
export function currentStep(state: Pick<EngineState, "described" | "step" | "statistics">): string | null {
  const steps = axisSteps(state.described);
  if (!hasSteps(steps)) return null;
  const stated: StatedPosition | undefined = state.statistics?.resultPosition;
  return stated && stated.step === state.step ? stated.stated : describeStep(steps, state.step);
}

/** Why a move in `direction` from `step` is not offered, or null where it is. The ends are the
 *  ends: nothing past them exists to move to (view/AC-033). */
export function endReason(steps: AxisSteps, step: number, direction: -1 | 1): string | null {
  if (direction < 0 && step <= 0) return "先頭のステップです";
  if (direction > 0 && step >= steps.count - 1) return "末尾のステップです";
  return null;
}
