"""Pathways facts, recomputed from committed JSON for the prototype.

Two corrections to what the tab draws today, both of which change the picture:

1. "Above living wage" uses LC.tiers[].above, which is the median rule -- every job
   in an occupation counted on whichever side that occupation's midpoint falls. The
   same defect lib/wage.js fixed for Wage quality.

2. "Range of outcomes" uses PCT.tiers, which is the employment-weighted MEAN of its
   occupations' percentiles. A mean of p10s is not the pooled p10: it averages away
   the between-occupation spread, which at a credential tier is most of the spread
   there is. Pooling the member occupations' ladders gives the real one.

Writes _pathfacts.json for the mock builder.
"""
import io, json, os, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))

LC, PCT = D("lightcast.json"), D("percentiles.json")
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
ORDER = ["No formal credential", "High school", "Sub-baccalaureate",
         "Bachelor's", "Graduate / professional"]
SHORT = {"No formal credential": "No formal credential", "High school": "High school",
         "Sub-baccalaureate": "Sub-baccalaureate", "Bachelor's": "Bachelor's",
         "Graduate / professional": "Graduate / professional"}


def ladder(box):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, floor):
    """Where `floor` falls along a p10-p90 ladder, as a percentile. Clamped."""
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


def pct_at(xs, q):
    """Inverse: the dollar value at percentile q on a ladder."""
    if q <= xs[0][1]:
        return xs[0][0]
    if q >= xs[-1][1]:
        return xs[-1][0]
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if q0 <= q <= q1:
            t = 0 if q1 == q0 else (q - q0) / (q1 - q0)
            return v0 + t * (v1 - v0)
    return None


def pooled(members):
    """The true ladder for a set of occupations: the dollar value V such that a given
    share of the group's JOBS sit below V. Walks a fine value grid and reads the
    employment-weighted share below each step, then inverts it.
    """
    lads = [(o["j"], ladder(PCT["occ"].get(o["s"]))) for o in members]
    lads = [(j, x) for j, x in lads if x and j > 0]
    if not lads:
        return None
    tot = sum(j for j, _ in lads)
    lo = min(x[0][0] for _, x in lads)
    hi = max(x[-1][0] for _, x in lads)
    grid, out, N = [], {}, 600
    for i in range(N + 1):
        v = lo + (hi - lo) * i / N
        s = sum(j * share_below(x, v) for j, x in lads) / tot
        grid.append((v, s))
    for q, k in PTS:
        hit = None
        for i in range(len(grid) - 1):
            (v0, s0), (v1, s1) = grid[i], grid[i + 1]
            if s0 <= q <= s1:
                t = 0 if s1 == s0 else (q - s0) / (s1 - s0)
                hit = v0 + t * (v1 - v0)
                break
        out[k] = round(hit) if hit is not None else None
    return out


POOL = [o for o in LC["allOcc"] if ladder(PCT["occ"].get(o["s"]))]
by = defaultdict(list)
for o in POOL:
    by[o["t"]].append(o)

TMAP = {r["t"]: r for r in LC["tiers"]}
rows = []
for k in ORDER:
    ms = by.get(k, [])
    jobs = sum(o["j"] for o in ms)
    belowN = sum(o["j"] * share_below(ladder(PCT["occ"][o["s"]]), LWA) / 100 for o in ms)
    pool_box = pooled(ms)
    pub = PCT["tiers"].get(k, {})
    rows.append({
        "t": k,
        "short": SHORT[k],
        "jobsAll": TMAP[k]["jobs"],
        "share": TMAP[k]["share"],
        "nocc": TMAP[k]["nocc"],
        "med": TMAP[k]["med"],
        "open": TMAP[k]["open"],
        "jobs": round(jobs),
        "belowN": round(belowN),
        "below": belowN / jobs * 100,
        "above": 100 - belowN / jobs * 100,
        "aboveOld": TMAP[k]["above"][LC["defaultLW"]],
        "box": pool_box,
        "boxPub": {k2: pub.get(k2) for _, k2 in PTS},
        "spread": pool_box["p90"] / pool_box["p10"],
        "spreadPub": (pub["p90"] / pub["p10"]) if pub.get("p10") else None,
    })

# --- the funnel: how many doors each credential opens ----------------------
MIN_OPEN = 50
fun = []
for k in ORDER:
    ms = [o for o in LC["allOcc"] if o["t"] == k]
    hire = [o for o in ms if (o.get("o") or 0) >= MIN_OPEN]
    pay = [o for o in hire if o.get("m") and o["m"] >= LWA]
    fun.append({
        "t": k, "nAll": len(ms), "nHiring": len(hire), "nPaying": len(pay),
        "openAll": sum(o.get("o") or 0 for o in ms),
        "openPaying": sum(o.get("o") or 0 for o in pay),
        "jobsPaying": sum(o["j"] for o in pay),
    })

print("%-26s %7s %6s %7s %7s %7s %7s  %7s %7s" %
      ("CREDENTIAL", "JOBS", "SHARE", "MEDIAN", "ABOVE", "(WAS)", "DELTA", "SPREAD", "(PUB)"))
for r in rows:
    print("%-26s %7s %5.1f%% %7s %6.1f%% %6.1f%% %+6.1f  %6.2fx %6.2fx" %
          (r["short"], f"{r['jobs']:,}", r["share"], f"${r['med']:,}",
           r["above"], r["aboveOld"], r["above"] - r["aboveOld"],
           r["spread"], r["spreadPub"]))
print()
print("%-26s %6s %6s %6s %8s %8s" % ("", "OCC", "HIRING", "PAYING", "OPENINGS", "PAYING"))
for r in fun:
    print("%-26s %6d %6d %6d %8s %8s" %
          (r["t"], r["nAll"], r["nHiring"], r["nPaying"],
           f"{round(r['openAll']):,}", f"{round(r['openPaying']):,}"))
print()
print("--- the step between rungs (pooled medians) ---")
for i in range(1, len(rows)):
    a, b = rows[i - 1], rows[i]
    print("  %-26s -> %-26s  %+8s  %+6.1f pts above LW" %
          (a["short"], b["short"], f"${b['box']['p50'] - a['box']['p50']:,}",
           b["above"] - a["above"]))

json.dump({"lwa": LWA, "lw": LC["defaultLW"], "rows": rows, "funnel": fun,
           "minOpen": MIN_OPEN, "totalJobs": LC["totalJobs"],
           "pricedJobs": round(sum(r["jobs"] for r in rows))},
          io.open(os.path.join(H, "_pathfacts.json"), "w", encoding="utf-8"), indent=1)
print("\nwrote _pathfacts.json")
