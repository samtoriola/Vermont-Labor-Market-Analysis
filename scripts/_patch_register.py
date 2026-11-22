"""Adds the workfile column to every row of the Methods source register."""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "components", "views", "Methods.js")
s = io.open(P, encoding="utf-8").read()

WORKFILE = {
    "Overview": "02_overview_and_wage_by_group.csv",
    "Employment · Industry sectors": "06_employment_sectors.csv",
    "Employment · Occupation": "07_employment_occupation_groups.csv",
    "Wage quality · Wage benchmark": "02_overview_and_wage_by_group.csv",
    "Wage quality · County living wage": "05_wage_county_floor.csv",
    "Demand & growth · General demand": "12_demand_what_postings_ask.csv",
    "Demand & growth · Hiring and growth": "01_occupations_master.csv",
    "Pathways · By credential level": "03_pathways_credential_ladder.csv",
    "Pathways · Which credentials pay": "04_pathways_openings_by_credential.csv",
    "Opportunities · Highest scoring": "08_opportunity_scores.csv",
    "VSCS alignment · Production by award": "10_vscs_production.csv",
    "VSCS alignment · Against demand": "09_vscs_alignment_by_group.csv",
    "Regions · County map": "13_regions_county_map.csv",
    "Regions · Counties compared": "11_regions_counties.csv",
}

# Each register row is `cells: [ 'Section', '...', '...', 'file' ],` -- find the
# one that opens with a known section name and append its workfile.
hits = 0
for section, wf in WORKFILE.items():
    pat = re.compile(
        r"(\{\s*\n\s*cells: \[\s*\n\s*'" + re.escape(section) + r"',\s*\n"
        r"(?:[^\]]*?\n)??\s*'[^']*',\s*\n)(\s*\],)",
        re.S,
    )
    new, n = pat.subn(lambda m: m.group(1) + m.group(0)[0:0]
                      + "                '" + wf + "',\n" + m.group(2), s)
    if n != 1:
        print("  !! %s matched %d times" % (section, n))
    else:
        s = new
        hits += 1

assert hits == len(WORKFILE), "%d of %d rows matched" % (hits, len(WORKFILE))
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Methods.js patched, %d register rows carry a workfile" % hits)
