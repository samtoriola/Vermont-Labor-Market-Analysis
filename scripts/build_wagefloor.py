"""Builds data/wagefloor.json: each county's jobs measured against its own cost floor.

WHY THIS FILE EXISTS AT ALL
---------------------------
Everything else the Wage quality tab needs is already in the browser. The share
of an occupation's jobs paying below a benchmark is read off that occupation's
own p10-p90 ladder, which data/percentiles.json already carries for all of them,
so the group, credential and occupation figures are computed live in lib/wage.js
-- which is also why the filter bar moves them.

The counties are the exception. A county's answer needs the pay ladder of every
occupation *within that county*, and that lives only in the Core LMI county
slice on the shared drive. So it is computed here, once, and committed.

THE MEASURE
-----------
Not the median rule. "Share above the living wage" used to compare an
occupation's median with the benchmark and then count all of that occupation's
jobs on one side of it: a median a dollar over put 100% of its jobs above, a
dollar under put 0% there. Half the people in each are on the wrong side of that
line. Statewide the errors mostly cancel -- 42.5% against 41.1% -- which is why
it survived; by occupation group they do not.

Here the benchmark's position is interpolated along each occupation's own
ladder, and the result weighted by that occupation's employment in the county.
An occupation whose ladder never reaches the benchmark counts 100% below; one
whose p10 already clears it counts 0%. Outside p10 and p90 the ladder says
nothing, so it is clamped rather than extrapolated.

TWO FLOORS, EVERY HOUSEHOLD
---------------------------
`local` measures each county against its own living wage; `state` measures the
same county against the statewide figure. Holding the household fixed is what
isolates geography, which is the whole point of showing the pair side by side --
but the household it is fixed AT is the reader's to choose, and for a long time
this file said otherwise: "the only household type published per county" was
wrong. scripts/vt_living_wage.csv carries all six MIT households for all 14
counties and for the state, and the build read one column of it.

Both floors now move together across households. The scalar `local` / `state` /
`lwA` fields keep meaning the default household so nothing downstream shifts
under them; `byLw` carries the full set, computed the same way rather than
rescaled from it.

WHICH ROWS
----------
Classes 1 and 2 and occupation level 5, matching build_counties.py exactly, so
the two files describe the same labour market. Rows whose ladder is missing or
unusable are dropped from both the numerator and the denominator, and the
coverage that leaves is reported in `cov` so the tab can say so.
"""
import json
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
CSV = os.path.join(FOLDER, "VT_CoreLMI_Occupation_by_County_2021_2025.csv")
OUT = os.path.join(HERE, "..", "data", "wagefloor.json")

YEAR = 2025
CLASSES = [1, 2]
OCC_LEVEL = 5
PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
# The grid a pooled ladder is sampled on. Dense enough that the group's p10 and
# p90 land where its jobs actually put them rather than on a member's quartile.
QS = list(range(5, 100, 2))


def D(name):
    with open(os.path.join(HERE, "..", "data", name), encoding="utf-8") as f:
        return json.load(f)


def ladder(box):
    """[(pay, quantile)] for one occupation, lowest first, or None if unusable."""
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, floor):
    """Percent of one occupation's jobs paying under `floor`.

    Clamped outside p10 and p90: the ladder says nothing out there, and
    extrapolating would invent a figure rather than read one.
    """
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
    """The pay at quantile `q`, interpolated along one occupation's ladder."""
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
    """A true p10-p90 for a county: pool its occupations' ladders by employment.

    Not the mean of their percentiles. A county's lowest-paid tenth is the tenth
    percentile of its jobs, which sits far below the average of its occupations'
    tenth percentiles -- averaging those away is averaging away the gap between
    one occupation and the next, which is most of the spread there is.

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
    want = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
    out, run, i = {}, 0.0, 0
    for v, w in pts:
        run += w
        while i < len(want) and run / total * 100 >= want[i][0]:
            out[want[i][1]] = round(v)
            i += 1
    while i < len(want):
        out[want[i][1]] = round(pts[-1][0])
        i += 1
    return out


lc, sow, cty = D("lightcast.json"), D("sow.json"), D("counties.json")
HOURS = lc["hours"]
LW_KEY = lc["defaultLW"]
LWA = round(lc["livingWage"][LW_KEY] * HOURS)

d = pd.read_csv(CSV, dtype={"areaid": str, "occid": str, "classid": int})
d["year"] = d["year"].astype(float).astype(int)
d["occ_level"] = d["occ_level"].astype(float).astype(int)
d = d[(d.year == YEAR) & (d.occ_level == OCC_LEVEL) & d.classid.isin(CLASSES) & (d.emp > 0)]
for _, k in PTS:
    d["a_" + k] = d["earn_" + k] * HOURS

fips = {r["c"]: r["fips"] for r in sow["regions"]}
lwa = {r["c"]: round(r["lwA"]) for r in sow["regions"]}

# The MIT table, all six households wide. Its column names are household codes
# -- a1c2 is one adult with two children -- and the dashboard's own key for each
# is the sentence it prints, so the two are matched here once and asserted
# against the statewide figure the app already carries.
HH = {
    "1 adult, no children": ("Living Wage", "a1c0"),
    "1 adult, 1 child": ("Living Wage", "a1c1"),
    "1 adult, 2 children": ("Living Wage", "a1c2"),
    "2 adults (both working), no children": ("Living Wage", "a2w2c0"),
    "2 adults (both working), 2 children": ("Living Wage", "a2w2c2"),
    "2 adults (1 working), 2 children": ("Living Wage", "a2w1c2"),
    "Vermont minimum wage": ("Minimum Wage", "a1c0"),
    "Poverty wage (1 adult)": ("Poverty Wage", "a1c0"),
}
mit = pd.read_csv(os.path.join(HERE, "vt_living_wage.csv"), dtype={"region_id": str})
mit["region_id"] = mit.region_id.str.zfill(5)


def floors(region_id):
    """Annual floor per household for one FIPS, or for the state as '00050'."""
    sub = mit[mit.region_id == region_id]
    out = {}
    for key, (wtype, col) in HH.items():
        row = sub[sub.wage_type == wtype]
        if row.empty:
            continue
        out[key] = round(float(row.iloc[0][col]) * HOURS)
    return out


STATE_LW = floors("00050")
for key, want in lc["livingWage"].items():
    got = STATE_LW.get(key)
    if got is None or abs(got - round(want * HOURS)) > 1:
        raise SystemExit("MIT table disagrees with the app on %r: %s vs %s"
                         % (key, got, round(want * HOURS)))
print("MIT households reconciled against lightcast.json: %d\n" % len(STATE_LW))
COUNTY_LW = {c: floors(fips[c]) for c in fips}

counties = []
for c in cty["counties"]:
    sub = d[d.areaid == fips[c["c"]]]
    if sub.empty:
        continue
    local = state = den = 0.0
    members = []
    # One running pair of sums per household, filled in the same pass.
    acc = {k: [0.0, 0.0] for k in STATE_LW}
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
        members.append((xs, r.emp))
        for k in STATE_LW:
            acc[k][0] += r.emp * share_below(xs, COUNTY_LW[c["c"]][k]) / 100
            acc[k][1] += r.emp * share_below(xs, STATE_LW[k]) / 100
    counties.append({
        "c": c["c"],
        "jobs": c["emp"],
        "med": c["med"],
        "thin": c["thin"],
        "lwA": lwa[c["c"]],
        # Priced jobs -- the denominator these shares are actually taken over,
        # which is smaller than the county's employment headline.
        "priced": int(round(den)),
        "cov": round(den / sub.emp.sum() * 100, 1),
        "local": round(local / den * 100, 1),
        "localN": int(round(local)),
        "state": round(state / den * 100, 1),
        "stateN": int(round(state)),
        "box": pooled(members),
        # Every household, same arithmetic. The default household's entry here
        # reproduces the scalars above, which check_workfiles asserts.
        "byLw": {
            k: {
                "lwA": COUNTY_LW[c["c"]][k],
                "local": round(acc[k][0] / den * 100, 1),
                "localN": int(round(acc[k][0])),
                "state": round(acc[k][1] / den * 100, 1),
                "stateN": int(round(acc[k][1])),
            }
            for k in STATE_LW
        },
    })

counties.sort(key=lambda r: -r["local"])
out = {
    "year": YEAR,
    "lwKey": LW_KEY,
    "lwA": LWA,
    "hours": HOURS,
    "lwRange": [min(lwa.values()), max(lwa.values())],
    "households": list(STATE_LW),
    "stateLw": STATE_LW,
    "lwRangeBy": {
        k: [min(COUNTY_LW[c][k] for c in COUNTY_LW), max(COUNTY_LW[c][k] for c in COUNTY_LW)]
        for k in STATE_LW
    },
    "counties": counties,
    "note": (
        "Share of each county's priced jobs paying below a living wage, read off "
        "each occupation's own pay ladder and weighted by its employment in that "
        "county. `local` uses the county's own living wage, `state` the statewide "
        "one. The scalar fields are one adult with no children; `byLw` carries "
        "all eight benchmarks, each computed the same way, so the household is "
        "the reader's to pick and both floors move together when they do."
    ),
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, separators=(",", ":"))

print("wrote %s (%s bytes)" % (os.path.abspath(OUT), f"{os.path.getsize(OUT):,}"))
print("statewide floor $%s (%s)\n" % (f"{LWA:,}", LW_KEY))
print("%-12s %9s %9s %10s %10s %7s" % ("COUNTY", "PRICED", "OWN FLOOR", "BELOW OWN", "BELOW ST", "COV"))
for r in counties:
    print("%-12s %9s %9s %9.1f%% %9.1f%% %6.1f%%"
          % (r["c"], f"{r['priced']:,}", f"${r['lwA']:,}", r["local"], r["state"], r["cov"]))
