'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { fmt, money } from '@/lib/format';
import { Table, ExportButton } from './ui';

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
              <div className="drill-actions">
                {d.rows && d.rows.length ? (
                  <ExportButton label={d.title} cols={d.cols} rows={d.rows} />
                ) : null}
                <button type="button" className="dclose" onClick={close}>
                  Close
                </button>
              </div>
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
            {d.rows && d.rows.length ? <Table cols={d.cols} rows={d.rows} /> : null}
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
  return {
    label,
    title,
    cap,
    stats: [
      ['Occupations', fmt(occ.length)],
      ['Jobs, 2025', fmt(jobs)],
      ['Above living wage', wAbove.toFixed(1) + '%'],
      ...extraStats,
    ],
    cols: ['Occupation', 'Jobs 2025', 'Change 2021-25', 'Projected 25-30', 'Median',
           'vs LW', 'Openings', 'Postings /100', 'Entry credential'],
    rows: occ.slice(0, 200).map((o) => ({
      cells: [
        o.n,
        fmt(o.j),
        o.chgPct === null || o.chgPct === undefined
          ? '—'
          : (o.chgPct > 0 ? '+' : '') + o.chgPct + '%',
        o.g === null || o.g === undefined ? '—' : (o.g > 0 ? '+' : '') + o.g + '%',
        o.m ? money(o.m) : '—',
        o.m ? (o.m / lwAnnual).toFixed(2) + '×' : '—',
        fmt(o.o),
        o.j ? ((o.p / o.j) * 100).toFixed(1) : '—',
        o.t,
      ],
    })),
    src:
      occ.length > 200
        ? `Lightcast · 200 largest of ${fmt(occ.length)} shown; export covers the same rows`
        : 'Lightcast · export downloads these rows as CSV',
  };
}
