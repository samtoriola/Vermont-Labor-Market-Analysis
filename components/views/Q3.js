'use client';

import { DATA, DEMAND, LC, ORDINAL, TOTJ } from '@/lib/data';
import { fmt } from '@/lib/format';
import { demandCols, familyCols } from '@/lib/tables';
import { Callout, Panel, Legend, Picker, Ranked, VHead, N } from '../ui';
import { RankedBars, GroupedBars } from '../charts';
import { ColumnStack } from '../columns';
import Sections from '../Sections';
// Legend, GroupedBars and demandDivergence are used only by the hidden
// "Three demand measures" section further down. Kept imported so bringing it back
// is the one edit it should be.
import { demandDivergence, observedSplit, growthSplit, requirementShare } from '@/lib/insight';

// Callout, Legend, N, GroupedBars and demandDivergence below are used only by the section(s) hidden further down. Kept
// imported so restoring one stays a single edit.

const ASKED_MEASURES = [
  { id: 'education', label: 'Education' },
  { id: 'experience', label: 'Experience' },
];

const DEMAND_MEASURES = [
  { id: 'ads', label: 'Job ads' },
  { id: 'observed', label: 'Change since 2021' },
  { id: 'projected', label: 'Projected growth' },
];

export default function Q3({ section }) {
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

  // Three readings of the same 22 kinds of work: who is advertising hardest, who
  // actually grew, and who is expected to. They were three sections, which made a
  // reader hold one ranking in their head while scrolling to the next. Behind one
  // control the ranking simply re-sorts in place.
  //
  // This is not the old "three demand measures" chart, which put three shares of
  // three different denominators side by side and asked the reader to reconcile
  // them. One measure at a time, each on its own scale.
  const dem = {
    ads: {
      title: 'Where do employers advertise more than their employment share would predict?',
      cap: "A type of work's share of job ads against its share of jobs. Above 1.0 means employers are advertising more than its size alone would suggest — a sign of hiring pressure.",
      src: `Job ads, ${LC.postWindow} · ${fmt(totPost)} unique ads`,
      table: 'job-ads-against-size',
      sort: { k: 'post', dir: -1 },
      chart: (
        <Ranked id="q3-fam" rows={hot}>
          {(pick) => (
            <RankedBars
              rows={pick.map((r) => ({
                label: r.f,
                value: r.idx,
                color: r.idx >= 1 ? '--s3' : '--s2',
                dec: 2,
                big: [[fmt(r.jobs), 'Jobs today']],
                extra: [
                  ['Postings share', r.postSh.toFixed(1) + '%'],
                  ['Jobs share', r.jobsSh.toFixed(1) + '%'],
                ],
              }))}
              opts={{
                dec: 2,
                rule: 1,
                ruleLabel: 'Parity',
                valueLabel: 'Ads per job, vs its size',
                aria: 'Postings alignment index',
              }}
            />
          )}
        </Ranked>
      ),
    },

    observed: {
      title: 'Which families grew, and which shrank, over the study window?',
      note: observedSplit(fams),
      cap: 'How employment actually changed between 2021 and 2025.',
      src: 'Vermont occupation data · 2021 jobs against 2025 jobs',
      table: 'change-since-2021',
      sort: { k: 'chgPct', dir: -1 },
      chart: (
        <Ranked
          id="q3-fam"
          rows={fams.filter((r) => r.chgPct !== null).sort((a, b) => b.chgPct - a.chgPct)}
        >
          {(pick) => (
            <RankedBars
              rows={pick.map((r) => ({
                label: r.f,
                value: r.chgPct,
                color: r.chgPct >= 0 ? '--s3' : '--s2',
                mode: 'pct',
                big: [[(r.chg >= 0 ? '+' : '') + fmt(r.chg), 'Jobs gained or lost']],
                extra: [
                  ['2021 jobs', fmt(r.jobs21)],
                  ['2025 jobs', fmt(r.jobs)],
                  ['Annual openings', fmt(r.open)],
                ],
              }))}
              opts={{
                mode: 'pct',
                signed: true,
                valueLabel: 'Change since 2021',
                aria: 'Observed change 2021 to 2025 by family',
              }}
            />
          )}
        </Ranked>
      ),
    },

    projected: {
      title: 'Which families are projected to grow over the next five years?',
      note: growthSplit(fams),
      cap: 'Projected change in jobs over the next five years. Bars to the left are expected to shrink.',
      src: 'Vermont occupation data · 2030 projection against 2025 jobs',
      table: 'projected-growth',
      sort: { k: 'g5pct', dir: -1 },
      chart: (
        <Ranked id="q3-fam" rows={growers}>
          {(pick) => (
            <RankedBars
              rows={pick.map((r) => ({
                label: r.f,
                value: r.g5pct,
                color: r.g5pct >= 0 ? '--s3' : '--s2',
                mode: 'pct',
                big: [[fmt(r.g5), 'Jobs projected to be added']],
                extra: [
                  ['2025 jobs', fmt(r.jobs)],
                  ['Annual openings', fmt(r.open)],
                ],
              }))}
              opts={{
                mode: 'pct',
                signed: true,
                valueLabel: 'Growth by 2030',
                aria: 'Projected five-year growth by family',
              }}
            />
          )}
        </Ranked>
      ),
    },
  };

  // ---- what postings ask for ---------------------------------------------
  // The one panel on the dashboard that compares places rather than ranking
  // categories, which is why it draws as columns. Vermont, four of its counties,
  // the rest of the state, the neighbouring state the pay charts already use,
  // and the country.
  const asked = (m) => {
    const edu = m === 'education';
    const field = edu ? 'edu' : 'exp';
    const stated = edu ? 'eduStated' : 'expStated';
    const order = edu ? DEMAND.eduOrder : DEMAND.expOrder;

    const rows = DEMAND.areas.map((a) => ({
      label: a.label,
      parts: a[field],
      total: a[stated],
      // Postings per job is the guard against reading column height as demand.
      // It is the number that explains Washington County.
      note: a.perJob ? a.perJob.toFixed(2) + '/job' : null,
    }));

    return {
      title: edu
        ? 'What education do Vermont employers ask for?'
        : 'How much experience do Vermont employers ask for?',
      note: edu
        ? requirementShare(DEMAND.areas, 'edu', 'eduStated', 2, "a bachelor's degree or more")
        : requirementShare(DEMAND.areas, 'exp', 'expStated', 2, 'four years of experience or more'),
      cap: edu
        ? `Each column is one place, and sums to 100%. Shares are of the postings that state an education level — ${((DEMAND.areas[0].eduStated / DEMAND.areas[0].postings) * 100).toFixed(0)}% of Vermont's do, so this is what employers write down, not what every job requires. The figure under each column is postings per job, which is how to tell a county that advertises heavily from one that hires heavily.`
        : `Each column is one place, and sums to 100%. Shares are of the postings that state a minimum experience — ${((DEMAND.areas[0].expStated / DEMAND.areas[0].postings) * 100).toFixed(0)}% of Vermont's do. The figure under each column is postings per job.`,
      src: `Vermont job postings, ${DEMAND.window} · ${DEMAND.note}`,
      table: edu ? 'education-asked-by-place' : 'experience-asked-by-place',
      order,
      field,
      stated,
      chart: (
        <>
          <Legend labels={order} colors={order.map((_, i) => ORDINAL[i])} />
          <ColumnStack
            rows={rows}
            series={order}
            opts={{
              height: 470,
              noteLabel: true,
              aria: edu
                ? 'Education asked for in job postings, by place'
                : 'Experience asked for in job postings, by place',
            }}
          />
        </>
      ),
    };
  };

  return (
    <>
      <VHead
        title="Employer demand and growth"
      >
        Where is the hiring happening, and is it in the same places as the jobs Vermont already has?
      </VHead>

      <Sections
        id="demand"
        active={section}
        items={[
          /* Hidden for now -- kept whole rather than deleted, because the chart is
             sound and only the demand on the reader was wrong: it put three shares
             of three different denominators side by side. To bring it back, restore
             the nav entry in lib/nav.js and uncomment this block.

          // {
          // id: 'three-demand-measures',
          // label: 'Three demand measures',
          // render: () => (
          // <Panel
          // title="Do jobs, openings and postings point at the same families?"
          // note={demandDivergence(align)}
          // cap="What share of the state's jobs, yearly openings and job ads each type of work accounts for."
          // src={`Lightcast · postings window ${LC.postWindow} · shares within each measure sum to 100%`}
          // data={{ cols: familyCols(), rows: fams, label: 'three-demand-measures',
          // initialSort: { k: 'jobs', dir: -1 }, unit: 'kinds of work' }}
          // >
          // <Legend
          // labels={['Share of jobs', 'Share of annual openings', 'Share of postings']}
          // colors={['--s1', '--s4', '--s3']}
          // />
          // <Ranked id="q3-align" rows={align.slice().sort((a, b) => b.jobsSh - a.jobsSh)}>
          // {(pick) => (
          // <GroupedBars
          // rows={pick
          // .map((r) => ({
          // label: r.f,
          // parts: [{ v: r.jobsSh }, { v: r.openSh }, { v: r.postSh }],
          // extra: [
          // ['Jobs share', r.jobsSh.toFixed(1) + '%'],
          // ['Openings share', r.openSh.toFixed(1) + '%'],
          // ['Postings share', r.postSh.toFixed(1) + '%'],
          // ],
          // }))}
          // opts={{
          // colors: ['--s1', '--s4', '--s3'],
          // aria: 'Jobs, openings and postings shares by family',
          // }}
          // />
          // )}
          // </Ranked>
          // </Panel>
          // ),
          // },
          */

          {
            id: 'general-demand',
            label: 'General demand',
            render: () => (
              <Picker id="q3-asked" label="Measure" options={ASKED_MEASURES}>
                {(m) => {
                  const v = asked(m);
                  return (
                    <Panel
                      title={v.title}
                      note={v.note}
                      cap={v.cap}
                      src={v.src}
                      data={{
                        cols: demandCols(v.order, v.field, v.stated),
                        rows: DEMAND.areas,
                        label: v.table,
                        initialSort: { k: 'postings', dir: -1 },
                        unit: 'places',
                      }}
                    >
                      {v.chart}
                    </Panel>
                  );
                }}
              </Picker>
            ),
          },
          {
            id: 'hiring-and-growth',
            label: 'Hiring and growth',
            render: () => (
              <Picker id="q3-measure" label="Measure" options={DEMAND_MEASURES}>
                {(m) => {
                  const v = dem[m];
                  return (
                    <Panel
                      title={v.title}
                      note={v.note}
                      cap={v.cap}
                      src={v.src}
                      data={{
                        cols: familyCols(),
                        rows: fams,
                        label: v.table,
                        initialSort: v.sort,
                        unit: 'kinds of work',
                      }}
                    >
                      {v.chart}
                    </Panel>
                  );
                }}
              </Picker>
            ),
          },
          // --- Hidden for now ---------------------------------------------
          // Methods defines openings under "What the measures mean".
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'how-openings-are-defined',
          // label: 'How openings are defined',
          // render: () => (
          // <Callout label="How openings are defined here">
          // <p>
          // Openings are Lightcast&rsquo;s own <strong>{LC.window} Openings</strong> figure &mdash;{' '}
          // <N>{fmt(LC.openTotal)}</N> across the window &mdash; divided by <N>{LC.openYears}</N> to
          // give an annual rate of <N>{fmt(LC.openTotal / LC.openYears)}</N>, or{' '}
          // <N>{((LC.openTotal / LC.openYears / TOTJ) * 100).toFixed(1)}%</N> of employment. That
          // divisor is the one assumption here; change it and every openings figure scales linearly.
          // </p>
          // <p>
          // Do not confuse this with <strong>separations</strong>, which Lightcast also reports (
          // <N>{fmt(LC.sepTotal)}</N> in 2025, <N>{LC.sepPct}%</N> of employment). Separations include
          // job-to-job transfers, so they measure churn rather than hiring need and run roughly four
          // times the openings figure. Openings is the measure to use for demand.
          // </p>
          // </Callout>
          // ),
          // },

        ]}
      />
    </>
  );
}
