"""Builds the data behind the Wage quality mockups. Throwaway, but the figures
in it are the real ones, so the two options can be judged on what they would
actually show.

THE MEASURE THE TAB SHOULD BE ON
--------------------------------
Today "share above the living wage" compares each occupation's MEDIAN with the
benchmark and then counts all of that occupation's jobs on one side of it. An
occupation whose median lands a dollar over contributes 100% of its jobs to
"above"; a dollar under and it contributes none. Half the people in each are on
the wrong side of that line.

Statewide the errors mostly cancel -- 42.5% against 41.1% -- which is why it has
survived. By family they do not: Installation & Repair reads 3.3% below on the
median rule and 22.6% on the distribution, Office & Admin Support 63.7% against
49.2%. Those are the numbers on the chart, and they are wrong in both
directions.

Every figure here is read off each occupation's own p10-p90 ladder, weighted by
its jobs, and rolled up from there.

POOLED FAMILY LADDERS
---------------------
percentiles.json carries a ladder per family already, but it is the
employment-weighted MEAN of its occupations' percentiles -- the average p10, not
the 10th percentile of the family's jobs. That is a much narrower thing: it
averages away the spread between occupations, which in a family like Healthcare
Practitioners is most of the spread there is. The ladders here are built by
pooling the occupations' own distributions and reading the percentiles off the
pool.
"""
import json, os, sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(HERE, "..", "data", n), encoding="utf-8"))
OUT = os.path.join(HERE, "_mock_wage.json")

lc, pct, sow, cty = D("lightcast.json"), D("percentiles.json"), D("sow.json"), D("counties.json")
HOURS = lc["hours"]
LW_KEY = lc["defaultLW"]
LWA = lc["livingWage"][LW_KEY] * HOURS

PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
QS = list(range(5, 100, 2))  # the grid a pooled ladder is sampled on


def ladder(box):
    """[(value, quantile)] for a published ladder, lowest first."""
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, floor):
    """Percent of a distribution under `floor`. Clamped outside p10 and p90,
    where the ladder says nothing and extrapolating would invent a figure."""
    if not xs:
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


def value_at(xs, q):
    """The pay at quantile `q`, interpolated along the ladder."""
    if q <= xs[0][1]:
        return xs[0][0]
    if q >= xs[-1][1]:
        return xs[-1][0]
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if q0 <= q <= q1:
            t = 0 if q1 == q0 else (q - q0) / (q1 - q0)
            return v0 + t * (v1 - v0)
    return xs[-1][0]


def pooled(members):
    """A true ladder for a group: pool the members' distributions by employment.

    members: [(ladder, jobs)]
    """
    pts = []
    for xs, w in members:
        if not xs or w <= 0:
            continue
        for q in QS:
            pts.append((value_at(xs, q), w))
    if not pts:
        return None
    pts.sort()
    total = sum(w for _, w in pts)
    out, seen, run = {}, 0, 0.0
    want = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
    i = 0
    for v, w in pts:
        run += w
        while i < len(want) and run / total * 100 >= want[i][0]:
            out[want[i][1]] = round(v)
            i += 1
    while i < len(want):
        out[want[i][1]] = round(pts[-1][0])
        i += 1
    return out


occ = [o for o in lc["allOcc"] if o.get("m") and pct["occ"].get(o["s"])]
for o in occ:
    o["_x"] = ladder(pct["occ"][o["s"]])
occ = [o for o in occ if o["_x"]]

# ---- families ------------------------------------------------------------
fams = []
for f in lc["families"]:
    ms = [o for o in occ if o["f"] == f["f"]]
    if not ms:
        continue
    jobs = sum(o["j"] for o in ms)
    below = sum(o["j"] * share_below(o["_x"], LWA) / 100 for o in ms)
    box = pooled([(o["_x"], o["j"]) for o in ms])
    # The occupations inside it that fall furthest short, for the hover and the
    # drill-down a real build would open.
    worst = sorted(ms, key=lambda o: -share_below(o["_x"], LWA) * o["j"])[:3]
    fams.append({
        "f": f["f"],
        "jobs": int(round(jobs)),
        "below": round(below / jobs * 100, 1),
        "belowN": int(round(below)),
        "oldBelow": round(100 - f["above"][LW_KEY], 1),
        "med": f["med"],
        "nocc": len(ms),
        "box": box,
        "worst": [{"n": o["n"], "j": int(o["j"]),
                   "b": round(share_below(o["_x"], LWA), 1)} for o in worst],
    })
fams.sort(key=lambda r: -r["below"])

# ---- entry credential ----------------------------------------------------
creds = []
for t in ["No formal credential", "High school", "Sub-baccalaureate",
          "Bachelor's", "Graduate / professional"]:
    ms = [o for o in occ if o.get("t") == t]
    if not ms:
        continue
    jobs = sum(o["j"] for o in ms)
    below = sum(o["j"] * share_below(o["_x"], LWA) / 100 for o in ms)
    creds.append({"f": t, "jobs": int(round(jobs)), "below": round(below / jobs * 100, 1),
                  "belowN": int(round(below)), "nocc": len(ms),
                  "box": pooled([(o["_x"], o["j"]) for o in ms])})

# ---- counties, each against its own cost floor ---------------------------
CSV = r"G:\My Drive\Vermont Labor Market Analysis\VT_CoreLMI_Occupation_by_County_2021_2025.csv"
d = pd.read_csv(CSV, dtype={"areaid": str, "occid": str, "classid": int})
d["year"] = d["year"].astype(float).astype(int)
d["occ_level"] = d["occ_level"].astype(float).astype(int)
d = d[(d.year == 2025) & (d.occ_level == 5) & d.classid.isin([1, 2]) & (d.emp > 0)]
for _, k in PTS:
    d["a_" + k] = d["earn_" + k] * HOURS

fips = {r["c"]: r["fips"] for r in sow["regions"]}
lwa = {r["c"]: r["lwA"] for r in sow["regions"]}
counties = []
for c in cty["counties"]:
    aid = fips.get(c["c"])
    sub = d[d.areaid == aid] if aid else None
    if sub is None or sub.empty:
        continue
    local = state = den = 0.0
    mem = []
    for r in sub.itertuples():
        box = {k: getattr(r, "a_" + k) for _, k in PTS}
        box = {k: v for k, v in box.items() if pd.notna(v) and v > 0}
        xs = ladder(box)
        sl, ss = share_below(xs, lwa[c["c"]]), share_below(xs, LWA)
        if sl is None or ss is None:
            continue
        local += r.emp * sl / 100
        state += r.emp * ss / 100
        den += r.emp
        mem.append((xs, r.emp))
    counties.append({
        "c": c["c"], "jobs": c["emp"], "med": c["med"], "thin": c["thin"],
        "lwA": round(lwa[c["c"]]),
        "local": round(local / den * 100, 1),
        "state": round(state / den * 100, 1),
        "localN": int(round(local)),
        "box": pooled(mem),
    })
counties.sort(key=lambda r: -r["local"])

tot = sum(o["j"] for o in occ)
below_tot = sum(o["j"] * share_below(o["_x"], LWA) / 100 for o in occ)
out = {
    "lwKey": LW_KEY, "lwA": round(LWA), "hours": HOURS,
    "households": {k: round(v * HOURS) for k, v in lc["livingWage"].items()},
    "totalJobs": int(round(tot)),
    "belowJobs": int(round(below_tot)),
    "belowShare": round(below_tot / tot * 100, 1),
    "oldShare": round(sum(o["j"] for o in occ if o["m"] < LWA) / tot * 100, 1),
    "statewideBox": pooled([(o["_x"], o["j"]) for o in occ]),
    "families": fams,
    "creds": creds,
    "counties": counties,
}
json.dump(out, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))
print("wrote %s (%s bytes)" % (OUT, f"{os.path.getsize(OUT):,}"))
print("\nstatewide: %s of %s jobs below $%s (%.1f%%); old rule said %.1f%%"
      % (f"{out['belowJobs']:,}", f"{out['totalJobs']:,}", f"{out['lwA']:,}",
         out["belowShare"], out["oldShare"]))
print("statewide pooled ladder:", out["statewideBox"])
print("\n%-34s %9s %8s %8s %9s  %s" % ("FAMILY", "JOBS", "BELOW", "WAS", "PEOPLE", "POOLED p10-p90"))
for r in fams:
    print("%-34s %9s %7.1f%% %7.1f%% %9s  $%s-$%s"
          % (r["f"][:34], f"{r['jobs']:,}", r["below"], r["oldBelow"], f"{r['belowN']:,}",
             f"{r['box']['p10']:,}", f"{r['box']['p90']:,}"))
print("\n%-12s %9s %9s %9s %9s" % ("COUNTY", "JOBS", "LOCAL LW", "BELOW LOC", "BELOW ST"))
for r in counties:
    print("%-12s %9s %9s %8.1f%% %8.1f%%"
          % (r["c"], f"{r['jobs']:,}", f"${r['lwA']:,}", r["local"], r["state"]))
