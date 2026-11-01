'use client';

import { SOW, SERIES, lwAnnual, occByFamily, credOpenByFamily, VSCS_TIERS } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { awardCols } from '@/lib/tables';
import { Callout, HowTo, Panel, Picker, Ranked, VHead, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { RankedBars } from '../charts';
import DataTable from '../DataTable';
import Sections from '../Sections';
import { awardMix, credGap } from '@/lib/insight';

// Callout and N below are used only by the section(s) hidden further down. Kept
// imported so restoring one stays a single edit.

export default function Q6({ lw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const V = SOW.vscs;

  /**
    * WHICH OPENINGS VSCS IS MEASURED AGAINST
    * ---------------------------------------
    * Not all of them. Dividing a group's graduates by every opening it has asks
    * VSCS to supply work a college is not the route into -- 6,065 food preparation
    * openings a year, 4,190 in sales -- and the chart then reads 3.5% overall with
    * five groups at zero. Against the openings whose entry credential is one VSCS
    * awards, the same production reads 9.7%, and three of those five turn out to
    * have no such openings at all.
    *
    * This is not a new measure. scripts/build_sow.py computes the total and its
    * own comment says why: "comparing VSCS output to ALL openings understates
    * alignment". It reaches the app as SOW.vscs.openCred and the chart had never
    * used it. All this does is split it by occupation group.
    */
  const CRED_OPEN = credOpenByFamily();
  const famRows = V.byFamily.map((r) => ({
    ...r,
    // Left unrounded: rounding every group before summing them put the read-out's
    // total a job above the caption's, and two totals for one thing on one panel
    // reads as an error. Rounded once, at the point each is printed.
    openCred: CRED_OPEN[r.f] || 0,
    openAll: r.open,
  }));
  const CRED_TOTAL = famRows.reduce((a, r) => a + r.openCred, 0);
  const famShare = (r) => (r.openCred ? (r.linked / r.openCred) * 100 : null);

  // A ratio needs a base worth dividing by. Lightcast models openings to a
  // fraction, so "greater than zero" is not a test: food preparation carries 0.3
  // credential-requiring openings a year across 6,065 openings, and on a bare
  // > 0 test it joined Sales and Legal on the chart as though it were the same
  // kind of finding. Ten a year is the floor the dashboard already uses for a
  // rate -- see "Rates need a real base" on Methods -- and it separates food
  // preparation at 0.3 from farming at 11.8, which is the next one up.
  const MIN_CRED_OPEN = 10;
  const famAlign = famRows
    .filter((r) => r.openCred >= MIN_CRED_OPEN)
    .sort((a, b) => (famShare(b) || 0) - (famShare(a) || 0));
  const noCred = famRows
    .filter((r) => r.openCred < MIN_CRED_OPEN)
    .sort((a, b) => b.openAll - a.openAll);

  const famDrill = (r) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: r.f,
        cap: 'The occupations in this group, and the graduates spread across them.',
        occ: occByFamily(r.f),
        lwAnnual: LWA,
        extraStats: [
          ['Openings asking for a VSCS credential', fmt(r.openCred)],
          ['All openings a year', fmt(r.openAll)],
          ['Graduates attributed', r.linked.toFixed(1)],
          [
            'Graduates as % of the openings that ask',
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
        [famShare(r) === null ? '—' : famShare(r).toFixed(0) + '%', 'Of the openings that ask'],
        [fmt(r.openCred), 'Openings asking'],
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
                  VSCS graduates measured against the Vermont openings that ask for a
                  credential it awards, at whichever grain you pick: the 22 occupation
                  groups, or occupation by occupation. A share here is graduates as a
                  percentage of those openings — never the share of openings filled,
                  which no figure on this dashboard can tell you.
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
                        note={credGap(famRows, MIN_CRED_OPEN)}
                        cap={`Each occupation group's VSCS graduates measured against the openings it has each year whose entry credential is one VSCS awards — ${fmt(CRED_TOTAL)} of Vermont's ${fmt(V.openAll)} annual openings. 25% means VSCS graduates a number equal to a quarter of those openings, not that it fills a quarter of them, which no figure here can tell you. The openings column sits beside the bar because a high share of a small number is a different finding from a high share of a large one. Hover for the counts; click for the occupations behind it.`}
                        src={`Federal completions data, 2024, against Vermont openings asking for a sub-baccalaureate, bachelor's or graduate credential · ${fmt(CRED_TOTAL)} openings a year · graduates spread by employment`}
                        data={{
                          cols: [
                            { k: 'f', label: 'Occupation group', kind: 'text', get: (r) => r.f },
                            { k: 'openCred', label: 'Openings asking for a VSCS credential', kind: 'num', get: (r) => r.openCred },
                            { k: 'linked', label: 'Graduates attributed', kind: 'num1', get: (r) => r.linked },
                            {
                              k: 'ratio',
                              label: 'Graduates as % of the openings that ask',
                              kind: 'rate',
                              get: famShare,
                            },
                            { k: 'openAll', label: 'All openings a year', kind: 'num', get: (r) => r.openAll },
                            {
                              k: 'ratioAll',
                              label: 'Against all openings',
                              kind: 'rate',
                              get: (r) => (r.openAll ? (r.linked / r.openAll) * 100 : null),
                            },
                            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
                          ],
                          // Every group, including the three with nothing to divide
                          // by -- the table is where the full list belongs.
                          rows: famRows,
                          label: 'graduates-against-openings',
                          initialSort: { k: 'ratio', dir: -1 },
                          unit: 'occupation groups',
                          onRowClick: famDrill,
                          note: 'Click a row for the occupations behind it.',
                        }}
                      >
                        <>
                        <Split items={famAlign} keyOf={(r) => r.f} detail={famDetail}>
                          {(select, active, width) => (
                        <Ranked id="q6-align" rows={famAlign}>
                          {(pick) => (
                            <RankedBars
                              rows={pick.map((r) => ({
                                label: r.f,
                                value: famShare(r) || 0,
                                // Grey where work asks for a credential VSCS awards and
                                // no graduate reaches it. That is the absence of a
                                // pipeline rather than a low one, and the two should not
                                // look the same. The groups with nothing to divide by are
                                // off the chart entirely, named underneath.
                                color: r.linked > 0 ? '--s1' : '--ink-3',
                                right: fmt(r.openCred),
                                onClick: () => select(r.f),
                                active: active === r.f,
                                extra: [
                                  ['Openings asking for a VSCS credential', fmt(r.openCred)],
                                  ['All openings a year', fmt(r.openAll)],
                                  ['Against all openings', r.openAll ? ((r.linked / r.openAll) * 100).toFixed(1) + '%' : '—'],
                                  ['Graduates attributed', r.linked.toFixed(1)],
                                  ['Jobs', fmt(r.jobs)],
                                ],
                              }))}
                              opts={{
                                mode: 'pct',
                                dec: 0,
                                labelWidth: 236,
                                width,
                                keepFill: true,
                                valueLabel: 'Graduates as % of the openings that ask',
                                valueHead: 'SHARE',
                                rightHead: 'OPENINGS',
                                clickHint: 'Click for the occupations inside it',
                                aria:
                                  'Graduates as a share of the credential-requiring openings in each occupation group',
                              }}
                            />
                          )}
                        </Ranked>
                          )}
                        </Split>
                        {noCred.length ? (
                          <p className="cap nocred">
                            Not on the chart: <strong>{noCred.map((r) => r.f).join(', ')}</strong>.
                            Between {noCred.length === 1 ? 'it' : 'them'}{' '}
                            {fmt(noCred.reduce((a, r) => a + r.openAll, 0))} openings a year, and
                            fewer than {MIN_CRED_OPEN} of those ask for a credential VSCS awards —
                            too small a base to divide by, so there is no share to draw. They are
                            in the table below.
                          </p>
                        ) : null}
                        </>
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
