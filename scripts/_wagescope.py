"""Throwaway: what is actually available for a rebuilt Wage quality tab?

Three questions. What does sow.json already carry per county (the local cost
floor is the interesting one). What does the materialised county slice carry
that the statewide export does not. And does the sharpest idea -- pay measured
against each county's own living wage rather than the state's -- actually
separate the counties, or does it collapse to the same ranking?
"""
import json, os, sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(HERE, "..", "data", n), encoding="utf-8"))

sow = D("sow.json")
lc = D("lightcast.json")
pct = D("percentiles.json")
cmp_ = D("compare.json")
cty = D("counties.json")

print("sow keys:", list(sow.keys()))
print("one region:", json.dumps(sow["regions"][0], indent=0))
print("\nlightcast keys:", list(lc.keys()))
print("percentiles keys:", list(pct.keys()))
print("compare keys:", list(cmp_.keys()))
print("living wage households:", list(lc["livingWage"].keys()))
print("default LW:", lc["defaultLW"], "hours:", lc.get("hours"))

print("\n--- county living wage against the state benchmark ---")
lwA_state = lc["livingWage"][lc["defaultLW"]] * lc["hours"]
print("state benchmark (%s): $%s/yr" % (lc["defaultLW"], f"{lwA_state:,.0f}"))
byc = {r["c"]: r for r in sow["regions"]}
rows = []
for c in cty["counties"]:
    r = byc.get(c["c"])
    if not r:
        continue
    rows.append((c["c"], c["emp"], c["med"], r["lwA"], c["med"] / r["lwA"],
                 c["med"] / lwA_state))
rows.sort(key=lambda t: -t[4])
print("%-12s %9s %9s %9s %7s %7s" % ("COUNTY", "JOBS", "MED JOB", "LOCAL LW", "x LOCAL", "x STATE"))
for c, e, m, lw, xl, xs in rows:
    print("%-12s %9s %9s %9s %7.2f %7.2f" % (c, f"{e:,}", f"${m:,}", f"${lw:,.0f}", xl, xs))
print("\nspread on the local floor: %.2f to %.2f" % (rows[-1][4], rows[0][4]))
print("would the ranking change? local order vs state order:")
local = [t[0] for t in sorted(rows, key=lambda t: -t[4])]
state = [t[0] for t in sorted(rows, key=lambda t: -t[5])]
print("  local:", ", ".join(local[:5]), "...")
print("  state:", ", ".join(state[:5]), "...")
print("  same order:", local == state)
