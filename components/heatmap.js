'use client';

import { useTipHandlers } from './Tooltip';
import { ORDINAL } from '@/lib/brand';
import { CHART_W } from '@/lib/chartw';
import { shortLabel } from '@/lib/labels';

/**
 * A grid of places against categories, shaded by how concentrated each is.
 *
 * Every other chart here answers one question for many rows. This answers one
 * question for every row and column at once, which is the only readable way to
 * ask "what is each county actually made of" -- fourteen ranked charts would be
 * the same figures and nobody would read the fourteenth.
 *
 * The shading is a ratio against the state, not a quantity, so a dark cell means
 * "more of this than Vermont has", never "a lot of this". The two come apart
 * badly in small counties -- Essex at the top of the ramp is sixty-three jobs --
 * so the count is on every hover and the thin columns are outlined.
 *
 * Five steps rather than a continuous ramp: a reader can tell one step from the
 * next, and cannot tell two neighbouring blends apart.
 *
 * The breaks are not round numbers chosen in advance. Location quotients cluster
 * hard around 1 -- here the middle half of 308 cells runs 0.81 to 1.13 -- so
 * even steps put two thirds of the grid in one colour and the whole thing reads
 * as a flat wall. These four break the distribution into useful pieces while
 * still falling on numbers a reader can hold, and 1.0 is a break rather than the
 * middle of a band, so the ramp changes colour exactly where a county stops
 * looking like the state.
 *
 * cols: { k, label, thin? }     the places, left to right
 * rows: { k, label }            the categories, top to bottom
 * value(colKey, rowKey) -> { v, label, extra: [[k, v]] } | null
 */
const STEPS = [
  { max: 0.8, label: 'Under 0.8×' },
  { max: 1, label: '0.8 to 1×' },
  { max: 1.25, label: '1 to 1.25×' },
  { max: 1.75, label: '1.25 to 1.75×' },
  { max: Infinity, label: '1.75× and over' },
];

/** The step a figure is printed on: the top one, where it is a real specialism. */
export const HEAT_PRINT_FROM = STEPS[STEPS.length - 2].max;

export const HEAT_STEPS = STEPS.map((s) => s.label);
export const HEAT_COLORS = ORDINAL;

function stepOf(v) {
  for (let i = 0; i < STEPS.length; i += 1) if (v < STEPS[i].max) return i;
  return STEPS.length - 1;
}

/** One cell. A component of its own so the tooltip hook runs once per cell. */
function Cell({ x, y, w, h, k, v, title, rows, meta, print }) {
  const tip = useTipHandlers(title, rows, meta);
  return (
    <g className="bar" {...tip}>
      <rect x={x} y={y} width={w} height={h} rx={2} fill={`var(${ORDINAL[k]})`} />
      {print ? (
        <text
          x={x + w / 2}
          y={y + h / 2 + 4}
          className={'seglab' + (k <= 1 ? ' lo' : '')}
          textAnchor="middle"
          fontSize={10.5}
        >
          {v.toFixed(1)}
        </text>
      ) : null}
    </g>
  );
}

export function Heatmap({ cols, rows, value, opts = {} }) {
  const w = opts.width || CHART_W;
  const labW = opts.labelWidth || 200;
  const topH = opts.headHeight || 96;
  const rowH = 23;
  const gap = 2;
  const padR = 8;
  const cellW = (w - labW - padR - (cols.length - 1) * gap) / cols.length;
  const h = topH + rows.length * (rowH + gap) + 6;

  // Printed on the top step only. Below it the colour has already said how far
  // from the state the cell sits, and three hundred numbers mostly saying 1.0
  // would bury the ten that do not.
  const printAbove = opts.printAbove === undefined ? HEAT_PRINT_FROM : opts.printAbove;

  // Every other chart here is a column of bars, which simply gets shorter as the
  // page narrows. A grid gets shorter in both directions at once: on a phone the
  // same scaling takes 11px type to 3px, and the whole thing becomes a swatch.
  // So below the width it was drawn for it scrolls sideways instead, at the size
  // it was authored at.
  return (
    <div className="gridscroll">
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Concentration by place and category'}
    >
      {cols.map((c, j) => {
        const cx = labW + j * (cellW + gap) + cellW / 2;
        return (
          <text
            key={c.k}
            x={cx}
            y={topH - 9}
            className="clab"
            fontSize={11.5}
            textAnchor="start"
            transform={`rotate(-52 ${cx} ${topH - 9})`}
          >
            {c.label}
          </text>
        );
      })}

      {rows.map((r, i) => {
        const y = topH + i * (rowH + gap);
        return (
          <g key={r.k}>
            <text
              x={labW - 11}
              y={y + rowH / 2 + 4}
              className="clab"
              textAnchor="end"
              fontSize={11.5}
            >
              {shortLabel(r.label)}
            </text>
            {cols.map((c, j) => {
              const d = value(c.k, r.k);
              if (!d) return null;
              const k = stepOf(d.v);
              return (
                <Cell
                  key={c.k}
                  x={labW + j * (cellW + gap)}
                  y={y}
                  w={cellW}
                  h={rowH}
                  k={k}
                  v={d.v}
                  print={d.v >= printAbove}
                  title={`${c.label} — ${shortLabel(r.label)}`}
                  rows={d.extra || []}
                  meta={{
                    big: [[d.v.toFixed(2) + '×', opts.valueLabel || 'Against the state']],
                    foot: c.thin ? opts.thinNote : undefined,
                  }}
                />
              );
            })}
          </g>
        );
      })}

      {/* Places with too few jobs to split this many ways are outlined rather
          than dropped: it is still the only figure there is for that place. */}
      {cols.map((c, j) =>
        c.thin ? (
          <rect
            key={`thin-${c.k}`}
            className="thinmark"
            x={labW + j * (cellW + gap) - 1}
            y={topH - 1}
            width={cellW + 2}
            height={rows.length * (rowH + gap) + 1}
            fill="none"
            rx={3}
          />
        ) : null
      )}
    </svg>
    </div>
  );
}
