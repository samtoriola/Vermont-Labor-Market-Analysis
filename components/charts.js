'use client';

import { useTipHandlers } from './Tooltip';
import { fmt, money, niceMax, trunc, fmtVal } from '@/lib/format';
import { SERIES } from '@/lib/data';

/**
 * Wraps an SVG group so the tooltip hook runs once per mark instance.
 * Calling useTipHandlers directly inside a .map() would break the rules of hooks.
 */
function TipMark({ title, rows, className, onClick, children }) {
  const h = useTipHandlers(title, rows);
  const clickable = typeof onClick === 'function';
  return (
    <g
      className={className + (clickable ? ' clickable' : '')}
      role={clickable ? 'button' : undefined}
      aria-label={clickable ? title : undefined}
      onClick={onClick}
      onKeyDown={
        clickable
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      {...h}
    >
      {children}
    </g>
  );
}

const V = (token) => `var(${token})`;

/* ------------------------------------------------------------------ *
 * Ranked horizontal bars
 * rows: { label, value, color?, money?, mode?, dec?, extra? }
 * ------------------------------------------------------------------ */
export function RankedBars({ rows, opts = {} }) {
  const labW = opts.labelWidth || 188;
  const rowH = 24;
  const gap = 7;
  const padR = opts.money ? 96 : 84;
  const padT = 28;
  const w = opts.width || 860;
  const h = padT + rows.length * (rowH + gap) + 4;
  const plotW = w - labW - padR;
  const signed = !!opts.signed;

  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.value)));
  const max = opts.max !== undefined ? opts.max : niceMax(maxAbs);
  const zeroX = signed ? labW + plotW / 2 : labW;
  const scale = signed ? plotW / 2 / max : plotW / max;

  const ticks = signed
    ? [-max, -max / 2, 0, max / 2, max]
    : [0, max / 4, max / 2, (3 * max) / 4, max];

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Ranked bar chart'}
    >
      {ticks.map((tv, i) => {
        const gx = zeroX + tv * scale;
        return (
          <g key={`t${i}`}>
            <line
              x1={gx}
              y1={padT - 9}
              x2={gx}
              y2={h - 4}
              className={tv === 0 && signed ? 'axis' : 'grid'}
              strokeWidth={1}
            />
            <text x={gx} y={padT - 15} className="nbadge" textAnchor="middle" fontSize={10}>
              {fmtVal(tv, opts)}
            </text>
          </g>
        );
      })}

      {opts.rule !== undefined && opts.rule <= max ? (
        <g>
          <line
            x1={zeroX + opts.rule * scale}
            y1={padT - 4}
            x2={zeroX + opts.rule * scale}
            y2={h - 4}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          {opts.ruleLabel ? (
            <text
              x={zeroX + opts.rule * scale + 5}
              y={h - 6}
              className="nbadge"
              fontSize={9.5}
              fill={V('--ink-2')}
            >
              {opts.ruleLabel}
            </text>
          ) : null}
        </g>
      ) : null}

      {rows.map((r, i) => {
        const y = padT + i * (rowH + gap);
        const v = r.value;
        const bw = Math.max(1.5, Math.abs(v) * scale);
        const bx = v < 0 ? zeroX - bw : zeroX;
        const shown = fmtVal(v, {
          money: r.money || opts.money,
          mode: r.mode || opts.mode,
          dec: r.dec !== undefined ? r.dec : opts.dec,
          signed,
        });
        const trows = [[opts.valueLabel || 'Value', shown], ...(r.extra || [])];

        return (
          <g key={r.label + i}>
            <text
              x={labW - 11}
              y={y + rowH / 2 + 4}
              className="clab"
              textAnchor="end"
              fontSize={12}
            >
              {trunc(r.label, Math.floor(labW / 6.4))}
            </text>
            <TipMark title={r.label} rows={trows} className="bar" onClick={r.onClick}>
              <rect x={bx} y={y} width={bw} height={rowH} rx={4} fill={V(r.color || '--s1')} />
              <text
                x={v < 0 ? bx - 9 : bx + bw + 9}
                y={y + rowH / 2 + 4}
                className="vlab"
                textAnchor={v < 0 ? 'end' : 'start'}
                fontSize={11.5}
              >
                {shown}
              </text>
            </TipMark>
          </g>
        );
      })}
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Box plot: p10 whisker, p25-p75 box, p50 line
 * ------------------------------------------------------------------ */
export function BoxPlot({ rows, opts = {} }) {
  const labW = opts.labelWidth || 214;
  const rowH = 30;
  const gap = 8;
  const padR = 88;
  const padT = 30;
  const w = opts.width || 860;
  const h = padT + rows.length * (rowH + gap) + 14;
  const plotW = w - labW - padR;
  const boxH = 17;
  const capH = 9;

  const lo = opts.min !== undefined ? opts.min : 0;
  const hiRaw = Math.max(...rows.map((r) => r.p90 || r.p50));
  const hi = opts.max !== undefined ? opts.max : niceMax(hiRaw);
  const X = (v) => labW + ((v - lo) / (hi - lo)) * plotW;

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Wage percentile distribution'}
    >
      {[0, 1, 2, 3, 4].map((t) => {
        const tv = lo + ((hi - lo) * t) / 4;
        const gx = X(tv);
        return (
          <g key={`t${t}`}>
            <line x1={gx} y1={padT - 10} x2={gx} y2={h - 12} className="grid" strokeWidth={1} />
            <text x={gx} y={padT - 16} className="nbadge" textAnchor="middle" fontSize={10}>
              {'$' + fmt(tv / 1000) + 'k'}
            </text>
          </g>
        );
      })}

      {opts.rule !== undefined && opts.rule >= lo && opts.rule <= hi ? (
        <g>
          <line
            x1={X(opts.rule)}
            y1={padT - 6}
            x2={X(opts.rule)}
            y2={h - 12}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          {opts.ruleLabel ? (
            <text
              x={X(opts.rule) + 5}
              y={h - 2}
              className="nbadge"
              fontSize={9.5}
              fill={V('--ink-2')}
            >
              {opts.ruleLabel}
            </text>
          ) : null}
        </g>
      ) : null}

      {rows.map((r, i) => {
        const y = padT + i * (rowH + gap);
        const cy = y + rowH / 2;
        const x10 = X(r.p10);
        const x25 = X(r.p25);
        const x50 = X(r.p50);
        const x75 = X(r.p75);
        const x90 = X(r.p90);
        const trows = [
          ['10th percentile', money(r.p10)],
          ['25th percentile', money(r.p25)],
          ['Median', money(r.p50)],
          ['75th percentile', money(r.p75)],
          ['90th percentile', money(r.p90)],
          ['p90 ÷ p10', (r.p90 / r.p10).toFixed(2) + '×'],
          ...(r.extra || []),
        ];

        return (
          <g key={r.label + i}>
            <text
              x={labW - 11}
              y={cy + 4}
              className="clab"
              textAnchor="end"
              fontSize={12}
            >
              {trunc(r.label, Math.floor(labW / 6.4))}
            </text>
            <TipMark title={r.label} rows={trows} className="bar" onClick={r.onClick}>
              <line x1={x10} y1={cy} x2={x25} y2={cy} stroke={V('--ink-3')} strokeWidth={1.5} />
              <line x1={x75} y1={cy} x2={x90} y2={cy} stroke={V('--ink-3')} strokeWidth={1.5} />
              <line
                x1={x10}
                y1={cy - capH / 2}
                x2={x10}
                y2={cy + capH / 2}
                stroke={V('--ink-3')}
                strokeWidth={1.5}
                strokeLinecap="round"
              />
              <line
                x1={x90}
                y1={cy - capH / 2}
                x2={x90}
                y2={cy + capH / 2}
                stroke={V('--ink-3')}
                strokeWidth={1.5}
                strokeLinecap="round"
              />
              <rect
                x={x25}
                y={cy - boxH / 2}
                width={Math.max(2, x75 - x25)}
                height={boxH}
                rx={3}
                fill={V(r.color || '--s1')}
              />
              {/* surface gap so the median line reads against the box fill */}
              <line
                x1={x50}
                y1={cy - boxH / 2 - 1}
                x2={x50}
                y2={cy + boxH / 2 + 1}
                stroke={V('--panel')}
                strokeWidth={3}
              />
              <line
                x1={x50}
                y1={cy - boxH / 2}
                x2={x50}
                y2={cy + boxH / 2}
                stroke={V('--ink')}
                strokeWidth={1.5}
              />
              <text x={x90 + 10} y={cy + 4} className="vlab" textAnchor="start" fontSize={11}>
                {money(r.p50)}
              </text>
              {opts.endLabels ? (
                <>
                  <text
                    x={x10}
                    y={cy + boxH / 2 + 11}
                    className="nbadge"
                    textAnchor="middle"
                    fontSize={9}
                  >
                    {money(r.p10)}
                  </text>
                  <text
                    x={x90}
                    y={cy + boxH / 2 + 11}
                    className="nbadge"
                    textAnchor="middle"
                    fontSize={9}
                  >
                    {money(r.p90)}
                  </text>
                </>
              ) : null}
            </TipMark>
          </g>
        );
      })}
    </svg>
  );
}

export function BoxLegend() {
  const cy = 17;
  const marks = [
    [30, '10th'],
    [80, '25th'],
    [135, 'median'],
    [190, '75th'],
    [250, '90th'],
  ];
  return (
    <svg
      className="chart boxkey"
      viewBox="0 0 300 46"
      role="img"
      aria-label="How to read the box plot"
    >
      <line x1={30} y1={cy} x2={80} y2={cy} stroke={V('--ink-3')} strokeWidth={1.5} />
      <line x1={190} y1={cy} x2={250} y2={cy} stroke={V('--ink-3')} strokeWidth={1.5} />
      <line x1={30} y1={cy - 4.5} x2={30} y2={cy + 4.5} stroke={V('--ink-3')} strokeWidth={1.5} />
      <line x1={250} y1={cy - 4.5} x2={250} y2={cy + 4.5} stroke={V('--ink-3')} strokeWidth={1.5} />
      <rect x={80} y={cy - 8.5} width={110} height={17} rx={3} fill={V('--s1')} />
      <line x1={135} y1={cy - 9.5} x2={135} y2={cy + 9.5} stroke={V('--panel')} strokeWidth={3} />
      <line x1={135} y1={cy - 8.5} x2={135} y2={cy + 8.5} stroke={V('--ink')} strokeWidth={1.5} />
      {marks.map(([x, label]) => (
        <text key={label} x={x} y={42} className="nbadge" textAnchor="middle" fontSize={9}>
          {label}
        </text>
      ))}
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * 100% stacked rows
 * rows: { label, parts: [{v}], total, hi? }
 * ------------------------------------------------------------------ */
export function StackedRows({ rows, opts = {} }) {
  const labW = opts.labelWidth || 188;
  const rowH = 21;
  const gap = 6;
  const padR = 58;
  const padT = 14;
  const w = 860;
  const h = padT + rows.length * (rowH + gap) + 2;
  const plotW = w - labW - padR;
  const names = opts.tierNames || [];

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Stacked share chart'}
    >
      {opts.rightLabel ? (
        <text x={w - padR + 9} y={padT - 3} className="nbadge" textAnchor="start" fontSize={9}>
          {opts.rightLabel}
        </text>
      ) : null}

      {rows.map((r, i) => {
        const y = padT + i * (rowH + gap);
        const tot = r.total || 1;
        let x = labW;
        const segs = r.parts.map((p, k) => {
          if (!p.v) return null;
          const pw = (p.v / tot) * plotW;
          const seg = (
            <TipMark
              key={k}
              title={`${r.label} — ${names[k] || 'Series ' + (k + 1)}`}
              rows={[
                ['Share of family', ((p.v / tot) * 100).toFixed(1) + '%'],
                ['Jobs', fmt(p.v)],
              ]}
            >
              <rect
                x={x}
                y={y}
                width={Math.max(0.5, pw - 2)}
                height={rowH}
                rx={2}
                fill={V(SERIES[k])}
              />
            </TipMark>
          );
          x += pw;
          return seg;
        });

        return (
          <g key={r.label + i}>
            <text x={labW - 11} y={y + rowH / 2 + 4} className="clab" textAnchor="end" fontSize={12}>
              {trunc(r.label, 28)}
            </text>
            {segs}
            {r.hi !== undefined ? (
              <text
                x={w - padR + 9}
                y={y + rowH / 2 + 4}
                className="vlab"
                textAnchor="start"
                fontSize={11}
              >
                {(r.hi * 100).toFixed(0) + '%'}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Dumbbell: two points per row with a connector
 * ------------------------------------------------------------------ */
export function Dumbbell({ rows }) {
  const labW = 188;
  const rowH = 24;
  const gap = 7;
  const padR = 98;
  const padT = 28;
  const w = 860;
  const h = padT + rows.length * (rowH + gap) + 4;
  const plotW = w - labW - padR;
  const max = niceMax(Math.max(...rows.map((r) => Math.max(r.a, r.b))));

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label="Employment 2021 versus 2025 by occupational family"
    >
      {[0, 1, 2, 3, 4].map((t) => {
        const gx = labW + (plotW * t) / 4;
        return (
          <g key={`t${t}`}>
            <line x1={gx} y1={padT - 9} x2={gx} y2={h - 4} className="grid" strokeWidth={1} />
            <text x={gx} y={padT - 15} className="nbadge" textAnchor="middle" fontSize={10}>
              {fmt((max * t) / 4)}
            </text>
          </g>
        );
      })}

      {rows.map((r, i) => {
        const y = padT + i * (rowH + gap);
        const cy = y + rowH / 2;
        const xa = labW + (r.a / max) * plotW;
        const xb = labW + (r.b / max) * plotW;
        const d = r.b - r.a;
        const txt = (d >= 0 ? '+' : '−') + fmt(Math.abs(d));

        return (
          <g key={r.label + i}>
            <text x={labW - 11} y={cy + 4} className="clab" textAnchor="end" fontSize={12}>
              {trunc(r.label, 28)}
            </text>
            <TipMark
              title={r.label}
              className="bar"
              rows={[
                ['2021', fmt(r.a)],
                ['2025 (11-mo)', fmt(r.b)],
                ['Change', txt],
                ['Distinguishable from zero?', r.sig ? 'Yes (95%)' : 'No'],
                ['Records 2021 / 2025', fmt(r.na) + ' / ' + fmt(r.nb)],
              ]}
            >
              <line
                x1={xa}
                y1={cy}
                x2={xb}
                y2={cy}
                stroke={V('--rule-strong')}
                strokeWidth={2.5}
                strokeLinecap="round"
              />
              <circle cx={xa} cy={cy} r={5} fill={V('--s3')} stroke={V('--panel')} strokeWidth={2} />
              <circle cx={xb} cy={cy} r={5} fill={V('--s1')} stroke={V('--panel')} strokeWidth={2} />
              <text
                x={w - padR + 9}
                y={cy + 4}
                className="vlab"
                textAnchor="start"
                fontSize={11}
                fill={r.sig ? undefined : V('--ink-3')}
              >
                {txt + (r.sig ? '' : ' ns')}
              </text>
            </TipMark>
          </g>
        );
      })}
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Single-series line chart
 * ------------------------------------------------------------------ */
export function TrendLine({ series, opts }) {
  const w = 430;
  const h = 200;
  const padL = 48;
  const padR = 18;
  const padT = 20;
  const padB = 32;
  const pw = w - padL - padR;
  const ph = h - padT - padB;
  const xs = series.x;
  const lo = opts.min;
  const hi = opts.max;
  const X = (i) => padL + (pw * i) / (xs.length - 1);
  const Y = (v) => padT + ph - ((v - lo) / (hi - lo)) * ph;
  const d = series.y.map((v, i) => (i ? 'L' : 'M') + X(i) + ' ' + Y(v)).join(' ');

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria}
    >
      {[0, 1, 2, 3].map((t) => {
        const gy = padT + ph - (ph * t) / 3;
        return (
          <g key={`g${t}`}>
            <line x1={padL} y1={gy} x2={w - padR} y2={gy} className="grid" strokeWidth={1} />
            <text x={padL - 8} y={gy + 3.5} className="nbadge" textAnchor="end" fontSize={10}>
              {opts.fmtY(lo + ((hi - lo) * t) / 3)}
            </text>
          </g>
        );
      })}
      {xs.map((yr, i) => (
        <text key={yr} x={X(i)} y={h - 11} className="nbadge" textAnchor="middle" fontSize={10}>
          {String(yr)}
        </text>
      ))}
      <path
        d={d}
        fill="none"
        stroke={V(opts.color || '--s1')}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {series.y.map((v, i) => {
        const last = i === series.y.length - 1;
        return (
          <g key={`p${i}`}>
            <TipMark title={String(xs[i])} rows={[[opts.aria, opts.fmtY(v)]]}>
              <circle
                cx={X(i)}
                cy={Y(v)}
                r={last ? 5 : 3.5}
                fill={V(opts.color || '--s1')}
                stroke={V('--panel')}
                strokeWidth={2}
              />
            </TipMark>
            {last ? (
              <text
                x={X(i) - 9}
                y={Y(v) - 12}
                className="vlab"
                textAnchor="end"
                fontSize={11}
              >
                {opts.fmtY(v)}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Scatter. Series capped at 3 per the all-pairs CVD rule.
 * ------------------------------------------------------------------ */
export function Scatter({ pts, opts }) {
  const w = 860;
  const h = 430;
  const padL = 66;
  const padR = 24;
  const padT = 22;
  const padB = 52;
  const pw = w - padL - padR;
  const ph = h - padT - padB;
  const xmax = niceMax(Math.max(...pts.map((p) => p.x)));
  const ys = pts.map((p) => p.y);
  const ymin = Math.max(1, Math.min(...ys));
  const ymax = Math.max(...ys);

  const X = (v) => padL + (v / xmax) * pw;
  const Y = (v) => {
    if (!opts.logY) return padT + ph - (v / ymax) * ph;
    const l0 = Math.log10(ymin);
    const l1 = Math.log10(ymax);
    return padT + ph - ((Math.log10(Math.max(v, ymin)) - l0) / (l1 - l0)) * ph;
  };

  const yticks = opts.logY
    ? [1, 10, 100, 1000, 10000].filter((t) => t >= ymin * 0.9 && t <= ymax * 1.6)
    : [0, ymax / 2, ymax];

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria}
    >
      {yticks.map((tv) => (
        <g key={`y${tv}`}>
          <line x1={padL} y1={Y(tv)} x2={w - padR} y2={Y(tv)} className="grid" strokeWidth={1} />
          <text x={padL - 9} y={Y(tv) + 3.5} className="nbadge" textAnchor="end" fontSize={10}>
            {fmt(tv)}
          </text>
        </g>
      ))}
      {[0, 1, 2, 3, 4].map((t) => {
        const gx = padL + (pw * t) / 4;
        return (
          <g key={`x${t}`}>
            <line x1={gx} y1={padT} x2={gx} y2={padT + ph} className="grid" strokeWidth={1} />
            <text x={gx} y={padT + ph + 17} className="nbadge" textAnchor="middle" fontSize={10}>
              {'$' + fmt((xmax * t) / 4 / 1000) + 'k'}
            </text>
          </g>
        );
      })}
      {opts.vRule ? (
        <g>
          <line
            x1={X(opts.vRule)}
            y1={padT - 2}
            x2={X(opts.vRule)}
            y2={padT + ph + 4}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          <text
            x={X(opts.vRule) + 6}
            y={padT + 10}
            className="nbadge"
            fontSize={10}
            fill={V('--ink-2')}
          >
            {opts.vRuleLabel || ''}
          </text>
        </g>
      ) : null}
      {pts.map((p, i) => (
        <TipMark key={i} title={p.label} rows={p.extra || []}>
          <circle
            cx={X(p.x)}
            cy={Y(p.y)}
            r={4}
            fill={V(SERIES[p.series])}
            fillOpacity={0.72}
            stroke={V('--panel')}
            strokeWidth={1}
          />
        </TipMark>
      ))}
      <text x={padL + pw / 2} y={h - 12} className="nbadge" textAnchor="middle" fontSize={11}>
        {opts.xLabel}
      </text>
      <text
        className="nbadge"
        textAnchor="middle"
        fontSize={11}
        transform={`translate(16,${padT + ph / 2}) rotate(-90)`}
      >
        {opts.yLabel}
      </text>
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Grouped bars: several measures per row
 * ------------------------------------------------------------------ */
export function GroupedBars({ rows, opts }) {
  const labW = 188;
  const barH = 7;
  const gapIn = 2;
  const rowPad = 11;
  const padR = 62;
  const padT = 26;
  const nS = opts.colors.length;
  const rowH = nS * barH + (nS - 1) * gapIn;
  const w = 860;
  const h = padT + rows.length * (rowH + rowPad) + 4;
  const plotW = w - labW - padR;
  const max = niceMax(Math.max(...rows.map((r) => Math.max(...r.parts.map((p) => p.v)))));

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria}
    >
      {[0, 1, 2, 3, 4].map((t) => {
        const gx = labW + (plotW * t) / 4;
        return (
          <g key={`t${t}`}>
            <line x1={gx} y1={padT - 9} x2={gx} y2={h - 4} className="grid" strokeWidth={1} />
            <text x={gx} y={padT - 15} className="nbadge" textAnchor="middle" fontSize={10}>
              {((max * t) / 4).toFixed(0) + '%'}
            </text>
          </g>
        );
      })}
      {rows.map((r, i) => {
        const y0 = padT + i * (rowH + rowPad);
        return (
          <g key={r.label + i}>
            <text x={labW - 11} y={y0 + rowH / 2 + 4} className="clab" textAnchor="end" fontSize={12}>
              {trunc(r.label, 28)}
            </text>
            <TipMark title={r.label} rows={r.extra || []} className="bar" onClick={r.onClick}>
              {r.parts.map((p, k) => (
                <rect
                  key={k}
                  x={labW}
                  y={y0 + k * (barH + gapIn)}
                  width={Math.max(1.5, (p.v / max) * plotW)}
                  height={barH}
                  rx={2}
                  fill={V(opts.colors[k])}
                />
              ))}
            </TipMark>
          </g>
        );
      })}
    </svg>
  );
}
