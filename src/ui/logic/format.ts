/* Formatting for display (MOD-015): how a value is written for a person to read.
 * No React and no transport here - a rule that can only be exercised by rendering a component is a
 * rule nobody tests (01_boundaries.md). The digits rule is INV-014: show what the source supports,
 * and no more. */

/** A value at the digits it honestly carries - never the storage's full expansion. */
export function formatValue(value: number, digits: number): string {
  if (!Number.isFinite(value)) return String(value);
  const shown = Number(value.toPrecision(Math.max(1, digits)));
  // toPrecision produces exponent notation for large magnitudes; keep it - a padded decimal
  // expansion would claim digits the source never had.
  return Math.abs(shown) >= 1e6 || (shown !== 0 && Math.abs(shown) < 1e-4)
    ? shown.toExponential(Math.max(0, digits - 1))
    : String(shown);
}

/** A byte count for people. Powers of 1024, labelled as such. */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KiB", "MiB", "GiB"] as const;
  let value = bytes;
  let unit = "B";
  for (const next of units) {
    if (value < 1024) break;
    value /= 1024;
    unit = next;
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ${unit}`;
}

/** Why a control is disabled, composed once so every surface words it the same way. */
export function disabledBecause(reason: string): { disabled: true; title: string } {
  return { disabled: true, title: `無効：${reason}` };
}
