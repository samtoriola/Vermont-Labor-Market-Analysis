"""The rename, carried into the workfiles and the suites that read the screen.

A column name in workfiles/ that no longer matches the label above it on screen
is the drift this project exists to prevent, so 01, 03, 04, 07 and 08 take the
new names too. The e2e suites click chips by their text, so they fail loudly
rather than silently when a label moves -- which is the point -- but they have to
be told the new text.

build_counties.py's note is prose about the county median; build.py's "2025
Turnover Rate" is Lightcast's own column name in the export and is left alone,
because renaming someone else's column in a comment makes the export harder to
find, not easier.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

EDITS = {
    # ------------------------------------------------ the workfile columns --
    "scripts/build_workfiles.py": [
        ('"occupation_group", "entry_credential"', '"occupation_group", "typical_entry_education"', 2),
        ('"job_ads", "turnover_pct"', '"job_ads", "replacement_rate_pct"', 1),
        ('["entry_credential", "occupations_priced"', '["typical_entry_education", "occupations_priced"', 1),
        ('["entry_credential", "occupations",', '["typical_entry_education", "occupations",', 1),
        ('"openings_per_year", "turnover_pct"', '"openings_per_year", "replacement_rate_pct"', 1),
        ('"01 where entry_credential is sub-bacc', '"01 where typical_entry_education is sub-bacc', 1),
    ],
    "scripts/check_workfiles.py": [
        ('r["entry_credential"] == "High school"', 'r["typical_entry_education"] == "High school"', 1),
    ],
    # ---------------------------------------------------------- the suites --
    "scripts/e2e_industry.py": [
        ('has_text="Entry credential"', 'has_text="Typical entry education"', 1),
    ],
    "scripts/e2e_rates.py": [
        ("# Typical pay by family is a ranked bar chart", "# Median pay by family is a ranked bar chart", 1),
        ('pick(pg, "Occupation", "Typical pay")', 'pick(pg, "Occupation", "Median pay")', 1),
    ],
    "scripts/e2e_regions.py": [
        ('("Typical pay", "med", True, money, False)', '("Median pay", "med", True, money, False)', 1),
    ],
    "scripts/e2e_split.py": [
        ('("Occupation", "Typical pay", 0)', '("Occupation", "Median pay", 0)', 1),
        ("# Typical pay, Above living wage and Range of outcomes were three chips over",
         "# Median pay, Above living wage and Range of outcomes were three chips over", 1),
    ],
    "scripts/e2e_wage.py": [
        ('(("Entry credential", len(group_by', '(("Typical entry education", len(group_by', 1),
    ],
    "scripts/build_counties.py": [
        ('"note": ("Employees only. Typical pay is the midpoint job, annualised at "',
         '"note": ("Employees only. Median pay is the midpoint job, annualised at "', 1),
    ],
}

loaded = []
for rel, pairs in EDITS.items():
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _, want in pairs:
        got = s.count(old)
        if got != want:
            raise SystemExit("%s: %d of %r, expected %d" % (rel, got, old[:70], want))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    n = 0
    for old, new, want in pairs:
        s = s.replace(old, new)
        n += want
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-32s %2d replacements" % (rel, n))
