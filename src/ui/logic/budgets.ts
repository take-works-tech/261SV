/* The latency budgets, as numbers (XC-305; LIM-010, LIM-011): set from measurements taken here
 * (E-222, E-223) against the published limits of attention (E-224), said on screen when exceeded,
 * and never raised to fit the code. One definition each: specs/05_limits.md names this file as the
 * source of truth for both, and the linter holds the two to each other. No React and no transport. */

/** specs/05_limits.md LIM-010: seconds from launch to a rendered sample result, on a warm file cache
 *  and the hardware class of E-063. Measured here at about 0.63 s packaged and warm and 1.05 s on
 *  the first launch after packaging (E-222); three seconds keeps the ten-second limit of attention
 *  (E-224) far off while leaving room for a slower disk than this one. */
export const LAUNCH_BUDGET_SECONDS = 3;

/** specs/05_limits.md LIM-011: milliseconds from selecting a case to every area reflecting it.
 *  Measured here at 99-110 ms with both cases loaded (E-223); one second is the limit for the
 *  flow of thought to stay uninterrupted (E-224), which is what "reflected at once" has to mean. */
export const SELECTION_BUDGET_MS = 1000;

/** What a switch that took `ms` says of itself, when it has anything to say: nothing within the
 *  budget, and the time with the budget beside it when over - never absorbed into silence. */
export function describeReflection(ms: number): string | null {
  if (ms <= SELECTION_BUDGET_MS) return null;
  return `ケースの反映に ${Math.round(ms)} ms かかりました（予算 ${SELECTION_BUDGET_MS} ms、LIM-011）`;
}
