'use client';

import { SOW, TIER_ORDER, lwAnnual } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, VHead, N } from '../ui';
import Filters, { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import OccTable from '../OccTable';
import { RankedBars } from '../charts';

export default function Q5({ lw }) {
  const { apply } = useFilters();
  const O = SOW.opp;
  const top = O.top;
  // Filters narrow the scored list; the composite itself is unchanged.
  const shown = apply(O.top.map((r) => ({ ...r, f: r.fam })));
  const tierLead = {};
  TIER_ORDER.forEach((t) => {
    if (O.byTier[t] && O.byTier[t].length) tierLead[t] = O.byTier[t][0];
  });

  return (
    <>
      <VHead
        title="Opportunity index"
      >
        Occupations scored on scale, growth, advertised demand and pay, at each level of educational accessibility.
      </VHead>

      <ActiveFilters />

      <Callout label="How the index is built">
        <p>
          Four components, <N>25%</N> each: employment, projected change 2025&ndash;2030,
          postings per 100 jobs, and median pay. Each occupation is ranked by percentile
          within every component and the index is the mean of those four ranks. Only
          occupations with at least <N>100</N> jobs and a published wage are scored.
        </p>
        <p>
          The four measure different things: their strongest mutual correlation is{' '}
          <N>0.39</N>, and effective influence spans <N>18.6%</N> to <N>29.4%</N> against a
          nominal <N>25%</N>. Living-wage ratios and absolute openings are reported per
          occupation but are not part of the score.
        </p>
      </Callout>

      <Filters shown={shown.length} total={O.top.length} note="of the top 30 scored" showFamilies />

      <Panel
        title="Highest-scoring occupations"
        cap={`Composite of four percentile ranks at ${O.weightEach}% each. Hover for the full breakdown — the score is simply the mean of those four numbers.`}
        src={`Lightcast · mean of four percentile ranks at ${O.weightEach}% each · occupations with ≥${O.minJobs} jobs (${fmt(O.nEligible)} of 798)`}
      >
        <RankedBars
          rows={shown.slice(0, 20).map((r) => ({
            label: r.n,
            value: r.sc,
            color: '--s1',
            dec: 1,
            extra: [
              ['Jobs', fmt(r.j)],
              ['Median earnings', money(r.m)],
              ['25th percentile', money(r.p25)],
              ['Median vs living wage', r.lw + '×'],
              ['p25 vs living wage', r.lw25 + '×'],
              ['Annual openings (context only)', fmt(r.o) + ' (' + r.op + ' per 100 jobs)'],
              ['Postings per 100 jobs', r.pp],
              ['5-yr growth', r.g + '%'],
              ['Entry credential', r.t],
              [`— scored components, ${O.weightEach}% each —`, ''],
              ['Employment', r.s_size],
              ['Growth', r.s_growth],
              ['Postings intensity', r.s_postings],
              ['Median pay', r.s_pay],
            ],
          }))}
          opts={{
            dec: 1,
            labelWidth: 262,
            max: 100,
            valueLabel: 'Opportunity score',
            aria: 'Highest-scoring occupations',
          }}
        />
      </Panel>

      {TIER_ORDER.filter((t) => O.byTier[t]).map((t) => (
        <Panel
          key={t}
          title={'Strongest opportunities — ' + t}
          cap={`Top ${O.byTier[t].length} by composite score within this entry-credential tier.`}
          src="Lightcast · same four-indicator composite, ranked within tier · openings shown for context, not scored"
        >
          <Table
            cols={[
              'Occupation',
              'Score',
              'Jobs',
              'Median',
              'Median vs LW',
              'Postings /100',
              '5-yr growth',
              'Annual openings',
            ]}
            rows={O.byTier[t].map((r) => ({
              cells: [
                r.n,
                r.sc.toFixed(1),
                fmt(r.j),
                money(r.m),
                r.lw + '×',
                r.pp,
                r.g + '%',
                fmt(r.o),
              ],
            }))}
          />
        </Panel>
      ))}
      <OccTable lw={lw} />
    </>
  );
}
