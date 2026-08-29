/* Expression editor (11_ui.md): where a derived quantity, a condition or a selection is written.
 *
 * Three things make it this product's editor rather than a text box: the names in scope are listed
 * (an expression referring to a name nobody can see is a guess), the unit signature is checked and
 * shown (INV-020 - a formula that adds MPa to degC is an error the reader should not have to catch),
 * and an unresolvable name is reported AT ITS CHARACTER POSITION rather than as "invalid".
 *
 * It computes nothing. Evaluation belongs to the engine (MOD-004); this is the surface.
 */
import { UnitLabel } from "./UnitLabel";

export type NameInScope = { name: string; unit: string | null; kind: string };

export type ExpressionProblem = {
  /** Zero-based offset into the text, so the surface can point at it rather than describe it. */
  at: number;
  length: number;
  message: string;
};

export function ExpressionEditor(props: {
  value: string;
  onChange?: (text: string) => void;
  namesInScope: NameInScope[];
  /** The unit the expression resolves to, `null` where an operand is undeclared (XC-003). */
  resultUnit?: string | null;
  /** Present when the expression does not resolve; nothing downstream may use it. */
  problem?: ExpressionProblem;
  readOnly?: boolean;
  label?: string;
}) {
  const { value, problem } = props;
  const before = problem ? value.slice(0, problem.at) : value;
  const bad = problem ? value.slice(problem.at, problem.at + problem.length) : "";
  const after = problem ? value.slice(problem.at + problem.length) : "";

  return (
    <div style={{ display: "grid", gap: 6, minWidth: 0 }}>
      {props.label ? <b className="type-caption">{props.label}</b> : null}

      <div
        style={{
          border: `1px solid var(${problem ? "--state-error" : "--line-strong"})`,
          borderRadius: "var(--radius-s)",
          background: "var(--surface-ground)",
          padding: "6px 8px",
          fontFamily: "var(--family-mono)",
          fontSize: "var(--text-body)",
          minWidth: 0,
          overflowX: "auto",
        }}
      >
        {problem ? (
          // The offending run is marked in place: "unresolvable" is a fact about a position.
          <code style={{ whiteSpace: "pre" }}>
            {before}
            <mark
              style={{
                background: "var(--state-error-ground)",
                color: "var(--state-error)",
                textDecoration: "underline wavy",
              }}
            >
              {bad}
            </mark>
            {after}
          </code>
        ) : props.readOnly ? (
          <code style={{ whiteSpace: "pre" }}>{value}</code>
        ) : (
          <input
            value={value}
            onChange={(event) => props.onChange?.(event.target.value)}
            aria-label={props.label ?? "式"}
            spellCheck={false}
            style={{
              width: "100%",
              minWidth: 0,
              border: 0,
              outline: 0,
              background: "transparent",
              color: "var(--ink-strong)",
              font: "inherit",
            }}
          />
        )}
      </div>

      {problem ? (
        <div className="notice error">
          <b>
            {problem.at + 1} 文字目：{problem.message}
          </b>
          <span className="why">解決しない名前があるため、何も選択・計算していません</span>
        </div>
      ) : (
        <p className="prop-note" style={{ margin: 0 }}>
          単位：
          <UnitLabel unit={props.resultUnit ?? null} />
          {props.resultUnit === null
            ? "（被演算子のいずれかが未宣言のため、結果も未宣言のままです）"
            : "（式から導かれた単位です）"}
        </p>
      )}

      <details>
        <summary className="type-caption" style={{ color: "var(--ink-muted)", cursor: "pointer" }}>
          この場で使える名前（{props.namesInScope.length}）
        </summary>
        <div className="table-scroll" style={{ maxHeight: 160, marginTop: 6 }}>
          <table className="value-table">
            <thead>
              <tr>
                <th scope="col">名前</th>
                <th scope="col">種類</th>
                <th scope="col">単位</th>
              </tr>
            </thead>
            <tbody>
              {props.namesInScope.map((one) => (
                <tr key={one.name}>
                  <th scope="row" style={{ fontFamily: "var(--family-mono)" }}>
                    {one.name}
                  </th>
                  <td>{one.kind}</td>
                  <td>
                    <UnitLabel unit={one.unit} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
