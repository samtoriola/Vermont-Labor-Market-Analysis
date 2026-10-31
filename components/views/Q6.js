'use client';

import { SOW, SERIES, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { awardCols } from '@/lib/tables';
import { Callout, HowTo, Panel, Picker, Ranked, VHead, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { RankedBars } from '../charts';
import DataTable from '../DataTable';
import Sections from '../Sections';
import { awardMix, familiesNoCompletions } from '@/lib/insight';

// Callout and N below are used only by the section(s) hidden further down. Kept
// imported so restoring one stays a single edit.

export default function Q6({ lw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const V = SOW.vscs;

  // Ordered by how far each occupation group's graduates go against its openings, with
  // the ones no graduate reaches at the foot rather than scattered through.
  const famShare = (r) => (r.open ? (r.linked / r.open) * 100 : null);

  const famAlign = V.byFamily
    .slice()
    .sort((a, b) => (famShare(b) || 0) - (famShare(a) || 0));

  const famDrill = (r) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: r.f,
        cap: 'The occupations in this group, and the graduates spread across them.',
        occ: occByFamily(r.f),
        lwAnnual: LWA,
        extraStats: [
          ['Openings a year', fmt(r.open)],
          ['Graduates attributed', r.linked.toFixed(1)],
          [
            'Graduates as % of openings',
            famShare(r) === null ? '—' : famShare(r).toFixed(1) + '%',
          ],
        ],
      })
    );

  // What the pane shows for an occupation group on this tab: the alignment figures
  // first, because that is the question the chart asked.
  const famDetail = (r) =>
    occDetail({
      label: 'Occupation group',
      title: r.f,
      occ: occByFamily(r.f),
      lwAnnual: LWA,
      stats: [
        [famShare(r) === null ? '—' : famShare(r).toFixed(1) + '%', 'Graduates vs openings'],
        [fmt(r.open), 'Openings a year'],
        [r.linked.toFixed(1), 'Graduates'],
      ],
      onMore: () => famDrill(r),
    });

  // Both ends of the linked-completion ratio in one sortable table. `under` is the
  // lowest ratios among occupations paying above the living wage; `over` the highest
  // overall, so the two can overlap and are de-duplicated on SOC.
  const ratioRows = V.under.concat(
    V.over.filter((r) => !V.under.some((u) => u.soc === r.soc))
  );
  // Two grains of one question -- where does production line up with demand --
  // which were two sections. The chart answers it for the 22 occupation groups; the
  // table answers it occupation by occupation, which is where a program sits.
  const LEVELS = [
    { id: 'family', label: 'By occupation group' },
    { id: 'occupation', label: 'By occupation' },
  ];

  const ratioCols = [
    { k: 'n', label: 'Occupation', kind: 'text', get: (r) => r.n },
    { k: 'open', label: 'Annual openings', kind: 'num', get: (r) => r.open },
    { k: 'linked', label: 'Graduates attributed', kind: 'num1', get: (r) => r.linked },
    {
      k: 'ratio',
      label: 'Graduates as % of openings',
      kind: 'rate',
      get: (r) => (r.ratio === null ? null : r.ratio * 100),
    },
    { k: 'm', label: 'Typical pay', kind: 'money', get: (r) => r.m },
    { k: 'lw', label: 'Times the living wage', kind: 'x', get: (r) => r.lw },
    { k: 't', label: 'Entry credential', kind: 'text', get: (r) => r.t },
  ];

  return (
    <>
      <VHead
        title="VSCS program alignment"
      >
        Does what VSCS graduates students in line up with where Vermont is hiring?
      </VHead>

      <Sections
        id="alignment"
        active={section}
        items={[
          {
            id: 'production-by-award',
            label: 'Production by award',
            render: () => (
              <>
                <HowTo>
                  What VSCS graduates, before any comparison with the labour market. Every
                  figure counts credentials awarded in one year, not people — one person
                  earning two is counted twice.
                </HowTo>
                <Panel
                  title="What credentials does VSCS award?"
                  note={awardMix(V.byAward, V.totalCompletions)}
                  cap={`How VSCS's ${fmt(V.totalCompletions)} graduates split across award levels. Hover for the count.`}
                  src="Federal completions data, 2024 · CCV and Vermont State University"
                  data={{ cols: awardCols(V.totalCompletions), rows: V.byAward, label: 'vscs-awards',
                          initialSort: { k: 'c', dir: -1 }, unit: 'award levels' }}
                >
                  <RankedBars
                    rows={V.byAward.map((r, i) => ({
                      label: r.a,
                      value: (r.c / V.totalCompletions) * 100,
                      color: SERIES[i % SERIES.length],
                      extra: [['Graduates', fmt(r.c)]],
                    }))}
                    opts={{
                      mode: 'pct',
                      labelWidth: 236,
                      valueLabel: 'Share of all awards',
                      aria: 'Share of VSCS awards by level',
                    }}
                  />
                </Panel>
              </>
            ),
          },
          {
            id: 'against-demand',
            label: 'Against demand',
            render: () => (
              <>
                <HowTo>
                  VSCS graduates measured against Vermont openings, at whichever grain you
                  pick: the 22 occupation groups, or occupation by occupation. A share here is
                  graduates as a percentage of openings — never the share of openings
                  filled, which no figure on this dashboard can tell you.
                </HowTo>
                <Picker id="q6-level" label="Level" options={LEVELS}>
                  {(level) =>
                    level === 'occupation' ? (
                      <Panel
                        title="Where does VSCS production sit relative to demand?"
                        cap="Occupations with at least 50 openings a year, shown at both ends: those paying above the living wage with the fewest graduates, and those with the most. Sort any column or search for an occupation. A lot of graduates per opening can mean a strong pipeline or an oversupplied one, and these figures cannot tell the two apart."
                        src="Federal completions data, 2024, against Vermont openings · openings ≥ 50"
                      >
                        <DataTable
                          cols={ratioCols}
                          rows={ratioRows}
                          initialSort={{ k: 'ratio', dir: 1 }}
                          exportLabel="vscs-production-against-demand"
                          rowKey={(r) => r.soc}
                          pageSize={30}
                        />
                      </Panel>
                    ) : (
                      <Panel
                        title="Where does VSCS production line up with openings?"
                        note={familiesNoCompletions(V.byFamily)}
                        cap="Each occupation group's VSCS graduates measured against the openings it has each year. 25% means VSCS graduates a number equal to a quarter of the openings — not that it fills a quarter of them, which no figure here can tell you. Grey bars draw no VSCS graduates at all. Work that needs no credential sits there by nature, because college is not the route into it. Hover for the counts; click for the occupations behind it."
                        src="Federal completions data, 2024, against Vermont openings · spread by employment"
                        data={{
                          cols: [
                            { k: 'f', label: 'Occupation group', kind: 'text', get: (r) => r.f },
                            { k: 'open', label: 'Openings a year', kind: 'num', get: (r) => r.open },
                            { k: 'linked', label: 'Graduates attributed', kind: 'num1', get: (r) => r.linked },
                            {
                              k: 'ratio',
                              label: 'Graduates as % of openings',
                              kind: 'rate',
                              get: famShare,
                            },
                            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
                          ],
                          rows: famAlign,
                          label: 'graduates-against-openings',
                          initialSort: { k: 'ratio', dir: -1 },
                          unit: 'occupation groups',
                          onRowClick: famDrill,
                          note: 'Click a row for the occupations behind it.',
                        }}
                      >
                        <Split items={famAlign} keyOf={(r) => r.f} detail={famDetail}>
                          {(select, active, width) => (
                        <Ranked id="q6-align" rows={famAlign}>
                          {(pick) => (
                            <RankedBars
                              rows={pick.map((r) => ({
                                label: r.f,
                                value: famShare(r) || 0,
                                // Grey where no graduate reaches this work at all. It is not
                                // a low score, it is the absence of a pipeline, and the two
                                // should not look the same. Keyed off the graduates rather
                                // than the share, so this counts the same families the
                                // read-out under the chart does.
                                color: r.linked > 0 ? '--s1' : '--ink-3',
                                onClick: () => select(r.f),
                                active: active === r.f,
                                extra: [
                                  ['Openings a year', fmt(r.open)],
                                  ['Graduates attributed', r.linked.toFixed(1)],
                                  ['Jobs', fmt(r.jobs)],
                                ],
                              }))}
                              opts={{
                                mode: 'pct',
                                labelWidth: 236,
                                width,
                                valueLabel: 'Graduates as % of openings',
                                clickHint: 'Click for the occupations inside it',
                                aria: 'Graduates as a share of openings by occupation group',
                              }}
                            />
                          )}
                        </Ranked>
                          )}
                        </Split>
                      </Panel>
                    )
                  }
                </Picker>
              </>
            ),
          },
          // --- Hidden for now ---------------------------------------------
          // Methods defines linked completions under "What the measures mean".
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'how-completions-were-linked',
          // label: 'How completions were linked',
          // render: () => (
          // <Callout label="How completions were linked to openings">
          // <p>
          // A program rarely feeds one job. Nursing feeds several nursing occupations; business
          // feeds dozens. So each program&rsquo;s graduates are spread across the occupations it
          // feeds, <strong>in proportion to how many people those occupations employ in
          // Vermont</strong> &mdash; a broad program lands where the jobs actually are, rather than
          // split evenly across every occupation on its list.
          // </p>
          // <p>
          // Graduates land in <N>{fmt(V.nSocLinked)}</N> occupations this way. Spreading them by
          // employment is an assumption about where graduates go, not a record of where they went
          // &mdash; 21 programs feed only occupations with no Vermont employment at all, and those
          // are split evenly instead.
          // </p>
          // <p>
          // It is also <strong>one year only</strong> (2024 graduates against 2025 openings), it
          // counts credentials rather than people &mdash; one person earning two counts twice &mdash;
          // and it says nothing about whether graduates stay in Vermont. Read these figures as a
          // place to look, never as a verdict on whether a field has too few or too many people.
          // </p>
          // </Callout>
          // ),
          // },

        ]}
      />
    </>
  );
}
