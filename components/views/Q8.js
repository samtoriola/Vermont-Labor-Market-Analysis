'use client';

import { DATA, LC, PCT, SOW, TOTJ, lwAnnual } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, QHead } from '../ui';

export default function Q8({ lw }) {
  const LWA = lwAnnual(lw);
  const t = {};
  LC.tiers.forEach((r) => {
    t[r.t] = r;
  });
  const V = SOW.vscs;
  const baReq = t["Bachelor's"].share + t['Graduate / professional'].share;
  const sub = t['Sub-baccalaureate'];
  const lastBa = DATA.trend[DATA.trend.length - 1].ba;
  const regsAsc = SOW.regions.slice().sort((a, b) => a.ba - b.ba);
  const regsDesc = SOW.regions.slice().sort((a, b) => b.ba - a.ba);

  const groups = [
    {
      title: 'Strong evidence, clear implication',
      color: '--s3',
      items: [
        [
          'The wage return concentrates at the bachelor’s threshold, not below it',
          `Median earnings move only ${money(
            PCT.tiers['Sub-baccalaureate'].p50 - PCT.tiers['High school'].p50
          )} from high school to sub-baccalaureate, then jump ${money(
            PCT.tiers["Bachelor's"].p50 - PCT.tiers['Sub-baccalaureate'].p50
          )} to bachelor’s. Any earnings-based case for a sub-baccalaureate credential has to rest on specific occupations, not on the tier average.`,
        ],
        [
          'Vermont’s largest occupations are its lowest-paying and most wage-compressed',
          `The ${LC.sizeTiers[0].nocc} occupations with 2,000+ jobs hold ${
            LC.sizeTiers[0].share
          }% of employment, pay a median of ${money(LC.sizeTiers[0].med)}, and only ${LC.sizeTiers[0].above[
            lw
          ].toFixed(0)}% clear the living wage. Their 90th percentile (${money(
            PCT.sizeTiers['Large (2,000+)'].p90
          )}) barely reaches the median of the mid-size tier. Volume and wage quality point in opposite directions.`,
        ],
        [
          'Most Vermont openings do not require a postsecondary credential',
          `Only ${fmt(V.openCred)} of ${fmt(V.openAll)} annual openings (${(
            (V.openCred / V.openAll) *
            100
          ).toFixed(1)}%) sit in occupations requiring one. VSCS serves ${
            V.credShare
          }% of that relevant demand. Program strategy should be measured against the credential-requiring segment, not against total openings.`,
        ],
      ],
    },
    {
      title: 'Strong evidence, implication depends on a VSCS choice',
      color: '--s1',
      items: [
        [
          'Wage-quality conclusions hinge on the benchmark, which is unset',
          `At the single-adult living wage (${money(LWA)}), ${sub.above[lw].toFixed(
            0
          )}% of sub-baccalaureate jobs clear it. The sub-baccalaureate 25th percentile sits at ${money(
            PCT.tiers['Sub-baccalaureate'].p25
          )} — within a few hundred dollars of that line — so the figure is highly sensitive. At a one-adult-one-child benchmark almost nothing clears. SOW section 7 leaves this choice to VSCS and it changes the answer to question 2.`,
        ],
        [
          'Regional strategy needs a geography decision before it needs more data',
          `Bachelor’s attainment ranges ${regsAsc[0].ba}% to ${regsDesc[0].ba}% across the 14 counties, while the cost floor is nearly flat. But county and PUMA geographies do not nest, so demand-side and attainment-side regional views cannot yet sit on one map.`,
        ],
        [
          'The opportunity index is a default, and its weights are a VSCS decision',
          `Question 5 scores four indicators at 25% each. Two earlier components were removed as redundant — living-wage ratio (rank-identical to pay) and openings intensity (negative variance contribution). The surviving four are near-independent, but the choice of indicators and weights still belongs to VSCS under section 7.`,
        ],
      ],
    },
    {
      title: 'Signal worth investigating, not yet a finding',
      color: '--s4',
      items: [
        [
          'A credential-requirement gap of roughly 15 points',
          `About ${baReq.toFixed(
            1
          )}% of Vermont jobs list a bachelor’s or higher at entry, while ${lastBa.toFixed(
            1
          )}% of workers 25+ hold one. That gap is where underemployment would live, but requirement and attainment come from different sources measuring different things, so it needs a dedicated cut before it carries weight.`,
        ],
        [
          'Undersupply candidates exist but rest on an allocation assumption',
          'The shortlist in question 6 filters to living-wage occupations with 50+ openings and thin VSCS linkage. It depends on splitting each program’s completions equally across its linked occupations, which will understate programs whose graduates concentrate.',
        ],
        [
          'Recent history and the forward projection disagree',
          `Vermont added ${fmt(TOTJ - LC.jobs21)} jobs over 2021–2025 (+${(
            (TOTJ / LC.jobs21 - 1) *
            100
          ).toFixed(1)}%), faster than the 2025–2030 projection implies. Which to plan against is a judgement the data does not settle.`,
        ],
      ],
    },
    {
      title: 'Cannot be answered with what is loaded',
      color: '--s2',
      items: [
        [
          'Occupational demand and wage premiums by region',
          'Both Lightcast exports are statewide; CPS gives Vermont only metro/non-metro. Core LMI covers all 14 counties and would close this.',
        ],
        [
          'Whether graduates stay, and where they land',
          'Completions count credentials conferred, not people retained or employed in Vermont. Lightcast profiles could trace graduate-to-job pathways; they are not in this build.',
        ],
        [
          'Programs serving public or civic need that demand measures miss',
          'SOW section 4D asks for these explicitly. Nursing, teaching and public-service programs may be strategically essential at demand levels this framework scores low. No quantitative measure here captures that, and it should not be inferred from silence.',
        ],
      ],
    },
  ];

  return (
    <>
      <QHead n={8}>
        What findings have the greatest implications for VSCS program planning, including
        opportunities to strengthen, expand, develop, reposition, or further evaluate specific
        program areas?
      </QHead>

      <Callout label="Scope of this section">
        <p>
          The SOW is explicit that this analysis informs institutional decisions but does not by
          itself prescribe whether a program should be created, expanded, reduced or discontinued
          &mdash; those calls also turn on student demand, mission, quality, instructional capacity,
          cost, access, transfer pathways and public-service obligations, none of which are in this
          data. What follows is therefore organised as findings and their implications, sorted by
          how much confidence the evidence supports.
        </p>
      </Callout>

      {groups.map((g) => (
        <div className="panel" key={g.title}>
          <h3>{g.title}</h3>
          <div className="findlist">
            {g.items.map(([head, body]) => (
              <div className="finding" key={head} style={{ borderLeftColor: `var(${g.color})` }}>
                <h4>{head}</h4>
                <p>{body}</p>
              </div>
            ))}
          </div>
        </div>
      ))}

      <Panel
        title="What would most improve the next version"
        cap="Ranked by how much each unlocks, given what is already here."
        src="Assessment, not data"
      >
        <Table
          cols={['Addition', 'Unlocks', 'Effort']}
          rows={[
            {
              cells: [
                'Lightcast Core LMI county extract (state + 14 counties)',
                'All of RQ7: demand, wage premiums and sufficiency by region',
                'Low',
              ],
            },
            {
              cells: [
                'VSCS program inventory and enrolment, not just completions',
                'Capacity and pipeline view; distinguishes small from shrinking',
                'Low',
              ],
            },
            {
              cells: [
                'A VSCS-agreed living-wage benchmark and household type',
                'Fixes every wage-quality figure in Q2, Q4, Q5',
                'None — a decision',
              ],
            },
            {
              cells: [
                'Growth-only openings series (excluding replacement)',
                'Restores a clean demand component to the Q5 index',
                'Low',
              ],
            },
            {
              cells: [
                'Multi-year completions (3–5 years)',
                'Trend rather than snapshot; stabilises small programs',
                'Low',
              ],
            },
            {
              cells: [
                'Lightcast profiles for Vermont graduates',
                'Retention and actual program-to-occupation pathways',
                'Medium',
              ],
            },
            {
              cells: [
                'More ACS vintages in the warehouse',
                'Attainment trend; currently only 2023 is loaded',
                'Medium',
              ],
            },
          ]}
        />
      </Panel>
    </>
  );
}
