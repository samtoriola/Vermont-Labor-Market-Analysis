/**
 * How much of the work pays below a benchmark.
 *
 * WHAT THIS REPLACES
 * ------------------
 * "Share above the living wage" used to compare an occupation's median with the
 * benchmark and then count all of that occupation's jobs on whichever side the
 * median fell. A median a dollar over put 100% of its jobs above; a dollar under
 * put 0% there. Half the people in each are on the wrong side of that line.
 *
 * Statewide the errors mostly cancel -- 42.5% on the median rule against 41.1%
 * read off the distributions -- which is why it survived. By occupation group
 * they do not, and the group chart is what people read:
 *
 *   Installation & Repair      3.3% below on the median rule, 22.6% on the ladders
 *   Office & Admin Support    63.7%                           49.2%
 *   Arts, Design & Media      14.2%                           29.0%
 *   Building & Grounds        90.9%                           79.2%
 *
 * So the benchmark's position is interpolated along each occupation's own p10-p90
 * ladder, which data/percentiles.json already carries for every priced occupation,
 * and the result weighted by employment. No new data, a different arithmetic.
 *
 * WHY IT IS COMPUTED IN THE BROWSER
 * ---------------------------------
 * Precomputing one number per row per benchmark would freeze it. Done here, a
 * group's answer follows the household the reader picks AND the filters they set,
 * because both are just a different list of occupations handed to the same sum.
 * The counties are the one exception -- their answer needs pay ladders per county,
 * which only exist in the Core LMI county slice -- so those are built once by
 * scripts/build_wagefloor.py and read from data/wagefloor.json.
 */
import { LC, PCT } from './data';

const PTS = [
  [10, 'p10'],
  [25, 'p25'],
  [50, 'p50'],
  [75, 'p75'],
  [90, 'p90'],
];

/** [[pay, quantile]] for one occupation, lowest first, or null if unusable. */
export function ladder(box) {
  if (!box) return null;
  const xs = [];
  PTS.forEach(([q, k]) => {
    if (box[k]) xs.push([box[k], q]);
  });
  return xs.length >= 2 ? xs : null;
}

/**
 * Percent of one occupation's jobs paying under `floor`.
 *
 * Clamped outside p10 and p90 rather than extrapolated: out there the ladder says
 * nothing, and a straight line drawn past its last point would invent a figure
 * instead of reading one. An occupation whose p90 is still under the benchmark is
 * 100% below, which is the honest reading of "every rung we can see falls short".
 */
export function shareBelow(box, floor) {
  const xs = ladder(box);
  if (!xs) return null;
  if (floor <= xs[0][0]) return 0;
  if (floor >= xs[xs.length - 1][0]) return 100;
  for (let i = 0; i < xs.length - 1; i += 1) {
    const [v0, q0] = xs[i];
    const [v1, q1] = xs[i + 1];
    if (v0 <= floor && floor <= v1) {
      const t = v1 === v0 ? 0 : (floor - v0) / (v1 - v0);
      return q0 + t * (q1 - q0);
    }
  }
  return null;
}

/** The ladder an occupation row is measured on, by SOC code. */
export function occBox(o) {
  return PCT.occ[o.s || o.soc] || null;
}

/** Does this occupation carry a usable ladder? Decides the denominator. */
export function priced(o) {
  return !!ladder(occBox(o));
}

/**
 * Roll a list of occupations up into one answer.
 *
 * `jobs` is the employment the answer actually rests on -- occupations without a
 * usable ladder are out of the numerator and the denominator both, rather than
 * silently counted as clearing the benchmark.
 */
export function rollUp(occ, floor) {
  let jobs = 0;
  let below = 0;
  let nocc = 0;
  let worst = null;
  occ.forEach((o) => {
    const s = shareBelow(occBox(o), floor);
    if (s === null) return;
    const j = o.j || 0;
    jobs += j;
    below += (j * s) / 100;
    nocc += 1;
    // The occupation putting the most people under the benchmark, which is what a
    // reader asks next and is rarely the one with the highest share.
    if (!worst || (j * s) / 100 > worst.n) worst = { o, n: (j * s) / 100, s };
  });
  if (!jobs) return null;
  return {
    jobs: Math.round(jobs),
    belowN: Math.round(below),
    below: (below / jobs) * 100,
    nocc,
    worst,
  };
}

/** Group a pool of occupations by one of its keys, then roll each group up. */
export function rollUpBy(occ, keyOf, floor) {
  const by = new Map();
  occ.forEach((o) => {
    const k = keyOf(o);
    if (k === null || k === undefined || k === '') return;
    if (!by.has(k)) by.set(k, []);
    by.get(k).push(o);
  });
  const out = [];
  by.forEach((rows, k) => {
    const r = rollUp(rows, floor);
    if (r) out.push({ f: k, occ: rows, ...r });
  });
  return out;
}

/**
 * The median rule's answer for the same rows, so the tab can say what changed.
 * Kept here beside the measure that replaced it rather than in the view, because
 * the comparison is the argument for the replacement.
 */
export function medianRuleBelow(occ, floor) {
  let jobs = 0;
  let below = 0;
  occ.forEach((o) => {
    if (!o.m) return;
    jobs += o.j || 0;
    if (o.m < floor) below += o.j || 0;
  });
  return jobs ? (below / jobs) * 100 : null;
}

/** Every priced occupation, the pool every row option is cut from. */
export function pricedPool(pool) {
  return (pool || LC.allOcc).filter(priced);
}
