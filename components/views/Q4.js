'use client';

import {
  DATA, LC, TIER_ORDER, SERIES,
  lwAnnual, occByTier, credentialFunnel,
} from '@/lib/data';
import { pooledLadder, rollUp, rollUpOn, shareBelow, occBox } from '@/lib/wage';
import { fmt, money } from '@/lib/format';
import { bandCols, credLadderCols, openingsCols } from '@/lib/tables';
import { Callout, HowTo, Legend, Panel, Picker, VHead, LwPicker, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { occOpenCols } from '../occCols';
import { RankedBars, RangeRows } from '../charts';
import { shortLabel } from '@/lib/labels';
import Sections from '../Sections';
// Callout, N and largestCategory are used only by the section hidden further down.
// Kept imported so restoring it stays a single edit.
import { openingsSplit, ladderShape, largestCategory } from '@/lib/insight';

/**
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
];

export default function Q4({ lw, setLw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  // Counts occupations, not jobs: the question is whether a credential opens a
  // door, not how many people are already through it.
  const MIN_OPEN = 50;
  const funnel = credentialFunnel(LWA, MIN_OPEN);

  const tierDrill = (k) =>
    open(
      occDrill({
        label: 'Entry credential',
        title: k,
        cap: 'Every occupation whose typical entry credential is this tier, largest first.',
        occ: occByTier(k),
        lwAnnual: LWA,
      })
    );
  const t = {};
  LC.tiers.forEach((r) => {
    t[r.t] = r;
  });
  // What the pane shows for a credential tier.
  const tierDetail = (r, stats) =>
    occDetail({
      label: 'Entry credential',
      title: r.t,
      occ: occByTier(r.t),
      lwAnnual: LWA,
      stats: stats || [
        [fmt(r.jobs), 'Jobs today'],
        [r.share.toFixed(1) + '%', 'Of all VT jobs'],
        [r.med ? money(r.med) : '—', 'Typical pay'],
      ],
      onMore: () => tierDrill(r.t),
    });

  const sub = t['Sub-baccalaureate'];
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

  /**
   * A year of hiring at each credential, split by the benchmark.
   *
   * The section used to count DOORS: occupations clearing a volume screen and
   * then a pay screen, 3 of 106 at the bottom of the ladder. Two things were
   * wrong with it as the headline. The screen changed meaning up the ladder --
   * at the bottom the pay test is what bites, at the top only 9 of 76 graduate
   * occupations clear the volume test at all and every one of them pays -- so
   * one number per row could not say which test a rung was failing. And the
   * openings column it printed was gated the same way, which is defensible for
   * counting doors and not for counting openings: it threw away a whole
   * occupation over a few hundred dollars on its median, and every employer too
   * small to hire 50 a year with it.
   *
   * So this counts the openings themselves, weighted by each occupation's own
   * pay distribution and with no volume screen. The figures move a long way --
   * no formal credential goes 9% to 16%, a bachelor's 73% to 91% -- and the
   * ordering is the same, which is what you would expect if the old number was
   * measuring the screen rather than the work.
   *
   * The doors count is not lost: it is a figure in the drill, where it answers
   * the question it is actually good for.
   */
  const openings = TIER_ORDER.map((key) => {
    const occ = occByTier(key);
    const roll = rollUpOn(occ, LWA, (o) => o.o || 0);
    const f = funnel.filter((x) => x.t === key)[0];
    if (!roll || !roll.total) return null;
    return {
      t: key,
      occ,
      openAll: roll.total,
      openPay: roll.total - roll.belowN,
      openShort: roll.belowN,
      share: 100 - roll.below,
      nocc: roll.nocc,
      nAll: f ? f.nAll : occ.length,
      nHiring: f ? f.nHiring : null,
      nPaying: f ? f.nPaying : null,
    };
  }).filter(Boolean);

  const openDrill = (r) =>
    open({
      label: 'Entry credential',
      title: r.t,
      cap:
        `Every occupation whose typical entry credential is this tier, most openings first. ` +
        `"Openings in work that pays" is each occupation's openings weighted by how much of ` +
        `it clears ${money(LWA)} a year, so an occupation that half clears it contributes half.`,
      occ: r.occ,
      cols: occOpenCols(LWA),
      initialSort: { k: 'o', dir: -1 },
      stats: [
        ['Occupations', fmt(r.nAll)],
        ['Openings a year', fmt(r.openAll)],
        ['In work that pays', fmt(r.openPay)],
        ['Share', r.share.toFixed(1) + '%'],
        // The old headline, kept where it is the right answer: this one is about
        // the occupation, not about its openings.
        [`Hiring ${MIN_OPEN}+ a year and paying`,
          r.nPaying === null ? '—' : `${r.nPaying} of ${r.nAll}`],
      ],
      src:
        'Search, filter and sort with the controls at the top; export downloads the filtered rows',
    });

  const openDetail = (r) => {
    const top = r.occ
      .filter((o) => o.o)
      .slice()
      .sort((a, b) => b.o - a.o)
      .slice(0, 8);
    return {
      label: 'Entry credential',
      title: r.t,
      stats: [
        [fmt(r.openAll), 'Openings a year'],
        [fmt(r.openPay), 'In work that pays'],
        [r.share.toFixed(0) + '%', 'Share of them'],
      ],
      note: `The ${top.length} occupations hiring most, of ${fmt(r.nAll)}.`,
      cols: ['Occupation', 'Openings', 'Pays it'],
      rows: top.map((o) => {
        const b = shareBelow(occBox(o), LWA);
        return [shortLabel(o.n), fmt(o.o), b === null ? '—' : (100 - b).toFixed(0) + '%'];
      }),
      more: {
        label: `All ${fmt(r.nAll)} occupations, with every measure`,
        onClick: () => openDrill(r),
      },
    };
  };

  const lo = Math.min(...ladder.map((r) => r.box.p10));
  const hi = Math.max(...ladder.map((r) => r.box.p90));
  const xMin = Math.floor(lo / 25000) * 25000;
  const xMax = Math.ceil(hi / 25000) * 25000;

  // The benchmark selector appears only on the measure it changes, so the page
  // never carries a control that does nothing.
  const bands = {
    cols: bandCols(LWA, 't', 'Entry credential'),
    rows: LC.tiers,
    unit: 'credentials',
  };

  const cred = {
    jobs: {
      title: 'How much Vermont employment sits at each credential level?',
      cap: "What share of Vermont's jobs ask for each level of education.",
      src: `Vermont occupation data, 2025 · ${fmt(LC.totalJobs)} jobs`,
      data: { ...bands, label: 'jobs-by-credential', initialSort: { k: 'jobs', dir: -1 } },
      chart: (
        <Split items={LC.tiers} keyOf={(r) => r.t} detail={tierDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={TIER_ORDER.map((k, i) => {
                const r = t[k];
                return {
                  label: r.t,
                  value: r.share,
                  color: SERIES[i],
                  mode: 'pct',
                  onClick: () => select(r.t),
                  active: active === r.t,
                  big: [[fmt(r.jobs), 'Jobs today']],
                  extra: [['Occupations', fmt(r.nocc)]],
                };
              })}
              opts={{
                mode: 'pct',
                labelWidth: 176,
                width,
                valueLabel: 'Share of jobs',
                clickHint: 'Click for the occupations at this level',
                aria: 'Employment share by credential tier',
              }}
            />
          )}
        </Split>
      ),
    },

    ladder: {
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
          {/* No legend. Three swatches cut from one ramp read as three shades of
              the same thing at 13px, and the caption already names the solid bar,
              the line and the heavy mark in the order the eye meets them. */}
          <Split
            items={ladder}
            keyOf={(r) => r.t}
            detail={(r) =>
              tierDetail(r, [
                [fmt(r.jobs), 'Jobs today'],
                [r.above.toFixed(0) + '%', 'Clears the benchmark'],
                [money(r.box.p50), 'The midpoint job'],
              ])
            }
          >
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

  };

  return (
    <>
      <VHead
        title="Education pathways"
      >
        What does each level of education lead to in Vermont — how many jobs, and at what pay?
      </VHead>

      <Sections
        id="pathways"
        active={section}
        items={[
          {
            id: 'by-credential-level',
            label: 'By credential level',
            render: () => (
              <>
                <HowTo>
                  The same five rungs, as what the work pays and as how much work sits
                  there. These are the credentials
                  <strong> jobs ask for</strong>, not the ones workers hold — the Workers
                  tab answers that, and the two do not match. Click a rung for the
                  occupations at that level.
                </HowTo>
                <Picker id="q4-cred" label="Measure" options={CRED_MEASURES}>
                {(m) => {
                  const v = cred[m];
                  return (
                    <>
                      {v.lw ? <LwPicker value={lw} onChange={setLw} /> : null}
                      <Panel
                        title={v.title}
                        note={v.note}
                        cap={v.cap}
                        src={v.src}
                        data={v.data}
                      >
                        {v.chart}
                      </Panel>
                    </>
                  );
                }}
                </Picker>
              </>
            ),
          },
          {
            id: 'which-credentials-pay',
            label: 'Which credentials pay',
            render: () => (
              <>
                <HowTo>
                  A year of hiring at each credential, and how much of it is in work
                  that pays a living wage. Openings, not jobs — this is what someone
                  leaving a credential actually meets. Click a bar for the occupations
                  hiring behind it.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="How much of a year’s hiring at each credential pays a living wage?"
                  note={openingsSplit(openings)}
                  cap={`Every annual opening at each entry credential. The filled part is those in work paying at or above the benchmark, read off each occupation’s own pay distribution and weighted by its openings — so an occupation whose midpoint clears the benchmark by a dollar contributes about half its openings, not all of them. No volume screen: an opening counts whether or not its occupation hires ${MIN_OPEN} a year. Each row is measured against its own openings, so the five do not add to 100%. Household: ${lw}.`}
                  src={`Vermont occupation data, 2025 · entry credential · annual openings · the benchmark’s position read off each occupation’s own 10th-to-90th percentile ladder, weighted by its openings · benchmark ${money(LWA)} a year (${lw})`}
                  data={{
                    cols: openingsCols(),
                    rows: openings,
                    label: 'openings-by-credential',
                    initialSort: { k: 'openAll', dir: -1 },
                    unit: 'credentials',
                    note:
                      'The last column is the old measure, kept because it answers a different question: how many occupations at this level both hire in volume and pay.',
                  }}
                >
                  <Legend
                    labels={['Openings in work that pays a living wage', 'The rest']}
                    colors={['--s1', '--track']}
                  />
                  <Split items={openings} keyOf={(r) => r.t} detail={openDetail}>
                    {(select, active, width) => (
                      <RankedBars
                        rows={openings.map((r) => ({
                          label: r.t,
                          value: r.openPay,
                          backdrop: r.openAll,
                          right: r.share.toFixed(0) + '%',
                          onClick: () => select(r.t),
                          active: active === r.t,
                          big: [[fmt(r.openAll), 'Openings a year']],
                          extra: [
                            ['In work that does not pay it', fmt(r.openShort)],
                            ['Occupations', fmt(r.nAll)],
                            [
                              `Hiring ${MIN_OPEN}+ a year and paying`,
                              r.nPaying === null ? '—' : `${r.nPaying} of ${r.nAll}`,
                            ],
                            ...(r.occ.filter((o) => o.o).length
                              ? [
                                  [
                                    'Hiring most',
                                    shortLabel(
                                      r.occ
                                        .filter((o) => o.o)
                                        .slice()
                                        .sort((a, b) => b.o - a.o)[0].n
                                    ),
                                  ],
                                ]
                              : []),
                          ],
                        }))}
                        opts={{
                          width,
                          labelWidth: 206,
                          valueLabel: 'Openings in work that pays',
                          valueHead: 'THAT PAY',
                          rightHead: 'SHARE',
                          clickHint: 'Click for the occupations hiring at this level',
                          aria:
                            'Annual openings by entry credential, with the share in work paying a living wage',
                        }}
                      />
                    )}
                  </Split>
                </Panel>
              </>
            ),
          },
          // --- Hidden for now ---------------------------------------------
          // The jobs-versus-workers contrast is the Overview panel, and the captions here already say which of the two each chart shows.
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'what-this-measures',
          // label: 'What this measures',
          // render: () => (
          // <Callout label="What this measures">
          // <p>
          // These are job <em>requirements</em>, not worker <em>attainment</em>: a property of the
          // job, not of the person holding it.{' '}
          // <N>{(ba.share + grad.share).toFixed(1)}%</N> of Vermont jobs ask for a bachelor&rsquo;s
          // or more, while <N>{lastCps.ba.toFixed(1)}%</N> of Vermont workers 25+ hold one, a
          // difference of <N>{(lastCps.ba - ba.share - grad.share).toFixed(1)} points</N>. The two
          // come from different sources and count different things.
          // </p>
          // </Callout>
          // ),
          // },

        ]}
      />
    </>
  );
}
