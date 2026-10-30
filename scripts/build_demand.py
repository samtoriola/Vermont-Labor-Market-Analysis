"""Builds data/demand.json from the materialised postings slice.

What employers ask for at the door -- education and experience -- for Vermont
against four of its counties, the rest of the state, a neighbouring state and
the country. Reads the CSV pull_postings.py wrote; queries nothing.

THE DENOMINATOR IS THE WHOLE POINT
----------------------------------
`min_edulevels_name` is never null: a posting that names no education level
carries the literal 'No Education Listed'. Just over half of Vermont postings
do. Every share here is therefore out of postings that *state* a level, not out
of all postings, and the panel has to say so -- otherwise a reader takes "41% of
Vermont postings want a bachelor's" as a fact about Vermont's labour demand when
it is a fact about the half of employers who filled that field in.

The counts behind each share are kept alongside it so the figure can always be
put back on the larger base.

WHICH COLUMNS
-------------
Four named counties, chosen by employment (from the Core LMI county slice), not
by posting volume -- posting volume is exactly the thing the panel is measuring
and would be circular. The rest of the state is one column so the named counties
do not have to carry the whole comparison, and New Hampshire and the United
States are the two benchmarks the pay charts already use.

WASHINGTON COUNTY
-----------------
Washington posts 63,322 times against 48,390 jobs -- 1.31 postings per job,
where Chittenden runs 0.44. It is Montpelier, so state government is the obvious
explanation, but posting intensity three times the largest county's is a
property of who writes postings, not of who hires. The build records the ratio
so the panel can show it rather than let a reader assume otherwise.
"""
import json
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
REQ = os.path.join(FOLDER, "VT_Postings_Education_Experience_by_Area.csv")
CTY = os.path.join(FOLDER, "VT_CoreLMI_Occupation_by_County_2021_2025.csv")
OUT = os.path.join(HERE, "..", "data", "demand.json")

WINDOW = "August 2024 \u2013 July 2026"
NOT_STATED_EDU = "No Education Listed"
NOT_STATED_EXP = "Not stated"

# Master's and doctoral/professional are one rung for this purpose: the question
# a reader brings is whether the door asks for a graduate degree, not which one.
EDU_ORDER = ["High school or GED", "Associate degree", "Bachelor's degree", "Graduate degree"]
EDU_MAP = {
    "High school or GED": "High school or GED",
    "Associate degree": "Associate degree",
    "Bachelor's degree": "Bachelor's degree",
    "Master's degree": "Graduate degree",
    "Ph.D. or professional degree": "Graduate degree",
}
EXP_ORDER = ["0 - 1 years", "2 - 3 years", "4 - 6 years", "7 - 9 years", "10+ years"]

NAMED = ["Chittenden", "Washington", "Windsor", "Rutland"]


def county_employment():
    """2025 employment by county, on the two classes the dashboard is built on."""
    d = pd.read_csv(CTY, dtype={"areaid": str})
    d["year"] = d["year"].astype(float).astype(int)
    d["occ_level"] = d["occ_level"].astype(int)
    d = d[(d.year == 2025) & (d.occ_level == 1) & (d.classid.isin([1, 2]))]
    return d.groupby("areaid").emp.sum()


def main():
    raw = pd.read_csv(REQ)
    emp = county_employment()

    # areaid -> the county name as the postings table spells it
    CODES = {
        "Addison": "50001", "Bennington": "50003", "Caledonia": "50005", "Chittenden": "50007",
        "Essex": "50009", "Franklin": "50011", "Grand Isle": "50013", "Lamoille": "50015",
        "Orange": "50017", "Orleans": "50019", "Rutland": "50021", "Washington": "50023",
        "Windham": "50025", "Windsor": "50027",
    }

    def bucket(area, atype):
        if atype != "COUNTY":
            return area
        name = area.replace(", VT", "")
        return name if name in NAMED else "Rest of Vermont"

    raw["bucket"] = [bucket(a, t) for a, t in zip(raw.area, raw.area_type)]
    # The state row and the county rows both exist in the pull; using both would
    # count every Vermont posting twice.
    vt_counties = raw[raw.area_type == "COUNTY"].copy()
    others = raw[raw.area_type != "COUNTY"].copy()

    cols = NAMED + ["Rest of Vermont"]
    areas = []

    def series(df, field, order, not_stated, mapper=None):
        d = df.copy()
        if mapper:
            d = d[d[field] != not_stated]
            d["k"] = d[field].map(mapper)
        else:
            d = d[d[field] != not_stated]
            d["k"] = d[field]
        g = d.groupby("k").postings.sum()
        return [int(g.get(k, 0)) for k in order]

    def add(key, label, df, employment=None):
        tot = int(df.postings.sum())
        e = series(df, "education", EDU_ORDER, NOT_STATED_EDU, EDU_MAP)
        x = series(df, "experience", EXP_ORDER, NOT_STATED_EXP)
        areas.append({
            "k": key,
            "label": label,
            "postings": tot,
            "edu": e,
            "exp": x,
            "eduStated": sum(e),
            "expStated": sum(x),
            # Postings per job, where employment is known. The reason Washington
            # cannot be read as "more demand" without this number beside it.
            "perJob": round(tot / employment, 2) if employment else None,
        })

    add("vt", "Vermont", others[others.area == "Vermont"], float(emp.get("50", 0)) or None)
    for n in NAMED:
        add(n.lower(), n, vt_counties[vt_counties.area == n + ", VT"],
            float(emp.get(CODES[n], 0)) or None)
    rest_emp = sum(float(emp.get(CODES[n], 0)) for n in CODES if n not in NAMED)
    add("rest", "Rest of Vermont",
        vt_counties[~vt_counties.area.isin([n + ", VT" for n in NAMED])], rest_emp or None)
    add("nh", "New Hampshire", others[others.area == "New Hampshire"])
    add("us", "United States", others[others.area == "United States"])

    out = {
        "window": WINDOW,
        "eduOrder": EDU_ORDER,
        "expOrder": EXP_ORDER,
        "areas": areas,
        "note": ("Non-staffing, unique postings for permanent positions, excluding "
                 "internships. Shares are of postings that state a level."),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))

    print("wrote %s (%s bytes)" % (OUT, f"{os.path.getsize(OUT):,}"))
    print("%-18s %10s %10s %7s  %s" % ("AREA", "POSTINGS", "STATED", "PER JOB", "BA+ SHARE"))
    for a in areas:
        ba = (a["edu"][2] + a["edu"][3]) / a["eduStated"] * 100 if a["eduStated"] else 0
        print("%-18s %10s %10s %7s  %5.1f%%"
              % (a["label"], f"{a['postings']:,}", f"{a['eduStated']:,}",
                 a["perJob"] if a["perJob"] else "-", ba))

    # The parts have to reconstruct the whole, or a column is missing.
    parts = sum(a["postings"] for a in areas if a["k"] in
                [n.lower() for n in NAMED] + ["rest"])
    whole = [a for a in areas if a["k"] == "vt"][0]["postings"]
    print("\ncounty columns %s vs Vermont %s (%+.2f%%)"
          % (f"{parts:,}", f"{whole:,}", (parts / whole - 1) * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
