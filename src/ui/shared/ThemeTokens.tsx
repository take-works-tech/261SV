/* Theme tokens (11_ui.md): the token layer as a typed surface.
 *
 * `tokens.css` holds the values; this file holds their *names*, so a screen that needs to reference
 * a token programmatically - a swatch in the settings surface, a legend gradient, an inline style -
 * names it through one place instead of spelling `var(--…)` into a string somewhere the linter
 * cannot see. Two layers, as XC-187 requires: primitives are raw steps, semantic names say what a
 * step is for, and product code uses the semantic ones.
 *
 * XC-256: the chrome is monochrome. There is no accent token, and adding one is a decision, not a
 * convenience - the saturated names below belong to data (colour maps) and to the muted semantic
 * trio, which is why they are kept apart from the surface and ink ladders.
 */

export const SURFACE_TOKENS = [
  "--surface-well",
  "--surface-ground",
  "--surface-panel",
  "--surface-raise",
  "--surface-active",
] as const;

export const INK_TOKENS = ["--ink-strong", "--ink", "--ink-muted", "--ink-faint"] as const;

export const LINE_TOKENS = ["--line", "--line-strong"] as const;

/** Data-adjacent, and the only saturation the chrome hosts (XC-256). */
export const STATE_TOKENS = ["--state-good", "--state-warn", "--state-error"] as const;

export const TEXT_TOKENS = [
  "--text-caption",
  "--text-body",
  "--text-emphasis",
  "--text-title",
  "--text-heading",
  "--text-display",
] as const;

export type SurfaceToken = (typeof SURFACE_TOKENS)[number];
export type InkToken = (typeof INK_TOKENS)[number];
export type LineToken = (typeof LINE_TOKENS)[number];
export type StateToken = (typeof STATE_TOKENS)[number];
export type TextToken = (typeof TEXT_TOKENS)[number];
export type ThemeToken = SurfaceToken | InkToken | LineToken | StateToken | TextToken;

/** `var(--token)`, spelled once. A screen that builds an inline style uses this, never a literal. */
export function token(name: ThemeToken): string {
  return `var(${name})`;
}

const LABELS: Partial<Record<ThemeToken, string>> = {
  "--surface-well": "ビューポートの底",
  "--surface-ground": "アプリの地",
  "--surface-panel": "パネル",
  "--surface-raise": "パネル内の段",
  "--surface-active": "選択・押下",
  "--ink-strong": "見出し・値",
  "--ink": "本文",
  "--ink-muted": "副次ラベル",
  "--ink-faint": "無効・プレースホルダ",
  "--line": "パネル内の罫",
  "--line-strong": "パネルの境界",
  "--state-good": "良",
  "--state-warn": "警告",
  "--state-error": "エラー",
};

/** The token ladder, shown as itself - a choice about appearance shown as an appearance (XC-215). */
export function ThemeTokens(props: { tokens?: readonly ThemeToken[] }) {
  const shown = props.tokens ?? [...SURFACE_TOKENS, ...INK_TOKENS, ...LINE_TOKENS, ...STATE_TOKENS];
  return (
    <div style={{ display: "grid", gap: 4 }}>
      {shown.map((name) => (
        <div key={name} style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <span
            aria-hidden
            style={{
              width: 26,
              height: 16,
              flex: "0 0 auto",
              borderRadius: "var(--radius-s)",
              border: `1px solid ${token("--line-strong")}`,
              background: token(name),
            }}
          />
          <code
            className="type-caption"
            style={{ fontFamily: "var(--family-mono)", color: token("--ink-muted") }}
          >
            {name}
          </code>
          <span
            className="type-caption"
            style={{
              minWidth: 0,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              color: token("--ink-faint"),
            }}
          >
            {LABELS[name] ?? ""}
          </span>
        </div>
      ))}
    </div>
  );
}
