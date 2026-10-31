'use client';

import { useState, useCallback } from 'react';
import { fmt, money } from '@/lib/format';
import { CHART_W, SPLIT_W } from '@/lib/chartw';
import { shortLabel } from '@/lib/labels';
import { rollUp } from '@/lib/wage';

/**
 * Master and detail, side by side.
 *
 * The chart starts at full width with nothing chosen, which is the view a reader
 * who only wants the ranking should get. Clicking a bar opens that bar's detail
 * beside it and the chart narrows to make room; clicking the same bar again closes
 * the pane and gives the width back.
 *
 * This replaces the full-screen drill for the first question a click asks -- what
 * is inside this bar -- because an overlay hides the chart that prompted it, and a
 * reader comparing two families had to open, read, close, open. The overlay is
 * still one click further on, for the whole table.
 *
 * A render prop rather than props on the chart, for the same reason as `Ranked`:
 * the selection is state, and sections render through plain functions.
 *
 * `children(select, active, width)` -- call `select(key)` from a bar, compare
 * `active` against that key to mark it, and draw at `width`. A key rather than a
 * row, because the rows a chart draws are often built for the chart and are not
 * the rows the detail is looked up from.
 */
export function Split({ items, keyOf, detail, children }) {
  const [sel, setSel] = useState(null);

  const select = useCallback((k) => setSel((cur) => (cur === k ? null : k)), []);

  const clear = useCallback(() => setSel(null), []);

  // Looked up by key rather than held as an object, so a re-render that rebuilds
  // the rows -- a living-wage change, say -- keeps the pane on the same item.
  const row = sel === null ? null : items.filter((i) => keyOf(i) === sel)[0];
  const d = row ? detail(row) : null;

  return (
    <div className={d ? 'split open' : 'split'}>
      <div className="split-chart">{children(select, sel, d ? SPLIT_W : CHART_W)}</div>
      {d ? <DetailPane d={d} onClose={clear} /> : null}
    </div>
  );
}

/** The pane itself. Kept separate so the shape of a detail is one thing to read. */
function DetailPane({ d, onClose }) {
  return (
    <aside className="detail" aria-label={`Detail: ${d.title}`}>
      <div className="detail-head">
        <div>
          {d.label ? <span className="dlabel">{d.label}</span> : null}
          <h4>{d.title}</h4>
        </div>
        <button type="button" className="dxclose" onClick={onClose} aria-label="Close the detail">
          ×
        </button>
      </div>

      {d.stats && d.stats.length ? (
        <div className="detail-stats">
          {d.stats.map(([v, k]) => (
            <div key={k}>
              <div className="dv">{v}</div>
              <div className="dk">{k}</div>
            </div>
          ))}
        </div>
      ) : null}

      {d.note ? <p className="detail-note">{d.note}</p> : null}

      {d.rows && d.rows.length ? (
        <table className="minitable">
          <thead>
            <tr>
              {d.cols.map((c, j) => (
                <th key={c} className={j ? 'num' : undefined}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {d.rows.map((r, i) => (
              <tr key={i}>
                {r.map((c, j) => (
                  <td key={j} className={j ? 'num' : undefined}>
                    {c}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {d.more ? (
        <button type="button" className="morelink" onClick={d.more.onClick}>
          {d.more.label}
          <span aria-hidden="true"> →</span>
        </button>
      ) : null}
    </aside>
  );
}

/**
 * The standard detail for a group of occupations -- a family, a size band, a
 * credential tier. The pane shows the largest few; `more` opens the full table.
 *
 * Deliberately three columns. The pane is 420px and the point of it is to answer
 * "what work is this" at a glance; everything else is a click away in the table
 * under the chart or in the overlay.
 */
export function occDetail({ label, title, occ, lwAnnual, stats, top = 8, onMore }) {
  const sorted = occ.slice().sort((a, b) => b.j - a.j);
  const jobs = occ.reduce((a, o) => a + o.j, 0);
  // Same measure as everywhere else: the benchmark's position along each
  // occupation's own ladder, weighted by its jobs. See lib/wage.js.
  const roll = rollUp(occ, lwAnnual);

  return {
    label,
    title,
    stats: stats || [
      [fmt(jobs), 'Jobs today'],
      [roll ? (100 - roll.below).toFixed(0) + '%' : '—', 'Pay a living wage'],
    ],
    note:
      occ.length > top
        ? `The ${top} largest of ${fmt(occ.length)} occupations.`
        : `All ${fmt(occ.length)} occupations.`,
    cols: ['Occupation', 'Jobs', 'Typical pay'],
    // Trailing "Except ..." and "All Other" clauses are dropped here as they are on
    // a chart axis: the pane is for a glance, and the full name is one click away.
    rows: sorted.slice(0, top).map((o) => [shortLabel(o.n), fmt(o.j), o.m ? money(o.m) : '—']),
    more: onMore
      ? { label: `All ${fmt(occ.length)} occupations, with every measure`, onClick: onMore }
      : null,
  };
}

/**
 * The same pane for a sector's detailed industries.
 *
 * Separate from occDetail rather than generalised with it: an industry row has no
 * entry credential and no living-wage comparison, so a shared function would be a
 * list of options neither caller reads in full.
 */
export function industryDetail({ title, ind, stats, top = 8, onMore }) {
  return {
    label: 'Industry sector',
    title,
    stats,
    note:
      ind.length > top
        ? `The ${top} largest of ${fmt(ind.length)} industries.`
        : `All ${fmt(ind.length)} industries.`,
    cols: ['Industry', 'Jobs', 'Average pay'],
    rows: ind.slice(0, top).map((d) => [d.n, fmt(d.j), d.earn ? money(d.earn) : '—']),
    more: onMore
      ? { label: `All ${fmt(ind.length)} industries in this sector`, onClick: onMore }
      : null,
  };
}
