/* Probe readout (11_ui.md): the value under the pick - with unit, digits, provenance and the
 * source's own location words (INV-023: GlobalNodeId, never an array index). Holding it as a
 * variable is an explicit act, not a side effect. */
import { ProvenanceBadge } from "./ProvenanceBadge";
import { QuantityChip } from "./QuantityChip";
import type { Provenance } from "./primitives";

export function ProbeReadout(props: {
  field: string;
  value: string;
  unit: string | null;
  origin: Provenance;
  location: string;
  onHold?: () => void;
}) {
  return (
    <div className="probe-readout" role="status">
      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <b>{props.field}</b>
        <QuantityChip value={props.value} unit={props.unit} />
        <ProvenanceBadge origin={props.origin} />
      </div>
      <span className="type-caption" style={{ color: "var(--ink-muted)" }}>
        位置 {props.location}
      </span>
      {props.onHold ? (
        <button className="btn ghost" onClick={props.onHold} style={{ justifySelf: "start" }}>
          変数として保持
        </button>
      ) : null}
    </div>
  );
}
