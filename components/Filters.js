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

/* What each option actually asks of a row, so the bar can tell which of them any
   row in this panel could satisfy. */
const MATCH = {
  tiers: (o, v) => o.t === v,
  families: (o, v) => o.f === v,
  wage: (o, v, lw) => (v === 'above' ? o.m >= lw : o.m && o.m < lw),
  minJobs: (o, v) => o.j >= v,
  growth: (o, v) => (v === 'growing' ? o.g > 0 : o.g < 0),
};

/**
 * Cross-filter bar. Rendered on every data tab and driven by shared state, so a
 * narrowing set on one tab persists across the others.
 *
 * `pool` is the list the panel draws from. Every option is checked against it and
 * the ones nothing could match are left out: on the highest-scoring occupations
 * there is no such thing as one in projected decline, and a chip that silently
 * empties the chart is worse than no chip. An option already in use is always
 * shown, so a filter carried from another tab can still be switched off here.
 */
export default function Filters({ shown, total, note, pool, showFamilies = false }) {
  const { f, set, toggle, reset, active, lwAnnual } = useFilters();

  // No pool given: show everything, which is what the bar did before it could ask.
  const live = (key, v) =>
    !pool || !pool.length || v === 'all' || v === 0
      ? true
      : pool.some((o) => MATCH[key](o, v, lwAnnual));

  const inUse = (key, v) =>
    key === 'tiers' || key === 'families' ? f[key].includes(v) : f[key] === v;

  const usable = (key, opts) => opts.filter(([v]) => live(key, v) || inUse(key, v));

  const tiers = usable('tiers', TIER_ORDER.map((t) => [t, t]));
  const wage = usable('wage', WAGE);
  const size = usable('minJobs', SIZE);
  const growth = usable('growth', GROWTH);
  const families = usable('families', LC.families.map((r) => [r.f, r.f]));

  // A group offering one choice is not a choice.
  const many = (opts) => opts.filter(([v]) => v !== 'all' && v !== 0).length > 0 && opts.length > 1;

  return (
    <div className="filterbar">
      {tiers.length > 1 ? (
        <div className="fgroup">
          <span className="flab">Entry credential</span>
          <div className="chips">
            {tiers.map(([t]) => (
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
      ) : null}

      {many(wage) ? (
        <div className="fgroup">
          <span className="flab">Pay</span>
          <div className="chips">
            {wage.map(([v, l]) => (
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
      ) : null}

      {many(size) ? (
        <div className="fgroup">
          <span className="flab">Size</span>
          <div className="chips">
            {size.map(([v, l]) => (
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
      ) : null}

      {many(growth) ? (
        <div className="fgroup">
          <span className="flab">Outlook</span>
          <div className="chips">
            {growth.map(([v, l]) => (
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
      ) : null}

      {showFamilies && families.length > 1 ? (
        <div className="fgroup fgroup-wide">
          <span className="flab">Occupation group</span>
          <div className="chips">
            {families.map(([t]) => (
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
