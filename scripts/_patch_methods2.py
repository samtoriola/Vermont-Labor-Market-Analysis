"""Methods, against what the dashboard actually draws now.

With Workers hidden and the dot columns long gone, the Census surveys reach the
screen in two places: the Home page's employed-Vermonters tile, and county
attainment and income on the Regions map. Four rules and one source row still
described person-level earnings charts, sampled dot columns and a jobs-against-
workers comparison that nothing draws.

The rules are commented rather than deleted, the same way the sections they
describe are, so restoring one restores the other.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "components", "views", "Methods.js")
s = io.open(P, encoding="utf-8").read()
subs = [
    # ---- the two Census rows, narrowed to what they still provide ----------
    ("""                'CPS (IPUMS)',
                'Vermont monthly microdata — labor force, attainment held',
                '2021–2025',
                '“Census household survey”',""",
     """                'CPS (IPUMS)',
                'Vermont monthly microdata. Reaches one figure: the employed-Vermonters tile on the home page',
                '2021–2025',
                '“Census household survey”',"""),
    ("""                'ACS (IPUMS)',
                'Person-level earnings; county attainment and income',
                '1-year 2024; 5-year 2016–2020',
                '“Census household survey”, “County survey data”',""",
     """                'ACS (IPUMS)',
                'County attainment and median income, on the Regions map',
                '5-year 2016–2020',
                '“County survey data”',"""),

    # ---- the comparison nothing draws any more -----------------------------
    ("""            [
              'Jobs vs workers',
              'Lightcast counts jobs and what a job asks for (326,582). CPS counts employed residents and what they hold (335,775). The ~3% gap is definitional — compare shares, not levels.',
            ],""",
     """            [
              'Jobs vs workers',
              'Every chart that ranks or compares work counts jobs and what a job asks for at entry. The credential a job asks for is not the credential the person in it holds, and nothing here measures the second — the section that did is not currently in the dashboard. Where the Census surveys do appear, on the Regions map and the home page, they count people, and no chart puts a jobs figure and a people figure on the same scale.',
            ],"""),

    # ---- three rules describing charts that are not reachable --------------
    ("""            [
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
            ],""",
     """            // --- Hidden for now ------------------------------------------
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
            // ],"""),

    # ---- CPS precision, for the one figure it still governs ----------------
    ("""              'CPS precision',
              'October 2025 is missing nationally, so 2025 is an 11-month average. Vermont weights are near-uniform (Kish 0.94), so intervals assume a design effect near 1. 80,569 person-month records cover 16,887 distinct people, and rate intervals use the person count, not the record count, because the survey re-interviews the same households. The unemployment rate shown is the direct CPS estimate; Vermont’s official rate comes from the model-based LAUS series, so the two differ by construction.',""",
     """              'CPS precision',
              'Governs the employed-Vermonters figure on the home page, which is the only CPS number currently on screen. October 2025 is missing nationally, so 2025 is an 11-month average. 80,569 person-month records cover 16,887 distinct people, and anything computed as a rate would use the person count rather than the record count, because the survey re-interviews the same households. It is a direct survey estimate; Vermont’s official labour-force figures come from the model-based LAUS series, so the two differ by construction.',"""),

    # ---- and where to check any of it --------------------------------------
    ("""      <Panel
        title="Color\"""",
     """      <Panel
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
        title="Color\""""),
]
for old, _ in subs:
    assert s.count(old) == 1, "%d occurrences of %r" % (s.count(old), old[:70])
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Methods.js patched,", len(s), "bytes")
