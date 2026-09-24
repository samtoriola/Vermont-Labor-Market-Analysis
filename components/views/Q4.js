'use client';

import {
  DATA, LC, PCT, TIER_ORDER, SERIES, COMPARE, PEOPLE,
  lwAnnual, occByTier, wageStats, occDots,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, VHead, LwPicker, N, DrillHint } from '../ui';
import { ActiveFilters } from '../Filters';
import { useDrill, occDrill } from '../Drill';
import { occDotTip, personTip } from '../occCols';
import { RankedBars } from '../charts';
import { DotColumns, DotLegend } from '../dots';

export default function Q4({ lw, setLw }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  const tierDrill = (k) =>
    open(
      occDrill({
        label: 'Entry credential',
        title: k,
        cap: 'Every occupation whose typical entry credential is this tier, largest first.',
        occ: occByTier(k),
        lwAnnual: LWA,
      })
    );
  const t = {};
  LC.tiers.forEach((r) => {
    t[r.t] = r;
  });
  const sub = t['Sub-baccalaureate'];
  const ba = t["Bachelor's"];
  const grad = t['Graduate / professional'];
  const lastCps = DATA.trend[DATA.trend.length - 1];
  const P = PCT.tiers;

  // One dot per occupation at each entry-credential tier. The gap between the
  // solid average line and the dashed median line is the thing a box plot hides.
  const tierDots = TIER_ORDER.filter((k) => occByTier(k).length).map((k) => {
    const occ = occByTier(k);
    const st = wageStats(occ);
    return {
      label: k,
      sub: fmt(st.n) + ' occupations',
      dots: occDots(occ),
      avg: st.avg,
      med: st.med,
      color: st.med >= LWA ? '--s3' : '--s2',
      onClick: () => tierDrill(k),
    };
  });

  // The same ladder measured on people rather than jobs: one dot per Vermonter who
  // answered the ACS, grouped by the credential they hold.
  const credPeople = PEOPLE.byCred.map((c) => ({
    label: c.label,
    sub: fmt(c.n) + ' respondents',
    dots: c.dots,
    avg: c.avg,
    med: c.med,
    thin: c.thin,
    color: c.med >= LWA ? '--s3' : '--s2',
  }));


  return (
    <>
      <VHead
        title="Education pathways"
      >
        The share of Vermont employment at each entry credential, and how those requirements relate to earnings.
      </VHead>

      <ActiveFilters />

      <LwPicker value={lw} onChange={setLw} />

      <Panel
        title="The credential ladder, by what the job requires"
        cap="One dot per occupation, placed at its median pay and sized by employment, grouped by the credential the job asks for at entry. The solid line is the employment-weighted average, the dashed line the median. Click a column to list its occupations."
        src="Lightcast · Typical Entry Level Education · every priced Vermont occupation"
      >
        <DotLegend unit="one occupation" />
        <DotColumns
          groups={tierDots}
          opts={{
            yMax: COMPARE.yMax,
            rule: LWA,
            ruleLabel: 'Living wage ' + money(LWA),
            dotTip: occDotTip(LWA),
            aria: 'Median pay of every occupation, by entry-credential tier',
          }}
        />
      </Panel>

      <Panel
        title="The credential ladder, by what people hold"
        cap="The same ladder measured on people instead of jobs. Every dot is one Vermont wage and salary worker who answered the American Community Survey, placed at their own wage income for the year and grouped by the credential they actually hold. The self-employed and military occupations are excluded. Dots are a random draw made in proportion to survey weight; the average and median lines come from every respondent in the column. Columns marked as a small sample rest on fewer than 100 respondents and should be read as indicative."
        src={`IPUMS USA, ACS 1-year 2024 · ${PEOPLE.universe.toLowerCase()} · living wage: MIT 2025, ${lw}`}
      >
        <DotLegend unit="one survey respondent" sized={false} />
        <DotColumns
          groups={credPeople}
          opts={{
            yMax: PEOPLE.yMax,
            rule: LWA,
            ruleLabel: 'Living wage ' + money(LWA),
            dotTip: personTip(LWA),
            aria: 'Earnings of individual survey respondents, by credential held',
          }}
        />
      </Panel>

      <Panel
        title="The credential ladder in full"
        cap={`Employment, the full wage distribution, and demand at each tier. Benchmark: ${lw}.`}
        src="Lightcast · Typical Entry Level Education, jobs-weighted"
      >
        <Table
          cols={[
            'Entry credential',
            'Jobs',
            'Share',
            '10th',
            '25th',
            'Median',
            '75th',
            '90th',
            'Above living wage',
            'Annual openings',
          ]}
          rows={TIER_ORDER.map((k) => {
            const r = t[k];
            const b = P[k] || {};
            return {
              cells: [
                r.t,
                fmt(r.jobs),
                r.share + '%',
                money(b.p10),
                money(b.p25),
                money(b.p50),
                money(b.p75),
                money(b.p90),
                r.above[lw].toFixed(1) + '%',
                fmt(r.open),
              ],
            };
          })}
        />
      </Panel>

      <div className="grid2">
        <Panel
          title="Share of employment"
          cap="Where Vermont's jobs sit on the credential ladder."
          src={`Lightcast · ${fmt(LC.totalJobs)} jobs`}
        >
          <RankedBars
            rows={TIER_ORDER.map((k, i) => {
              const r = t[k];
              return {
                label: r.t,
                value: r.share,
                color: SERIES[i],
                mode: 'pct',
                extra: [
                  ['Jobs', fmt(r.jobs)],
                  ['Occupations', fmt(r.nocc)],
                ],
              };
            })}
            opts={{
              mode: 'pct',
              labelWidth: 176,
              width: 470,
              valueLabel: 'Share of jobs',
              aria: 'Employment share by credential tier',
            }}
          />
        </Panel>

        <Panel
          title="Earnings dispersion"
          cap="The 90th percentile divided by the 10th: the width of the earnings range at each entry credential."
          src="Lightcast · ratio of 90th to 10th percentile"
        >
          <RankedBars
            rows={TIER_ORDER.filter((k) => P[k]).map((k, i) => {
              const b = P[k];
              return {
                label: k,
                value: b.p90 / b.p10,
                color: SERIES[i],
                dec: 2,
                extra: [
                  ['10th percentile', money(b.p10)],
                  ['90th percentile', money(b.p90)],
                  ['Median', money(b.p50)],
                ],
              };
            })}
            opts={{
              dec: 2,
              labelWidth: 176,
              width: 470,
              valueLabel: 'p90 ÷ p10',
              aria: 'Earnings dispersion by credential tier',
            }}
          />
        </Panel>
      </div>

      <Panel
        title="Share of jobs paying above the living wage"
        cap={`The wage-quality payoff to each credential tier. Benchmark: ${lw} at ${money(LWA)}/yr — change it above.`}
        src="Lightcast · MIT Living Wage 2025 · occupation median vs benchmark"
      >
        <RankedBars
          rows={TIER_ORDER.map((k, i) => {
            const r = t[k];
            return {
              label: r.t,
              value: r.above[lw],
              color: SERIES[i],
              mode: 'pct',
              extra: [
                ['Jobs', fmt(r.jobs)],
                ['Median earnings', money(r.med)],
              ],
            };
          })}
          opts={{
            mode: 'pct',
            labelWidth: 176,
            max: 100,
            valueLabel: 'Above living wage',
            aria: 'Living-wage share by credential tier',
          }}
        />
      </Panel>

      <Panel
        title="All eight credential categories"
        cap="The five tiers unpacked into the credential labels Lightcast assigns. Sub-baccalaureate covers three distinct categories."
        src="Lightcast · 2 of 798 occupations carry no education assignment"
      >
        <Table
          cols={[
            'Lightcast entry credential',
            'SOW tier',
            'Jobs',
            'Share',
            'Median earnings',
            'Occupations',
          ]}
          rows={LC.eduDetail.map((r) => ({
            cells: [r.e, r.tier, fmt(r.jobs), r.share + '%', r.med ? money(r.med) : '—', fmt(r.nocc)],
          }))}
        />
      </Panel>

      <Callout label="What this measures">
        <p>
          These are job <em>requirements</em>, not worker <em>attainment</em>: a property of the
          job, not of the person holding it.{' '}
          <N>{(ba.share + grad.share).toFixed(1)}%</N> of Vermont jobs ask for a bachelor&rsquo;s
          or more, while <N>{lastCps.ba.toFixed(1)}%</N> of Vermont workers 25+ hold one, a
          difference of <N>{(lastCps.ba - ba.share - grad.share).toFixed(1)} points</N>. The two
          come from different sources and count different things.
        </p>
      </Callout>
    </>
  );
}
