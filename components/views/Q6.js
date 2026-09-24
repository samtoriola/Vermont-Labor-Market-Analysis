'use client';

import { SOW, SERIES, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, VHead, N } from '../ui';
import { ActiveFilters } from '../Filters';
import { useDrill, occDrill } from '../Drill';
import { RankedBars } from '../charts';

export default function Q6({ lw }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const V = SOW.vscs;

  return (
    <>
      <VHead
        title="VSCS program alignment"
      >
        VSCS credential production set against Vermont occupational demand.
      </VHead>

      <ActiveFilters />

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
          model of graduate behaviour, not an observation of it &mdash; 21 programs link only to
          occupations with no Vermont employment at all, and those fall back to an even split
          across their linked occupations.
        </p>
        <p>
          This is also a <strong>single-year snapshot</strong> (IPEDS 2024 completions against
          Lightcast 2025 openings), it counts credentials rather than people, and it says nothing
          about whether graduates stay in Vermont. Treat every ratio below as a screening signal for
          further investigation, never as a supply-demand verdict.
        </p>
      </Callout>

      <Panel
        title="VSCS production by award level"
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

      <Panel
        title="Linked completions against annual openings, by family"
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

      <Panel
        title="Lowest linked-completion ratios, openings above the living wage"
        cap="Occupations with at least 50 annual openings that pay above the living wage, ranked by the lowest linked-completion ratio."
        src="Filtered to openings ≥ 50 and median earnings at or above the living wage"
      >
        <Table
          cols={[
            'Occupation',
            'Annual openings',
            'Linked completions',
            'Ratio',
            'Median',
            'vs LW',
            'Entry credential',
          ]}
          rows={V.under.map((r) => ({
            cells: [
              r.n,
              fmt(r.open),
              r.linked.toFixed(1),
              r.ratio.toFixed(3),
              money(r.m),
              r.lw + '×',
              r.t,
            ],
          }))}
        />
      </Panel>

      <Panel
        title="Highest linked-completion ratios"
        cap="Highest linked-completion ratios among occupations with at least 50 annual openings. A high ratio may indicate a strong pipeline or a saturated one; the data cannot distinguish them."
        src="Same universe, ranked by highest ratio"
      >
        <Table
          cols={[
            'Occupation',
            'Annual openings',
            'Linked completions',
            'Ratio',
            'Median',
            'vs LW',
            'Entry credential',
          ]}
          rows={V.over.map((r) => ({
            cells: [
              r.n,
              fmt(r.open),
              r.linked.toFixed(1),
              r.ratio.toFixed(3),
              money(r.m),
              r.lw + '×',
              r.t,
            ],
          }))}
        />
      </Panel>
    </>
  );
}
