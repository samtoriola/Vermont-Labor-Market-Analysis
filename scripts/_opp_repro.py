"""Can the opportunity index be rebuilt from committed data alone?

build_sow.py computes it from two local CSVs on G:, then goes on to query
BigQuery for everything else, so re-running the whole builder to change one
component is not on. If the index reproduces exactly from data/lightcast.json
and data/percentiles.json, the component can be swapped locally instead.

This proves it or it does not. Nothing is written.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def D(n):
    return json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))


LC, PCT, SOW = D("lightcast.json"), D("percentiles.json"), D("sow.json")
OPP = SOW["opp"]

SKIP = {"Military", "Other"}
elig = []
for o in LC["allOcc"]:
    box = PCT["occ"].get(o["s"]) or {}
    if not o.get("m") or not box.get("p25"):
        continue
    if (o.get("j") or 0) < OPP["minJobs"]:
        continue
    if o.get("f") in SKIP or o.get("g") is None:
        continue
    elig.append({
        "soc": o["s"], "n": o["n"], "j": o["j"], "m": o["m"], "o": o.get("o"),
        "p": o.get("p") or 0, "g": o["g"], "turn": o.get("turn"),
        "t": o.get("t"), "f": o.get("f"), "p25": box["p25"],
        "pp": (o["p"] / o["j"] * 100) if o.get("j") else 0,
    })

print("eligible: %d   sow says %d" % (len(elig), OPP["nEligible"]))


def pct_rank(rows, key):
    """pandas rank(pct=True)*100: average rank for ties, over the count."""
    vals = sorted(r[key] for r in rows)
    n = len(vals)
    # average rank (1-based) of each distinct value
    pos = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vals[j + 1] == vals[i]:
            j += 1
        pos[vals[i]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return {r["soc"]: pos[r[key]] / n * 100 for r in rows}


COMPS = [("size", "j"), ("growth", "g"), ("postings", "pp"), ("pay", "m")]
ranks = {lab: pct_rank(elig, col) for lab, col in COMPS}
for r in elig:
    for lab, _ in COMPS:
        r["s_" + lab] = ranks[lab][r["soc"]]
    r["sc"] = sum(r["s_" + lab] for lab, _ in COMPS) / len(COMPS)

by_soc = {r["soc"]: r for r in elig}
print()
print("%-10s %-40s %7s %7s" % ("soc", "occupation", "sow", "here"))
bad = 0
for t in OPP["top"][:10]:
    mine = by_soc.get(t["soc"])
    got = round(mine["sc"], 1) if mine else None
    flag = "" if got is not None and abs(got - t["sc"]) < 0.15 else "   <-- OFF"
    if flag:
        bad += 1
    print("%-10s %-40s %7.1f %7s%s" % (t["soc"], t["n"][:40], t["sc"], got, flag))

off = 0
for t in OPP["top"]:
    mine = by_soc.get(t["soc"])
    if not mine or abs(round(mine["sc"], 1) - t["sc"]) >= 0.15:
        off += 1
print()
print("top-30 scores reproduced: %d/%d" % (len(OPP["top"]) - off, len(OPP["top"])))

order = sorted(elig, key=lambda r: -r["sc"])
print("top 10 here, in order:")
for r in order[:10]:
    print("   %-44s %5.1f" % (r["n"][:44], r["sc"]))
