'use client';

import { SERIES_HEX, ORDINAL_HEX, GOOD_HEX, BAD_HEX, lwHourly, lwAnnual } from '@/lib/data';
import { money } from '@/lib/format';
import { Panel, Table, VHead, Defs } from '../ui';

function Swatches({ items }) {
  return (
    <div className="swatches">
      {items.map(([hex, label]) => (
        <span key={hex + label}>
          <i style={{ background: hex }} />
          {label} {hex}
        </span>
      ))}
    </div>
  );
}

export default function Methods({ lw }) {
  return (
    <>
      <VHead title="Methods &amp; limits">
        How each figure is produced, and what this dashboard cannot tell you.
      </VHead>

      <Panel title="Sources">
        <Table
          cols={['Source', 'What it provides', 'Vintage']}
          text={[1, 2]}
          rows={[
            {
              cells: [
                'Lightcast',
                'Vermont occupations, industries and job postings',
                '2021–2025; postings to Jan 2026',
              ],
            },
            {
              cells: [
                'BLS OEWS',
                'Wage percentiles and means by occupation',
                'Vermont and New Hampshire 2025; United States 2024',
              ],
            },
            { cells: ['CPS (IPUMS)', 'Vermont monthly microdata', '2021–2025'] },
            {
              cells: [
                'ACS (IPUMS)',
                'Person-level earnings; county attainment',
                '1-year 2024; 5-year 2016–2020',
              ],
            },
            { cells: ['IPEDS', 'CCV and Vermont State University completions', '2024'] },
            { cells: ['MIT Living Wage', 'Vermont statewide and by county', '2025'] },
          ]}
        />
      </Panel>

      <Panel title="What the measures mean">
        <Defs
          items={[
            [
              'Jobs vs workers',
              'Lightcast counts jobs and what a job asks for (326,582). CPS counts employed residents and what they hold (335,775). The ~3% gap is definitional — compare shares, not levels.',
            ],
            [
              'Openings',
              'Lightcast’s 2021–2025 openings (195,571) ÷ 4 = 48,893 a year, 15.0% of employment. Not separations (202,870), which count job-to-job moves.',
            ],
            [
              'Turnover',
              'Separations over jobs. Includes people moving between employers, so it reads as churn, not unmet hiring need.',
            ],
            [
              'Wage percentiles',
              'As published. One occupation shows its own percentiles and mean. Family, tier and size figures are the employment-weighted mean of their occupations’ percentiles — a faithful range, not an exact group quantile.',
            ],
            [
              'Projected growth',
              'A Lightcast model of change to 2030, not an observation. Change over 2021–2025 is what happened, and the two are kept in separate panels for that reason.',
            ],
            [
              'Opportunity index',
              'Mean of four percentile ranks, 25% each: employment, projected growth, postings per 100 jobs, median pay. Occupations with 100+ jobs and a published wage.',
            ],
            [
              'Linked completions',
              'CIP-to-SOC is many-to-many, so each program’s completions are split across its linked occupations in proportion to their Vermont employment. A model of where graduates go, not an observation of it.',
            ],
          ]}
        />
      </Panel>

      <Panel title="Rules applied to the data">
        <Defs
          items={[
            [
              'Living wage is a setting',
              `Default ${money(lwAnnual(lw))} a year — $${lwHourly(lw).toFixed(2)} an hour at 2,080 hours, ${lw}. MIT’s Vermont figures run $17.06 to $63.91 depending on household. Every wage-quality number moves with this choice.`,
            ],
            [
              'Computed notes',
              'The line under a chart is generated from the data, not written. It appears only when a comparison clears a stated margin; otherwise it says there is no material difference. It never recommends an action.',
            ],
            [
              'Rates need a real base',
              'Lightcast models employment to a fraction of a job, so growth, change and turnover are left blank below 10 jobs. Without the rule Gambling Managers reads 19,390% growth on 0.005 jobs. Suppresses ~120 of 796 occupations per measure, 0.11% of employment. A blank means the base was too small, not zero.',
            ],
            [
              'Who counts as a worker',
              'The person-level earnings charts cover wage and salary workers aged 25–64 in civilian occupations, full-time year-round. The self-employed and military are excluded, matching the OEWS universe.',
            ],
            [
              'Person dots are sampled',
              'Columns hold more respondents than a chart can draw, so dots are a random draw made in proportion to survey weight. Average and median lines come from every respondent, not the dots shown.',
            ],
            [
              'Full-time and part-time',
              'Full-time is usual hours of 35 or more, taken from reported hours rather than the summary status code. 9.5% of employed Vermonters report that their hours vary and cannot be placed either side, so the split is shown over those with reportable hours.',
            ],
            [
              'CPS precision',
              'October 2025 is missing nationally, so 2025 is an 11-month average. Vermont weights are near-uniform (Kish 0.94), so intervals assume a design effect near 1. 80,569 person-month records cover 16,887 distinct people, and rate intervals use the person count, not the record count, because the survey re-interviews the same households. The unemployment rate shown is the direct CPS estimate; Vermont’s official rate comes from the model-based LAUS series, so the two differ by construction.',
            ],
          ]}
        />
      </Panel>

      <Panel title="Not covered">
        <ul className="lim">
          <li>
            <strong>Demand by county.</strong> Both Lightcast exports are statewide; CPS resolves
            Vermont no finer than metro and non-metro.
          </li>
          <li>
            <strong>VSCS program inventory and enrolment.</strong> Capacity is invisible here —
            only completions are counted.
          </li>
          <li>
            <strong>Graduate retention and destination.</strong> Nothing here tracks whether
            graduates take a related job, or stay in Vermont.
          </li>
          <li>
            <strong>Public and civic value.</strong> Programs serving need that labor demand does
            not price. Absence of a signal is not evidence of low value.
          </li>
        </ul>
      </Panel>

      <Panel title="Color" cap="Color follows the entity, never its rank. Ordered measures use one hue.">
        <Swatches
          items={[
            [GOOD_HEX, 'At or above living wage'],
            [BAD_HEX, 'Below living wage'],
          ]}
        />
        <Swatches items={SERIES_HEX.map((h, i) => [h, `Series ${i + 1}`])} />
        <Swatches
          items={[
            [ORDINAL_HEX[0], 'Ramp low'],
            [ORDINAL_HEX[4], 'Ramp high'],
          ]}
        />
      </Panel>
    </>
  );
}
