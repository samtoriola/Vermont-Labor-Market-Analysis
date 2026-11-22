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

