"""Throwaway: every headline figure the Overview could draw on, in one place.

Pulled from the committed JSON only -- nothing is queried. The point is to see
what the dashboard already knows before deciding what its front page should say.
"""
import json, os, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(H, "..", "data", n), encoding="utf-8"))

lc, pct, cps, sow, cty, wf, glance, dem = (
    D("lightcast.json"), D("percentiles.json"), D("cps.json"), D("sow.json"),
    D("counties.json"), D("wagefloor.json"), D("glance.json"), D("demand.json"))

PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
LWA = lc["livingWage"][lc["defaultLW"]] * lc["hours"]


def lad(b):
    if not b: return None
    xs = [(b[k], q) for q, k in PTS if b.get(k)]
    return xs if len(xs) >= 2 else None


def below(xs, f):
    if not xs: return None
    if f <= xs[0][0]: return 0.0
    if f >= xs[-1][0]: return 100.0
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if v0 <= f <= v1:
            t = 0 if v1 == v0 else (f - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)


POOL = [o for o in lc["allOcc"] if lad(pct["occ"].get(o["s"]))]
jobs = sum(o["j"] for o in POOL)
belowN = sum(o["j"] * below(lad(pct["occ"][o["s"]]), LWA) / 100 for o in POOL)

groups = defaultdict(list)
for o in POOL:
    groups[o["f"]].append(o)
grows = []
for f, ms in groups.items():
    j = sum(o["j"] for o in ms)
    b = sum(o["j"] * below(lad(pct["occ"][o["s"]]), LWA) / 100 for o in ms)
    grows.append({"f": f, "jobs": int(j), "below": round(b / j * 100, 1), "belowN": int(b)})
grows.sort(key=lambda r: -r["jobs"])

last = cps["trend"][-1]
tier = {t["t"]: t for t in lc["tiers"]}
baReq = tier["Bachelor's"]["share"] + tier["Graduate / professional"]["share"]

print("=" * 72)
print("SCALE")
print("  jobs, 2025                %s   (%s detailed occupations)" % (f'{lc["totalJobs"]:,}', f'{len(lc["allOcc"]):,}'))
print("  jobs, 2021                %s   change %+.1f%%" % (f'{lc["jobs21"]:,}', (lc["totalJobs"] / lc["jobs21"] - 1) * 100))
print("  employed Vermonters       %s   (household survey, %s)" % (f'{last["emp"]:,}', last.get("y", "2025")))
print("  openings a year           %s   (%s)" % (f'{round(lc["openTotal"]/lc["openYears"]):,}', lc["window"]))
print("  separations a year        %s   turnover %.1f%%" % (f'{round(lc["sepTotal"]/lc["openYears"]):,}', lc["sepPct"]))
print("  labour force participation %.1f%%   unemployment %.2f%%" % (glance["lfpr"], glance["ur"]))
print("  full-time share           %.1f%%" % glance["ftShare"])

print("\nPAY")
print("  living wage, 1 adult      $%s/yr  ($%.2f/hr)" % (f"{round(LWA):,}", lc["livingWage"][lc["defaultLW"]]))
print("  jobs below it             %s of %s  = %.1f%%" % (f"{round(belowN):,}", f"{round(jobs):,}", belowN / jobs * 100))
print("  statewide pay ladder      p10 $%s  p50 $%s  p90 $%s"
      % tuple(f'{pct["statewide"][k]:,}' for k in ("p10", "p50", "p90")))
print("  county living wage range  $%s to $%s" % (f'{wf["lwRange"][0]:,}', f'{wf["lwRange"][1]:,}'))

print("\nWHAT JOBS ASK FOR vs WHAT WORKERS HOLD")
print("  jobs needing BA+          %.1f%%        workers holding it  %.1f%%" % (baReq, last["ba"]))
for t in lc["tiers"]:
    print("    %-26s %5.1f%% of jobs   median $%s" % (t["t"], t["share"], f'{t["med"]:,}'))

print("\nVSCS")
v = sow["vscs"]
print("  completions, 2024         %s across %s programs" % (f'{v["totalCompletions"]:,}', v.get("nPrograms", "?")))
print("  annual openings covered   %s" % f'{v["openAll"]:,}')
print("  completions per 100 openings  %.1f" % (v["totalCompletions"] / v["openAll"] * 100))

print("\nPLACES")
print("  counties                  %d   largest %s (%s jobs)" % (len(cty["counties"]), cty["counties"][0]["c"], f'{cty["counties"][0]["emp"]:,}'))
pay = sorted(cty["counties"], key=lambda r: -r["med"])
print("  typical job pay range     $%s (%s) to $%s (%s)"
      % (f'{pay[0]["med"]:,}', pay[0]["c"], f'{pay[-1]["med"]:,}', pay[-1]["c"]))

print("\nTHE 22 GROUPS, largest first")
print("  %-34s %9s %8s %10s" % ("GROUP", "JOBS", "BELOW", "PEOPLE"))
for r in grows:
    print("  %-34s %9s %7.1f%% %10s" % (r["f"][:34], f'{r["jobs"]:,}', r["below"], f'{r["belowN"]:,}'))

out = {"scale": {"jobs": lc["totalJobs"], "jobs21": lc["jobs21"], "occ": len(lc["allOcc"]),
                 "emp": last["emp"], "openings": round(lc["openTotal"] / lc["openYears"]),
                 "lfpr": glance["lfpr"], "ur": glance["ur"], "ft": glance["ftShare"],
                 "turn": lc["sepPct"]},
       "pay": {"lwA": round(LWA), "lwH": lc["livingWage"][lc["defaultLW"]],
               "belowN": round(belowN), "priced": round(jobs), "belowPct": round(belowN / jobs * 100, 1),
               "box": pct["statewide"], "ctyRange": wf["lwRange"]},
       "cred": {"baReq": round(baReq, 1), "baHold": round(last["ba"], 1),
                "tiers": [{"t": t["t"], "share": t["share"], "med": t["med"]} for t in lc["tiers"]]},
       "vscs": {"completions": v["totalCompletions"], "openAll": v["openAll"]},
       "places": {"n": len(cty["counties"]), "top": cty["counties"][0]["c"],
                  "topJobs": cty["counties"][0]["emp"],
                  "payHi": pay[0], "payLo": pay[-1]},
       "groups": grows}
json.dump(out, open(os.path.join(H, "_ovfacts.json"), "w", encoding="utf-8"), separators=(",", ":"))
print("\nwrote _ovfacts.json")
