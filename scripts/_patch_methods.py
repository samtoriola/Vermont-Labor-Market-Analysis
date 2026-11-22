"""Adds the per-chart source register to Methods and brings the rest of the tab
up to the current app. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "components", "views", "Methods.js")
s = io.open(P, encoding="utf-8").read()


def sub(old, new, n=1):
    global s
    assert s.count(old) == n, "%d occurrences of %r" % (s.count(old), old[:70])
    s = s.replace(old, new)


# ---- 1. the Sources table gains the name each chart calls it by --------------
old_src = """      <Panel title="Sources">
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
      </Panel>"""

new_src = """      <Panel
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
      </Panel>"""
sub(old_src, new_src)

# ---- 2. the percentile definition states how far the published roll-up is out -
old_pct = """            [
              'Wage percentiles',
              'As published. One occupation shows its own percentiles and mean. Occupation group and tier ranges are the employment-weighted mean of their occupations’ percentiles — a faithful range, not an exact group quantile.',
            ],"""
new_pct = """            [
              'Wage percentiles',
              'As published. One occupation shows its own percentiles and mean. Occupation group and credential ranges are the employment-weighted mean of their occupations’ percentiles, which is not the same as the group’s own quantile: a mean of tenth percentiles averages away the spread between occupations, which at a credential level is most of the spread there is. It understates the range by up to 44% — graduate / professional reads 2.5× from lowest-paid tenth to highest, against 3.6× when the member occupations’ ladders are pooled. The ordering survives; the magnitude does not. Where a figure is pooled rather than published, the chart says so.',
            ],"""
sub(old_pct, new_pct)

# ---- 3. the colour key, after Ember left the wage charts ---------------------
old_col = """      <Panel title="Color" cap="Color follows the entity, never its rank. Ordered measures use one hue.">
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
      </Panel>"""
new_col = """      <Panel
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
      </Panel>"""
sub(old_col, new_col)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Methods.js patched,", len(s), "bytes")
