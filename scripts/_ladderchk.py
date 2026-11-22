"""Throwaway: how much narrower is the published family/tier ladder than the real one?

percentiles.json's family and tier ladders are the employment-weighted MEAN of
their occupations' percentiles. Q4's "Range of outcomes" measure divides p90 by
p10 on that ladder and calls it the range of outcomes at a credential level,
which is a different and much smaller quantity than the spread of the jobs.
"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
pct = json.load(open(os.path.join(H, "..", "data", "percentiles.json"), encoding="utf-8"))
mock = json.load(open(os.path.join(H, "_mock_wage.json"), encoding="utf-8"))

print("%-26s %11s %11s %7s %7s" % ("ENTRY CREDENTIAL", "PUBLISHED", "POOLED", "PUB x", "REAL x"))
for c in mock["creds"]:
    p = pct["tiers"].get(c["f"])
    if not p:
        continue
    print("%-26s %5s-%5s %5s-%5s %6.2f %6.2f"
          % (c["f"][:26], f"{p['p10']//1000:,}k", f"{p['p90']//1000:,}k",
             f"{c['box']['p10']//1000:,}k", f"{c['box']['p90']//1000:,}k",
             p["p90"] / p["p10"], c["box"]["p90"] / c["box"]["p10"]))

print()
print("%-26s %11s %11s %7s %7s" % ("OCCUPATION GROUP", "PUBLISHED", "POOLED", "PUB x", "REAL x"))
worst = []
for f in mock["families"]:
    p = pct["families"].get(f["f"])
    if not p:
        continue
    worst.append((f["box"]["p90"] / f["box"]["p10"] - p["p90"] / p["p10"], f["f"], p, f["box"]))
for d, name, p, b in sorted(worst, reverse=True)[:6]:
    print("%-26s %5s-%5s %5s-%5s %6.2f %6.2f"
          % (name[:26], f"{p['p10']//1000:,}k", f"{p['p90']//1000:,}k",
             f"{b['p10']//1000:,}k", f"{b['p90']//1000:,}k",
             p["p90"] / p["p10"], b["p90"] / b["p10"]))
