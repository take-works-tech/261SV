/* Unresolved list (11_ui.md): what did not resolve, named - the name and what is missing, both
 * (XC-090). A count alone is something somebody accepts without reading. */

export type UnresolvedItem = { what: string; missing: string };

export function UnresolvedList(props: { items: UnresolvedItem[]; title?: string }) {
  if (props.items.length === 0) return null;
  return (
    <div className="unresolved-list" role="status">
      {props.title ? <b className="type-caption">{props.title}</b> : null}
      {props.items.map((item) => (
        <div key={item.what} className="notice warn">
          <b>{item.what}</b>
          <span className="why">不足：{item.missing}</span>
        </div>
      ))}
    </div>
  );
}
