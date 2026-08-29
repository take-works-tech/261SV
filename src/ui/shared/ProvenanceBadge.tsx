/* Provenance badge (11_ui.md): where a value came from, shown wherever the value is (INV-013).
 * The five origins are GL-016's; the badge never guesses and never disappears. */
import { PROVENANCE_LABEL, type Provenance } from "./primitives";

export function ProvenanceBadge(props: { origin: Provenance }) {
  return (
    <span className="provenance-badge" title={`来歴：${PROVENANCE_LABEL[props.origin]}`}>
      {PROVENANCE_LABEL[props.origin]}
    </span>
  );
}
