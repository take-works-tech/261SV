/* Field selector (11_ui.md): pick a field by name WITH its association - point and cell values of
 * one quantity are different numbers (INV-032), so the association is part of the choice, not a
 * detail hidden behind it. */

export type FieldOption = {
  name: string;
  association: "point" | "cell" | "integrationPoint";
  unit: string | null;
};

const ASSOCIATION_LABEL = { point: "節点", cell: "要素", integrationPoint: "積分点" } as const;

export function FieldSelector(props: {
  fields: FieldOption[];
  value: string | null;
  onChange: (name: string) => void;
  disabled?: boolean;
  disabledReason?: string;
}) {
  return (
    <select
      className="field-input"
      value={props.value ?? ""}
      onChange={(event) => props.onChange(event.target.value)}
      disabled={props.disabled}
      title={props.disabled ? props.disabledReason : undefined}
      aria-label="フィールド"
    >
      {props.value === null ? <option value="">（未選択）</option> : null}
      {props.fields.map((field) => (
        <option key={`${field.name}:${field.association}`} value={field.name}>
          {field.name}（{ASSOCIATION_LABEL[field.association]}
          {field.unit === null ? "・単位未宣言" : `・${field.unit}`}）
        </option>
      ))}
    </select>
  );
}
