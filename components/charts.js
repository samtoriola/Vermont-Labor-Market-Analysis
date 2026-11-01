'use client';

import { useTipHandlers } from './Tooltip';
import { fmt, money, niceMax, trunc, fmtVal } from '@/lib/format';
import { SERIES } from '@/lib/data';
import { CHART_W } from '@/lib/chartw';
import { shortLabel } from '@/lib/labels';

/**
 * Wraps an SVG group so the tooltip hook runs once per mark instance.
 * Calling useTipHandlers directly inside a .map() would break the rules of hooks.
 */
function TipMark({ title, rows, meta, className = '', onClick, children }) {
  const h = useTipHandlers(title, rows, meta);
  const clickable = typeof onClick === 'function';
  return (
    <g
      className={(className + (clickable ? ' clickable' : '')).trim()}
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
  // A second figure per row, printed beside the first. Only worth it where the
  // bar already carries two measures -- length for one, fill for the other --
  // and the second has no axis of its own to be read against.
  const hasRight = rows.some((r) => r.right !== undefined && r.right !== null);
  const padR = (opts.money ? 96 : 84) + (hasRight ? 58 : 0);
  // The column heads need a line of their own above the axis ticks, which sit
  // at padT - 15 and are centre-anchored, so they reach past the plot's end.
  const padT = opts.valueHead || opts.rightHead ? 46 : 28;
  const w = opts.width || CHART_W;
  const h = padT + rows.length * (rowH + gap) + 4;
  const plotW = w - labW - padR;
  const signed = !!opts.signed;

  // A chart with a bar chosen fades the rest, so the pane beside it and the bar it
  // belongs to read as one thing. Nothing chosen, nothing faded.
  const hasSel = rows.some((r) => r.active);

  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.value)));
  // Round the axis to four round steps rather than to one round top. niceMax alone
  // takes $111,896 to $150,000, whose quarters are $37,500 and $112,500; rounding
  // the step instead gives $30,000 and a top of $120,000, and every tick is a
  // number a reader recognises.
  const max = opts.max !== undefined ? opts.max : niceMax(maxAbs / 4) * 4;

  // A zero-centered axis is right only when the bars actually straddle zero.
  // `signed` is the caller saying negatives are possible and values carry a sign;
  // whether any are present is a property of the rows, which a top or bottom slice
  // changes. Reading it from the data stops a slice of all-positive bars from
  // being drawn into half the plot with the other half empty.
  const twoSided = signed && rows.some((r) => r.value < 0);
  const zeroX = twoSided ? labW + plotW / 2 : labW;
  const scale = twoSided ? plotW / 2 / max : plotW / max;

  const ticks = twoSided
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
              className={tv === 0 && twoSided ? 'axis' : 'grid'}
              strokeWidth={1}
            />
            <text x={gx} y={padT - 15} className="nbadge" textAnchor="middle" fontSize={10}>
              {/* An axis of round numbers and bars carrying a decimal: "0% 25% 50%"
                  over "86.5%" reads better than five copies of ".0%". */}
              {fmtVal(tv, opts.tickDec === undefined ? opts : { ...opts, dec: opts.tickDec })}
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
        // The measure the bar is, as the card's headline; everything else stays a
        // row underneath it.
        const meta = {
          sub: opts.tipSub,
          big: [[shown, opts.valueLabel || 'Value'], ...(r.big || [])],
          foot: r.onClick ? opts.clickHint || 'Click for the detail' : undefined,
        };
        const dim = hasSel && !r.active;

        return (
          <g key={r.label + i}>
            {/* An empty track behind the bar, for charts where the remainder is
                itself an answer: a bar filling a third of the row says two thirds
                clear the benchmark, which a bar floating on the panel does not.
                Only honest on a fixed scale -- on a ranked axis the track would
                end at the largest row, which means nothing. */}
            {opts.track ? (
              <rect
                x={zeroX}
                y={y}
                width={max * scale}
                height={rowH}
                rx={4}
                fill={V('--track')}
                opacity={dim ? 0.5 : 1}
              />
            ) : null}
            <text
              x={labW - 11}
              y={y + rowH / 2 + 4}
              className={r.active ? 'clab on' : 'clab'}
              textAnchor="end"
              fontSize={12}
              opacity={dim ? 0.55 : 1}
            >
              {trunc(shortLabel(r.label), Math.floor(labW / 6.4))}
            </text>
            <TipMark
              title={r.label}
              rows={r.extra || []}
              meta={meta}
              className="bar"
              onClick={r.onClick}
            >
              {/* Choosing a bar fades the rest, so the pane beside it and the bar
                  it belongs to read as one thing. Where fill carries a measure
                  rather than a category, fading it destroys the chart's second
                  variable -- five shaded bands wash out to one. `keepFill` holds
                  the bars at full strength and lets the labels do the fading,
                  marking the chosen bar with an outline instead. */}
              <rect
                x={bx}
                y={y}
                width={bw}
                height={rowH}
                rx={4}
                fill={V(r.color || '--s1')}
                fillOpacity={dim && !opts.keepFill ? 0.32 : 1}
                stroke={r.active && opts.keepFill ? V('--ink') : undefined}
                strokeWidth={r.active && opts.keepFill ? 1.5 : undefined}
              />
              <text
                {...(opts.track || hasRight
                  // In a column past the end of the plot, not at each bar's tip.
                  // On a fixed track the remainder is the answer; where a second
                  // figure follows, two ragged diagonals would be unreadable.
                  ? { x: zeroX + max * scale + 9, textAnchor: 'start' }
                  : { x: v < 0 ? bx - 9 : bx + bw + 9, textAnchor: v < 0 ? 'end' : 'start' })}
                y={y + rowH / 2 + 4}
                className={r.active ? 'vlab on' : 'vlab'}
                fontSize={11.5}
                opacity={dim ? 0.5 : 1}
              >
                {shown}
              </text>
              {hasRight ? (
                <text
                  x={zeroX + max * scale + 67}
                  y={y + rowH / 2 + 4}
                  className="nbadge"
                  textAnchor="start"
                  fontSize={11.5}
                  opacity={dim ? 0.5 : 1}
                >
                  {r.right}
                </text>
              ) : null}
            </TipMark>
          </g>
        );
      })}

      {/* Two unlabelled columns of figures would be a guess. The heads sit above
          the plot rather than in it, so they do not read as a row. */}
      {opts.valueHead ? (
        <text
          x={zeroX + max * scale + 9}
          y={padT - 30}
          className="nbadge"
          textAnchor="start"
          fontSize={9}
        >
          {opts.valueHead}
        </text>
      ) : null}
      {hasRight && opts.rightHead ? (
        <text
          x={zeroX + max * scale + 67}
          y={padT - 30}
          className="nbadge"
          textAnchor="start"
          fontSize={9}
        >
          {opts.rightHead}
        </text>
      ) : null}
    </svg>
  );
}

/* ------------------------------------------------------------------ *
 * Ranked pay ranges
 * rows: { label, box: {p10,p25,p50,p75,p90}, right?, right2?, extra? }
 *
 * One row per category drawn as the span its pay actually covers, rather than
 * one bar at its midpoint. A bar says what the middle job earns and nothing
 * about how far the rest sit from it, which on a credential ladder is the
 * question -- two rungs can share a midpoint and lead to very different places.
 * Drawing the range also lets a benchmark be ruled down the chart, so where the
 * line cuts each row IS the share falling short, with no second chart.
 *
 * Deliberately not called a box plot, and the copy around it is not either: the
 * quartile-and-whisker vocabulary was taken out of this dashboard on purpose and
 * scripts/e2e_dots.py holds it out. The parts are named in plain words instead.
 * ------------------------------------------------------------------ */
export function RangeRows({ rows, opts = {} }) {
  const labW = opts.labelWidth || 206;
  const rowH = 62;
  const padT = 52;
  const w = opts.width || CHART_W;
  const hasRight = rows.some((r) => r.right !== undefined && r.right !== null);
  const padR = hasRight ? 202 : 58;
  const plotW = w - labW - padR;
  const h = padT + rows.length * rowH - 10;

  const lo = opts.xMin !== undefined ? opts.xMin : Math.min(...rows.map((r) => r.box.p10));
  const hi = opts.xMax !== undefined ? opts.xMax : Math.max(...rows.map((r) => r.box.p90));
  const X = (v) => labW + ((v - lo) / (hi - lo)) * plotW;

  const step = opts.tickStep || (hi - lo) / 4;
  const ticks = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1; t += step) ticks.push(t);

  const hasSel = rows.some((r) => r.active);
  const col1 = w - 114;
  const col2 = w - 4;

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={opts.aria || 'Ranked pay ranges'}
    >
      {ticks.map((tv) => (
        <g key={`t${tv}`}>
          <line x1={X(tv)} y1={padT - 10} x2={X(tv)} y2={h - 14} className="grid" strokeWidth={1} />
          <text x={X(tv)} y={padT - 18} className="nbadge" textAnchor="middle" fontSize={10}>
            {opts.money ? `$${fmt(tv / 1000)}k` : fmt(tv)}
          </text>
        </g>
      ))}

      {opts.valueHead ? (
        <text x={col1} y={padT - 18} className="nbadge" textAnchor="end" fontSize={9}>
          {opts.valueHead}
        </text>
      ) : null}
      {hasRight && opts.rightHead ? (
        <text x={col2} y={padT - 18} className="nbadge" textAnchor="end" fontSize={9}>
          {opts.rightHead}
        </text>
      ) : null}

      {rows.map((r, i) => {
        const b = r.box;
        const cy = padT + i * rowH + 16;
        const dim = hasSel && !r.active;
        const meta = {
          big: [[money(b.p50), opts.valueLabel || 'The midpoint job'], ...(r.big || [])],
          foot: r.onClick ? opts.clickHint || 'Click for the detail' : undefined,
        };
        return (
          <g key={r.label + i} opacity={dim ? 0.42 : 1}>
            <text
              x={labW - 14}
              y={cy + 4}
              className={r.active ? 'clab on' : 'clab'}
              textAnchor="end"
              fontSize={12}
            >
              {trunc(shortLabel(r.label), Math.floor(labW / 6.4))}
            </text>
            <TipMark
              title={r.label}
              rows={r.extra || []}
              meta={meta}
              className="bar"
              onClick={r.onClick}
            >
              {/* An invisible band, so the whole row is a hover and click target
                  rather than only the 18px the drawn marks cover. */}
              <rect
                x={labW}
                y={cy - rowH / 2 + 8}
                width={plotW}
                height={rowH - 12}
                fill="transparent"
              />
              <line
                x1={X(b.p10)}
                y1={cy}
                x2={X(b.p90)}
                y2={cy}
                stroke={V('--ord3')}
                strokeWidth={1.5}
              />
              {[b.p10, b.p90].map((e) => (
                <line
                  key={`e${e}`}
                  x1={X(e)}
                  y1={cy - 7}
                  x2={X(e)}
                  y2={cy + 7}
                  stroke={V('--ord3')}
                  strokeWidth={1.5}
                />
              ))}
              <rect
                x={X(b.p25)}
                y={cy - 9}
                width={Math.max(2, X(b.p75) - X(b.p25))}
                height={18}
                rx={2}
                fill={V(r.color || '--ord2')}
                stroke={r.active ? V('--ink') : undefined}
                strokeWidth={r.active ? 1.5 : undefined}
              />
              <line
                x1={X(b.p50)}
                y1={cy - 13}
                x2={X(b.p50)}
                y2={cy + 13}
                stroke={V('--ord5')}
                strokeWidth={3}
                strokeLinecap="round"
              />
              <text
                x={X(b.p50)}
                y={cy + 31}
                className={r.active ? 'vlab on' : 'vlab'}
                textAnchor="middle"
                fontSize={11.5}
              >
                {money(b.p50)}
              </text>
              {hasRight ? (
                <>
                  <text x={col1} y={cy + 4} className="nbadge" textAnchor="end" fontSize={11.5}>
                    {r.right}
                  </text>
                  <text x={col2} y={cy + 4} className="nbadge" textAnchor="end" fontSize={11.5}>
                    {r.right2}
                  </text>
                </>
              ) : null}
            </TipMark>
          </g>
        );
      })}

      {/* Ruled through every row rather than drawn per row: the whole point is
          that one benchmark cuts five rungs in five different places. */}
      {opts.rule !== undefined && opts.rule >= lo && opts.rule <= hi ? (
        <g>
          <line
            x1={X(opts.rule)}
            y1={padT - 10}
            x2={X(opts.rule)}
            y2={h - 10}
            stroke={V('--ink-2')}
            strokeWidth={1.5}
            strokeDasharray="4 3"
          />
          <text
            x={X(opts.rule) + 7}
            y={h - 14}
            className="nbadge"
            fontSize={9.5}
            fill={V('--ink-2')}
          >
            {opts.ruleLabel}
          </text>
        </g>
      ) : null}
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
  const w = opts.width || CHART_W;
  const h = padT + rows.length * (rowH + gap) + 2;
  const plotW = w - labW - padR;
  const names = opts.tierNames || [];
  const colors = opts.colors || SERIES;
  // Same rule as the ranked bars: fade the rest only once something is chosen.
  const hasSel = rows.some((r) => r.active);

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
        const dim = hasSel && !r.active;
        let x = labW;
        const segs = r.parts.map((p, k) => {
          if (!p.v) return null;
          const pw = (p.v / tot) * plotW;
          const share = (p.v / tot) * 100;
          const seg = (
            <TipMark
              key={k}
              className="bar"
              title={`${r.label} — ${names[k] || 'Series ' + (k + 1)}`}
              rows={[['Jobs', fmt(p.v)]]}
              meta={{
                big: [[share.toFixed(1) + '%', opts.shareLabel || 'Share of this row']],
                foot: r.onClick ? opts.clickHint || 'Click for the detail' : undefined,
              }}
              onClick={r.onClick}
            >
              <rect
                x={x}
                y={y}
                width={Math.max(0.5, pw - 2)}
                height={rowH}
                rx={2}
                fill={V(colors[k])}
                fillOpacity={dim ? 0.32 : 1}
              />
            </TipMark>
          );
          x += pw;
          return seg;
        });

        return (
          <g key={r.label + i}>
            <text
              x={labW - 11}
              y={y + rowH / 2 + 4}
              className={r.active ? 'clab on' : 'clab'}
              textAnchor="end"
              fontSize={12}
              opacity={dim ? 0.55 : 1}
            >
              {trunc(shortLabel(r.label), Math.floor(labW / 6.4))}
            </text>
            {segs}
            {r.hi !== undefined ? (
              <text
                x={w - padR + 9}
                y={y + rowH / 2 + 4}
                className={r.active ? 'vlab on' : 'vlab'}
                textAnchor="start"
                fontSize={11}
                opacity={dim ? 0.5 : 1}
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
  const w = CHART_W;
  const h = padT + rows.length * (rowH + gap) + 4;
  const plotW = w - labW - padR;
  const max = niceMax(Math.max(...rows.map((r) => Math.max(r.a, r.b))));

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label="Employment 2021 versus 2025 by occupation group"
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
              {trunc(shortLabel(r.label), 28)}
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
  const w = CHART_W;
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
  const w = CHART_W;
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
              {trunc(shortLabel(r.label), 28)}
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
