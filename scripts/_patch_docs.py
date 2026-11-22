"""Brings About and Methods to the current dashboard and names the workfiles."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def edit(rel, pairs):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        assert s.count(old) == 1, "%s: %d occurrences of %r" % (rel, s.count(old), old[:70])
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


edit("components/views/About.js", [
    # Sources as a list of named sources rather than one sentence.
    ("""            [
              'Sources',
              'Lightcast Vermont exports for occupations, industries and job postings; Lightcast Core LMI for the county slice and for posting-level education, experience and geography; BLS OEWS for wage percentiles; Census CPS and ACS microdata for workers and earnings; IPEDS for credential production; MIT Living Wage for the self-sufficiency benchmark.',
            ],""",
     """            [
              'Sources',
              'Six, and every figure traces to one of them. Lightcast Vermont exports — occupations, industries and job postings, 2021–2025. Lightcast Core LMI — the county slice, and posting-level education, experience and geography. BLS OEWS 2025 — the wage percentiles every pay figure is read off. IPEDS 2024 — credential production at the Community College of Vermont and Vermont State University, with the federal CIP-to-SOC crosswalk linking a programme to the occupations it feeds. MIT Living Wage 2025 — the self-sufficiency benchmark, statewide and per county. Census ACS — county attainment and median income, on the Regions map only. Methods names which of them sits behind each chart, and what each chart calls it.',
            ],"""),

    # How the data gets in, plus where to check it.
    ("""            [
              'How the data gets in',
              'Nothing is queried live. Build scripts pull from BigQuery and the Lightcast exports and write a small set of JSON files that the app reads at build time. Numbers change only when a script is re-run and the app redeployed.',
            ],""",
     """            [
              'How the data gets in',
              'Nothing is queried live. Build scripts in scripts/ pull from BigQuery and the Lightcast exports and write eleven JSON files that the app imports at build time. Numbers change only when a script is re-run and the app redeployed, so what is on screen is always the committed data and never a live query that might answer differently tomorrow.',
            ],
            [
              'Checking the numbers',
              'The workfiles/ folder carries every figure the dashboard draws as a spreadsheet, built from the same JSON the app reads. Each one holds the inputs and the intermediate steps rather than only the answer, so a measure can be redone with a calculator. Start at 00_headline_figures.csv, which lists each number quoted in a caption or a tile with the file and the arithmetic that reproduces it.',
            ],"""),

    # Two tab descriptions that no longer match what the tab draws.
    ("""                'Pathways',
                'What the credential ladder pays, measured on what jobs require. Jobs, not people',""",
     """                'Pathways',
                'The pay range of each rung of the credential ladder with the benchmark ruled across it, and how much of a year\\u2019s hiring at each pays a living wage. Measured on what jobs require, not on what workers hold',"""),
    ("""                'VSCS alignment',
                `How ${fmt(SOW.vscs.totalCompletions)} VSCS completions sit against ${fmt(SOW.vscs.openAll)} annual openings, by occupation group and by occupation`,""",
     """                'VSCS alignment',
                `What VSCS awards, and how its ${fmt(SOW.vscs.totalCompletions)} completions sit against the ${fmt(SOW.vscs.openCred)} openings a year that ask for a credential it awards \\u2014 of ${fmt(SOW.vscs.openAll)} in all`,"""),
    ("""                'Opportunities',
                'Occupations scoring highest on scale, growth, demand and pay — and which of them VSCS could act on',""",
     """                'Opportunities',
                'Occupations scoring highest on scale, growth, advertised demand and pay, each bar split into the four ranks the score is the mean of',"""),

    # The source line is only half the answer now.
    ("""              'Check where a number came from',
              'Every chart carries a source line underneath it, written in plain words rather than by vendor. Methods holds the key to those names and a row per section saying what it draws, which source it came from, and which file the app reads.',""",
     """              'Check where a number came from',
              'Every chart carries a source line underneath it, written in plain words rather than by vendor. Methods holds the key to those names and a row per section saying what it draws, which source it came from, which file the app reads, and which workfile reproduces it by hand.',"""),
])

edit("components/views/Methods.js", [
    # A workfile against every chart.
    ("""        <Table
          cols={['Section', 'What it draws', 'Source', 'File']}
          text={[1, 2, 3]}""",
     """        <Table
          cols={['Section', 'What it draws', 'Source', 'File', 'Workfile']}
          text={[1, 2, 3, 4]}"""),
    ("""        cap="One row per section. Where a section carries a measure control, every measure on it draws from the same files. The file column is what the app imports at build time; scripts/README.md says which script writes each one and what it reads."
      >""",
     """        cap="One row per section. Where a section carries a measure control, every measure on it draws from the same files. The file column is what the app imports at build time, and scripts/README.md says which script writes each one and what it reads. The workfile column is the spreadsheet in workfiles/ that reproduces that chart&rsquo;s figures by hand, inputs and intermediate steps included."
      >"""),
    ("""            [
              'Below a living wage',
              'The benchmark’s position along each occupation’s own percentile ladder, weighted by that occupation’s jobs and rolled up. Used by the Overview, Wage quality and Pathways, which is every chart that compares pay with self-sufficiency.""",
     """            [
              'Below a living wage',
              'The benchmark’s position along each occupation’s own percentile ladder, weighted by that occupation’s jobs and rolled up. Used by the Overview, Wage quality and Pathways, which is every chart that compares pay with self-sufficiency. Pathways’ hiring chart weights the same measure by annual openings rather than by jobs, because an occupation can hold a great many jobs and almost never hire."""),
])
