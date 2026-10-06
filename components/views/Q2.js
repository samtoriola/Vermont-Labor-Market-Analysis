'use client';

import {
  LC, PCT, COMPARE, PEOPLE, SIZE_ORDER, TOTJ,
  lwAnnual, wageStats, occDots, occBySize, compareCol,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Panel, VHead, LwPicker } from '../ui';
import Filters, { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import { useDrill, occDrill } from '../Drill';
import { occDotTip, personTip } from '../occCols';
import { RankedBars, Scatter } from '../charts';
import { DotColumns, DotLegend, PercentileLadder, LadderLegend } from '../dots';
import Sections from '../Sections';
import { meanAboveMedian, meanMedianGap, sizePayStep, sizeWageGap, topOccShare } from '@/lib/insight';

export default function Q2({ lw, setLw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const { apply } = useFilters();
  const filtered = apply(LC.allOcc);

  const sizeDrill = (band) =>
    open(
      occDrill({
        label: 'Occupation size',
        title: band,
        cap: 'Every occupation in this size band, largest first.',
        occ: occBySize(band),
        lwAnnual: LWA,
      })
    );
  const sz = LC.sizeTiers;
  const [big, mid, small] = sz;
  const top = LC.topOcc.slice(0, 25);

  const szDots = SIZE_ORDER.map((band) => {
    const occ = occBySize(band);
    const st = wageStats(occ);
    return {
      label: band,
      sub: fmt(st.n) + ' occupations',
      dots: occDots(occ),
      avg: st.avg,
      med: st.med,
      onClick: () => sizeDrill(band),
    };
  }).filter((r) => r.dots.length);

  const areaRefs = ['Vermont', 'New Hampshire', 'United States'].map(compareCol).filter(Boolean);

  // The occupation dot charts are job-level: what a role pays. These are people --
  // one dot per ACS respondent, at their own wage income. Vermont leads, the
  // neighbouring state and the nation follow as reference.
  const peopleAreas = PEOPLE.byArea.map((a, i) => ({
    label: a.label,
    sub: fmt(a.n) + ' respondents',
    dots: a.dots,
    avg: a.avg,
    med: a.med,
    thin: a.thin,
    ref: i > 0,
  }));

  // Percentile ladder for the largest occupations. OEWS supplies the mean alongside
  // the percentiles, so mean and median can be read on one line; Lightcast supplies
  // the percentiles for anything OEWS suppresses.
  const ladder = top
    .map((r) => {
      const L = COMPARE.vtLadder[r.soc];
      const b = L || PCT.occ[r.soc];
      if (!b) return null;
      return {
        label: r.n,
        p10: b.p10,
        p25: b.p25,
        p50: b.p50,
        p75: b.p75,
        p90: b.p90,
        mu: L ? L.mu : null,
        // OEWS publishes no combined row for a few occupations Lightcast reports as
        // one, so the mean is genuinely absent rather than merely missing.
        muNote: L ? null : 'not published for Vermont',
        color: b.p50 >= LWA ? '--s3' : '--s2',
        extra: [
          ['Jobs, 2025', fmt(r.j)],
          ['SOC', r.soc],
          ['Entry education', r.e],
        ],
      };
    })
    .filter(Boolean);
  const ladderMu = ladder.filter((r) => r.mu !== null && r.mu !== undefined).length;

  return (
    <>
      <VHead
        title="Occupation size and wage quality"
      >
        Which occupations employ the largest numbers of Vermont workers, and how does wage quality — measured against a self-sufficiency benchmark — vary across large, medium, and smaller occupations?
      </VHead>

      <ActiveFilters />

      <LwPicker value={lw} onChange={setLw} />







      <Filters shown={filtered.length} total={LC.allOcc.length} showFamilies />

      <Sections
        id="wage"
        active={section}
        items={[
          {
            id: 'wage-quality-by-size',
            label: 'Wage quality by size',
            render: () => (
                <Panel
                  title="Do the largest occupations pay a living wage?"
                  note={sizeWageGap(LC.sizeTiers, lw)}
                  cap={`Benchmark: ${lw} at ${money(LWA)}/yr.`}
                  src="Lightcast · jobs-weighted · occupation median vs MIT living wage"
                >
                  <RankedBars
                    rows={sz.map((r) => ({
                      label: r.s,
                      value: r.above[lw],
                      color: '--s1',
                      mode: 'pct',
                      onClick: () => sizeDrill(r.s),
                      extra: [
                        ['Occupations', fmt(r.nocc)],
                        ['Jobs', fmt(r.jobs)],
                        ['Share of employment', r.share + '%'],
                        ['Median earnings', money(r.med)],
                        ['Annual openings', fmt(r.open)],
                      ],
                    }))}
                    opts={{
                      mode: 'pct',
                      labelWidth: 196,
                      valueLabel: 'Above living wage',
                      aria: 'Wage quality by size tier',
                    }}
                  />
                </Panel>
            ),
          },
          {
            id: 'median-pay-by-size',
            label: 'Median pay by size',
            render: () => (
                <Panel
                  title="How does pay spread within large, medium and smaller occupations?"
                  note={sizePayStep(PCT.sizeTiers, SIZE_ORDER)}
                  cap="One dot per occupation, placed at its median pay and sized by employment. The solid line is the employment-weighted average, the dashed line the median. The three columns on the right put Vermont as a whole beside its nearest comparable state and the nation. Click a Vermont column for the occupations behind it."
                  src="Lightcast Vermont occupations · reference columns BLS OEWS: Vermont and New Hampshire 2025, United States 2024"
                >
                  <DotLegend unit="one occupation" />
                  <DotColumns
                    groups={szDots.concat(areaRefs)}
                    opts={{
                      yMax: COMPARE.yMax,
                      rule: LWA,
                      ruleLabel: 'Living wage ' + money(LWA),
                      dotTip: occDotTip(LWA),
                      aria: 'Median pay of every occupation, by size band and by area',
                    }}
                  />
                </Panel>
            ),
          },
          {
            id: 'worker-earnings',
            label: 'Worker earnings',
            render: () => (
                <Panel
                  title="What do individual Vermonters actually earn?"
                  note={meanMedianGap(PEOPLE.byArea[0])}
                  cap="Every dot is one Vermont wage and salary worker who answered the American Community Survey, placed at their own wage income for the year. The self-employed and military occupations are excluded, matching the universe used by the occupation charts. Dots are a random draw made in proportion to survey weight, so the cloud reflects the population rather than the raw respondent mix — but the average and median lines are computed from every respondent, not just the dots shown."
                  src={`IPUMS USA, ACS 1-year 2024 · ${PEOPLE.universe.toLowerCase()} · living wage: MIT 2025, ${lw}`}
                >
                  <DotLegend unit="one survey respondent" sized={false} />
                  <DotColumns
                    groups={peopleAreas}
                    opts={{
                      yMax: PEOPLE.yMax,
                      rule: LWA,
                      ruleLabel: 'Living wage ' + money(LWA),
                      dotTip: personTip(LWA),
                      aria: 'Earnings of individual survey respondents, by area',
                    }}
                  />
                </Panel>
            ),
          },
          {
            id: '25-largest-by-jobs',
            label: '25 largest by jobs',
            render: () => (
                <Panel
                  title="Which 25 occupations employ the most Vermonters?"
                  note={topOccShare(top, TOTJ, LC.allOcc.length)}
                  cap="Ranked by 2025 jobs. Green clears the living wage at the median, amber does not."
                  src="Lightcast · hover for SOC, earnings, entry credential and demand"
                >
                  <RankedBars
                    rows={top.map((r) => ({
                      label: r.n.length > 42 ? r.n.slice(0, 40) + '…' : r.n,
                      value: r.j,
                      color: r.m && r.m >= LWA ? '--s3' : '--s2',
                      extra: [
                        ['SOC', r.soc],
                        ['Median earnings', r.m ? money(r.m) : '—'],
                        ['vs living wage', r.m ? (r.m / LWA).toFixed(2) + '×' : '—'],
                        ['Typical entry education', r.e],
                        ['Annual openings', fmt(r.o)],
                        ['Unique postings, 5 yr', fmt(r.p)],
                        ['5-yr projected growth', r.g !== null ? r.g + '%' : '—'],
                      ],
                    }))}
                    opts={{ labelWidth: 262, aria: '25 largest occupations by employment' }}
                  />
                </Panel>
            ),
          },
          {
            id: 'mean-against-median',
            label: 'Mean against median',
            render: () => (
                <Panel
                  title="In the largest occupations, how far is the average above the typical worker?"
                  note={meanAboveMedian(ladder)}
                  cap="The line spans the 10th to 90th percentile, the thick middle the 25th to 75th. The solid dot is the median and the hollow ring the mean; the distance between them is the pull of the upper tail. The dashed vertical is the living wage."
                  src={`BLS OEWS Vermont 2025 · ${ladderMu} of ${ladder.length} with a published mean · percentiles from Lightcast where OEWS reports no combined row · living wage: MIT 2025, ${lw}`}
                >
                  <LadderLegend />
                  <PercentileLadder
                    rows={ladder}
                    opts={{
                      labelWidth: 262,
                      rule: LWA,
                      ruleLabel: 'Living wage',
                      aria: 'Percentile range, median and mean for the 25 largest occupations',
                    }}
                  />
                </Panel>
            ),
          },
          {
            id: 'size-against-pay',
            label: 'Size against pay',
            render: () => (
                <Panel
                  title="Does a bigger occupation pay better or worse?"
                  cap={`${fmt(filtered.length)} of ${fmt(LC.allOcc.length)} occupations after filters. The vertical line is the living wage. Colored by size tier.`}
                  src="Lightcast · occupations with usable median earnings · log y-axis"
                >
                  <Scatter
                    pts={filtered
                      .filter((r) => r.m)
                      .map((r) => ({
                        x: r.m,
                        y: r.j,
                        label: r.n,
                        series: r.j >= 2000 ? 0 : r.j >= 500 ? 1 : 2,
                        extra: [
                          ['Median earnings', money(r.m)],
                          ['Jobs', fmt(r.j)],
                          ['Entry education', r.t],
                          ['Family', r.f],
                        ],
                      }))}
                    opts={{
                      xLabel: 'Median annual earnings',
                      yLabel: 'Jobs (log scale)',
                      logY: true,
                      vRule: LWA,
                      vRuleLabel: 'Living wage',
                      aria: 'Occupation size against median earnings',
                    }}
                  />
                </Panel>
            ),
          },
        ]}
      />
    </>
  );
}
