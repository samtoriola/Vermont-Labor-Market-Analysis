'use client';

import { SOW, LC } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Callout, Panel, Table, QHead, N } from '../ui';
import { RankedBars } from '../charts';

export default function Q7() {
  const R = SOW.regions.slice();
  const byBa = R.slice().sort((a, b) => b.ba - a.ba);
  const byLw = R.slice().sort((a, b) => b.lwH - a.lwH);
  const byInc = R.slice().sort((a, b) => (b.incLw || 0) - (a.incLw || 0));
  const tightest = byInc[byInc.length - 1];
  const loosest = byInc[0];

  return (
    <>
      <QHead n={7}>
        How does labor market opportunity vary across Vermont&rsquo;s regions, including differences
        in occupational demand, wage sufficiency, educational attainment, and occupation-specific
        wage premiums?
      </QHead>

      <Answer label="Answer — two of four dimensions">
        <p>
          <strong>Educational attainment varies enormously across Vermont.</strong> The share of
          25&ndash;64-year-olds holding a bachelor&rsquo;s degree or higher runs from{' '}
          <N>{byBa[0].ba}%</N> in {byBa[0].c} County to <N>{byBa[byBa.length - 1].ba}%</N> in{' '}
          {byBa[byBa.length - 1].c} &mdash; a{' '}
          <N>{(byBa[0].ba - byBa[byBa.length - 1].ba).toFixed(1)}-point</N> spread within one small
          state.
        </p>
        <p>
          <strong>Wage sufficiency varies far less, and not in the same pattern.</strong> The
          single-adult living wage ranges only <N>${byLw[byLw.length - 1].lwH.toFixed(2)}</N> to{' '}
          <N>${byLw[0].lwH.toFixed(2)}</N> per hour across the 14 counties. Because the cost floor
          is nearly flat while incomes are not, the binding constraint is earnings, not cost of
          living. {tightest.c} County has the tightest margin: median household income of{' '}
          <N>{money(tightest.inc)}</N> against a living wage of <N>{money(tightest.lwA)}</N>, a
          ratio of <N>{tightest.incLw}×</N> &mdash; against <N>{loosest.incLw}×</N> in {loosest.c}.
        </p>
        <p>
          Attainment and cost do not move together, so a high-attainment county is not automatically
          a high-opportunity one, and the counties furthest from self-sufficiency are not the most
          expensive &mdash; they are the lowest-earning.
        </p>
      </Answer>

      <Callout label="The demand half of this question is unanswered">
        <p>
          Both Lightcast exports are <strong>statewide only</strong>, and CPS resolves Vermont to
          metro/non-metro and nothing finer. So occupational demand by region, and
          occupation-specific wage premiums by region, cannot be computed from the data loaded here
          &mdash; two of this question&rsquo;s four dimensions are missing.
        </p>
        <p>
          Closing it needs county-level occupation data. Lightcast Core LMI in the warehouse covers
          all 14 Vermont counties (<code>areaid</code> 50001&ndash;50027) with occupation
          employment, earnings and projections, which would answer it fully. A county-level
          Lightcast export would do the same. Note also that county regions and the ACS PUMA
          geography used for microdata attainment do not nest cleanly, which is a live decision for
          SOW section 7&rsquo;s regional definitions.
        </p>
      </Callout>

      <Panel
        title="Bachelor's attainment by county"
        cap="Share of the 25–64 population holding a bachelor's degree or higher."
        src="ACS 2016–2020 5-year county tables · bachelors_degree_or_higher_25_64 ÷ pop_25_64"
      >
        <RankedBars
          rows={byBa.map((r) => ({
            label: r.c,
            value: r.ba,
            color: '--s1',
            mode: 'pct',
            extra: [
              ['Population', fmt(r.pop)],
              ['Median household income', money(r.inc)],
              ['Living wage (1 adult)', '$' + r.lwH.toFixed(2) + '/hr'],
              ['Income ÷ living wage', r.incLw + '×'],
            ],
          }))}
          opts={{
            mode: 'pct',
            labelWidth: 148,
            valueLabel: 'BA+ share, 25–64',
            aria: "Bachelor's attainment by county",
          }}
        />
      </Panel>

      <Panel
        title="Median household income against the local living wage"
        cap="How far a typical household sits above the single-adult self-sufficiency threshold in its own county. Values near 1.0 mean the median household is close to the floor."
        src={`ACS median household income ÷ MIT living wage 2025, single adult, annualised at ${fmt(LC.hours)} hours · household income vs a single-adult threshold is indicative, not a like-for-like comparison`}
      >
        <RankedBars
          rows={byInc.map((r) => ({
            label: r.c,
            value: r.incLw,
            color: r.incLw >= 1.25 ? '--s3' : '--s2',
            dec: 2,
            extra: [
              ['Median household income', money(r.inc)],
              ['Living wage, annualised', money(r.lwA)],
              ['BA+ share', r.ba + '%'],
              ['Population', fmt(r.pop)],
            ],
          }))}
          opts={{
            dec: 2,
            labelWidth: 148,
            rule: 1,
            ruleLabel: 'Parity',
            valueLabel: 'Income ÷ living wage',
            aria: 'Median income relative to living wage by county',
          }}
        />
      </Panel>

      <Panel
        title="All 14 counties"
        cap="Population, attainment, income and the local cost floor side by side."
        src="ACS 2016–2020 5-year · MIT Living Wage 2025 · sorted by population"
      >
        <Table
          cols={[
            'County',
            'Population',
            'BA+ 25–64',
            'Median income',
            'Living wage /hr',
            'Living wage /yr',
            'Income ÷ LW',
          ]}
          rows={R.map((r) => ({
            cells: [
              r.c,
              fmt(r.pop),
              r.ba + '%',
              money(r.inc),
              '$' + r.lwH.toFixed(2),
              money(r.lwA),
              r.incLw + '×',
            ],
          }))}
        />
      </Panel>
    </>
  );
}
