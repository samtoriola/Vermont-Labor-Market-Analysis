"""Wage percentile distributions for Vermont.

Source: Occupation_Table_..._37191a85abaf7e4a_Updated.csv
  Pct. 10 / 25 / 75 / 90 ANNUAL Earnings + Median Annual Earnings, all 798 occupations.
  Supplied as annual figures, so no annualisation step is applied.
  (Verified identical to the previous export's hourly percentiles x 2,080.)

Rollups are EMPLOYMENT-WEIGHTED MEANS of the constituent occupations' percentiles,
not a pooled wage distribution. Labelled as such in the UI.
"""
import pandas as pd, numpy as np, json, os

FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
UPD = os.path.join(FOLDER, "Occupation_Table_All_Occupations_in_Vermont_37191a85abaf7e4a_Updated.csv")
SHORT = ["p10", "p25", "p50", "p75", "p90"]

upd = pd.read_csv(UPD, encoding="utf-8-sig", low_memory=False)

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
TIER_ORDER = ["No formal credential","High school","Sub-baccalaureate","Bachelor's",
              "Graduate / professional"]

o = pd.DataFrame({
    "soc": upd["SOC"].astype(str), "name": upd["Description"].astype(str),
    "jobs": upd["2025 Jobs"].astype(float),
    "p10": upd["Pct. 10 Annual Earnings"].astype(float),
    "p25": upd["Pct. 25 Annual Earnings"].astype(float),
    "p50": upd["Median Annual Earnings"].astype(float),
    "p75": upd["Pct. 75 Annual Earnings"].astype(float),
    "p90": upd["Pct. 90 Annual Earnings"].astype(float),
    "edu_raw": upd["Typical Entry Level Education"],
})
o["family"] = o["soc"].str[:2].map(SOC_MAJOR).fillna("Other")
o["tier"] = o["edu_raw"].map(EDU_TIER).fillna("Not assigned")

zero = (o[SHORT] <= 0).any(axis=1)
ok = ~zero
print("occupations with a zero/missing percentile: %d of %d (%.2f%% of jobs)"
      % (zero.sum(), len(o), o.loc[zero, "jobs"].sum() / o["jobs"].sum() * 100))
mono = (o.loc[ok, "p10"] <= o.loc[ok, "p25"]) & (o.loc[ok, "p25"] <= o.loc[ok, "p50"]) \
     & (o.loc[ok, "p50"] <= o.loc[ok, "p75"]) & (o.loc[ok, "p75"] <= o.loc[ok, "p90"])
print("monotonic across all five percentiles: %d of %d priced occupations"
      % (mono.sum(), ok.sum()))
print("jobs covered: %.1f%%" % (o.loc[ok, "jobs"].sum() / o["jobs"].sum() * 100))

def box(dfx):
    dd = dfx[(~(dfx[SHORT] <= 0).any(axis=1)) & (dfx["jobs"] > 0)]
    if not len(dd):
        return None
    w = dd["jobs"].values
    b = {k: round(float(np.average(dd[k].values, weights=w))) for k in SHORT}
    b["cov"] = round(float(dd["jobs"].sum() / dfx["jobs"].sum()) * 1000) / 10
    b["nocc"] = int(len(dd))
    return b

res = {"native": "annual", "source": "Lightcast Vermont updated occupation export",
       "note": "employment-weighted mean of occupation percentiles"}
res["families"] = {}
for f, dfx in o.groupby("family"):
    if f in ("Military", "Other"):
        continue
    b = box(dfx)
    if b:
        res["families"][f] = b
res["tiers"] = {}
for t in TIER_ORDER:
    b = box(o[o["tier"] == t])
    if b:
        res["tiers"][t] = b
o["sizeTier"] = pd.cut(o["jobs"], [-1, 500, 2000, 1e9],
                       labels=["Smaller (<500)", "Medium (500-2,000)", "Large (2,000+)"])
res["sizeTiers"] = {}
for s in ["Large (2,000+)", "Medium (500-2,000)", "Smaller (<500)"]:
    b = box(o[o["sizeTier"] == s])
    if b:
        res["sizeTiers"][s] = b
res["statewide"] = box(o)
res["occ"] = {r["soc"]: {k: round(r[k]) for k in SHORT} for _, r in o[ok].iterrows()}

with open("pct_data.js", "w") as f:
    f.write("const PCT = " + json.dumps(res, separators=(",", ":"), default=float) + ";\n")

print("\n--- credential tiers ---")
for t in TIER_ORDER:
    b = res["tiers"][t]
    print(f"  {t:24s} p10=${b['p10']:>7,} p25=${b['p25']:>7,} p50=${b['p50']:>7,} "
          f"p75=${b['p75']:>7,} p90=${b['p90']:>7,} cov={b['cov']:5.1f}%")
print("\nstatewide:", res["statewide"])
print("occ boxes:", len(res["occ"]), "| bytes:", os.path.getsize("pct_data.js"))
