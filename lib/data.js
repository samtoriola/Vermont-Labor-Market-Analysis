// Static data, imported at build time. Regenerate with the Python build scripts
// (build.py, build_pct.py, build_sow.py, cps_vt_extract.py) and re-run mk_app_data.py.
import cps from '@/data/cps.json';
import lightcast from '@/data/lightcast.json';
import percentiles from '@/data/percentiles.json';
import sow from '@/data/sow.json';

export const DATA = cps;          // CPS microdata aggregates, Vermont 2021-2025
export const LC = lightcast;      // Lightcast occupation / industry / postings
export const PCT = percentiles;   // Wage percentile distributions
export const SOW = sow;           // SOW Q5-Q8: opportunity index, VSCS, regions

export const TOTJ = LC.totalJobs;

export const TIER_ORDER = [
  'No formal credential',
  'High school',
  'Sub-baccalaureate',
  "Bachelor's",
  'Graduate / professional',
];

// Categorical series slots. Order is the CVD-safety mechanism -- do not cycle or reorder.
export const SER = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6'];

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

// CPS attainment shares, used for the requirement-vs-attainment contrast.
export function cpsSubBacc() {
  return DATA.pathways
    .filter((p) => p.p === 'Associate degree (sub-baccalaureate)' || p.p === 'Some college, no degree')
    .reduce((a, p) => a + p.sh, 0);
}

export function cpsHsOrLess() {
  return DATA.pathways
    .filter((p) => p.p === 'High school diploma' || p.p === 'Less than high school')
    .reduce((a, p) => a + p.sh, 0);
}
