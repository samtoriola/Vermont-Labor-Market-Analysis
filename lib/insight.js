/**
 * Computed answers to "so what" -- one line per panel, generated from the same data
 * the chart reads so they cannot go stale when the pipeline is re-run.
 *
 * Two rules govern everything here:
 *
 * 1. Every function returns null when its comparison does not clear a stated margin.
 *    A panel with nothing worth saying says nothing. Without that gate every chart
 *    manufactures significance and a reader stops believing any of it.
 *
 * 2. Rules run over the full population, never the rows a panel happens to display.
 *    A rule written against a top-15 slice reports the truncation and it reads exactly
 *    like a finding.
 *
 * Nothing here prescribes an action: the scope of work is explicit that the analysis
 * does not, by itself, say whether a program should be created, expanded or cut.
 */
import { fmt, money } from './format';

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
  if (a === null || b === null || Math.abs(b - a) < minGap) return null;
  return (
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
  if (Math.abs(gap) < minPct) return null;
  const dir = gap > 0 ? 'above' : 'below';
  return (
    `Vermont's employment-weighted median is ${money(vt.med)} against ${money(us.med)} ` +
    `nationally — ${Math.abs(gap).toFixed(0)}% ${dir} the national figure.`
  );
}

/* ---------- against itself ---------- */

/** How far the average sits above the typical worker, within one earnings distribution. */
export function meanMedianGap(area, minPct = 15) {
  if (!area || !area.med || !area.avg) return null;
  const gap = (area.avg / area.med - 1) * 100;
  if (gap < minPct) return null;
  return (
    `Half of these workers earn under ${money(area.med)}, while the average is ` +
    `${money(area.avg)} — ${gap.toFixed(0)}% higher, the distance a thin top tail opens up.`
  );
}

/**
 * Whether employment is concentrated in a couple of sectors. Vermont's is not, so this
 * returns null today -- kept because it is the rule that demonstrates the gate working,
 * and because a future data refresh could change the answer.
 */
export function topConcentration(sectors, total, topN = 2, nextN = 5) {
  const s = sectors.slice().sort((a, b) => b.j - a.j);
  if (s.length < topN + nextN || !total) return null;
  const top = s.slice(0, topN).reduce((a, r) => a + r.j, 0);
  const next = s.slice(topN, topN + nextN).reduce((a, r) => a + r.j, 0);
  if (top <= next) return null;
  return (
    `${s[0].s} and ${s[1].s} hold ${((top / total) * 100).toFixed(0)}% of Vermont jobs ` +
    `between them — more than the next ${nextN} sectors combined.`
  );
}
