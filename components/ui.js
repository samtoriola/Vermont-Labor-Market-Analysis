'use client';

import { useRef, useState, useEffect, useCallback } from 'react';
import { LC, SERIES, SERIES_HEX } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { downloadCsv, exportName } from '@/lib/csv';
import { downloadPanelPng } from '@/lib/png';
import DataTable from './DataTable';
import { ExportButton } from './ExportButton';
import { rankViews, defaultView, applyView } from '@/lib/rank';

export function Panel({ title, cap, src, note, data, exportData, children }) {
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
      {data ? <PanelData {...data} /> : null}
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
 * The figures behind a chart, folded away under it.
 *
 * A chart answers the one question it was drawn for. The table carries everything
 * else -- sort it another way, search it, or take the CSV -- without making every
 * section twice as long for readers who only wanted the chart. Closed by default
 * for that reason; the count is on the summary so it is clear what is in there.
 */
export function PanelData({ cols, rows, label, initialSort, onRowClick, note, unit = 'rows' }) {
  const [open, setOpen] = useState(false);

  // Keyed on the panel, and reset when the reader moves to another one: the
  // sections swap through the same slot in the tree, so without this a table left
  // open on one panel would carry its open state onto the next.
  const key = `vt-data-${label}`;
  useEffect(() => {
    let want = false;
    try {
      want = localStorage.getItem(key) === '1';
    } catch (e) {
      /* blocked storage -- start closed */
    }
    setOpen(want);
  }, [key]);

  const toggle = useCallback(() => {
    setOpen((v) => {
      try {
        localStorage.setItem(key, v ? '0' : '1');
      } catch (e) {
        /* non-fatal */
      }
      return !v;
    });
  }, [key]);

  if (!cols || !rows || !rows.length) return null;

  return (
    <div className="paneldata">
      <button
        type="button"
        className="datatoggle"
        aria-expanded={open}
        onClick={toggle}
      >
        <span className={open ? 'chev open' : 'chev'} aria-hidden="true">
          {'›'}
        </span>
        {open ? 'Hide the figures' : `Show the figures (${rows.length} ${unit})`}
      </button>
      {open ? (
        <DataTable
          cols={cols}
          rows={rows}
          initialSort={initialSort}
          exportLabel={label}
          onRowClick={onRowClick}
          note={note}
          pageSize={30}
        />
      ) : null}
    </div>
  );
}

/**
 * A row of chips. The three controls below differ in what they hold, not in how
 * they look, so the markup lives in one place.
 */
function ChipRow({ label, options, value, onPick }) {
  return (
    <div className="rankctl">
      {label ? <span className="sclab">{label}</span> : null}
      <div className="chips">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            className={o.id === value ? 'on' : undefined}
            aria-pressed={o.id === value}
            onClick={() => onPick(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * A chip choice that survives a reload. Blocked storage is not an error here:
 * the control still works, it just forgets. Whether a stored value is still a
 * valid option is settled at render, where the options are known.
 */
function useSticky(key, initial) {
  const [value, setValue] = useState(initial);

  useEffect(() => {
    try {
      const v = localStorage.getItem(key);
      if (v) setValue(v);
    } catch (e) {
      /* blocked storage -- keep the default */
    }
  }, [key]);

  const pick = useCallback(
    (next) => {
      setValue(next);
      try {
        localStorage.setItem(key, next);
      } catch (e) {
        /* non-fatal */
      }
    },
    [key]
  );

  return [value, pick];
}

/**
 * Measure and depth as one control bar, with the rows that pair selects.
 *
 * These used to be two controls that did not look related: a measure picker
 * above the panel and a top / bottom control inside it. They are related --
 * between them they decide what the panel is about -- and holding both here is
 * what lets the panel's read-out answer the combination, instead of reporting a
 * whole-population figure that does not move when the reader changes either one.
 *
 * `rowsFor` returns the whole pool for a measure, already in the order the chart
 * ranks it. The slice is taken here and handed to the body, so the chart and the
 * read-out cannot disagree about which rows are on screen.
 *
 * The second control is the top / bottom / all split by default, derived from
 * the row count. Pass `views` to name your own instead -- how many places to
 * show, say -- and `rowsFor` is then given both the measure and the view and
 * returns exactly the rows to draw.
 */
export function Scope({ id, viewId, measures, rowsFor, views: fixed, show, children }) {
  const [m, pickM] = useSticky(`vt-pick-${id}`, measures.length ? measures[0].id : null);
  const [v, pickV] = useSticky(
    `vt-rank-${viewId || id}`,
    fixed && fixed.length ? fixed[0].id : defaultView(show)
  );

  if (!measures.length) return null;
  const measure = measures.some((o) => o.id === m) ? m : measures[0].id;

  if (fixed && fixed.length) {
    const view = fixed.some((x) => x.id === v) ? v : fixed[0].id;
    return (
      <>
        <div className="ctlbar">
          <ChipRow label="Measure" options={measures} value={measure} onPick={pickM} />
          <ChipRow label={viewLabel(fixed)} options={fixed} value={view} onPick={pickV} />
        </div>
        {children(measure, rowsFor(measure, view) || [], view)}
      </>
    );
  }

  const rows = rowsFor(measure) || [];
  const derived = rankViews(rows.length, show);
  const view = derived.some((x) => x.id === v) ? v : defaultView(show);

  return (
    <>
      <div className="ctlbar">
        <ChipRow label="Measure" options={measures} value={measure} onPick={pickM} />
        {derived.length ? (
          <ChipRow label="Show" options={derived} value={view} onPick={pickV} />
        ) : null}
      </div>
      {children(measure, derived.length ? applyView(rows, view, show) : rows, view)}
    </>
  );
}

/** Named views can carry their own control label; "Show" is the fallback. */
function viewLabel(views) {
  return (views[0] && views[0].group) || 'Show';
}

/**
 * One of several views of the same shape, chosen with a row of buttons.
 *
 * Where a section would otherwise stack a panel per category -- five credential
 * tiers, say -- this shows one and lets the reader pick, which is the difference
 * between a page that scrolls and a panel that fits.
 *
 * A component rather than a prop, for the same reason as `Ranked`: the choice is
 * state, and the sections render through plain functions.
 */
export function Picker({ id, label, options, children }) {
  const [active, setActive] = useState(options.length ? options[0].id : null);

  const key = `vt-pick-${id}`;
  useEffect(() => {
    try {
      const v = localStorage.getItem(key);
      if (v && options.some((o) => o.id === v)) setActive(v);
    } catch (e) {
      /* blocked storage -- keep the first option */
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, options.map((o) => o.id).join('|')]);

  const pick = useCallback(
    (next) => {
      setActive(next);
      try {
        localStorage.setItem(key, next);
      } catch (e) {
        /* non-fatal */
      }
    },
    [key]
  );

  if (!options.length) return null;
  const current = options.some((o) => o.id === active) ? active : options[0].id;

  return (
    <>
      <ChipRow label={label} options={options} value={current} onPick={pick} />
      {children(current)}
    </>
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
      <ChipRow label="Show" options={views} value={current} onPick={pick} />
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

/**
 * Legend for a sequential ramp: what the shading means, and the two ends of it.
 *
 * A categorical legend names every colour because the colours are names. A ramp
 * has no names, only a direction, so the honest legend is the direction and the
 * range it covers.
 */
export function RampLegend({ label, lo, hi }) {
  return (
    <div className="ramplegend">
      <span className="rl">{label}</span>
      <span className="end">{lo}</span>
      <span className="bar" aria-hidden="true" />
      <span className="end">{hi}</span>
    </div>
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

export { ExportButton };
