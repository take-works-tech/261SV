/* Variable row (11_ui.md): one workspace variable with its value, unit and provenance - the badge
 * travels with the value (INV-013), and an undeclared unit is shown, never papered over (XC-003). */
import { ProvenanceBadge } from "./ProvenanceBadge";
import { QuantityChip } from "./QuantityChip";
import type { Provenance } from "./primitives";

export function VariableRow(props: {
  name: string;
  value: string;
  unit: string | null;
  origin: Provenance;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <button className="tree-row" aria-selected={props.selected ?? false} onClick={props.onSelect}>
      <span className="label">{props.name}</span>
      <QuantityChip value={props.value} unit={props.unit} />
      <ProvenanceBadge origin={props.origin} />
    </button>
  );
}
