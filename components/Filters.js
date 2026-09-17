'use client';

import { TIER_ORDER } from '@/lib/data';
import { fmt } from '@/lib/format';

const WAGE_OPTS = [
  ['all', 'All'],
  ['above', 'At or above living wage'],
  ['below', 'Below living wage'],
];

const SIZE_OPTS = [
  [0, 'All sizes'],
  [500, '500+ jobs'],
  [2000, '2,000+ jobs'],
];

/**
 * Filter bar for the occupation-level views. Credential tiers are multi-select;
 * wage and size are single-select. Empty tiers means no tier restriction.
 */
export default function Filters({ f, setF, shown, total, note }) {
  function toggleTier(t) {
    const cur = f.tiers || [];
    setF({ ...f, tiers: cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t] });
  }

  const dirty = (f.tiers && f.tiers.length) || f.wage !== 'all' || f.minJobs > 0;

  return (
    <div className="filterbar">
      <div className="fgroup">
        <span className="flab">Entry credential</span>
        <div className="chips">
          {TIER_ORDER.map((t) => (
            <button
              key={t}
              type="button"
              className="chip"
              aria-pressed={(f.tiers || []).includes(t)}
              onClick={() => toggleTier(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="fgroup">
        <span className="flab">Wage quality</span>
        <div className="chips">
          {WAGE_OPTS.map(([v, l]) => (
            <button
              key={v}
              type="button"
              className="chip"
              aria-pressed={f.wage === v}
              onClick={() => setF({ ...f, wage: v })}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="fgroup">
        <span className="flab">Minimum size</span>
        <div className="chips">
          {SIZE_OPTS.map(([v, l]) => (
            <button
              key={v}
              type="button"
              className="chip"
              aria-pressed={f.minJobs === v}
              onClick={() => setF({ ...f, minJobs: v })}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="fcount">
        {fmt(shown)} of {fmt(total)} occupations
        {note ? ` · ${note}` : ''}
        {dirty ? (
          <>
            {' · '}
            <button
              type="button"
              className="freset"
              onClick={() => setF({ ...f, tiers: [], wage: 'all', minJobs: 0 })}
            >
              reset
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}
