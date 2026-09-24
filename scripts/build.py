"""Integrate Lightcast Vermont exports + MIT living wage into the dashboard dataset.

PRIMARY SOURCE (window-consistent, 2021-2025):
  Occupation_Table_..._37191a85abaf7e4a_Updated.csv - 798 detailed SOC
    2021/2025 Jobs, 2021-2025 Change, 2021-2025 Openings (Lightcast's own measure),
    2025 Separations, Median + Pct 10/25/75/90 ANNUAL Earnings, entry education,
    projections to 2030.

CARRIED FORWARD (same 2025 snapshot, verified identical job totals and percentiles):
  Occupation_Table_..._947ddfb5a42985dc.csv - only for 2025 Employment Concentration (LQ),
    which the updated export omits.

  Job_Postings_Table_Vermont_...csv  - unique postings Jan 2021 - Jan 2026 by SOC
  Industry_Table_..._2f9f3aeb90250b18.csv - 947 NAICS; carries ONLY 2001 and 2025 job
    columns, so NO 2021 baseline exists at sector level. Sector change is therefore
    omitted rather than shown out-of-window.
  sandbox.mit_living_wage_2025 - Vermont state + 14 counties

ANNUALISATION: "2021 - 2025 Openings" is a cumulative total across the 2021->2025 span.
  Divided by 4 to match how "2021 - 2025 Change" is computed (endpoint difference over
  4 intervals). Surfaced in the UI so the divisor is auditable.
"""
import pandas as pd, numpy as np, json, os

FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
UPD = os.path.join(FOLDER, "Occupation_Table_All_Occupations_in_Vermont_37191a85abaf7e4a_Updated.csv")
PREV = os.path.join(FOLDER, "Occupation_Table_All_Occupations_in_Vermont_947ddfb5a42985dc.csv")
POST = os.path.join(FOLDER, "Job_Postings_Table_Vermont_46d10895226907a6.csv")
IND = os.path.join(FOLDER, "Industry_Table_All_Industries_in_Vermont_2f9f3aeb90250b18.csv")

OPEN_YEARS = 4
HOURS = 2080.0

upd = pd.read_csv(UPD, encoding="utf-8-sig", low_memory=False)
prev = pd.read_csv(PREV, encoding="utf-8-sig", low_memory=False)
post = pd.read_csv(POST, encoding="utf-8-sig")
ind = pd.read_csv(IND, encoding="utf-8-sig", low_memory=False)

SOC_MAJOR = {
 "11":"Management","13":"Business & Financial Operations","15":"Computer & Mathematical",
 "17":"Architecture & Engineering","19":"Life, Physical & Social Science",
 "21":"Community & Social Service","23":"Legal","25":"Educational Instruction & Library",
 "27":"Arts, Design, Entertainment & Media","29":"Healthcare Practitioners & Technical",
 "31":"Healthcare Support","33":"Protective Service","35":"Food Preparation & Serving",
 "37":"Building & Grounds Cleaning","39":"Personal Care & Service","41":"Sales",
 "43":"Office & Administrative Support","45":"Farming, Fishing & Forestry",
 "47":"Construction & Extraction","49":"Installation, Maintenance & Repair",
 "51":"Production","53":"Transportation & Material Moving","55":"Military",
}
EDU_TIER = {
 "No formal educational credential":"No formal credential",
 "High school diploma or equivalent":"High school",
 "Some college, no degree":"Sub-baccalaureate",
 "Postsecondary nondegree award":"Sub-baccalaureate",
 "Associate's degree":"Sub-baccalaureate",
 "Bachelor's degree":"Bachelor's",
 "Master's degree":"Graduate / professional",
 "Doctoral or professional degree":"Graduate / professional",
}
EDU_DETAIL_ORDER = ["No formal educational credential","High school diploma or equivalent",
 "Some college, no degree","Postsecondary nondegree award","Associate's degree",
 "Bachelor's degree","Master's degree","Doctoral or professional degree"]
TIER_ORDER = ["No formal credential","High school","Sub-baccalaureate","Bachelor's",
              "Graduate / professional"]
NAICS_SECTOR = [
 (11,11,"Agriculture, Forestry, Fishing & Hunting"),(21,21,"Mining, Quarrying, Oil & Gas"),
 (22,22,"Utilities"),(23,23,"Construction"),(31,33,"Manufacturing"),
 (42,42,"Wholesale Trade"),(44,45,"Retail Trade"),(48,49,"Transportation & Warehousing"),
 (51,51,"Information"),(52,52,"Finance & Insurance"),(53,53,"Real Estate & Rental"),
 (54,54,"Professional, Scientific & Technical"),(55,55,"Management of Companies"),
 (56,56,"Administrative, Support & Waste Mgmt"),(61,61,"Educational Services"),
 (62,62,"Health Care & Social Assistance"),(71,71,"Arts, Entertainment & Recreation"),
 (72,72,"Accommodation & Food Services"),(81,81,"Other Services"),
 (92,92,"Public Administration"),(90,90,"Government"),
]

o = pd.DataFrame({
    "soc": upd["SOC"].astype(str),
    "name": upd["Description"].astype(str),
    "jobs21": upd["2021 Jobs"].astype(float),
    "jobs25": upd["2025 Jobs"].astype(float),
    "jobs30": upd["2030 Jobs"].astype(float),
    "chg": upd["2021 - 2025 Change"].astype(float),
    "openTot": upd["2021 - 2025 Openings"].astype(float),
    "sep25": upd["2025 Separations"].astype(float),
    "turnRate": upd["2025 Turnover Rate"].astype(float),
    "med": upd["Median Annual Earnings"].astype(float),
    "p10": upd["Pct. 10 Annual Earnings"].astype(float),
    "p25": upd["Pct. 25 Annual Earnings"].astype(float),
    "p75": upd["Pct. 75 Annual Earnings"].astype(float),
    "p90": upd["Pct. 90 Annual Earnings"].astype(float),
    "edu_raw": upd["Typical Entry Level Education"],
})
o["p50"] = o["med"]
o["family"] = o["soc"].str[:2].map(SOC_MAJOR).fillna("Other")
o["edu_detail"] = o["edu_raw"].fillna("Not assigned")
o["tier"] = o["edu_raw"].map(EDU_TIER).fillna("Not assigned")
o["open"] = o["openTot"] / OPEN_YEARS
o["chgPct"] = np.where(o["jobs21"] > 0, o["chg"] / o["jobs21"], np.nan)
o["g5"] = o["jobs30"] - o["jobs25"]
o["g5pct"] = np.where(o["jobs25"] > 0, o["g5"] / o["jobs25"], np.nan)
# Turnover: Lightcast's own 2025 rate, with separations/jobs as fallback where blank.
# Churn-inclusive -- separations count job-to-job transfers, not just exits -- so this
# reads as a stability signal, not unmet hiring need.
# Suppressed below 10 jobs: a rate on a fractional headcount is meaningless and
# produces absurd values. Gambling Change Persons carries 0.02 jobs against 129
# separations in the source, i.e. 5,281x -- an artefact of Lightcast's own modelling,
# not a Vermont signal. 47 occupations sit under 1 job and hold 7 jobs between them.
TURN_MIN_JOBS = 10
o["turn"] = np.where(o["turnRate"].notna(), o["turnRate"],
                     np.where(o["jobs25"] > 0, o["sep25"] / o["jobs25"], np.nan))
o["turn"] = np.where(o["jobs25"] >= TURN_MIN_JOBS, o["turn"], np.nan)

# carry LQ forward from the previous export (verified same snapshot)
lq = prev[["SOC", "2025 Employment Concentration"]].copy()
lq.columns = ["soc", "lq"]
lq["soc"] = lq["soc"].astype(str)
o = o.merge(lq, on="soc", how="left")

p = post.rename(columns={"SOC": "soc",
    "Unique Postings from Jan 2021 - Jan 2026": "postings",
    "Median Annual Advertised Salary": "adv"})[["soc", "postings", "adv"]]
p["soc"] = p["soc"].astype(str)
o = o.merge(p, on="soc", how="left")
o["postings"] = o["postings"].fillna(0.0)

LW = {
 "1 adult, no children": 23.95, "1 adult, 1 child": 47.29, "1 adult, 2 children": 63.91,
 "2 adults (both working), no children": 17.06, "2 adults (both working), 2 children": 34.47,
 "2 adults (1 working), 2 children": 45.47,
 "Vermont minimum wage": 14.01, "Poverty wage (1 adult)": 7.52,
}
DEFAULT_LW = "1 adult, no children"
TOTJ = o["jobs25"].sum()
PCTS = ["p10", "p25", "p50", "p75", "p90"]

print("2025 jobs: %.0f   2021 jobs: %.0f   net change: %+.0f (%.1f%%)"
      % (TOTJ, o["jobs21"].sum(), o["chg"].sum(), o["chg"].sum() / o["jobs21"].sum() * 100))
print("annual openings: %.0f (%.1f%% of jobs)  [total %.0f / %d yr]"
      % (o["open"].sum(), o["open"].sum() / TOTJ * 100, o["openTot"].sum(), OPEN_YEARS))
print("LQ matched: %d of %d" % (o["lq"].notna().sum(), len(o)))
print("zero-earnings occupations: %d (%.2f%% of jobs)"
      % ((o["med"] <= 0).sum(), o.loc[o["med"] <= 0, "jobs25"].sum() / TOTJ * 100))

def wavg(d, col, wcol="jobs25"):
    m = d[col].notna() & (d[col] > 0) & d[wcol].notna()
    if not m.any() or d.loc[m, wcol].sum() == 0:
        return None
    return float(np.average(d.loc[m, col], weights=d.loc[m, wcol]))

def share_above(d, thresh):
    m = d["med"] > 0
    if not m.any():
        return None
    w = d.loc[m, "jobs25"]
    return float((w * (d.loc[m, "med"] >= thresh)).sum() / w.sum())

def boxof(d):
    dd = d[(~(d[PCTS] <= 0).any(axis=1)) & (d["jobs25"] > 0)]
    if not len(dd):
        return None
    w = dd["jobs25"].values
    b = {k: round(float(np.average(dd[k].values, weights=w))) for k in PCTS}
    b["cov"] = round(float(dd["jobs25"].sum() / d["jobs25"].sum()) * 1000) / 10
    b["nocc"] = int(len(dd))
    return b

def rollup(d):
    return {
        "jobs": round(float(d["jobs25"].sum())),
        "jobs21": round(float(d["jobs21"].sum())),
        "chg": round(float(d["chg"].sum())),
        "chgPct": (round(float(d["chg"].sum() / d["jobs21"].sum()) * 1000) / 10
                   if d["jobs21"].sum() else None),
        "g5": round(float(d["g5"].sum())),
        "g5pct": (round(float(d["g5"].sum() / d["jobs25"].sum()) * 1000) / 10
                  if d["jobs25"].sum() else None),
        "open": round(float(d["open"].sum())),
        "sep": round(float(d["sep25"].sum())),
        "turn": (round(float(d["sep25"].sum() / d["jobs25"].sum()) * 1000) / 10
                 if d["jobs25"].sum() else None),
        "post": round(float(d["postings"].sum())),
        "med": (round(wavg(d, "med")) if wavg(d, "med") else None),
        "lq": (round(wavg(d, "lq"), 2) if wavg(d, "lq") else None),
        "nocc": int(len(d)),
        "box": boxof(d),
    }

out = {"totalJobs": round(float(TOTJ)), "jobs21": round(float(o["jobs21"].sum())),
       "livingWage": LW, "defaultLW": DEFAULT_LW, "hours": HOURS,
       "openYears": OPEN_YEARS, "openTotal": round(float(o["openTot"].sum())),
       "postWindow": "Jan 2021 - Jan 2026", "window": "2021-2025",
       "sepTotal": round(float(o["sep25"].sum())),
       "sepPct": round(float(o["sep25"].sum() / TOTJ) * 1000) / 10,
       "statewideBox": boxof(o)}

fam = []
for f, d in o.groupby("family"):
    if f in ("Military", "Other"):
        continue
    r = rollup(d)
    r["f"] = f
    r["above"] = {k: (round(share_above(d, v * HOURS) * 1000) / 10
                      if share_above(d, v * HOURS) is not None else None)
                  for k, v in LW.items()}
    r["tiers"] = {t: round(float(dd["jobs25"].sum())) for t, dd in d.groupby("tier")}
    fam.append(r)
fam.sort(key=lambda r: -r["jobs"])
out["families"] = fam

tierrows = []
for t in TIER_ORDER:
    d = o[o["tier"] == t]
    if not len(d):
        continue
    r = rollup(d)
    r["t"] = t
    r["share"] = round(r["jobs"] / TOTJ * 1000) / 10
    r["above"] = {k: (round(share_above(d, v * HOURS) * 1000) / 10
                      if share_above(d, v * HOURS) is not None else None)
                  for k, v in LW.items()}
    tierrows.append(r)
out["tiers"] = tierrows

edurows = []
for e in EDU_DETAIL_ORDER:
    d = o[o["edu_detail"] == e]
    if not len(d):
        continue
    r = rollup(d)
    r["e"] = e
    r["tier"] = EDU_TIER.get(e, "Not assigned")
    r["share"] = round(r["jobs"] / TOTJ * 1000) / 10
    edurows.append(r)
out["eduDetail"] = edurows

def occrow(r):
    return {"soc": r["soc"], "n": r["name"], "j": round(r["jobs25"]),
            "j21": round(r["jobs21"]), "chg": round(r["chg"]),
            "chgPct": (round(r["chgPct"] * 1000) / 10 if pd.notna(r["chgPct"]) else None),
            "m": (round(r["med"]) if r["med"] > 0 else None),
            "o": round(r["open"]), "p": int(r["postings"]),
            "g": (round(r["g5pct"] * 1000) / 10 if pd.notna(r["g5pct"]) else None),
            "lq": (round(r["lq"], 2) if pd.notna(r["lq"]) else None),
            "sep": round(r["sep25"], 1),
            "turn": (round(r["turn"] * 1000) / 10 if pd.notna(r["turn"]) else None),
            "e": r["edu_detail"], "t": r["tier"], "fam": r["family"]}
out["topOcc"] = [occrow(r) for _, r in
                 o.sort_values("jobs25", ascending=False).head(40).iterrows()]

o["sizeTier"] = pd.cut(o["jobs25"], [-1, 500, 2000, 1e9],
                       labels=["Smaller (<500)", "Medium (500-2,000)", "Large (2,000+)"])
sz = []
for s in ["Large (2,000+)", "Medium (500-2,000)", "Smaller (<500)"]:
    d = o[o["sizeTier"] == s]
    r = rollup(d)
    r["s"] = s
    r["share"] = round(r["jobs"] / TOTJ * 1000) / 10
    r["above"] = {k: (round(share_above(d, v * HOURS) * 1000) / 10
                      if share_above(d, v * HOURS) is not None else None)
                  for k, v in LW.items()}
    sz.append(r)
out["sizeTiers"] = sz

# j21/chg/chgPct = OBSERVED employment change 2021-2025 (what happened).
# g5/g = PROJECTED change 2025-2030 (what Lightcast forecasts). Both are carried
# because they disagree: Vermont grew faster over the window than the forecast implies.
out["allOcc"] = [
    {"s": r["soc"], "n": r["name"], "j": round(r["jobs25"], 1),
     "j21": round(r["jobs21"], 1),
     "chg": round(r["chg"], 1),
     "chgPct": (round(r["chgPct"] * 1000) / 10 if pd.notna(r["chgPct"]) else None),
     "m": (round(r["med"]) if r["med"] > 0 else None),
     "o": round(r["open"], 1), "p": int(r["postings"]),
     "g5": round(r["g5"], 1),
     "g": (round(r["g5pct"] * 1000) / 10 if pd.notna(r["g5pct"]) else None),
     "sep": round(r["sep25"], 1),
     "turn": (round(r["turn"] * 1000) / 10 if pd.notna(r["turn"]) else None),
     "lq": (round(r["lq"], 2) if pd.notna(r["lq"]) else None),
     "t": r["tier"], "f": r["family"]}
    for _, r in o.iterrows() if r["family"] not in ("Military", "Other")]

# ---- industry: 2025 level only. The export has no 2021 column, so sector-level
# change over the study window is NOT available and is deliberately omitted.
ind2 = pd.DataFrame({"naics": ind["NAICS"].astype(str),
                     "jobs25": ind["2025 Jobs"].astype(float),
                     "earn": ind["Avg. Earnings Per Job"].astype(float)})
ind2["p2"] = ind2["naics"].str[:2].astype(int)
def sec(v):
    for lo, hi, nm in NAICS_SECTOR:
        if lo <= v <= hi:
            return nm
    return "Other / unclassified"
ind2["sector"] = ind2["p2"].map(sec)
secrows = []
tot_ind = float(ind2["jobs25"].sum())
for s, d in ind2.groupby("sector"):
    j = float(d["jobs25"].sum())
    if j <= 0:
        continue
    m = d["earn"] > 0
    secrows.append({"s": s, "j": round(j),
                    "earn": (round(float(np.average(d.loc[m, "earn"],
                              weights=d.loc[m, "jobs25"]))) if m.any() and
                              d.loc[m, "jobs25"].sum() > 0 else None),
                    "share": round(j / tot_ind * 1000) / 10,
                    "nnaics": int(len(d))})
secrows.sort(key=lambda r: -r["j"])
out["sectors"] = secrows
out["sectorNote"] = ("industry export carries only 2001 and 2025 job columns; "
                     "no 2021 baseline, so sector change over the window is unavailable")

lw = pd.read_csv("vt_living_wage.csv")
cty = lw[(lw["region_type"] == "county") & (lw["wage_type"] == "Living Wage")]
out["countyLW"] = {"min": float(cty["a1c0"].min()), "max": float(cty["a1c0"].max()),
                   "n": int(len(cty))}

with open("lc_data.js", "w") as f:
    f.write("const LC = " + json.dumps(out, separators=(",", ":"), default=float) + ";\n")

print("\n--- families (top 8): 2021->2025 actual, annual openings ---")
for r in fam[:8]:
    print(f"  {r['f']:38s} jobs={r['jobs']:>7,} chg={r['chg']:>+6,} ({r['chgPct']:>+5.1f}%) "
          f"open={r['open']:>6,} med=${r['med'] or 0:>7,}")
print("\n--- credential tiers ---")
for r in tierrows:
    b = r["box"]
    print(f"  {r['t']:24s} jobs={r['jobs']:>7,} ({r['share']:4.1f}%) chg={r['chgPct']:>+5.1f}% "
          f"open={r['open']:>6,} p25=${b['p25']:>7,} p50=${b['p50']:>7,} p75=${b['p75']:>7,} "
          f"aboveLW={r['above'][DEFAULT_LW]}%")
print("\n--- size tiers ---")
for r in sz:
    b = r["box"]
    print(f"  {r['s']:22s} jobs={r['jobs']:>7,} open={r['open']:>6,} "
          f"p10=${b['p10']:>7,} p50=${b['p50']:>7,} p90=${b['p90']:>7,} "
          f"aboveLW={r['above'][DEFAULT_LW]}%")
print("\nstatewide box:", out["statewideBox"])
print("sectors:", len(secrows), "| bytes:", os.path.getsize("lc_data.js"))
