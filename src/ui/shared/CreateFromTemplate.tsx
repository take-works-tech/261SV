/* 「テンプレートから作成」(11_ui.md) - one component wherever a template becomes an item.
 *
 * XC-063 is the whole of it: a template is applied only after its unresolved references are shown.
 * Not counted - listed, with the name and what is missing (XC-090), because "3 unresolved" is a
 * number somebody accepts without reading. Nothing is created until the list has been seen; a
 * template applied over a missing field would produce an item that looks complete and is not.
 */
import { UnresolvedList, type UnresolvedItem } from "./UnresolvedList";

export type TemplateOption = {
  id: string;
  name: string;
  origin: string;
  revision: number;
  /** Empty means everything the template needs is present in this workspace. */
  unresolved: UnresolvedItem[];
};

export function CreateFromTemplate(props: {
  templates: TemplateOption[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: (id: string) => void;
  onCancel?: () => void;
}) {
  const selected = props.templates.find((one) => one.id === props.selectedId) ?? null;
  const blocked = selected !== null && selected.unresolved.length > 0;

  return (
    <section style={{ display: "grid", gap: 8, minWidth: 0 }} aria-label="テンプレートから作成">
      <b className="type-caption">テンプレートから作成</b>

      {props.templates.length === 0 ? (
        <p className="prop-note" style={{ margin: 0 }}>
          使えるテンプレートがありません。ライブラリから取り込むか、既存の項目を保存します
        </p>
      ) : (
        <div style={{ display: "grid", gap: 3 }}>
          {props.templates.map((template) => (
            <button
              key={template.id}
              className="tree-row"
              aria-selected={props.selectedId === template.id}
              onClick={() => props.onSelect(template.id)}
            >
              <span className="label">{template.name}</span>
              <span className="meta">
                {template.origin}・rev {template.revision}
              </span>
              {template.unresolved.length > 0 ? (
                <span className="meta" style={{ color: "var(--state-warn)" }}>
                  未解決 {template.unresolved.length}
                </span>
              ) : null}
            </button>
          ))}
        </div>
      )}

      {selected && selected.unresolved.length > 0 ? (
        <UnresolvedList
          title="このテンプレートが必要とし、このワークスペースに無いもの"
          items={selected.unresolved}
        />
      ) : null}

      <div style={{ display: "flex", gap: 6 }}>
        <button
          className="btn primary"
          disabled={selected === null || blocked}
          title={
            selected === null
              ? "無効：テンプレートが選ばれていません"
              : blocked
                ? "無効：未解決の参照があります。上の一覧を解消してから作成できます（XC-063）"
                : undefined
          }
          onClick={() => selected && props.onCreate(selected.id)}
        >
          作成
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
