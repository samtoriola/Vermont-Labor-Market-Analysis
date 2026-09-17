'use client';

import { useState } from 'react';
import { SOW, TIER_ORDER, lwAnnual, filterOcc } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Callout, Panel, Table, VHead, N } from '../ui';
import Filters from '../Filters';
import { RankedBars } from '../charts';

export default function Q5({ lw }) {
  const LWA = lwAnnual(lw);
  const [f, setF] = useState({ tiers: [], wage: 'all', minJobs: 0 });
  const O = SOW.opp;
  const top = O.top;
  // Filters narrow the scored list; the composite itself is unchanged.
  const shown = filterOcc(
    O.top.map((r) => ({ ...r, lwAnnual: LWA })),
    { ...f, lwAnnual: LWA }
  );
  const baCount = top.filter((r) => r.t === "Bachelor's").length;
  const tierLead = {};
  TIER_ORDER.forEach((t) => {
    if (O.byTier[t] && O.byTier[t].length) tierLead[t] = O.byTier[t][0];
  });
  const spotlight = top[6] || top[top.length - 1];

  return (
    <>
      <VHead
        title="Where the opportunity is"
      >
        Occupations combining scale, growth, advertised demand and pay — scored transparently, and read at each level of educational accessibility.
      </VHead>

      <Answer>
        <p>
          Scoring all <N>{fmt(O.nEligible)}</N> Vermont occupations with at least {O.minJobs} jobs
          on four indicators weighted <N>{O.weightEach}%</N> each &mdash; employment, projected
          growth, postings per 100 jobs and median earnings &mdash; the highest-scoring are{' '}
          {top[0].n} (<N>{top[0].sc}</N>), {top[1].n} (<N>{top[1].sc}</N>) and {top[2].n} (
          <N>{top[2].sc}</N>).
        </p>
        <p>
          Postings are expressed <strong>per 100 jobs</strong> rather than as a raw count, so a
          large occupation does not score twice for being large &mdash; employment already has its
          own component. {spotlight.n} is the clearest case: only the{' '}
          <N>{spotlight.s_size}th</N> percentile on employment, but the{' '}
          <N>{spotlight.s_postings}th</N> on postings intensity, which a volume-based measure would
          have buried.
        </p>
        <p>
          <strong>The ranking tilts heavily toward bachelor&rsquo;s-entry work</strong> &mdash;{' '}
          <N>{baCount}</N> of the top <N>{top.length}</N>. That tilt is a finding, not an artefact:
          with each component verified to carry independent signal, higher-credential occupations
          genuinely lead on the combination of pay, growth and advertised demand. It also grew when
          the openings component was removed, because openings intensity was the one indicator that
          favoured high-turnover low-wage work. The tier-by-tier tables below are therefore the more
          actionable view for VSCS, since they ask what is strongest{' '}
          <em>at each level of educational accessibility</em>.
        </p>
        <p>
          On that basis the leaders are{' '}
          {TIER_ORDER.filter((t) => tierLead[t]).map((t, i) => (
            <span key={t}>
              {i > 0 ? '; ' : ''}
              <strong>{t}</strong> &mdash; {tierLead[t].n}
            </span>
          ))}
          .
        </p>
        <p>
          The SOW leaves indicator weights and thresholds to VSCS (section 7). These are equal
          weights on percentile ranks: a defensible default and nothing more. Every component score
          is shown so the composite can be audited or reweighted.
        </p>
      </Answer>

      <Callout label="How this index was arrived at">
        <p>It began as six indicators and was cut to four, each removal for a measured reason.</p>
        <p>
          <strong>Earnings relative to the living wage</strong> was dropped because the benchmark is
          a constant, making the ratio a monotonic transform of median pay. The two components were
          rank-identical (<N>r = 1.000</N>), so the wage dimension silently held <N>33%</N> of the
          weight while the sixth component added nothing. Re-measuring adequacy at the 25th
          percentile only brought the correlation to <N>0.966</N> &mdash; still redundant &mdash; so
          the wage dimension is now represented once, by median pay.
        </p>
        <p>
          <strong>Openings</strong> was dropped next. As an absolute count it correlated{' '}
          <N>0.92</N> with employment, double-counting scale. Rebased per 100 jobs it became a
          turnover measure, and in Vermont turnover concentrates in low-wage work &mdash; it
          correlated <N>&minus;0.68</N> with pay, contributed <N>&minus;4.7%</N> of composite
          variance (actively cancelling the other components) and changed only 3 of the top 10.
          Advertised demand is captured more cleanly by postings intensity.
        </p>
        <p>
          What remains: four components whose strongest mutual correlation is <N>0.39</N>, with
          effective influence spanning <N>18.6%</N> to <N>29.4%</N> against a nominal{' '}
          <N>25%</N> &mdash; close enough that equal weighting means what it says. Living-wage
          ratios and absolute openings are still reported per occupation for context; they are
          simply not scored. A growth-only openings series, excluding replacement demand, would be a
          legitimate fifth component if Lightcast can supply one.
        </p>
      </Callout>

      <Filters f={f} setF={setF} shown={shown.length} total={O.top.length} note="of the top 30 scored" />

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
    </>
  );
}
