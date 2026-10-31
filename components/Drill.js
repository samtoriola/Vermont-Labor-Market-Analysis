'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { fmt } from '@/lib/format';
import { rollUp } from '@/lib/wage';
import DataTable from './DataTable';
import { occCols } from './occCols';

const DrillContext = createContext({ open: () => {}, close: () => {} });

export function useDrill() {
  return useContext(DrillContext);
}

/**
 * Click-to-drill overlay. A chart mark or table row with underlying detail calls
 * open({...}); the page dims behind a scrim and the detail opens over it.
 */
export function DrillProvider({ children }) {
  const [d, setD] = useState(null);

  const open = useCallback((payload) => setD(payload), []);
  const close = useCallback(() => setD(null), []);

  // Escape closes, and body scroll locks while the scrim is up.
  useEffect(() => {
    if (!d) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [d, close]);

  return (
    <DrillContext.Provider value={{ open, close }}>
      {children}
      {d ? (
        <div
          className="scrim"
          role="dialog"
          aria-modal="true"
          aria-label={d.title}
          onClick={(e) => {
            if (e.target === e.currentTarget) close();
          }}
        >
          <div className="drill">
            <div className="drill-head">
              <div>
                {d.label ? <span className="dlabel">{d.label}</span> : null}
                <h3>{d.title}</h3>
              </div>
              <button type="button" className="dclose" onClick={close}>
                Close
              </button>
            </div>
            {d.cap ? <p className="dcap">{d.cap}</p> : null}
            {d.stats && d.stats.length ? (
              <div className="dstats">
                {d.stats.map(([k, v]) => (
                  <div className="dstat" key={k}>
                    <div className="k">{k}</div>
                    <div className="v">{v}</div>
                  </div>
                ))}
              </div>
            ) : null}
            {d.occ && d.occ.length ? (
              <DataTable
                cols={d.cols}
                rows={d.occ}
                initialSort={{ k: 'j', dir: -1 }}
                exportLabel={d.title}
                rowKey={d.rowKey || ((r) => r.s)}
                pageSize={25}
              />
            ) : null}
            {d.src ? <div className="srcline">{d.src}</div> : null}
          </div>
        </div>
      ) : null}
    </DrillContext.Provider>
  );
}

/** Standard occupation-detail payload, shared by the family and tier drill-downs. */
export function occDrill({ label, title, cap, occ, lwAnnual, extraStats = [] }) {
  const jobs = occ.reduce((a, o) => a + o.j, 0);
  // Read off each occupation's own pay ladder, not from whether its median clears
  // the benchmark -- the median rule counts every job in an occupation on one side
  // of a line half of them are on the wrong side of. See lib/wage.js.
  const roll = rollUp(occ, lwAnnual);
  const withTurn = occ.filter((o) => o.turn !== null && o.turn !== undefined && o.j > 0);
  const turn = withTurn.length
    ? withTurn.reduce((a, o) => a + o.turn * o.j, 0) / withTurn.reduce((a, o) => a + o.j, 0)
    : null;

  return {
    label,
    title,
    cap,
    occ,
    cols: occCols(lwAnnual),
    stats: [
      ['Occupations', fmt(occ.length)],
      ['Jobs, 2025', fmt(jobs)],
      ['Below living wage', roll ? roll.below.toFixed(1) + '%' : '—'],
      ['Turnover', turn === null ? '—' : turn.toFixed(1) + '%'],
      ...extraStats,
    ],
    src:
      'Search, filter and sort with the controls at the top; export downloads the filtered rows',
  };
}
