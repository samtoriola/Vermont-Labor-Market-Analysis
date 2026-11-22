"""Throwaway: is a distribution-based measure of wage adequacy worth building?

The tab currently answers "does this work pay a living wage" by comparing each
occupation's MEDIAN with the benchmark and then counting all of that
occupation's jobs as clearing or not clearing. An occupation whose median lands
a dollar over the floor contributes 100% of its jobs to "above"; one a dollar
under contributes 0%. Half the people in each are on the wrong side of that.

Both percentiles.json (statewide) and the county slice (by county) carry the
full p10-p90 ladder per occupation, so the share of JOBS below the floor can be
interpolated from each occupation's own distribution instead. This checks
whether that changes the answer enough to be worth the rebuild, and whether it
can be done per county against each county's own cost floor.

Family figures are rolled up from the occupations inside each family, never
from the family's own published ladder: that ladder is the employment-weighted
MEAN of its occupations' percentiles, which is a far narrower thing than the
distribution of jobs and would read much too low.
"""
import json, os, sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(HERE, "..", "data", n), encoding="utf-8"))

lc, pct, sow, cty = D("lightcast.json"), D("percentiles.json"), D("sow.json"), D("counties.json")
HOURS = lc["hours"]
LWA = lc["livingWage"][lc["defaultLW"]] * HOURS

print("countyLW in lightcast.json:", json.dumps(lc["countyLW"]))
print("percentiles.note:", pct.get("note"))

PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]


def share_below(box, floor):
    """Percent of a distribution under `floor`, read off p10..p90.

    Linear between the published points. Outside them the ladder says nothing,
    so the tails are clamped at 5% and 95% rather than extrapolated into numbers
    the data cannot support.
    """
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    if len(xs) < 2:
        return None
    if floor <= xs[0][0]:
        return 0.0
    if floor >= xs[-1][0]:
        return 100.0
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if v0 <= floor <= v1:
            t = 0 if v1 == v0 else (floor - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)
    return None


# ---- statewide: median rule vs distribution rule -------------------------
occ = [o for o in lc["allOcc"] if o.get("m")]
tot = sum(o["j"] for o in occ)
med_rule = sum(o["j"] for o in occ if o["m"] < LWA) / tot * 100

dist_num, dist_den, no_box = 0.0, 0.0, 0
for o in occ:
    b = pct["occ"].get(o["s"])
    s_ = share_below(b, LWA) if b else None
    if s_ is None:
        no_box += 1
        continue
    dist_num += o["j"] * s_ / 100
    dist_den += o["j"]

print("\n--- statewide, benchmark $%s (%s) ---" % (f"{LWA:,.0f}", lc["defaultLW"]))
print("  jobs priced:            %s" % f"{tot:,.0f}")
print("  median rule:            %.1f%% of jobs below  (%s jobs)"
      % (med_rule, f"{med_rule / 100 * tot:,.0f}"))
print("  distribution rule:      %.1f%% of jobs below  (%s jobs)"
      % (dist_num / dist_den * 100, f"{dist_num:,.0f}"))
print("  occupations with no usable ladder: %d of %d" % (no_box, len(occ)))

# ---- by family, both ways -----------------------------------------------
print("\n--- by family ---")
print("%-34s %9s %8s %8s %8s" % ("FAMILY", "JOBS", "MEDIAN", "DISTRIB", "GAP"))
fam = {}
for o in occ:
    b = pct["occ"].get(o["s"])
    s_ = share_below(b, LWA) if b else None
    if s_ is None:
        continue
    a, c = fam.setdefault(o["f"], [0.0, 0.0])
    fam[o["f"]] = [a + o["j"] * s_ / 100, c + o["j"]]
rows = []
for f in lc["families"]:
    if f["f"] not in fam:
        continue
    num, den = fam[f["f"]]
    rows.append((f["f"], f["jobs"], 100 - f["above"][lc["defaultLW"]], num / den * 100))
for f, j, m, dd in sorted(rows, key=lambda r: -r[3]):
    print("%-34s %9s %7.1f%% %7.1f%% %+7.1f" % (f[:34], f"{j:,}", m, dd, dd - m))

# ---- by county, each against its own cost floor --------------------------
CSV = r"G:\My Drive\Vermont Labor Market Analysis\VT_CoreLMI_Occupation_by_County_2021_2025.csv"
print("\n--- by county, against each county's own living wage ---")
d = pd.read_csv(CSV, dtype={"areaid": str, "occid": str, "classid": int})
d["year"] = d["year"].astype(float).astype(int)
d["occ_level"] = d["occ_level"].astype(float).astype(int)
d = d[(d.year == 2025) & (d.occ_level == 5) & d.classid.isin([1, 2]) & (d.emp > 0)]
for _, k in PTS:
    d["a_" + k] = d["earn_" + k] * HOURS
print("  rows: %s   counties: %d" % (f"{len(d):,}", d.areaid.nunique()))

fips = {r["c"]: r["fips"] for r in sow["regions"]}
lwa = {r["c"]: r["lwA"] for r in sow["regions"]}
out = []
for c in cty["counties"]:
    aid = fips.get(c["c"])
    sub = d[d.areaid == aid] if aid else None
    if sub is None or sub.empty:
        continue
    local = state = den = 0.0
    for r in sub.itertuples():
        box = {k: getattr(r, "a_" + k) for _, k in PTS}
        box = {k: v for k, v in box.items() if pd.notna(v) and v > 0}
        sl, ss = share_below(box, lwa[c["c"]]), share_below(box, LWA)
        if sl is None or ss is None:
            continue
        local += r.emp * sl / 100
        state += r.emp * ss / 100
        den += r.emp
    out.append((c["c"], c["emp"], lwa[c["c"]], local / den * 100, state / den * 100))

print("%-12s %9s %9s %10s %10s" % ("COUNTY", "JOBS", "LOCAL LW", "BELOW LOCAL", "BELOW STATE"))
for c, e, lw, bl, bs in sorted(out, key=lambda t: -t[3]):
    print("%-12s %9s %9s %9.1f%% %9.1f%%" % (c, f"{e:,}", f"${lw:,.0f}", bl, bs))
