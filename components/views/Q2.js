'use client';

import {
  LC, PCT, COMPARE, PEOPLE, SIZE_ORDER, TOTJ,
  lwAnnual, occBySize, compareCol,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Panel, Ranked, VHead, LwPicker } from '../ui';
import Filters, { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import { useDrill, occDrill } from '../Drill';
import { occCols, personTip } from '../occCols';
import { bandCols, ladderCols, peopleCols } from '@/lib/tables';
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
  const topPool = LC.topOcc;

  // One bar per size band at the pay of its typical occupation. A bar cannot show
  // the spread the dot columns showed, so the hover carries the range the
  // occupations in the band actually cover.
  const szBars = sz
    .filter((r) => r.med)
    .map((r) => {
      const bx = r.box || {};
      return {
        label: r.s,
        value: r.med,
        color: r.med >= LWA ? '--s3' : '--s2',
        onClick: () => sizeDrill(r.s),
        extra: [
          ['Times the living wage', (r.med / LWA).toFixed(2) + '×'],
          ['Middle half pays', bx.p25 && bx.p75 ? money(bx.p25) + ' to ' + money(bx.p75) : '—'],
          ['Lowest-paid tenth', bx.p10 ? money(bx.p10) : '—'],
          ['Highest-paid tenth', bx.p90 ? money(bx.p90) : '—'],
          ['Occupations', fmt(r.nocc)],
          ['Jobs', fmt(r.jobs)],
        ],
      };
    })
    .sort((a, b) => b.value - a.value);

  // The state, its nearest comparable state and the country, as grey baseline bars
  // rather than three more clouds -- they cost half the chart to make one point.
  const areaRefs = ['Vermont', 'New Hampshire', 'United States']
    .map(compareCol)
    .filter(Boolean)
    .map((a) => ({
      label: a.label,
      value: a.med,
      color: '--ink-3',
      extra: [
        ['Times the living wage', (a.med / LWA).toFixed(2) + '×'],
        ['Basis', a.sub],
      ],
    }));

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
        Which occupations employ the most Vermonters, and do the big ones pay enough to live on?
      </VHead>

      <Sections
        id="wage"
        active={section}
        items={[
          {
            id: 'wage-quality-by-size',
            label: 'Wage quality by size',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="Do the largest occupations pay a living wage?"
                  note={sizeWageGap(LC.sizeTiers, lw)}
                  cap={`Benchmark: ${lw} at ${money(LWA)}/yr.`}
                  src="Vermont occupation data, 2025 · weighted by jobs · occupation median against the benchmark"
                  data={{ cols: bandCols(LWA), rows: sz, label: 'wage-quality-by-size',
                          initialSort: { k: 'jobs', dir: -1 }, unit: 'size bands' }}
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
              </>
            ),
          },
          {
            id: 'median-pay-by-size',
            label: 'Median pay by size',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="What does a typical job pay, by how big the occupation is?"
                  note={sizePayStep(PCT.sizeTiers, SIZE_ORDER)}
                  cap="Green bars clear the living wage, amber ones do not. The grey bars are the state, its nearest comparable state and the country. Hover for the range inside a band; click for the occupations behind it."
                  src="Vermont occupation data, 2025 · reference bars from published state and national wage data"
                  data={{ cols: occCols(LWA), rows: LC.allOcc, label: 'pay-by-occupation-size',
                          initialSort: { k: 'j', dir: -1 }, unit: 'occupations',
                          note: 'Every priced Vermont occupation — the dots in the chart above.' }}
                >
                  <RankedBars
                    rows={szBars.concat(areaRefs)}
                    opts={{
                      money: true,
                      rule: LWA,
                      ruleLabel: 'Living wage',
                      valueLabel: 'Typical pay',
                      labelWidth: 236,
                      aria: 'Typical pay by occupation size band and by area',
                    }}
                  />
                </Panel>
              </>
            ),
          },
          {
            id: 'worker-earnings',
            label: 'Worker earnings',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="What do individual Vermonters actually earn?"
                  note={meanMedianGap(PEOPLE.byArea[0])}
                  cap="Each dot is one Vermonter on a wage or salary, placed at what they earned that year. The self-employed and the military are left out, matching the occupation charts. The dots are a fair sample; the average and midpoint lines come from everyone who answered, not just the dots shown."
                  src={`Census household survey, 2024 · ${PEOPLE.universe.toLowerCase()} · living-wage benchmark 2025, ${lw}`}
                  data={{ cols: peopleCols('Place'), rows: PEOPLE.byArea, label: 'worker-earnings',
                          initialSort: { k: 'med', dir: -1 }, unit: 'places',
                          note: 'Groups, not the individual dots: each dot is one anonymous respondent.' }}
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
              </>
            ),
          },
          {
            id: '25-largest-by-jobs',
            label: '25 largest by jobs',
            render: () => (
                <Panel
                  title="Which 25 occupations employ the most Vermonters?"
                  note={topOccShare(top, TOTJ, LC.allOcc.length)}
                  cap="Ranked by how many people they employ. Green clears the living wage at the typical job, amber does not."
                  src="Vermont occupation data, 2025 · hover for the occupation code, earnings, entry credential and demand"
                  data={{ cols: occCols(LWA), rows: topPool, label: 'largest-occupations',
                          initialSort: { k: 'j', dir: -1 }, unit: 'occupations' }}
                >
                  <Ranked id="q2-top" rows={topPool} show={25}>
                    {(pick) => (
                  <RankedBars
                    rows={pick.map((r) => ({
                      // Full name: the chart shortens and, if it still has to, truncates.
                      label: r.n,
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
                    )}
                  </Ranked>
                </Panel>
            ),
          },
          {
            id: 'mean-against-median',
            label: 'Mean against median',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="In the largest occupations, how far is the average above the typical worker?"
                  note={meanAboveMedian(ladder)}
                  cap="The gap between the midpoint and the average is how far top earners pull the average up."
                  src={`Published wage percentiles, Vermont 2025 · ${ladderMu} of ${ladder.length} with a published average · living-wage benchmark 2025, ${lw}`}
                  data={{ cols: ladderCols(LWA), rows: ladder, label: 'pay-spread-largest-occupations',
                          initialSort: { k: 'med', dir: -1 }, unit: 'occupations' }}
                >
                  <LadderLegend />
                  <Ranked id="q2-ladder" rows={ladder}>
                    {(pick) => (
                  <PercentileLadder
                    rows={pick}
                    opts={{
                      labelWidth: 262,
                      rule: LWA,
                      ruleLabel: 'Living wage',
                      aria: 'Percentile range, median and mean for the 25 largest occupations',
                    }}
                  />
                    )}
                  </Ranked>
                </Panel>
              </>
            ),
          },
          {
            id: 'size-against-pay',
            label: 'Size against pay',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
              <>
                <ActiveFilters />
                <Filters shown={filtered.length} total={LC.allOcc.length} pool={LC.allOcc} showFamilies />
                <Panel
                  title="Does a bigger occupation pay better or worse?"
                  cap={`${fmt(filtered.length)} of ${fmt(LC.allOcc.length)} occupations. The vertical line is the living wage; color shows how large the occupation is.`}
                  src="Vermont occupation data, 2025 · occupations with a usable median · log scale"
                  data={{ cols: occCols(LWA), rows: filtered, label: 'size-against-pay',
                          initialSort: { k: 'j', dir: -1 }, unit: 'occupations' }}
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
              </>
              </>
            ),
          },
        ]}
      />
    </>
  );
}
