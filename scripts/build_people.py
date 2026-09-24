"""Person-level earnings dots from ACS 1-year 2024 microdata (IPUMS USA).

Every dot is ONE REAL ACS RESPONDENT, plotted at their own wage and salary income.
Columns hold more respondents than a chart can show, so each column carries a random
sample drawn WITHOUT replacement with probability proportional to the survey weight
(PERWT) -- so the visible cloud reflects the population distribution rather than the
raw respondent mix. The average and median lines are computed from the FULL weighted
sample, not from the sampled dots, so they are the true population figures.

Universe: wage and salary workers, aged 25-64, usually 35+ hours a week and 48+ weeks
a year, in a civilian occupation, with positive wage income. Full-time year-round keeps
the credential comparison from being a comparison of hours worked.

The self-employed are excluded (CLASSWKR = 1), which drops 252 of Vermont's 2,025
full-time year-round workers, 12.4% -- a higher share than New Hampshire's 8.5% or the
national 8.4%. Note that IPUMS counts the incorporated self-employed as self-employed
(98 of Vermont's 252), while OEWS counts those who draw a salary as wage and salary
workers, so this universe is very slightly tighter than the OEWS one.

Military occupations (SOC 55) are excluded too: 4 records in Vermont. Neither Lightcast
nor OEWS covers them, so this keeps the person charts on the same footing as the
occupation charts.

Earnings is INCWAGE, wage and salary income. With the self-employed removed, no kept
record reports zero wage income, so business income is not needed to fill a gap.

IPUMS top-codes the highest earnings per state (Vermont 2024: $954,000). Those records
sit far above the chart ceiling and draw as off-scale marks, so the censoring does not
distort anything visible.
"""
import json, os, pathlib
import numpy as np
import pandas as pd
import warnings
from google.cloud import bigquery

warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")
HERE = pathlib.Path(__file__).resolve().parent
RNG = np.random.default_rng(20260924)

AREA_DOTS = 1000   # dots per area column
CRED_DOTS = 250    # dots per credential column
NA_WAGE = 999998   # IPUMS INCWAGE N/A sentinel sits above this

# IPUMS EDUCD -> the dashboard's attainment ladder. Ordered low to high.
CREDS = [
    ("Less than high school", lambda e: e <= 61),
    ("High school diploma", lambda e: 62 <= e <= 64),
    ("Some college, no degree", lambda e: 65 <= e <= 80),
    ("Associate degree", lambda e: 81 <= e <= 83),
    ("Bachelor's degree", lambda e: e == 101),
    ("Graduate / professional", lambda e: 114 <= e <= 116),
]
CRED_NAMES = [n for n, _ in CREDS]

FAMS = json.load(open(HERE.parent / "data" / "lightcast.json"))["families"]
SOC2FAM = {}
for r in FAMS:
    SOC2FAM[r["f"]] = r["f"]
# SOC major group -> Lightcast family label, matched on the family list already in the app.
MAJOR = {
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
    "53": "Transportation & Material Moving",
    # No entry for SOC 55: military occupations are filtered out of the universe.
}
unknown = sorted(set(MAJOR.values()) - set(SOC2FAM))
assert not unknown, f"family labels do not match the app's list: {unknown}"

SQL = """
WITH g AS (SELECT DISTINCT SERIAL, STATEFIP FROM `strada-data-lab-c9d1.ipums_usa.2024_acs1_household_geographic`),
i AS (SELECT SERIAL, PERNUM, PERWT, INCWAGE FROM `strada-data-lab-c9d1.ipums_usa.2024_acs1_person_income`),
e AS (SELECT SERIAL, PERNUM, EDUCD FROM `strada-data-lab-c9d1.ipums_usa.2024_acs1_person_education`),
w AS (SELECT SERIAL, PERNUM, EMPSTAT, UHRSWORK, WKSWORK2, CLASSWKR, OCCSOC FROM `strada-data-lab-c9d1.ipums_usa.2024_acs1_person_work`),
d AS (SELECT SERIAL, PERNUM, AGE FROM `strada-data-lab-c9d1.ipums_usa.2024_acs1_person_demographic`)
SELECT g.STATEFIP AS st, e.EDUCD AS educd, d.AGE AS age, i.PERWT AS wt,
       i.INCWAGE AS wage, w.UHRSWORK AS hrs, w.OCCSOC AS soc
FROM i
JOIN e USING (SERIAL, PERNUM)
JOIN w USING (SERIAL, PERNUM)
JOIN d USING (SERIAL, PERNUM)
JOIN g USING (SERIAL)
WHERE w.EMPSTAT = 1
  AND d.AGE BETWEEN 25 AND 64
  AND w.UHRSWORK >= 35
  AND w.WKSWORK2 >= 5
  AND w.CLASSWKR = 2
  AND NOT STARTS_WITH(CAST(w.OCCSOC AS STRING), '55')
  AND i.INCWAGE > 0
  AND i.INCWAGE < 999998
  AND i.PERWT > 0
"""

print("pulling ACS 1-year 2024 person records ...")
df = c.query(SQL).to_dataframe()
print(f"  {len(df):,} respondents nationwide")

df["cred"] = -1
for k, (_, test) in enumerate(CREDS):
    df.loc[df["educd"].map(test), "cred"] = k
df = df[df["cred"] >= 0]
df["fam"] = df["soc"].astype(str).str[:2].map(MAJOR).fillna("Unclassified")
df["wt"] = df["wt"].astype(float)
df["wage"] = df["wage"].astype(float)
print(f"  {len(df):,} with a classifiable credential")


def wmean(v, w):
    return float(np.average(v, weights=w))


def wmedian(v, w):
    o = np.argsort(v)
    v, w = np.asarray(v)[o], np.asarray(w)[o]
    cw = np.cumsum(w)
    return float(np.interp(cw[-1] / 2, cw, v))


def wpct(v, w, q):
    o = np.argsort(v)
    v, w = np.asarray(v)[o], np.asarray(w)[o]
    cw = np.cumsum(w)
    return float(np.interp(cw[-1] * q, cw, v))


def column(sub, label, note, ndots):
    """One chart column: population statistics from all records, dots from a sample."""
    v, w = sub["wage"].to_numpy(), sub["wt"].to_numpy()
    n = min(ndots, len(sub))
    idx = RNG.choice(len(sub), size=n, replace=False, p=w / w.sum())
    s = sub.iloc[np.sort(idx)]
    return {
        "label": label,
        "note": note,
        "n": int(len(sub)),                 # respondents behind the column
        # A column smaller than the dot target shows every respondent rather than a
        # weighted draw, so its cloud reflects the raw sample, not the population.
        "all": bool(n == len(sub)),
        "thin": bool(len(sub) < 100),       # too few respondents to read precisely
        "pop": round(float(w.sum())),       # people they represent
        "avg": round(wmean(v, w)),
        "med": round(wmedian(v, w)),
        "p10": round(wpct(v, w, 0.10)),
        "p25": round(wpct(v, w, 0.25)),
        "p75": round(wpct(v, w, 0.75)),
        "p90": round(wpct(v, w, 0.90)),
        "dots": [
            {"v": int(r.wage), "c": int(r.cred), "a": int(r.age),
             "h": int(r.hrs), "f": r.fam}
            for r in s.itertuples()
        ],
    }


vt, nh = df[df["st"] == 50], df[df["st"] == 33]
out = {
    "src": "IPUMS USA, ACS 1-year 2024",
    "universe": "Wage and salary workers aged 25-64 in civilian occupations, 35+ usual hours and 48+ weeks a year, with positive wage income; the self-employed and military occupations excluded",
    "creds": CRED_NAMES,
    "byArea": [],
    "byCred": [],
}

print("\nby area (one dot = one respondent):")
for label, sub, note in [
    ("Vermont", vt, "ACS 1-year 2024"),
    ("New Hampshire", nh, "ACS 1-year 2024"),
    ("United States", df, "ACS 1-year 2024"),
]:
    col = column(sub, label, note, AREA_DOTS)
    out["byArea"].append(col)
    print(f"  {label:15s} n={col['n']:>7,}  represents {col['pop']:>11,}  "
          f"avg={col['avg']:>7,}  median={col['med']:>7,}  dots={len(col['dots'])}")

print("\nVermont by credential:")
for k, name in enumerate(CRED_NAMES):
    sub = vt[vt["cred"] == k]
    if len(sub) < 30:
        print(f"  {name:26s} n={len(sub)} -- too few respondents, column dropped")
        continue
    col = column(sub, name, "ACS 1-year 2024", CRED_DOTS)
    out["byCred"].append(col)
    print(f"  {name:26s} n={col['n']:>5,}  avg={col['avg']:>7,}  "
          f"median={col['med']:>7,}  dots={len(col['dots'])}")

allv = np.array([d["v"] for grp in ("byArea", "byCred") for col in out[grp] for d in col["dots"]])
out["yMax"] = 200000
out["above"] = int((allv > out["yMax"]).sum())
print(f"\ny-scale 0 to {out['yMax']:,}: {(allv <= out['yMax']).mean()*100:.1f}% of dots on scale, "
      f"{out['above']} above (drawn pinned at the top edge)")

p = HERE.parent / "data" / "people.json"
p.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(f"wrote {p} ({os.path.getsize(p):,} bytes)")
