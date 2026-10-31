"""Builds data/counties.json from the materialised Core LMI county slice.

Closes the demand-side half of SOW research question 7. County attainment and
income were already on the Regions tab from the household survey; what was
missing was the labour market itself -- how many jobs each county holds, what
they pay, and what occupation group each county is actually made of. Reads the CSV
pull_counties.py wrote; queries nothing.

WHICH ROWS
----------
Classes 1 and 2 (QCEW and non-QCEW employees), because that is the basis every
other figure on the dashboard sits on: it reproduces the statewide total to
within 28 jobs out of 326,610. Adding the self-employed and extended proprietors
would put a county total 40% above the state total shown on every other tab. See
the long note in pull_counties.py.

TWO OCCUPATION LEVELS, FOR TWO DIFFERENT THINGS
-----------------------------------------------
Level 1 ("Total, All Occupations") is the county's employment. Level 5 (detailed
SOC) is what the family mix and the typical pay are built from. They are reported
independently by Lightcast and do not have to agree exactly, so the shares below
are taken against the level-5 sum rather than against the level-1 headline --
otherwise a county's 22 families would not add to 100%.

TYPICAL PAY
-----------
`earn_p50` is an hourly rate per occupation, so a county's "typical pay" is the
employment-weighted median across its detailed occupations, annualised at the
same 2,080 hours the living-wage benchmark already uses. It is the pay of the
midpoint *job*, which is not the pay of the midpoint worker -- the Workers tab
answers that from the household survey, and the two are not interchangeable.

CONCENTRATION
-------------
`lq` is a location quotient: the county's share of its jobs in a family against
Vermont's share of the same family. 1.0 means the county looks like the state.
It is a ratio of shares, so it says nothing about size -- Essex at 8.5x in
Farming & Forestry is 65 jobs. The chart prints the underlying count on hover
for exactly that reason, and the thin-county floor below marks the two counties
where a 22-way split rests on very little.
"""
import json
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
CTY = os.path.join(FOLDER, "VT_CoreLMI_Occupation_by_County_2021_2025.csv")
OUT = os.path.join(HERE, "..", "data", "counties.json")

YEAR = 2025
BASE = 2021
HOURS = 2080
CLASSES = [1, 2]

# Below this many jobs a 22-way split of the county is thinner than the
# differences a concentration chart draws with it. Essex (1,154) and Grand Isle
# (1,497) are the two; the next smallest county holds 8,766.
THIN = 3000

SOC_MAJOR = {
    "11": "Management", "13": "Business & Financial Operations",
    "15": "Computer & Mathematical", "17": "Architecture & Engineering",
    "19": "Life, Physical & Social Science", "21": "Community & Social Service",
    "23": "Legal", "25": "Educational Instruction & Library",
    "27": "Arts, Design, Entertainment & Media",
    "29": "Healthcare Practitioners & Technical", "31": "Healthcare Support",
    "33": "Protective Service", "35": "Food Preparation & Serving",
    "37": "Building & Grounds Cleaning", "39": "Personal Care & Service",
    "41": "Sales", "43": "Office & Administrative Support",
    "45": "Farming, Fishing & Forestry", "47": "Construction & Extraction",
    "49": "Installation, Maintenance & Repair", "51": "Production",
    "53": "Transportation & Material Moving", "55": "Military",
}

NAMES = {
    "50001": "Addison", "50003": "Bennington", "50005": "Caledonia",
    "50007": "Chittenden", "50009": "Essex", "50011": "Franklin",
    "50013": "Grand Isle", "50015": "Lamoille", "50017": "Orange",
    "50019": "Orleans", "50021": "Rutland", "50023": "Washington",
    "50025": "Windham", "50027": "Windsor",
}
STATE = "50"


def load():
    d = pd.read_csv(CTY, dtype={"areaid": str, "occid": str, "classid": int})
    d["year"] = d["year"].astype(float).astype(int)
    d["occ_level"] = d["occ_level"].astype(float).astype(int)
    d = d[d.classid.isin(CLASSES)]
    d = d[d.areaid.isin(list(NAMES) + [STATE])]
    d["fam"] = d["occid"].str[:2].map(SOC_MAJOR)
    # The statewide export carries 22 families and no Military, so the county
    # mix drops it too -- otherwise the Regions chart would have a row no other
    # family chart on the dashboard has, and the shares would be against a
    # different base than every statewide figure they get compared with.
    d.loc[d.fam == "Military", "fam"] = None
    return d


def weighted_median(df):
    """Pay of the midpoint job, not the mean of the occupation medians.

    Sorting by rate and walking up the employment is the only way to get the
    midpoint job out of per-occupation percentiles: averaging them would weight
    a 60-job occupation the same as a 6,000-job one.
    """
    d = df[df.earn_p50.notna() & (df.emp > 0)].sort_values("earn_p50")
    if d.empty:
        return None
    cum = d.emp.cumsum()
    half = d.emp.sum() / 2
    hit = d[cum >= half]
    return float(hit.iloc[0].earn_p50) * HOURS


def main():
    if not os.path.isfile(CTY):
        print("REFUSED: %s is not there -- run pull_counties.py first." % CTY)
        return 1

    d = load()
    now = d[d.year == YEAR]
    then = d[d.year == BASE]

    # Level 1 is the headline employment; level 5 is everything else.
    tot = now[now.occ_level == 1].groupby("areaid").emp.sum()
    tot21 = then[then.occ_level == 1].groupby("areaid").emp.sum()
    det = now[(now.occ_level == 5) & now.fam.notna()]

    # Families ordered by state employment, so the chart's rows run largest
    # first rather than alphabetically.
    st_fam = det[det.areaid == STATE].groupby("fam").emp.sum().sort_values(ascending=False)
    st_total = st_fam.sum()
    fam_order = [f for f in st_fam.index if st_fam[f] > 0]
    st_share = {f: st_fam[f] / st_total * 100 for f in fam_order}

    counties = []
    for aid, name in NAMES.items():
        c = det[det.areaid == aid]
        base = c.emp.sum()
        if not base:
            print("  skipped %s: no detailed rows" % name)
            continue
        fam = c.groupby("fam").emp.sum()
        mix, lq, cnt = {}, {}, {}
        for f in fam_order:
            jobs = float(fam.get(f, 0))
            share = jobs / base * 100
            mix[f] = round(share, 1)
            lq[f] = round(share / st_share[f], 2) if st_share[f] else None
            cnt[f] = int(round(jobs))
        emp = float(tot.get(aid, 0))
        e21 = float(tot21.get(aid, 0))
        counties.append({
            "k": aid,
            "c": name,
            "emp": int(round(emp)),
            "emp21": int(round(e21)),
            "chg": round((emp / e21 - 1) * 100, 1) if e21 else None,
            "med": int(round(weighted_median(c))),
            "nocc": int((c.emp > 0).sum()),
            "mix": mix,
            "lq": lq,
            "jobs": cnt,
            # Marked rather than dropped: a county this small still belongs on a
            # ranking, it just cannot carry a 22-way split.
            "thin": emp < THIN,
        })

    counties.sort(key=lambda r: -r["emp"])

    st_emp = float(tot.get(STATE, 0))
    st_e21 = float(tot21.get(STATE, 0))
    out = {
        "year": YEAR,
        "base": BASE,
        "thinFloor": THIN,
        "famOrder": fam_order,
        "state": {
            "c": "Vermont",
            "emp": int(round(st_emp)),
            "emp21": int(round(st_e21)),
            "chg": round((st_emp / st_e21 - 1) * 100, 1) if st_e21 else None,
            "med": int(round(weighted_median(det[det.areaid == STATE]))),
            "share": {f: round(st_share[f], 1) for f in fam_order},
        },
        "counties": counties,
        "note": ("Employees only. Typical pay is the midpoint job, annualised at "
                 "%s hours." % f"{HOURS:,}"),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))

    print("wrote %s (%s bytes)" % (OUT, f"{os.path.getsize(OUT):,}"))
    print("%-13s %9s %9s %8s  %s" % ("COUNTY", "JOBS", "TYPICAL", "CHG", "MOST CONCENTRATED"))
    for r in counties:
        top = sorted(fam_order, key=lambda f: -(r["lq"][f] or 0))[0]
        print("%-13s %9s %9s %+7.1f%%  %s (%.1fx)%s"
              % (r["c"], f"{r['emp']:,}", f"${r['med']:,}", r["chg"], top, r["lq"][top],
                 "   THIN" if r["thin"] else ""))
    print("%-13s %9s %9s %+7.1f%%" % ("Vermont", f"{out['state']['emp']:,}",
                                      f"${out['state']['med']:,}", out["state"]["chg"]))

    # The counties are reported independently of the state, so this is a check
    # rather than an identity -- but a large gap would mean the slice is wrong.
    parts = sum(r["emp"] for r in counties)
    print("\n14 counties %s vs state %s (%+.2f%%)"
          % (f"{parts:,}", f"{out['state']['emp']:,}", (parts / out["state"]["emp"] - 1) * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
