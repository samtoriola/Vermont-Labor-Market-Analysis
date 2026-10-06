'use client';

import { LC, TOTJ, DATA, SOW, GLANCE } from '@/lib/data';
import { fmt } from '@/lib/format';
import { Panel, Table, VHead, Defs } from '../ui';

export default function About() {
  return (
    <>
      <VHead title="About the Vermont Labor Market Overview">
        Scope, sources and methodology
      </VHead>

      <Panel title="Overview">
        <p className="lede">
          The Vermont Labor Market Overview, developed by Strada Education Foundation for the
          Vermont State Colleges System, covers <strong>{fmt(LC.allOcc.length)}</strong> detailed
          occupations and <strong>{fmt(TOTJ)}</strong> jobs across Vermont&rsquo;s 14 counties,
          with employment and wages for 2025 and change measured from 2021.
        </p>
        <p className="lede">
          It lets workforce planners, institutional researchers and policymakers see what the
          state employs, what that work pays against a self-sufficiency benchmark, where employers
          are hiring, and how VSCS credential production sits against occupational demand.
        </p>
      </Panel>

      <Panel title="Dataset overview">
        <Defs
          items={[
            [
              'Sources',
              'Lightcast Vermont exports for occupations, industries and job postings; BLS OEWS for wage percentiles; Census CPS and ACS microdata for workers and earnings; IPEDS for credential production; MIT Living Wage for the self-sufficiency benchmark.',
            ],
            [
              'Filter',
              `Vermont only. ${fmt(LC.allOcc.length)} detailed occupations, ${fmt(DATA.families.length)} occupational families, all 14 counties, and the two VSCS institutions — the Community College of Vermont and Vermont State University.`,
            ],
            [
              'Unit of analysis',
              'Two units, and they are not interchangeable. Lightcast and OEWS count jobs and what a job asks for at entry. CPS and ACS count people and what they hold or earn. Each panel states which it uses; the Overview sets the two side by side deliberately.',
            ],
            [
              'When outcomes are measured',
              `Employment and wages are 2025. Change is measured over 2021–2025, projections run to 2030, job postings cover ${LC.postWindow}, and credential production is the 2024 academic year.`,
            ],
            [
              'How the data gets in',
              'Nothing is queried live. Build scripts pull from BigQuery and the Lightcast exports and write a small set of JSON files that the app reads at build time. Numbers change only when a script is re-run and the app redeployed.',
            ],
            [
              'What this is not',
              'Not a forecast and not a program recommendation. It reports what the sources say and states where they disagree. Sources, measure definitions and every suppression rule are on the Methods tab.',
            ],
          ]}
        />
      </Panel>

      <Panel title="The tabs" cap="Each tab answers one question from the project scope.">
        <Table
          cols={['Tab', 'What it answers']}
          text={[1]}
          rows={[
            {
              cells: [
                'Overview',
                'Headline scale of the labor market, and the gap between what jobs require and what workers hold',
              ],
            },
            {
              cells: [
                'Employment structure',
                'Which occupational families and industries employ Vermonters, and what each pays',
              ],
            },
            {
              cells: [
                'Wage quality',
                'How pay compares with a self-sufficiency benchmark, by occupation size and for individual workers',
              ],
            },
            {
              cells: [
                'Demand & growth',
                'Where openings, advertised demand and projected growth concentrate, and where the three disagree',
              ],
            },
            {
              cells: [
                'Pathways',
                'What the credential ladder pays — measured both on what jobs require and on what workers hold',
              ],
            },
            {
              cells: [
                'Opportunities',
                'Occupations scoring highest on scale, growth, demand and pay — and which of them VSCS could act on',
              ],
            },
            {
              cells: [
                'VSCS alignment',
                `How ${fmt(SOW.vscs.totalCompletions)} VSCS completions sit against ${fmt(SOW.vscs.openAll)} annual openings, by family and by occupation`,
              ],
            },
            {
              cells: ['Regions', 'How attainment, earnings and the local cost floor differ across the 14 counties'],
            },
            {
              cells: [
                'Methods',
                'Sources, what each measure means, the rules applied to the data, and what is not covered',
              ],
            },
          ]}
        />
      </Panel>

      <Panel title="How to use it">
        <Defs
          items={[
            [
              'Set the living wage first',
              'Wage quality and Pathways carry a household selector. It moves every figure that compares pay with self-sufficiency, so set it before reading those tabs.',
            ],
            [
              'Click through to the detail',
              'Bars, dot columns and table rows that sit on underlying occupations open a detail panel when clicked. Employment structure, Wage quality, Pathways and VSCS alignment all support it.',
            ],
            [
              'Search, filter and sort inside a table',
              'Every detail table and the full occupation table take a text search, a numeric range filter on any column, and sorting by any column. Sorting is on the underlying value, so money and percentages order correctly.',
            ],
            [
              'Export what you filtered',
              'The download button on a table exports the rows you are looking at, not the whole dataset — filter first, then export.',
            ],
            [
              'Show the top or the bottom of a ranking',
              'Long ranked charts carry a Show control. The default is the view the chart has always had; the other options take the same rows from the other end, or the whole list, and the count is on each button.',
            ],
            [
              'Save a chart as an image',
              'The PNG button on a chart saves what is on screen, carrying the question, the read-out and the source with it, so a chart dropped into a deck stays attributable.',
            ],
            [
              'Filters carry across tabs',
              'Credential tier, family, wage and size filters set on Wage quality or Opportunities stay applied as you move between tabs. Active filters are listed at the top of each tab, and can be cleared there.',
            ],
            [
              'Hover any mark',
              'Points, bars and dots carry their own figures on hover, including the occupation behind a single dot.',
            ],
          ]}
        />
      </Panel>
    </>
  );
}
