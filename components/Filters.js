'use client';

import { LC, TIER_ORDER } from '@/lib/data';
import { fmt } from '@/lib/format';
import { useFilters } from './FilterContext';

const WAGE = [
  ['all', 'All'],
  ['above', 'At/above living wage'],
  ['below', 'Below living wage'],
];
const SIZE = [
  [0, 'Any size'],
  [500, '500+ jobs'],
  [2000, '2,000+ jobs'],
];
const GROWTH = [
  ['all', 'All'],
  ['growing', 'Projected growth'],
  ['shrinking', 'Projected decline'],
];

/**
 * Cross-filter bar. Rendered on every data tab and driven by shared state, so a
 * narrowing set on one tab persists across the others.
 */
export default function Filters({ shown, total, note, showFamilies = false }) {
  const { f, set, toggle, reset, active } = useFilters();
  const families = LC.families.map((r) => r.f);

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
              aria-pressed={f.tiers.includes(t)}
              onClick={() => toggle('tiers', t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="fgroup">
        <span className="flab">Wage quality</span>
        <div className="chips">
          {WAGE.map(([v, l]) => (
            <button
              key={v}
              type="button"
              className="chip"
              aria-pressed={f.wage === v}
              onClick={() => set('wage', v)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="fgroup">
        <span className="flab">Minimum size</span>
        <div className="chips">
          {SIZE.map(([v, l]) => (
            <button
              key={v}
              type="button"
              className="chip"
              aria-pressed={f.minJobs === v}
              onClick={() => set('minJobs', v)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="fgroup">
        <span className="flab">Projected direction</span>
        <div className="chips">
          {GROWTH.map(([v, l]) => (
            <button
              key={v}
              type="button"
              className="chip"
              aria-pressed={f.growth === v}
              onClick={() => set('growth', v)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {showFamilies ? (
        <div className="fgroup fgroup-wide">
          <span className="flab">Occupational family</span>
          <div className="chips">
            {families.map((t) => (
              <button
                key={t}
                type="button"
                className="chip chip-sm"
                aria-pressed={f.families.includes(t)}
                onClick={() => toggle('families', t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="fcount">
        {shown !== undefined ? (
          <>
            <strong>{fmt(shown)}</strong> of {fmt(total)} occupations
            {note ? ` · ${note}` : ''}
          </>
        ) : null}
        {active.length ? (
          <>
            {' · '}
            <button type="button" className="freset" onClick={reset}>
              clear {active.length} filter{active.length > 1 ? 's' : ''}
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}

/** Compact strip showing which filters are carried onto this tab, each removable. */
export function ActiveFilters() {
  const { active, set, toggle, reset } = useFilters();
  if (!active.length) return null;
  return (
    <div className="activebar">
      <span className="flab">Filtering by</span>
      {active.map((a) => (
        <button
          key={a.key + a.label}
          type="button"
          className="chip chip-active"
          onClick={() => (Array.isArray(a.value) || a.key === 'tiers' || a.key === 'families'
            ? toggle(a.key, a.value)
            : set(a.key, a.value))}
          title="Remove this filter"
        >
          {a.label} <span aria-hidden="true">×</span>
        </button>
      ))}
      <button type="button" className="freset" onClick={reset}>
        clear all
      </button>
    </div>
  );
}
