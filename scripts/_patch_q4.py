"""Rebuilds the "By credential level" section as the pay ladder. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "components", "views", "Q4.js")
s = io.open(P, encoding="utf-8").read()


def sub(old, new, n=1):
    global s
    assert s.count(old) == n, "%d occurrences of %r" % (s.count(old), old[:80])
    s = s.replace(old, new)


# ---- imports ---------------------------------------------------------------
sub("""import {
  DATA, LC, PCT, TIER_ORDER, SERIES,
  lwAnnual, occByTier, credentialFunnel,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { bandCols } from '@/lib/tables';
import { Callout, HowTo, Panel, Picker, Table, VHead, LwPicker, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { occCols } from '../occCols';
import { RankedBars } from '../charts';
import Sections from '../Sections';
// Callout, N and largestCategory are used only by the section hidden further down.
// Kept imported so restoring it stays a single edit.
import {
  funnelContrast, ladderStep, livingWageJump, largestCategory,
} from '@/lib/insight';""",
"""import {
  DATA, LC, TIER_ORDER, SERIES,
  lwAnnual, occByTier, credentialFunnel,
} from '@/lib/data';
import { pooledLadder, rollUp } from '@/lib/wage';
import { fmt, money } from '@/lib/format';
import { bandCols, credLadderCols } from '@/lib/tables';
import { Callout, HowTo, Legend, Panel, Picker, Table, VHead, LwPicker, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { RankedBars, RangeRows } from '../charts';
import Sections from '../Sections';
// Callout, N and largestCategory are used only by the section hidden further down.
// Kept imported so restoring it stays a single edit.
import { funnelContrast, ladderShape, largestCategory } from '@/lib/insight';""")

# ---- the measure chips -----------------------------------------------------
sub("""const CRED_MEASURES = [
  { id: 'jobs', label: 'Share of jobs' },
  { id: 'pay', label: 'Typical pay' },
  { id: 'above', label: 'Above living wage' },
  { id: 'spread', label: 'Range of outcomes' },
];""",
"""/**
 * THE TAB, REBUILT
 * ----------------
 * This section carried four measures over the same five rungs: share of jobs,
 * typical pay, above the living wage, and range of outcomes. The last three are
 * one distribution asked three times, and splitting them across three charts is
 * what hid the shape of the ladder -- a reader had to hold two charts in their
 * head to see that a rung's midpoint clears the benchmark while a third of the
 * work behind it does not.
 *
 * They are one chart now: each rung drawn as the pay range its work covers, with
 * the benchmark ruled down all five. Where the line cuts a rung is the share
 * falling short, so the sufficiency measure is a position rather than a second
 * chart, and the spread is visible instead of being a ratio in a bar.
 *
 * Both retired measures were also wrong:
 *
 *   "Above living wage" read LC.tiers[].above, the median rule -- every job in an
 *   occupation counted on whichever side that occupation's midpoint falls. It
 *   reported that 100% of graduate / professional jobs clear the benchmark. 2.2%
 *   of them do not. lib/wage.js rollUp() replaces it, and Pathways was the last
 *   place the old rule survived.
 *
 *   "Range of outcomes" read PCT.tiers, the employment-weighted mean of its
 *   occupations' percentiles, which understates the spread by up to 44% because a
 *   mean of tenth percentiles averages away the gaps between occupations.
 *   lib/wage.js pooledLadder() replaces it.
 *
 * Share of jobs stays: it answers a different question and is the only measure
 * here that is not about pay.
 */
const CRED_MEASURES = [
  { id: 'ladder', label: 'The pay ladder' },
  { id: 'jobs', label: 'Share of jobs' },
];""")

# ---- the rows the ladder is drawn from -------------------------------------
sub("""  const sub = t['Sub-baccalaureate'];
  const ba = t["Bachelor's"];
  const grad = t['Graduate / professional'];
  const lastCps = DATA.trend[DATA.trend.length - 1];
  const P = PCT.tiers;""",
"""  const sub = t['Sub-baccalaureate'];
  const ba = t["Bachelor's"];
  const grad = t['Graduate / professional'];
  const lastCps = DATA.trend[DATA.trend.length - 1];

  // One row per rung: the pooled pay range, and how much of that work clears the
  // benchmark. The ladder is cached by tier because it does not depend on the
  // household selector -- only the rule drawn across it does -- so moving the
  // selector redraws without recomputing 781 ladders.
  const ladder = TIER_ORDER.map((key) => {
    const occ = occByTier(key);
    const box = pooledLadder(occ, key);
    const roll = rollUp(occ, LWA);
    if (!box || !roll) return null;
    return {
      t: key,
      box,
      jobs: roll.jobs,
      belowN: roll.belowN,
      above: 100 - roll.below,
      nocc: roll.nocc,
      share: t[key] ? t[key].share : null,
      occ,
    };
  }).filter(Boolean);

  const lo = Math.min(...ladder.map((r) => r.box.p10));
  const hi = Math.max(...ladder.map((r) => r.box.p90));
  const xMin = Math.floor(lo / 25000) * 25000;
  const xMax = Math.ceil(hi / 25000) * 25000;""")

# ---- drop the bars that fed the retired "Typical pay" chart ----------------
sub("""  // One bar per entry credential at the pay of its typical occupation. A bar cannot
  // show the spread, so the hover carries the range the occupations in it cover.
  const tierBars = TIER_ORDER.map((k) => t[k])
    .filter((r) => r && r.med)
    .map((r) => {
      const bx = r.box || {};
      return {
        label: r.t,
        value: r.med,
        color: r.med >= LWA ? '--s3' : '--s2',
        big: [[fmt(r.jobs), 'Jobs today']],
        extra: [
          ['Times the living wage', (r.med / LWA).toFixed(2) + '×'],
          ['Middle half pays', bx.p25 && bx.p75 ? money(bx.p25) + ' to ' + money(bx.p75) : '—'],
          ['Lowest-paid tenth', bx.p10 ? money(bx.p10) : '—'],
          ['Highest-paid tenth', bx.p90 ? money(bx.p90) : '—'],
          ['Share of all jobs', r.share.toFixed(1) + '%'],
          ['Occupations', fmt(r.nocc)],
        ],
      };
    });

  // Four questions about the same five rungs, which were three sections and four
  // panels: how much work sits at each level, what it pays, how much of it clears
  // the benchmark, and how wide the outcomes are. One control, one chart frame.
  //
  // The benchmark selector appears only on the two measures it changes, so the page
  // never carries a control that does nothing.
  const bands = {""",
"""  // The benchmark selector appears only on the measure it changes, so the page
  // never carries a control that does nothing.
  const bands = {""")

# ---- the new ladder measure, in place of pay / above / spread --------------
old_tail = s.split("  const cred = {\n", 1)[1]
start = old_tail.index("    pay: {")
end = old_tail.index("  };\n\n  return (")
body = """    ladder: {
      lw: true,
      title: 'What does each rung of the ladder actually pay?',
      note: ladderShape(ladder, LWA),
      cap:
        'The solid bar is the middle half of the work at that entry credential, the line ' +
        'reaches from the lowest-paid tenth to the highest, and the heavy mark is the ' +
        'midpoint job. Pooled across the occupations at each rung and weighted by their ' +
        'employment, so the spread is the one the work actually has. Where the dashed ' +
        'benchmark crosses a rung is the share of it falling short. Click a rung for the ' +
        'occupations inside it.',
      src:
        `Vermont occupation data, 2025 · ${fmt(ladder.reduce((a, r) => a + r.jobs, 0))} jobs ` +
        'with a published pay distribution · pay ladders pooled across the occupations at ' +
        `each entry credential and weighted by employment · benchmark ${money(LWA)} a year (${lw})`,
      data: {
        cols: credLadderCols(LWA),
        rows: ladder,
        label: 'pay-ladder-by-credential',
        initialSort: { k: 'p50', dir: -1 },
        unit: 'credentials',
        note:
          'Every pay figure here is pooled across the occupations at that credential, not ' +
          'the published roll-up, which understates the spread.',
      },
      chart: (
        <>
          <Legend
            labels={['Middle half of the work', 'Midpoint job', 'Lowest to highest-paid tenth']}
            colors={['--ord2', '--ord5', '--ord3']}
          />
          <Split items={ladder} keyOf={(r) => r.t} detail={(r) => tierDetail(r)}>
            {(select, active, width) => (
              <RangeRows
                rows={ladder.map((r) => ({
                  label: r.t,
                  box: r.box,
                  right: fmt(r.jobs),
                  right2: r.above.toFixed(0) + '%',
                  onClick: () => select(r.t),
                  active: active === r.t,
                  big: [[fmt(r.jobs), 'Jobs today']],
                  extra: [
                    ['Clears the benchmark', r.above.toFixed(1) + '%'],
                    ['People below it', fmt(r.belowN)],
                    ['Middle half pays', money(r.box.p25) + ' to ' + money(r.box.p75)],
                    ['Lowest-paid tenth', money(r.box.p10)],
                    ['Highest-paid tenth', money(r.box.p90)],
                    ['Times wider, top tenth over bottom', (r.box.p90 / r.box.p10).toFixed(2) + '×'],
                    ['Occupations', fmt(r.nocc)],
                  ],
                }))}
                opts={{
                  width,
                  money: true,
                  xMin,
                  xMax,
                  tickStep: 50000,
                  labelWidth: 206,
                  rule: LWA,
                  ruleLabel: `Living wage ${money(LWA)}`,
                  valueLabel: 'The midpoint job',
                  valueHead: 'JOBS',
                  rightHead: 'CLEARS IT',
                  clickHint: 'Click for the occupations at this level',
                  aria: 'Annual pay by entry credential, lowest-paid tenth to highest',
                }}
              />
            )}
          </Split>
        </>
      ),
    },

"""
s = s.replace(old_tail[start:end], body)

# ---- the how-to line, which promised four measures -------------------------
sub("""                <HowTo>
                  Four measures of the same five rungs. These are the credentials
                  <strong> jobs ask for</strong>, not the ones workers hold — the Workers
                  tab answers that, and the two do not match. Click a bar for the
                  occupations at that level.
                </HowTo>""",
"""                <HowTo>
                  The same five rungs, as what the work pays and as how much work sits
                  there. These are the credentials
                  <strong> jobs ask for</strong>, not the ones workers hold — the Workers
                  tab answers that, and the two do not match. Click a rung for the
                  occupations at that level.
                </HowTo>""")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q4.js patched,", len(s), "bytes")
