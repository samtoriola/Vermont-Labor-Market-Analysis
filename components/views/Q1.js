'use client';

import {
  DATA, LC, TOTJ, TIER_ORDER, SERIES, COMPARE,
  AGE_LABELS, AGE_COLORS,
  lwAnnual, occByFamily, compareCol, indBySector, ageParts,
} from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { familyCols, sectorCols, industryCols } from '@/lib/tables';
import { HowTo, Panel, Legend, Picker, Ranked, RampLegend, Scope, VHead, DrillHint } from '../ui';
import { Split, occDetail, industryDetail } from '../Detail';
import { useDrill, occDrill } from '../Drill';
import { RankedBars, StackedRows } from '../charts';
import { BubbleChart } from '../bubbles';
import Sections from '../Sections';
import {
  credentialSpread, familyConcentration, oldestWorkforce, sliceAge, sliceShare, vsNation,
} from '@/lib/insight';

const SECTOR_MEASURES = [
  { id: 'jobs', label: 'Share of jobs' },
  { id: 'age', label: 'Age mix' },
];

const FAM_MEASURES = [
  { id: 'jobs', label: 'Share of jobs' },
  { id: 'pay', label: 'Typical pay' },
  { id: 'credential', label: 'Entry credential' },
  { id: 'age', label: 'Age mix' },
];

export default function Q1({ lw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  const famDrill = (f) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: f.f,
        cap: 'Every detailed occupation in this group, largest first.',
        occ: occByFamily(f.f),
        lwAnnual: LWA,
        extraStats: [['Annual openings', fmt(f.open)]],
      })
    );
  const fams = LC.families;

  // One bar per family at its typical pay, matching the shape of the jobs chart
  // above it. A bar cannot show the spread within a family, so the hover carries the
  // range the occupations inside it actually cover.
  const payBars = fams
    .filter((r) => r.med)
    .map((r) => ({
      label: r.f,
      value: r.med,
      color: r.med >= LWA ? '--s3' : '--s2',
      big: [[fmt(r.jobs), 'Jobs today']],
      extra: [
        ['Times the living wage', (r.med / LWA).toFixed(2) + '×'],
        ['Lowest-paid tenth', r.box && r.box.p10 ? money(r.box.p10) : '—'],
        ['Highest-paid tenth', r.box && r.box.p90 ? money(r.box.p90) : '—'],
        ['Occupations', fmt(r.nocc)],
      ],
    }))
    .sort((a, b) => b.value - a.value);

  // Reference bars: the state as a whole, the nearest comparable state, the nation.
  // Appended after the ranking rather than ranked with it, and drawn in grey so they
  // read as a baseline rather than as another occupation group.
  const famRefs = ['Vermont', 'New Hampshire', 'United States']
    .map(compareCol)
    .filter(Boolean)
    .map((a) => ({
      label: a.label,
      value: a.med,
      color: '--ink-3',
      extra: [
        ['Times the living wage', (a.med / LWA).toFixed(2) + '×'],
        ['Basis', a.sub],
      ],
    }));

  // What the pane shows for a family: the headline figures, then the largest
  // occupations inside it, then a way through to the whole table.
  const famDetail = (r) =>
    occDetail({
      label: 'Occupation group',
      title: r.f,
      occ: occByFamily(r.f),
      lwAnnual: LWA,
      stats: [
        [fmt(r.jobs), 'Jobs today'],
        [((r.jobs / TOTJ) * 100).toFixed(1) + '%', 'Of all VT jobs'],
        [r.med ? money(r.med) : '—', 'Typical pay'],
      ],
      onMore: () => famDrill(r),
    });

  // Sized by employment, shaded by how much of it asks for a degree. The mix
  // across all five rungs moves to the hover: it is what a reader wants second,
  // after "how big is this and how credentialled".
  const credRows = fams
    .map((r) => {
      const tot = TIER_ORDER.reduce((a, t) => a + (r.tiers[t] || 0), 0);
      const ba = (r.tiers["Bachelor's"] || 0) + (r.tiers['Graduate / professional'] || 0);
      return {
        row: r,
        label: r.f,
        total: tot,
        hi: ba / (tot || 1),
        mix: TIER_ORDER.map((t) => [t, (((r.tiers[t] || 0) / (tot || 1)) * 100).toFixed(0) + '%']),
      };
    })
    .sort((a, b) => b.hi - a.hi);

  const credLo = credRows.length ? credRows[credRows.length - 1].hi : 0;
  const credHi = credRows.length ? credRows[0].hi : 1;

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

  // ---- industry sectors ---------------------------------------------------
  // The sector chart could count the industries inside a bar but not name them.
  // It can now: 757 detailed industries carry their sector, so a click opens the
  // ones inside a sector exactly as a click on an occupation group opens its occupations.
  const indDrill = (r) => {
    const ind = indBySector(r.s);
    open({
      label: 'Industry sector',
      title: r.s,
      cap: 'Every detailed industry in this sector, largest first.',
      occ: ind,
      cols: industryCols(),
      rowKey: (d) => d.naics,
      stats: [
        ['Industries', fmt(ind.length)],
        ['Jobs', fmt(r.j)],
        ['Share of all jobs', r.share + '%'],
        ['Average pay per job', r.earn ? money(r.earn) : '\u2014'],
      ],
      src: 'Search, filter and sort with the controls at the top; export downloads the filtered rows',
    });
  };

  const indDetail = (r) =>
    industryDetail({
      title: r.s,
      ind: indBySector(r.s),
      stats: [
        [fmt(r.j), 'Jobs'],
        [r.share + '%', 'Of all VT jobs'],
        [r.earn ? money(r.earn) : '\u2014', 'Average pay'],
      ],
      onMore: () => indDrill(r),
    });

  // Oldest first on the age measure: the question it answers is where the work has
  // to be replaced soonest, so the rows that answer it belong at the top.
  const secAge = LC.sectors
    .map((r) => ({ row: r, a: ageParts(r) }))
    .filter((x) => x.a)
    .sort((x, y) => y.a.o55 - x.a.o55);

  const secPool = { jobs: LC.sectors, age: secAge };

  /**
   * The sector panel, built from the measure and the rows actually on screen.
   *
   * An object literal would have been enough while the read-out was a constant.
   * It is not one any more: "all 21 sectors", "the 11 largest" and "the 10
   * smallest" are three different claims about three different sets of numbers,
   * and the line under the chart has to be the one that matches what the reader
   * chose. So the panel is built per render from `pick`.
   */
  const sector = (m, pick) => {
    if (m === 'age') {
      return {
        title: 'How old is the workforce in each industry?',
        note: sliceAge(pick, secAge, {
          unit: 'sectors',
          name: (x) => x.row.s,
          age: (x) => x.a,
        }),
        cap: 'The age mix of each sector, oldest first. The figure on the right is the share aged 55 and over \u2014 the work most likely to need replacing within a decade.',
        src: 'Vermont industry data, 2025 \u00b7 eight reported age bands rolled up to three',
        table: 'industries',
        sort: { k: 'o55', dir: -1 },
        chart: (
          <>
            <Legend labels={AGE_LABELS} colors={AGE_COLORS} />
            <Split items={LC.sectors} keyOf={(r) => r.s} detail={indDetail}>
              {(select, active, width) => (
                <StackedRows
                  rows={pick.map((x) => ({
                    label: x.row.s,
                    parts: x.a.parts,
                    total: x.a.total,
                    hi: x.a.o55,
                    onClick: () => select(x.row.s),
                    active: active === x.row.s,
                  }))}
                  opts={{
                    labelWidth: 236,
                    width,
                    colors: AGE_COLORS,
                    tierNames: AGE_LABELS,
                    shareLabel: 'Share of this sector',
                    rightLabel: '55+',
                    clickHint: 'Click for the industries inside it',
                    aria: 'Age mix by industry sector',
                  }}
                />
              )}
            </Split>
          </>
        ),
      };
    }

    return {
      title: 'Which industries employ Vermonters?',
      note: sliceShare(pick, LC.sectors, TOTJ, {
        unit: 'sectors',
        value: (r) => r.j,
        name: (r) => r.s,
      }),
      cap: `Each industry's share of the state's ${fmt(TOTJ)} jobs.`,
      src: 'Vermont industry data, 2025 \u00b7 757 detailed industries with Vermont jobs, rolled up to sector',
      table: 'industries',
      sort: { k: 'j', dir: -1 },
      chart: (
        <>
          <DrillHint>Click any bar to open the industries inside it beside the chart.</DrillHint>
          <Split items={LC.sectors} keyOf={(r) => r.s} detail={indDetail}>
            {(select, active, width) => (
              <RankedBars
                rows={pick.map((r) => ({
                  label: r.s,
                  value: r.share,
                  color: '--s3',
                  onClick: () => select(r.s),
                  active: active === r.s,
                  big: [[fmt(r.j), 'Jobs']],
                  extra: [
                    ['Avg. earnings per job', r.earn ? money(r.earn) : '\u2014'],
                    ['Industries in this sector', fmt(r.nnaics)],
                  ],
                }))}
                opts={{
                  mode: 'pct',
                  labelWidth: 236,
                  width,
                  valueLabel: 'Share of all jobs',
                  clickHint: 'Click for the industries inside it',
                  aria: 'Share of Vermont jobs by industry sector',
                }}
              />
            )}
          </Split>
        </>
      ),
    };
  };

  const famAge = fams
    .map((r) => ({ row: r, a: ageParts(r) }))
    .filter((x) => x.a)
    .sort((x, y) => y.a.o55 - x.a.o55);

  // One question -- what differs across the 22 occupation groups -- asked three ways.
  // These were three sections scrolling past each other; they are the same 22 rows
  // every time, so the reader should be able to swap the measure and watch the
  // ranking move rather than lose their place between pages.
  const fam = {
    jobs: {
      title: 'Which occupation groups employ the most Vermonters?',
      note: familyConcentration(fams, TOTJ),
      cap: `Each occupation group's share of the state's ${fmt(TOTJ)} jobs.`,
      src: `Vermont occupation data, 2025 · 22 occupational groups · ${fmt(TOTJ)} jobs`,
      table: 'jobs-by-occupation-group',
      sort: { k: 'jobs', dir: -1 },
      chart: (
        <>
          <DrillHint>Click any bar to open the occupations inside it beside the chart.</DrillHint>
          <Split items={fams} keyOf={(r) => r.f} detail={famDetail}>
            {(select, active, width) => (
              <Ranked id="q1-fam" rows={fams}>
                {(pick) => (
                  <RankedBars
                    rows={pick.map((r) => ({
                      label: r.f,
                      value: (r.jobs / TOTJ) * 100,
                      color: '--s1',
                      onClick: () => select(r.f),
                      active: active === r.f,
                      big: [[fmt(r.jobs), 'Jobs today']],
                      extra: [
                        ['Median earnings', r.med ? money(r.med) : '—'],
                        ['Change 2021–2025', (r.chg >= 0 ? '+' : '') + fmt(r.chg) + ` (${r.chgPct}%)`],
                        ['Annual openings', fmt(r.open)],
                        ['Detailed occupations', fmt(r.nocc)],
                      ],
                    }))}
                    opts={{
                      mode: 'pct',
                      width,
                      valueLabel: 'Share of all jobs',
                      clickHint: 'Click for the occupations inside it',
                      aria: 'Share of Vermont jobs by occupation group',
                    }}
                  />
                )}
              </Ranked>
            )}
          </Split>
        </>
      ),
    },

    pay: {
      title: 'What does each occupation group pay?',
      note: vsNation(COMPARE.areas),
      cap: 'Green bars clear the living wage at the typical job, amber ones do not. The grey bars are the state, its nearest comparable state and the country.',
      src: `Vermont occupation data, 2025 · reference bars from published state and national wage data · living-wage benchmark 2025, ${lw}`,
      table: 'pay-by-occupation-group',
      sort: { k: 'med', dir: -1 },
      chart: (
        <Split items={fams} keyOf={(r) => r.f} detail={famDetail}>
          {(select, active, width) => (
            <Ranked id="q1-fam" rows={payBars}>
              {(pick) => (
                <RankedBars
                  rows={pick
                    .map((b) => ({
                      ...b,
                      onClick: () => select(b.label),
                      active: active === b.label,
                    }))
                    .concat(famRefs)}
                  opts={{
                    money: true,
                    width,
                    rule: LWA,
                    ruleLabel: 'Living wage',
                    valueLabel: 'Typical pay',
                    clickHint: 'Click for the occupations inside it',
                    aria: 'Typical pay by occupation group',
                  }}
                />
              )}
            </Ranked>
          )}
        </Split>
      ),
    },

    age: {
      title: 'How old is the workforce in each occupation group?',
      note: oldestWorkforce(fams, (r) => r.f, 'occupation group'),
      cap: 'The age mix of each occupation group, oldest first. The figure on the right is the share aged 55 and over \u2014 the work most likely to need replacing within a decade.',
      src: 'Vermont occupation data, 2025 \u00b7 eight reported age bands rolled up to three',
      table: 'age-by-occupation-group',
      sort: { k: 'o55', dir: -1 },
      chart: (
        <>
          <Legend labels={AGE_LABELS} colors={AGE_COLORS} />
          <Split items={fams} keyOf={(r) => r.f} detail={famDetail}>
            {(select, active, width) => (
              <Ranked id="q1-fam" rows={famAge}>
                {(pick) => (
                  <StackedRows
                    rows={pick.map((x) => ({
                      label: x.row.f,
                      parts: x.a.parts,
                      total: x.a.total,
                      hi: x.a.o55,
                      onClick: () => select(x.row.f),
                      active: active === x.row.f,
                    }))}
                    opts={{
                      width,
                      colors: AGE_COLORS,
                      tierNames: AGE_LABELS,
                      shareLabel: 'Share of this occupation group',
                      rightLabel: '55+',
                      clickHint: 'Click for the occupations inside it',
                      aria: 'Age mix by occupation group',
                    }}
                  />
                )}
              </Ranked>
            )}
          </Split>
        </>
      ),
    },

    credential: {
      title: 'What credential does each occupation group ask for at entry?',
      note: credentialSpread(fams),
      cap: 'Each circle is an occupation group, sized by how many jobs it holds and shaded by how much of that work asks for a degree at the door. What the job asks for, not what the people doing it hold. Hover for the full mix across all five levels.',
      src: 'Vermont occupation data, 2025 · entry credential, weighted by jobs',
      table: 'entry-credential-by-occupation-group',
      sort: { k: 'jobs', dir: -1 },
      chart: (
        <>
          <RampLegend
            label="Share asking for a bachelor's or more"
            lo={(credLo * 100).toFixed(0) + '%'}
            hi={(credHi * 100).toFixed(0) + '%'}
          />
          <Split items={fams} keyOf={(r) => r.f} detail={famDetail}>
            {(select, active, width) => (
              <BubbleChart
                rows={credRows.map((c) => ({
                  label: c.label,
                  value: c.total,
                  t: credHi > credLo ? (c.hi - credLo) / (credHi - credLo) : 0.5,
                  shown: (c.hi * 100).toFixed(0) + '%',
                  onClick: () => select(c.label),
                  active: active === c.label,
                  clickHint: 'Click for the occupations inside it',
                  big: [
                    [(c.hi * 100).toFixed(0) + '%', "Ask for a bachelor's or more"],
                    [fmt(c.total), 'Jobs today'],
                  ],
                  extra: c.mix,
                }))}
                opts={{
                  width,
                  height: 640,
                  aria: 'Employment and entry credential by occupation group',
                }}
              />
            )}
          </Split>
        </>
      ),
    },
  };

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
              <>
                <HowTo>
                  Vermont&rsquo;s 21 industry sectors. Measure changes what the bars are;
                  Show changes how much of the ranking you see, and the line underneath
                  answers the two together. Click a bar for the industries inside it.
                </HowTo>
                <Scope
                  id="q1-sec"
                  viewId="q1-sectors"
                  measures={SECTOR_MEASURES}
                  rowsFor={(m) => secPool[m]}
                >
                  {(m, pick) => {
                    const v = sector(m, pick);
                    return (
                      <Panel
                        title={v.title}
                        note={v.note}
                        cap={v.cap}
                        src={v.src}
                        data={{
                          cols: sectorCols(),
                          rows: LC.sectors,
                          label: v.table,
                          initialSort: v.sort,
                          onRowClick: indDrill,
                          unit: 'sectors',
                          note: 'Click a row for the detailed industries behind it.',
                        }}
                      >
                        {v.chart}
                      </Panel>
                    );
                  }}
                </Scope>
              </>
            ),
          },
          {
            id: 'by-occupation-group',
            label: 'By occupation group',
            render: () => (
              <>
                <HowTo>
                  The same 22 occupation groups under every measure — jobs, pay, what they ask
                  for at the door, and who is doing them. Click a bar for the occupations
                  inside it.
                </HowTo>
                <Picker id="q1-fam" label="Measure" options={FAM_MEASURES}>
                  {(m) => {
                    const v = fam[m];
                    return (
                      <Panel
                        title={v.title}
                        note={v.note}
                        cap={v.cap}
                        src={v.src}
                        data={{
                          cols: familyCols(LWA),
                          rows: fams,
                          label: v.table,
                          initialSort: v.sort,
                          onRowClick: famDrill,
                          unit: 'occupation groups',
                          note: 'Click a row for the occupations behind it.',
                        }}
                      >
                        {v.chart}
                      </Panel>
                    );
                  }}
                </Picker>
              </>
            ),
          },
        ]}
      />
    </>
  );
}
