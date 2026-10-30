"""Throwaway: does the county slice's Vermont family mix match the dashboard's?

The two come from different Lightcast products (Core LMI by county vs the
statewide occupation export), so they do not have to agree -- but a family that
disagrees by much would make every location quotient built on it wrong.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "..", "data", "counties.json"), encoding="utf-8"))
p = json.load(open(os.path.join(HERE, "..", "data", "lightcast.json"), encoding="utf-8"))

dash = {r["f"]: r["jobs"] / p["totalJobs"] * 100 for r in p["families"]}
print("%-42s %8s %8s %8s" % ("FAMILY", "SLICE", "DASH", "DIFF"))
worst = 0
for f in d["famOrder"]:
    a, b = d["state"]["share"][f], dash.get(f)
    if b is None:
        print("%-42s %8.2f   not in the statewide export" % (f, a)); continue
    worst = max(worst, abs(a - b))
    print("%-42s %8.2f %8.2f %+8.2f" % (f, a, b, a - b))
print("\nlargest gap: %.2f points" % worst)

print("\nwhat the prototype quoted, recomputed:")
for name, fam in (("Essex", "Farming, Fishing & Forestry"),
                  ("Washington", "Community & Social Service"),
                  ("Grand Isle", "Farming, Fishing & Forestry")):
    c = [x for x in d["counties"] if x["c"] == name][0]
    print("  %-11s %-34s %5.2fx  (%s of %s jobs)"
          % (name, fam, c["lq"][fam], f"{c['jobs'][fam]:,}", f"{c['emp']:,}"))

print("\nsharpest specialisation anywhere:")
best = sorted(((c["lq"][f], c["c"], f, c["jobs"][f], c["thin"])
               for c in d["counties"] for f in d["famOrder"]), reverse=True)[:8]
for lq, c, f, j, thin in best:
    print("  %5.2fx  %-11s %-34s %6s jobs%s" % (lq, c, f, f"{j:,}", "  (thin)" if thin else ""))
