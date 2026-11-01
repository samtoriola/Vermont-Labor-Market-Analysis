'use client';

import { LC, TOTJ, SOW, GLANCE } from '@/lib/data';
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
              'Six, and every figure traces to one of them. Lightcast Vermont exports — occupations, industries and job postings, 2021–2025. Lightcast Core LMI — the county slice, and posting-level education, experience and geography. BLS OEWS 2025 — the wage percentiles every pay figure is read off. IPEDS 2024 — credential production at the Community College of Vermont and Vermont State University, with the federal CIP-to-SOC crosswalk linking a programme to the occupations it feeds. MIT Living Wage 2025 — the self-sufficiency benchmark, statewide and per county. Census ACS — county attainment and median income, on the Regions map only. Methods names which of them sits behind each chart, and what each chart calls it.',
            ],
            [
              'Filter',
              `Vermont only. ${fmt(LC.allOcc.length)} detailed occupations, ${fmt(LC.families.length)} occupation groups, all 14 counties, and the two VSCS institutions — the Community College of Vermont and Vermont State University.`,
            ],
            [
              'Unit of analysis',
              'Two units, and they are not interchangeable. Lightcast and OEWS count jobs and what a job asks for at entry — including the credential a job asks for, which is not the credential the person in it holds. The Census surveys count people, and reach two figures: employed Vermonters, on the home page, and what a county\u2019s residents hold and earn, on the Regions map. Every chart that ranks or compares work counts jobs, each panel says which, and no chart puts a jobs figure and a people figure on the same scale.',
            ],
            [
              'When outcomes are measured',
              `Employment and wages are 2025. Change is measured over 2021–2025, projections run to 2030, job postings cover ${LC.postWindow}, and credential production is the 2024 academic year.`,
            ],
            [
              'How the data gets in',
              'Nothing is queried live. Build scripts in scripts/ pull from BigQuery and the Lightcast exports and write eleven JSON files that the app imports at build time. Numbers change only when a script is re-run and the app redeployed, so what is on screen is always the committed data and never a live query that might answer differently tomorrow.',
            ],
            [
              'Checking the numbers',
              'The workfiles/ folder carries every figure the dashboard draws as a spreadsheet, built from the same JSON the app reads. Each one holds the inputs and the intermediate steps rather than only the answer, so a measure can be redone with a calculator. Start at 00_headline_figures.csv, which lists each number quoted in a caption or a tile with the file and the arithmetic that reproduces it.',
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
                'The whole labor market on one chart: every occupation group by size, shaded by how much of its work pays below a living wage',
              ],
            },
            {
              cells: [
                'Employment',
                'Which occupation groups and industries employ Vermonters, and what each pays',
              ],
            },
            {
              cells: [
                'Wage quality',
                'How much of the work pays less than a self-sufficiency benchmark, and how that changes when each county is measured against its own cost floor',
              ],
            },
            {
              cells: [
                'Demand & growth',
                'What employers ask for at the door by place, and where openings, advertised demand and projected growth concentrate',
              ],
            },
            {
              cells: [
                'Pathways',
                'The pay range of each rung of the credential ladder with the benchmark ruled across it, and how much of a year\u2019s hiring at each pays a living wage. Measured on what jobs require, not on what workers hold',
              ],
            },

            {
              cells: [
                'Opportunities',
                'Occupations scoring highest on scale, growth, advertised demand and pay, each bar split into the four ranks the score is the mean of',
              ],
            },
            {
              cells: [
                'VSCS alignment',
                `What VSCS awards, and how its ${fmt(SOW.vscs.totalCompletions)} completions sit against the ${fmt(SOW.vscs.openCred)} openings a year that ask for a credential it awards \u2014 of ${fmt(SOW.vscs.openAll)} in all`,
              ],
            },
            {
              cells: [
                'Regions',
                'How jobs, pay, attainment and the local cost floor differ across the 14 counties, and what each county is concentrated in',
              ],
            },
            {
              cells: [
                'Methods',
                'Sources, what each measure means, and the rules applied to the data',
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
              'The Overview, Wage quality, Pathways, Opportunities and Regions all carry a household selector. It moves every figure that compares pay with self-sufficiency, so set it before reading those tabs. The default is one adult with no children, which is the only household MIT publishes for every county.',
            ],
            [
              'Click through to the detail',
              'Bars and table rows that sit on underlying occupations open a panel beside the chart, with that row’s figures and its largest occupations. A link in the panel opens the whole table. The Overview, Employment, Wage quality, Demand & growth, Pathways and VSCS alignment all support it.',
            ],
            [
              'Check where a number came from',
              'Every chart carries a source line underneath it, written in plain words rather than by vendor, and each of the four tiles on the home page carries its own on hover — source, vintage, the file the app reads, and the workfile that reproduces it. Methods holds the key to those names and a row per section saying what it draws, which source it came from, which file the app reads, and which workfile reproduces it by hand.',
            ],
            [
              'Read the line above each chart',
              'Every section opens with one line saying what it shows and what its controls do. Where a section carries a measure control, it is one panel answering several questions rather than several pages, and the read-out under the chart follows whichever you pick.',
            ],
            [
              'Search, filter and sort inside a table',
              'Every detail table and the full occupation table take a text search, a numeric range filter on any column, and sorting by any column. Sorting is on the underlying value, so money and percentages order correctly.',
            ],
            [
              'Where the definitions live',
              'Methods holds every measure, the rules applied, and what the data cannot tell you. Each chart carries a short caption and a source line; Methods is where the full definition sits.',
            ],
            [
              'Take the figures behind any chart',
              'Every chart carries a Show the figures link underneath it. That opens the table the chart was drawn from — sort it any way, search it, or download the CSV — and on charts that drill down, the rows open the same detail the chart does.',
            ],
            [
              'Export what you filtered',
              'The download button on a table exports the rows you are looking at, not the whole dataset — filter first, then export.',
            ],
            [
              'Pick a category instead of scrolling past them',
              'Where a section would otherwise stack one panel per category — the credential tiers on Opportunities, for instance — it shows one and gives you buttons to switch.',
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
              'Hover any mark',
              'Every mark carries its own figures on hover — a bar, a point on a scatter, one segment of a split bar, or one rung of a pay range. A segment names the measure it is as well as its value, so a score built from four ranks can be read a rank at a time.',
            ],
          ]}
        />
      </Panel>
    </>
  );
}
