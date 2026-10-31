'use client';

import { useTipHandlers } from './Tooltip';
import { fmt } from '@/lib/format';
import { ORDINAL } from '@/lib/brand';
import { CHART_W } from '@/lib/chartw';

/**
 * 100% stacked columns, one per place.
 *
 * Everything else on this dashboard is a horizontal ranked bar, because
 * everything else is a ranking: twenty-two occupation groups, twenty-one sectors,
 * sorted so the eye can run down the order. This is not a ranking. It is a small
 * fixed set of places whose composition is being compared, and the order is
 * meaningful but not a result -- so it reads across, and the orientation itself
 * tells a reader they are being asked a different question.
 *
 * Every column sums to the same height, which is the point: the comparison is
 * composition, not volume. Volume is in the hover and on the figures table,
 * because a column that holds 651 postings and one that holds 70 million look
 * identical here and a reader has to be able to find that out.
 *
 * rows:   { label, parts: [n], total, note }
 * series: the segment names, bottom to top
 */
function Seg({ x, y, w, h, k, name, label, value, share, total, colors, dim, note, thin }) {
  const tip = useTipHandlers(`${label} — ${name}`, [
    ['Postings', fmt(value)],
    ['Of postings that state one', fmt(total)],
    ...(note ? [['Postings per job', note]] : []),
  ], {
    big: [[share.toFixed(1) + '%', `Share of ${label}`]],
    foot: thin ? 'Too few postings here to split reliably' : undefined,
  });

  return (
    <g className="bar" {...tip}>
      <rect
        x={x}
        y={y}
        width={w}
        height={Math.max(0.5, h)}
        fill={`var(${colors[k]})`}
        fillOpacity={dim ? 0.32 : thin ? 0.45 : 1}
      />
      {/* The number goes inside the segment only where it fits without
          crowding; below that the hover carries it. */}
      {h > 17 && w > 42 ? (
        <text
          x={x + w / 2}
          y={y + h / 2 + 4}
          className={'seglab' + (k <= 1 ? ' lo' : '')}
          textAnchor="middle"
          fontSize={11}
        >
          {share.toFixed(1) + '%'}
        </text>
      ) : null}
    </g>
  );
}

export function ColumnStack({ rows, series, opts = {} }) {
  const w = opts.width || CHART_W;
  const padT = 16;
  const padB = opts.noteLabel ? 64 : 46;
  const padL = 54;
  const padR = 8;
  const h = opts.height || 460;
  const plotH = h - padT - padB;
  const colors = opts.colors || ORDINAL;
  const n = rows.length;
  const slot = (w - padL - padR) / n;
  const colW = Math.min(opts.maxColumnWidth || 104, slot * 0.72);
  // How much name fits on a line, from the space a column actually has. Fixed at
  // 13 this read fine at eight columns and ran "New Hampshire" straight into
  // "United States" at seventeen.
  const maxChars = Math.max(6, Math.floor(slot / 6.2));

  // A gridline every 20 points. The axis is the only way to read a segment that
  // is too thin to carry its own number.
  const ticks = [0, 20, 40, 60, 80, 100];

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Composition by place'}
    >
      {ticks.map((t) => {
        const y = padT + plotH - (t / 100) * plotH;
        return (
          <g key={t}>
            <line x1={padL} x2={w - padR} y1={y} y2={y} className="grid" />
            <text x={padL - 9} y={y + 4} className="nbadge" textAnchor="end" fontSize={10}>
              {t}%
            </text>
          </g>
        );
      })}

      {rows.map((r, i) => {
        const cx = padL + slot * i + slot / 2;
        const x = cx - colW / 2;
        const tot = r.total || 1;
        let acc = 0;
        return (
          <g key={r.label}>
            {r.parts.map((v, k) => {
              if (!v) return null;
              const share = (v / tot) * 100;
              const segH = (share / 100) * plotH;
              const y = padT + plotH - ((acc + share) / 100) * plotH;
              acc += share;
              return (
                <Seg
                  key={k}
                  x={x}
                  y={y}
                  w={colW}
                  h={segH}
                  k={k}
                  name={series[k]}
                  label={r.label}
                  value={v}
                  share={share}
                  total={tot}
                  colors={colors}
                  dim={false}
                  note={r.note}
                  thin={r.thin}
                />
              );
            })}
            {/* A column built on too few postings is drawn, not hidden -- but it
                is outlined so it cannot be read as being as solid as the rest.
                Hiding a small county would be the worse answer: it is still the
                only figure there is for that place. */}
            {r.thin ? (
              <rect
                x={x}
                y={padT}
                width={colW}
                height={plotH}
                fill="none"
                className="thinmark"
                pointerEvents="none"
              />
            ) : null}
            {/* Place names wrap rather than truncate: "Rest of Vermont" cut to
                "Rest of Ver…" is not a place. */}
            {String(r.label).split(' ').reduce((lines, word) => {
              const last = lines[lines.length - 1];
              if (last && (last + ' ' + word).length <= maxChars) {
                lines[lines.length - 1] = last + ' ' + word;
              } else {
                lines.push(word);
              }
              return lines;
            }, []).slice(0, 2).map((line, li) => (
              <text
                key={li}
                x={cx}
                y={padT + plotH + 17 + li * 12}
                className="clab"
                textAnchor="middle"
                fontSize={11}
              >
                {line}
              </text>
            ))}
            {opts.noteLabel && r.note ? (
              <text
                x={cx}
                y={padT + plotH + 17 + 26}
                className="vlab"
                textAnchor="middle"
                fontSize={10}
              >
                {r.note}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}
