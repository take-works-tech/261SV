/* The viewport as a design state. The production renderer is vtk.js reached through the decided
 * paths (XC-087, XC-251); drawing a fake part here with a 3D library would prejudge that decision
 * and make the mockup look like evidence of implemented behaviour, which it never is. What this
 * placeholder does show truthfully: the well is the darkest surface on screen, the legend owns the
 * only saturation (XC-256), the pane badge names its case (XC-202), and a reduced display says so.
 */
import type { ColourMapId } from "./ColourMapControl";

export function ViewportPlaceholder(props: {
  caseName: string;
  fieldLabel?: string;
  map?: ColourMapId;
  legendTicks?: string[];
  reducedNote?: string;
  children?: React.ReactNode;
}) {
  const map = props.map ?? "viridis";
  return (
    <div className="viewport-pane">
      <div className="pane-badge">
        <b>{props.caseName}</b>
        {props.fieldLabel ? <span>{props.fieldLabel}</span> : null}
      </div>

      {/* A monochrome silhouette stands in for geometry - deliberately not a rendering. */}
      <svg
        viewBox="0 0 400 300"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        aria-label="表示領域（設計状態 - 実描画ではありません）"
        role="img"
      >
        <g fill="none" stroke="var(--ink-faint)" strokeWidth="1">
          <path d="M120 210 L200 90 L290 150 L268 226 L160 240 Z" />
          <path d="M200 90 L214 132 L290 150" />
          <path d="M214 132 L188 196 L160 240" />
          <path d="M188 196 L268 226" />
          <path d="M120 210 L188 196" />
        </g>
        <g stroke="var(--g-ink-faint)" strokeWidth="1" opacity="0.5">
          <line x1="30" y1="270" x2="70" y2="270" />
          <line x1="30" y1="270" x2="30" y2="230" />
          <line x1="30" y1="270" x2="56" y2="288" />
        </g>
      </svg>

      {props.fieldLabel ? (
        <div className="legend">
          <span className="title">{props.fieldLabel}</span>
          <span className="bar" style={{ backgroundImage: `var(--map-${map})` }} />
          <span className="ticks">
            {(props.legendTicks ?? ["200", "150", "100", "50", "0"]).map((tick) => (
              <span key={tick}>{tick}</span>
            ))}
          </span>
        </div>
      ) : null}

      {props.reducedNote ? (
        <div
          className="pane-badge"
          style={{ top: "auto", bottom: 8, left: 8 }}
          role="note"
        >
          表示は簡略化：{props.reducedNote}（数値は完全データ）
        </div>
      ) : null}

      {props.children}
    </div>
  );
}
