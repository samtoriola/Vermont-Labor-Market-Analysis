'use client';

import { SOW, SER } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Callout, Panel, Table, QHead, N } from '../ui';
import { RankedBars } from '../charts';

export default function Q6() {
  const V = SOW.vscs;
  const vtsu = V.byInst.find((r) => r.i === 'Vermont State University');
  const ccv = V.byInst.find((r) => r.i === 'Community College of Vermont');

  return (
    <>
      <QHead n={6}>
        How well does VSCS graduate production align with occupational demand, and where do
        program-to-occupation relationships suggest strong pipelines, diffuse career pathways,
        potential undersupply, or limited labor market opportunity?
      </QHead>

      <Answer>
        <p>
          VSCS awarded <N>{fmt(V.totalCompletions)}</N> credentials in 2024 &mdash;{' '}
          <N>{fmt(vtsu ? vtsu.c : 0)}</N> at Vermont State University and{' '}
          <N>{fmt(ccv ? ccv.c : 0)}</N> at Community College of Vermont &mdash; across{' '}
          <N>{fmt(V.nCip)}</N> instructional programs.
        </p>
        <p>
          <strong>The denominator matters more than the numerator here.</strong> Vermont has{' '}
          <N>{fmt(V.openAll)}</N> annual openings, but only <N>{fmt(V.openCred)}</N> of them (
          <N>{((V.openCred / V.openAll) * 100).toFixed(1)}%</N>) are in occupations that require any
          postsecondary credential at entry. Against that relevant denominator VSCS produces{' '}
          <N>{V.credShare}%</N> of annual demand &mdash; not the{' '}
          <N>{((V.totalCompletions / V.openAll) * 100).toFixed(1)}%</N> that a comparison against
          all openings would suggest.
        </p>
        <p>
          Programs link to <N>{fmt(V.nSocLinked)}</N> of Vermont&rsquo;s 798 occupations, covering{' '}
          <N>{V.openingsCovered}%</N> of all openings. The families with the largest raw openings
          &mdash; Food Preparation, Sales, Transportation &mdash; show almost no linked completions,
          and <strong>that is the expected and correct result</strong>: those occupations require no
          credential, so a near-zero ratio there signals irrelevance, not undersupply. Read the
          ratio only within credential-requiring work.
        </p>
      </Answer>

      <Callout label="Method, and what it cannot tell you">
        <p>
          CIP-to-SOC is many-to-many: a program links to several occupations and an occupation draws
          from several programs. Each program&rsquo;s completions are therefore split{' '}
          <strong>equally</strong> across its linked occupations. That preserves the total but is an
          assumption, not an observation &mdash; the SOW itself calls this a network of pathways
          rather than a mapping. A program whose graduates in practice concentrate in one occupation
          will look understated here.
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
        cap="What VSCS actually confers. Associate degrees and bachelor's degrees dominate; certificates are a meaningful third channel."
        src="IPEDS 2024 Completions · MAJORNUM=1, CIPCODE≠99 · CCV + Vermont State University"
      >
        <RankedBars
          rows={V.byAward.map((r, i) => ({
            label: r.a,
            value: r.c,
            color: SER[i % SER.length],
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
        cap="Openings are Vermont-wide; linked completions are VSCS output allocated across each program's occupations. A low ratio in a no-credential family is expected, not a gap."
        src="IPEDS 2024 × cip2020_soc2018 crosswalk × Lightcast openings · fractional allocation across linked SOCs"
      >
        <Table
          cols={[
            'Occupational family',
            'Annual openings',
            'Linked completions',
            'Completions per opening',
          ]}
          rows={V.byFamily.map((r) => ({
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
        title="Potential undersupply — for investigation, not conclusion"
        cap="Occupations with at least 50 annual openings that pay above the living wage, ranked by the lowest linked-completion ratio. These are where demand exists, pay is adequate, and VSCS production is thinnest — the shortlist worth a closer look."
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
        title="Strongest existing pipelines"
        cap="Highest linked-completion ratios among occupations with at least 50 annual openings — where VSCS production is most concentrated relative to demand. A very high ratio may indicate a strong pipeline or a saturated one; the data cannot distinguish them."
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
