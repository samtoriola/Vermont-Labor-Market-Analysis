'use client';

import { LC, TOTJ, DATA, SOW } from '@/lib/data';
import { fmt } from '@/lib/format';
import { Panel, Table, VHead, Defs } from '../ui';

export default function About() {
  return (
    <>
      <VHead title="About this dashboard">
        What it covers, how to read it, and where each number comes from.
      </VHead>

      <Panel title="Purpose">
        <Defs
          items={[
            [
              'What this is',
              'A view of the Vermont labour market built for Strada Education Foundation and the Vermont State Colleges System: what the state employs, what that work pays, where employers are hiring, and how VSCS credential production sits against occupational demand.',
            ],
            [
              'Scope',
              `Vermont only. ${fmt(LC.allOcc.length)} detailed occupations covering ${fmt(TOTJ)} jobs, ${fmt(DATA.families.length)} occupational families, all 14 counties, and the two VSCS institutions — the Community College of Vermont and Vermont State University.`,
            ],
            [
              'Period',
              `Employment and wages are 2025, change is measured over 2021–2025, and projections run to 2030.`,
            ],
            [
              'What it is not',
              'Not a forecast and not a program recommendation. It reports what the sources say and states where they disagree.',
            ],
            [
              'Not live',
              'Build scripts pull from BigQuery and the Lightcast exports and write a small set of JSON files that the app reads at build time. Numbers change only when a script is re-run and the app redeployed.',
            ],
            [
              'Where the detail is',
              'Sources, measure definitions and every suppression rule are on the Methods \u0026 limits tab. Each panel also carries its own source line.',
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
                'Headline scale of the labour market, and the gap between what jobs require and what workers hold',
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
                'Occupations scoring highest on scale, growth, advertised demand and pay together, at each credential level',
              ],
            },
            {
              cells: [
                'VSCS alignment',
                'VSCS completions set against annual openings, by family and by occupation',
              ],
            },
            {
              cells: ['Regions', 'How attainment, earnings and the local cost floor differ across the 14 counties'],
            },
            {
              cells: [
                'Methods & limits',
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
