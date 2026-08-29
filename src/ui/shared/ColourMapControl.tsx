/* Colour map control (11_ui.md): choose a map by seeing it - a choice about appearance shown as an
 * appearance (XC-215). The swatch is the one saturated element the chrome hosts, because the map IS
 * data (XC-256); a map that is not perceptually uniform carries a note (XC-111). */

export type ColourMapId = "viridis" | "plasma" | "greys";

const MAPS: { id: ColourMapId; name: string; uniform: boolean }[] = [
  { id: "viridis", name: "Viridis", uniform: true },
  { id: "plasma", name: "Plasma", uniform: true },
  { id: "greys", name: "グレー", uniform: true },
];

export function ColourMapControl(props: {
  value: ColourMapId;
  onChange: (id: ColourMapId) => void;
}) {
  return (
    <div role="radiogroup" aria-label="カラーマップ" style={{ display: "flex", gap: 6 }}>
      {MAPS.map((map) => (
        <button
          key={map.id}
          role="radio"
          aria-checked={props.value === map.id}
          className="shelf-card"
          style={{ width: 72 }}
          onClick={() => props.onChange(map.id)}
        >
          <span
            className="thumb"
            style={{ backgroundImage: `var(--map-${map.id})`, height: 18 }}
            aria-hidden
          />
          <span className="name">{map.name}</span>
        </button>
      ))}
    </div>
  );
}
