/* The figure of a graph the engine answered (XC-290): each series a polyline through the points that
 * have a value, broken where one is missing - a gap with its reason, never a bridge (XC-001) - the
 * vertical axis labelled as the engine labelled it (the internal unit, or the undeclared marker,
 * graph/AC-002), the horizontal axis the result position or the case, and the legend in the logic
 * layer's words. Nothing is computed here but where to put what was answered. */
import type { GraphData, GraphSeries } from "../logic/graphs";
import { chartPoints, horizontal, legendLine, tickValue, verticalRange } from "../logic/graphs";

const WIDTH = 640;
const HEIGHT = 320;
const LEFT = 72;
const RIGHT = 16;
const TOP = 16;
const BOTTOM = 44;
const STROKES = ["var(--ink-strong)", "var(--accent, #3a6ea5)", "var(--state-warn)", "var(--ink-muted)"];

export function SeriesChart(props: { data: GraphData; undeclared: string }) {
  const { data, undeclared } = props;
  const range = verticalRange(data);
  const axis = horizontal(data);
  const xs = data.series.flatMap((series) => chartPoints(data, series).map((one) => one.x));
  const xLow = xs.length > 0 ? Math.min(...xs) : 0;
  const xHigh = xs.length > 0 ? Math.max(...xs) : 1;
  const xSpan = xHigh === xLow ? 1 : xHigh - xLow;
  const toX = (x: number) => LEFT + ((x - xLow) / xSpan) * (WIDTH - LEFT - RIGHT);
  const toY = (y: number) => (range ? TOP + (1 - (y - range[0]) / (range[1] - range[0])) * (HEIGHT - TOP - BOTTOM) : HEIGHT - BOTTOM);
  const first = data.series[0];

  return (
    <figure style={{ margin: 0, display: "grid", gap: 8 }}>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`グラフ：${data.series.map((one) => one.label).join("、")}`} style={{ width: "100%", height: "auto", background: "var(--surface-panel)", border: "1px solid var(--line-strong)", borderRadius: "var(--radius-m)" }}>
        <line x1={LEFT} y1={TOP} x2={LEFT} y2={HEIGHT - BOTTOM} stroke="var(--line-strong)" />
        <line x1={LEFT} y1={HEIGHT - BOTTOM} x2={WIDTH - RIGHT} y2={HEIGHT - BOTTOM} stroke="var(--line-strong)" />
        <text x={8} y={TOP + 10} fontSize={11} fill="var(--ink-muted)">{data.axisLabel}</text>
        <text x={WIDTH - RIGHT} y={HEIGHT - 6} fontSize={11} fill="var(--ink-muted)" textAnchor="end">{axis.title}</text>
        {range && first ? (
          <>
            <text x={LEFT - 6} y={toY(range[1]) + 4} fontSize={10} fill="var(--ink-muted)" textAnchor="end">{tickValue(range[1], first)}</text>
            <text x={LEFT - 6} y={toY(range[0]) + 4} fontSize={10} fill="var(--ink-muted)" textAnchor="end">{tickValue(range[0], first)}</text>
          </>
        ) : null}
        {data.series.map((series, index) => {
          const points = chartPoints(data, series);
          const stroke = STROKES[index % STROKES.length];
          // Segments between neighbours that both have a value; a missing point breaks the line.
          const segments: string[] = [];
          let current: string[] = [];
          for (const point of points) {
            if (point.y === null) {
              if (current.length > 1) segments.push(current.join(" "));
              current = [];
              continue;
            }
            current.push(`${toX(point.x)},${toY(point.y)}`);
          }
          if (current.length > 1) segments.push(current.join(" "));
          return (
            <g key={series.label}>
              {segments.map((segment, at) => (
                <polyline key={at} points={segment} fill="none" stroke={stroke} strokeWidth={1.5} />
              ))}
              {points.map((point, at) =>
                point.y === null ? (
                  <g key={at}>
                    <line x1={toX(point.x) - 4} y1={HEIGHT - BOTTOM - 4} x2={toX(point.x) + 4} y2={HEIGHT - BOTTOM + 4} stroke="var(--state-warn)" />
                    <line x1={toX(point.x) - 4} y1={HEIGHT - BOTTOM + 4} x2={toX(point.x) + 4} y2={HEIGHT - BOTTOM - 4} stroke="var(--state-warn)" />
                    <title>{`${point.label}：値なし（${point.reason ?? "理由不明"}）`}</title>
                  </g>
                ) : (
                  <circle key={at} cx={toX(point.x)} cy={toY(point.y)} r={3.5} fill={stroke}>
                    <title>{`${point.label}：${tickValue(point.y, series)} ${series.unit ?? undeclared}`}</title>
                  </circle>
                ),
              )}
            </g>
          );
        })}
        {first
          ? chartPoints(data, first).map((point, at) => (
              <text key={at} x={toX(point.x)} y={HEIGHT - BOTTOM + 14} fontSize={10} fill="var(--ink-muted)" textAnchor="middle">
                {point.label.length > 18 ? `${point.label.slice(0, 17)}…` : point.label}
              </text>
            ))
          : null}
      </svg>
      <figcaption style={{ display: "grid", gap: 3 }}>
        {data.series.map((series: GraphSeries, index) => (
          <span key={series.label} className="type-caption" style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <span aria-hidden style={{ width: 14, height: 3, background: STROKES[index % STROKES.length], display: "inline-block" }} />
            {legendLine(series, undeclared)}
          </span>
        ))}
        {data.missing.map((line) => (
          <span key={line} className="type-caption" style={{ color: "var(--state-warn)" }}>
            データなし：{line}
          </span>
        ))}
        {data.resultAxisNote ? (
          <span className="type-caption" style={{ color: "var(--state-warn)" }}>{data.resultAxisNote}</span>
        ) : null}
      </figcaption>
    </figure>
  );
}
