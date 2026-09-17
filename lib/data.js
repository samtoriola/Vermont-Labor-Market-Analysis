// Static data, imported at build time. Regenerate via scripts/ then re-run
// scripts/mk_app_data.py. Nothing here queries anything at runtime.
import cps from '@/data/cps.json';
import lightcast from '@/data/lightcast.json';
import percentiles from '@/data/percentiles.json';
import sow from '@/data/sow.json';
import vtmap from '@/data/vt-map.json';

export const DATA = cps; // CPS microdata aggregates, Vermont 2021-2025
export const LC = lightcast; // Lightcast occupation / industry / postings
export const PCT = percentiles; // Wage percentile distributions
export const SOW = sow; // Opportunity index, VSCS alignment, county figures
export const MAP = vtmap; // Simplified Vermont county SVG paths

export const TOTJ = LC.totalJobs;

export const TIER_ORDER = [
  'No formal credential',
  'High school',
  'Sub-baccalaureate',
  "Bachelor's",
  'Graduate / professional',
];

export const SIZE_ORDER = ['Large (2,000+)', 'Medium (500-2,000)', 'Smaller (<500)'];

export {
  SERIES,
  SERIES_HEX,
  ORDINAL,
  ORDINAL_HEX,
  BRAND,
  GOOD,
  BAD,
  GOOD_HEX,
  BAD_HEX,
  rampStep,
  rampHex,
} from './brand';

export const DEFAULT_LW = LC.defaultLW;

export function lwHourly(key) {
  return LC.livingWage[key];
}

export function lwAnnual(key) {
  return LC.livingWage[key] * LC.hours;
}

export function tierRow(t) {
  return LC.tiers.filter((r) => r.t === t)[0];
}

export function cpsSubBacc() {
  return DATA.pathways
    .filter(
      (p) => p.p === 'Associate degree (sub-baccalaureate)' || p.p === 'Some college, no degree'
    )
    .reduce((a, p) => a + p.sh, 0);
}

export function cpsHsOrLess() {
  return DATA.pathways
    .filter((p) => p.p === 'High school diploma' || p.p === 'Less than high school')
    .reduce((a, p) => a + p.sh, 0);
}

/** Occupations passing the active filters. */
export function filterOcc(occ, f) {
  if (!f) return occ;
  return occ.filter((o) => {
    if (f.tiers && f.tiers.length && !f.tiers.includes(o.t)) return false;
    if (f.wage === 'above' && !(o.m && o.m >= f.lwAnnual)) return false;
    if (f.wage === 'below' && !(o.m && o.m < f.lwAnnual)) return false;
    if (f.minJobs && o.j < f.minJobs) return false;
    return true;
  });
}

/** Detailed occupations belonging to one family, for drill-down. */
export function occByFamily(fam) {
  return LC.allOcc.filter((o) => o.f === fam).sort((a, b) => b.j - a.j);
}

/** Detailed occupations at one credential tier, for drill-down. */
export function occByTier(tier) {
  return LC.allOcc.filter((o) => o.t === tier).sort((a, b) => b.j - a.j);
}
