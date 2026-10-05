/**
 * Computed answers to "so what" -- one line per panel, generated from the same data
 * the chart reads so they cannot go stale when the pipeline is re-run.
 *
 * Every rule returns one of three things, and the difference matters:
 *
 *   { text, muted: false }  a comparison cleared its margin -- the finding
 *   { text, muted: true }   the rule ran and found nothing notable, and says so
 *   null                    the rule could not run at all, so the panel stays blank
 *
 * The middle state is the point. A line that simply vanishes when a reader changes
 * the benchmark reads as a bug; saying "no material difference at this benchmark" is
 * itself informative, because at the minimum wage every job clears it. Keeping the
 * third state separate means a missing figure never masquerades as a null result.
 *
 * Rules run over the full population, never the rows a panel happens to display. A
 * rule written against a top-15 slice reports the truncation and it reads exactly like
 * a finding.
 *
 * Nothing here prescribes an action: the scope of work is explicit that the analysis
 * does not, by itself, say whether a program should be created, expanded or cut.
 */
import { fmt, money } from './format';

const found = (text) => ({ text, muted: false });
const none = (text) => ({ text, muted: true });

/* ---------- against a benchmark ---------- */

/**
 * Wage quality across occupation size, measured against the living wage. Depends on
 * the household the reader has selected, so it is computed in the view rather than
 * baked into the data.
 */
export function sizeWageGap(sizeTiers, lwKey, minGap = 10) {
  const big = sizeTiers.filter((r) => r.s.startsWith('Large'))[0];
  const small = sizeTiers.filter((r) => r.s.startsWith('Smaller'))[0];
  if (!big || !small) return null;
  const a = big.above[lwKey];
  const b = small.above[lwKey];
  if (a === null || b === null || a === undefined || b === undefined) return null;

  if (Math.abs(b - a) < minGap) {
    return none(
      `No material difference at this benchmark — ${a.toFixed(0)}% of jobs in the ` +
      `largest occupations clear it, against ${b.toFixed(0)}% in the smallest.`
    );
  }
  return found(
    `The ${fmt(big.nocc)} occupations with 2,000+ jobs hold ${big.share.toFixed(0)}% of ` +
    `employment, and ${a.toFixed(0)}% of those jobs clear the living wage — against ` +
    `${b.toFixed(0)}% among the smallest occupations.`
  );
}

/* ---------- against a comparator ---------- */

/** Vermont pay against the nation, on the same OEWS basis. */
export function vsNation(areas, minPct = 5) {
  const vt = areas.filter((a) => a.label === 'Vermont')[0];
  const us = areas.filter((a) => a.label === 'United States')[0];
  if (!vt || !us || !us.med) return null;

  const gap = (vt.med / us.med - 1) * 100;
  if (Math.abs(gap) < minPct) {
    return none(
      `Vermont tracks the nation here — an employment-weighted median of ` +
      `${money(vt.med)} against ${money(us.med)}, within ${Math.abs(gap).toFixed(0)}%.`
    );
  }
  return found(
    `Vermont's employment-weighted median is ${money(vt.med)} against ${money(us.med)} ` +
    `nationally — ${Math.abs(gap).toFixed(0)}% ${gap > 0 ? 'above' : 'below'} the ` +
    `national figure.`
  );
}

/* ---------- against itself ---------- */

/** How far the average sits above the typical worker, within one earnings distribution. */
export function meanMedianGap(area, minPct = 15) {
  if (!area || !area.med || !area.avg) return null;

  const gap = (area.avg / area.med - 1) * 100;
  if (gap < minPct) {
    return none(
      `Average and median sit close together here — ${money(area.avg)} against ` +
      `${money(area.med)} — so no small group is pulling the average far from typical.`
    );
  }
  return found(
    `Half of these workers earn under ${money(area.med)}, while the average is ` +
    `${money(area.avg)} — ${gap.toFixed(0)}% higher, the distance a thin top tail opens up.`
  );
}

/** Whether employment is concentrated in a couple of sectors. */
export function topConcentration(sectors, total, topN = 2, nextN = 5) {
  const s = sectors.slice().sort((a, b) => b.j - a.j);
  if (s.length < topN + nextN || !total) return null;

  const top = s.slice(0, topN).reduce((a, r) => a + r.j, 0);
  const next = s.slice(topN, topN + nextN).reduce((a, r) => a + r.j, 0);
  const share = (top / total) * 100;

  if (top <= next) {
    return none(
      `Employment is spread rather than concentrated — the two largest sectors hold ` +
      `${share.toFixed(0)}% of jobs between them, less than the next ${nextN} combined.`
    );
  }
  return found(
    `${s[0].s} and ${s[1].s} hold ${share.toFixed(0)}% of Vermont jobs between them — ` +
    `more than the next ${nextN} sectors combined.`
  );
}
