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

      <Panel
        title="Sources"
        cap="The line under every chart names its source in plain words rather than by vendor. The last column is the key to those names."
      >
        <Table
          cols={['Source', 'What it provides', 'Vintage', 'Named under a chart as']}
          text={[1, 2, 3]}
          rows={[
            {
              cells: [
                'Lightcast',
                'Vermont occupations, industries and job postings',
                '2021–2025; postings to Jan 2026',
                '“Vermont occupation data”, “Vermont industry data”, “Job ads”, “Vermont job postings”',
              ],
            },
            {
              cells: [
                'Lightcast Core LMI',
                'The county slice: occupation by county; posting education, experience and geography',
                '2021–2025',
                '“Vermont occupation data by county”, “Vermont employment by county”',
              ],
            },
            {
              cells: [
                'BLS OEWS',
                'Wage percentiles and means by occupation',
                'Vermont and New Hampshire 2025; United States 2024',
                'Folded into “Vermont occupation data”; named where a chart compares states',
              ],
            },
            {
              cells: [
                'CPS (IPUMS)',
                'Vermont monthly microdata — labor force, attainment held',
                '2021–2025',
                '“Census household survey”',
              ],
            },
            {
              cells: [
                'ACS (IPUMS)',
                'Person-level earnings; county attainment and income',
                '1-year 2024; 5-year 2016–2020',
                '“Census household survey”, “County survey data”',
              ],
            },
            {
              cells: [
                'IPEDS',
                'CCV and Vermont State University completions',
                '2024',
                '“Federal completions data”',
              ],
            },
            {
              cells: [
                'CIP-to-SOC crosswalk',
                'Links a program of study to the occupations it feeds',
                '2020 CIP to 2018 SOC',
                'Named where completions are set against openings',
              ],
            },
            {
              cells: [
                'MIT Living Wage',
                'Vermont statewide and by county, by household type',
                '2025',
                '“living-wage benchmark 2025”, “benchmark $…”',
              ],
            },
          ]}
        />
      </Panel>

      <Panel
        title="What each chart uses"
        cap="One row per section. Where a section carries a measure control, every measure on it draws from the same files. The file column is what the app imports at build time; scripts/README.md says which script writes each one and what it reads."
      >
        <Table
          cols={['Section', 'What it draws', 'Source', 'File']}
          text={[1, 2, 3]}
          rows={[
            {
              cells: [
                'Overview',
                'Jobs per occupation group, shaded by how much of that work pays below a living wage',
                'Lightcast occupations · OEWS percentiles · MIT',
                'lightcast.json, percentiles.json',
              ],
            },
            {
              cells: [
                'Employment · Industry sectors',
                'Jobs and the 55-and-over share across 21 sectors, and the industries inside one',
                'Lightcast industries',
                'lightcast.json',
              ],
            },
            {
              cells: [
                'Employment · Occupation',
                'Jobs, typical pay, entry credential and age mix across 22 occupation groups',
                'Lightcast occupations · OEWS for the state and national reference bars',
                'lightcast.json, compare.json',
              ],
            },
            {
              cells: [
                'Wage quality · Wage benchmark',
                'The share and the headcount paying below the benchmark, by group, credential or occupation',
                'Lightcast occupations · OEWS percentiles · MIT',
                'lightcast.json, percentiles.json',
              ],
            },
            {
              cells: [
                'Wage quality · County living wage',
                'The same share for all 14 counties, against each county’s own floor and the statewide one',
                'Lightcast Core LMI county slice · MIT by county',
                'wagefloor.json',
              ],
            },
            {
              cells: [
                'Demand & growth · General demand',
                'What job ads ask for in education and experience, by county and against the nation',
                'Lightcast Core LMI postings',
                'demand.json',
              ],
            },
            {
              cells: [
                'Demand & growth · Hiring and growth',
                'Job ads per 100 jobs, change over 2021–2025, and the projection to 2030',
                'Lightcast occupations and postings',
                'lightcast.json',
              ],
            },
            {
              cells: [
                'Pathways · By credential level',
                'Jobs, typical pay, living-wage clearance and the pay range at five entry credentials',
                'Lightcast occupations · OEWS percentiles · MIT',
                'lightcast.json, percentiles.json',
              ],
            },
            {
              cells: [
                'Pathways · Which credentials pay',
                'Occupations at each credential that both hire in volume and pay a living wage',
                'Lightcast occupations · MIT',
                'lightcast.json',
              ],
            },
            {
              cells: [
                'Workers · What people hold',
                'What credentials employed Vermonters hold, and how that has moved since 2021',
                'CPS via IPUMS',
                'cps.json',
              ],
            },
            {
              cells: [
                'Workers · What people earn',
                'Person-level earnings against the benchmark, by the credential a worker holds',
                'ACS 1-year via IPUMS · MIT',
                'people.json',
              ],
            },
            {
              cells: [
                'Opportunities · Highest scoring',
                'The four-measure composite index, filtered by entry credential',
                'Lightcast occupations · OEWS',
                'sow.json',
              ],
            },
            {
              cells: [
                'Opportunities · Program candidates',
                'The index set against VSCS completions, under the screen thresholds',
                'Lightcast · IPEDS · CIP-to-SOC crosswalk',
                'sow.json',
              ],
            },
            {
              cells: [
                'VSCS alignment · Production by award',
                'CCV and Vermont State University completions by award level',
                'IPEDS',
                'sow.json',
              ],
            },
            {
              cells: [
                'VSCS alignment · Against demand',
                'Completions linked to occupations, set against annual openings',
                'IPEDS · CIP-to-SOC crosswalk · Lightcast openings',
                'sow.json',
              ],
            },
            {
              cells: [
                'Regions · County map',
                'County attainment, median income and the local cost floor',
                'ACS 5-year · MIT by county · simplified county outlines',
                'sow.json, counties.json, vt-map.json',
              ],
            },
            {
              cells: [
                'Regions · Counties compared',
                'County jobs, typical pay, change since 2021, and what each county is concentrated in',
                'Lightcast Core LMI county slice',
                'counties.json',
              ],
            },
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
              'As published. One occupation shows its own percentiles and mean. Occupation group and credential ranges are the employment-weighted mean of their occupations’ percentiles, which is not the same as the group’s own quantile: a mean of tenth percentiles averages away the spread between occupations, which at a credential level is most of the spread there is. It understates the range by up to 44% — graduate / professional reads 2.5× from lowest-paid tenth to highest, against 3.6× when the member occupations’ ladders are pooled. The ordering survives; the magnitude does not. Where a figure is pooled rather than published, the chart says so.',
            ],
            [
              'Below a living wage',
              'The benchmark’s position along each occupation’s own percentile ladder, weighted by that occupation’s jobs and rolled up. Not whether the occupation’s median clears it: that rule counts every job in an occupation on whichever side its midpoint falls, which is out by 19 points on Installation & Repair and 15 on Office & Admin Support. Clamped outside the 10th and 90th percentiles, where the published ladder says nothing.',
            ],
            [
              'The county cost floor',
              'MIT publishes a living wage per county, one adult with no children, running from $45,323 to $53,768. Where the dashboard compares counties against a cost floor it uses both that figure and the statewide one, because the gap between the two answers is the finding. Every other tab uses the statewide benchmark.',
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
              'A low score is not a verdict',
              'Every measure here is a labor-market one. Programs serve need that labor demand does not price — public, civic and care work among them — and none of that is visible in this data. A low score means the market signals are weak, not that a program lacks value.',
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

      {/* --- Hidden for now ------------------------------------------------
          The six limits this listed are no longer stated anywhere in the
          dashboard. Restore by removing this wrapper.

      <Panel title="Not covered">
        <ul className="lim">
          <li>
            <strong>Projected growth by county.</strong> The county slice carries employment
            and pay through 2025 and no further; the projections to 2030 shown elsewhere are
            statewide. A county outlook would need a different, far larger table.
          </li>
          <li>
            <strong>County and survey areas do not line up.</strong> County lines and the areas the
            Census uses for its microdata do not nest, so a county view of demand and a county view
            of what people hold cannot share one map.
          </li>
          <li>
            <strong>County income is not like-for-like.</strong> The county figures set a median{' '}
            <em>household</em> income against a wage floor built for one adult. Read it as how far a
            county sits from the floor, not as a measure of any one worker.
          </li>
          <li>
            <strong>VSCS program inventory and enrolment.</strong> Capacity is invisible here —
            only completions are counted.
          </li>
          <li>
            <strong>Graduate retention and destination.</strong> Nothing here tracks whether
            graduates take a related job, or stay in Vermont.
          </li>
        </ul>
      </Panel>

          Public and civic value was the sixth item here. It is kept, as
          "A low score is not a verdict" under Rules applied to the data, because
          it guards against reading a weak score as a judgement on a program
          rather than on the market. Do not restore it here as well.
      */}

      <Panel
        title="Color"
        cap="Color follows the entity, never its rank. Ordered measures use one hue, and red is reserved for a mark that contrasts two sides inside one chart."
      >
        <p className="lede">
          The green / red pair marks two sides of the benchmark where both appear on the same
          chart — the pay of a credential level, an occupation group or a county, some of which
          clears it and some of which does not. It is not used for a whole chart: a bar that is
          86% red reads as an alarm rather than a measurement, which is why Wage quality and the
          Overview use the ordinal ramp instead.
        </p>
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
