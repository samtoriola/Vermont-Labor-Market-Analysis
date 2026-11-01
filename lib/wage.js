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
  const r = rollUpOn(occ, floor, (o) => o.j || 0);
  return r && { ...r, jobs: r.total };
}

/**
 * The same roll-up over any weight, not only employment.
 *
 * Weighting by jobs answers "how much of the work pays below the benchmark",
 * which is the question on every other tab. Weighting by openings answers "how
 * much of a year's HIRING is in work that pays below it", which is a different
 * question and the one a person leaving a credential actually faces: an
 * occupation can hold a lot of jobs and almost never hire, or the reverse.
 *
 * The measure is identical -- the benchmark's position along each occupation's
 * own ladder -- so the two cannot disagree about an occupation, only about how
 * much that occupation counts.
 */
export function rollUpOn(occ, floor, weightOf) {
  let total = 0;
  let below = 0;
  let nocc = 0;
  let worst = null;
  occ.forEach((o) => {
    const s = shareBelow(occBox(o), floor);
    if (s === null) return;
    const w = weightOf(o) || 0;
    total += w;
    below += (w * s) / 100;
    nocc += 1;
    // The occupation putting the most people under the benchmark, which is what a
    // reader asks next and is rarely the one with the highest share.
    if (!worst || (w * s) / 100 > worst.n) worst = { o, n: (w * s) / 100, s };
  });
  if (!total) return null;
  return {
    total: Math.round(total),
    belowN: Math.round(below),
    below: (below / total) * 100,
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

/**
 * The real pay ladder for a set of occupations.
 *
 * WHY NOT THE PUBLISHED ONE
 * -------------------------
 * data/percentiles.json carries a ladder per occupation group and per credential
 * already, but those are the employment-weighted MEAN of their occupations'
 * percentiles. A mean of tenth percentiles is not the group's tenth percentile:
 * it averages away the spread BETWEEN occupations, which at a credential level is
 * most of the spread there is. The understatement reaches 44%:
 *
 *   Graduate / professional   2.52x p90/p10 published, 3.62x pooled
 *   Bachelor's                2.30x                    2.83x
 *   High school               1.81x                    2.09x
 *
 * The ordering survives, the magnitude does not, and a chart drawn to show how
 * wide the outcomes are is exactly the chart that cannot use it.
 *
 * HOW
 * ---
 * shareBelow() already answers "what share of this occupation's jobs sit under
 * $V". Summing it across the members weighted by employment gives the group's
 * share under $V, for any V. Each member's answer is linear in V between its own
 * published percentiles, so the pooled curve is piecewise linear with a kink only
 * where some member has one. Evaluating at exactly those points -- the union of
 * every member's p10 to p90 -- makes the interpolation between them exact, and a
 * grid fine enough to match it would be slower.
 */
const pooledCache = new Map();

export function pooledLadder(occ, cacheKey) {
  if (cacheKey && pooledCache.has(cacheKey)) return pooledCache.get(cacheKey);
  const members = [];
  let tot = 0;
  occ.forEach((o) => {
    const xs = ladder(occBox(o));
    const j = o.j || 0;
    if (xs && j > 0) {
      members.push([j, xs]);
      tot += j;
    }
  });
  if (!members.length) return null;

  // Every pay value at which some member's curve bends, which is every value the
  // pooled curve can bend at too.
  const knots = new Set();
  members.forEach(([, xs]) => xs.forEach(([v]) => knots.add(v)));
  const vs = [...knots].sort((a, b) => a - b);

  // [pay, share of the group's jobs below it], rising.
  const grid = [];
  vs.forEach((v) => {
    let s = 0;
    members.forEach(([j, xs]) => {
      let q = null;
      if (v <= xs[0][0]) q = 0;
      else if (v >= xs[xs.length - 1][0]) q = 100;
      else {
        for (let n = 0; n < xs.length - 1; n += 1) {
          const [v0, q0] = xs[n];
          const [v1, q1] = xs[n + 1];
          if (v0 <= v && v <= v1) {
            q = q0 + (v1 === v0 ? 0 : ((v - v0) / (v1 - v0)) * (q1 - q0));
            break;
          }
        }
      }
      s += (j * q) / 100;
    });
    grid.push([v, (s / tot) * 100]);
  });

  const out = {};
  PTS.forEach(([q, key]) => {
    let hit = null;
    for (let i = 0; i < grid.length - 1; i += 1) {
      const [v0, s0] = grid[i];
      const [v1, s1] = grid[i + 1];
      if (s0 <= q && q <= s1) {
        hit = v0 + (s1 === s0 ? 0 : ((q - s0) / (s1 - s0)) * (v1 - v0));
        break;
      }
    }
    out[key] = hit === null ? null : Math.round(hit);
  });
  out.jobs = Math.round(tot);
  out.nocc = members.length;
  if (cacheKey) pooledCache.set(cacheKey, out);
  return out;
}
