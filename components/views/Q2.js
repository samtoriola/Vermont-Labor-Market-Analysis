'use client';

import { useState } from 'react';
import { LC, PCT, lwAnnual, filterOcc, occByTier } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Panel, Table, VHead, LwPicker, N, DrillHint } from '../ui';
import Filters from '../Filters';
import { useDrill, occDrill } from '../Drill';
import { RankedBars, BoxPlot, BoxLegend, Scatter } from '../charts';

export default function Q2({ lw, setLw }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const [f, setF] = useState({ tiers: [], wage: 'all', minJobs: 0 });
  const filtered = filterOcc(LC.allOcc, { ...f, lwAnnual: LWA });

  const sizeDrill = (tier) => {
    const lo = tier === 'Large (2,000+)' ? 2000 : tier === 'Medium (500-2,000)' ? 500 : 0;
    const hi = tier === 'Large (2,000+)' ? Infinity : tier === 'Medium (500-2,000)' ? 2000 : 500;
    open(
      occDrill({
        label: 'Occupation size',
        title: tier,
        cap: 'Every occupation in this size band, largest first.',
        occ: LC.allOcc.filter((o) => o.j >= lo && o.j < hi).sort((a, b) => b.j - a.j),
        lwAnnual: LWA,
      })
    );
  };
  const sz = LC.sizeTiers;
  const [big, mid, small] = sz;
  const top = LC.topOcc.slice(0, 25);

  const szBox = sz
    .filter((r) => PCT.sizeTiers[r.s])
    .map((r) => {
      const b = PCT.sizeTiers[r.s];
      return {
        label: r.s,
        p10: b.p10,
        p25: b.p25,
        p50: b.p50,
        p75: b.p75,
        p90: b.p90,
        color: '--s1',
        extra: [
          ['Occupations', fmt(r.nocc)],
          ['Jobs', fmt(r.jobs)],
          ['Share of employment', r.share + '%'],
          ['Above living wage', r.above[lw].toFixed(1) + '%'],
        ],
      };
    });

  const occBox = top
    .filter((r) => PCT.occ[r.soc])
    .map((r) => {
      const b = PCT.occ[r.soc];
      const belowLabel =
        b.p25 >= LWA ? 'under 25%' : b.p50 >= LWA ? '25–50%' : b.p75 >= LWA ? '50–75%' : 'over 75%';
      return {
        label: r.n,
        p10: b.p10,
        p25: b.p25,
        p50: b.p50,
        p75: b.p75,
        p90: b.p90,
        color: b.p50 >= LWA ? '--s3' : '--s2',
        extra: [
          ['Jobs', fmt(r.j)],
          ['SOC', r.soc],
          ['Entry education', r.e],
          ['Share below living wage', belowLabel],
        ],
      };
    });

  return (
    <>
      <VHead
        title="Occupation size and wage quality"
      >
        Which occupations employ the most Vermonters, and how pay compares with a self-sufficiency benchmark across large, medium and smaller occupations.
      </VHead>

      <Answer>
        <p>
          <strong>Wage quality runs opposite to occupation size.</strong> Vermont&rsquo;s{' '}
          <N>{big.nocc}</N> largest occupations (2,000+ jobs each) hold <N>{big.share.toFixed(1)}%</N>{' '}
          of all employment at a median of <N>{money(big.med)}</N>, and only{' '}
          <N>{big.above[lw].toFixed(0)}%</N> of those jobs clear the living wage. The{' '}
          <N>{small.nocc}</N> smaller occupations pay a median of <N>{money(small.med)}</N>, with{' '}
          <N>{small.above[lw].toFixed(0)}%</N> clearing it.
        </p>
        <p>
          So the occupations that employ the most Vermonters are systematically the ones least
          likely to pay a self-sufficient wage. That is the central tension in this question: scale
          and wage quality point in opposite directions, and a program strategy aimed only at the
          biggest occupations would concentrate graduates in the weakest-paying part of the market.
        </p>
        <p>
          The percentile spread sharpens this. Large occupations are not just lower-paid, they are{' '}
          <strong>compressed</strong>: their 90th percentile (
          <N>{money(PCT.sizeTiers[big.s].p90)}</N>) barely clears the <em>median</em> of the medium
          tier (<N>{money(PCT.sizeTiers[mid.s].p50)}</N>). Someone at the top of a large Vermont
          occupation earns about what a typical worker in a mid-sized one earns. There is limited
          upside inside the biggest occupations, which matters more for program design than the
          median gap alone suggests.
        </p>
        <p>
          The benchmark matters, so it is a control rather than an assumption &mdash; SOW section 7
          leaves the choice to VSCS. Switch household type below and every wage-quality figure on
          this page updates.
        </p>
      </Answer>

      <LwPicker value={lw} onChange={setLw} />

      <Panel
        title="Share of jobs above the living wage, by occupation size"
        cap={`The inverse relationship, stated directly. Benchmark: ${lw} at ${money(LWA)}/yr.`}
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

      <Panel
        title="Earnings distribution by occupation size"
        cap="The same inverse relationship, now with spread. The larger the occupation, the lower and tighter its wage distribution — large occupations top out near where medium and smaller ones begin."
        src="Lightcast · employment-weighted mean of occupation percentiles · annual figures as supplied"
      >
        <BoxLegend />
        <BoxPlot
          rows={szBox}
          opts={{
            labelWidth: 196,
            rule: LWA,
            ruleLabel: 'Living wage ' + money(LWA),
            endLabels: true,
            aria: 'Earnings percentile distribution by occupation size tier',
          }}
        />
      </Panel>

      <Panel
        title="Size tiers in full"
        cap="Each tier's scale, pay, spread and demand side by side."
        src="Lightcast · tiers cut at 500 and 2,000 jobs"
      >
        <Table
          cols={[
            'Size tier',
            'Occupations',
            'Jobs',
            'Share',
            '10th',
            '25th',
            'Median',
            '75th',
            '90th',
            'Above living wage',
          ]}
          rows={sz.map((r) => {
            const b = PCT.sizeTiers[r.s] || {};
            return {
              cells: [
                r.s,
                fmt(r.nocc),
                fmt(r.jobs),
                r.share + '%',
                money(b.p10),
                money(b.p25),
                money(b.p50),
                money(b.p75),
                money(b.p90),
                r.above[lw].toFixed(1) + '%',
              ],
            };
          })}
        />
      </Panel>

      <Panel
        title="The 25 largest occupations — employment"
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

      <Panel
        title="The 25 largest occupations — earnings distribution"
        cap="These are true occupation-level percentiles, not weighted means. Where the box sits entirely left of the living-wage line, most people in that occupation earn below self-sufficiency — not just the bottom tail."
        src={`Lightcast · ${fmt(Object.keys(PCT.occ).length)} occupations priced · true occupation percentiles`}
      >
        <BoxLegend />
        <BoxPlot
          rows={occBox}
          opts={{
            labelWidth: 262,
            rule: LWA,
            ruleLabel: 'Living wage',
            aria: 'Earnings percentiles for the 25 largest occupations',
          }}
        />
      </Panel>

      <Filters f={f} setF={setF} shown={filtered.length} total={LC.allOcc.length} />

      <Panel
        title="Every occupation: size against pay"
        cap={`${fmt(filtered.length)} of ${fmt(LC.allOcc.length)} occupations after filters. The vertical line is the living wage. Coloured by size tier.`}
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
    </>
  );
}
