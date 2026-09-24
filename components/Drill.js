'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { fmt } from '@/lib/format';
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
                rowKey={(r) => r.s}
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
  const priced = occ.filter((o) => o.m);
  const above = priced.filter((o) => o.m >= lwAnnual);
  const wAbove = priced.length
    ? (above.reduce((a, o) => a + o.j, 0) / priced.reduce((a, o) => a + o.j, 0)) * 100
    : 0;
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
      ['Above living wage', wAbove.toFixed(1) + '%'],
      ['Turnover', turn === null ? '—' : turn.toFixed(1) + '%'],
      ...extraStats,
    ],
    src:
      'Lightcast · search, filter and sort above; export downloads the filtered rows',
  };
}
