"""Writes ../workfiles/*.csv -- every figure the dashboard draws, as a spreadsheet.

WHY THESE EXIST
---------------
Every chart carries a "Show the figures" table and a CSV export, which is enough
to check one chart. It is not enough to check the dashboard: several measures are
computed in the browser from two files at once, and the only way to verify one by
hand is to have the inputs and the intermediate columns side by side.

So each workfile carries the inputs, then the steps, then the figure the chart
prints -- not just the answer. The share of an occupation's jobs below the
benchmark, for instance, arrives with that occupation's five published
percentiles beside it, so the interpolation can be redone with a calculator.

These are a build output, like the JSON. Nothing reads them; re-run this script
after any data refresh. Reads only the committed JSON in ../data, so it runs
offline and costs nothing.

    python build_workfiles.py
"""
import csv
import io
import json
import os
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "workfiles")


def D(name):
    with io.open(os.path.join(HERE, "..", "data", name), encoding="utf-8") as f:
        return json.load(f)


LC = D("lightcast.json")
PCT = D("percentiles.json")
SOW = D("sow.json")
CTY = D("counties.json")
WF = D("wagefloor.json")
DEM = D("demand.json")
GLA = D("glance.json")

LW_NAME = LC["defaultLW"]
LWA = LC["livingWage"][LW_NAME] * LC["hours"]
PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
TIER_ORDER = ["No formal credential", "High school", "Sub-baccalaureate",
              "Bachelor's", "Graduate / professional"]
VSCS_TIERS = {"Sub-baccalaureate", "Bachelor's", "Graduate / professional"}
written = []


def write(name, cols, rows, note):
    """One CSV, with a provenance line above the header.

    The note is a comment row rather than a sidecar file: a spreadsheet opened
    from a shared drive six months from now should say what it is without anyone
    having to find the README.
    """
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# " + note])
        w.writerow(cols)
        for r in rows:
            w.writerow(r)
    written.append((name, len(rows), note))
    print("  %-38s %5d rows" % (name, len(rows)))


# ---------------------------------------------------------------- measures ---
def ladder(box):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, v):
    """Where v falls along a p10-p90 ladder, as a percentile. Clamped at the ends."""
    if not xs:
        return None
    if v <= xs[0][0]:
        return 0.0
    if v >= xs[-1][0]:
        return 100.0
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if v0 <= v <= v1:
            t = 0 if v1 == v0 else (v - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)
    return None


def pooled(members):
    """A group's own ladder, built from its members' weighted by employment.

    The pooled curve bends only where some member's does, so evaluating at
    exactly those points makes the interpolation between them exact. Same method
    as pooledLadder() in lib/wage.js.
    """
    ms = [(o["j"], ladder(PCT["occ"].get(o["s"]))) for o in members]
    ms = [(j, x) for j, x in ms if x and j > 0]
    if not ms:
        return None
    tot = sum(j for j, _ in ms)
    vs = sorted({v for _, x in ms for v, _ in x})
    curve = [(v, sum(j * share_below(x, v) for j, x in ms) / tot) for v in vs]
    out = {}
    for q, key in PTS:
        hit = None
        for i in range(len(curve) - 1):
            (v0, s0), (v1, s1) = curve[i], curve[i + 1]
            if s0 <= q <= s1:
                t = 0 if s1 == s0 else (q - s0) / (s1 - s0)
                hit = v0 + t * (v1 - v0)
                break
        out[key] = hit
    return out


def n1(v):
    return "" if v is None else round(float(v), 1)


def n2(v):
    return "" if v is None else round(float(v), 2)


print("workfiles ->", os.path.abspath(OUT))
print()

# ---------------------------------------------------------------- the master ---
# One row per occupation with every field the dashboard uses plus the derived
# share-below, because most other workfiles are a roll-up of this one.
master = []
for o in sorted(LC["allOcc"], key=lambda o: -o["j"]):
    box = PCT["occ"].get(o["s"]) or {}
    xs = ladder(box)
    sb = share_below(xs, LWA) if xs else None
    master.append([
        o["s"], o["n"], o["f"], o["t"], n1(o["j"]), n1(o.get("j21")),
        n1(o.get("chgPct")), n1(o.get("g")), o.get("m") or "", n1(o.get("o")),
        n1(o.get("p")), n1(o.get("turn")),
        box.get("p10", ""), box.get("p25", ""), box.get("p50", ""),
        box.get("p75", ""), box.get("p90", ""),
        "yes" if xs else "no", n1(sb),
        "" if sb is None else n1(o["j"] * sb / 100),
        n2(o["m"] / LWA) if o.get("m") else "",
    ])
write(
    "01_occupations_master.csv",
    ["soc", "occupation", "occupation_group", "entry_credential", "jobs_2025",
     "jobs_2021", "change_pct", "projected_pct_2030", "median_pay", "openings_per_year",
     "job_ads", "turnover_pct", "p10", "p25", "p50", "p75", "p90",
     "has_pay_ladder", "pct_of_jobs_below_benchmark", "jobs_below_benchmark",
     "median_times_living_wage"],
    master,
    "Every Vermont occupation. p10-p90 are BLS OEWS 2025 as published; "
    "pct_of_jobs_below_benchmark interpolates $%d along that ladder and is the "
    "measure every wage chart rolls up. openings_per_year is Lightcast "
    "2021-2025 openings / 4." % LWA,
)

POOL = [o for o in LC["allOcc"] if ladder(PCT["occ"].get(o["s"]))]


def rollup(members, weight):
    tot = below = 0.0
    n = 0
    for o in members:
        sb = share_below(ladder(PCT["occ"].get(o["s"])), LWA)
        if sb is None:
            continue
        w = weight(o) or 0
        tot += w
        below += w * sb / 100
        n += 1
    return tot, below, n


# ---------------------------------------------------------- Overview / Wage ---
by_fam = defaultdict(list)
for o in POOL:
    by_fam[o["f"]].append(o)
rows = []
for f, ms in sorted(by_fam.items(), key=lambda kv: -sum(o["j"] for o in kv[1])):
    tot, below, n = rollup(ms, lambda o: o["j"])
    med_rule = sum(o["j"] for o in ms if o.get("m") and o["m"] < LWA)
    rows.append([f, n, n1(tot), n1(below), n1(below / tot * 100),
                 n1(100 - below / tot * 100), n1(med_rule),
                 n1(med_rule / tot * 100), n1(tot / sum(o["j"] for o in POOL) * 100)])
write(
    "02_overview_and_wage_by_group.csv",
    ["occupation_group", "occupations_priced", "jobs_priced", "jobs_below_benchmark",
     "pct_below_benchmark", "pct_at_or_above", "jobs_below_on_median_rule",
     "pct_below_on_median_rule", "share_of_priced_jobs"],
    rows,
    "The Overview chart and Wage quality / Wage benchmark, by occupation group. "
    "pct_below_benchmark sums 01's jobs_below_benchmark over the group and divides "
    "by jobs_priced. The median-rule columns are the measure this replaced, kept so "
    "the difference can be seen: it counts every job in an occupation on whichever "
    "side that occupation's median falls.",
)

by_tier = defaultdict(list)
for o in POOL:
    by_tier[o["t"]].append(o)
rows = []
for t in TIER_ORDER:
    ms = by_tier.get(t, [])
    if not ms:
        continue
    tot, below, n = rollup(ms, lambda o: o["j"])
    pb = pooled(ms) or {}
    pub = PCT["tiers"].get(t, {})
    rows.append([
        t, n, n1(tot), n1(below), n1(below / tot * 100), n1(100 - below / tot * 100),
        n1(pb.get("p10")), n1(pb.get("p25")), n1(pb.get("p50")), n1(pb.get("p75")),
        n1(pb.get("p90")),
        n2(pb["p90"] / pb["p10"]) if pb.get("p10") else "",
        pub.get("p10", ""), pub.get("p50", ""), pub.get("p90", ""),
        n2(pub["p90"] / pub["p10"]) if pub.get("p10") else "",
    ])
write(
    "03_pathways_credential_ladder.csv",
    ["entry_credential", "occupations_priced", "jobs_priced", "jobs_below_benchmark",
     "pct_below_benchmark", "pct_clearing_benchmark",
     "pooled_p10", "pooled_p25", "pooled_p50", "pooled_p75", "pooled_p90",
     "pooled_p90_over_p10",
     "published_p10", "published_p50", "published_p90", "published_p90_over_p10"],
    rows,
    "Pathways / By credential level. pooled_* is the rung's own ladder, built from "
    "its occupations' ladders weighted by employment -- the value V at which a given "
    "share of the rung's JOBS pay less than V. published_* is percentiles.json's "
    "tier roll-up, the employment-weighted MEAN of those occupations' percentiles, "
    "which understates the spread by up to 44% and is NOT what the chart draws.",
)

rows = []
for t in TIER_ORDER:
    ms = [o for o in LC["allOcc"] if o["t"] == t]
    tot, below, n = rollup(ms, lambda o: o.get("o") or 0)
    hiring = [o for o in ms if (o.get("o") or 0) >= 50]
    paying = [o for o in hiring if o.get("m") and o["m"] >= LWA]
    rows.append([t, len(ms), n1(tot), n1(tot - below), n1((tot - below) / tot * 100),
                 len(hiring), len(paying),
                 n1(sum(o["o"] for o in paying)),
                 n1(sum(o["o"] for o in paying) / sum(o.get("o") or 0 for o in ms) * 100)])
write(
    "04_pathways_openings_by_credential.csv",
    ["entry_credential", "occupations", "openings_per_year_priced",
     "openings_in_work_paying_benchmark", "pct_of_openings_paying",
     "occupations_hiring_50_plus", "of_those_median_above_benchmark",
     "their_openings", "pct_on_the_old_gated_measure"],
    rows,
    "Pathways / Which credentials pay. The first five columns are the chart: each "
    "occupation's openings weighted by the share of it clearing the benchmark, with "
    "no volume screen. The last four are the measure this replaced -- occupations "
    "hiring 50+ a year whose MEDIAN clears -- kept so the gap can be seen.",
)

rows = []
for r in sorted(WF["counties"], key=lambda r: -r["local"]):
    rows.append([r["c"], n1(r.get("jobs")), n1(r["lwA"]), n1(LWA),
                 n1(r["local"]), n1(r.get("localN")), n1(r["state"]),
                 n1(r.get("stateN")), n1(r["local"] - r["state"]),
                 n1(r.get("med")), n1(r.get("cov")),
                 "yes" if r.get("thin") else "no"])
write(
    "05_wage_county_floor.csv",
    ["county", "jobs", "county_living_wage", "statewide_living_wage",
     "pct_below_own_floor", "jobs_below_own_floor", "pct_below_statewide_floor",
     "jobs_below_statewide_floor", "difference_points", "midpoint_pay",
     "pct_of_jobs_priced", "small_market"],
    rows,
    "Wage quality / County living wage. Built by scripts/build_wagefloor.py from the "
    "Core LMI county slice, because a pay ladder per occupation per county exists "
    "nowhere else. Both floors are one adult with no children -- the only household "
    "MIT publishes per county -- so the pair isolates geography.",
)

# ------------------------------------------------------------- Employment ----
write(
    "06_employment_sectors.csv",
    ["sector", "jobs", "share_of_jobs", "avg_pay_per_job", "aged_under_35",
     "aged_35_to_54", "aged_55_plus", "aged_55_plus_pct", "detailed_industries"],
    [[x["s"], n1(x.get("j")), n1(x.get("share")), x.get("earn") or "",
      n1(x.get("age", {}).get("u35")), n1(x.get("age", {}).get("m")),
      n1(x.get("age", {}).get("o55")),
      n1(x["age"]["o55"] / x["j"] * 100) if x.get("age") and x.get("j") else "",
      x.get("nnaics") or ""] for x in
     sorted(LC["sectors"], key=lambda x: -(x.get("j") or 0))],
    "Employment / Industry sectors. Lightcast Vermont industry export, 2025, "
    "757 detailed industries rolled up to sector.",
)

fam = {f["f"]: f for f in LC["families"]}
write(
    "07_employment_occupation_groups.csv",
    ["occupation_group", "jobs", "jobs_2021", "change_pct", "median_pay",
     "occupations", "openings_per_year", "turnover_pct", "job_ads",
     "aged_55_plus", "aged_55_plus_pct", "location_quotient"],
    [[f["f"], n1(f.get("jobs")), n1(f.get("jobs21")), n1(f.get("chgPct")),
      f.get("med") or "", f.get("nocc") or "", n1(f.get("open")), n1(f.get("turn")),
      n1(f.get("post")), n1(f.get("age", {}).get("o55")),
      n1(f["age"]["o55"] / f["jobs"] * 100) if f.get("age") and f.get("jobs") else "",
      n2(f.get("lq"))]
     for f in sorted(LC["families"], key=lambda f: -(f.get("jobs") or 0))],
    "Employment / Occupation. The 22 SOC major groups.",
)

# ------------------------------------------------------------ Opportunities --
O = SOW["opp"]
write(
    "08_opportunity_scores.csv",
    ["soc", "occupation", "occupation_group", "entry_credential", "score",
     "rank_employment", "rank_growth", "rank_advertising", "rank_pay",
     "mean_of_four_ranks", "jobs", "projected_pct_2030", "ads_per_100_jobs",
     "median_pay", "widest_gap_between_ranks"],
    [[r["soc"], r["n"], r["f"], r["t"], n1(r["sc"]),
      r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"],
      n1((r["s_size"] + r["s_growth"] + r["s_postings"] + r["s_pay"]) / 4),
      n1(r["j"]), n1(r.get("g")), n1(r.get("pp")), r.get("m") or "",
      max(r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"])
      - min(r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"])]
     for r in sorted(O["top"], key=lambda r: -r["sc"])],
    "Opportunities / Highest scoring. Each rank is a percentile against the %d "
    "scored occupations on that measure alone; the score is their mean at 25%% "
    "each. mean_of_four_ranks is that arithmetic redone here -- it should equal "
    "score to a rounding place. The chart draws each rank as a quarter of the bar."
    % O["nEligible"],
)

# ------------------------------------------------------------ VSCS alignment --
V = SOW["vscs"]
cred_open = defaultdict(float)
all_open = defaultdict(float)
for o in LC["allOcc"]:
    all_open[o["f"]] += o.get("o") or 0
    if o["t"] in VSCS_TIERS:
        cred_open[o["f"]] += o.get("o") or 0
rows = []
for r in sorted(V["byFamily"], key=lambda r: -(r["linked"] / cred_open[r["f"]]
                                               if cred_open[r["f"]] >= 10 else -1)):
    oc = cred_open[r["f"]]
    rows.append([r["f"], n1(r["linked"]), n1(oc), n1(r["open"]),
                 n1(r["linked"] / oc * 100) if oc else "",
                 n1(r["linked"] / r["open"] * 100) if r["open"] else "",
                 n1(r.get("jobs")), "yes" if oc >= 10 else "no"])
write(
    "09_vscs_alignment_by_group.csv",
    ["occupation_group", "graduates_attributed", "openings_asking_for_a_vscs_credential",
     "all_openings", "pct_of_openings_that_ask", "pct_of_all_openings", "jobs",
     "drawn_on_the_chart"],
    rows,
    "VSCS alignment / Against demand. openings_asking_* counts only occupations "
    "whose entry credential is sub-baccalaureate, bachelor's or graduate -- the "
    "three VSCS awards into -- and is what the chart divides by. pct_of_all_openings "
    "is the measure it replaced. A group with fewer than 10 such openings has no "
    "base to divide by and is named under the chart instead of drawn as a zero. "
    "NOTE: graduates_attributed is modelled, not observed -- see the README.",
)

write(
    "10_vscs_production.csv",
    ["award_level", "completions", "share_of_all_completions"],
    [[a["a"], a["c"], n1(a["c"] / V["totalCompletions"] * 100)] for a in V["byAward"]]
    + [["TOTAL", V["totalCompletions"], 100.0]]
    + [["-- by institution --", "", ""]]
    + [[i["i"], i["c"], n1(i["c"] / V["totalCompletions"] * 100)] for i in V["byInst"]],
    "VSCS alignment / Production by award. IPEDS 2024, CCV and Vermont State "
    "University. Counts credentials awarded in one year, not people -- one person "
    "earning two is counted twice.",
)

# ------------------------------------------------------------------ Regions --
write(
    "11_regions_counties.csv",
    ["county", "jobs", "jobs_2021", "change_pct", "midpoint_pay", "occupations"],
    [[c["c"], n1(c.get("emp")), n1(c.get("emp21")), n1(c.get("chg")),
      c.get("med") or "", c.get("nocc") or ""]
     for c in sorted(CTY["counties"], key=lambda c: -(c.get("emp") or 0))]
    + [["Vermont", n1(CTY["state"].get("emp")), n1(CTY["state"].get("emp21")),
        n1(CTY["state"].get("chg")), CTY["state"].get("med") or "", ""]],
    "Regions / Counties compared. Core LMI county slice, classes 1+2 (QCEW and "
    "non-QCEW employees), which reproduce the statewide total to 0.009%%; summing "
    "all four classes lands 40%% high. Pay is the employment-weighted midpoint job, "
    "annualised at %d hours." % LC["hours"],
)

# ----------------------------------------------------------------- Demand ----
rows = []
for a in DEM["areas"]:
    ed = a.get("edu") or []
    ex = a.get("exp") or []
    rows.append([a["label"], a.get("grp"), n1(a.get("postings")), n1(a.get("perJob")),
                 n1(a.get("eduStated"))]
                + [n1(v) for v in ed]
                + [n1(v / a["eduStated"] * 100) if a.get("eduStated") else "" for v in ed]
                + [n1(a.get("expStated"))]
                + [n1(v) for v in ex]
                + [n1(v / a["expStated"] * 100) if a.get("expStated") else "" for v in ex]
                + ["yes" if a.get("thin") else "no"])
write(
    "12_demand_what_postings_ask.csv",
    ["area", "kind", "postings", "postings_per_job", "postings_stating_education"]
    + ["n_" + e for e in DEM["eduOrder"]]
    + ["pct_" + e for e in DEM["eduOrder"]]
    + ["postings_stating_experience"]
    + ["n_" + e for e in DEM["expOrder"]]
    + ["pct_" + e for e in DEM["expOrder"]]
    + ["small_sample"],
    rows,
    "Demand & growth / General demand. %s. %s Shares are of postings that state a "
    "level, which is why the n_ and pct_ columns have different denominators from "
    "`postings`; an area below %d postings is marked small_sample."
    % (DEM["window"], DEM["note"], DEM["thinFloor"]),
)

# ---------------------------------------------------------- Regions / map ----
reg = {r["c"]: r for r in SOW["regions"]}
cty = {c["c"]: c for c in CTY["counties"]}
rows = []
for c in sorted(SOW["regions"], key=lambda r: -(r.get("pop") or 0)):
    j = cty.get(c["c"], {})
    rows.append([c["c"], c.get("fips"), n1(c.get("pop")), n1(c.get("ba")),
                 n1(c.get("inc")), n1(c.get("lwH")), n1(c.get("lwA")),
                 n2(c.get("incLw")), n1(j.get("emp")), j.get("med") or ""])
write(
    "13_regions_county_map.csv",
    ["county", "fips", "population", "pct_with_a_bachelors_or_more",
     "median_household_income", "county_living_wage_hourly",
     "county_living_wage_annual", "income_times_the_living_wage",
     "jobs_located_in_the_county", "midpoint_pay_of_those_jobs"],
    rows,
    "Regions / County map. Population, attainment and income are the county's "
    "RESIDENTS, from the Census ACS 5-year; jobs and pay are the workplaces "
    "located there, from the Core LMI county slice. The two count different "
    "people and are in one file because the map shades by one and the figures "
    "under it carry both. income_times_the_living_wage sets a median HOUSEHOLD "
    "income against a floor built for one adult, so read it as distance from the "
    "floor rather than as any one worker's position.",
)

# ------------------------------------------------------------ the home page --
# One row per tile, carrying what the tile's hover card says: the four headline
# figures come from four sources and two universes -- jobs and people -- which do
# not add together, and the tiles are the one place they sit side by side.
charted = sum(o.get("j") or 0 for o in LC["allOcc"])
write(
    "14_home_tiles.csv",
    ["tile", "value", "what_it_counts", "source", "vintage", "data_file",
     "workfile_to_check", "how_to_check_it"],
    [
        ["Jobs, 2025", n1(LC["totalJobs"]),
         "Jobs located in Vermont, not people; someone holding two counts twice",
         "Lightcast Vermont occupation export", "2025", "data/lightcast.json",
         "01_occupations_master.csv",
         "Export total. The %s charted occupations sum to %s; the %s difference is "
         "military and unmapped SOCs, which 01 excludes"
         % (len(LC["allOcc"]), n1(charted), n1(LC["totalJobs"] - charted))],
        ["Employed Vermonters", GLA["emp"],
         "People with a job, counted where they live; a survey estimate, not a count",
         "Census CPS microdata (IPUMS)",
         "%s, %d months" % (GLA["year"], GLA["months"]), "data/glance.json",
         "15_labor_force_cps.csv",
         "Weighted monthly average over the %d months of %s available"
         % (GLA["months"], GLA["year"])],
        ["Annual openings", n1(LC["openTotal"] / LC["openYears"]),
         "Openings a year, including replacing people who leave, not only new jobs",
         "Lightcast Vermont occupation export", LC["window"], "data/lightcast.json",
         "00_headline_figures.csv",
         "%s openings over the window / %d" % (n1(LC["openTotal"]), LC["openYears"])],
        ["VSCS completions", V["totalCompletions"],
         "Credentials awarded, not people; one graduate finishing two counts twice",
         "IPEDS", "2024 academic year", "data/sow.json", "10_vscs_production.csv",
         "Sum of completions in 10, across CCV and Vermont State University"],
    ],
    "Home. One row per headline tile, which is what that tile's hover card says: "
    "source, vintage, the file the app reads and the workfile that reproduces it. "
    "The four figures count two different things -- the first and third count "
    "jobs, the second counts people, the fourth counts credentials -- so none of "
    "them adds to another.",
)

# The one CPS figure on screen. Carried in full rather than alone, because an
# employment count with no labour force or unemployment beside it cannot be
# sanity-checked against anything.
write(
    "15_labor_force_cps.csv",
    ["measure", "value", "note"],
    [
        ["Year", GLA["year"], "Months available: %d" % GLA["months"]],
        ["Population 16 and over", n1(GLA["pop16"]), "Civilian, non-institutional"],
        ["Labor force", n1(GLA["lf"]), "Employed plus unemployed"],
        ["Employed", n1(GLA["emp"]), "The home page tile"],
        ["Unemployed", n1(GLA["unemp"]), "Looking for work and available for it"],
        ["Labor force participation rate", GLA["lfpr"], "Labor force / population 16+"],
        ["Unemployment rate", GLA["ur"], "Unemployed / labor force"],
        ["Unemployment rate, 95% interval", GLA["urCi"],
         "Plus or minus, in points; survey estimate, not the official LAUS series"],
        ["Working full time", n1(GLA["ft"]), "Usual hours 35 or more: %.1f%%" % GLA["ftShare"]],
        ["Working part time", n1(GLA["pt"]), "Usual hours under 35: %.1f%%" % GLA["ptShare"]],
        ["Hours vary", n1(GLA["vary"]),
         "%.1f%% report hours that vary and cannot be placed either side" % GLA["varyShare"]],
        ["Sample: labor force records", GLA["nLf"], "Person-months, not people"],
        ["Sample: distinct people", GLA["nPeopleLf"],
         "The survey re-interviews households, so rates use this, not the record count"],
        ["Sample: unemployed records", GLA["nUnemp"],
         "Small, which is why the rate carries an interval"],
    ],
    "Home / Employed Vermonters. The Census household survey (CPS) figures behind "
    "the one CPS number the dashboard draws. Weighted estimates from Vermont "
    "monthly microdata; October 2025 is missing nationally, so the year is an "
    "11-month average. These count PEOPLE where they live, and the job counts "
    "elsewhere in these files count JOBS where they are located: the two differ by "
    "construction and should not be differenced.",
)

# ------------------------------------------------------------- the headlines --
pool_tot, pool_below, _ = rollup(POOL, lambda o: o["j"])
tot_cred_open = sum(cred_open.values())
tot_linked = sum(r["linked"] for r in V["byFamily"])
hs = pooled(by_tier["High school"]) or {}
heads = [
    ["Jobs, 2025", n1(LC["totalJobs"]), "data/lightcast.json totalJobs",
     "Export total; 01 sums to %s, %s less, being military and unmapped SOCs"
     % (n1(charted), n1(LC["totalJobs"] - charted)), "Home / every tab"],
    ["Jobs in the charted occupations", n1(charted), "01, all rows",
     "Sum of jobs_2025 in 01", "Every chart that ranks or compares work"],
    ["Employed Vermonters", GLA["emp"], "data/glance.json emp",
     "15, Employed; a PEOPLE count, not comparable with the job counts above",
     "Home"],
    ["Occupations", len(LC["allOcc"]), "data/lightcast.json allOcc",
     "Row count of 01", "About"],
    ["Jobs with a published pay ladder", n1(pool_tot), "01 where has_pay_ladder = yes",
     "Sum of jobs_2025 over those rows", "Overview, Wage quality"],
    ["Living-wage benchmark, " + LW_NAME, n1(LWA),
     "MIT Living Wage 2025 x %d hours" % LC["hours"],
     "$%.2f/hr x %d" % (LC["livingWage"][LW_NAME], LC["hours"]), "Every wage chart"],
    ["Share of priced jobs below it", n1(pool_below / pool_tot * 100),
     "02, jobs_below_benchmark / jobs_priced", "Sum both columns in 02", "Overview"],
    ["Midpoint high-school job", n1(hs.get("p50")), "03 pooled_p50",
     "Pooled ladder over high-school occupations", "Pathways"],
    ["Annual openings", n1(LC["openTotal"] / LC["openYears"]),
     "Lightcast 2021-2025 openings / %d" % LC["openYears"],
     "%s / %d" % (n1(LC["openTotal"]), LC["openYears"]), "Demand, Pathways"],
    ["Openings asking for a VSCS credential", n1(tot_cred_open),
     "01 where entry_credential is sub-bacc, bachelor's or graduate",
     "Sum openings_per_year over those rows", "VSCS alignment"],
    ["VSCS completions, 2024", V["totalCompletions"], "IPEDS, 10",
     "Sum of completions in 10", "VSCS alignment"],
    ["Completions landing in a Vermont occupation", n1(tot_linked),
     "09 graduates_attributed", "Sum that column in 09", "VSCS alignment"],
    ["Graduates vs openings that ask", n1(tot_linked / tot_cred_open * 100),
     "09", "graduates_attributed / openings_asking_*, both summed", "VSCS alignment"],
    ["Occupations scored on the opportunity index", O["nEligible"],
     "100+ jobs and a published wage", "01 filtered", "Opportunities"],
]
write(
    "00_headline_figures.csv",
    ["figure", "value", "source", "how_to_check_it", "where_it_appears"],
    heads,
    "Every number quoted in a caption, a read-out or a tile, with the workfile and "
    "the arithmetic that reproduces it. Start here.",
)

# ------------------------------------------------------------------ README ---
readme = """# Workfiles

Every figure the dashboard draws, as a spreadsheet, so the numbers can be checked
without reading the code or running it.

**Start with `00_headline_figures.csv`.** It lists each number quoted in a caption,
a read-out or a tile, with the file and the arithmetic that reproduces it.

These are a build output. `scripts/build_workfiles.py` writes them from the same
committed JSON in `data/` that the app imports at build time, so a figure here and
the same figure on screen come from one source and cannot drift. Re-run it after
any data refresh:

```
python scripts/build_workfiles.py
```

Nothing in the app reads these files.

## The files

| File | What it carries | Rows |
| --- | --- | --- |
"""
for name, n, note in sorted(written):
    first = note.split(".")[0]
    readme += "| `%s` | %s | %d rows |\n" % (name, first, n)

readme += """
## How to check a figure by hand

Each file carries the inputs and the intermediate steps, not just the answer, so
a measure can be redone with a calculator.

**"41%% of priced jobs pay below a living wage"** — open
`01_occupations_master.csv`. For one occupation, `pct_of_jobs_below_benchmark` is
where $%d falls along its own `p10`&ndash;`p90` ladder, interpolated straight-line
between the two published percentiles either side of it, and clamped at 0 and 100
outside them. `jobs_below_benchmark` is that share times `jobs_2025`. Sum both
columns and divide: that is the Overview headline, and `02` has the same sum per
occupation group.

**A credential rung's pay range** — `03_pathways_credential_ladder.csv` carries
`pooled_*` and `published_*` side by side. The pooled one is what the chart draws:
the value V at which a given share of the rung's jobs pay less than V, built from
its occupations' ladders weighted by employment. The published one is the mean of
those occupations' percentiles, which is a different statistic and understates the
spread by up to 44%%. If a figure on screen matches the published column rather
than the pooled one, something has regressed.

**VSCS alignment** — `09_vscs_alignment_by_group.csv` carries both denominators.
The chart divides by `openings_asking_for_a_vscs_credential`; `pct_of_all_openings`
is the measure that replaced and is kept for comparison.

## What these cannot settle

Three things are modelled rather than observed, and no amount of checking the
arithmetic will change that:

- **Graduates attributed to an occupation.** CIP-to-SOC is many-to-many, so each
  program's completions are split across the occupations it feeds in proportion to
  their Vermont employment. %.1f%% of completions move under that assumption. It
  is a model of where graduates go, not a record of where they went, and
  %s of %s completions land in a Vermont occupation at all.
- **Projected growth to 2030.** A Lightcast model, not an observation. Change over
  2021&ndash;2025 is what happened; the two are kept in separate columns for that
  reason.
- **The openings divisor.** `openings_per_year` is Lightcast's 2021&ndash;2025
  openings divided by %d. If that window is meant inclusively as five years, every
  openings figure here scales down by a fifth.

Measure definitions, suppression rules and the full caveat list are on the
dashboard's Methods tab.
""" % (LWA, V["allocMovedPct"], "{:,}".format(int(round(tot_linked))),
       "{:,}".format(V["totalCompletions"]), LC["openYears"])

with io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="") as f:
    f.write(readme)
print("\n  %-38s" % "README.md")
print("\n%d workfiles written." % (len(written) + 1))
