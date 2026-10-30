'use client';

import {
  LC, PCT, COMPARE, SIZE_ORDER, TOTJ,
  lwAnnual, occBySize, compareCol,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { HowTo, Panel, Picker, Ranked, VHead, LwPicker } from '../ui';
import Filters, { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { occCols } from '../occCols';
import { bandCols, ladderCols } from '@/lib/tables';
import { RankedBars, Scatter } from '../charts';
import { PercentileLadder, LadderLegend } from '../dots';
import Sections from '../Sections';
import { meanAboveMedian, sizePayStep, sizeWageGap, topOccShare } from '@/lib/insight';

// The 25 largest occupations were two sections asking two things about one set
// of rows: how much employment they hold, and how far the average sits above
// the typical worker inside them. Same 25 rows both times, so they are one
// panel with the measure on a control.
const LARGEST_MEASURES = [
  { id: 'share', label: 'Share of jobs' },
  { id: 'spread', label: 'Pay spread' },
];

// Three questions about the relationship between how big an occupation is and
// what it pays, which were two sections: the three size bands at the pay of
// their typical job, how much of each band clears the benchmark, and the same
// relationship without the banding at all -- every occupation as one point.
// The third was its own section and is the ungrouped version of the first two.
const SIZE_MEASURES = [
  { id: 'pay', label: 'Typical pay' },
  { id: 'above', label: 'Above living wage' },
  { id: 'each', label: 'Every occupation' },
];

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

  // What the pane shows for a size band.
  const sizeDetail = (r) =>
    occDetail({
      label: 'Occupation size',
      title: r.s,
      occ: occBySize(r.s),
      lwAnnual: LWA,
      stats: [
        [fmt(r.jobs), 'Jobs today'],
        [r.share + '%', 'Of all VT jobs'],
        [r.med ? money(r.med) : '—', 'Typical pay'],
      ],
      onMore: () => sizeDrill(r.s),
    });
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
        big: [[fmt(r.jobs), 'Jobs today']],
        extra: [
          ['Times the living wage', (r.med / LWA).toFixed(2) + '×'],
          ['Middle half pays', bx.p25 && bx.p75 ? money(bx.p25) + ' to ' + money(bx.p75) : '—'],
          ['Lowest-paid tenth', bx.p10 ? money(bx.p10) : '—'],
          ['Highest-paid tenth', bx.p90 ? money(bx.p90) : '—'],
          ['Occupations', fmt(r.nocc)],
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

  // Two questions about the same three bands -- what the typical job pays, and how
  // much of the band clears the benchmark -- which were two sections apart. The
  // benchmark selector stays on both, because both answers move with it.
  const size = {
    pay: {
      title: 'What does a typical job pay, by how big the occupation is?',
      note: sizePayStep(PCT.sizeTiers, SIZE_ORDER),
      cap: 'Green bars clear the living wage, amber ones do not. The grey bars are the state, its nearest comparable state and the country.',
      src: 'Vermont occupation data, 2025 · reference bars from published state and national wage data',
      data: {
        cols: occCols(LWA),
        rows: LC.allOcc,
        label: 'pay-by-occupation-size',
        initialSort: { k: 'j', dir: -1 },
        unit: 'occupations',
        note: 'Every priced Vermont occupation, the detail behind the three bands.',
      },
      chart: (
        <Split items={sz} keyOf={(r) => r.s} detail={sizeDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={szBars
                .map((b) => ({
                  ...b,
                  onClick: () => select(b.label),
                  active: active === b.label,
                }))
                .concat(areaRefs)}
              opts={{
                money: true,
                width,
                rule: LWA,
                ruleLabel: 'Living wage',
                valueLabel: 'Typical pay',
                labelWidth: 236,
                clickHint: 'Click for the occupations in this band',
                aria: 'Typical pay by occupation size band and by area',
              }}
            />
          )}
        </Split>
      ),
    },

    above: {
      title: 'Do the largest occupations pay a living wage?',
      note: sizeWageGap(LC.sizeTiers, lw),
      cap: `Benchmark: ${lw} at ${money(LWA)}/yr.`,
      src: 'Vermont occupation data, 2025 · weighted by jobs · occupation median against the benchmark',
      data: {
        cols: bandCols(LWA),
        rows: sz,
        label: 'wage-quality-by-size',
        initialSort: { k: 'jobs', dir: -1 },
        unit: 'size bands',
      },
      chart: (
        <Split items={sz} keyOf={(r) => r.s} detail={sizeDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={sz.map((r) => ({
                label: r.s,
                value: r.above[lw],
                color: '--s1',
                mode: 'pct',
                onClick: () => select(r.s),
                active: active === r.s,
                big: [[fmt(r.jobs), 'Jobs today']],
                extra: [
                  ['Occupations', fmt(r.nocc)],
                  ['Share of employment', r.share + '%'],
                  ['Median earnings', money(r.med)],
                  ['Annual openings', fmt(r.open)],
                ],
              }))}
              opts={{
                mode: 'pct',
                labelWidth: 196,
                width,
                valueLabel: 'Above living wage',
                clickHint: 'Click for the occupations in this band',
                aria: 'Wage quality by size tier',
              }}
            />
          )}
        </Split>
      ),
    },

    // The same question with the banding taken off: every occupation as one
    // point, so a reader can see how much spread the three bars were hiding.
    // It carries the filter bar, because at 798 points narrowing is the only
    // way to ask about one part of the market.
    each: {
      filters: true,
      title: 'Does a bigger occupation pay better or worse?',
      cap: `${fmt(filtered.length)} of ${fmt(LC.allOcc.length)} occupations, one point each. The vertical line is the living wage; colour is the size band the other two measures group by.`,
      src: 'Vermont occupation data, 2025 · occupations with a usable median · log scale',
      data: {
        cols: occCols(LWA),
        rows: filtered,
        label: 'size-against-pay',
        initialSort: { k: 'j', dir: -1 },
        unit: 'occupations',
      },
      chart: (
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
      ),
    },
  };

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
            id: 'size-and-pay',
            label: 'Size and pay',
            render: () => (
              <>
                <HowTo>
                  Pick a measure. The first two group every occupation into three size
                  bands and ask what that band pays; the third drops the banding and
                  plots all of them, where the filters apply. Click a bar for the
                  occupations inside it.
                </HowTo>
                <Picker id="q2-size" label="Measure" options={SIZE_MEASURES}>
                  {(m) => {
                    const v = size[m];
                    return (
                      <>
                        <LwPicker value={lw} onChange={setLw} />
                        {v.filters ? (
                          <>
                            <ActiveFilters />
                            <Filters
                              shown={filtered.length}
                              total={LC.allOcc.length}
                              pool={LC.allOcc}
                              showFamilies
                            />
                          </>
                        ) : null}
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
            id: 'largest-occupations',
            label: 'Largest occupations',
            render: () => (
              <>
                <HowTo>
                  The same twenty-five occupations under both measures: how much of
                  Vermont's employment each holds, and how far the average inside it sits
                  above the typical worker. Use Show to see the rest of the ranking.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Picker id="q2-largest" label="Measure" options={LARGEST_MEASURES}>
                  {(m) =>
                    m === 'spread' ? (
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
                    ) : (
                      <Panel
                        title="Which 25 occupations employ the most Vermonters?"
                        note={topOccShare(top, TOTJ, LC.allOcc.length)}
                        cap="Each occupation's share of the state's jobs, largest first. Green clears the living wage at the typical job, amber does not. Hover for the count."
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
                                value: (r.j / TOTJ) * 100,
                                color: r.m && r.m >= LWA ? '--s3' : '--s2',
                                extra: [
                                  ['Jobs', fmt(r.j)],
                                  ['Occupation code', r.soc],
                                  ['Median earnings', r.m ? money(r.m) : '—'],
                                  ['Times the living wage', r.m ? (r.m / LWA).toFixed(2) + '×' : '—'],
                                  ['Entry credential', r.e],
                                  ['Openings a year', fmt(r.o)],
                                  ['Job ads, 5 yr', fmt(r.p)],
                                  ['Projected by 2030', r.g !== null ? r.g + '%' : '—'],
                                ],
                              }))}
                              opts={{
                                mode: 'pct',
                                dec: 2,
                                labelWidth: 262,
                                valueLabel: 'Share of all jobs',
                                aria: 'Share of Vermont jobs in the largest occupations',
                              }}
                            />
                          )}
                        </Ranked>
                      </Panel>
                    )
                  }
                </Picker>
              </>
            ),
          },
        ]}
      />
    </>
  );
}
