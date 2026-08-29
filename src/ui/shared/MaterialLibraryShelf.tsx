/* Material library shelf (11_ui.md): the resource strip docked below the canvas.
 *
 * Six states, and they are states of the shelf rather than six shelves: collapsed (title bar only),
 * one-row (the default), expanded (vertical growth), narrow (a bottom drawer, because a shelf
 * squeezed below its card width stops being scannable), searching (filters, sample-vs-original,
 * sort), selected (an asset is chosen; applying it is a separate, explicit act - selecting is not
 * applying).
 *
 * An asset is shown as itself (XC-215): a material as its own swatch, a colour map as its ramp. A
 * missing thumbnail is NAMED rather than drawn as an empty tile - the reader must be able to tell
 * "no picture" from "a picture of nothing".
 */

export type ShelfState =
  | "collapsed"
  | "one-row"
  | "expanded"
  | "narrow"
  | "searching"
  | "selected";

export type ShelfAsset = {
  id: string;
  name: string;
  /** The asset drawn as itself: a CSS background (gradient, swatch) or a source path. */
  swatch?: string;
  source: "sample" | "workspace" | "shared";
  /** Stated rather than implied: a sample-derived copy whose origin has a newer version (XC-130). */
  newerSampleExists?: boolean;
};

const SOURCE_LABEL = { sample: "サンプル", workspace: "ワークスペース", shared: "共有" } as const;

export function MaterialLibraryShelf(props: {
  title: string;
  categories: string[];
  activeCategory?: string;
  assets: ShelfAsset[];
  state: ShelfState;
  selectedId?: string | null;
  query?: string;
  onSelect?: (id: string) => void;
  onApply?: (id: string) => void;
  onCategory?: (category: string) => void;
  onQuery?: (text: string) => void;
}) {
  const { state } = props;
  const rows = state === "expanded" ? 2 : 1;
  const visible =
    state === "searching" && props.query
      ? props.assets.filter((asset) => asset.name.includes(props.query ?? ""))
      : props.assets;

  return (
    <div className="shelf">
      <header>
        <b>{props.title}</b>
        {state !== "collapsed" && state !== "narrow" ? (
          <span style={{ display: "flex", gap: 2 }}>
            {props.categories.map((category) => (
              <button
                key={category}
                className="btn ghost"
                aria-pressed={category === props.activeCategory}
                onClick={() => props.onCategory?.(category)}
              >
                {category}
              </button>
            ))}
          </span>
        ) : null}
        {state === "searching" ? (
          <span className="side-search" style={{ margin: 0, height: 24 }}>
            <input
              value={props.query ?? ""}
              onChange={(event) => props.onQuery?.(event.target.value)}
              placeholder="資産を検索"
              aria-label="資産を検索"
            />
          </span>
        ) : null}
        <span className="type-caption" style={{ marginLeft: "auto", color: "var(--ink-faint)" }}>
          {state === "collapsed"
            ? "見出しのみ（開くと資産が並びます）"
            : state === "narrow"
              ? "幅が足りないため、下段のドロワーで開きます"
              : `${visible.length} 件`}
        </span>
      </header>

      {state === "collapsed" || state === "narrow" ? null : visible.length === 0 ? (
        <p className="prop-note" style={{ padding: "0 10px 10px" }}>
          この条件に一致する資産はありません。検索語を外すと全件に戻ります
        </p>
      ) : (
        Array.from({ length: rows }, (_, row) => (
          <div className="shelf-row" key={row}>
            {visible.map((asset) => (
              <button
                key={`${row}:${asset.id}`}
                className="shelf-card"
                aria-pressed={state === "selected" && props.selectedId === asset.id}
                title={
                  state === "selected" && props.selectedId === asset.id
                    ? "選択中 — 適用は「適用」かドラッグで（選ぶことは当てることではありません）"
                    : `${asset.name}（${SOURCE_LABEL[asset.source]}）`
                }
                onClick={() => props.onSelect?.(asset.id)}
                onDoubleClick={() => props.onApply?.(asset.id)}
              >
                <span
                  className="thumb"
                  style={asset.swatch ? { background: asset.swatch } : undefined}
                  aria-hidden={asset.swatch ? true : undefined}
                >
                  {asset.swatch ? "" : "画像なし"}
                </span>
                <span className="name">{asset.name}</span>
                <span className="type-caption" style={{ color: "var(--ink-faint)" }}>
                  {SOURCE_LABEL[asset.source]}
                  {asset.newerSampleExists ? "・元に新版" : ""}
                </span>
              </button>
            ))}
          </div>
        ))
      )}
    </div>
  );
}
