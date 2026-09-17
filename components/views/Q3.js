'use client';

import { DATA, LC, TOTJ } from '@/lib/data';
import { fmt } from '@/lib/format';
import { Answer, Callout, Panel, Legend, VHead, N } from '../ui';
import { RankedBars, GroupedBars, Dumbbell } from '../charts';

export default function Q3() {
  const fams = LC.families.slice();
  const totPost = fams.reduce((a, r) => a + r.post, 0);
  const totOpen = fams.reduce((a, r) => a + r.open, 0);

  const align = fams.map((r) => ({
    f: r.f,
    jobsSh: (r.jobs / TOTJ) * 100,
    postSh: (r.post / totPost) * 100,
    openSh: (r.open / totOpen) * 100,
    g5pct: r.g5pct,
    jobs: r.jobs,
    idx: r.post / totPost / (r.jobs / TOTJ),
  }));
  const hot = align.slice().sort((a, b) => b.idx - a.idx);
  const growers = fams
    .filter((r) => r.g5pct !== null)
    .sort((a, b) => b.g5pct - a.g5pct);
  const g5Total = fams.reduce((a, r) => a + r.g5, 0);
  const shrinking = growers.filter((r) => r.g5pct < 0).length;

  const cpsRows = DATA.families
    .map((f) => {
      const t = DATA.famTrend[f.f] || {};
      const a = (t[2021] || {}).e || 0;
      const b = (t[2025] || {}).e || 0;
      const na = (t[2021] || {}).n || 0;
      const nb = (t[2025] || {}).n || 0;
      const sea = na ? a / Math.sqrt(na) : 0;
      const seb = nb ? b / Math.sqrt(nb) : 0;
      return {
        label: f.f,
        a,
        b,
        na,
        nb,
        sig: Math.abs(b - a) > 1.96 * Math.sqrt(sea * sea + seb * seb),
      };
    })
    .sort((x, y) => y.b - y.a - (x.b - x.a));

  return (
    <>
      <VHead
        title="Employer demand and growth"
      >
        Where projected growth, annual openings and advertised demand concentrate — and how closely each tracks the existing employment base.
      </VHead>

      <Answer>
        <p>
          <strong>The three measures do not point at the same places.</strong> Postings demand is
          most over-represented in {hot[0].f} (<N>{hot[0].idx.toFixed(2)}×</N> its employment share)
          and {hot[1].f} (<N>{hot[1].idx.toFixed(2)}×</N>), while the most under-represented is{' '}
          {hot[hot.length - 1].f} at <N>{hot[hot.length - 1].idx.toFixed(2)}×</N>.
        </p>
        <p>
          Projected growth is concentrated differently again: {growers[0].f} leads at{' '}
          <N>{growers[0].g5pct}%</N> over five years, and {shrinking} of {growers.length} families
          are projected to shrink. Statewide, jobs grow from <N>{fmt(TOTJ)}</N> toward{' '}
          <N>{fmt(TOTJ + g5Total)}</N> by 2030 &mdash; roughly{' '}
          <N>{((g5Total / TOTJ) * 100).toFixed(1)}%</N> over the window, which is slow growth
          rather than expansion.
        </p>
        <p>
          Against that, the <strong>observed</strong> base moved differently again: Vermont
          actually added <N>{fmt(TOTJ - LC.jobs21)}</N> jobs between 2021 and 2025 (
          <N>+{((TOTJ / LC.jobs21 - 1) * 100).toFixed(1)}%</N>), faster than the forward projection
          anticipates. Recent history and the forecast are telling different stories, so treat the
          projection as the conservative case.
        </p>
        <p>
          Read the alignment index as a screening device, not a verdict: postings skew toward
          occupations that recruit online and churn often, so a high index can mean genuine unmet
          demand or simply high turnover.
        </p>
      </Answer>

      <Callout label="How openings are defined here">
        <p>
          Openings are Lightcast&rsquo;s own <strong>{LC.window} Openings</strong> figure &mdash;{' '}
          <N>{fmt(LC.openTotal)}</N> across the window &mdash; divided by <N>{LC.openYears}</N> to
          give an annual rate of <N>{fmt(LC.openTotal / LC.openYears)}</N>, or{' '}
          <N>{((LC.openTotal / LC.openYears / TOTJ) * 100).toFixed(1)}%</N> of employment. That
          divisor is the one assumption here; change it and every openings figure scales linearly.
        </p>
        <p>
          Do not confuse this with <strong>separations</strong>, which Lightcast also reports (
          <N>{fmt(LC.sepTotal)}</N> in 2025, <N>{LC.sepPct}%</N> of employment). Separations include
          job-to-job transfers, so they measure churn rather than hiring need and run roughly four
          times the openings figure. Openings is the measure to use for demand.
        </p>
      </Callout>

      <Panel
        title="Three measures of demand, against the employment base"
        cap="Each family's share of jobs, of annual openings, and of unique postings. Where the bars diverge, the measures disagree."
        src={`Lightcast · postings window ${LC.postWindow} · shares within each measure sum to 100%`}
      >
        <Legend
          labels={['Share of jobs', 'Share of annual openings', 'Share of postings']}
          colors={['--s1', '--s4', '--s3']}
        />
        <GroupedBars
          rows={align
            .slice()
            .sort((a, b) => b.jobsSh - a.jobsSh)
            .map((r) => ({
              label: r.f,
              parts: [{ v: r.jobsSh }, { v: r.openSh }, { v: r.postSh }],
              extra: [
                ['Jobs share', r.jobsSh.toFixed(1) + '%'],
                ['Openings share', r.openSh.toFixed(1) + '%'],
                ['Postings share', r.postSh.toFixed(1) + '%'],
              ],
            }))}
          opts={{
            colors: ['--s1', '--s4', '--s3'],
            aria: 'Jobs, openings and postings shares by family',
          }}
        />
      </Panel>

      <Panel
        title="Postings demand relative to employment share"
        cap="The alignment index: a family's share of postings divided by its share of jobs. Above 1.0 means employers advertise more than the employment base would predict."
        src={`Lightcast · ${fmt(totPost)} unique postings over ${LC.postWindow}`}
      >
        <RankedBars
          rows={hot.map((r) => ({
            label: r.f,
            value: r.idx,
            color: r.idx >= 1 ? '--s3' : '--s2',
            dec: 2,
            extra: [
              ['Postings share', r.postSh.toFixed(1) + '%'],
              ['Jobs share', r.jobsSh.toFixed(1) + '%'],
              ['Jobs', fmt(r.jobs)],
            ],
          }))}
          opts={{
            dec: 2,
            rule: 1,
            ruleLabel: 'Parity',
            valueLabel: 'Index',
            aria: 'Postings alignment index',
          }}
        />
      </Panel>

      <Panel
        title="Observed change, 2021–2025"
        cap="What actually happened over the study window, by family — the anchor any projection or postings measure should be read against."
        src="Lightcast · 2021 Jobs vs 2025 Jobs, both from the occupation export"
      >
        <RankedBars
          rows={fams
            .filter((r) => r.chgPct !== null)
            .sort((a, b) => b.chgPct - a.chgPct)
            .map((r) => ({
              label: r.f,
              value: r.chgPct,
              color: r.chgPct >= 0 ? '--s3' : '--s2',
              mode: 'pct',
              extra: [
                ['2021 jobs', fmt(r.jobs21)],
                ['2025 jobs', fmt(r.jobs)],
                ['Change', (r.chg >= 0 ? '+' : '') + fmt(r.chg) + ' jobs'],
                ['Annual openings', fmt(r.open)],
              ],
            }))}
          opts={{
            mode: 'pct',
            signed: true,
            valueLabel: '2021–25 change',
            aria: 'Observed change 2021 to 2025 by family',
          }}
        />
      </Panel>

      <Panel
        title="Projected growth, 2025–2030"
        cap="Five-year projected change in jobs by family. Negative bars are projected contraction."
        src="Lightcast · 2030 Jobs vs 2025 Jobs"
      >
        <RankedBars
          rows={growers.map((r) => ({
            label: r.f,
            value: r.g5pct,
            color: r.g5pct >= 0 ? '--s3' : '--s2',
            mode: 'pct',
            extra: [
              ['2025 jobs', fmt(r.jobs)],
              ['Projected change', fmt(r.g5) + ' jobs'],
              ['Annual openings', fmt(r.open)],
            ],
          }))}
          opts={{
            mode: 'pct',
            signed: true,
            valueLabel: '5-yr growth',
            aria: 'Projected five-year growth by family',
          }}
        />
      </Panel>

      <Panel
        title="Independent cross-check: what CPS actually observed"
        cap="Lightcast projections are modelled. CPS is a survey of what happened. Changes marked “ns” are not distinguishable from zero at 95% — which is most of them, so read this as corroboration of direction only."
        src="CPS · 2025 is an 11-month average · SE of a weighted total approximated as e/√n at design effect ≈ 1"
      >
        <Legend labels={['2021', '2025']} colors={['--s3', '--s1']} />
        <Dumbbell rows={cpsRows} />
      </Panel>
    </>
  );
}
