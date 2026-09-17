'use client';

import { LC, SER } from '@/lib/data';
import { fmt, money } from '@/lib/format';

export function Panel({ title, cap, src, children }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      {cap ? <p className="cap">{cap}</p> : null}
      {children}
      {src ? <div className="srcline">{src}</div> : null}
    </div>
  );
}

export function Answer({ label = 'Answer', children }) {
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

export function QHead({ n, children }) {
  return (
    <div className="qhead">
      <div className="qlabel">Research question {n}</div>
      <h2>{children}</h2>
    </div>
  );
}

export function Legend({ labels, colors }) {
  return (
    <ul className="legend">
      {labels.map((l, i) => (
        <li key={l}>
          <span className="sw" style={{ background: `var(${colors[i]})` }} />
          {l}
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
            <tr key={i} className={r.low ? 'lowN' : undefined}>
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

/** Numeric span in the tabular monospace face. */
export function N({ children }) {
  return <span className="num">{children}</span>;
}

/**
 * Living-wage household-type selector. SOW section 7 leaves the benchmark to VSCS,
 * so it is a control rather than a hardcoded assumption.
 */
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
        {'MIT Living Wage 2025, Vermont · $' +
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

export { SER };
