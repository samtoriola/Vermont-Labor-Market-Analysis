'use client';

import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { TIER_ORDER } from '@/lib/data';

const EMPTY = {
  tiers: [], // entry-credential tiers, multi-select
  families: [], // occupational families, multi-select — set by clicking a chart
  wage: 'all', // all | above | below (vs the living-wage benchmark)
  minJobs: 0, // 0 | 500 | 2000
  growth: 'all', // all | growing | shrinking (projected 2025-2030)
};

const Ctx = createContext(null);

export function useFilters() {
  return useContext(Ctx);
}

/**
 * Cross-filter state, shared by every tab.
 *
 * Deliberately global rather than per-tab: narrowing to sub-baccalaureate on one tab
 * and then switching tabs keeps the narrowing, so the tabs read as views of one
 * filtered dataset instead of eight unrelated pages. The active-filter bar makes the
 * carried state visible, which is the thing that otherwise confuses people.
 */
export function FilterProvider({ children, lwAnnual }) {
  const [f, setF] = useState(EMPTY);

  const reset = useCallback(() => setF(EMPTY), []);

  const toggle = useCallback((key, value) => {
    setF((p) => {
      const cur = p[key] || [];
      return {
        ...p,
        [key]: cur.includes(value) ? cur.filter((x) => x !== value) : [...cur, value],
      };
    });
  }, []);

  const set = useCallback((key, value) => setF((p) => ({ ...p, [key]: value })), []);

  const active = useMemo(() => {
    const out = [];
    (f.tiers || []).forEach((t) => out.push({ key: 'tiers', value: t, label: t }));
    (f.families || []).forEach((t) => out.push({ key: 'families', value: t, label: t }));
    if (f.wage !== 'all') {
      out.push({
        key: 'wage',
        value: 'all',
        label: f.wage === 'above' ? 'At/above living wage' : 'Below living wage',
      });
    }
    if (f.minJobs > 0) {
      out.push({ key: 'minJobs', value: 0, label: f.minJobs.toLocaleString() + '+ jobs' });
    }
    if (f.growth !== 'all') {
      out.push({
        key: 'growth',
        value: 'all',
        label: f.growth === 'growing' ? 'Projected growth' : 'Projected decline',
      });
    }
    return out;
  }, [f]);

  /** Apply the active filters to an occupation list. */
  const apply = useCallback(
    (occ) =>
      occ.filter((o) => {
        if (f.tiers.length && !f.tiers.includes(o.t)) return false;
        if (f.families.length && !f.families.includes(o.f)) return false;
        if (f.wage === 'above' && !(o.m && o.m >= lwAnnual)) return false;
        if (f.wage === 'below' && !(o.m && o.m < lwAnnual)) return false;
        if (f.minJobs && o.j < f.minJobs) return false;
        if (f.growth === 'growing' && !(o.g > 0)) return false;
        if (f.growth === 'shrinking' && !(o.g < 0)) return false;
        return true;
      }),
    [f, lwAnnual]
  );

  const value = useMemo(
    () => ({ f, setF, set, toggle, reset, active, apply, TIER_ORDER }),
    [f, set, toggle, reset, active, apply]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
