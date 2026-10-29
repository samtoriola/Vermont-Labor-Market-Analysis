"""Adds the detailed industries and the age mix to data/lightcast.json.

Additive on purpose. build.py rebuilds the whole file from the exports; this reads
the file build.py produced and writes two new keys into it, so every number already
on the page stays byte-identical and a reviewer only has to check what is new.

Adds:
  industries   947 detailed NAICS with their sector, jobs and average pay -- the
               rows behind a sector bar, which the sector chart could previously
               only count.
  age          on every family and every sector row: three ordered bands rolled up
               from the eight the exports carry.

The exports give age as eight bands from 14-18 to 65+. Three is what a reader can
hold at once and the cut points are the ones that matter here: who is early in a
career, who is mid, and who is close enough to leaving that the work has to be
replaced. 55+ is the share VSCS should read as replacement demand.

The sector and family maps are imported from build.py rather than retyped, so a
rollup cannot drift between the two scripts.
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
OCC = os.path.join(
    FOLDER, "Occupation_Table_All_Occupations_in_Vermont_947ddfb5a42985dc.csv"
)
IND = os.path.join(FOLDER, "Industry_Table_All_Industries_in_Vermont_2f9f3aeb90250b18.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lightcast.json")

# Kept in step with build.py by importing them, not by copying them.
from build_maps import NAICS_SECTOR, SOC_MAJOR  # noqa: E402

BANDS = {
    "u35": ["14-18", "19-21", "22-24", "25-34"],
    "m": ["35-44", "45-54"],
    "o55": ["55-64", "65+"],
}
AGE_COL = "Current Year Age %s"


def age_of(row):
    """The three bands, as counts, plus what share of the row they cover."""
    out = {}
    for k, cols in BANDS.items():
        out[k] = float(sum(row[AGE_COL % c] for c in cols))
    return out


def sector_of(naics):
    p2 = int(str(naics)[:2])
    for lo, hi, nm in NAICS_SECTOR:
        if lo <= p2 <= hi:
            return nm
    return "Other / unclassified"


def main():
    lc = json.load(open(OUT, encoding="utf-8"))

    # ---- occupations -> families -------------------------------------------
    occ = pd.read_csv(OCC, encoding="utf-8-sig", low_memory=False)
    occ["family"] = occ["SOC"].astype(str).str[:2].map(SOC_MAJOR).fillna("Other")
    occ = occ[~occ["family"].isin(("Military", "Other"))]

    fam_age = {}
    for fam, d in occ.groupby("family"):
        tot = {k: 0.0 for k in BANDS}
        for _, r in d.iterrows():
            a = age_of(r)
            for k in tot:
                tot[k] += a[k]
        fam_age[fam] = tot

    covered = 0
    for row in lc["families"]:
        a = fam_age.get(row["f"])
        if not a:
            continue
        s = sum(a.values())
        if s <= 0:
            continue
        row["age"] = {k: round(v) for k, v in a.items()}
        covered += 1

    # ---- industries -> sectors, and the detail rows themselves --------------
    ind = pd.read_csv(IND, encoding="utf-8-sig", low_memory=False)
    ind["sector"] = ind["NAICS"].map(sector_of)

    detail = []
    for _, r in ind.iterrows():
        j = float(r["2025 Jobs"])
        if j <= 0:
            continue
        earn = float(r["Avg. Earnings Per Job"])
        detail.append(
            {
                "naics": str(r["NAICS"]),
                "n": str(r["Description"]),
                "sec": r["sector"],
                "j": round(j),
                "earn": round(earn) if earn > 0 else None,
            }
        )
    detail.sort(key=lambda d: -d["j"])
    lc["industries"] = detail

    sec_age = {}
    for s, d in ind.groupby("sector"):
        tot = {k: 0.0 for k in BANDS}
        for _, r in d.iterrows():
            a = age_of(r)
            for k in tot:
                tot[k] += a[k]
        sec_age[s] = tot

    for row in lc["sectors"]:
        a = sec_age.get(row["s"])
        if not a or sum(a.values()) <= 0:
            continue
        row["age"] = {k: round(v) for k, v in a.items()}

    json.dump(lc, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))

    fa = sum(sum(r["age"].values()) for r in lc["families"] if "age" in r)
    sa = sum(sum(r["age"].values()) for r in lc["sectors"] if "age" in r)
    print("families with an age mix: %d of %d" % (covered, len(lc["families"])))
    print("  age total %s against %s jobs" % (f"{fa:,.0f}", f"{lc['totalJobs']:,}"))
    print("sectors with an age mix:  %d of %d"
          % (sum(1 for r in lc["sectors"] if "age" in r), len(lc["sectors"])))
    print("  age total %s" % f"{sa:,.0f}")
    print("detailed industries:      %d" % len(detail))
    print("  bytes: %s" % f"{os.path.getsize(OUT):,}")


if __name__ == "__main__":
    main()
