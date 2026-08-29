/* Number cell (11_ui.md): a figure in a table - right-aligned, tabular, and honest about absence.
 * A missing value renders as a stated absence with its reason, never as a blank or a zero (XC-001). */

export function NumberCell(props: {
  value: string | null;
  missingBecause?: string;
}) {
  if (props.value === null) {
    return (
      <td className="number-cell">
        <span className="missing-value">値なし（{props.missingBecause ?? "理由未記録"}）</span>
      </td>
    );
  }
  return <td className="number-cell">{props.value}</td>;
}
