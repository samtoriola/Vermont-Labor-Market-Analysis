'use client';

import { useState, useMemo } from 'react';
import { LC, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { useFilters } from './FilterContext';
import { useDrill, occDrill } from './Drill';
import { ExportButton } from './ui';

/**
 * The master occupation table: every Vermont occupation with both growth measures,
 * responding to the shared cross-filters, sortable, exportable, and with each row
 * opening its family in the drill-down.
 *
 * Observed change (2021-2025) and projected change (2025-2030) sit side by side
 * deliberately — they disagree, and a table showing only one invites the reader to
 * treat a forecast as history.
 */

const COLS = [
  ['n', 'Occupation', (o) => o.n, 'text'],
  ['j', 'Jobs 2025', (o) => o.j, 'num'],
  ['chgPct', 'Change 2021–25', (o) => o.chgPct, 'pct'],
  ['g', 'Projected 25–30', (o) => o.g, 'pct'],
  ['m', 'Median', (o) => o.m, 'money'],
  ['o', 'Openings /yr', (o) => o.o, 'num'],
  ['pp', 'Postings /100', (o) => (o.j ? (o.p / o.j) * 100 : null), 'num1'],
  ['t', 'Entry credential', (o) => o.t, 'text'],
];

function render(kind, v, lwa) {
  if (v === null || v === undefined) return '—';
  if (kind === 'num') return fmt(v);
  if (kind === 'num1') return v.toFixed(1);
  if (kind === 'money') return money(v);
  if (kind === 'pct') return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
  return v;
}

export default function OccTable({ lw, limit = 50 }) {
  const { apply, f } = useFilters();
  const { open } = useDrill();
  const [sort, setSort] = useState({ key: 'j', dir: -1 });
  const [showAll, setShowAll] = useState(false);
  const LWA = lwAnnual(lw);

  const rows = useMemo(() => {
    const col = COLS.find((c) => c[0] === sort.key) || COLS[1];
    const get = col[2];
    return apply(LC.allOcc)
      .slice()
      .sort((a, b) => {
        const x = get(a);
        const y = get(b);
        if (x === null || x === undefined) return 1;
        if (y === null || y === undefined) return -1;
        return typeof x === 'string' ? x.localeCompare(y) * sort.dir : (x - y) * sort.dir;
      });
  }, [apply, sort]);

  const shown = showAll ? rows : rows.slice(0, limit);

  // Export carries every filtered row, not just the visible page.
  const exportCols = COLS.map((c) => c[1]).concat(['Family', 'SOC']);
  const exportRows = rows.map((o) => ({
    cells: COLS.map((c) => render(c[3], c[2](o), LWA)).concat([o.f, o.s]),
  }));

  function header(c) {
    const on = sort.key === c[0];
    return (
      <th
        key={c[0]}
        onClick={() => setSort({ key: c[0], dir: on ? -sort.dir : -1 })}
        style={{ cursor: 'pointer', color: on ? 'var(--accent)' : undefined }}
        title="Sort by this column"
      >
        {c[1]}
        {on ? (sort.dir === -1 ? ' ▾' : ' ▴') : ''}
      </th>
    );
  }

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>All occupations</h3>
        <ExportButton label="all-occupations" cols={exportCols} rows={exportRows} />
      </div>
      <p className="cap">
        Every Vermont occupation passing the filters above, with observed change over
        2021–2025 beside the 2025–2030 projection. Click a column to sort, or a row to open
        its occupational family. Export downloads all {fmt(rows.length)} filtered rows.
      </p>

      <div className="tblwrap">
        <table>
          <thead>
            <tr>{COLS.map(header)}</tr>
          </thead>
          <tbody>
            {shown.map((o) => (
              <tr
                key={o.s}
                style={{ cursor: 'pointer' }}
                onClick={() =>
                  open(
                    occDrill({
                      label: 'Occupational family',
                      title: o.f,
                      cap: `Opened from ${o.n}. Every occupation in this family, largest first.`,
                      occ: occByFamily(o.f),
                      lwAnnual: LWA,
                    })
                  )
                }
              >
                {COLS.map((c) => {
                  const v = c[2](o);
                  const cls =
                    c[3] === 'pct' && typeof v === 'number'
                      ? v > 0
                        ? 'up'
                        : v < 0
                          ? 'down'
                          : 'num'
                      : c[3] === 'text'
                        ? undefined
                        : 'num';
                  return (
                    <td key={c[0]} className={cls}>
                      {render(c[3], v, LWA)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > limit ? (
        <button type="button" className="freset" onClick={() => setShowAll(!showAll)}>
          {showAll ? `show first ${limit}` : `show all ${fmt(rows.length)}`}
        </button>
      ) : null}

      <div className="srcline">
        Lightcast · observed change from 2021/2025 jobs · projection from 2030 jobs ·
        green is growth, amber decline
      </div>
    </div>
  );
}
