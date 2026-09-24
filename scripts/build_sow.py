"""Data for SOW research questions 5-8.

Q5  High-demand / high-value opportunity framework (SOW 4B)
Q6  VSCS graduate production vs occupational demand (SOW 4C)
Q7  Regional variation (SOW RQ7) - partial: county wage sufficiency + attainment
Q8  Synthesis inputs (SOW 4D)

Q6 method: IPEDS 2024 completions for VSCS (CCV 230861, Vermont State University 231165),
MAJORNUM=1, CIPCODE!=99, joined to cip2020_soc2018_crosswalk. Because CIP->SOC is
many-to-many, each CIP's completions are split across its linked SOCs IN PROPORTION TO
THOSE OCCUPATIONS' VERMONT EMPLOYMENT (fractional allocation), falling back to an equal
split only where none of a CIP's linked occupations exist in Vermont. This preserves the
total but is an assumption, not a fact -- no graduate is observed entering any job, and
the SOW itself calls program-to-occupation a network of pathways, not a mapping. Both
allocations are computed and the difference is reported, because weighting moves about a
third of the completions relative to an equal split.
"""
import pandas as pd, numpy as np, json, os, warnings
from google.cloud import bigquery
warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")

FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
UPD = os.path.join(FOLDER, "Occupation_Table_All_Occupations_in_Vermont_37191a85abaf7e4a_Updated.csv")
POST = os.path.join(FOLDER, "Job_Postings_Table_Vermont_46d10895226907a6.csv")
OPEN_YEARS = 4
LW_DEFAULT = 23.95 * 2080          # 1 adult, no children
VSCS = [230861, 231165]

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
AWLEVEL = {
 1:"Certificate, <1 year", 2:"Certificate, 1-2 years", 3:"Associate degree",
 4:"Certificate, 2-4 years", 5:"Bachelor's degree", 6:"Postbaccalaureate certificate",
 7:"Master's degree", 8:"Post-master's certificate", 17:"Doctorate, research",
 18:"Doctorate, professional practice", 19:"Doctorate, other",
 20:"Certificate, <12 weeks", 21:"Certificate, 12 weeks-1 year",
}

# ---------------- occupation base ----------------
upd = pd.read_csv(UPD, encoding="utf-8-sig", low_memory=False)
post = pd.read_csv(POST, encoding="utf-8-sig")

o = pd.DataFrame({
    "soc": upd["SOC"].astype(str), "name": upd["Description"].astype(str),
    "jobs": upd["2025 Jobs"].astype(float),
    "jobs21": upd["2021 Jobs"].astype(float),
    "jobs30": upd["2030 Jobs"].astype(float),
    "med": upd["Median Annual Earnings"].astype(float),
    "p25": upd["Pct. 25 Annual Earnings"].astype(float),
    "p75": upd["Pct. 75 Annual Earnings"].astype(float),
    "openTot": upd["2021 - 2025 Openings"].astype(float),
    "edu_raw": upd["Typical Entry Level Education"],
    "exp": upd["Work Experience Required"],
    "ojt": upd["Typical On-The-Job Training"],
})
p = post.rename(columns={"SOC": "soc",
    "Unique Postings from Jan 2021 - Jan 2026": "postings"})[["soc", "postings"]]
p["soc"] = p["soc"].astype(str)
o = o.merge(p, on="soc", how="left")
o["postings"] = o["postings"].fillna(0.0)
o["family"] = o["soc"].str[:2].map(SOC_MAJOR).fillna("Other")
o["tier"] = o["edu_raw"].map(EDU_TIER).fillna("Not assigned")
o["open"] = o["openTot"] / OPEN_YEARS
o["g5pct"] = np.where(o["jobs"] > 0, (o["jobs30"] - o["jobs"]) / o["jobs"] * 100, np.nan)
o["postPer100"] = np.where(o["jobs"] > 0, o["postings"] / o["jobs"] * 100, np.nan)
o["lwRatio"] = np.where(o["med"] > 0, o["med"] / LW_DEFAULT, np.nan)
# Openings INTENSITY, not volume: absolute openings correlate 0.92 with employment,
# which double-counted size in the composite.
o["openPer100"] = np.where(o["jobs"] > 0, o["open"] / o["jobs"] * 100, np.nan)
# Adequacy measured at the 25TH PERCENTILE, not the median. Median / living-wage is a
# monotonic transform of median pay (the benchmark is a constant), so it was rank-identical
# to the pay component and contributed zero information. p25 depends on the occupation's
# SPREAD, which is genuinely independent of its median.
o["p25LwRatio"] = np.where(o["p25"] > 0, o["p25"] / LW_DEFAULT, np.nan)

out = {}

# ---------------- Q5: opportunity index ----------------
# Six equally weighted components, each percentile-ranked within Vermont.
elig = o[(o["med"] > 0) & (o["p25"] > 0) & (o["jobs"] >= 100) &
         (o["family"] != "Military") & (o["family"] != "Other") &
         o["g5pct"].notna()].copy()
# FOUR components at 25% each. Two were removed for measured, not stylistic, reasons:
#
#   adequacy (median / living wage) -- rank-identical to pay, because the benchmark is a
#     constant (r = 1.000; r = 0.966 even when measured at p25). It carried no information
#     while silently giving the wage dimension 33% of the weight.
#
#   openings (per 100 jobs) -- correlated -0.675 with pay, because Vermont's high-turnover
#     occupations are its low-wage ones. It contributed -4.7% of composite variance, i.e. it
#     actively cancelled the other components, and changed only 3 of the top 10. Turnover is
#     not a clean demand signal; postings intensity covers advertised demand better.
#     A growth-only openings series (excluding replacement) would be a valid re-addition.
#
# Living-wage ratios (lw, lw25) and absolute openings (o, op) are still reported per
# occupation for context -- they are simply not scored.
COMPS = [("size", "jobs"), ("growth", "g5pct"),
         ("postings", "postPer100"), ("pay", "med")]
for label, col in COMPS:
    elig["s_" + label] = elig[col].rank(pct=True) * 100
elig["score"] = elig[["s_" + l for l, _ in COMPS]].mean(axis=1)
elig = elig.sort_values("score", ascending=False)

print("Q5 eligible occupations: %d (jobs>=100, priced)  = %.1f%% of jobs"
      % (len(elig), elig["jobs"].sum() / o["jobs"].sum() * 100))

# verify the components now carry independent information
cm = elig[["s_" + l for l, _ in COMPS]].corr()
print("\ncomponent correlation matrix (post-fix):")
print(cm.round(3).to_string())
mx = 0.0
for i, (a, _) in enumerate(COMPS):
    for b, _ in COMPS[i + 1:]:
        r = abs(cm.loc["s_" + a, "s_" + b])
        if r > mx:
            mx, pair = r, (a, b)
print("\nhighest absolute off-diagonal correlation: %.3f  %s" % (mx, pair))

def orow(r):
    d = {"soc": r["soc"], "n": r["name"], "j": round(r["jobs"]),
         "m": round(r["med"]), "o": round(r["open"]), "p": int(r["postings"]),
         "g": round(r["g5pct"], 1), "pp": round(r["postPer100"], 1),
         "op": round(r["openPer100"], 1),
         "p25": round(r["p25"]), "lw25": round(r["p25LwRatio"], 2),
         "lw": round(r["lwRatio"], 2), "t": r["tier"], "f": r["family"],
         "sc": round(r["score"], 1),
         "exp": (r["exp"] if pd.notna(r["exp"]) else None),
         "ojt": (r["ojt"] if pd.notna(r["ojt"]) else None)}
    for label, _ in COMPS:
        d["s_" + label] = round(r["s_" + label])
    return d

out["opp"] = {
    "components": [l for l, _ in COMPS],
    "note": "equal-weight mean of four percentile ranks, 25% each", "wageBasis": "median annual earnings", "nComp": 4, "weightEach": 25, "dropped": "adequacy (r=1.000 with pay); openings intensity (-4.7% variance share)",
    "minJobs": 100, "nEligible": int(len(elig)),
    "top": [orow(r) for _, r in elig.head(30).iterrows()],
    "byTier": {},
}
for t, d in elig.groupby("tier"):
    out["opp"]["byTier"][t] = [orow(r) for _, r in
                               d.sort_values("score", ascending=False).head(10).iterrows()]

# ---------------- Q6: VSCS completions -> SOC ----------------
comp = c.query(f"""
SELECT UNITID, CIPCODE, AWLEVEL, SUM(CTOTALT) AS completions
FROM `strada-data-lab-c9d1.ipeds.2024_Completions_AwardsByCIP_C2024_A`
WHERE UNITID IN ({','.join(map(str, VSCS))}) AND MAJORNUM = 1 AND CIPCODE != 99
GROUP BY 1,2,3
""").to_dataframe()
xw = c.query("""
SELECT CIP2020Code AS cip, CIP2020Title AS cipname, SOC2018Code AS soc
FROM `strada-data-lab-c9d1.cip_soc_crosswalk.cip2020_soc2018_crosswalk`
""").to_dataframe()

comp["cip"] = comp["CIPCODE"].astype(float)
comp["completions"] = comp["completions"].astype(float)
INST = {230861: "Community College of Vermont", 231165: "Vermont State University"}
comp["inst"] = comp["UNITID"].map(INST)
comp["award"] = comp["AWLEVEL"].map(AWLEVEL).fillna(
    comp["AWLEVEL"].astype(str).radd("AWLEVEL "))

tot_comp = comp["completions"].sum()
print("\nQ6 VSCS completions 2024: %.0f across %d CIP-award rows"
      % (tot_comp, len(comp)))
print(comp.groupby("inst")["completions"].sum().to_string())
print("\nby award level:")
print(comp.groupby("award")["completions"].sum().sort_values(ascending=False).to_string())

# ---- allocation of completions across a program's linked occupations ----
#
# EMPLOYMENT-WEIGHTED. Each program's completions are divided across its linked SOCs
# in proportion to those occupations' Vermont employment, so a broad program lands
# mostly where the jobs actually are.
#
# The earlier equal split was indefensible for broad programs: Business Administration
# links to 23 occupations, so 93 graduates became 4.04 apiece across all 23 -- including
# occupations with almost no Vermont employment. Weighting concentrates them in the
# large management and business occupations instead.
#
# Both allocations are computed; the weighted one is reported and the equal one is kept
# so the size of the choice stays visible.
nsoc = xw.groupby("cip")["soc"].nunique().rename("nsoc")
link = comp.merge(xw, on="cip", how="inner").merge(nsoc, on="cip", how="left")

# Vermont employment per SOC. SOCs absent from the Lightcast list get 0, which is the
# point: a graduate cannot take a job that does not exist in Vermont.
jobs_by_soc = o.set_index("soc")["jobs"].to_dict()
link["soc_jobs"] = link["soc"].map(jobs_by_soc).fillna(0.0)
link["cip_jobs"] = link.groupby(["cip", "AWLEVEL", "UNITID"])["soc_jobs"].transform("sum")

link["frac_eq"] = link["completions"] / link["nsoc"]

# Fallback: if none of a CIP's linked occupations exist in Vermont there is no
# employment signal, so use the equal split rather than dropping those completions.
link["frac"] = np.where(
    link["cip_jobs"] > 0,
    link["completions"] * link["soc_jobs"] / link["cip_jobs"].replace(0, np.nan),
    link["frac_eq"],
)
link["frac"] = link["frac"].fillna(link["frac_eq"])

n_fallback = int((link["cip_jobs"] <= 0).groupby(link["cip"]).any().sum())
print()
print("allocation: employment-weighted")
print("  totals preserved: %.1f in == %.1f out (weighted), %.1f (equal)"
      % (tot_comp, link["frac"].sum(), link["frac_eq"].sum()))
print("  CIPs with no VT employment in any linked SOC (fell back to equal): %d" % n_fallback)

eq_by_soc = link.groupby("soc")["frac_eq"].sum()
wt_by_soc = link.groupby("soc")["frac"].sum()
cmp_soc = pd.concat([eq_by_soc, wt_by_soc], axis=1).fillna(0.0)
moved = (cmp_soc["frac"] - cmp_soc["frac_eq"]).abs().sum() / 2
print("  reallocated vs equal split: %.0f of %.0f completions (%.1f%%)"
      % (moved, tot_comp, moved / tot_comp * 100))
print("  SOCs receiving completions: %d weighted vs %d equal"
      % (int((wt_by_soc > 0.01).sum()), int((eq_by_soc > 0.01).sum())))

socsup_eq = link.groupby("soc")["frac_eq"].sum().rename("linked_eq").reset_index()
socsup = link.groupby("soc")["frac"].sum().rename("linked").reset_index()
dem = o[["soc", "name", "jobs", "open", "med", "tier", "family", "lwRatio"]].copy()
al = dem.merge(socsup, on="soc", how="left").merge(socsup_eq, on="soc", how="left")
al["linked"] = al["linked"].fillna(0.0)
al["linked_eq"] = al["linked_eq"].fillna(0.0)
al["ratio"] = np.where(al["open"] > 0, al["linked"] / al["open"], np.nan)

matched_soc = int((al["linked"] > 0).sum())
print("SOCs with linked VSCS completions: %d of %d" % (matched_soc, len(al)))
print("openings covered by linked SOCs: %.1f%%"
      % (al.loc[al["linked"] > 0, "open"].sum() / al["open"].sum() * 100))

# The meaningful denominator: openings in occupations that actually require a
# postsecondary credential. Comparing VSCS output to ALL openings understates alignment,
# because most Vermont openings are in occupations needing no formal credential.
CRED = ["Sub-baccalaureate", "Bachelor's", "Graduate / professional"]
al_t = al.merge(o[["soc", "tier"]].rename(columns={"tier": "tier2"}), on="soc", how="left")
open_cred = float(al_t.loc[al_t["tier2"].isin(CRED), "open"].sum())
open_all = float(al["open"].sum())
print("\nopenings, all occupations:            %,.0f".replace(",", "") % open_all)
print("openings requiring a credential:      %.0f (%.1f%% of all)"
      % (open_cred, open_cred / open_all * 100))
print("VSCS completions as %% of credential-requiring openings: %.1f%%"
      % (tot_comp / open_cred * 100))

out["vscs"] = {
    "openAll": round(open_all),
    "openCred": round(open_cred),
    "credShare": round(tot_comp / open_cred * 1000) / 10,
    "totalCompletions": round(float(tot_comp)),
    "byInst": [{"i": k, "c": round(float(v))} for k, v in
               comp.groupby("inst")["completions"].sum().items()],
    "byAward": [{"a": k, "c": round(float(v))} for k, v in
                comp.groupby("award")["completions"].sum().sort_values(ascending=False).items()],
    "nCip": int(comp["cip"].nunique()),
    "alloc": "employment-weighted",
    "allocMovedPct": round(float(moved / tot_comp) * 1000) / 10,
    "nSocLinked": matched_soc,
    "openingsCovered": round(float(al.loc[al["linked"] > 0, "open"].sum()
                                   / al["open"].sum()) * 1000) / 10,
}
# family-level supply vs demand
famal = al.groupby("family").agg(linked=("linked", "sum"),
                                 linked_eq=("linked_eq", "sum"),
                                 open=("open", "sum"),
                                 jobs=("jobs", "sum")).reset_index()
famal = famal[~famal["family"].isin(["Military", "Other"])]
famal["ratio"] = np.where(famal["open"] > 0, famal["linked"] / famal["open"], np.nan)
out["vscs"]["byFamily"] = [
    {"f": r["family"], "linked": round(r["linked"], 1),
     "linkedEq": round(r["linked_eq"], 1), "open": round(r["open"]),
     "jobs": round(r["jobs"]),
     "ratio": (round(r["ratio"], 3) if pd.notna(r["ratio"]) else None)}
    for _, r in famal.sort_values("open", ascending=False).iterrows()]

# undersupply / oversupply candidates among sizeable occupations
cand = al[(al["open"] >= 50) & (al["med"] > 0)].copy()
cand["ratio"] = cand["linked"] / cand["open"]
out["vscs"]["under"] = [
    {"soc": r["soc"], "n": r["name"], "open": round(r["open"]), "linked": round(r["linked"], 1),
     "ratio": round(r["ratio"], 3), "m": round(r["med"]), "t": r["tier"],
     "lw": round(r["lwRatio"], 2)}
    for _, r in cand[cand["lwRatio"] >= 1].nsmallest(15, "ratio").iterrows()]
out["vscs"]["over"] = [
    {"soc": r["soc"], "n": r["name"], "open": round(r["open"]), "linked": round(r["linked"], 1),
     "ratio": round(r["ratio"], 3), "m": round(r["med"]), "t": r["tier"],
     "lw": round(r["lwRatio"], 2)}
    for _, r in cand.nlargest(15, "ratio").iterrows()]

# ---------------- Q7: regional ----------------
cty = c.query("""
SELECT geo_id, total_pop, pop_25_64, median_income,
       bachelors_degree_or_higher_25_64, some_college_and_associates_degree,
       high_school_including_ged, less_than_high_school_graduate
FROM `strada-data-lab-c9d1.census_bureau_acs.county_2020_5yr`
WHERE LENGTH(geo_id) = 5 AND STARTS_WITH(geo_id, '50')
ORDER BY geo_id
""").to_dataframe()
lw = pd.read_csv("vt_living_wage.csv")
lwc = lw[(lw["region_type"] == "county") & (lw["wage_type"] == "Living Wage")][["region_id", "a1c0"]]
lwc.columns = ["geo_id", "lw_hourly"]
lwc["geo_id"] = lwc["geo_id"].astype(str)
CTY_NAMES = {
 "50001":"Addison","50003":"Bennington","50005":"Caledonia","50007":"Chittenden",
 "50009":"Essex","50011":"Franklin","50013":"Grand Isle","50015":"Lamoille",
 "50017":"Orange","50019":"Orleans","50021":"Rutland","50023":"Washington",
 "50025":"Windham","50027":"Windsor"}
cty["geo_id"] = cty["geo_id"].astype(str)
reg = cty.merge(lwc, on="geo_id", how="left")
reg["county"] = reg["geo_id"].map(CTY_NAMES)
reg = reg[reg["county"].notna()].copy()
reg["baRate"] = reg["bachelors_degree_or_higher_25_64"] / reg["pop_25_64"] * 100
reg["lwAnnual"] = reg["lw_hourly"] * 2080
reg["incomeVsLw"] = reg["median_income"] / reg["lwAnnual"]
print("\nQ7 counties matched: %d" % len(reg))
print(reg[["county", "total_pop", "median_income", "baRate", "lw_hourly"]]
      .sort_values("baRate", ascending=False).to_string(index=False))

out["regions"] = [
    {"c": r["county"], "fips": r["geo_id"], "pop": int(r["total_pop"]),
     "inc": int(r["median_income"]) if pd.notna(r["median_income"]) else None,
     "ba": round(r["baRate"], 1), "lwH": round(r["lw_hourly"], 2),
     "lwA": round(r["lwAnnual"]), "incLw": round(r["incomeVsLw"], 2)}
    for _, r in reg.sort_values("total_pop", ascending=False).iterrows()]
out["regionNote"] = ("county living wage from MIT 2025; attainment and median income from "
                     "ACS 2016-2020 5-year county tables. Occupational demand by county is "
                     "NOT in the Lightcast exports (statewide only) and CPS resolves Vermont "
                     "only to metro/non-metro, so the demand half of RQ7 is unanswered.")

with open("sow_data.js", "w") as f:
    f.write("const SOW = " + json.dumps(out, separators=(",", ":"), default=float) + ";\n")

print("\n--- Q5 top 8 opportunities ---")
for r in out["opp"]["top"][:8]:
    print(f"  {r['n'][:44]:44s} score={r['sc']:5.1f} jobs={r['j']:>6,} "
          f"med=${r['m']:>7,} open={r['o']:>5,} g={r['g']:>5.1f}% {r['t']}")
print("\n--- Q6 family alignment (top 6 by openings) ---")
for r in out["vscs"]["byFamily"][:6]:
    print(f"  {r['f']:38s} openings={r['open']:>6,} linked_completions={r['linked']:>7.1f} "
          f"ratio={r['ratio']}")
print("\nbytes:", os.path.getsize("sow_data.js"))
