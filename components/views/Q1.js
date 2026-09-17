'use client';

import { DATA, LC, PCT, TOTJ, TIER_ORDER, SER, lwAnnual } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Panel, Legend, Table, QHead, N } from '../ui';
import { RankedBars, StackedRows, BoxPlot, BoxLegend } from '../charts';

export default function Q1({ lw }) {
  const LWA = lwAnnual(lw);
  const fams = LC.families;
  const top3 = fams.slice(0, 3);
  const hiPay = fams.slice().sort((a, b) => (b.med || 0) - (a.med || 0))[0];
  const loPay = fams.filter((r) => r.med).sort((a, b) => a.med - b.med)[0];
  const top3Share = (top3.reduce((a, r) => a + r.jobs, 0) / TOTJ) * 100;

  const famBox = fams
    .filter((r) => PCT.families[r.f])
    .map((r) => {
      const b = PCT.families[r.f];
      return {
        label: r.f,
        p10: b.p10,
        p25: b.p25,
        p50: b.p50,
        p75: b.p75,
        p90: b.p90,
        color: b.p50 >= LWA ? '--s3' : '--s2',
        extra: [
          ['Jobs', fmt(r.jobs)],
          ['Above living wage', r.above[lw] !== null ? r.above[lw] + '% of jobs' : '—'],
          ['Occupations priced', fmt(b.nocc)],
          ['Jobs covered', b.cov + '%'],
        ],
      };
    })
    .sort((a, b) => b.p50 - a.p50);

  const credRows = fams
    .map((r) => {
      const parts = TIER_ORDER.map((t) => ({ v: r.tiers[t] || 0 }));
      const tot = parts.reduce((a, x) => a + x.v, 0);
      return {
        label: r.f,
        parts,
        total: tot,
        hi: ((r.tiers["Bachelor's"] || 0) + (r.tiers['Graduate / professional'] || 0)) / (tot || 1),
      };
    })
    .sort((a, b) => b.hi - a.hi);

  const cpsRows = DATA.families.slice(0, 12).map((f) => {
    const tops = (DATA.famSector[f.f] || []).slice(0, 3);
    return {
      cells: [
        f.f,
        fmt(f.e),
        ...[0, 1, 2].map((i) => (tops[i] ? `${tops[i].s} (${fmt(tops[i].e)})` : '—')),
      ],
    };
  });

  return (
    <>
      <QHead n={1}>
        How is Vermont employment distributed across occupational families, and how does that
        distribution vary by industry, earnings, and typical entry-level education?
      </QHead>

      <Answer>
        <p>
          Vermont employment is <strong>broad, not concentrated</strong>. The three largest
          families &mdash;{' '}
          {top3.map((r, i) => (
            <span key={r.f}>
              {i > 0 ? ', ' : ''}
              {r.f} (<N>{fmt(r.jobs)}</N>)
            </span>
          ))}{' '}
          &mdash; hold just <N>{top3Share.toFixed(1)}%</N> of jobs between them, and the largest
          single family is only <N>{((fams[0].jobs / TOTJ) * 100).toFixed(1)}%</N>.
        </p>
        <p>
          <strong>Earnings vary far more than size does.</strong> Median earnings run from{' '}
          <N>{money(loPay.med)}</N> in {loPay.f} to <N>{money(hiPay.med)}</N> in {hiPay.f} &mdash;
          a {(hiPay.med / loPay.med).toFixed(1)}&times; spread across families of broadly similar
          size. But the spread <em>within</em> Vermont is nearly as wide as the spread between
          families: statewide the 10th percentile is <N>{money(PCT.statewide.p10)}</N> and the 90th
          is <N>{money(PCT.statewide.p90)}</N>, a{' '}
          <N>{(PCT.statewide.p90 / PCT.statewide.p10).toFixed(1)}&times;</N> range. A family median
          alone hides that, which is why the distribution chart below matters more than the ranking.
        </p>
        <p>
          By industry, Health Care &amp; Social Assistance and Educational Services anchor the
          professional families. By entry credential the spread is equally wide, and the two do not
          move together: some large families are majority high-school-entry, others majority BA.
        </p>
      </Answer>

      <Panel
        title="Jobs by occupational family"
        cap="Vermont 2025. Hover for earnings, concentration, openings and change since 2021."
        src={`Lightcast occupation table · 22 SOC major groups · ${fmt(TOTJ)} total jobs`}
      >
        <RankedBars
          rows={fams.map((r) => ({
            label: r.f,
            value: r.jobs,
            color: '--s1',
            extra: [
              ['Median earnings', r.med ? money(r.med) : '—'],
              ['Employment concentration', r.lq !== null ? r.lq + '× US' : '—'],
              ['Change 2021–2025', (r.chg >= 0 ? '+' : '') + fmt(r.chg) + ` (${r.chgPct}%)`],
              ['Annual openings', fmt(r.open)],
              ['Unique postings, 5 yr', fmt(r.post)],
              ['Detailed occupations', fmt(r.nocc)],
            ],
          }))}
          opts={{ aria: 'Jobs by occupational family' }}
        />
      </Panel>

      <Panel
        title="Earnings distribution by family"
        cap="Whiskers span the 10th to 90th percentile, the box the 25th to 75th, the line the median. Green medians clear the living wage, amber do not. Percentiles are the employment-weighted mean of each family's occupation percentiles, not a pooled wage distribution — the spread is indicative of range, not an exact family quantile."
        src={`Lightcast Vermont occupation export · annual percentiles, 100% of jobs priced · benchmark: MIT Living Wage 2025, ${lw}`}
      >
        <BoxLegend />
        <BoxPlot
          rows={famBox}
          opts={{
            rule: LWA,
            ruleLabel: 'Living wage ' + money(LWA),
            aria: 'Earnings percentile distribution by occupational family',
          }}
        />
      </Panel>

      <Panel
        title="Typical entry credential, by family"
        cap="Share of each family's jobs at each entry-credential tier, sorted by the BA+ share. This is the requirement attached to the job, not the credential its workers hold."
        src="Lightcast · Typical Entry Level Education, jobs-weighted"
      >
        <Legend labels={TIER_ORDER} colors={SER} />
        <StackedRows
          rows={credRows}
          opts={{
            rightLabel: 'BA+',
            tierNames: TIER_ORDER,
            aria: 'Entry credential mix by family',
          }}
        />
      </Panel>

      <Panel
        title="Jobs by industry sector"
        cap={`The same ${fmt(TOTJ)} jobs, organised by NAICS sector, with average earnings per job. Levels are 2025; sector-level change over 2021–2025 is not in this export.`}
        src="Lightcast industry table · 947 six-digit NAICS rolled to sector · 2025 levels only: the industry export carries no 2021 column, so sector change over the study window is not available"
      >
        <RankedBars
          rows={LC.sectors.map((r) => ({
            label: r.s,
            value: r.j,
            color: '--s3',
            extra: [
              ['Share of jobs', r.share + '%'],
              ['Avg. earnings per job', r.earn ? money(r.earn) : '—'],
              ['NAICS codes in sector', fmt(r.nnaics)],
            ],
          }))}
          opts={{ labelWidth: 236, aria: 'Jobs by industry sector' }}
        />
      </Panel>

      <Panel
        title="Which industries each family works in"
        cap="Neither Lightcast export carries an occupation-by-industry staffing pattern, so this cross comes from CPS microdata — the only source here that observes both on the same person. Top 12 families by CPS employment."
        src="CPS 2021–2025 pooled · annual-average employment · complementary to the Lightcast levels above"
      >
        <Table
          cols={['Family', 'CPS employment', 'Largest industry', '2nd', '3rd']}
          rows={cpsRows}
        />
      </Panel>
    </>
  );
}
