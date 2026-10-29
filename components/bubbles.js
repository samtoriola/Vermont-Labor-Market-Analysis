'use client';

import { useMemo } from 'react';
import { useTipHandlers } from './Tooltip';
import { trunc } from '@/lib/format';
import { ORDINAL } from '@/lib/brand';
import { CHART_W } from '@/lib/chartw';
import { shortLabel } from '@/lib/labels';

/**
 * Packed circles: one per row, sized by one measure and shaded by another.
 *
 * Where a stacked bar asks the reader to compare twenty-two rows of five
 * segments each -- a hundred and ten marks, none of which starts at the same
 * place -- this asks them to read two things: how big, and how dark. The mix the
 * segments carried moves into the hover, which is where a reader goes when the
 * shape of a row has already caught their eye.
 *
 * Area, not radius, is proportional to the value, so a circle twice the area of
 * another is twice the jobs. Reading area is still less precise than reading a
 * bar, which is why every circle wide enough carries its own number and the rest
 * are one hover away.
 *
 * rows: { label, value, t, shown, extra, big, onClick, active }
 *   value  sizes the circle
 *   t      0..1, the position on the sequential ramp that shades it
 *   shown  the formatted figure printed under the name
 */

/** Greedy pack: each circle takes the spot nearest the middle that is still free. */
function pack(radii, padding) {
  const placed = [];
  const STEPS = 180;

  radii.forEach((r, i) => {
    if (!placed.length) {
      placed.push({ x: 0, y: 0, r, i });
      return;
    }
    let best = null;
    // A new circle is always tangent to one already placed, so only those rings
    // are worth sampling. The nearest free point to the centre keeps the cluster
    // tight instead of letting it trail off in whatever order the rows arrived.
    for (const p of placed) {
      const d = p.r + r + padding;
      for (let a = 0; a < STEPS; a++) {
        const th = (a / STEPS) * Math.PI * 2;
        const x = p.x + Math.cos(th) * d;
        const y = p.y + Math.sin(th) * d;
        let clear = true;
        for (const q of placed) {
          const dx = q.x - x;
          const dy = q.y - y;
          if (dx * dx + dy * dy < (q.r + r + padding - 0.01) ** 2) {
            clear = false;
            break;
          }
        }
        if (!clear) continue;
        const score = x * x + y * y;
        if (!best || score < best.score) best = { x, y, score };
      }
    }
    placed.push({ x: best ? best.x : 0, y: best ? best.y : 0, r, i });
  });

  return placed;
}

/**
 * Greedy word wrap for a name inside a circle.
 *
 * Truncating instead would cut "Office & Administrative Support" to "Office &
 * Admin Su...", which is the one part of the name a reader does not need. A
 * circle is widest across its middle, so the lines are centred on it.
 */
function wrap(text, maxChars, maxLines) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (t.length <= maxChars || !cur) {
      cur = t;
      continue;
    }
    lines.push(cur);
    cur = w;
    if (lines.length === maxLines - 1) break;
  }
  if (cur && lines.length < maxLines) lines.push(cur);
  const kept = lines.join(' ').split(/\s+/).length;
  if (kept < words.length) {
    lines[lines.length - 1] = trunc(lines[lines.length - 1] + '…', maxChars);
  }
  return lines.map((l) => trunc(l, maxChars));
}

function Bubble({ c, row, dim }) {
  const h = useTipHandlers(row.label, row.extra || [], {
    sub: row.sub,
    big: row.big || [],
    foot: row.onClick ? row.clickHint || 'Click for the detail' : undefined,
  });
  const clickable = typeof row.onClick === 'function';

  // Room for the name only once the circle is wide enough to hold it legibly.
  // Type size tracks the circle but is capped low enough that a mid-size circle
  // gets characters rather than one big word: at 0.24r the characters per line
  // came out constant, because the font grew as fast as the circle did.
  const fs = Math.max(8.5, Math.min(13, c.r * 0.2));
  const show = c.r > 26;
  const chars = Math.max(5, Math.floor((c.r * 1.62) / (fs * 0.54)));
  const maxLines = c.r > 50 ? 3 : c.r > 34 ? 2 : 1;
  const lines = show ? wrap(shortLabel(row.label), chars, maxLines) : [];
  // The name's lines plus the figure under them, centred on the circle.
  const lh = fs * 1.1;
  const top = c.y - ((lines.length + 1 - 1) * lh) / 2 + fs * 0.34;

  return (
    <g
      className={'bub' + (clickable ? ' clickable' : '')}
      role={clickable ? 'button' : undefined}
      aria-label={clickable ? row.label : undefined}
      onClick={row.onClick}
      onKeyDown={
        clickable
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                row.onClick();
              }
            }
          : undefined
      }
      {...h}
    >
      <circle
        cx={c.x}
        cy={c.y}
        r={c.r}
        fill={`var(${ORDINAL[c.step]})`}
        fillOpacity={dim ? 0.3 : 1}
        stroke={row.active ? 'var(--ink)' : 'none'}
        strokeWidth={row.active ? 2 : 0}
      />
      {show ? (
        <g opacity={dim ? 0.45 : 1} pointerEvents="none">
          {lines.map((l, k) => (
            <text
              key={k}
              x={c.x}
              y={top + k * lh}
              className={'bublab' + (c.step <= 2 ? ' lo' : '')}
              textAnchor="middle"
              fontSize={fs}
            >
              {l}
            </text>
          ))}
          <text
            x={c.x}
            y={top + lines.length * lh}
            className={'bublab val' + (c.step <= 2 ? ' lo' : '')}
            textAnchor="middle"
            fontSize={fs * 0.92}
          >
            {row.shown}
          </text>
        </g>
      ) : null}
    </g>
  );
}

export function BubbleChart({ rows, opts = {} }) {
  const w = opts.width || CHART_W;
  const h = opts.height || 560;
  const hasSel = rows.some((r) => r.active);

  // Packing is the expensive part and it only depends on the sizes, so it is kept
  // across the re-renders that a selection or a hover causes.
  const key = rows.map((r) => `${r.label}:${r.value}`).join('|');
  const laid = useMemo(() => {
    const order = rows
      .map((r, i) => ({ r, i }))
      .filter((x) => x.r.value > 0)
      .sort((a, b) => b.r.value - a.r.value);
    if (!order.length) return { circles: [] };

    const max = order[0].r.value;
    // Area proportional to the value: r = sqrt(v). Scaled to the box afterwards,
    // so the unit here does not matter.
    const radii = order.map((x) => Math.sqrt(x.r.value / max) * 100);
    const placed = pack(radii, 3);

    let x0 = Infinity;
    let x1 = -Infinity;
    let y0 = Infinity;
    let y1 = -Infinity;
    placed.forEach((c) => {
      x0 = Math.min(x0, c.x - c.r);
      x1 = Math.max(x1, c.x + c.r);
      y0 = Math.min(y0, c.y - c.r);
      y1 = Math.max(y1, c.y + c.r);
    });
    const pad = 6;
    const scale = Math.min((w - pad * 2) / (x1 - x0), (h - pad * 2) / (y1 - y0));
    const dx = (w - (x1 - x0) * scale) / 2 - x0 * scale;
    const dy = (h - (y1 - y0) * scale) / 2 - y0 * scale;

    const circles = placed.map((c, k) => {
      const row = order[k].r;
      const t = row.t === undefined ? 0 : Math.max(0, Math.min(1, row.t));
      return {
        row,
        x: c.x * scale + dx,
        y: c.y * scale + dy,
        r: c.r * scale,
        // Five discrete steps rather than a continuous blend: the ramp is defined
        // as five tokens so that light and dark mode can each be checked, and a
        // reader comparing two circles can tell a step apart where they cannot
        // tell two neighbouring blends apart.
        step: Math.min(ORDINAL.length - 1, Math.floor(t * ORDINAL.length)),
      };
    });
    return { circles };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, w, h]);

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={opts.aria || 'Packed circle chart'}
    >
      {laid.circles.map((c) => (
        <Bubble key={c.row.label} c={c} row={c.row} dim={hasSel && !c.row.active} />
      ))}
    </svg>
  );
}
