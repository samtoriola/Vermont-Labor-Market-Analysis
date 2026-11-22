"""Review 11/18: the three terminology changes that run across every tab.

  Turnover            -> Replacement rate
  Entry credential    -> Typical entry education
  Typical pay         -> Median pay

The third is not the rename that was asked for. The review says "average pay",
and there is no average in the data: data/percentiles.json carries p10/p25/p50/
p75/p90 and nothing else, and `m` on every occupation is the p50. Relabelling a
median as an average would put a wrong word on about thirty surfaces in a
dashboard whose whole claim is that the label matches the arithmetic. "Median
pay" is the plain, precise version of "typical", which is what the note is
reaching for; a real mean needs an OEWS pull.

Labels are sentence case here, as every other label on the dashboard is, so it
is "Typical entry education" rather than "Typical Entry Education".

Checks every substitution before writing anything.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

# rel -> list of (old, new, expected_count)
EDITS = {
    # ---------------------------------------------------- Turnover ----------
    "components/Drill.js": [
        ("['Turnover', turn === null", "['Replacement rate', turn === null", 1),
    ],
    "components/occCols.js": [
        ("label: 'Turnover'", "label: 'Replacement rate'", 2),
        ("              'Turnover',", "              'Replacement rate',", 1),
        ("label: 'Typical pay'", "label: 'Median pay'", 2),
        ("label: 'Entry credential'", "label: 'Typical entry education'", 2),
        ("            ['Entry credential', d.t || '—'],",
         "            ['Typical entry education', d.t || '—'],", 1),
    ],
    "lib/tables.js": [
        ("label: 'Turnover'", "label: 'Replacement rate'", 1),
        ("label: 'Typical pay'", "label: 'Median pay'", 4),
        ("label: 'Typical job pays'", "label: 'Median pay'", 2),
        ("label: 'Entry credential'", "label: 'Typical entry education'", 3),
    ],
    # ------------------------------------------- Entry credential ----------
    "components/Filters.js": [
        ('<span className="flab">Entry credential</span>',
         '<span className="flab">Typical entry education</span>', 1),
    ],
    "lib/screen.js": [
        ("label: 'Entry credential'", "label: 'Typical entry education'", 1),
        ("label: 'Typical pay'", "label: 'Median pay'", 1),
    ],
    # ------------------------------------------------------- views ---------
    "components/views/Q1.js": [
        ("{ id: 'pay', label: 'Typical pay' }", "{ id: 'pay', label: 'Median pay' }", 1),
        ("{ id: 'credential', label: 'Entry credential' }",
         "{ id: 'credential', label: 'Typical entry education' }", 1),
        ("'Typical pay'],", "'Median pay'],", 1),
        ("valueLabel: 'Typical pay',", "valueLabel: 'Median pay',", 1),
        ("aria: 'Typical pay by occupation group',", "aria: 'Median pay by occupation group',", 1),
    ],
    "components/views/Q2.js": [
        ("{ id: 'cred', label: 'Entry credential' }",
         "{ id: 'cred', label: 'Typical entry education' }", 1),
        ("kind === 'cred' ? 'Entry credential' :", "kind === 'cred' ? 'Typical entry education' :", 1),
        ("['Entry education', r.t],", "['Typical entry education', r.t],", 1),
    ],
    "components/views/Q4.js": [
        ("label: 'Entry credential',", "label: 'Typical entry education',", 4),
        ("bandCols(LWA, 't', 'Entry credential')", "bandCols(LWA, 't', 'Typical entry education')", 1),
        ("'Typical pay'],", "'Median pay'],", 1),
    ],
    "components/views/Q5.js": [
        ("'Typical pay'],", "'Median pay'],", 2),
        ("['Typical pay', r.m ? money(r.m) : '—'],", "['Median pay', r.m ? money(r.m) : '—'],", 2),
        ("['Entry credential', r.t],", "['Typical entry education', r.t],", 2),
    ],
    "components/views/Q6.js": [
        ("label: 'Typical pay'", "label: 'Median pay'", 1),
        ("label: 'Entry credential'", "label: 'Typical entry education'", 1),
    ],
    "components/views/Q7.js": [
        ("{ id: 'pay', label: 'Typical pay' }", "{ id: 'pay', label: 'Median pay' }", 1),
        ('<div className="k">Typical job pays</div>', '<div className="k">Median pay</div>', 1),
        ("['Typical job pays', money(r.med)],", "['Median pay', money(r.med)],", 1),
        ("valueLabel: 'Typical pay',", "valueLabel: 'Median pay',", 1),
        ("aria: 'Typical pay by county',", "aria: 'Median pay by county',", 1),
        ("note: 'Jobs and typical pay are the county’s workplaces;",
         "note: 'Jobs and median pay are the county’s workplaces;", 1),
    ],
    "components/Detail.js": [
        ("cols: ['Occupation', 'Jobs', 'Typical pay'],",
         "cols: ['Occupation', 'Jobs', 'Median pay'],", 1),
    ],
    # ------------------------------------------------------ the prose ------
    "components/OccTable.js": [
        ("turnover is separations ÷ jobs and counts job-to-job transfers, so it reads as",
         "the replacement rate is separations ÷ jobs and counts job-to-job transfers, so it reads as", 1),
    ],
    "components/views/Methods.js": [
        ("              'Turnover',", "              'Replacement rate',", 1),
        ("'Jobs, typical pay, entry credential and age mix across 22 occupation groups'",
         "'Jobs, median pay, typical entry education and age mix across 22 occupation groups'", 1),
        ("'County jobs, typical pay, change since 2021, and what each county is concentrated in'",
         "'County jobs, median pay, change since 2021, and what each county is concentrated in'", 1),
        ("so growth, change and turnover are left blank below 10 jobs",
         "so growth, change and the replacement rate are left blank below 10 jobs", 1),
    ],
    "lib/insight.js": [
        ("`a top tail lifting it away from typical pay.`", "`a top tail lifting it away from median pay.`", 1),
        ("none(`Typical pay varies little across counties", "none(`Median pay varies little across counties", 1),
    ],
}

loaded = []
for rel, pairs in EDITS.items():
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _, want in pairs:
        got = s.count(old)
        if got != want:
            raise SystemExit("%s: %d occurrences of %r, expected %d" % (rel, got, old[:70], want))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    n = 0
    for old, new, want in pairs:
        s = s.replace(old, new)
        n += want
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-32s %2d replacements" % (rel, n))
