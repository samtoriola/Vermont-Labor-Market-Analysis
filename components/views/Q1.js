'use client';

import {
  DATA, LC, PCT, TOTJ, TIER_ORDER, SERIES, COMPARE,
  lwAnnual, occByFamily, wageStats, occDots, compareCol,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { familyCols, sectorCols } from '@/lib/tables';
import { Panel, Legend, Ranked, Table, VHead, N, DrillHint } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { occDotTip } from '../occCols';
import { RankedBars, StackedRows } from '../charts';
import Sections from '../Sections';
import { credentialSpread, familyConcentration, topConcentration, vsNation } from '@/lib/insight';
import { DotRows, DotLegend } from '../dots';

export default function Q1({ lw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  const famDrill = (f) =>
    open(
      occDrill({
        label: 'Occupational family',
        title: f.f,
        cap: 'Every detailed occupation in this family, largest first.',
        occ: occByFamily(f.f),
        lwAnnual: LWA,
        extraStats: [['Annual openings', fmt(f.open)]],
      })
    );
  const fams = LC.families;

  // One dot per occupation, placed at its own median pay and sized by employment.
  // The solid line is the employment-weighted average, the dashed line the median:
  // where they separate, a few well-paid occupations are carrying the family.
  const famDots = fams
    .map((r) => {
      const occ = occByFamily(r.f);
      const st = wageStats(occ);
      return {
        label: r.f,
        dots: occDots(occ),
        avg: st.avg,
        med: st.med,
        color: st.med >= LWA ? '--s3' : '--s2',
        onClick: () => famDrill(r),
      };
    })
    .filter((r) => r.dots.length)
    .sort((a, b) => b.avg - a.avg);

  // Reference rows: the state as a whole, the nearest comparable state, the nation.
  const famRefs = ['Vermont', 'New Hampshire', 'United States']
    .map(compareCol)
    .filter(Boolean);

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
      <VHead
        title="Employment structure"
      >
        Who employs Vermonters, what do those jobs pay, and what do they ask for at the door?
      </VHead>

      <Sections
        id="structure"
        active={section}
        items={[
          {
            id: 'sectors',
            label: 'Industry sectors',
            render: () => (
              <Panel
                title="Which industries employ Vermonters?"
                note={topConcentration(LC.sectors, TOTJ)}
                cap={`The same ${fmt(TOTJ)} jobs, grouped by industry, with average earnings per job.`}
                src="Vermont industry data, 2025 · 947 detailed industries rolled up to sector"
                data={{ cols: sectorCols(), rows: LC.sectors, label: 'industries',
                        initialSort: { k: 'j', dir: -1 }, unit: 'industries' }}
              >
                <Ranked id="q1-sectors" rows={LC.sectors}>
                  {(pick) => (
                <RankedBars
                  rows={pick.map((r) => ({
                    label: r.s,
                    value: r.j,
                    color: '--s3',
                    extra: [
                      ['Share of jobs', r.share + '%'],
                      ['Avg. earnings per job', r.earn ? money(r.earn) : '—'],
                      ['Industries in this sector', fmt(r.nnaics)],
                    ],
                  }))}
                  opts={{ labelWidth: 236, aria: 'Jobs by industry sector' }}
                />
                  )}
                </Ranked>
              </Panel>
            ),
          },
          {
            id: 'jobs',
            label: 'Jobs by family',
            render: () => (
              <Panel
                title="Which occupational families employ the most Vermonters?"
                note={familyConcentration(fams, TOTJ)}
                src={`Vermont occupation data, 2025 · 22 occupational groups · ${fmt(TOTJ)} jobs`}
                data={{ cols: familyCols(LWA), rows: fams, label: 'jobs-by-type-of-work',
                        initialSort: { k: 'jobs', dir: -1 }, onRowClick: famDrill,
                        unit: 'kinds of work',
                        note: 'Click a row for the occupations behind it.' }}
              >
                <DrillHint />
                <Ranked id="q1-jobs" rows={fams}>
                  {(pick) => (
                <RankedBars
                  rows={pick.map((r) => ({
                    label: r.f,
                    value: r.jobs,
                    color: '--s1',
                    onClick: () => famDrill(r),
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
                  )}
                </Ranked>
              </Panel>
            ),
          },
          {
            id: 'pay',
            label: 'Median pay',
            render: () => (
              <Panel
                title="What does each occupational family pay?"
                note={vsNation(COMPARE.areas)}
                cap="Green rows clear the living wage at the typical job, amber ones do not. Click a row for the occupations behind it."
                src={`Vermont occupation data, 2025 · reference rows from published state and national wage data · living-wage benchmark 2025, ${lw}`}
                data={{ cols: familyCols(LWA), rows: fams, label: 'pay-by-type-of-work',
                        initialSort: { k: 'med', dir: -1 }, onRowClick: famDrill,
                        unit: 'kinds of work',
                        note: 'Click a row for the occupations behind it.' }}
              >
                <DotLegend unit="one occupation" />
                <Ranked id="q1-pay" rows={famDots}>
                  {(pick) => (
                <DotRows
                  rows={pick.concat(famRefs)}
                  opts={{
                    xMax: COMPARE.yMax,
                    rule: LWA,
                    ruleLabel: 'Living wage ' + money(LWA),
                    dotTip: occDotTip(LWA),
                    aria: 'Median pay of every occupation, grouped by family',
                  }}
                />
                  )}
                </Ranked>
              </Panel>
            ),
          },
          {
            id: 'credential',
            label: 'Entry credential',
            render: () => (
              <Panel
                title="What credential does each family ask for at entry?"
                note={credentialSpread(fams)}
                cap="What the job asks for at the door, not what the people doing it hold."
                src="Vermont occupation data, 2025 · entry credential, weighted by jobs"
                data={{ cols: familyCols(LWA), rows: fams, label: 'entry-credential-by-type-of-work',
                        initialSort: { k: 'jobs', dir: -1 }, onRowClick: famDrill,
                        unit: 'kinds of work' }}
              >
                <Legend labels={TIER_ORDER} colors={SERIES} />
                <Ranked id="q1-cred" rows={credRows}>
                  {(pick) => (
                <StackedRows
                  rows={pick}
                  opts={{
                    rightLabel: 'BA+',
                    tierNames: TIER_ORDER,
                    aria: 'Entry credential mix by family',
                  }}
                />
                  )}
                </Ranked>
              </Panel>
            ),
          },
        ]}
      />
    </>
  );
}
