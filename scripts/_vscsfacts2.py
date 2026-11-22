"""The alignment facts, against the denominator the tab does not currently use.

The chart measures each occupation group's VSCS graduates against ALL of its
annual openings. Most of those openings are in work that asks for no credential
at all -- 6,065 a year in food preparation, 4,190 in sales -- which VSCS was never
going to supply and which a college is not the route into. Measured that way the
whole system reads at 3.5% and the five groups that get no graduates read as
failures rather than as work colleges do not feed.

sow.json already carries the right denominator as `openCred`: the 17,437 openings
a year in occupations whose entry credential is one VSCS awards. This computes
that split per occupation group, so the comparison can be made at the grain the
chart draws.
"""
import io
import json
import os
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))

LC, SOW = D("lightcast.json"), D("sow.json")
V = SOW["vscs"]
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
# The entry credentials VSCS actually awards into.
CRED = {"Sub-baccalaureate", "Bachelor's", "Graduate / professional"}

openCred = defaultdict(float)
openAll = defaultdict(float)
for o in LC["allOcc"]:
    openAll[o["f"]] += o.get("o") or 0
    if o["t"] in CRED:
        openCred[o["f"]] += o.get("o") or 0

link = {r["f"]: r["linked"] for r in V["byFamily"]}
jobs = {r["f"]: r["jobs"] for r in V["byFamily"]}
TOT_CRED = sum(openCred.values())
TOT_LINK = sum(link.values())

rows = []
for f in sorted(link, key=lambda f: -link[f]):
    oc, oa, g = openCred[f], openAll[f], link[f]
    rows.append({
        "f": f, "linked": g, "openCred": round(oc), "openAll": round(oa),
        "jobs": round(jobs[f]),
        "shareGrad": g / TOT_LINK * 100 if TOT_LINK else 0,
        "shareOpen": oc / TOT_CRED * 100 if TOT_CRED else 0,
        "ratioCred": g / oc * 100 if oc else None,
        "ratioAll": g / oa * 100 if oa else None,
    })

print("credential-requiring openings total: %s (sow.json says %s)"
      % (f"{round(TOT_CRED):,}", f"{V['openCred']:,}"))
print("graduates attributed: %.0f of %s completions" % (TOT_LINK, V["totalCompletions"]))
print()
print("%-42s %7s %9s %9s %7s %7s %7s %7s"
      % ("OCCUPATION GROUP", "GRADS", "CRED OPEN", "ALL OPEN", "%GRAD", "%OPEN", "GAP", "RATIO"))
for r in sorted(rows, key=lambda r: -(r["shareGrad"] - r["shareOpen"])):
    print("%-42s %7.1f %9s %9s %6.1f%% %6.1f%% %+6.1f %6s"
          % (r["f"][:42], r["linked"], f"{r['openCred']:,}", f"{r['openAll']:,}",
             r["shareGrad"], r["shareOpen"], r["shareGrad"] - r["shareOpen"],
             "—" if r["ratioCred"] is None else "%.0f%%" % r["ratioCred"]))

print()
print("--- the funnel ---")
stages = [
    ("VSCS completions, 2024", V["totalCompletions"]),
    ("Linked to a Vermont occupation", round(TOT_LINK)),
]
print("  %-40s %s" % ("Openings a year, all of Vermont", f"{V['openAll']:,}"))
print("  %-40s %s  (%.0f%% of them)"
      % ("...asking for a credential VSCS awards", f"{V['openCred']:,}",
         V["openCred"] / V["openAll"] * 100))
for lab, n in stages:
    print("  %-40s %s" % (lab, f"{n:,}"))
print("  %-40s %.1f%%" % ("Graduates against credential openings",
                          TOT_LINK / TOT_CRED * 100))
print("  %-40s %.1f%%" % ("...against all openings (what the tab shows)",
                          TOT_LINK / sum(openAll.values()) * 100))

noneg = [r for r in rows if not r["linked"]]
print()
print("groups with no graduates: %d — %s" % (len(noneg), ", ".join(r["f"] for r in noneg)))
print("  their credential-requiring openings: %s a year"
      % f"{sum(r['openCred'] for r in noneg):,}")
print("  their total openings:                %s a year"
      % f"{sum(r['openAll'] for r in noneg):,}")

json.dump({"rows": rows, "totCred": round(TOT_CRED), "totLink": round(TOT_LINK),
           "v": {k: V[k] for k in ("totalCompletions", "nCip", "nSocLinked", "openAll",
                                   "openCred", "openingsCovered", "allocMovedPct",
                                   "credShare", "byAward", "byInst")},
           "under": V["under"], "over": V["over"], "lwa": LWA},
          io.open(os.path.join(H, "_vscsfacts2.json"), "w", encoding="utf-8"))
print("\nwrote _vscsfacts2.json")
