'use client';

import {
  DATA, LC, PCT, TIER_ORDER, SERIES, PEOPLE,
  lwAnnual, occByTier, credentialFunnel,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { bandCols, peopleCols } from '@/lib/tables';
import { Callout, Panel, Picker, Table, VHead, LwPicker, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { occCols } from '../occCols';
import { RankedBars } from '../charts';
import Sections from '../Sections';
// Callout, N and largestCategory are used only by the section hidden further down.
// Kept imported so restoring it stays a single edit.
import {
  funnelContrast, ladderStep, peopleLadderStep, livingWageJump, largestCategory,
} from '@/lib/insight';

const CRED_MEASURES = [
  { id: 'jobs', label: 'Share of jobs' },
  { id: 'pay', label: 'Typical pay' },
  { id: 'above', label: 'Above living wage' },
  { id: 'spread', label: 'Range of outcomes' },
];

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
  // What the pane shows for a credential tier.
  const tierDetail = (r) =>
    occDetail({
      label: 'Entry credential',
      title: r.t,
      occ: occByTier(r.t),
      lwAnnual: LWA,
      stats: [
        [fmt(r.jobs), 'Jobs today'],
        [r.share.toFixed(1) + '%', 'Of all VT jobs'],
        [r.med ? money(r.med) : '—', 'Typical pay'],
      ],
      onMore: () => tierDrill(r.t),
    });

  const sub = t['Sub-baccalaureate'];
  const ba = t["Bachelor's"];
  const grad = t['Graduate / professional'];
  const lastCps = DATA.trend[DATA.trend.length - 1];
  const P = PCT.tiers;

  // One bar per entry credential at the pay of its typical occupation. A bar cannot
  // show the spread, so the hover carries the range the occupations in it cover.
  const tierBars = TIER_ORDER.map((k) => t[k])
    .filter((r) => r && r.med)
    .map((r) => {
      const bx = r.box || {};
      return {
        label: r.t,
        value: r.med,
        color: r.med >= LWA ? '--s3' : '--s2',
        big: [[fmt(r.jobs), 'Jobs today']],
        extra: [
          ['Times the living wage', (r.med / LWA).toFixed(2) + '×'],
          ['Middle half pays', bx.p25 && bx.p75 ? money(bx.p25) + ' to ' + money(bx.p75) : '—'],
          ['Lowest-paid tenth', bx.p10 ? money(bx.p10) : '—'],
          ['Highest-paid tenth', bx.p90 ? money(bx.p90) : '—'],
          ['Share of all jobs', r.share.toFixed(1) + '%'],
          ['Occupations', fmt(r.nocc)],
        ],
      };
    });

  // The same ladder measured on people rather than jobs: the midpoint earner at each
  // credential they hold. The average sits well above the midpoint at the top of the
  // ladder, so it goes on the hover with the range rather than being dropped.
  const credBars = PEOPLE.byCred.map((c) => ({
    label: c.thin ? c.label + ' (small sample)' : c.label,
    value: c.med,
    color: c.thin ? '--ink-3' : c.med >= LWA ? '--s3' : '--s2',
    extra: [
      ['Times the living wage', (c.med / LWA).toFixed(2) + '×'],
      ['Average earnings', money(c.avg)],
      ['Middle half earns', money(c.p25) + ' to ' + money(c.p75)],
      ['Lowest-paid tenth', money(c.p10)],
      ['Highest-paid tenth', money(c.p90)],
      ['Respondents', fmt(c.n)],
    ],
  }));

  // Four questions about the same five rungs, which were three sections and four
  // panels: how much work sits at each level, what it pays, how much of it clears
  // the benchmark, and how wide the outcomes are. One control, one chart frame.
  //
  // The benchmark selector appears only on the two measures it changes, so the page
  // never carries a control that does nothing.
  const bands = {
    cols: bandCols(LWA, 't', 'Entry credential'),
    rows: LC.tiers,
    unit: 'credentials',
  };

  const cred = {
    jobs: {
      title: 'How much Vermont employment sits at each credential level?',
      cap: "What share of Vermont's jobs ask for each level of education.",
      src: `Vermont occupation data, 2025 · ${fmt(LC.totalJobs)} jobs`,
      data: { ...bands, label: 'jobs-by-credential', initialSort: { k: 'jobs', dir: -1 } },
      chart: (
        <Split items={LC.tiers} keyOf={(r) => r.t} detail={tierDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={TIER_ORDER.map((k, i) => {
                const r = t[k];
                return {
                  label: r.t,
                  value: r.share,
                  color: SERIES[i],
                  mode: 'pct',
                  onClick: () => select(r.t),
                  active: active === r.t,
                  big: [[fmt(r.jobs), 'Jobs today']],
                  extra: [['Occupations', fmt(r.nocc)]],
                };
              })}
              opts={{
                mode: 'pct',
                labelWidth: 176,
                width,
                valueLabel: 'Share of jobs',
                clickHint: 'Click for the occupations at this level',
                aria: 'Employment share by credential tier',
              }}
            />
          )}
        </Split>
      ),
    },

    pay: {
      lw: true,
      title: 'What does each rung pay, by what the job asks for?',
      note: ladderStep(LC.tiers, TIER_ORDER),
      cap: 'What a typical job pays at each entry credential. Green bars clear the living wage, amber ones do not.',
      src: 'Vermont occupation data, 2025 · entry credential · every priced Vermont occupation',
      data: {
        cols: occCols(LWA),
        rows: LC.allOcc,
        label: 'pay-by-what-the-job-asks',
        initialSort: { k: 'j', dir: -1 },
        unit: 'occupations',
        note: 'Every priced Vermont occupation, the detail behind the five rungs.',
      },
      chart: (
        <Split items={LC.tiers} keyOf={(r) => r.t} detail={tierDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={tierBars.map((b) => ({
                ...b,
                onClick: () => select(b.label),
                active: active === b.label,
              }))}
              opts={{
                money: true,
                width,
                rule: LWA,
                ruleLabel: 'Living wage',
                valueLabel: 'Typical pay',
                labelWidth: 236,
                clickHint: 'Click for the occupations at this level',
                aria: 'Typical pay by entry credential',
              }}
            />
          )}
        </Split>
      ),
    },

    above: {
      lw: true,
      title: 'Which credential levels clear the living wage?',
      note: livingWageJump(LC.tiers, TIER_ORDER, lw),
      cap: `What share of each credential's jobs pay at or above the living wage for ${lw} — ${money(LWA)} a year.`,
      src: 'Vermont occupation data, 2025 · occupation median against the benchmark',
      data: { ...bands, label: 'above-the-living-wage', initialSort: { k: 'jobs', dir: -1 } },
      chart: (
        <Split items={LC.tiers} keyOf={(r) => r.t} detail={tierDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={TIER_ORDER.map((k, i) => {
                const r = t[k];
                return {
                  label: r.t,
                  value: r.above[lw],
                  color: SERIES[i],
                  mode: 'pct',
                  onClick: () => select(r.t),
                  active: active === r.t,
                  big: [[fmt(r.jobs), 'Jobs today']],
                  extra: [
                    ['Median earnings', money(r.med)],
                    ['Occupations', fmt(r.nocc)],
                  ],
                };
              })}
              opts={{
                mode: 'pct',
                labelWidth: 176,
                max: 100,
                width,
                valueLabel: 'Above living wage',
                clickHint: 'Click for the occupations at this level',
                aria: 'Living-wage share by credential tier',
              }}
            />
          )}
        </Split>
      ),
    },

    spread: {
      title: 'How wide is the range of outcomes at each credential level?',
      cap: 'How many times more the best-paid tenth earn than the worst-paid tenth. A wider range means the credential leads to very different outcomes.',
      src: 'Vermont occupation data, 2025 · highest-paid tenth against lowest-paid tenth',
      data: { ...bands, label: 'pay-range-by-credential', initialSort: { k: 'med', dir: -1 } },
      chart: (
        <RankedBars
          rows={TIER_ORDER.filter((k) => P[k]).map((k, i) => {
            const b = P[k];
            return {
              label: k,
              value: b.p90 / b.p10,
              color: SERIES[i],
              dec: 2,
              big: [[money(b.p50), 'Midpoint pay']],
              extra: [
                ['Lowest-paid tenth', money(b.p10)],
                ['Highest-paid tenth', money(b.p90)],
              ],
            };
          })}
          opts={{
            dec: 2,
            labelWidth: 176,
            valueLabel: 'Times wider',
            aria: 'Earnings dispersion by credential tier',
          }}
        />
      ),
    },
  };

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
            id: 'by-credential-level',
            label: 'By credential level',
            render: () => (
              <Picker id="q4-cred" label="Measure" options={CRED_MEASURES}>
                {(m) => {
                  const v = cred[m];
                  return (
                    <>
                      {v.lw ? <LwPicker value={lw} onChange={setLw} /> : null}
                      <Panel
                        title={v.title}
                        note={v.note}
                        cap={v.cap}
                        src={v.src}
                        data={v.data}
                      >
                        {v.chart}
                      </Panel>
                    </>
                  );
                }}
              </Picker>
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
                  cap="The same ladder measured on people rather than jobs: what the midpoint Vermonter earns at each credential they hold. The self-employed and the military are left out. A bar marked as a small sample rests on fewer than 100 answers and is rough. Hover for the average and the range."
                  src={`Census household survey, 2024 · ${PEOPLE.universe.toLowerCase()} · living-wage benchmark 2025, ${lw}`}
                  data={{ cols: peopleCols('Credential held'), rows: PEOPLE.byCred, label: 'pay-by-credential-held',
                          initialSort: { k: 'med', dir: -1 }, unit: 'credentials',
                          note: 'Groups, not the individual dots: each dot is one anonymous respondent.' }}
                >
                  <RankedBars
                    rows={credBars}
                    opts={{
                      money: true,
                      rule: LWA,
                      ruleLabel: 'Living wage',
                      valueLabel: 'Midpoint earnings',
                      labelWidth: 236,
                      aria: 'Midpoint earnings by credential held',
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
                src={`Vermont occupation data, 2025 · entry credential · openings ≥ ${MIN_OPEN}/yr · living-wage benchmark 2025`}
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
          // --- Hidden for now ---------------------------------------------
          // The jobs-versus-workers contrast is the Overview panel, and the captions here already say which of the two each chart shows.
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'what-this-measures',
          // label: 'What this measures',
          // render: () => (
          // <Callout label="What this measures">
          // <p>
          // These are job <em>requirements</em>, not worker <em>attainment</em>: a property of the
          // job, not of the person holding it.{' '}
          // <N>{(ba.share + grad.share).toFixed(1)}%</N> of Vermont jobs ask for a bachelor&rsquo;s
          // or more, while <N>{lastCps.ba.toFixed(1)}%</N> of Vermont workers 25+ hold one, a
          // difference of <N>{(lastCps.ba - ba.share - grad.share).toFixed(1)} points</N>. The two
          // come from different sources and count different things.
          // </p>
          // </Callout>
          // ),
          // },

        ]}
      />
    </>
  );
}
