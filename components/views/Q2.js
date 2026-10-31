'use client';

import { LC, TIER_ORDER, WF, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { HowTo, Panel, Picker, PickerPair, VHead, LwPicker, Legend } from '../ui';
import { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import { useDrill, occDrill } from '../Drill';
import { occCols } from '../occCols';
import { shortfallCols, floorCols } from '@/lib/tables';
import { RankedBars, Scatter } from '../charts';
import { pricedPool, rollUp, rollUpBy } from '@/lib/wage';
import Sections from '../Sections';
import { countyFloorShift, wageShortfall } from '@/lib/insight';

/**
 * Wage quality: how much of Vermont's work pays less than it costs to live here.
 *
 * WHAT CHANGED, AND WHY
 * ---------------------
 * This tab used to be organised by occupation size -- what a large, medium or small
 * occupation typically pays, and how much of each band cleared the benchmark. Three
 * of its five charts were cut that way, and occupation size is a property of the
 * classification rather than a question anyone brings to it. Nobody asks whether
 * big occupations pay well; they ask whether *this* work pays enough to live on.
 *
 * It also answered that question with the wrong arithmetic. "Share above the living
 * wage" compared an occupation's median with the benchmark and counted all of its
 * jobs on whichever side the median fell, so Installation & Repair read 3.3% below
 * when 22.6% of its jobs are, and Office & Admin Support read 63.7% when 49.2% are.
 * lib/wage.js carries the measure that replaced it and the full argument for it.
 *
 * So: two sections. One asks how much of the work falls short, over whichever rows
 * the reader wants, measured either as a share or as a headcount -- which do not
 * rank the same, and that disagreement is the finding. The other asks where it
 * bites, which is new: the cost floor is not the same in every county, and the
 * dashboard had been measuring all 14 against one statewide figure.
 *
 * The controls are the ones Employment and Demand already carry -- rows and measure
 * on chips, the filter bar above, click a bar for the occupations behind it -- so
 * the reader is not learning a new tab, only a different question.
 */

// What the rows are. The first three are rankings; the fourth drops the grouping
// and plots every occupation, which is where the filter bar earns its place.
const ROWS = [
  { id: 'group', label: 'Occupation groups' },
  { id: 'cred', label: 'Entry credential' },
  { id: 'occ', label: 'Largest occupations' },
  { id: 'each', label: 'Every occupation' },
];

// Share and headcount give different answers over the same rows, and the gap
// between them is the reason to carry both: the work least likely to pay a living
// wage is not where most of the people paid under one actually are.
const MEASURES = [
  { id: 'share', label: 'Share of jobs below' },
  { id: 'count', label: 'People below' },
];

const BENCH = [
  { id: 'local', label: "Each county's own floor" },
  { id: 'state', label: 'One statewide floor' },
];

/** The pay of the midpoint job in a set of occupations, not the mean of medians. */
function midpointPay(occ) {
  const priced = occ.filter((o) => o.m).sort((a, b) => a.m - b.m);
  const total = priced.reduce((a, o) => a + o.j, 0);
  if (!total) return null;
  let run = 0;
  for (let i = 0; i < priced.length; i += 1) {
    run += priced[i].j;
    if (run >= total / 2) return priced[i].m;
  }
  return priced[priced.length - 1].m;
}

export default function Q2({ lw, setLw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const { apply } = useFilters();

  // Only occupations carrying a usable pay ladder can be measured at all, so they
  // are the pool every row option is cut from and the denominator every share is
  // taken over. Saying so in the source line is the difference between a share of
  // the jobs we can price and a share of all of them.
  const pool = pricedPool(LC.allOcc);
  const filtered = apply(pool);
  const head = rollUp(filtered, LWA);

  const drill = (title, occ, cap) =>
    open(occDrill({ label: 'Occupation group', title, cap, occ, lwAnnual: LWA }));

  // One row per occupation group, per credential, or one per occupation for the
  // largest 25 -- the same five measures either way, so the chart and the table
  // under it do not care which is on screen.
  const rowsFor = (kind) => {
    if (kind === 'group') {
      return rollUpBy(filtered, (o) => o.f, LWA).map((r) => ({
        ...r,
        med: midpointPay(r.occ),
        onOpen: () => drill(r.f, r.occ, 'Every occupation in this group, largest first.'),
      }));
    }
    if (kind === 'cred') {
      return rollUpBy(filtered, (o) => o.t, LWA)
        .sort((a, b) => TIER_ORDER.indexOf(a.f) - TIER_ORDER.indexOf(b.f))
        .map((r) => ({
          ...r,
          med: midpointPay(r.occ),
          onOpen: () =>
            drill(r.f, r.occ, 'Every occupation entered at this credential, largest first.'),
        }));
    }
    // One occupation is its own row, so there is nothing inside it to open; the
    // click opens the group it belongs to instead, which is the next question.
    return filtered
      .slice()
      .sort((a, b) => b.j - a.j)
      .slice(0, 25)
      .map((o) => ({
        ...rollUp([o], LWA),
        f: o.n,
        soc: o.s,
        med: o.m,
        occ: [o],
        onOpen: () =>
          drill(o.f, occByFamily(o.f), `Opened from ${o.n}. Every occupation in this group.`),
      }));
  };

  const unit = (kind) =>
    kind === 'cred' ? 'credential levels' : kind === 'occ' ? 'occupations' : 'occupation groups';
  const rowLabel = (kind) =>
    kind === 'cred' ? 'Entry credential' : kind === 'occ' ? 'Occupation' : 'Occupation group';

  const bars = (rows, measure, kind) =>
    rows
      .slice()
      .sort((a, b) => (measure === 'share' ? b.below - a.below : b.belowN - a.belowN))
      .map((r) => ({
        label: r.f,
        value: measure === 'share' ? r.below : r.belowN,
        color: '--s2',
        big: [[fmt(r.jobs), 'Priced jobs']],
        onClick: r.onOpen,
        extra: [
          [
            measure === 'share' ? 'People below it' : 'Share of its jobs',
            measure === 'share' ? fmt(r.belowN) : r.below.toFixed(1) + '%',
          ],
          ['At or above it', fmt(r.jobs - r.belowN)],
          ['The midpoint job pays', r.med ? money(r.med) : '—'],
          ...(kind === 'occ' ? [['Occupation code', r.soc]] : [['Occupations', fmt(r.nocc)]]),
          ...(r.worst && kind !== 'occ'
            ? [['Most people short', `${r.worst.o.n} (${fmt(Math.round(r.worst.n))})`]]
            : []),
        ],
      }));

  const src =
    `Vermont occupation data, 2025 · ${fmt(head ? head.jobs : 0)} jobs with a published pay ` +
    `distribution · benchmark ${money(LWA)} a year (${lw}) · the benchmark's position read off ` +
    `each occupation's own 10th-to-90th percentile ladder, weighted by its jobs`;

  // The counties are the one answer that cannot be computed in the browser: it needs
  // a pay ladder per occupation per county, which lives only in the Core LMI county
  // slice. scripts/build_wagefloor.py does it once and commits the result.
  const cty = WF.counties;
  // Grand Isle and Essex are a few thousand jobs each, and on this chart they land
  // at the two ends of the ranking. A figure resting on that little is a true
  // reading and a weak finding, and the chart cannot say so by itself.
  const thin = cty.filter((r) => r.thin);
  const thinLine = thin.length
    ? ` ${thin.map((r) => r.c).join(' and ')} ${thin.length > 1 ? 'are' : 'is'} the smallest ` +
      `labour ${thin.length > 1 ? 'markets' : 'market'} in the state, so ${thin.length > 1 ? 'those figures rest' : 'that figure rests'} ` +
      `on very little: hover for the job counts.`
    : '';
  const ctyBars = (mode) =>
    cty
      .slice()
      .sort((a, b) => (mode === 'local' ? b.local - a.local : b.state - a.state))
      .map((r) => ({
        label: r.c,
        value: mode === 'local' ? r.local : r.state,
        color: '--s2',
        big: [[fmt(r.jobs), 'Jobs in the county']],
        extra: [
          ['Against its own floor', r.local.toFixed(1) + '%'],
          ['Against the statewide floor', r.state.toFixed(1) + '%'],
          ['Its own living wage', money(r.lwA)],
          ['Jobs below its own floor', fmt(r.localN)],
          ['The midpoint job pays', money(r.med)],
          ...(r.thin ? [['Note', 'One of the two smallest counties']] : []),
        ],
      }));

  return (
    <>
      <VHead title="Does the work pay enough?">
        {head
          ? `${fmt(head.belowN)} Vermont jobs — ${head.below.toFixed(0)}% of the ` +
            `${fmt(head.jobs)} the published distributions can price — pay less than ` +
            `${money(LWA)} a year.`
          : 'How much of Vermont’s work pays less than it costs to live here.'}
      </VHead>

      <Sections
        id="wage"
        active={section}
        items={[
          {
            id: 'how-much-falls-short',
            label: 'How much falls short',
            render: () => (
              <>
                <HowTo>
                  The filled part of each bar is the share of that work paying below the
                  benchmark; the track behind it is the rest. Pick what the rows are and
                  what the bar measures — share and headcount do not rank the same — and
                  the line under the chart answers the pair. Click a bar for the
                  occupations behind it.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                {/* The benchmark is the only control this tab needs: it is the
                    question. The five-group filter bar the other tabs carry was
                    four more ways to narrow a chart whose rows are already the
                    narrowing -- a credential filter on a chart of credentials is
                    a chart with rows missing. A filter set on another tab still
                    applies and still says so, because it moves these figures. */}
                <ActiveFilters />
                <PickerPair
                  id="q2-rows"
                  aLabel="Rows"
                  a={ROWS}
                  bLabel="Measure"
                  b={MEASURES}
                  hideB={(kind) => kind === 'each'}
                >
                  {(kind, measure) =>
                    kind === 'each' ? (
                      <Panel
                        title="Does a bigger occupation pay better or worse?"
                        cap={`${filtered.length === pool.length ? fmt(pool.length) : `${fmt(filtered.length)} of ${fmt(pool.length)}`} occupations, one point each. The vertical line is the living wage, so everything left of it is work whose typical job falls short.`}
                        src={`Vermont occupation data, 2025 · occupations with a published pay distribution · log scale · benchmark ${money(LWA)} a year (${lw})`}
                        data={{
                          cols: occCols(LWA),
                          rows: filtered,
                          label: 'size-against-pay',
                          initialSort: { k: 'j', dir: -1 },
                          unit: 'occupations',
                        }}
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
                                ['Occupation group', r.f],
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
                    ) : (
                      (() => {
                        const rows = rowsFor(kind);
                        return (
                          <Panel
                            title={
                              measure === 'share'
                                ? `How much of each ${rowLabel(kind).toLowerCase()} pays below a living wage?`
                                : 'How many people are in work that pays below a living wage?'
                            }
                            note={wageShortfall(rows, measure, rowLabel(kind).toLowerCase())}
                            cap={
                              measure === 'share'
                                ? 'The share of each row’s jobs paying under the benchmark, read off every occupation’s own pay distribution rather than from its median. The track behind each bar is 100% of that row’s jobs.'
                                : 'The same calculation weighted by employment, so a large row with a moderate share outranks a small row with a high one.'
                            }
                            src={src}
                            data={{
                              cols: shortfallCols(rowLabel(kind)),
                              rows,
                              label: 'wage-shortfall-by-' + kind,
                              initialSort: {
                                k: measure === 'share' ? 'below' : 'belowN',
                                dir: -1,
                              },
                              unit: unit(kind),
                            }}
                          >
                            <Legend
                              labels={['Below the benchmark', 'At or above it']}
                              colors={['--s2', '--track']}
                            />
                            <RankedBars
                              rows={bars(rows, measure, kind)}
                              opts={{
                                mode: measure === 'share' ? 'pct' : undefined,
                                // A headcount wants thousands separators, which
                                // fmtVal gives only when no decimal count is set.
                                dec: measure === 'share' ? 1 : undefined,
                                // A share belongs on a 0-100 track, where the empty
                                // part of the bar is itself the answer. A headcount
                                // has no natural top, so it keeps the ranked axis.
                                max: measure === 'share' ? 100 : undefined,
                                tickDec: 0,
                                track: measure === 'share',
                                labelWidth: kind === 'occ' ? 262 : 212,
                                valueLabel:
                                  measure === 'share' ? 'Below the benchmark' : 'People below',
                                clickHint:
                                  kind === 'occ'
                                    ? 'Click for the occupation group this belongs to'
                                    : 'Click for the occupations behind it',
                                aria:
                                  measure === 'share'
                                    ? 'Share of jobs paying below the living wage'
                                    : 'People in jobs paying below the living wage',
                              }}
                            />
                          </Panel>
                        );
                      })()
                    )
                  }
                </PickerPair>
              </>
            ),
          },
          {
            id: 'where-the-floor-bites',
            label: 'Where the floor bites',
            render: () => (
              <>
                <HowTo>
                  The share of each county’s jobs paying below a living wage. Switch the
                  benchmark between the county’s own cost floor and one statewide figure,
                  and watch which counties move — a high-wage county with a high floor can
                  look better than it is on the statewide number.
                </HowTo>
                <Picker id="q2-bench" label="Benchmark" options={BENCH}>
                  {(mode) => (
                    <Panel
                      title={
                        mode === 'local'
                          ? 'Against its own cost floor, where does the work fall shortest?'
                          : 'Against one statewide floor, where does the work fall shortest?'
                      }
                      note={countyFloorShift(cty, mode)}
                      cap={
                        mode === 'local'
                          ? `Each county against its own living wage, which runs from ${money(WF.lwRange[0])} in the cheapest county to ${money(WF.lwRange[1])} in the dearest. Both benchmarks are one adult with no children — the only household type published per county — so the pair isolates geography and nothing else.${thinLine}`
                          : `Every county against the statewide ${money(WF.lwA)}, which is how the rest of the dashboard reads them. Switch to each county’s own floor to see what that assumption costs.${thinLine}`
                      }
                      src={`Vermont occupation data by county, ${WF.year} · employees · the benchmark’s position read off each occupation’s own pay ladder, weighted by its employment in that county · county living wage, one adult, no children`}
                      data={{
                        cols: floorCols(),
                        rows: cty,
                        label: 'county-wage-floor',
                        initialSort: { k: mode, dir: -1 },
                        unit: 'counties',
                      }}
                    >
                      <Legend
                        labels={['Below the benchmark', 'At or above it']}
                        colors={['--s2', '--track']}
                      />
                      <RankedBars
                        rows={ctyBars(mode)}
                        opts={{
                          mode: 'pct',
                          dec: 1,
                          tickDec: 0,
                          max: 100,
                          track: true,
                          labelWidth: 150,
                          valueLabel: 'Below the benchmark',
                          aria: 'Share of county jobs paying below a living wage',
                        }}
                      />
                    </Panel>
                  )}
                </Picker>
              </>
            ),
          },
        ]}
      />
    </>
  );
}
