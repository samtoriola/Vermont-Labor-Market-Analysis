"""Facts for the "Which credentials pay" prototype. Committed JSON only.

The section screens every Vermont occupation twice -- hiring in volume, then
paying a living wage -- and prints the counts in a table. This recomputes that
screen, and three things the table cannot say:

  Which occupations actually clear it, by name. The table says "3 of 106" and
  stops, which is exactly where the reader's next question starts.

  The same screen counted in annual openings rather than in occupations, which is
  what a person leaving a credential actually faces.

  What the pay gate costs. "Paying a living wage" is the occupation's median
  against the benchmark -- the median rule, used here on a question about the
  occupation rather than about its jobs, which is the one place it is defensible.
  But an occupation whose median clears by a dollar still has half its jobs
  below, so the gate's answer and the distribution's answer are worth setting
  side by side.
"""
import io
import json
import os
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))

LC, PCT = D("lightcast.json"), D("percentiles.json")
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
MIN_OPEN = 50
PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
ORDER = ["No formal credential", "High school", "Sub-baccalaureate",
         "Bachelor's", "Graduate / professional"]
SHORT = {"No formal credential": "None", "High school": "High school",
         "Sub-baccalaureate": "Sub-bacc.", "Bachelor's": "Bachelor's",
         "Graduate / professional": "Graduate"}


def ladder(box):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, v):
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


rows = []
pts = []
for t in ORDER:
    allo = [o for o in LC["allOcc"] if o["t"] == t]
    hiring = [o for o in allo if (o.get("o") or 0) >= MIN_OPEN]
    paying = [o for o in hiring if o.get("m") and o["m"] >= LWA]
    open_all = sum(o.get("o") or 0 for o in allo)
    open_pay = sum(o["o"] for o in paying)
    # The same openings weighted by how much of each occupation actually clears
    # the benchmark, with no volume gate at all.
    wopen = 0.0
    for o in allo:
        s = share_below(ladder(PCT["occ"].get(o["s"])), LWA)
        if s is not None:
            wopen += (o.get("o") or 0) * (100 - s) / 100
    top = sorted(paying, key=lambda o: -(o.get("o") or 0))[:6]
    rows.append({
        "t": t, "short": SHORT[t],
        "nAll": len(allo), "nHiring": len(hiring), "nPaying": len(paying),
        "openAll": round(open_all), "openPay": round(open_pay),
        "shareOpen": open_pay / open_all * 100 if open_all else None,
        "wOpen": round(wopen), "wShare": wopen / open_all * 100 if open_all else None,
        "jobsPay": round(sum(o["j"] for o in paying)),
        "top": [{"n": o["n"], "o": round(o["o"]), "m": o["m"], "j": round(o["j"]),
                 "below": round(share_below(ladder(PCT["occ"].get(o["s"])), LWA) or 0, 1)}
                for o in top],
        # the big near-misses: hiring hard, median under the benchmark
        "miss": [{"n": o["n"], "o": round(o["o"]), "m": o["m"]}
                 for o in sorted([x for x in hiring if not (x.get("m") and x["m"] >= LWA)],
                                 key=lambda o: -(o.get("o") or 0))[:4]],
    })
    for o in allo:
        if o.get("o") and o.get("m"):
            pts.append([ORDER.index(t), round(o["o"]), o["m"], round(o["j"]), o["n"]])

print("%-26s %5s %7s %7s %10s %10s %7s %10s %7s" %
      ("CREDENTIAL", "OCC", "HIRING", "PAYING", "OPENINGS", "THAT PAY", "SHARE", "WEIGHTED", "SHARE"))
for r in rows:
    print("%-26s %5d %7d %7d %10s %10s %6.1f%% %10s %6.1f%%" %
          (r["t"], r["nAll"], r["nHiring"], r["nPaying"],
           f"{r['openAll']:,}", f"{r['openPay']:,}", r["shareOpen"],
           f"{r['wOpen']:,}", r["wShare"]))
print()
for r in rows:
    print(r["t"])
    for o in r["top"]:
        print("    + %-46s %6s openings  %9s  %4.0f%% of its jobs below" %
              (o["n"][:46], f"{o['o']:,}", f"${o['m']:,}", o["below"]))
    for o in r["miss"]:
        print("    - %-46s %6s openings  %9s  (median under)" %
              (o["n"][:46], f"{o['o']:,}", f"${o['m']:,}"))
    print()

json.dump({"lwa": LWA, "lw": LC["defaultLW"], "minOpen": MIN_OPEN,
           "rows": rows, "pts": pts, "order": ORDER},
          io.open(os.path.join(H, "_doorfacts.json"), "w", encoding="utf-8"))
print("wrote _doorfacts.json ·", len(pts), "points")
