"""Degree type and per-CIP detail for the VSCS panels.

The 11/18 review asked for degree type on VSCS alignment and a program filter on
By credential level. Both were filed as blocked; neither was. build_sow.py has
always pulled AWLEVEL and CIPCODE -- the award and the programme are already in
the frame -- and then collapsed both when it aggregated to SOC. Nothing new had
to be fetched except the same two cheap reads: the IPEDS completions table (11
MiB scanned) and the CIP-SOC crosswalk (under a MiB).

This runs ONLY those two queries, so it does not re-run build_sow.py's ACS county
pull or anything else, and it writes only new keys into data/sow.json.

THE ALLOCATION IS NOT REDONE. It is build_sow.py's, reproduced line for line --
each programme's completions split across its linked SOCs in proportion to those
occupations' Vermont employment, equal split as the fallback where none of them
exist here. The script asserts that it reproduces the published totals before it
writes anything: 1,983 completions in, 1,700.1 landing in a Vermont occupation,
and every occupation group's `linked` matching byFamily to within 0.05. If the
allocation ever drifts from build_sow.py's, this fails loudly rather than
publishing a second, quieter set of numbers.

What it adds to sow.json, all under `vscs`:
  byAwardFamily  occupation group -> award level -> graduates attributed
  awardOrder     award levels, least to most study, for stacking
  byCip          one row per programme: code, title, completions, award mix,
                 the occupation groups it feeds, and the entry tiers of those
"""
import io
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from google.cloud import bigquery

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
VSCS = [230861, 231165]
INST = {230861: "Community College of Vermont", 231165: "Vermont State University"}
AWLEVEL = {
    1: "Certificate, <1 year", 2: "Certificate, 1-2 years", 3: "Associate degree",
    4: "Certificate, 2-4 years", 5: "Bachelor's degree", 6: "Postbaccalaureate certificate",
    7: "Master's degree", 8: "Post-master's certificate", 17: "Doctorate, research",
    18: "Doctorate, professional practice", 19: "Doctorate, other",
    20: "Certificate, <12 weeks", 21: "Certificate, 12 weeks-1 year",
}
# Least to most study. The chart stacks in this order so a bar reads left to
# right as the ladder, not as whatever order a groupby happened to produce.
AWARD_ORDER = [
    "Certificate, <12 weeks", "Certificate, 12 weeks-1 year", "Certificate, <1 year",
    "Certificate, 1-2 years", "Certificate, 2-4 years", "Associate degree",
    "Bachelor's degree", "Postbaccalaureate certificate", "Master's degree",
    "Post-master's certificate", "Doctorate, research",
    "Doctorate, professional practice", "Doctorate, other",
]


def D(n):
    return json.load(io.open(os.path.join(DATA, n), encoding="utf-8"))


LC = D("lightcast.json")
SOW_PATH = os.path.join(DATA, "sow.json")
SOW = json.load(io.open(SOW_PATH, encoding="utf-8"))
V = SOW["vscs"]

jobs_by_soc = {o["s"]: (o.get("j") or 0.0) for o in LC["allOcc"]}
fam_by_soc = {o["s"]: o.get("f") for o in LC["allOcc"]}
tier_by_soc = {o["s"]: o.get("t") for o in LC["allOcc"]}

c = bigquery.Client(project="strada-data-lab-c9d1")

print("query 1/2: IPEDS completions by CIP and award ...")
comp = c.query(f"""
SELECT UNITID, CIPCODE, AWLEVEL, SUM(CTOTALT) AS completions
FROM `strada-data-lab-c9d1.ipeds.2024_Completions_AwardsByCIP_C2024_A`
WHERE UNITID IN ({','.join(map(str, VSCS))}) AND MAJORNUM = 1 AND CIPCODE != 99
GROUP BY 1,2,3
""").to_dataframe()

print("query 2/2: CIP-SOC crosswalk ...")
xw = c.query("""
SELECT CIP2020Code AS cip, CIP2020Title AS cipname, SOC2018Code AS soc
FROM `strada-data-lab-c9d1.cip_soc_crosswalk.cip2020_soc2018_crosswalk`
""").to_dataframe()

comp["cip"] = comp["CIPCODE"].astype(float)
comp["completions"] = comp["completions"].astype(float)
comp["inst"] = comp["UNITID"].map(INST)
comp["award"] = comp["AWLEVEL"].map(AWLEVEL).fillna(
    comp["AWLEVEL"].astype(str).radd("AWLEVEL "))
tot_comp = comp["completions"].sum()
print("\ncompletions: %.0f across %d CIP-award rows" % (tot_comp, len(comp)))

# ---- build_sow.py's allocation, reproduced ------------------------------
nsoc = xw.groupby("cip")["soc"].nunique().rename("nsoc")
link = comp.merge(xw, on="cip", how="inner").merge(nsoc, on="cip", how="left")
link["soc_jobs"] = link["soc"].map(jobs_by_soc).fillna(0.0)
link["cip_jobs"] = link.groupby(["cip", "AWLEVEL", "UNITID"])["soc_jobs"].transform("sum")
link["frac_eq"] = link["completions"] / link["nsoc"]
link["frac"] = np.where(
    link["cip_jobs"] > 0,
    link["completions"] * link["soc_jobs"] / link["cip_jobs"].replace(0, np.nan),
    link["frac_eq"],
)
link["frac"] = link["frac"].fillna(link["frac_eq"])
link["f"] = link["soc"].map(fam_by_soc)
link["t"] = link["soc"].map(tier_by_soc)

# ---- reconcile against what is already published ------------------------
landed = link[link["f"].notna()]["frac"].sum()
print("landing in a Vermont occupation: %.1f (published %.1f)"
      % (landed, sum(r["linked"] for r in V["byFamily"])))

if abs(tot_comp - V["totalCompletions"]) > 0.5:
    raise SystemExit("completions %.0f != published %s" % (tot_comp, V["totalCompletions"]))

fam_now = link.groupby("f")["frac"].sum()
worst = 0.0
for r in V["byFamily"]:
    mine = float(fam_now.get(r["f"], 0.0))
    worst = max(worst, abs(mine - r["linked"]))
if worst > 0.05:
    raise SystemExit("allocation drifted from build_sow.py: worst group off by %.3f" % worst)
print("reconciled: every occupation group within %.3f of byFamily\n" % worst)

# ---- degree type, by occupation group -----------------------------------
by_af = link.groupby(["f", "award"])["frac"].sum()
byAwardFamily = {}
for (f, aw), v in by_af.items():
    if v < 0.05:
        continue
    byAwardFamily.setdefault(f, {})[aw] = round(float(v), 1)

print("degree type by occupation group (top 6 groups):")
tot_by_f = link.groupby("f")["frac"].sum().sort_values(ascending=False)
for f in tot_by_f.index[:6]:
    mix = byAwardFamily.get(f, {})
    parts = ", ".join("%s %.1f" % (a, mix[a]) for a in AWARD_ORDER if a in mix)
    print("  %-38s %6.1f  =  %s" % (f[:38], tot_by_f[f], parts))

# ---- one row per programme ----------------------------------------------
# A CIP is a programme; it can be awarded at several levels by both institutions,
# so completions are summed across those and the award mix carried beside them.
cipname = xw.drop_duplicates("cip").set_index("cip")["cipname"].to_dict()
rows = []
for cip, g in comp.groupby("cip"):
    lk = link[link["cip"] == cip]
    fams = (lk.groupby("f")["frac"].sum().sort_values(ascending=False)
            if len(lk) else pd.Series(dtype=float))
    tiers = sorted({tier_by_soc.get(s) for s in lk["soc"].unique()
                    if tier_by_soc.get(s)})
    rows.append({
        "cip": ("%.4f" % cip).rstrip("0").rstrip("."),
        "n": cipname.get(cip, "CIP %s" % cip),
        "c": round(float(g["completions"].sum()), 1),
        "awards": {a: round(float(v), 1)
                   for a, v in g.groupby("award")["completions"].sum().items()},
        "inst": sorted(g["inst"].dropna().unique().tolist()),
        "linked": round(float(lk["frac"].sum()), 1) if len(lk) else 0.0,
        "nsoc": int(lk["soc"].nunique()) if len(lk) else 0,
        "fams": [{"f": f, "linked": round(float(v), 1)} for f, v in fams.items() if v >= 0.05],
        "tiers": tiers,
        # Graduates attributed per entry credential tier. This is the overlap the
        # Pathways filter draws: a programme's output spread across the rungs of
        # the ladder its linked occupations are entered at. A programme whose
        # occupations sit on three different rungs is a real finding about the
        # programme, not noise.
        "tierMix": ({t: round(float(v), 1)
                     for t, v in lk.groupby("t")["frac"].sum().items() if v >= 0.05}
                    if len(lk) else {}),
    })
rows.sort(key=lambda r: -r["c"])
print("\nprogrammes: %d, largest five:" % len(rows))
for r in rows[:5]:
    print("  %-52s %6.1f completions, %d linked SOCs, tiers %s"
          % (r["n"][:52], r["c"], r["nsoc"], ", ".join(r["tiers"]) or "none"))

unlinked = [r for r in rows if r["nsoc"] == 0]
print("\nprogrammes the crosswalk does not link at all: %d (%.1f completions)"
      % (len(unlinked), sum(r["c"] for r in unlinked)))

V["byAwardFamily"] = byAwardFamily
V["awardOrder"] = [a for a in AWARD_ORDER
                   if any(a in m for m in byAwardFamily.values())]
V["byCip"] = rows
V["detailNote"] = ("Degree type and programme detail share build_sow.py's "
                   "employment-weighted allocation; byAwardFamily sums to byFamily.")

json.dump(SOW, io.open(SOW_PATH, "w", encoding="utf-8"), separators=(",", ":"))
print("\nwrote %s (%s bytes)" % (SOW_PATH, "{:,}".format(os.path.getsize(SOW_PATH))))
