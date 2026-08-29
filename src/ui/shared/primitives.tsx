/* The trustworthy-number primitives and small shared pieces (MOD-010).
 *
 * Presentational only: MOD-010 depends on domain-core alone, so nothing here reads session state -
 * every value arrives as a prop. Each named component of specs/11_ui.md has exactly one
 * implementation file in this directory; `check_commands.py` fails a second one by filename.
 *
 * A number never appears without its unit or the undeclared marker (XC-003); a missing value is a
 * stated absence, never a blank (XC-001); provenance travels with the value (INV-013, GL-016).
 */
import type { ReactNode } from "react";

export const UNDECLARED = "単位未宣言";

export type Provenance = "declared" | "dataset" | "computed" | "measured" | "reference";

export const PROVENANCE_LABEL: Record<Provenance, string> = {
  declared: "宣言",
  dataset: "データ",
  computed: "計算",
  measured: "実測",
  reference: "資料",
};

export function Chrome({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
