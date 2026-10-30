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
      `Vermont tracks the country here — a typical job paying ` +
      `${money(vt.med)} against ${money(us.med)}, within ${Math.abs(gap).toFixed(0)}%.`
    );
  }
  return found(
    `Vermont's typical job pays ${money(vt.med)} against ${money(us.med)} ` +
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

/* ---------- against what the reader chose to look at ---------- */

/*
 * The two rules below are the exception to the rule stated at the top of this
 * file, that findings are computed over the whole population and never over the
 * rows a panel happens to display.
 *
 * They earn it by naming the slice in the first clause -- "these 11 sectors",
 * never "Vermont" -- so a figure drawn from part of a population cannot be read
 * as one drawn from all of it. A reader who narrows a ranking to its top half is
 * asking a question about that half, and a read-out that answers a different
 * question is no more useful for having been computed from more rows.
 *
 * `shown` is a slice of `all` by reference, so membership is identity rather
 * than a match on name.
 */

/** A share reads better with a decimal only while it is small. */
const pct = (v) => (v < 10 ? v.toFixed(1) : v.toFixed(0));

/** What the rows on screen hold, as a share of all employment. */
export function sliceShare(shown, all, total, opt = {}) {
  const unit = opt.unit || 'sectors';
  const value = opt.value || ((r) => r.j);
  const name = opt.name || ((r) => r.s);
  if (!shown || !shown.length || !all.length || !total) return null;

  // Nothing is filtered out, so the question is the one about the population as
  // a whole: how concentrated it is.
  if (shown.length >= all.length) {
    const s = all.slice().sort((a, b) => value(b) - value(a));
    if (s.length < 7) return null;
    const two = value(s[0]) + value(s[1]);
    const next = s.slice(2, 7).reduce((a, r) => a + value(r), 0);
    const sh = pct((two / total) * 100);
    // Both branches carry the same figures and name the same two rows: which way
    // the comparison fell is the finding, and a reader should not have to lose
    // the names to learn that employment is spread rather than concentrated.
    const text =
      `All ${all.length} ${unit}, ${fmt(total)} jobs. ${name(s[0])} and ${name(s[1])} ` +
      `hold ${sh}% of them between them — ${two > next ? 'more' : 'less'} than the ` +
      `next five combined.`;
    return two > next ? found(text) : none(text);
  }

  const sum = shown.reduce((a, r) => a + value(r), 0);
  const rest = all.filter((r) => shown.indexOf(r) < 0);
  const restSum = rest.reduce((a, r) => a + value(r), 0);
  const big = rest.slice().sort((a, b) => value(b) - value(a))[0];

  // Holding most of the employment and holding what is left of it are two
  // different claims, so each takes the comparison that lands.
  if (sum >= restSum) {
    return found(
      `These ${shown.length} ${unit} hold ${pct((sum / total) * 100)}% of Vermont jobs — ` +
      `${fmt(sum)} of ${fmt(total)} — leaving ${pct((restSum / total) * 100)}% across ` +
      `the other ${rest.length}.`
    );
  }
  if (big && sum < value(big)) {
    return found(
      `These ${shown.length} ${unit} hold ${pct((sum / total) * 100)}% of Vermont jobs ` +
      `between them — ${fmt(sum)} in all, fewer than ${name(big)} on its own.`
    );
  }
  return found(
    `These ${shown.length} ${unit} hold ${pct((sum / total) * 100)}% of Vermont jobs ` +
    `between them — ${fmt(sum)} of ${fmt(total)}.`
  );
}

/**
 * How old the rows on screen are, against the rows they were chosen out of.
 *
 * Reported as the 55-and-over share and as a count, because the count is what a
 * programme gets sized against: it is the work that has to be replaced within
 * about a decade whatever else is true of it.
 */
export function sliceAge(shown, all, opt = {}) {
  const unit = opt.unit || 'sectors';
  const name = opt.name || ((x) => x.row.s);
  const age = opt.age || ((x) => x.a);
  if (!shown || !shown.length || !all.length) return null;

  const roll = (rows) =>
    rows.reduce(
      (acc, x) => {
        const a = age(x);
        if (a && a.total) {
          acc.t += a.total;
          acc.o += a.o55 * a.total;
        }
        return acc;
      },
      { t: 0, o: 0 }
    );

  const here = roll(shown);
  if (!here.t) return null;
  const sh = (here.o / here.t) * 100;
  const jobs = fmt(Math.round(here.o));

  if (shown.length >= all.length) {
    const v = shown
      .map((x) => ({ n: name(x), sh: age(x).o55 * 100 }))
      .sort((a, b) => b.sh - a.sh);
    const hi = v[0];
    const lo = v[v.length - 1];
    if (hi.sh - lo.sh < (opt.minGap || 8)) {
      return none(
        `Across all ${all.length} ${unit}, ${sh.toFixed(0)}% of the workforce is 55 or ` +
        `over — ${jobs} jobs — and the mix barely varies, from ${lo.sh.toFixed(0)}% to ` +
        `${hi.sh.toFixed(0)}%.`
      );
    }
    return found(
      `Across all ${all.length} ${unit}, ${sh.toFixed(0)}% of the workforce is 55 or ` +
      `over — ${jobs} jobs to replace within a decade. ${hi.n} runs oldest at ` +
      `${hi.sh.toFixed(0)}%, ${lo.n} youngest at ${lo.sh.toFixed(0)}%.`
    );
  }

  const rest = all.filter((x) => shown.indexOf(x) < 0);
  const there = roll(rest);
  if (!there.t) return null;
  return found(
    `These ${shown.length} ${unit} run ${sh.toFixed(0)}% aged 55 and over — ${jobs} ` +
    `jobs — against ${((there.o / there.t) * 100).toFixed(0)}% across the other ` +
    `${rest.length}.`
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
    return none(`What jobs ask for and what workers hold are close here, within ${pts(g)}.`);
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
    return none(`No one kind of work dominates: the largest ${topN} hold ${sh.toFixed(0)}% of jobs.`);
  }
  return found(
    `The largest ${topN} families hold ${sh.toFixed(0)}% of Vermont jobs between them.`
  );
}

/**
 * Where the workforce is oldest, and how far that is from where it is youngest.
 *
 * Reported as the 55-and-over share, because that is the share whose work has to
 * be replaced within about a decade whatever else is true of it, and a reader
 * planning programmes needs the gap between the extremes, not the average.
 *
 * `label` names the row kind, so one rule serves both the sector and the family
 * chart rather than two that could drift apart.
 */
export function oldestWorkforce(rows, nameOf, label = 'kind of work', minGap = 8) {
  const v = rows
    .map((r) => {
      const a = r.age;
      if (!a) return null;
      const tot = a.u35 + a.m + a.o55;
      return tot ? { n: nameOf(r), sh: (a.o55 / tot) * 100 } : null;
    })
    .filter(Boolean)
    .sort((a, b) => b.sh - a.sh);
  if (v.length < 2) return null;
  const hi = v[0];
  const lo = v[v.length - 1];
  const gap = hi.sh - lo.sh;
  if (gap < minGap) {
    return none(
      `Every ${label} has a similar age mix: the 55-and-over share runs from ` +
        `${lo.sh.toFixed(0)}% to ${hi.sh.toFixed(0)}%.`
    );
  }
  return found(
    `${hi.n} has the oldest workforce — ${hi.sh.toFixed(0)}% are 55 or over, ` +
      `against ${lo.sh.toFixed(0)}% in ${lo.n}.`
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
    return none(`The average sits above the typical worker in ${n} of ${w.length} of these occupations.`);
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
  return found(`${n} of ${w.length} kinds of work are projected to shrink by 2030.`);
}

/** Observed change, how many families grew. */
export function observedSplit(fams, minShare = 10) {
  const w = fams.filter((r) => r.chgPct !== null && r.chgPct !== undefined);
  if (!w.length) return null;
  const n = w.filter((r) => r.chgPct < 0).length;
  if ((n / w.length) * 100 < minShare) return none('Nearly every family grew over 2021–2025.');
  return found(`${w.length - n} of ${w.length} kinds of work grew between 2021 and 2025; ${n} shrank.`);
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
  return found(`${s[0].a} and ${s[1].a} are ${sh.toFixed(0)}% of everything VSCS awards.`);
}

/** Families whose occupations draw no VSCS completions at all. */
export function familiesNoCompletions(byFamily, minOpen = 2000) {
  const z = byFamily.filter((r) => r.linked === 0);
  if (!z.length) return none('Every occupational family draws some VSCS completions.');
  const open = z.reduce((a, r) => a + r.open, 0);
  if (open < minOpen) {
    return none(`${z.length} kinds of work draw no VSCS graduates at all, on ${fmt(open)} openings a year.`);
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

/**
 * The contrast between the credential that most reliably leads to a job that both
 * hires and pays, and the one that least reliably does.
 */
export function funnelContrast(rows, minGap = 20) {
  const w = rows.filter((r) => r.nHiring >= 5);
  if (w.length < 2) return null;
  const rate = (r) => (r.nPaying / r.nHiring) * 100;
  const s = w.slice().sort((a, b) => rate(b) - rate(a));
  const hi = s[0];
  const lo = s[s.length - 1];
  if (rate(hi) - rate(lo) < minGap) {
    return none('Occupations that hire at scale pay a living wage at a similar rate across credentials.');
  }
  return found(
    `At ${hi.t.toLowerCase()}, ${hi.nPaying} of the ${hi.nHiring} occupations hiring at ` +
    `scale pay above the living wage; at ${lo.t.toLowerCase()}, ${lo.nPaying} of ${lo.nHiring}.`
  );
}

/* ---------- the opportunity screen ---------- */

/** What the screen returned, against the whole occupation set. */
export function screenYield(all, acted, universe) {
  if (!universe) return null;
  if (!all.length) {
    return none('No occupation clears the screen at these thresholds.');
  }
  const pc = (all.length / universe) * 100;
  return found(
    `${fmt(all.length)} of ${fmt(universe)} occupations clear the screen (${pc.toFixed(1)}%), ` +
    `and ${fmt(acted.length)} of those show movement on at least two signals without an ` +
    `established VSCS pipeline.`
  );
}

/**
 * One row, stated as it would be said over a slide. Figures only; it draws no
 * conclusion and does not address the reader.
 */
export function screenNarration(r) {
  const size = r.j >= 2000 ? 'a large occupation' : r.j >= 500 ? 'a mid-sized occupation' : 'a small occupation';
  const growth =
    r.g === null || r.g === undefined
      ? ''
      : r.g > 0
        ? `, projected to grow ${r.g.toFixed(1)}% by 2030`
        : `, projected to contract ${Math.abs(r.g).toFixed(1)}% by 2030`;
  const pipe =
    r.linked === 0
      ? 'VSCS produces no completions linked to it'
      : `VSCS produces ${r.linked.toFixed(1)} linked completions a year against those openings`;
  return (
    `${r.n} is ${size} at ${fmt(r.j)} jobs, turning over ${fmt(r.o)} openings a year ` +
    `at a median of ${money(r.m)}${growth}, on a ${r.t.toLowerCase()} credential. ${pipe}.`
  );
}
