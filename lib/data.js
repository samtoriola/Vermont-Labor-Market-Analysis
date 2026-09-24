// Static data, imported at build time. Regenerate via scripts/ then re-run
// scripts/mk_app_data.py. Nothing here queries anything at runtime.
import cps from '@/data/cps.json';
import lightcast from '@/data/lightcast.json';
import percentiles from '@/data/percentiles.json';
import sow from '@/data/sow.json';
import vtmap from '@/data/vt-map.json';
import compare from '@/data/compare.json';
import people from '@/data/people.json';

export const DATA = cps; // CPS microdata aggregates, Vermont 2021-2025
export const LC = lightcast; // Lightcast occupation / industry / postings
export const PCT = percentiles; // Wage percentile distributions
export const SOW = sow; // Opportunity index, VSCS alignment, county figures
export const MAP = vtmap; // Simplified Vermont county SVG paths
export const COMPARE = compare; // OEWS wage distributions: Vermont, New Hampshire, US
export const PEOPLE = people; // ACS person-level earnings, one record per respondent

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

/**
 * Employment-weighted mean and median of a set of occupation medians. The mean is
 * the line the dot charts draw as "average"; the median is the wage that splits
 * employment in half. They differ whenever a few well-paid occupations sit far
 * above the bulk, which is the gap the dot charts exist to show.
 */
export function wageStats(occ) {
  const priced = occ.filter((o) => o.m > 0 && o.j > 0);
  if (!priced.length) return { avg: 0, med: 0, jobs: 0, n: 0 };
  const jobs = priced.reduce((a, o) => a + o.j, 0);
  const avg = priced.reduce((a, o) => a + o.m * o.j, 0) / jobs;
  const sorted = priced.slice().sort((a, b) => a.m - b.m);
  let cum = 0;
  let med = sorted[sorted.length - 1].m;
  for (const o of sorted) {
    cum += o.j;
    if (cum >= jobs / 2) {
      med = o.m;
      break;
    }
  }
  return { avg, med, jobs, n: priced.length };
}

/** Occupation records reshaped as chart dots: value is pay, size is employment. */
export function occDots(occ) {
  return occ
    .filter((o) => o.m > 0 && o.j > 0)
    .map((o) => ({ v: o.m, e: o.j, n: o.n, s: o.s, t: o.t, f: o.f, g: o.g, turn: o.turn }));
}

/** The size band an occupation falls in, matching SIZE_ORDER. */
export function sizeBand(o) {
  if (o.j >= 2000) return SIZE_ORDER[0];
  if (o.j >= 500) return SIZE_ORDER[1];
  return SIZE_ORDER[2];
}

/** Detailed occupations in one size band, for drill-down. */
export function occBySize(band) {
  return LC.allOcc.filter((o) => sizeBand(o) === band).sort((a, b) => b.j - a.j);
}

/** A reference column built from the OEWS comparison file. */
export function compareCol(label) {
  const a = COMPARE.areas.filter((x) => x.label === label)[0];
  if (!a) return null;
  return {
    label: a.label,
    sub: a.src,
    ref: true,
    avg: a.avg,
    med: a.med,
    dots: a.dots.map((d) => ({ v: d.v, e: d.e, n: d.n, s: d.s, lo: d.lo, hi: d.hi })),
  };
}
