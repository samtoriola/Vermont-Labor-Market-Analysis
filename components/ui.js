'use client';

import { useRef, useState, useEffect, useCallback } from 'react';
import { LC, SERIES, SERIES_HEX } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { downloadCsv, exportName } from '@/lib/csv';
import { downloadPanelPng } from '@/lib/png';
import { rankViews, defaultView, applyView } from '@/lib/rank';

export function Panel({ title, cap, src, note, exportData, children }) {
  const body = useRef(null);
  return (
    <div className="panel" ref={body}>
      <div className="panel-head">
        <h3>{title}</h3>
        <div className="panel-actions">
          <PngButton panelRef={body} title={title} note={note} src={src} />
          {exportData ? (
            <ExportButton
              label={exportData.name || title}
              cols={exportData.cols}
              rows={exportData.rows}
            />
          ) : null}
        </div>
      </div>
      {cap ? <p className="cap">{cap}</p> : null}
      {children}
      {/* The computed answer to "so what". A rule that ran and found nothing notable
          says so in a muted line; null means it could not run at all. */}
      {note ? (
        <p className={note.muted ? 'pnote muted' : 'pnote'}>{note.text}</p>
      ) : null}
      {src ? <div className="srcline">{src}</div> : null}
    </div>
  );
}

/**
 * Wraps a long ranked chart in a top / bottom / all control.
 *
 * A render prop rather than a prop on the chart components, because the choice is
 * state and the sections render through plain functions -- a hook called in there
 * would run only while that section is open, which is not a hook at all.
 *
 * `rows` is the whole pool. `show` is how many the chart drew before it had a
 * control, and leaving it out means the chart was already drawing everything.
 */
export function Ranked({ id, rows, show, children }) {
  const views = rankViews(rows ? rows.length : 0, show);
  const [view, setView] = useState(defaultView(show));

  const key = `vt-rank-${id}`;
  useEffect(() => {
    try {
      const v = localStorage.getItem(key);
      if (v && views.some((x) => x.id === v)) setView(v);
    } catch (e) {
      /* blocked storage -- keep the default */
    }
    // The ids are what matter; `views` is rebuilt every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, views.map((v) => v.id).join('|')]);

  const pick = useCallback(
    (next) => {
      setView(next);
      try {
        localStorage.setItem(key, next);
      } catch (e) {
        /* non-fatal */
      }
    },
    [key]
  );

  // A filter can leave too few rows to be worth splitting.
  if (!views.length) return children(rows);
  const current = views.some((v) => v.id === view) ? view : views[0].id;

  return (
    <>
      <div className="rankctl">
        <span className="sclab">Show</span>
        <div className="chips">
          {views.map((v) => (
            <button
              key={v.id}
              type="button"
              className={v.id === current ? 'on' : undefined}
              aria-pressed={v.id === current}
              onClick={() => pick(v.id)}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>
      {children(applyView(rows, current, show))}
    </>
  );
}

/**
 * Saves the panel's chart as a PNG. Rendered in the browser from the SVG that is
 * already on screen, so the image matches what the reader is looking at.
 *
 * The button hides itself when the panel holds no chart -- several panels are a
 * table or a definition list, where there is nothing to picture.
 */
export function PngButton({ panelRef, title, note, src }) {
  const [state, setState] = useState('idle');

  const save = useCallback(async () => {
    setState('busy');
    const ok = await downloadPanelPng(panelRef.current, {
      title,
      // A muted note says the rule ran and found nothing worth reporting, which is
      // not a claim worth carrying into a slide.
      note: note && !note.muted ? note.text : null,
      src,
      filename: exportName(title),
    });
    setState(ok ? 'idle' : 'failed');
  }, [panelRef, title, note, src]);

  // Settled after mount, because the panel's children are what decide this and the
  // ref is empty while the first render is still in progress. Starting hidden keeps
  // the server and first client render in agreement.
  const [hasChart, setHasChart] = useState(false);
  useEffect(() => {
    setHasChart(!!(panelRef.current && panelRef.current.querySelector('svg.chart')));
  });

  if (!hasChart) return null;

  return (
    <button
      type="button"
      className="exportbtn iconbtn"
      onClick={save}
      disabled={state === 'busy'}
      title={state === 'failed' ? 'Could not build the image' : 'Save this chart as a PNG'}
    >
      <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true" focusable="false">
        <path
          d="M8 1.5v7.5M8 9l-2.6-2.6M8 9l2.6-2.6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M2.5 11v2.5h11V11"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {state === 'busy' ? 'Saving' : 'PNG'}
    </button>
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
 * Legend. Pass hexes to print the color code beside each label — worth doing
 * where the color itself carries meaning (a threshold, a ramp position).
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

/**
 * Columns after the first are right-aligned as figures, which is right for almost
 * every table here. `text` lists the indices that hold prose instead.
 */
export function Table({ cols, rows, text = [] }) {
  const isText = (j) => j === 0 || text.includes(j);
  return (
    <div className="tblwrap">
      <table>
        <thead>
          <tr>
            {cols.map((c, j) => (
              <th key={c} className={isText(j) ? 'thtext' : undefined}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} onClick={r.onClick} style={r.onClick ? { cursor: 'pointer' } : undefined}>
              {r.cells.map((c, j) => (
                <td key={j} className={isText(j) ? (j ? 'tdtext' : undefined) : 'num'}>
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
/** Term and one-line definition. Reads faster than a paragraph. */
export function Defs({ items }) {
  return (
    <dl className="defs">
      {items.map(([term, body]) => (
        <div key={term}>
          <dt>{term}</dt>
          <dd>{body}</dd>
        </div>
      ))}
    </dl>
  );
}

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
