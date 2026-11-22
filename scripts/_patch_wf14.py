"""Two workfiles the home page needed and nobody had written.

The headline file claims to carry every number quoted in a caption, a read-out or
a tile, and the employed-Vermonters tile was not in it -- the one CPS figure on
screen had no workfile at all. 14 is the register behind the tiles' new hover
cards; 15 is the labour-force detail that checks the second of them.

While here: 00 told a reader to check "Jobs, 2025" by summing 01, which gives a
different number. 01 excludes military and unmapped SOCs, so the sum is 1,450
short of the statewide total. Saying so is the point of the file.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "build_workfiles.py")
s = io.open(P, encoding="utf-8").read()

subs = [
    ('DEM = D("demand.json")',
     'DEM = D("demand.json")\nGLA = D("glance.json")'),

    # ---- the two new files, written before the headline file ---------------
    ("# ------------------------------------------------------------- the headlines --",
     '''# ------------------------------------------------------------ the home page --
# One row per tile, carrying what the tile's hover card says: the four headline
# figures come from four sources and two universes -- jobs and people -- which do
# not add together, and the tiles are the one place they sit side by side.
charted = sum(o.get("j") or 0 for o in LC["allOcc"])
write(
    "14_home_tiles.csv",
    ["tile", "value", "what_it_counts", "source", "vintage", "data_file",
     "workfile_to_check", "how_to_check_it"],
    [
        ["Jobs, 2025", n1(LC["totalJobs"]),
         "Jobs located in Vermont, not people; someone holding two counts twice",
         "Lightcast Vermont occupation export", "2025", "data/lightcast.json",
         "01_occupations_master.csv",
         "Export total. The %s charted occupations sum to %s; the %s difference is "
         "military and unmapped SOCs, which 01 excludes"
         % (len(LC["allOcc"]), n1(charted), n1(LC["totalJobs"] - charted))],
        ["Employed Vermonters", GLA["emp"],
         "People with a job, counted where they live; a survey estimate, not a count",
         "Census CPS microdata (IPUMS)",
         "%s, %d months" % (GLA["year"], GLA["months"]), "data/glance.json",
         "15_labor_force_cps.csv",
         "Weighted monthly average over the %d months of %s available"
         % (GLA["months"], GLA["year"])],
        ["Annual openings", n1(LC["openTotal"] / LC["openYears"]),
         "Openings a year, including replacing people who leave, not only new jobs",
         "Lightcast Vermont occupation export", LC["window"], "data/lightcast.json",
         "00_headline_figures.csv",
         "%s openings over the window / %d" % (n1(LC["openTotal"]), LC["openYears"])],
        ["VSCS completions", V["totalCompletions"],
         "Credentials awarded, not people; one graduate finishing two counts twice",
         "IPEDS", "2024 academic year", "data/sow.json", "10_vscs_production.csv",
         "Sum of completions in 10, across CCV and Vermont State University"],
    ],
    "Home. One row per headline tile, which is what that tile's hover card says: "
    "source, vintage, the file the app reads and the workfile that reproduces it. "
    "The four figures count two different things -- the first and third count "
    "jobs, the second counts people, the fourth counts credentials -- so none of "
    "them adds to another.",
)

# The one CPS figure on screen. Carried in full rather than alone, because an
# employment count with no labour force or unemployment beside it cannot be
# sanity-checked against anything.
write(
    "15_labor_force_cps.csv",
    ["measure", "value", "note"],
    [
        ["Year", GLA["year"], "Months available: %d" % GLA["months"]],
        ["Population 16 and over", n1(GLA["pop16"]), "Civilian, non-institutional"],
        ["Labor force", n1(GLA["lf"]), "Employed plus unemployed"],
        ["Employed", n1(GLA["emp"]), "The home page tile"],
        ["Unemployed", n1(GLA["unemp"]), "Looking for work and available for it"],
        ["Labor force participation rate", GLA["lfpr"], "Labor force / population 16+"],
        ["Unemployment rate", GLA["ur"], "Unemployed / labor force"],
        ["Unemployment rate, 95% interval", GLA["urCi"],
         "Plus or minus, in points; survey estimate, not the official LAUS series"],
        ["Working full time", n1(GLA["ft"]), "Usual hours 35 or more: %.1f%%" % GLA["ftShare"]],
        ["Working part time", n1(GLA["pt"]), "Usual hours under 35: %.1f%%" % GLA["ptShare"]],
        ["Hours vary", n1(GLA["vary"]),
         "%.1f%% report hours that vary and cannot be placed either side" % GLA["varyShare"]],
        ["Sample: labor force records", GLA["nLf"], "Person-months, not people"],
        ["Sample: distinct people", GLA["nPeopleLf"],
         "The survey re-interviews households, so rates use this, not the record count"],
        ["Sample: unemployed records", GLA["nUnemp"],
         "Small, which is why the rate carries an interval"],
    ],
    "Home / Employed Vermonters. The Census household survey (CPS) figures behind "
    "the one CPS number the dashboard draws. Weighted estimates from Vermont "
    "monthly microdata; October 2025 is missing nationally, so the year is an "
    "11-month average. These count PEOPLE where they live, and the job counts "
    "elsewhere in these files count JOBS where they are located: the two differ by "
    "construction and should not be differenced.",
)

# ------------------------------------------------------------- the headlines --'''),

    # ---- 00: say what summing 01 actually gives ----------------------------
    ('''    ["Jobs, 2025", n1(LC["totalJobs"]), "data/lightcast.json totalJobs",
     "Sum of jobs_2025 in 01", "Employment / every tab"],''',
     '''    ["Jobs, 2025", n1(LC["totalJobs"]), "data/lightcast.json totalJobs",
     "Export total; 01 sums to %s, %s less, being military and unmapped SOCs"
     % (n1(charted), n1(LC["totalJobs"] - charted)), "Home / every tab"],
    ["Jobs in the charted occupations", n1(charted), "01, all rows",
     "Sum of jobs_2025 in 01", "Every chart that ranks or compares work"],
    ["Employed Vermonters", GLA["emp"], "data/glance.json emp",
     "15, Employed; a PEOPLE count, not comparable with the job counts above",
     "Home"],'''),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:90]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("build_workfiles.py patched,", len(s), "bytes")
