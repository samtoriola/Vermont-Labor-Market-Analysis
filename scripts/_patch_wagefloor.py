"""County living wage: carry every household, not just one adult.

The section's own doc block said one adult with no children is "the only
household type published per county". That is not true -- scripts/vt_living_wage.csv
has had all six MIT households per county the whole time, and the build only ever
read one column of it. The tab then withheld the household selector on the
grounds of a limit that did not exist.

So the build now computes `local` and `state` for every household, the same way
it computes them for one adult: the benchmark's position on each occupation's own
ladder, weighted by that occupation's employment in that county. Not recomputed in
the browser off the pooled county ladder, which would disagree with the committed
figure at the default household and look like a bug.

ADDITIVE ON PURPOSE. The existing scalar fields stay exactly as they are and keep
meaning the default household, so build_workfiles, check_workfiles and the suites
that read them do not move. The new per-household block sits beside them under
`byLw`, and the tab reads it only when the reader picks something else.

Checks every substitution before writing anything.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "build_wagefloor.py")
s = io.open(P, encoding="utf-8").read()

subs = [
    # ---- the doc block, which asserted a limit that is not real -----------
    ("""TWO FLOORS, ONE HOUSEHOLD
-------------------------
`local` measures each county against its own living wage; `state` measures the
same county against the statewide figure. Both are one adult with no children,
because that is the only household type published per county -- so the pair
isolates geography, which is the whole point of showing them side by side. The
tab does not offer the household selector on this section for that reason.""",
     """TWO FLOORS, EVERY HOUSEHOLD
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
rescaled from it.""",),

    # ---- read the per-household floors ------------------------------------
    ("""fips = {r["c"]: r["fips"] for r in sow["regions"]}
lwa = {r["c"]: round(r["lwA"]) for r in sow["regions"]}""",
     """fips = {r["c"]: r["fips"] for r in sow["regions"]}
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
    \"\"\"Annual floor per household for one FIPS, or for the state as '00050'.\"\"\"
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
print("MIT households reconciled against lightcast.json: %d\\n" % len(STATE_LW))
COUNTY_LW = {c: floors(fips[c]) for c in fips}""",),

    # ---- compute every household, not only the default --------------------
    ("""    local = state = den = 0.0
    members = []
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
        members.append((xs, r.emp))""",
     """    local = state = den = 0.0
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
            acc[k][1] += r.emp * share_below(xs, STATE_LW[k]) / 100""",),

    ("""        "state": round(state / den * 100, 1),
        "stateN": int(round(state)),
        "box": pooled(members),
    })""",
     """        "state": round(state / den * 100, 1),
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
    })""",),

    # ---- and say so at the top level --------------------------------------
    ("""    "lwRange": [min(lwa.values()), max(lwa.values())],
    "counties": counties,
    "note": (
        "Share of each county's priced jobs paying below a living wage, read off "
        "each occupation's own pay ladder and weighted by its employment in that "
        "county. `local` uses the county's own living wage, `state` the statewide "
        "one; both are one adult with no children, the only household type "
        "published per county."
    ),""",
     """    "lwRange": [min(lwa.values()), max(lwa.values())],
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
    ),""",),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:90]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("build_wagefloor.py patched,", len(s), "bytes")
