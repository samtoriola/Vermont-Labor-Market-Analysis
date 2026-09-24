'use client';

import { LC, SERIES, SERIES_HEX } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { downloadCsv, exportName } from '@/lib/csv';

export function Panel({ title, cap, src, exportData, children }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <h3>{title}</h3>
        {exportData ? (
          <ExportButton
            label={exportData.name || title}
            cols={exportData.cols}
            rows={exportData.rows}
          />
        ) : null}
      </div>
      {cap ? <p className="cap">{cap}</p> : null}
      {children}
      {src ? <div className="srcline">{src}</div> : null}
    </div>
  );
}

/** Downloads the panel's underlying rows as CSV. Client-side; nothing is uploaded. */
export function ExportButton({ label, cols, rows }) {
  if (!rows || !rows.length) return null;
  return (
    <button
      type="button"
      className="exportbtn"
      onClick={() => downloadCsv(exportName(label), cols, rows)}
      title={`Download ${rows.length} rows as CSV`}
    >
      Export CSV
    </button>
  );
}

export function Answer({ label = 'In short', children }) {
  return (
    <div className="answer">
      <span className="alabel">{label}</span>
      {children}
    </div>
  );
}

export function Callout({ label, children }) {
  return (
    <div className="callout">
      <span className="colabel">{label}</span>
      {children}
    </div>
  );
}

/** Section heading. No question numbers — this reads as a report, not a response. */
export function VHead({ title, children }) {
  return (
    <div className="vhead">
      <h2>{title}</h2>
      {children ? <p>{children}</p> : null}
    </div>
  );
}

/**
 * Legend. Pass hexes to print the colour code beside each label — worth doing
 * where the colour itself carries meaning (a threshold, a ramp position).
 */
export function Legend({ labels, colors, hexes }) {
  return (
    <ul className="legend">
      {labels.map((l, i) => (
        <li key={l}>
          <span className="sw" style={{ background: `var(${colors[i]})` }} />
          {l}
          {hexes && hexes[i] ? <span className="hex">{hexes[i]}</span> : null}
        </li>
      ))}
    </ul>
  );
}

export function Tiles({ items }) {
  return (
    <div className="tiles">
      {items.map((t) => (
        <div className="tile" key={t[0]}>
          <div className="tl">{t[0]}</div>
          <div className="tv">{t[1]}</div>
          <div className="td">{t[2]}</div>
        </div>
      ))}
    </div>
  );
}

export function Table({ cols, rows }) {
  return (
    <div className="tblwrap">
      <table>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} onClick={r.onClick} style={r.onClick ? { cursor: 'pointer' } : undefined}>
              {r.cells.map((c, j) => (
                <td key={j} className={j ? 'num' : undefined}>
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Numeric span in the tabular figure style. */
export function N({ children }) {
  return <span className="num">{children}</span>;
}

/** Makes the drill-down discoverable rather than hidden. */
export function DrillHint({ children = 'Click any bar to see the occupations behind it.' }) {
  return <p className="drillhint">{children}</p>;
}

/** Living-wage household selector. The benchmark is a choice, so it is a control. */
export function LwPicker({ value, onChange }) {
  const hourly = LC.livingWage[value];
  return (
    <div className="ctrls">
      <label htmlFor="lw-select">
        <span>Living-wage benchmark</span>
        <select id="lw-select" value={value} onChange={(e) => onChange(e.target.value)}>
          {Object.keys(LC.livingWage).map((k) => (
            <option key={k} value={k}>
              {k + '  —  $' + LC.livingWage[k].toFixed(2) + '/hr'}
            </option>
          ))}
        </select>
      </label>
      <span className="ctrlnote">
        {'$' +
          hourly.toFixed(2) +
          '/hr = ' +
          money(hourly * LC.hours) +
          '/yr at ' +
          fmt(LC.hours) +
          ' hours'}
      </span>
    </div>
  );
}

export { SERIES, SERIES_HEX };
