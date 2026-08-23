'use client'

// XC-215: a choice about how something will look is shown as how it will look. Both measured references
// do this rather than listing names - ParaView renders every colour-map preset to a pixmap for its
// preset dialog (`pqPresetToPixmap`, reflowed into a grid), and Blender ships the matcap, studio and
// world previews as image files it draws into the picker (E-128).
//
// The samples here are drawn, not loaded: inline SVG and CSS gradients, so they carry no asset, follow
// the theme tokens, and stay crisp at any scale. They are illustrations of a design state, never
// evidence that the renderer produces this picture.

export type SampleKind =
  | 'chart'
  | 'palette'
  | 'surface'
  | 'line'
  | 'marker'
  | 'page'
  | 'columns'
  | 'margin'
  | 'figure'
  | 'background'
  | 'representation'
  | 'grade'

const palettes: Record<string, string[]> = {
  accessible: ['#2f6df6', '#e8710a', '#12876f', '#8c4bd8', '#c62b5b'],
  monochrome: ['#1d2b33', '#46606e', '#7b939f', '#adc0c9', '#dbe4e9'],
  print: ['#1b3b6f', '#5a7ca8', '#9aaec6', '#c9d4e0', '#eef2f6'],
}

// One band per develop preset, matching the exposure and tone map each one names. `measurement` is the
// ungraded ramp, so it is the one the others are read against.
const gradeStops: Record<string, string> = {
  measurement: 'linear-gradient(90deg, #10161b, #6b7d88, #f2f5f7)',
  standard: 'linear-gradient(90deg, #141b21, #6f8290, #eef3f6)',
  technicalDocument: 'linear-gradient(90deg, #1b242b, #8497a2, #ffffff)',
  presentation: 'linear-gradient(90deg, #0b1116, #6d8494, #f6fbfd)',
  photoreal: 'linear-gradient(90deg, #14100d, #86776a, #fdf7ee)',
}

function Frame({ children, tone = 'light' }: { children: React.ReactNode; tone?: 'light' | 'dark' }) {
  return (
    <svg viewBox="0 0 48 32" className={`option-sample-svg ${tone}`} aria-hidden="true" focusable="false">
      {children}
    </svg>
  )
}

function ChartSample({ value }: { value: string }) {
  if (value === 'scatter' || value === 'scatter3d') {
    const points = [[8, 24], [15, 18], [21, 21], [27, 12], [33, 15], [39, 8]]
    return <Frame>{points.map(([x, y]) => <circle key={`${x}`} cx={x} cy={y} r="2.1" />)}</Frame>
  }
  if (value === 'bar') {
    const bars = [[8, 12], [16, 20], [24, 8], [32, 16], [40, 22]]
    return <Frame>{bars.map(([x, h]) => <rect key={`${x}`} x={x - 3} y={28 - h} width="6" height={h} rx="1" />)}</Frame>
  }
  if (value === 'distribution') {
    return <Frame><path d="M4 28 C 14 28, 14 6, 24 6 C 34 6, 34 28, 44 28 Z" /></Frame>
  }
  if (value === 'heatmap') {
    const cells = [0.15, 0.4, 0.75, 0.95, 0.3, 0.6, 0.85, 0.5, 0.2, 0.45, 0.7, 0.35]
    return (
      <Frame>
        {cells.map((v, i) => (
          <rect key={i} x={6 + (i % 4) * 9} y={6 + Math.floor(i / 4) * 7} width="8" height="6" opacity={0.2 + v * 0.8} />
        ))}
      </Frame>
    )
  }
  if (value === 'surface') {
    return (
      <Frame>
        <path d="M6 22 L18 12 L30 18 L42 9" fill="none" strokeWidth="1.6" />
        <path d="M6 27 L18 17 L30 23 L42 14" fill="none" strokeWidth="1.6" opacity=".55" />
        <path d="M6 22 L6 27 M18 12 L18 17 M30 18 L30 23 M42 9 L42 14" fill="none" strokeWidth="1.1" opacity=".35" />
      </Frame>
    )
  }
  if (value === 'contour3d') {
    return (
      <Frame>
        <ellipse cx="24" cy="16" rx="17" ry="10" fill="none" strokeWidth="1.4" />
        <ellipse cx="24" cy="16" rx="11" ry="6.5" fill="none" strokeWidth="1.4" opacity=".7" />
        <ellipse cx="24" cy="16" rx="5" ry="3" fill="none" strokeWidth="1.4" opacity=".45" />
      </Frame>
    )
  }
  return (
    <Frame>
      <path d="M5 25 L14 14 L22 19 L31 8 L43 12" fill="none" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </Frame>
  )
}

function LineSample({ value }: { value: string }) {
  if (value === 'none') return <Frame><circle cx="24" cy="16" r="2.4" /></Frame>
  const dash = value === 'dashed' ? '7 4' : value === 'dotted' ? '1.5 4' : undefined
  return <Frame><path d="M4 16 H44" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeDasharray={dash} /></Frame>
}

function MarkerSample({ value }: { value: string }) {
  const at = [12, 24, 36]
  if (value === 'none') return <Frame><path d="M4 16 H44" fill="none" strokeWidth="2" strokeLinecap="round" /></Frame>
  return (
    <Frame>
      <path d="M4 16 H44" fill="none" strokeWidth="1.4" opacity=".45" />
      {at.map((x) =>
        value === 'square' ? <rect key={x} x={x - 3} y={13} width="6" height="6" rx="1" />
          : value === 'triangle' ? <path key={x} d={`M${x} 12 L${x + 3.4} 19 L${x - 3.4} 19 Z`} />
            : <circle key={x} cx={x} cy="16" r="3.2" />)}
    </Frame>
  )
}

function PageSample({ value }: { value: string }) {
  const landscape = value === 'landscape' || value === 'screen'
  const w = landscape ? 34 : 22
  const h = landscape ? 24 : 28
  return (
    <Frame>
      <rect x={(48 - w) / 2} y={(32 - h) / 2} width={w} height={h} rx="1.5" fill="none" strokeWidth="1.6" />
      {[0, 1, 2].map((i) => (
        <rect key={i} x={(48 - w) / 2 + 3} y={(32 - h) / 2 + 5 + i * 5} width={w - 6} height="2" rx="1" opacity=".38" />
      ))}
    </Frame>
  )
}

function MarginSample({ value }: { value: string }) {
  const inset = value === 'narrow' ? 2.5 : value === 'wide' ? 7 : 4.5
  return (
    <Frame>
      <rect x="12" y="2" width="24" height="28" rx="1.5" fill="none" strokeWidth="1.6" />
      <rect x={12 + inset} y={2 + inset} width={24 - inset * 2} height={28 - inset * 2} rx="1" opacity=".28" />
    </Frame>
  )
}

function ColumnsSample({ value }: { value: string }) {
  const columns = value === 'double' ? 2 : 1
  const gap = 3
  const inner = 24 - (columns - 1) * gap
  const width = inner / columns
  return (
    <Frame>
      <rect x="12" y="2" width="24" height="28" rx="1.5" fill="none" strokeWidth="1.6" />
      {Array.from({ length: columns }, (_, i) => (
        <rect key={i} x={12 + i * (width + gap)} y="6" width={width} height="20" rx="1" opacity=".28" />
      ))}
    </Frame>
  )
}

function FigureSample({ value }: { value: string }) {
  const bordered = value === 'bordered'
  return (
    <Frame>
      <rect x="6" y="6" width="36" height="20" rx="1.5" fill="none" strokeWidth={bordered ? 1.8 : 0} opacity={bordered ? 1 : 0} />
      {[0, 1, 2].map((i) => (
        <rect key={i} x="9" y={9 + i * 5.5} width="30" height="3.6" rx="1" opacity={i % 2 === 0 ? 0.32 : 0.14} />
      ))}
    </Frame>
  )
}

function RepresentationSample({ value }: { value: string }) {
  if (value === 'points') {
    const dots = [[14, 12], [22, 9], [30, 13], [18, 20], [26, 22], [34, 18], [12, 22], [38, 11]]
    return <Frame>{dots.map(([x, y]) => <circle key={`${x}-${y}`} cx={x} cy={y} r="1.7" />)}</Frame>
  }
  if (value === 'wireframe' || value === 'surface-with-edges' || value === 'surface-edges') {
    return (
      <Frame>
        {value !== 'wireframe' && <path d="M10 24 L18 8 L30 8 L38 24 Z" opacity=".22" />}
        <path d="M10 24 L18 8 L30 8 L38 24 Z M18 8 L24 24 M30 8 L24 24 M10 24 L30 8 M38 24 L18 8" fill="none" strokeWidth="1.2" />
      </Frame>
    )
  }
  return <Frame><path d="M10 24 L18 8 L30 8 L38 24 Z" /></Frame>
}

/** One option's picture. Kinds that are a band of colour render as a div; the rest are drawn SVG. */
export function OptionSample({ kind, value }: { kind: SampleKind; value: string }) {
  if (kind === 'palette') {
    const swatches = palettes[value] ?? palettes.accessible
    return (
      <span className="option-sample-strip" aria-hidden="true">
        {swatches.map((colour) => <i key={colour} style={{ background: colour }} />)}
      </span>
    )
  }
  if (kind === 'grade') {
    return <span className="option-sample-band" aria-hidden="true" style={{ background: gradeStops[value] ?? gradeStops.measurement }} />
  }
  if (kind === 'background') {
    const fills: Record<string, string> = {
      light: '#f4f7f9',
      dark: '#16202a',
      transparent: 'repeating-conic-gradient(#dfe6ea 0% 25%, #ffffff 0% 50%) 0 0 / 10px 10px',
      solid: '#3d5666',
      gradient: 'linear-gradient(160deg, #2b4d68, #b9cdd8)',
      image: 'linear-gradient(160deg, #4b6b52, #cfd8b6)',
      environment: 'conic-gradient(from 210deg, #24384a, #7fa5bd, #e8eef2, #24384a)',
    }
    return <span className="option-sample-band" aria-hidden="true" style={{ background: fills[value] ?? fills.light }} />
  }
  if (kind === 'chart' || kind === 'surface') return <ChartSample value={value} />
  if (kind === 'line') return <LineSample value={value} />
  if (kind === 'marker') return <MarkerSample value={value} />
  if (kind === 'page') return <PageSample value={value} />
  if (kind === 'margin') return <MarginSample value={value} />
  if (kind === 'columns') return <ColumnsSample value={value} />
  if (kind === 'figure') return <FigureSample value={value} />
  return <RepresentationSample value={value} />
}

/**
 * `sample` draws something other than the option's own value. It exists for one option: the one that
 * means "follow the theme", whose picture has to be whatever the theme currently resolves to (XC-221).
 */
export type VisualOption = { value: string; label: string; detail?: string; sample?: string }

/**
 * A single-choice control whose options are pictures with their names beneath. It replaces a `<select>`
 * wherever the thing being chosen is visual (XC-215). The name stays on screen: a picture alone cannot
 * be searched, read aloud, or quoted in a specification.
 */
export function VisualOptions({
  label,
  kind,
  options,
  value,
  onChange,
  columns = 3,
}: {
  label: string
  kind: SampleKind
  options: VisualOption[]
  value: string
  onChange: (value: string) => void
  columns?: number
}) {
  return (
    <div className="visual-options-field">
      <span className="visual-options-label">{label}</span>
      <div
        className="visual-options"
        role="radiogroup"
        aria-label={label}
        style={{ '--visual-option-columns': columns } as React.CSSProperties}
      >
        {options.map((option) => (
          <button
            type="button"
            role="radio"
            aria-checked={value === option.value}
            className={`visual-option ${value === option.value ? 'active' : ''}`}
            key={option.value}
            title={option.detail ?? option.label}
            onClick={() => onChange(option.value)}
          >
            <span className="visual-option-sample"><OptionSample kind={kind} value={option.sample ?? option.value} /></span>
            <small>{option.label}</small>
          </button>
        ))}
      </div>
    </div>
  )
}
