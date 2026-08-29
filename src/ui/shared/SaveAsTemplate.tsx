/* 「テンプレートとして保存」(11_ui.md) - one component wherever an item becomes a template.
 *
 * The interesting half is what a template must NOT carry. An item is bound to its cases, its
 * fields and its assets; a template that kept those bindings would apply somebody else's Run 12 to
 * a new workspace and look right doing it. So the bindings that will become requirements are listed
 * before saving, and the ones that stay pinned are listed beside them - the reader decides with
 * both in view (AC-037).
 */

export type Binding = { what: string; boundTo: string };

export function SaveAsTemplate(props: {
  itemName: string;
  /** Bindings that become requirements of the template - the target must supply them. */
  becomeRequirements: Binding[];
  /** Bindings that stay as they are, because they belong to the template rather than to a case. */
  stayPinned: Binding[];
  name: string;
  onName: (text: string) => void;
  onSave: () => void;
  onCancel?: () => void;
}) {
  const nameGiven = props.name.trim() !== "";
  return (
    <section style={{ display: "grid", gap: 8, minWidth: 0 }} aria-label="テンプレートとして保存">
      <b className="type-caption">「{props.itemName}」をテンプレートとして保存</b>

      <div className="prop-row">
        <label htmlFor="tpl-name">テンプレート名</label>
        <input
          id="tpl-name"
          className="field-input"
          value={props.name}
          onChange={(event) => props.onName(event.target.value)}
          placeholder="例：強度確認レポート（社内様式）"
        />
      </div>

      <div>
        <b className="type-caption" style={{ color: "var(--ink-strong)" }}>
          適用先が用意するもの（{props.becomeRequirements.length}）
        </b>
        {props.becomeRequirements.length === 0 ? (
          <p className="prop-note">ありません — この項目はケースにもフィールドにも束縛されていません</p>
        ) : (
          <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
            {props.becomeRequirements.map((binding) => (
              <li key={binding.what} className="type-body">
                {binding.what}
                <span style={{ color: "var(--ink-faint)" }}>（現在：{binding.boundTo}）</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <b className="type-caption" style={{ color: "var(--ink-strong)" }}>
          テンプレートに残るもの（{props.stayPinned.length}）
        </b>
        {props.stayPinned.length === 0 ? (
          <p className="prop-note">ありません</p>
        ) : (
          <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
            {props.stayPinned.map((binding) => (
              <li key={binding.what} className="type-body">
                {binding.what}
                <span style={{ color: "var(--ink-faint)" }}>：{binding.boundTo}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="prop-note" style={{ margin: 0 }}>
        束縛は要件に変わります。残したままにすると、別のワークスペースで他人のケースを指したまま
        正しく見えるテンプレートになります（AC-037）
      </p>

      <div style={{ display: "flex", gap: 6 }}>
        <button
          className="btn primary"
          disabled={!nameGiven}
          title={nameGiven ? undefined : "無効：テンプレート名が要ります"}
          onClick={props.onSave}
        >
          保存
        </button>
        {props.onCancel ? (
          <button className="btn ghost" onClick={props.onCancel}>
            取りやめ
          </button>
        ) : null}
      </div>
    </section>
  );
}
