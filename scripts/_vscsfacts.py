"""Facts for the VSCS alignment prototype. Committed JSON only."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))

LC, SOW = D("lightcast.json"), D("sow.json")
V = SOW["vscs"]
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]

print("vscs keys:", sorted(V.keys()))
for k in ("totalCompletions", "nCip", "nSocLinked", "openAll", "openCred",
          "openingsCovered", "allocMovedPct", "credShare"):
    print("  %-18s %s" % (k, V.get(k)))
print()
print("byAward:", json.dumps(V["byAward"], indent=1)[:600])
print()
print("byInst:", json.dumps(V.get("byInst"), indent=1)[:400])
print()
print("byFamily[0]:", json.dumps(V["byFamily"][0], indent=1))
print()
fam = sorted(V["byFamily"], key=lambda r: -(r["linked"] / r["open"] * 100 if r["open"] else 0))
print("%-44s %9s %9s %8s %9s" % ("OCCUPATION GROUP", "OPENINGS", "GRADS", "RATIO", "JOBS"))
for r in fam:
    sh = (r["linked"] / r["open"] * 100) if r["open"] else None
    print("%-44s %9s %9.1f %7s %9s"
          % (r["f"][:44], f"{round(r['open']):,}", r["linked"],
             "—" if sh is None else "%.1f%%" % sh, f"{round(r['jobs']):,}"))
print()
tot_open = sum(r["open"] for r in V["byFamily"])
tot_link = sum(r["linked"] for r in V["byFamily"])
none_fam = [r for r in V["byFamily"] if not r["linked"]]
print("total openings across groups: %s | graduates: %.0f | overall %.1f%%"
      % (f"{round(tot_open):,}", tot_link, tot_link / tot_open * 100))
print("groups with no graduates at all: %d, holding %s openings"
      % (len(none_fam), f"{round(sum(r['open'] for r in none_fam)):,}"))
print()
print("under (fewest graduates per opening, paying above LW):")
for r in V["under"][:8]:
    print("   %-46s open %5s  grads %6.1f  ratio %s"
          % (r["n"][:46], round(r["open"]), r["linked"],
             "—" if r["ratio"] is None else "%.1f%%" % (r["ratio"] * 100)))
print()
print("over (most graduates per opening):")
for r in V["over"][:8]:
    print("   %-46s open %5s  grads %6.1f  ratio %s"
          % (r["n"][:46], round(r["open"]), r["linked"],
             "—" if r["ratio"] is None else "%.1f%%" % (r["ratio"] * 100)))

json.dump({"v": V, "lwa": LWA, "totOpen": tot_open, "totLink": tot_link,
           "openAllState": LC["openTotal"] / LC["openYears"]},
          io.open(os.path.join(H, "_vscsfacts.json"), "w", encoding="utf-8"))
print("\nwrote _vscsfacts.json")
