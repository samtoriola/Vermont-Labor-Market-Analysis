'use client';

import { SOW, SERIES, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, VHead, N } from '../ui';
import { ActiveFilters } from '../Filters';
import { useDrill, occDrill } from '../Drill';
import { RankedBars } from '../charts';
import DataTable from '../DataTable';
import Sections from '../Sections';

export default function Q6({ lw }) {
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
    { k: 'linked', label: 'Linked completions', kind: 'num1', get: (r) => r.linked },
    { k: 'ratio', label: 'Completions per opening', kind: 'num3', get: (r) => r.ratio },
    { k: 'm', label: 'Median', kind: 'money', get: (r) => r.m },
    { k: 'lw', label: 'vs living wage', kind: 'x', get: (r) => r.lw },
    { k: 't', label: 'Entry credential', kind: 'text', get: (r) => r.t },
  ];

  return (
    <>
      <VHead
        title="VSCS program alignment"
      >
        How well does VSCS graduate production align with occupational demand, and where do program-to-occupation relationships suggest strong pipelines, diffuse career pathways, potential undersupply, or limited labor market opportunity?
      </VHead>

      <ActiveFilters />

      <Sections
        id="alignment"
        items={[
          {
            id: 'production-by-award',
            label: 'Production by award',
            render: () => (
                <Panel
                  title="What credentials does VSCS award?"
                  cap="Completions by award level."
                  src="IPEDS 2024 Completions · MAJORNUM=1, CIPCODE≠99 · CCV + Vermont State University"
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
                      valueLabel: 'Completions',
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
                  cap="Click a row to list the occupations behind it. Openings are Vermont-wide; linked completions are VSCS output allocated across each program's occupations. Families whose occupations require no credential will show a low ratio by construction."
                  src="IPEDS 2024 × cip2020_soc2018 crosswalk × Lightcast openings · employment-weighted allocation"
                >
                  <Table
                    cols={[
                      'Occupational family',
                      'Annual openings',
                      'Linked completions',
                      'Completions per opening',
                    ]}
                    rows={V.byFamily.map((r) => ({
                      onClick: () =>
                        open(
                          occDrill({
                            label: 'Occupational family',
                            title: r.f,
                            cap: 'Occupations in this family, against which VSCS completions were allocated.',
                            occ: occByFamily(r.f),
                            lwAnnual: LWA,
                            extraStats: [
                              ['Annual openings', fmt(r.open)],
                              ['Linked completions', r.linked.toFixed(1)],
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
                cap="Occupations with at least 50 annual openings, at both ends of the ratio: the lowest among those paying above the living wage, and the highest overall. Sort any column or search for an occupation. A high ratio may mean a strong pipeline or a saturated one; the data cannot tell them apart."
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
          {
            id: 'how-completions-were-linked',
            label: 'How completions were linked',
            render: () => (
                <Callout label="How completions were linked to openings">
                  <p>
                    CIP-to-SOC is many-to-many: a program links to several occupations and an occupation draws
                    from several programs. Each program&rsquo;s completions are divided across its linked
                    occupations <strong>in proportion to those occupations&rsquo; Vermont employment</strong>,
                    so a broad program lands in proportion to where the jobs are rather than evenly across
                    every occupation it links to.
                  </p>
                  <p>
                    Completions land in <N>{fmt(V.nSocLinked)}</N> occupations. Weighting by employment is a
                    model of graduate behavior, not an observation of it &mdash; 21 programs link only to
                    occupations with no Vermont employment at all, and those fall back to an even split
                    across their linked occupations.
                  </p>
                  <p>
                    This is also a <strong>single-year snapshot</strong> (IPEDS 2024 completions against
                    Lightcast 2025 openings), it counts credentials rather than people, and it says nothing
                    about whether graduates stay in Vermont. Treat every ratio here as a screening signal for
                    further investigation, never as a supply-demand verdict.
                  </p>
                </Callout>
            ),
          },
        ]}
      />
    </>
  );
}
