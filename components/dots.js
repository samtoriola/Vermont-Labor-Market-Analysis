'use client';

import { useTip } from './Tooltip';
import { fmt, money, trunc } from '@/lib/format';

const V = (token) => `var(${token})`;

/**
 * Deterministic pseudo-random in [0,1). The same dot lands in the same place on
 * every render, so the cloud does not shuffle when a filter changes.
 */
function hash01(i) {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

/* ------------------------------------------------------------------ *
 * Dot distribution
 *
 * One dot per underlying record -- an occupation, or a survey respondent,
 * depending on what the caller passes. The average and median are drawn as
 * lines across the column so you can see where they sit inside the spread,
 * which is the thing a box plot hides.
 *
 * groups: { label, sub?, dots: [{ v, e? }], avg, med, ref?, thin?, color?, onClick? }
 * opts:   { yMax, rule, ruleLabel, dotTip, unit, width, height }
 * ------------------------------------------------------------------ */
export function DotColumns({ groups, opts = {} }) {
  const { show, hide } = useTip();

  const padL = 64;
  const padR = 14;
  const padT = 16;
  const padB = 76;
  const w = opts.width || 880;
  const plotH = opts.height || 330;
  const h = padT + plotH + padB;
  const plotW = w - padL - padR;
  const colW = plotW / groups.length;
  const yMax = opts.yMax || 200000;
  const Y = (v) => padT + plotH - (Math.min(v, yMax) / yMax) * plotH;
  const y0 = padT + plotH;

  // Dot radius carries employment where the caller supplies it; person-level dots
  // all count for one, so they stay a fixed size.
  const maxE = Math.max(1, ...groups.flatMap((g) => g.dots.map((d) => d.e || 0)));
  const sized = maxE > 1;
  const rOf = (d) =>
    sized ? Math.max(1.6, Math.min(9, Math.sqrt((d.e || 0) / maxE) * 9)) : 2.1;

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);
  const firstRef = groups.findIndex((g) => g.ref);

  return (
    <svg
      className="chart dotcols"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Distribution of earnings'}
    >
      {ticks.map((tv) => (
        <g key={`t${tv}`}>
          <line x1={padL} y1={Y(tv)} x2={w - padR} y2={Y(tv)} className="grid" strokeWidth={1} />
          <text x={padL - 8} y={Y(tv) + 3.5} className="nbadge" textAnchor="end" fontSize={10}>
            {tv === 0 ? '$0' : '$' + fmt(tv / 1000) + 'k'}
          </text>
        </g>
      ))}

      {/* Reference columns sit behind a divider so they do not read as Vermont data. */}
      {firstRef > 0 ? (
        <line
          x1={padL + firstRef * colW}
          y1={padT - 6}
          x2={padL + firstRef * colW}
          y2={y0 + 52}
          stroke={V('--rule')}
          strokeWidth={1}
        />
      ) : null}

      {groups.map((g, gi) => {
        const x0 = padL + gi * colW;
        const cx = x0 + colW / 2;
        const band = Math.min(colW - 18, 118);
        const left = cx - band / 2;
        const tone = g.color || (g.ref ? '--ink-3' : '--s1');
        const clickable = typeof g.onClick === 'function';

        return (
          <g key={g.label + gi} className={'dotcol' + (g.ref ? ' ref' : '')}>
            {/* Filled to the average, the way the reference visual reads. */}
            <rect
              x={left}
              y={Y(g.avg)}
              width={band}
              height={Math.max(0, y0 - Y(g.avg))}
              fill={V(tone)}
              opacity={0.07}
            />

            {g.dots.map((d, i) => {
              const over = d.v > yMax;
              const dy = over ? padT + 4 : Y(d.v);
              const dx = left + 5 + hash01(gi * 7919 + i) * (band - 10);
              const tip = () => (opts.dotTip ? opts.dotTip(d, g) : { title: '', rows: [] });
              const on = {
                onMouseMove: (e) => {
                  const t = tip();
                  show(e, t.title, t.rows);
                },
                onMouseLeave: hide,
              };
              return over ? (
                <path
                  key={i}
                  d={`M${dx} ${dy - 4}L${dx + 3.6} ${dy + 2}L${dx - 3.6} ${dy + 2}Z`}
                  fill={V(tone)}
                  opacity={0.85}
                  className="dot over"
                  {...on}
                />
              ) : (
                <circle
                  key={i}
                  cx={dx}
                  cy={dy}
                  r={rOf(d)}
                  fill={V(tone)}
                  opacity={sized ? 0.5 : 0.36}
                  className="dot"
                  {...on}
                />
              );
            })}

            {/* Median first, so the average line reads on top of it where they meet. */}
            <line
              x1={left}
              y1={Y(g.med)}
              x2={left + band}
              y2={Y(g.med)}
              stroke={V('--ink-2')}
              strokeWidth={1.5}
              strokeDasharray="5 3"
            />
            <line
              x1={left - 4}
              y1={Y(g.avg)}
              x2={left + band + 4}
              y2={Y(g.avg)}
              stroke={V('--panel')}
              strokeWidth={4}
            />
            <line
              x1={left - 4}
              y1={Y(g.avg)}
              x2={left + band + 4}
              y2={Y(g.avg)}
              stroke={V('--ink')}
              strokeWidth={2}
            />

            <g
              className={clickable ? 'collabel clickable' : 'collabel'}
              role={clickable ? 'button' : undefined}
              tabIndex={clickable ? 0 : undefined}
              aria-label={clickable ? `${g.label} detail` : undefined}
              onClick={g.onClick}
              onKeyDown={
                clickable
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        g.onClick();
                      }
                    }
                  : undefined
              }
            >
              <rect x={x0} y={y0 + 2} width={colW} height={padB - 8} fill="transparent" />
              <text x={cx} y={y0 + 18} className="vlab" textAnchor="middle" fontSize={12}>
                {money(g.avg)}
              </text>
              <text x={cx} y={y0 + 31} className="nbadge" textAnchor="middle" fontSize={9}>
                {opts.unit || 'average'}
              </text>
              <text x={cx} y={y0 + 49} className="clab" textAnchor="middle" fontSize={11.5}>
                {trunc(g.label, Math.floor(colW / 6.2))}
              </text>
              {g.sub ? (
                <text x={cx} y={y0 + 62} className="nbadge" textAnchor="middle" fontSize={9}>
                  {g.sub}
                  {g.thin ? ' · small sample' : ''}
                </text>
              ) : null}
            </g>
          </g>
        );
      })}
      {/* Drawn last so the label stays legible over the dots and the average
          lines that cross it. */}
      {opts.rule !== undefined && opts.rule < yMax ? (
        <g>
          <line
            x1={padL}
            y1={Y(opts.rule)}
            x2={w - padR}
            y2={Y(opts.rule)}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          {opts.ruleLabel ? (
            <text x={padL + 4} y={Y(opts.rule) - 6} className="nbadge rulelab" fontSize={9.5} fill={V('--ink-2')}>
              {opts.ruleLabel}
            </text>
          ) : null}
        </g>
      ) : null}

    </svg>
  );
}

/** Key for the dot chart: what a dot is, and which line is which. */
export function DotLegend({ unit = 'one occupation', sized = true }) {
  return (
    <svg className="chart boxkey" viewBox="0 0 470 40" role="img" aria-label="How to read the dot chart">
      <circle cx={10} cy={13} r={3} fill={V('--s1')} opacity={0.45} />
      <circle cx={19} cy={17} r={5} fill={V('--s1')} opacity={0.45} />
      <circle cx={30} cy={11} r={2.4} fill={V('--s1')} opacity={0.45} />
      <text x={41} y={17} className="nbadge" fontSize={9.5}>
        each dot = {unit}
        {sized ? ', sized by employment' : ''}
      </text>
      <line x1={10} y1={33} x2={34} y2={33} stroke={V('--ink')} strokeWidth={2} />
      <text x={41} y={36} className="nbadge" fontSize={9.5}>
        average
      </text>
      <line x1={96} y1={33} x2={120} y2={33} stroke={V('--ink-2')} strokeWidth={1.5} strokeDasharray="5 3" />
      <text x={127} y={36} className="nbadge" fontSize={9.5}>
        median
      </text>
      <path d="M186 29L189.6 35L182.4 35Z" fill={V('--s1')} opacity={0.85} />
      <text x={196} y={36} className="nbadge" fontSize={9.5}>
        above the top of the scale
      </text>
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Percentile ladder
 *
 * One row per occupation: the 10th-to-90th percentile span, the middle half
 * picked out, a solid dot at the median and a hollow ring at the mean. Mean
 * and median on the same line show how far the average is pulled by the top
 * of the distribution.
 *
 * rows: { label, p10, p25, p50, p75, p90, mu, color?, extra?, onClick? }
 * ------------------------------------------------------------------ */
export function PercentileLadder({ rows, opts = {} }) {
  const { show, hide } = useTip();

  const labW = opts.labelWidth || 262;
  const rowH = 22;
  const gap = 5;
  const padR = 104;
  const padT = 30;
  const w = opts.width || 880;
  const h = padT + rows.length * (rowH + gap) + 12;
  const plotW = w - labW - padR;

  const lo = opts.min !== undefined ? opts.min : 0;
  const hi = opts.max !== undefined ? opts.max : Math.max(...rows.map((r) => r.p90 || r.p50));
  const X = (v) => labW + ((Math.min(v, hi) - lo) / (hi - lo)) * plotW;

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Earnings percentile ladder'}
    >
      {[0, 1, 2, 3, 4].map((t) => {
        const tv = lo + ((hi - lo) * t) / 4;
        return (
          <g key={`t${t}`}>
            <line x1={X(tv)} y1={padT - 10} x2={X(tv)} y2={h - 8} className="grid" strokeWidth={1} />
            <text x={X(tv)} y={padT - 16} className="nbadge" textAnchor="middle" fontSize={10}>
              {'$' + fmt(tv / 1000) + 'k'}
            </text>
          </g>
        );
      })}

      {opts.rule !== undefined && opts.rule <= hi ? (
        <g>
          <line
            x1={X(opts.rule)}
            y1={padT - 6}
            x2={X(opts.rule)}
            y2={h - 8}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          {opts.ruleLabel ? (
            <text x={X(opts.rule) + 5} y={h - 1} className="nbadge rulelab" fontSize={9.5} fill={V('--ink-2')}>
              {opts.ruleLabel}
            </text>
          ) : null}
        </g>
      ) : null}

      {rows.map((r, i) => {
        const cy = padT + i * (rowH + gap) + rowH / 2;
        const tone = r.color || '--s1';
        const hasMu = r.mu !== null && r.mu !== undefined;
        const gapPct = hasMu && r.p50 ? ((r.mu - r.p50) / r.p50) * 100 : null;
        const title = r.label;
        const trows = [
          ['10th percentile', money(r.p10)],
          ['25th percentile', money(r.p25)],
          ['Median', money(r.p50)],
          ['Mean', hasMu ? money(r.mu) : '—'],
          ['75th percentile', money(r.p75)],
          ['90th percentile', money(r.p90)],
          [
            'Mean vs median',
            gapPct === null ? '—' : (gapPct >= 0 ? '+' : '') + gapPct.toFixed(1) + '%',
          ],
          ...(r.extra || []),
        ];
        const clickable = typeof r.onClick === 'function';

        return (
          <g key={r.label + i}>
            <text x={labW - 11} y={cy + 4} className="clab" textAnchor="end" fontSize={11.5}>
              {trunc(r.label, Math.floor(labW / 6.1))}
            </text>
            <g
              className={'ladder' + (clickable ? ' clickable' : '')}
              role={clickable ? 'button' : undefined}
              tabIndex={0}
              aria-label={title}
              onClick={r.onClick}
              onKeyDown={
                clickable
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        r.onClick();
                      }
                    }
                  : undefined
              }
              onMouseMove={(e) => show(e, title, trows)}
              onMouseLeave={hide}
              onFocus={(e) => {
                const b = e.currentTarget.getBoundingClientRect();
                show({ clientX: b.left + b.width / 2, clientY: b.bottom }, title, trows);
              }}
              onBlur={hide}
            >
              <rect x={labW} y={cy - rowH / 2} width={plotW} height={rowH} fill="transparent" />
              <line x1={X(r.p10)} y1={cy} x2={X(r.p90)} y2={cy} stroke={V('--ink-3')} strokeWidth={1.25} />
              <line x1={X(r.p10)} y1={cy - 4} x2={X(r.p10)} y2={cy + 4} stroke={V('--ink-3')} strokeWidth={1.25} />
              <line x1={X(r.p90)} y1={cy - 4} x2={X(r.p90)} y2={cy + 4} stroke={V('--ink-3')} strokeWidth={1.25} />
              <line
                x1={X(r.p25)}
                y1={cy}
                x2={X(r.p75)}
                y2={cy}
                stroke={V(tone)}
                strokeWidth={5}
                strokeLinecap="round"
                opacity={0.55}
              />
              {hasMu ? (
                <circle
                  cx={X(r.mu)}
                  cy={cy}
                  r={4.6}
                  fill={V('--panel')}
                  stroke={V('--ink')}
                  strokeWidth={1.8}
                />
              ) : null}
              <circle cx={X(r.p50)} cy={cy} r={4.2} fill={V(tone)} stroke={V('--panel')} strokeWidth={1.2} />
              <text x={w - padR + 8} y={cy + 4} className="vlab" textAnchor="start" fontSize={11}>
                {money(r.p50)}
              </text>
            </g>
          </g>
        );
      })}
    </svg>
  );
}

/** Key for the percentile ladder. */
export function LadderLegend() {
  const cy = 15;
  return (
    <svg className="chart boxkey" viewBox="0 0 430 40" role="img" aria-label="How to read the percentile ladder">
      <line x1={14} y1={cy} x2={150} y2={cy} stroke={V('--ink-3')} strokeWidth={1.25} />
      <line x1={14} y1={cy - 4} x2={14} y2={cy + 4} stroke={V('--ink-3')} strokeWidth={1.25} />
      <line x1={150} y1={cy - 4} x2={150} y2={cy + 4} stroke={V('--ink-3')} strokeWidth={1.25} />
      <line
        x1={46}
        y1={cy}
        x2={112}
        y2={cy}
        stroke={V('--s1')}
        strokeWidth={5}
        strokeLinecap="round"
        opacity={0.55}
      />
      <circle cx={70} cy={cy} r={4.2} fill={V('--s1')} stroke={V('--panel')} strokeWidth={1.2} />
      <circle cx={97} cy={cy} r={4.6} fill={V('--panel')} stroke={V('--ink')} strokeWidth={1.8} />
      <text x={14} y={34} className="nbadge" fontSize={9}>
        10th
      </text>
      <text x={46} y={34} className="nbadge" fontSize={9} textAnchor="middle">
        25th
      </text>
      <text x={70} y={34} className="nbadge" fontSize={9} textAnchor="middle">
        median
      </text>
      <text x={99} y={34} className="nbadge" fontSize={9} textAnchor="middle">
        mean
      </text>
      <text x={124} y={34} className="nbadge" fontSize={9} textAnchor="middle">
        75th
      </text>
      <text x={150} y={34} className="nbadge" fontSize={9} textAnchor="middle">
        90th
      </text>
      <text x={186} y={19} className="nbadge" fontSize={9.5}>
        the ring sits right of the dot wherever a long top tail pulls the average up
      </text>
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Dot distribution, laid out in rows
 *
 * The same chart as DotColumns turned on its side, for when there are too
 * many categories to give each one a readable column. Dots jitter vertically
 * inside each row; the average and median are vertical lines.
 *
 * rows: { label, sub?, dots: [{ v, e? }], avg, med, ref?, color?, onClick? }
 * ------------------------------------------------------------------ */
export function DotRows({ rows, opts = {} }) {
  const { show, hide } = useTip();

  const labW = opts.labelWidth || 206;
  const rowH = opts.rowH || 30;
  const gap = 6;
  const padR = 92;
  const padT = 28;
  const w = opts.width || 880;
  const h = padT + rows.length * (rowH + gap) + 12;
  const plotW = w - labW - padR;
  const xMax = opts.xMax || 200000;
  const X = (v) => labW + (Math.min(v, xMax) / xMax) * plotW;

  const maxE = Math.max(1, ...rows.flatMap((r) => r.dots.map((d) => d.e || 0)));
  const sized = maxE > 1;
  const rOf = (d) => (sized ? Math.max(1.5, Math.min(7, Math.sqrt((d.e || 0) / maxE) * 7)) : 2);

  return (
    <svg
      className="chart dotrows"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Distribution of earnings'}
    >
      {[0, 1, 2, 3, 4].map((t) => {
        const tv = (xMax * t) / 4;
        return (
          <g key={`t${t}`}>
            <line x1={X(tv)} y1={padT - 10} x2={X(tv)} y2={h - 8} className="grid" strokeWidth={1} />
            <text x={X(tv)} y={padT - 16} className="nbadge" textAnchor="middle" fontSize={10}>
              {tv === 0 ? '$0' : '$' + fmt(tv / 1000) + 'k'}
            </text>
          </g>
        );
      })}

      {rows.map((r, ri) => {
        const y0 = padT + ri * (rowH + gap);
        const cy = y0 + rowH / 2;
        const band = rowH - 6;
        const tone = r.color || (r.ref ? '--ink-3' : '--s1');
        const clickable = typeof r.onClick === 'function';

        return (
          <g key={r.label + ri} className={'dotrow' + (r.ref ? ' ref' : '')}>
            <text x={labW - 11} y={cy + 4} className="clab" textAnchor="end" fontSize={11.5}>
              {trunc(r.label, Math.floor(labW / 6.1))}
            </text>

            <rect x={labW} y={cy - band / 2} width={Math.max(0, X(r.avg) - labW)} height={band} fill={V(tone)} opacity={0.07} />

            {r.dots.map((d, i) => {
              const over = d.v > xMax;
              const dx = over ? X(xMax) - 4 : X(d.v);
              const dy = cy - band / 2 + 2 + hash01(ri * 7919 + i) * (band - 4);
              const on = {
                onMouseMove: (e) => {
                  const t = opts.dotTip ? opts.dotTip(d, r) : { title: '', rows: [] };
                  show(e, t.title, t.rows);
                },
                onMouseLeave: hide,
              };
              return over ? (
                <path
                  key={i}
                  d={`M${dx + 4} ${dy}L${dx - 2} ${dy + 3.4}L${dx - 2} ${dy - 3.4}Z`}
                  fill={V(tone)}
                  opacity={0.85}
                  className="dot over"
                  {...on}
                />
              ) : (
                <circle key={i} cx={dx} cy={dy} r={rOf(d)} fill={V(tone)} opacity={0.5} className="dot" {...on} />
              );
            })}

            <line x1={X(r.med)} y1={cy - band / 2} x2={X(r.med)} y2={cy + band / 2} stroke={V('--ink-2')} strokeWidth={1.5} strokeDasharray="5 3" />
            <line x1={X(r.avg)} y1={cy - band / 2 - 2} x2={X(r.avg)} y2={cy + band / 2 + 2} stroke={V('--panel')} strokeWidth={4} />
            <line x1={X(r.avg)} y1={cy - band / 2 - 2} x2={X(r.avg)} y2={cy + band / 2 + 2} stroke={V('--ink')} strokeWidth={2} />

            <g
              className={clickable ? 'collabel clickable' : 'collabel'}
              role={clickable ? 'button' : undefined}
              tabIndex={clickable ? 0 : undefined}
              aria-label={clickable ? `${r.label} detail` : undefined}
              onClick={r.onClick}
              onKeyDown={
                clickable
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        r.onClick();
                      }
                    }
                  : undefined
              }
            >
              <rect x={labW} y={y0} width={plotW} height={rowH} fill="transparent" />
              <text x={w - padR + 8} y={cy + 4} className="vlab" textAnchor="start" fontSize={11}>
                {money(r.avg)}
              </text>
            </g>
          </g>
        );
      })}
      {/* Drawn last so the label is not painted over by the dots. */}
      {opts.rule !== undefined && opts.rule < xMax ? (
        <g>
          <line
            x1={X(opts.rule)}
            y1={padT - 6}
            x2={X(opts.rule)}
            y2={h - 8}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          {opts.ruleLabel ? (
            <text x={X(opts.rule) + 5} y={h - 1} className="nbadge rulelab" fontSize={9.5} fill={V('--ink-2')}>
              {opts.ruleLabel}
            </text>
          ) : null}
        </g>
      ) : null}

    </svg>
  );
}
