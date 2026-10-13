'use client';

import { SOW, SERIES, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { awardCols } from '@/lib/tables';
import { Callout, Panel, Table, VHead, N } from '../ui';
import { useDrill, occDrill } from '../Drill';
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

  // Both ends of the linked-completion ratio in one sortable table. `under` is the
  // lowest ratios among occupations paying above the living wage; `over` the highest
  // overall, so the two can overlap and are de-duplicated on SOC.
  const ratioRows = V.under.concat(
    V.over.filter((r) => !V.under.some((u) => u.soc === r.soc))
  );
  const ratioCols = [
    { k: 'n', label: 'Occupation', kind: 'text', get: (r) => r.n },
    { k: 'open', label: 'Annual openings', kind: 'num', get: (r) => r.open },
    { k: 'linked', label: 'VSCS graduates', kind: 'num1', get: (r) => r.linked },
    { k: 'ratio', label: 'Graduates per opening', kind: 'num3', get: (r) => r.ratio },
    { k: 'm', label: 'Median', kind: 'money', get: (r) => r.m },
    { k: 'lw', label: 'vs living wage', kind: 'x', get: (r) => r.lw },
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
                <Panel
                  title="What credentials does VSCS award?"
                  note={awardMix(V.byAward, V.totalCompletions)}
                  cap="How many VSCS graduates finished at each award level."
                  src="IPEDS 2024 Completions · MAJORNUM=1, CIPCODE≠99 · CCV + Vermont State University"
                  data={{ cols: awardCols(V.totalCompletions), rows: V.byAward, label: 'vscs-awards',
                          initialSort: { k: 'c', dir: -1 }, unit: 'award levels' }}
                >
                  <RankedBars
                    rows={V.byAward.map((r, i) => ({
                      label: r.a,
                      value: r.c,
                      color: SERIES[i % SERIES.length],
                      extra: [
                        ['Share of VSCS output', ((r.c / V.totalCompletions) * 100).toFixed(1) + '%'],
                      ],
                    }))}
                    opts={{
                      labelWidth: 236,
                      valueLabel: 'Graduates',
                      aria: 'VSCS completions by award level',
                    }}
                  />
                </Panel>
            ),
          },
          {
            id: 'against-openings',
            label: 'Against openings',
            render: () => (
                <Panel
                  title="Where does VSCS production line up with openings?"
                  note={familiesNoCompletions(V.byFamily)}
                  cap="Click a row to list the occupations behind it. Openings are statewide; graduates are VSCS completions spread across the occupations each program feeds. Work that needs no credential will always show few graduates per opening, simply because colleges are not the route into it."
                  src="IPEDS 2024 × cip2020_soc2018 crosswalk × Lightcast openings · employment-weighted allocation"
                >
                  <Table
                    cols={[
                      'Type of work',
                      'Annual openings',
                      'VSCS graduates',
                      'Graduates per opening',
                    ]}
                    rows={V.byFamily.map((r) => ({
                      onClick: () =>
                        open(
                          occDrill({
                            label: 'Type of work',
                            title: r.f,
                            cap: 'Occupations in this family, against which VSCS completions were allocated.',
                            occ: occByFamily(r.f),
                            lwAnnual: LWA,
                            extraStats: [
                              ['Annual openings', fmt(r.open)],
                              ['VSCS graduates', r.linked.toFixed(1)],
                            ],
                          })
                        ),
                      cells: [
                        r.f,
                        fmt(r.open),
                        r.linked.toFixed(1),
                        r.ratio === null ? '—' : r.ratio.toFixed(3),
                      ],
                    }))}
                  />
                </Panel>
            ),
          },
          {
            id: 'production-against-demand',
            label: 'Production vs demand',
            render: () => (
              <Panel
                title="Where does VSCS production sit relative to demand?"
                cap="Occupations with at least 50 openings a year, shown at both ends: those paying above the living wage with the fewest graduates, and those with the most. Sort any column or search for an occupation. A lot of graduates per opening can mean a strong pipeline or an oversupplied one, and these figures cannot tell the two apart."
                src="IPEDS 2024 × cip2020_soc2018 crosswalk × Lightcast openings · openings ≥ 50"
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
