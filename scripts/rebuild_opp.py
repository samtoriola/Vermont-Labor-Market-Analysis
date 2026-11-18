"""Rebuild the opportunity index with replacement in place of advertising.

WHY THIS IS A SEPARATE SCRIPT
build_sow.py owns the index, but it also queries BigQuery for the VSCS crosswalk
and the ACS county tables, so re-running it to change one component means paying
for the other two. The index itself needs nothing but data/lightcast.json and
data/percentiles.json, which scripts/_opp_repro.py established: the eligible set
comes back at 406 of 406, and 29 of the 30 published scores reproduce to within
0.15 (Sales Managers moves 0.2, because lightcast.json rounds projected growth to
one decimal and the builder had full precision). So the index is rebuilt here,
from committed data, and build_sow.py's own COMPS list is updated to match so a
future full rebuild agrees.

WHAT CHANGED, AND THE CAVEAT
The 11/18 review asks for advertising to be replaced by replacement, ranked so
that low replacement scores high -- a stable occupation being the better bet.

That is defensible and it is what this does. It is also worth knowing that
build_sow.py had already dropped a turnover-shaped component once, for a measured
reason: openings per 100 jobs correlated -0.675 with pay, "because Vermont's
high-turnover occupations are its low-wage ones", and contributed -4.7% of
composite variance. Inverting the sign does not remove that relationship, it
flips it: low-replacement work is well-paid work, so the new component and the
pay component now point the same way rather than cancelling.

The correlation is printed every run. Read it before trusting the ranking: a
component that correlates highly with pay is giving the wage dimension a second
vote under another name, which is exactly why "adequacy" was dropped.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(H, "..", "data")


def D(n):
    return json.load(io.open(os.path.join(DATA, n), encoding="utf-8"))


LC, PCT = D("lightcast.json"), D("percentiles.json")
SOW_PATH = os.path.join(DATA, "sow.json")
SOW = json.load(io.open(SOW_PATH, encoding="utf-8"))
OPP = SOW["opp"]
MINJ = OPP["minJobs"]
SKIP = {"Military", "Other"}

elig = []
for o in LC["allOcc"]:
    box = PCT["occ"].get(o["s"]) or {}
    if not o.get("m") or not box.get("p25"):
        continue
    if (o.get("j") or 0) < MINJ or o.get("f") in SKIP or o.get("g") is None:
        continue
    # A replacement rate is the component now, so an occupation without one
    # cannot be scored. Lightcast suppresses it below 10 jobs; nothing here is
    # under 100, so this should drop nothing, and it says so if it does.
    if o.get("turn") is None:
        print("  no replacement rate, dropped: %s (%s jobs)" % (o["n"], o["j"]))
        continue
    elig.append({
        "soc": o["s"], "n": o["n"], "j": o["j"], "m": o["m"],
        "o": round(o.get("o") or 0), "p": int(o.get("p") or 0),
        "g": o["g"], "turn": o["turn"], "t": o.get("t"), "f": o.get("f"),
        "p25": box["p25"],
        "pp": round(o["p"] / o["j"] * 100, 1) if o.get("j") else 0,
        "op": round((o.get("o") or 0) / o["j"] * 100, 1) if o.get("j") else 0,
    })

LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
for r in elig:
    r["lw"] = round(r["m"] / LWA, 2)
    r["lw25"] = round(r["p25"] / LWA, 2)


def pct_rank(rows, keyfn):
    """pandas rank(pct=True) * 100 -- average rank for ties, over the count."""
    vals = sorted(keyfn(r) for r in rows)
    n = len(vals)
    pos, i = {}, 0
    while i < n:
        j = i
        while j + 1 < n and vals[j + 1] == vals[i]:
            j += 1
        pos[vals[i]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return [pos[keyfn(r)] / n * 100 for r in rows]


# Low replacement ranks high, which is the whole point of the swap: a negated
# rate put through the same ascending rank as everything else.
COMPS = [
    ("size", lambda r: r["j"]),
    ("growth", lambda r: r["g"]),
    ("replacement", lambda r: -r["turn"]),
    ("pay", lambda r: r["m"]),
]
for lab, fn in COMPS:
    col = pct_rank(elig, fn)
    for r, v in zip(elig, col):
        r["s_" + lab] = v
for r in elig:
    r["sc"] = sum(r["s_" + lab] for lab, _ in COMPS) / len(COMPS)


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


print("eligible occupations: %d\n" % len(elig))
print("component correlation matrix:")
labs = [l for l, _ in COMPS]
cols = {l: [r["s_" + l] for r in elig] for l in labs}
print("              " + "".join("%12s" % l for l in labs))
worst = (0.0, None)
for a in labs:
    row = "%-14s" % a
    for b in labs:
        rr = pearson(cols[a], cols[b])
        row += "%12.3f" % rr
        if a != b and abs(rr) > worst[0]:
            worst = (abs(rr), (a, b))
    print(row)
print("\nhighest absolute off-diagonal: %.3f  %s" % worst)
if worst[0] >= 0.6:
    print("  NOTE: at this level two components are substantially the same measure.")
    print("  The build dropped 'adequacy' for exactly this (r = 1.000 with pay).")

elig.sort(key=lambda r: -r["sc"])
prev = {t["soc"]: t["sc"] for t in OPP["top"]}
print("\ntop 15 under the new index (was: rank under the old top-30 where known):")
for i, r in enumerate(elig[:15], 1):
    was = prev.get(r["soc"])
    print("  %2d. %-44s %5.1f   %s" % (i, r["n"][:44], r["sc"],
                                       ("was %.1f" % was) if was else "not in the old top 30"))
dropped = [t["n"] for t in OPP["top"][:15] if t["soc"] not in {r["soc"] for r in elig[:15]}]
if dropped:
    print("\nleft the top 15: %s" % ", ".join(dropped))

KEEP = ["soc", "n", "j", "m", "o", "p", "g", "pp", "op", "turn", "p25", "lw25",
        "lw", "t", "f", "sc"]


def row(r):
    d = {k: r[k] for k in KEEP}
    d["sc"] = round(r["sc"], 1)
    d["exp"] = None
    d["ojt"] = None
    for lab, _ in COMPS:
        d["s_" + lab] = round(r["s_" + lab])
    return d


OPP["components"] = labs
OPP["note"] = "equal-weight mean of four percentile ranks, 25% each"
OPP["dropped"] = ("adequacy (r=1.000 with pay); openings intensity; postings intensity, "
                  "replaced by the replacement rate at the 11/18 review")
OPP["replacementNote"] = ("Low replacement ranks high: a lower share of the workforce "
                          "leaving each year is treated as the better position.")
OPP["nEligible"] = len(elig)
OPP["top"] = [row(r) for r in elig[:30]]
OPP["byTier"] = {
    t: [row(r) for r in elig if r["t"] == t][:10]
    for t in sorted({r["t"] for r in elig if r["t"]})
}

json.dump(SOW, io.open(SOW_PATH, "w", encoding="utf-8"), separators=(",", ":"))
print("\nwrote %s (%s bytes)" % (SOW_PATH, "{:,}".format(os.path.getsize(SOW_PATH))))
