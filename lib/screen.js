/**
 * The opportunity screen: which Vermont occupations VSCS could act on.
 *
 * Every other tab answers what is true. This one answers what is actionable, which
 * needs a stated definition rather than a ranking. An occupation qualifies when it
 * clears four tests at once:
 *
 *   demand       enough annual openings to be worth a program
 *   pay          at or above the self-sufficiency benchmark the reader has chosen
 *   reachable    asks for a credential VSCS actually awards
 *   not obvious  excludes the occupations everyone already names, optionally
 *
 * It then reports how much VSCS already supplies, and whether the occupation shows
 * movement worth acting on.
 *
 * One methodological point that changes results. The "dynamic" tests are ranked WITHIN
 * each credential tier, never across the whole set. Median postings run about 65 per
 * 100 jobs at high school against 161 at bachelor's, because trades are not advertised
 * online at white-collar rates. A single threshold reads as a demand test and acts as
 * a credential filter: it removes exactly the sub-baccalaureate occupations VSCS is
 * best placed to serve.
 *
 * Nothing here recommends an action. A row is a candidate for investigation, and the
 * scope of work is explicit that this analysis does not by itself decide a program.
 */
import { LC, SOW } from './data';

export const SCREEN_TIERS = ['Sub-baccalaureate', "Bachelor's"];

/** Pipeline labels, in the order they should read. */
export const SUPPLY = {
  none: 'No VSCS pipeline',
  thin: 'Thin pipeline',
  established: 'Established pipeline',
};

function median(xs) {
  const v = xs.filter((x) => Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return 0;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

export function opportunityScreen({
  lwAnnual,
  minOpen = 50,
  tiers = SCREEN_TIERS,
  excludeObvious = true,
  thinRatio = 0.08,
  growthFloor = 3,
}) {
  const obvious = new Set(excludeObvious ? LC.topOcc.slice(0, 25).map((r) => r.soc) : []);
  const bySoc = (SOW.vscs && SOW.vscs.bySoc) || {};

  const base = LC.allOcc.filter(
    (o) =>
      o.m &&
      o.m >= lwAnnual &&
      o.o &&
      o.o >= minOpen &&
      tiers.includes(o.t) &&
      !obvious.has(o.s)
  );

  // Thresholds computed inside each tier, for the reason in the header comment.
  const norms = {};
  tiers.forEach((t) => {
    const w = base.filter((o) => o.t === t && o.j);
    norms[t] = {
      op: median(w.map((o) => (o.o / o.j) * 100)),
      post: median(w.map((o) => (o.p / o.j) * 100)),
    };
  });

  return base
    .map((o) => {
      const n = norms[o.t] || { op: 0, post: 0 };
      const opRate = o.j ? (o.o / o.j) * 100 : 0;
      const postRate = o.j ? (o.p / o.j) * 100 : 0;
      const signals = [
        opRate > n.op ? 'openings' : null,
        postRate > n.post ? 'postings' : null,
        (o.g || 0) > growthFloor ? 'growth' : null,
      ].filter(Boolean);

      const sup = bySoc[o.s] || {};
      const linked = sup.linked || 0;
      const ratio = sup.ratio === undefined ? null : sup.ratio;
      const supply =
        linked === 0 ? SUPPLY.none : ratio !== null && ratio < thinRatio ? SUPPLY.thin : SUPPLY.established;

      return {
        ...o,
        opRate,
        postRate,
        linked,
        ratio,
        supply,
        signals,
        nSignals: signals.length,
        // Evidence is incomplete where a figure the screen leans on was suppressed.
        incomplete: o.g === null || o.g === undefined || o.turn === null || o.turn === undefined,
      };
    })
    .sort((a, b) => b.o - a.o);
}

/** Columns for the screen table, shared with its export. */
export function screenCols() {
  return [
    { k: 'n', label: 'Occupation', kind: 'text', get: (r) => r.n },
    { k: 'o', label: 'Openings /yr', kind: 'num', get: (r) => r.o },
    { k: 'j', label: 'Jobs', kind: 'num', get: (r) => r.j },
    { k: 'g', label: 'Projected 25–30', kind: 'pct', get: (r) => r.g },
    { k: 'm', label: 'Median', kind: 'money', get: (r) => r.m },
    { k: 'linked', label: 'VSCS completions', kind: 'num1', get: (r) => r.linked },
    { k: 'supply', label: 'Pipeline', kind: 'text', get: (r) => r.supply },
    { k: 'nSignals', label: 'Signals', kind: 'num', get: (r) => r.nSignals },
    { k: 't', label: 'Entry credential', kind: 'text', get: (r) => r.t },
  ];
}
