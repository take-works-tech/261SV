/* Unit label (11_ui.md): a unit as declared, or the undeclared marker - nothing in the interface
 * infers one (XC-003). Undeclared reads as a state to fix, not as an empty string. */
import { UNDECLARED } from "./primitives";

export function UnitLabel(props: { unit: string | null }) {
  if (props.unit === null) {
    return <span className="missing-value">{UNDECLARED}</span>;
  }
  return <span>{props.unit}</span>;
}
