/* Quantity chip (11_ui.md): one value with its unit - or the undeclared marker - and its digits.
 * The unit is never inferred (XC-003); `digits` is what the source honestly supports (INV-014). */
import { UNDECLARED } from "./primitives";

export function QuantityChip(props: {
  value: string;
  unit: string | null;
  title?: string;
}) {
  const undeclared = props.unit === null;
  return (
    <span className="quantity-chip" title={props.title}>
      <span className="value">{props.value}</span>
      <span className={undeclared ? "unit undeclared" : "unit"}>
        {undeclared ? UNDECLARED : props.unit}
      </span>
    </span>
  );
}
