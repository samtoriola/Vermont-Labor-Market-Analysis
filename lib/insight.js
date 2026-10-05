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

/* ------------------------------------------------------------------ *
 * Rollout rules. Same three states throughout; each one short.
 * ------------------------------------------------------------------ */

const pts = (n) => {
  const v = Math.abs(n);
  return `${v % 1 < 0.05 ? v.toFixed(0) : v.toFixed(1)} points`;
};

/** Jobs asking for a credential against workers holding one. */
export function requirementsGap(reqPct, holdPct, minGap = 5) {
  if (reqPct === null || holdPct === null) return null;
  const g = holdPct - reqPct;
  if (Math.abs(g) < minGap) {
    return none(`Requirements and attainment are close here, within ${pts(g)}.`);
  }
  return found(
    `${holdPct.toFixed(1)}% of workers hold a bachelor's or higher while ` +
    `${reqPct.toFixed(1)}% of jobs ask for one — a gap of ${pts(g)}.`
  );
}

/** How much of employment the largest few families hold. */
export function familyConcentration(fams, total, topN = 3, minShare = 30) {
  if (!fams.length || !total) return null;
  const s = fams.slice().sort((a, b) => b.jobs - a.jobs);
  const sh = (s.slice(0, topN).reduce((a, r) => a + r.jobs, 0) / total) * 100;
  if (sh < minShare) {
    return none(`No family dominates: the largest ${topN} hold ${sh.toFixed(0)}% of jobs.`);
  }
  return found(
    `The largest ${topN} families hold ${sh.toFixed(0)}% of Vermont jobs between them.`
  );
}

/** Spread in the BA+ requirement across families. */
export function credentialSpread(fams, minSpread = 30) {
  const v = fams
    .map((r) => {
      const tot = Object.values(r.tiers || {}).reduce((a, x) => a + x, 0);
      if (!tot) return null;
      const ba = (r.tiers["Bachelor's"] || 0) + (r.tiers['Graduate / professional'] || 0);
      return { f: r.f, pc: (ba / tot) * 100 };
    })
    .filter(Boolean)
    .sort((a, b) => b.pc - a.pc);
  if (v.length < 2) return null;
  const hi = v[0];
  const lo = v[v.length - 1];
  if (hi.pc - lo.pc < minSpread) return none('The BA+ requirement varies little across families.');
  return found(
    `The BA+ requirement runs from ${hi.pc.toFixed(0)}% of jobs in ${hi.f} to ` +
    `${lo.pc.toFixed(0)}% in ${lo.f}.`
  );
}

/** Median pay, largest tier against smallest. */
export function sizePayStep(pctSizeTiers, order, minPct = 10) {
  const big = pctSizeTiers[order[0]];
  const small = pctSizeTiers[order[2]];
  if (!big || !small) return null;
  const d = (small.p50 / big.p50 - 1) * 100;
  if (Math.abs(d) < minPct) return none('Median pay is similar across the three size tiers.');
  return found(
    `Smaller occupations pay a median of ${money(small.p50)} against ${money(big.p50)} ` +
    `in the largest — ${Math.abs(d).toFixed(0)}% ${d > 0 ? 'more' : 'less'}.`
  );
}

/** How much employment sits in the 25 largest occupations. */
export function topOccShare(topOcc, total, nAll, minShare = 20) {
  if (!topOcc.length || !total) return null;
  const sh = (topOcc.reduce((a, r) => a + r.j, 0) / total) * 100;
  if (sh < minShare) {
    return none(`The 25 largest occupations hold ${sh.toFixed(0)}% of employment.`);
  }
  return found(
    `These 25 occupations — ${((25 / nAll) * 100).toFixed(0)}% of the ${fmt(nAll)} in ` +
    `Vermont — hold ${sh.toFixed(0)}% of all employment.`
  );
}

/** Within the largest occupations, how often the average sits above the median. */
export function meanAboveMedian(rows, minShare = 60) {
  const w = rows.filter((r) => r.mu !== null && r.mu !== undefined && r.p50);
  if (w.length < 5) return null;
  const n = w.filter((r) => r.mu > r.p50).length;
  if ((n / w.length) * 100 < minShare) {
    return none(`The average sits above the median in ${n} of ${w.length} of these occupations.`);
  }
  return found(
    `In ${n} of ${w.length} of these occupations the average sits above the median — ` +
    `a top tail lifting it away from typical pay.`
  );
}

/** Where advertised demand diverges most from the employment base. */
export function demandDivergence(align, minGap = 3) {
  if (!align.length) return null;
  const s = align.slice().sort((a, b) => b.postSh - b.jobsSh - (a.postSh - a.jobsSh));
  const t = s[0];
  const g = t.postSh - t.jobsSh;
  if (g < minGap) return none('Postings track the employment base closely across families.');
  return found(
    `${t.f} draws ${t.postSh.toFixed(1)}% of postings on ${t.jobsSh.toFixed(1)}% of jobs — ` +
    `the widest gap between advertised demand and the employment base.`
  );
}

/** How many families are projected to shrink. */
export function growthSplit(fams, minShare = 10) {
  const w = fams.filter((r) => r.g5pct !== null && r.g5pct !== undefined);
  if (!w.length) return null;
  const n = w.filter((r) => r.g5pct < 0).length;
  if ((n / w.length) * 100 < minShare) {
    return none('Almost every family is projected to grow over the next five years.');
  }
  return found(`${n} of ${w.length} families are projected to shrink by 2030.`);
}

/** Observed change, how many families grew. */
export function observedSplit(fams, minShare = 10) {
  const w = fams.filter((r) => r.chgPct !== null && r.chgPct !== undefined);
  if (!w.length) return null;
  const n = w.filter((r) => r.chgPct < 0).length;
  if ((n / w.length) * 100 < minShare) return none('Nearly every family grew over 2021–2025.');
  return found(`${w.length - n} of ${w.length} families grew over 2021–2025; ${n} contracted.`);
}

/** The biggest step on the credential ladder. */
export function ladderStep(tiers, order, minPct = 15) {
  const v = order.map((k) => tiers.filter((r) => r.t === k)[0]).filter((r) => r && r.med);
  if (v.length < 2) return null;
  let best = null;
  for (let i = 1; i < v.length; i += 1) {
    const d = (v[i].med / v[i - 1].med - 1) * 100;
    if (!best || d > best.d) best = { d, from: v[i - 1], to: v[i] };
  }
  if (!best || best.d < minPct) return none('The rungs of the ladder are evenly spaced on pay.');
  return found(
    `The widest step is ${best.from.t} to ${best.to.t}: ${money(best.from.med)} to ` +
    `${money(best.to.med)}, ${best.d.toFixed(0)}% more.`
  );
}

/** The same step, measured on people rather than jobs. */
export function peopleLadderStep(byCred, minPct = 15) {
  const v = byCred.filter((c) => c.med);
  if (v.length < 2) return null;
  let best = null;
  for (let i = 1; i < v.length; i += 1) {
    const d = (v[i].med / v[i - 1].med - 1) * 100;
    if (!best || d > best.d) best = { d, from: v[i - 1], to: v[i] };
  }
  if (!best || best.d < minPct) return none('Earnings rise evenly across the credentials workers hold.');
  return found(
    `The widest step is ${best.from.label} to ${best.to.label}: ${money(best.from.med)} to ` +
    `${money(best.to.med)}, ${best.d.toFixed(0)}% more.`
  );
}

/** The biggest jump in the share of jobs clearing the living wage. */
export function livingWageJump(tiers, order, lwKey, minJump = 15) {
  const v = order.map((k) => tiers.filter((r) => r.t === k)[0]).filter(Boolean);
  let best = null;
  for (let i = 1; i < v.length; i += 1) {
    const a = v[i - 1].above[lwKey];
    const b = v[i].above[lwKey];
    if (a === null || b === null || a === undefined || b === undefined) continue;
    if (!best || b - a > best.d) best = { d: b - a, from: v[i - 1], to: v[i], a, b };
  }
  if (!best) return null;
  if (best.d < minJump) {
    return none('No single rung changes the odds of clearing the living wage at this benchmark.');
  }
  return found(
    `The biggest jump is ${best.from.t} to ${best.to.t}: ${best.a.toFixed(0)}% of jobs ` +
    `clearing the living wage, then ${best.b.toFixed(0)}%.`
  );
}

/** The largest single credential category inside the tiers. */
export function largestCategory(eduDetail, minShare = 20) {
  if (!eduDetail.length) return null;
  const s = eduDetail.slice().sort((a, b) => b.share - a.share)[0];
  if (s.share < minShare) return none('No single credential category dominates.');
  return found(
    `${s.e} alone covers ${s.share.toFixed(0)}% of Vermont jobs — the largest single category.`
  );
}

/** Which credential levels the highest-scoring occupations ask for. */
export function topScoreCredentials(top, n = 20, minShare = 50) {
  const w = top.slice(0, n);
  if (!w.length) return null;
  const ba = w.filter((r) => r.t === "Bachelor's" || r.t === 'Graduate / professional').length;
  if ((ba / w.length) * 100 < minShare) {
    return none('The highest-scoring occupations are spread across credential levels.');
  }
  return found(
    `${ba} of the top ${w.length} ask for a bachelor's or higher.`
  );
}

/** What VSCS actually awards. */
export function awardMix(byAward, total, minShare = 60) {
  if (byAward.length < 2 || !total) return null;
  const s = byAward.slice().sort((a, b) => b.c - a.c);
  const sh = ((s[0].c + s[1].c) / total) * 100;
  if (sh < minShare) return none('VSCS production is spread across award levels.');
  return found(`${s[0].a} and ${s[1].a} are ${sh.toFixed(0)}% of VSCS completions.`);
}

/** Families whose occupations draw no VSCS completions at all. */
export function familiesNoCompletions(byFamily, minOpen = 2000) {
  const z = byFamily.filter((r) => r.linked === 0);
  if (!z.length) return none('Every occupational family draws some VSCS completions.');
  const open = z.reduce((a, r) => a + r.open, 0);
  if (open < minOpen) {
    return none(`${z.length} families draw no VSCS completions, on ${fmt(open)} annual openings.`);
  }
  return found(
    `${z.length} of ${byFamily.length} families draw no VSCS completions at all, on ` +
    `${fmt(open)} annual openings between them.`
  );
}

/** Spread in attainment across counties. */
export function countySpread(regions, minSpread = 15) {
  if (regions.length < 2) return null;
  const s = regions.slice().sort((a, b) => b.ba - a.ba);
  const hi = s[0];
  const lo = s[s.length - 1];
  if (hi.ba - lo.ba < minSpread) return none('Attainment is fairly even across the 14 counties.');
  return found(
    `Bachelor's-or-higher runs from ${hi.ba}% in ${hi.c} to ${lo.ba}% in ${lo.c} — a ` +
    `${pts(hi.ba - lo.ba)} spread.`
  );
}

/** Income against the local cost floor, across counties. */
export function countyIncomeRange(regions, minSpread = 0.2) {
  if (regions.length < 2) return null;
  const s = regions.slice().sort((a, b) => b.incLw - a.incLw);
  const hi = s[0];
  const lo = s[s.length - 1];
  if (hi.incLw - lo.incLw < minSpread) {
    return none('Income against the local wage floor is similar across counties.');
  }
  return found(
    `Median income covers ${hi.incLw}× the local living wage in ${hi.c} but ` +
    `${lo.incLw}× in ${lo.c}.`
  );
}
