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
                'Vermont monthly microdata. Reaches one figure on screen: the employed-Vermonters tile on the home page, which 15_labor_force_cps.csv carries in full',
                '2021–2025',
                '“Census household survey”',
              ],
            },
            {
              cells: [
                'ACS (IPUMS)',
                'County attainment and median income, on the Regions map',
                '5-year 2016–2020',
                '“County survey data”',
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
        cap="One row per section. Where a section carries a measure control, every measure on it draws from the same files. The file column is what the app imports at build time, and scripts/README.md says which script writes each one and what it reads. The workfile column is the spreadsheet in workfiles/ that reproduces that chart&rsquo;s figures by hand, inputs and intermediate steps included."
      >
        <Table
          cols={['Section', 'What it draws', 'Source', 'File', 'Workfile']}
          text={[1, 2, 3, 4]}
          rows={[
            {
              cells: [
                'Home',
                'Four headline tiles. Two count jobs, one counts people, one counts credentials',
                'Lightcast occupations · Census household survey · IPEDS',
                'lightcast.json, glance.json, sow.json',
                '14_home_tiles.csv',
              ],
            },
            {
              cells: [
                'Overview',
                'Jobs per occupation group, shaded by how much of that work pays below a living wage',
                'Lightcast occupations · OEWS percentiles · MIT',
                'lightcast.json, percentiles.json',
                '02_overview_and_wage_by_group.csv',
              ],
            },
            {
              cells: [
                'Employment · Industry sectors',
                'Jobs and the 55-and-over share across 21 sectors, and the industries inside one',
                'Lightcast industries',
                'lightcast.json',
                '06_employment_sectors.csv',
              ],
            },
            {
              cells: [
                'Employment · Occupation',
                'Jobs, typical pay, entry credential and age mix across 22 occupation groups',
                'Lightcast occupations · OEWS for the state and national reference bars',
                'lightcast.json, compare.json',
                '07_employment_occupation_groups.csv',
              ],
            },
            {
              cells: [
                'Wage quality · Wage benchmark',
                'The share and the headcount paying below the benchmark, by group, credential or occupation',
                'Lightcast occupations · OEWS percentiles · MIT',
                'lightcast.json, percentiles.json',
                '02_overview_and_wage_by_group.csv',
              ],
            },
            {
              cells: [
                'Wage quality · County living wage',
                'The same share for all 14 counties, against each county’s own floor and the statewide one',
                'Lightcast Core LMI county slice · MIT by county',
                'wagefloor.json',
                '05_wage_county_floor.csv',
              ],
            },
            {
              cells: [
                'Demand & growth · General demand',
                'What job ads ask for in education and experience, by county and against the nation',
                'Lightcast Core LMI postings',
                'demand.json',
                '12_demand_what_postings_ask.csv',
              ],
            },
            {
              cells: [
                'Demand & growth · Hiring and growth',
                'Job ads per 100 jobs, change over 2021–2025, and the projection to 2030',
                'Lightcast occupations and postings',
                'lightcast.json',
                '01_occupations_master.csv',
              ],
            },
            {
              cells: [
                'Pathways · By credential level',
                'The pay range of each of five entry credentials, with the benchmark ruled across them, and how much employment sits at each',
                'Lightcast occupations · OEWS percentiles, pooled across the occupations at each credential · MIT',
                'lightcast.json, percentiles.json',
                '03_pathways_credential_ladder.csv',
              ],
            },
            {
              cells: [
                'Pathways · Which credentials pay',
                'A year of hiring at each credential, and how much of it is in work paying a living wage',
                'Lightcast occupations and openings · OEWS percentiles · MIT',
                'lightcast.json, percentiles.json',
                '04_pathways_openings_by_credential.csv',
              ],
            },

            {
              cells: [
                'Opportunities · Highest scoring',
                'The composite index, each bar split into the four percentile ranks it is the mean of',
                'Lightcast occupations · OEWS',
                'sow.json',
                '08_opportunity_scores.csv',
              ],
            },

            {
              cells: [
                'VSCS alignment · Production by award',
                'CCV and Vermont State University completions by award level',
                'IPEDS',
                'sow.json',
                '10_vscs_production.csv',
              ],
            },
            {
              cells: [
                'VSCS alignment · Against demand',
                'Completions linked to occupations, set against the annual openings that ask for a credential VSCS awards',
                'IPEDS · CIP-to-SOC crosswalk · Lightcast openings and entry credential',
                'sow.json, lightcast.json',
                '09_vscs_alignment_by_group.csv',
              ],
            },
            {
              cells: [
                'Regions · County map',
                'County attainment, median income and the local cost floor',
                'ACS 5-year · MIT by county · simplified county outlines',
                'sow.json, counties.json, vt-map.json',
                '13_regions_county_map.csv',
              ],
            },
            {
              cells: [
                'Regions · Counties compared',
                'County jobs, typical pay, change since 2021, and what each county is concentrated in',
                'Lightcast Core LMI county slice',
                'counties.json',
                '11_regions_counties.csv',
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
              'Every chart that ranks or compares work counts jobs and what a job asks for at entry. The credential a job asks for is not the credential the person in it holds, and nothing here measures the second — the section that did is not currently in the dashboard. Where the Census surveys do appear, on the Regions map and the home page, they count people, and no chart puts a jobs figure and a people figure on the same scale.',
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
              'The benchmark’s position along each occupation’s own percentile ladder, weighted by that occupation’s jobs and rolled up. Used by the Overview, Wage quality and Pathways, which is every chart that compares pay with self-sufficiency. Pathways’ hiring chart weights the same measure by annual openings rather than by jobs, because an occupation can hold a great many jobs and almost never hire. Not whether the occupation’s median clears it: that rule counts every job in an occupation on whichever side its midpoint falls, which is out by 19 points on Installation & Repair and 15 on Office & Admin Support. Clamped outside the 10th and 90th percentiles, where the published ladder says nothing.',
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
              'Openings that ask for a VSCS credential',
              'The denominator the alignment chart divides by: the 17,436 openings a year, of 48,893, in occupations whose entry credential is sub-baccalaureate, bachelor’s or graduate — the three VSCS awards into. Measured against every opening instead, VSCS production reads 3.5% rather than 9.8%, and five occupation groups read as zero when three of them have almost no such openings to begin with. Food preparation has 0.3 a year. A group is left off the chart below ten, under the same rule as any other rate here, and named underneath it.',
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
              'Two job totals',
              'The home page prints 326,582 jobs and every chart totals 325,132. The difference is 1,450 jobs in military occupations and in SOC codes falling outside the 22 occupation groups, which the exports carry in the statewide total and the charts drop, because neither has an occupation group, a credential or a pay ladder to sit under. It is 0.4% of employment, and it is why group shares read off a chart will not quite reproduce against the tile.',
            ],
            [
              'Rates need a real base',
              'Lightcast models employment to a fraction of a job, so growth, change and turnover are left blank below 10 jobs. Without the rule Gambling Managers reads 19,390% growth on 0.005 jobs. Suppresses ~120 of 796 occupations per measure, 0.11% of employment. A blank means the base was too small, not zero.',
            ],
            // --- Hidden for now ------------------------------------------
            // These three govern the person-level earnings charts on Workers,
            // which is commented out of lib/nav.js, and the dot columns, which
            // no section draws. Restore them with the section.
            // [
            //   'Who counts as a worker',
            //   'The person-level earnings charts cover wage and salary workers aged 25–64 in civilian occupations, full-time year-round. The self-employed and military are excluded, matching the OEWS universe.',
            // ],
            // [
            //   'Person dots are sampled',
            //   'Columns hold more respondents than a chart can draw, so dots are a random draw made in proportion to survey weight. Average and median lines come from every respondent, not the dots shown.',
            // ],
            // [
            //   'Full-time and part-time',
            //   'Full-time is usual hours of 35 or more, taken from reported hours rather than the summary status code. 9.5% of employed Vermonters report that their hours vary and cannot be placed either side, so the split is shown over those with reportable hours.',
            // ],
            [
              'CPS precision',
              'Governs the employed-Vermonters figure on the home page, which is the only CPS number currently on screen. October 2025 is missing nationally, so 2025 is an 11-month average. 80,569 person-month records cover 16,887 distinct people, and anything computed as a rate would use the person count rather than the record count, because the survey re-interviews the same households. It is a direct survey estimate; Vermont’s official labour-force figures come from the model-based LAUS series, so the two differ by construction.',
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
        title="Checking the numbers"
        cap="Every figure the dashboard draws is also a spreadsheet, built from the same files the app reads."
      >
        <Defs
          items={[
            [
              'The workfiles',
              'The workfiles/ folder carries one CSV per chart, listed in the register above. Each holds the inputs and the intermediate steps rather than only the answer, so a measure can be redone with a calculator — the share of an occupation’s jobs below the benchmark arrives with that occupation’s five published percentiles beside it.',
            ],
            [
              'Start at the headline',
              '00_headline_figures.csv lists every number quoted in a caption, a read-out or a tile, with the workfile and the arithmetic that reproduces it. 01_occupations_master.csv carries all 796 occupations with every field and the derived share-below, and most other workfiles are a roll-up of it.',
            ],
            [
              'They cannot drift',
              'scripts/build_workfiles.py writes them from data/, the same JSON the app imports at build time, so a figure in a workfile and the same figure on screen come from one source. scripts/check_workfiles.py walks the chain — occupation rows sum to group rows, group rows sum to the headline, the headline is what the page prints — and fails if any link comes apart.',
            ],
            [
              'What they cannot settle',
              'Three things are modelled rather than observed, and checking the arithmetic will not change that: where VSCS graduates go, growth projected to 2030, and the openings divisor. Each is defined above; workfiles/README.md repeats them beside the files.',
            ],
          ]}
        />
      </Panel>

      <Panel
        title="Color"
        cap="Color follows the entity, never its rank. Ordered measures use one hue, and red is reserved for a mark that contrasts two sides inside one chart."
      >
        <p className="lede">
          The green / red pair marks two sides of the benchmark where both appear on the same
          chart — the pay of a credential level, an occupation group or a county, some of which
          clears it and some of which does not. It is not used for a whole chart: a bar that is
          86% red reads as an alarm rather than a measurement, which is why Wage quality and the
          Overview use the ordinal ramp instead. Where the two sides are points rather than a
          range — the scatter of every occupation on Wage quality — the shortfall keeps red
          and the other half takes Ocean rather than green. Green against red is too close to
          tell apart under the commonest colour blindness, and a point carries no value label
          to read instead; the benchmark line separates the two either way.
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
