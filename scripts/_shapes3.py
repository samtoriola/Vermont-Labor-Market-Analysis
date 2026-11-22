import io, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(io.open(os.path.join(H, "..", "data", n), encoding="utf-8"))
DEM, SOW = D("demand.json"), D("sow.json")
print("demand keys:", sorted(DEM.keys()))
for k in sorted(DEM.keys()):
    v = DEM[k]
    print("  %-14s %s" % (k, json.dumps(v)[:320]))
print()
print("sow.regions:", json.dumps(SOW["regions"])[:700])
