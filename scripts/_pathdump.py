import io, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
F = json.load(io.open(os.path.join(H, "_pathfacts.json"), encoding="utf-8"))
print("LWA", F["lwa"], "| lw", F["lw"], "| totalJobs", F["totalJobs"], "| priced", F["pricedJobs"])
for r in F["rows"]:
    b, p = r["box"], r["boxPub"]
    print("\n%s  jobsAll=%s share=%.1f nocc=%d open=%s" %
          (r["t"], f"{r['jobsAll']:,}", r["share"], r["nocc"], f"{round(r['open']):,}"))
    print("   pooled p10=%s p25=%s p50=%s p75=%s p90=%s" %
          tuple(f"${b[k]:,}" for k in ("p10", "p25", "p50", "p75", "p90")))
    print("   publis p10=%s p25=%s p50=%s p75=%s p90=%s" %
          tuple(f"${p[k]:,}" for k in ("p10", "p25", "p50", "p75", "p90")))
    print("   above=%.1f (was %.1f)  belowN=%s  spread=%.2f (pub %.2f)" %
          (r["above"], r["aboveOld"], f"{r['belowN']:,}", r["spread"], r["spreadPub"]))
print()
for r in F["funnel"]:
    print("%-26s occ=%3d hiring=%3d paying=%3d  open=%7s  openPaying=%7s (%.1f%%)  jobsPaying=%s" %
          (r["t"], r["nAll"], r["nHiring"], r["nPaying"], f"{round(r['openAll']):,}",
           f"{round(r['openPaying']):,}", r["openPaying"] / r["openAll"] * 100,
           f"{round(r['jobsPaying']):,}"))
