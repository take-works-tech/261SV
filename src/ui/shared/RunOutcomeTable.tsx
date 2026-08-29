/* Run outcome table (11_ui.md): unit × case outcomes of one pipeline run. Every cell states what
 * happened - applied, skipped (and why), failed, refused - because a run record that hides a skip
 * reports success for work that never ran (AC-015). */

export type Outcome = "applied" | "skipped" | "failed" | "refused";

const OUTCOME_LABEL: Record<Outcome, string> = {
  applied: "適用",
  skipped: "スキップ",
  failed: "失敗",
  refused: "拒否",
};

export function RunOutcomeTable(props: {
  units: string[];
  cases: string[];
  outcome: (unit: string, kase: string) => { kind: Outcome; note?: string };
}) {
  return (
    <div className="table-scroll">
      <table className="value-table">
        <thead>
          <tr>
            <th scope="col">ケース</th>
            {props.units.map((unit) => (
              <th key={unit} scope="col">{unit}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {props.cases.map((kase) => (
            <tr key={kase}>
              <th scope="row">{kase}</th>
              {props.units.map((unit) => {
                const cell = props.outcome(unit, kase);
                return (
                  <td key={unit} title={cell.note}>
                    <span className={cell.kind === "failed" ? "missing-value" : undefined}>
                      {OUTCOME_LABEL[cell.kind]}
                      {cell.note ? `（${cell.note}）` : ""}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
