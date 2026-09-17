'use client';

import { MAP, ORDINAL_HEX } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { useTipHandlers } from './Tooltip';

/**
 * Vermont county choropleth. One hue, light to dark (Ocean tints), because every
 * metric here is sequential. County outlines come from the Census TIGER county
 * boundaries, simplified to 882 points and projected equal-aspect at build time,
 * so there is no mapping library and nothing to fetch at runtime.
 */

const METRICS = {
  ba: {
    label: "Bachelor's or higher, 25–64",
    get: (r) => r.ba,
    fmt: (v) => v.toFixed(1) + '%',
    src: 'ACS 2016–2020 5-year',
  },
  inc: {
    label: 'Median household income',
    get: (r) => r.inc,
    fmt: (v) => money(v),
    src: 'ACS 2016–2020 5-year',
  },
  incLw: {
    label: 'Income ÷ living wage',
    get: (r) => r.incLw,
    fmt: (v) => v.toFixed(2) + '×',
    src: 'ACS ÷ MIT Living Wage 2025',
  },
  lwH: {
    label: 'Living wage, 1 adult',
    get: (r) => r.lwH,
    fmt: (v) => '$' + v.toFixed(2) + '/hr',
    src: 'MIT Living Wage 2025',
  },
  pop: {
    label: 'Population',
    get: (r) => r.pop,
    fmt: (v) => fmt(v),
    src: 'ACS 2016–2020 5-year',
  },
};

export const MAP_METRICS = METRICS;

function County({ d, name, fill, selected, tipRows, onClick }) {
  const h = useTipHandlers(name + ' County', tipRows);
  return (
    <path
      d={d}
      fill={fill}
      data-sel={selected ? 'true' : undefined}
      role="button"
      aria-label={name + ' County'}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      {...h}
    />
  );
}

export default function VermontMap({ regions, metric, setMetric, selected, onSelect }) {
  const M = METRICS[metric];
  const byName = {};
  regions.forEach((r) => {
    byName[r.c] = r;
  });

  const vals = regions.map((r) => M.get(r)).filter((v) => v !== null && v !== undefined);
  const lo = Math.min(...vals);
  const hi = Math.max(...vals);

  // quintile position → ramp step; guard the degenerate lo === hi case
  const stepFor = (v) => {
    if (v === null || v === undefined) return 'var(--rule)';
    const t = hi === lo ? 0.999 : (v - lo) / (hi - lo);
    const i = Math.min(ORDINAL_HEX.length - 1, Math.floor(t * ORDINAL_HEX.length));
    return `var(--ord${i + 1})`;
  };

  const ordered = regions.slice().sort((a, b) => M.get(b) - M.get(a));

  return (
    <>
      <div className="ctrls">
        <label htmlFor="map-metric">
          <span>Shade counties by</span>
          <select id="map-metric" value={metric} onChange={(e) => setMetric(e.target.value)}>
            {Object.entries(METRICS).map(([k, m]) => (
              <option key={k} value={k}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
        <span className="ctrlnote">
          {M.fmt(lo)} – {M.fmt(hi)} across 14 counties · {M.src}
        </span>
      </div>

      <div className="mapwrap">
        <svg
          className="mapsvg"
          viewBox={MAP.viewBox}
          role="img"
          aria-label={'Vermont counties shaded by ' + M.label}
        >
          {Object.entries(MAP.counties).map(([fips, c]) => {
            const r = byName[c.n];
            if (!r) return null;
            return (
              <County
                key={fips}
                d={c.d}
                name={c.n}
                fill={stepFor(M.get(r))}
                selected={selected === c.n}
                tipRows={[
                  // lead with the shaded metric, then the rest without repeating it
                  [M.label, M.fmt(M.get(r))],
                  ...[
                    ['Population', fmt(r.pop), 'pop'],
                    ['Median income', money(r.inc), 'inc'],
                    ['BA+ 25–64', r.ba + '%', 'ba'],
                    ['Income ÷ living wage', r.incLw + '×', 'incLw'],
                    ['Living wage', '$' + r.lwH.toFixed(2) + '/hr', 'lwH'],
                  ]
                    .filter(([, , key]) => key !== metric)
                    .map(([k, v]) => [k, v]),
                  ['', 'click to pin'],
                ]}
                onClick={() => onSelect(selected === c.n ? null : c.n)}
              />
            );
          })}
        </svg>

        <div className="mapside">
          <div className="ramp">
            {ORDINAL_HEX.map((hex, i) => (
              <i key={hex} style={{ background: `var(--ord${i + 1})` }} title={hex} />
            ))}
          </div>
          <div className="ramplabs">
            <span>{M.fmt(lo)}</span>
            <span>{M.fmt(hi)}</span>
          </div>

          <div className="tblwrap" style={{ marginTop: 14 }}>
            <table>
              <thead>
                <tr>
                  <th>County</th>
                  <th>{M.label}</th>
                  <th>Population</th>
                </tr>
              </thead>
              <tbody>
                {ordered.map((r) => (
                  <tr
                    key={r.c}
                    onClick={() => onSelect(selected === r.c ? null : r.c)}
                    style={{
                      cursor: 'pointer',
                      background: selected === r.c ? 'var(--accent-soft)' : undefined,
                    }}
                  >
                    <td>{r.c}</td>
                    <td className="num">{M.fmt(M.get(r))}</td>
                    <td className="num">{fmt(r.pop)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
