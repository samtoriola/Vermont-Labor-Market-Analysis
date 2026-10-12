'use client';

import {
  DATA, LC, PCT, TIER_ORDER, SERIES, COMPARE, PEOPLE,
  lwAnnual, occByTier, wageStats, occDots, credentialFunnel,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, VHead, LwPicker, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { occDotTip, personTip } from '../occCols';
import { RankedBars } from '../charts';
import { DotColumns, DotLegend } from '../dots';
import Sections from '../Sections';
import {
  funnelContrast, ladderStep, peopleLadderStep, livingWageJump, largestCategory,
} from '@/lib/insight';

export default function Q4({ lw, setLw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  // Counts occupations, not jobs: the question is whether a credential opens a
  // door, not how many people are already through it.
  const MIN_OPEN = 50;
  const funnel = credentialFunnel(LWA, MIN_OPEN);

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
        What does each level of education lead to in Vermont — how many jobs, and at what pay?
      </VHead>

      <Sections
        id="pathways"
        active={section}
        items={[
          {
            id: 'employment-and-dispersion',
            label: 'Employment and dispersion',
            render: () => (
                <div className="grid2">
                  <Panel
                    title="How much Vermont employment sits at each credential level?"
                    cap="What share of Vermont's jobs ask for each level of education."
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
                        width: 640,
                        valueLabel: 'Share of jobs',
                        aria: 'Employment share by credential tier',
                      }}
                    />
                  </Panel>

                  <Panel
                    title="How wide is the range of outcomes at each credential level?"
                    cap="How many times more the best-paid tenth earn than the worst-paid tenth. A wider range means the credential leads to very different outcomes."
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
                        width: 640,
                        valueLabel: 'Times wider',
                        aria: 'Earnings dispersion by credential tier',
                      }}
                    />
                  </Panel>
                </div>
            ),
          },
          {
            id: 'what-the-job-requires',
            label: 'What the job requires',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="What does each rung pay, by what the job asks for?"
                  note={ladderStep(LC.tiers, TIER_ORDER)}
                  cap="One dot per occupation, placed at its typical pay and sized by how many people it employs, grouped by what the job asks for. The solid line is the average, the dashed line the midpoint. Click a column to list its occupations."
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
              </>
            ),
          },
          {
            id: 'what-people-hold',
            label: 'What people hold',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="What does each rung pay, by the credential workers hold?"
                  note={peopleLadderStep(PEOPLE.byCred)}
                  cap="The same ladder measured on people rather than jobs. Every dot is one Vermonter on a wage or salary who answered the American Community Survey, placed at what they earned and grouped by the credential they hold. The self-employed and the military are left out. The dots are a fair sample; the average and midpoint lines come from everyone in the column. Columns marked as a small sample rest on fewer than 100 answers and are rough."
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
              </>
            ),
          },
          {
            id: 'above-the-living-wage',
            label: 'Above the living wage',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="Which credential levels clear the living wage?"
                  note={livingWageJump(LC.tiers, TIER_ORDER, lw)}
                  cap={`What share of each credential's jobs pay at or above the living wage for ${lw} — ${money(LWA)} a year. Change the household at the top of this tab.`}
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
              </>
            ),
          },
          {
            id: 'which-credentials-pay',
            label: 'Which credentials pay',
            render: () => (
              <>
                <LwPicker value={lw} onChange={setLw} />
              <Panel
                title="Which credentials lead to a job that both hires and pays?"
                cap={`Every Vermont occupation at each credential, narrowed twice: first to those hiring in volume — at least ${MIN_OPEN} openings a year — then to those paying a living wage. These are counts of occupations, not jobs, so it reads as how many doors a credential opens. The last column is each row measured against its own level, not against the others, so the five do not add to 100%. Household: ${lw}.`}
                src={`Lightcast · Typical Entry Level Education · openings ≥ ${MIN_OPEN}/yr · benchmark: MIT Living Wage 2025`}
                note={funnelContrast(funnel)}
              >
                <Table
                  cols={[
                    'Entry credential',
                    'Occupations',
                    `Hiring (${MIN_OPEN}+ openings)`,
                    'Paying a living wage',
                    'Openings',
                    'Share of all openings at this level',
                  ]}
                  rows={funnel.map((r) => ({
                    cells: [
                      r.t,
                      fmt(r.nAll),
                      fmt(r.nHiring),
                      fmt(r.nPaying),
                      fmt(r.open),
                      r.shareOpen === null ? '\u2014' : r.shareOpen.toFixed(1) + '%',
                    ],
                  }))}
                />
              </Panel>
              </>
            ),
          },
          {
            id: 'what-this-measures',
            label: 'What this measures',
            render: () => (
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
            ),
          },
        ]}
      />
    </>
  );
}
