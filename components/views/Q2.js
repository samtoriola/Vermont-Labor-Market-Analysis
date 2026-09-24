'use client';

import {
  LC, PCT, COMPARE, PEOPLE, SIZE_ORDER,
  lwAnnual, wageStats, occDots, occBySize, compareCol,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Panel, Table, VHead, LwPicker, N, DrillHint } from '../ui';
import Filters, { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import OccTable from '../OccTable';
import { useDrill, occDrill } from '../Drill';
import { occDotTip, personTip } from '../occCols';
import { RankedBars, Scatter } from '../charts';
import { DotColumns, DotLegend, PercentileLadder, LadderLegend } from '../dots';

export default function Q2({ lw, setLw }) {
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

  // The occupation dots above are job-level: what a role pays. These are people --
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
        Which occupations employ the most Vermonters, and how pay compares with a self-sufficiency benchmark across large, medium and smaller occupations.
      </VHead>

      <ActiveFilters />

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
        title="Where pay sits, by occupation size"
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

      <Panel
        title="What people actually earn"
        cap="The chart above is about jobs; this one is about people. Every dot is one Vermont wage and salary worker who answered the American Community Survey, placed at their own wage income for the year. The self-employed and military occupations are excluded, which keeps this on the same footing as the occupation charts above. Dots are a random draw made in proportion to survey weight, so the cloud reflects the population rather than the raw respondent mix — but the average and median lines are computed from every respondent, not just the dots shown."
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
        title="The 25 largest occupations — mean against median"
        cap="The line spans the 10th to 90th percentile, the thick middle the 25th to 75th. The solid dot is the median and the hollow ring the mean. Wherever the ring sits to the right of the dot, a long upper tail is lifting the average above what a typical worker earns — the reason an average alone is a poor guide to pay. Where the whole line falls left of the living-wage mark, most people in that occupation earn below self-sufficiency, not just the bottom tail."
        src={`BLS OEWS Vermont 2025 · ${ladderMu} of ${ladder.length} shown with a published mean · living wage: MIT 2025, ${lw}`}
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

      <Filters shown={filtered.length} total={LC.allOcc.length} showFamilies />

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
      <OccTable lw={lw} />
    </>
  );
}
