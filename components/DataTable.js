'use client';

import { useState, useMemo } from 'react';
import { fmt, money } from '@/lib/format';
import { ExportButton } from './ui';

/**
 * Sortable, filterable, exportable table shared by the master view and the
 * drill-down.
 *
 * Sorting works on the underlying value, not the rendered string: sorting
 * "$53,886" as text would put $9,000 above $100,000. Export always covers every
 * filtered row, not just the visible page.
 */

export function render(kind, v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  switch (kind) {
    case 'num':
      return fmt(v);
    case 'num1':
      return v.toFixed(1);
    case 'money':
      return money(v);
    case 'pct':
      return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
    case 'rate':
      return v.toFixed(1) + '%';
    case 'x':
      return v.toFixed(2) + '×';
    default:
      return String(v);
  }
}

/** pct cells carry direction in colour as well as sign. */
function cellClass(kind, v) {
  if (kind === 'text') return undefined;
  if (kind === 'pct' && typeof v === 'number') {
    if (v > 0) return 'up';
    if (v < 0) return 'down';
  }
  return 'num';
}

export default function DataTable({
  cols,
  rows,
  initialSort,
  exportLabel,
  pageSize = 50,
  onRowClick,
  rowKey = (r, i) => i,
  note,
}) {
  const [sort, setSort] = useState(initialSort || { k: cols[0].k, dir: 1 });
  const [q, setQ] = useState('');
  const [colFilter, setColFilter] = useState({ k: '', min: '', max: '' });
  const [showAll, setShowAll] = useState(false);

  const numericCols = cols.filter((c) => c.kind !== 'text');

  const view = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let out = rows;

    if (needle) {
      const textCols = cols.filter((c) => c.kind === 'text');
      out = out.filter((r) =>
        textCols.some((c) => String(c.get(r) ?? '').toLowerCase().includes(needle))
      );
    }

    if (colFilter.k && (colFilter.min !== '' || colFilter.max !== '')) {
      const col = cols.find((c) => c.k === colFilter.k);
      const lo = colFilter.min === '' ? -Infinity : Number(colFilter.min);
      const hi = colFilter.max === '' ? Infinity : Number(colFilter.max);
      out = out.filter((r) => {
        const v = col.get(r);
        return typeof v === 'number' && v >= lo && v <= hi;
      });
    }

    const col = cols.find((c) => c.k === sort.k) || cols[0];
    return out.slice().sort((a, b) => {
      const x = col.get(a);
      const y = col.get(b);
      // missing values sink to the bottom regardless of direction
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return typeof x === 'string' ? x.localeCompare(y) * sort.dir : (x - y) * sort.dir;
    });
  }, [rows, cols, q, colFilter, sort]);

  const shown = showAll ? view : view.slice(0, pageSize);
  const exportRows = view.map((r) => ({ cells: cols.map((c) => render(c.kind, c.get(r))) }));
  const filtered = view.length !== rows.length;

  return (
    <>
      <div className="dtbar">
        <input
          className="dtsearch"
          type="search"
          placeholder="Search occupations…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search rows"
        />

        <label className="dtfilter">
          <span>Filter</span>
          <select
            value={colFilter.k}
            onChange={(e) => setColFilter({ ...colFilter, k: e.target.value })}
            aria-label="Column to filter"
          >
            <option value="">no column</option>
            {numericCols.map((c) => (
              <option key={c.k} value={c.k}>
                {c.label}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="min"
            value={colFilter.min}
            disabled={!colFilter.k}
            onChange={(e) => setColFilter({ ...colFilter, min: e.target.value })}
            aria-label="Minimum"
          />
          <input
            type="number"
            placeholder="max"
            value={colFilter.max}
            disabled={!colFilter.k}
            onChange={(e) => setColFilter({ ...colFilter, max: e.target.value })}
            aria-label="Maximum"
          />
          {colFilter.k || q ? (
            <button
              type="button"
              className="freset"
              onClick={() => {
                setColFilter({ k: '', min: '', max: '' });
                setQ('');
              }}
            >
              reset
            </button>
          ) : null}
        </label>

        <span className="dtcount">
          {filtered ? (
            <>
              <strong>{fmt(view.length)}</strong> of {fmt(rows.length)}
            </>
          ) : (
            <>{fmt(rows.length)} rows</>
          )}
          {note ? ` · ${note}` : ''}
        </span>

        {exportLabel ? (
          <ExportButton
            label={exportLabel}
            cols={cols.map((c) => c.label)}
            rows={exportRows}
          />
        ) : null}
      </div>

      <div className="tblwrap">
        <table>
          <thead>
            <tr>
              {cols.map((c) => {
                const on = sort.k === c.k;
                return (
                  <th
                    key={c.k}
                    className="sortable"
                    aria-sort={on ? (sort.dir === -1 ? 'descending' : 'ascending') : 'none'}
                    onClick={() => setSort({ k: c.k, dir: on ? -sort.dir : -1 })}
                    title={`Sort by ${c.label}`}
                  >
                    {c.label}
                    <span className="sortmark">{on ? (sort.dir === -1 ? '▾' : '▴') : '⇅'}</span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr
                key={rowKey(r, i)}
                onClick={onRowClick ? () => onRowClick(r) : undefined}
                style={onRowClick ? { cursor: 'pointer' } : undefined}
              >
                {cols.map((c) => {
                  const v = c.get(r);
                  return (
                    <td key={c.k} className={cellClass(c.kind, v)}>
                      {render(c.kind, v)}
                    </td>
                  );
                })}
              </tr>
            ))}
            {shown.length === 0 ? (
              <tr>
                <td colSpan={cols.length} style={{ textAlign: 'center', color: 'var(--ink-3)' }}>
                  No rows match these filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {view.length > pageSize ? (
        <button type="button" className="freset" onClick={() => setShowAll(!showAll)}>
          {showAll ? `show first ${pageSize}` : `show all ${fmt(view.length)}`}
        </button>
      ) : null}
    </>
  );
}
