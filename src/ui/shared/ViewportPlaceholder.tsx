/* The viewport as a design state. The production renderer is vtk.js reached through the decided
 * paths (XC-087, XC-251); drawing a fake part here with a 3D library would prejudge that decision
 * and make the mockup look like evidence of implemented behaviour, which it never is. What this
 * placeholder does show truthfully: the well is the darkest surface on screen, the legend owns the
 * only saturation (XC-256), the pane badge names its case (XC-202), and a reduced display says so.
 */
import { useRef } from "react";
import type { ColourMapId } from "./ColourMapControl";

export function ViewportPlaceholder(props: {
  caseName: string;
  fieldLabel?: string;
  map?: ColourMapId;
  legendTicks?: string[];
  reducedNote?: string;
  children?: React.ReactNode;
  /** A frame the engine drew, when one exists. With it this is not a placeholder at all: the
   *  silhouette is replaced by the picture, and the label stops saying "design state" because it no
   *  longer is one. Without it nothing changes - the catalogue of design states is what it was. */
  imageUrl?: string | null;
  /** Turn the model. The numbers are pixels the pointer moved, and what that means for the camera is
   *  the layer above's - this component knows where a pointer went and nothing about geometry. */
  onOrbit?: (byPixels: { x: number; y: number }) => void;
  /** Read the value under a click, as a pixel **of the drawn frame**. The conversion from where the
   *  image is on screen to where it is in the frame happens here because only here are both known;
   *  what that pixel means is the engine's, which is the only place the camera exists. */
  onPickPixel?: (atPixel: { x: number; y: number }) => void;
}) {
  const map = props.map ?? "viridis";
  const drawn = Boolean(props.imageUrl);
  const dragged = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const interactive = drawn && (props.onOrbit || props.onPickPixel);
  return (
    <div
      className="viewport-pane"
      style={interactive ? { cursor: "grab" } : undefined}
      onPointerDown={
        interactive
          ? (event) => {
              dragged.current = { x: event.clientX, y: event.clientY, moved: false };
              event.currentTarget.setPointerCapture(event.pointerId);
            }
          : undefined
      }
      onPointerMove={
        props.onOrbit && drawn
          ? (event) => {
              const from = dragged.current;
              if (!from) return;
              const dx = event.clientX - from.x;
              const dy = event.clientY - from.y;
              if (Math.abs(dx) + Math.abs(dy) < 3) return;
              dragged.current = { x: event.clientX, y: event.clientY, moved: true };
              props.onOrbit?.({ x: dx, y: dy });
            }
          : undefined
      }
      onPointerUp={
        interactive
          ? (event) => {
              const from = dragged.current;
              dragged.current = null;
              if (!from || from.moved || !props.onPickPixel) return;
              // A click, not a drag. The image is letterboxed inside the pane (`object-fit:
              // contain`), so the pixel of the frame is found from where the image actually sits -
              // reading the pane's own fraction would name a pixel the picture does not have there.
              const image = event.currentTarget.querySelector("img");
              if (!image) return;
              const box = image.getBoundingClientRect();
              const scale = Math.min(box.width / image.naturalWidth, box.height / image.naturalHeight);
              const drawnWidth = image.naturalWidth * scale;
              const drawnHeight = image.naturalHeight * scale;
              const left = box.left + (box.width - drawnWidth) / 2;
              const top = box.top + (box.height - drawnHeight) / 2;
              const x = (event.clientX - left) / scale;
              const y = (event.clientY - top) / scale;
              if (x < 0 || y < 0 || x >= image.naturalWidth || y >= image.naturalHeight) return;
              props.onPickPixel({ x, y });
            }
          : undefined
      }
    >
      <div className="pane-badge">
        <b>{props.caseName}</b>
        {props.fieldLabel ? <span>{props.fieldLabel}</span> : null}
      </div>

      {drawn ? (
        <img
          src={props.imageUrl ?? undefined}
          alt={`${props.caseName}${props.fieldLabel ? "・" + props.fieldLabel : ""}`}
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "contain" }}
        />
      ) : (
      /* A monochrome silhouette stands in for geometry - deliberately not a rendering. */
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
      )}

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
