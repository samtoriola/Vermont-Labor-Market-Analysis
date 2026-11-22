"""Facts for the Opportunities prototype. Committed JSON only."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))

LC, SOW, PCT = D("lightcast.json"), D("sow.json"), D("percentiles.json")
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
O = SOW["opp"]
VSCS = SOW["vscs"]
BYSOC = VSCS.get("bySoc", {})

print("opp keys:", sorted(O.keys()))
print("weightEach", O.get("weightEach"), "minJobs", O.get("minJobs"), "nEligible", O.get("nEligible"))
print("top:", len(O["top"]), "byTier:", {k: len(v) for k, v in O["byTier"].items()})
print()
print("one row:", json.dumps(O["top"][0], indent=1))
print()
print("%-44s %5s %6s %6s %6s %6s" % ("THE 12 HIGHEST SCORING", "SCORE", "SIZE", "GROWTH", "ADS", "PAY"))
for r in O["top"][:12]:
    print("%-44s %5.1f %6.0f %6.0f %6.0f %6.0f"
          % (r["n"][:44], r["sc"], r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"]))

# How much does the composite hide? The spread of an occupation's own four ranks.
print()
spreads = sorted(O["top"], key=lambda r: -(max(r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"])
                                           - min(r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"])))
print("WIDEST GAP BETWEEN AN OCCUPATION'S OWN FOUR RANKS")
for r in spreads[:6]:
    c = [r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"]]
    print("  %-42s score %5.1f  from %3.0f to %3.0f  (%s)"
          % (r["n"][:42], r["sc"], min(c), max(c),
             " ".join("%s %.0f" % (k, v) for k, v in
                      zip(("size", "grow", "ads", "pay"), c))))
print()
print("NARROWEST")
for r in spreads[-4:]:
    c = [r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"]]
    print("  %-42s score %5.1f  from %3.0f to %3.0f" % (r["n"][:42], r["sc"], min(c), max(c)))

# ---- the screen -----------------------------------------------------------
SCREEN_TIERS = ["Sub-baccalaureate", "Bachelor's"]
MIN_OPEN = 50
THIN = 0.08
GROWTH_FLOOR = 3
obvious = {r["soc"] for r in LC["topOcc"][:25]}


def med(xs):
    v = sorted(x for x in xs if x is not None)
    if not v:
        return 0
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


base = [o for o in LC["allOcc"]
        if o.get("m") and o["m"] >= LWA and o.get("o") and o["o"] >= MIN_OPEN
        and o["t"] in SCREEN_TIERS and o["s"] not in obvious]
norms = {}
for t in SCREEN_TIERS:
    w = [o for o in base if o["t"] == t and o.get("j")]
    norms[t] = {"op": med([(o["o"] / o["j"]) * 100 for o in w]),
                "post": med([(o["p"] / o["j"]) * 100 for o in w])}

cand = []
for o in base:
    n = norms.get(o["t"], {"op": 0, "post": 0})
    opr = (o["o"] / o["j"]) * 100 if o.get("j") else 0
    pr = (o["p"] / o["j"]) * 100 if o.get("j") else 0
    sig = [x for x in (
        "openings" if opr > n["op"] else None,
        "postings" if pr > n["post"] else None,
        "growth" if (o.get("g") or 0) > GROWTH_FLOOR else None) if x]
    sup = BYSOC.get(o["s"], {})
    linked = sup.get("linked", 0) or 0
    ratio = sup.get("ratio")
    pipeline = ("No VSCS pipeline" if linked == 0
                else "Thin pipeline" if (ratio is not None and ratio < THIN)
                else "Established pipeline")
    cand.append({"n": o["n"], "s": o["s"], "o": round(o["o"]), "j": round(o["j"]),
                 "m": o["m"], "g": o.get("g"), "t": o["t"], "f": o["f"],
                 "linked": round(linked, 1), "ratio": ratio, "pipeline": pipeline,
                 "sig": sig, "nSig": len(sig), "opRate": round(opr, 1), "postRate": round(pr, 1)})
cand.sort(key=lambda r: -r["o"])

print()
print("THE SCREEN AT ITS DEFAULTS: %d occupations" % len(cand))
from collections import Counter
print("  pipeline:", dict(Counter(r["pipeline"] for r in cand)))
print("  signals :", dict(Counter(r["nSig"] for r in cand)))
acted = [r for r in cand if r["nSig"] >= 2 and r["pipeline"] != "Established pipeline"]
print("  2+ signals and not established: %d" % len(acted))
print()
print("%-44s %6s %7s %7s %9s %5s %s" %
      ("", "OPEN", "JOBS", "PAY", "GRADS", "SIG", "PIPELINE"))
for r in cand[:16]:
    print("%-44s %6s %7s %8s %9s %5d %s"
          % (r["n"][:44], f"{r['o']:,}", f"{r['j']:,}", f"${r['m']:,}",
             r["linked"], r["nSig"], r["pipeline"]))

json.dump({"lwa": LWA, "lw": LC["defaultLW"], "minOpen": MIN_OPEN,
           "weightEach": O.get("weightEach"), "minJobs": O.get("minJobs"),
           "nEligible": O.get("nEligible"), "top": O["top"], "cand": cand,
           "acted": [r["s"] for r in acted], "tiers": SCREEN_TIERS},
          io.open(os.path.join(H, "_oppfacts.json"), "w", encoding="utf-8"))
print()
print("wrote _oppfacts.json")
