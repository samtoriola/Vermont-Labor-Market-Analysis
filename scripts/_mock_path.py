"""Writes the Pathways prototype page. Throwaway.

Three ways the Pathways tab could work, drawn in the dashboard's own visual
language so the options can be judged against the live app rather than against a
sketch. Every figure comes out of _pathfacts.py, which recomputes them from the
committed JSON -- no query is run.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(io.open(os.path.join(HERE, "_pathfacts.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "..", "_shots", "pathways-options.html")

ROWS = F["rows"]
FUN = {r["t"]: r for r in F["funnel"]}
LWA = F["lwa"]
R = {r["t"]: r for r in ROWS}
ORDER = [r["t"] for r in ROWS]


def money(v):
    return "$" + format(int(round(v)), ",")


def fmt(v):
    return format(int(round(v)), ",")


def k(v):
    return "$" + format(int(round(v / 1000)), ",") + "k"


# ---------------------------------------------------------------- chart A ---
# The ladder. One row per rung: the pooled p10-p90 span, the middle half heavier,
# the midpoint ticked, and the living wage ruled straight down the five. Two
# figure columns on the right, as the Overview carries.
def chart_a():
    W, padL, plotW, padT, rowH = 1180, 206, 772, 52, 64
    XMIN, XMAX = 25000, 225000
    H = padT + len(ORDER) * rowH + 34

    def X(v):
        return padL + (v - XMIN) / (XMAX - XMIN) * plotW

    s = []
    s.append('<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Annual pay '
             'by entry credential, tenth to ninetieth percentile">' % (W, H))
    for t in (50000, 100000, 150000, 200000):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (X(t), padT - 10, X(t), padT + len(ORDER) * rowH - 18))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%s</text>'
                 % (X(t), padT - 18, k(t)))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">JOBS</text>' % (1066, padT - 18))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">CLEARS IT</text>' % (1176, padT - 18))

    for i, t in enumerate(ORDER):
        r, b = R[t], R[t]["box"]
        cy = padT + i * rowH + 16
        s.append('<text class="clab" x="%d" y="%.1f" text-anchor="end">%s</text>'
                 % (padL - 14, cy + 4, t))
        # p10-p90 whisker
        s.append('<line class="whisk" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (X(b["p10"]), cy, X(b["p90"]), cy))
        for e in ("p10", "p90"):
            s.append('<line class="whisk" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (X(b[e]), cy - 7, X(b[e]), cy + 7))
        # middle half
        s.append('<rect class="iqr" x="%.1f" y="%.1f" width="%.1f" height="18" rx="2"/>'
                 % (X(b["p25"]), cy - 9, X(b["p75"]) - X(b["p25"])))
        # midpoint
        s.append('<line class="med" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (X(b["p50"]), cy - 13, X(b["p50"]), cy + 13))
        s.append('<text class="vlab" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                 % (X(b["p50"]), cy + 31, money(b["p50"])))
        s.append('<text class="fig" x="%d" y="%.1f" text-anchor="end">%s</text>'
                 % (1066, cy + 4, fmt(r["jobsAll"])))
        s.append('<text class="fig" x="%d" y="%.1f" text-anchor="end">%.0f%%</text>'
                 % (1176, cy + 4, r["above"]))
    # the living wage, ruled through all five
    s.append('<line class="rule" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
             % (X(LWA), padT - 10, X(LWA), padT + len(ORDER) * rowH - 10))
    s.append('<text class="rulelab" x="%.1f" y="%d">Living wage %s</text>'
             % (X(LWA) + 7, padT + len(ORDER) * rowH - 14, money(LWA)))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart B ---
# What a step buys. Four risers, bar length is the pay gain, right column is the
# gain in the share clearing the benchmark.
def chart_b():
    steps = []
    for i in range(1, len(ORDER)):
        a, b = R[ORDER[i - 1]], R[ORDER[i]]
        steps.append({
            "from": ORDER[i - 1], "to": ORDER[i],
            "pay": b["box"]["p50"] - a["box"]["p50"],
            "pts": b["above"] - a["above"],
        })
    W, padL, plotW, padT, rowH = 1180, 290, 690, 52, 70
    H = padT + len(steps) * rowH + 24
    mx = 35000

    def X(v):
        return padL + v / mx * plotW

    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Pay gain at each '
         'step up the credential ladder">' % (W, H)]
    for t in (10000, 20000, 30000):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (X(t), padT - 10, X(t), padT + len(steps) * rowH - 24))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">+%s</text>'
                 % (X(t), padT - 18, k(t)))
    s.append('<text class="colhead" x="1176" y="%d" text-anchor="end">CLEARS IT</text>' % (padT - 18))
    for i, st in enumerate(steps):
        y = padT + i * rowH
        big = st["pts"] > 20
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s <tspan class="arr">&#8594;</tspan> %s</text>'
                 % (padL - 14, y + 20, st["from"], st["to"]))
        s.append('<rect class="%s" x="%d" y="%d" width="%.1f" height="26" rx="3"/>'
                 % ("barhi" if big else "barlo", padL, y + 3, X(st["pay"]) - padL))
        s.append('<text class="vlab" x="%.1f" y="%d">+%s</text>'
                 % (X(st["pay"]) + 10, y + 22, money(st["pay"])))
        s.append('<text class="fig" x="1176" y="%d" text-anchor="end">+%.0f pts</text>'
                 % (y + 22, st["pts"]))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart C ---
# Which doors open. A nested funnel per rung over a shared count of occupations.
def chart_c():
    W, padL, plotW, padT, rowH = 1180, 206, 700, 52, 70
    H = padT + len(ORDER) * rowH + 24
    mx = max(FUN[t]["nAll"] for t in ORDER)

    def X(n):
        return n / mx * plotW

    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Occupations at each '
         'credential that hire in volume and pay a living wage">' % (W, H)]
    for t in (100, 200, 300):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (padL + X(t), padT - 10, padL + X(t), padT + len(ORDER) * rowH - 24))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d</text>'
                 % (padL + X(t), padT - 18, t))
    s.append('<text class="colhead" x="1176" y="%d" text-anchor="end">OPENINGS THAT PAY</text>'
             % (padT - 18))
    for i, t in enumerate(ORDER):
        f = FUN[t]
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 14, y + 21, t))
        s.append('<rect class="f1" x="%d" y="%d" width="%.1f" height="28" rx="3"/>'
                 % (padL, y + 2, X(f["nAll"])))
        s.append('<rect class="f2" x="%d" y="%d" width="%.1f" height="28" rx="3"/>'
                 % (padL, y + 2, X(f["nHiring"])))
        s.append('<rect class="f3" x="%d" y="%d" width="%.1f" height="28" rx="3"/>'
                 % (padL, y + 2, X(f["nPaying"])))
        s.append('<text class="vlab" x="%.1f" y="%d">%d of %d</text>'
                 % (padL + X(f["nAll"]) + 10, y + 21, f["nPaying"], f["nAll"]))
        sh = f["openPaying"] / f["openAll"] * 100
        s.append('<text class="fig" x="1176" y="%d" text-anchor="end">%s of %s</text>'
                 % (y + 21, fmt(f["openPaying"]), fmt(f["openAll"])))
        s.append('<text class="figsub" x="1176" y="%d" text-anchor="end">%.0f%%</text>'
                 % (y + 38, sh))
    s.append("</svg>")
    return "\n".join(s)


# -------------------------------------------------------------------- page ---
def srcblock(line, uses):
    rows = "".join("<tr><th>%s</th><td>%s</td></tr>" % (a, b) for a, b in uses)
    return ('<p class="src">%s</p>'
            '<details class="uses"><summary>What this chart uses</summary>'
            '<table>%s</table></details>' % (line, rows))


LW = F["lw"]
nf, hs, sb, ba, gr = (R[t] for t in ORDER)
step_hs = hs["box"]["p50"] - nf["box"]["p50"]
step_sb = sb["box"]["p50"] - hs["box"]["p50"]
step_ba = ba["box"]["p50"] - sb["box"]["p50"]
step_gr = gr["box"]["p50"] - ba["box"]["p50"]

CSS = r"""
:root{
  --s1:#009ba5; --ord1:#ccebed; --ord2:#99d7db; --ord3:#66c3c9; --ord4:#33afb7; --ord5:#009ba5;
  --ink:#16202a; --ink-2:#41505e; --ink-3:#74838f;
  --bg:#f7f8f8; --panel:#fff; --rule:#e4e8ea; --rule-2:#cfd6da; --track:#e8ecee; --cool:#e9f5f6;
  --display:'EB Garamond',Georgia,serif;
  --body:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --fig:'DM Mono',ui-monospace,'SF Mono',Menlo,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
  color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1280px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:30px 72px}
h1{font-family:var(--display);font-size:33px;line-height:1.15;margin:0 0 6px;
  font-weight:600;text-wrap:balance}
.sub{color:var(--ink-2);margin:0 0 6px;max-width:68ch}
.meta{color:var(--ink-3);font-size:13px;margin:0 0 30px}
h2{font-family:var(--display);font-size:25px;margin:0 0 4px;font-weight:600;text-wrap:balance}
.opt{margin:0 0 14px}
.opt .tag{display:inline-block;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--s1);font-weight:600;margin-bottom:3px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:9px;
  padding:20px 22px 16px;margin:0 0 30px}
.panel h3{font-family:var(--display);font-size:21px;margin:0 0 5px;font-weight:600;text-wrap:balance}
.cap{color:var(--ink-2);font-size:13.5px;margin:0 0 16px;max-width:92ch}
.chart{width:100%;height:auto;display:block;overflow:visible}
.cwrap{overflow-x:auto}
.note{background:var(--cool);border-left:3px solid var(--s1);border-radius:0 5px 5px 0;
  padding:11px 15px;margin:16px 0 0;font-size:14px;color:var(--ink)}
.src{color:var(--ink-3);font-size:11.5px;margin:16px 0 0;padding-top:11px;
  border-top:1px solid var(--rule);line-height:1.5}
.uses{margin:9px 0 0;font-size:12px}
.uses summary{color:var(--s1);cursor:pointer;font-weight:500}
.uses table{border-collapse:collapse;margin:9px 0 2px;width:100%}
.uses th{text-align:left;color:var(--ink-3);font-weight:500;white-space:nowrap;
  padding:3px 16px 3px 0;vertical-align:top;width:1%}
.uses td{padding:3px 0;color:var(--ink-2);font-family:var(--fig);font-size:11.5px}
.chips{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin:0 0 16px}
.chips .lab{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3);
  margin-right:5px}
.chip{border:1px solid var(--rule-2);border-radius:999px;padding:5px 14px;font-size:13px;
  color:var(--ink-2);background:var(--panel)}
.chip.on{background:var(--s1);border-color:var(--s1);color:#fff;font-weight:500}
.grid{stroke:var(--rule);stroke-width:1}
.tick,.elab{font-family:var(--fig);font-size:10px;fill:var(--ink-3)}
.colhead{font-family:var(--body);font-size:10px;letter-spacing:.09em;fill:var(--ink-3);font-weight:500}
.clab{font-family:var(--body);font-size:13px;fill:var(--ink)}
.clab .arr{fill:var(--ink-3)}
.vlab{font-family:var(--fig);font-size:12px;fill:var(--ink);font-weight:500}
.fig{font-family:var(--fig);font-size:12.5px;fill:var(--ink);font-weight:500}
.figsub{font-family:var(--fig);font-size:11px;fill:var(--ink-3)}
.whisk{stroke:var(--ord3);stroke-width:1.5}
.iqr{fill:var(--ord2)}
.med{stroke:var(--ord5);stroke-width:3;stroke-linecap:round}
.rule{stroke:var(--ink-2);stroke-width:1.5;stroke-dasharray:4 3}
.rulelab{font-family:var(--body);font-size:11px;fill:var(--ink-2)}
.barhi{fill:var(--ord5)}
.barlo{fill:var(--ord2)}
.f1{fill:var(--track)}
.f2{fill:var(--ord3)}
.f3{fill:var(--ord5)}
.legend{display:flex;flex-wrap:wrap;gap:17px;margin:0 0 13px;font-size:12px;color:var(--ink-2)}
.legend span{display:flex;align-items:center;gap:6px}
.legend i{width:13px;height:13px;border-radius:3px;display:inline-block}
table.fx{border-collapse:collapse;width:100%;font-size:13px}
table.fx th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);font-weight:500;padding:0 14px 7px 0;border-bottom:1px solid var(--rule)}
table.fx td{padding:7px 14px 7px 0;border-bottom:1px solid var(--rule);
  font-family:var(--fig);font-size:12.5px;color:var(--ink)}
table.fx td:first-child{font-family:var(--body);font-size:13.5px}
table.fx tr:last-child td{border-bottom:0}
.num{text-align:right}
.was{color:var(--ink-3)}
.rec{background:var(--panel);border:1px solid var(--s1);border-radius:9px;padding:20px 22px;
  margin:0 0 30px}
.rec h3{font-family:var(--display);font-size:21px;margin:0 0 7px;font-weight:600}
.rec ol{margin:0;padding-left:20px}
.rec li{margin:0 0 7px;color:var(--ink-2)}
.rec li strong{color:var(--ink)}
hr.sep{border:0;border-top:1px solid var(--rule);margin:40px 0 28px}
@media (max-width:620px){
  h1{font-size:26px} h2{font-size:21px} .panel{padding:16px 14px 13px}
  .cwrap{overflow-x:auto} .chart{min-width:700px}
}
"""

HTML = f"""<title>Vermont Pathways Prototype</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&family=EB+Garamond:wght@500;600&display=swap">
<style>{CSS}</style>

<div class="wrap">
  <h1>Pathways, rebuilt</h1>
  <p class="sub">Three ways the Pathways tab could answer its question — what each level of
  education leads to in Vermont, in jobs and in pay. Drawn in the dashboard's own visual
  language, so they can be judged against the live app.</p>
  <p class="meta">Every figure here is recomputed from the committed JSON by
  <code>scripts/_pathfacts.py</code>. No query was run. Benchmark: {LW}, {money(LWA)} a year.</p>

  <div class="panel">
    <h3>First, two numbers the tab currently gets wrong</h3>
    <p class="cap">Both defects are in the measures, not the charts, and both are already
    fixed elsewhere in the dashboard. Worth settling before choosing a layout, because they
    change what the charts say.</p>
    <table class="fx">
      <tr><th>Entry credential</th><th class="num">Clears the living wage</th>
          <th class="num">Tab says today</th><th class="num">Spread, p90 / p10</th>
          <th class="num">Tab says today</th></tr>
      {"".join(
        f'<tr><td>{r["t"]}</td><td class="num">{r["above"]:.1f}%</td>'
        f'<td class="num was">{r["aboveOld"]:.1f}%</td>'
        f'<td class="num">{r["spread"]:.2f}&times;</td>'
        f'<td class="num was">{r["spreadPub"]:.2f}&times;</td></tr>' for r in ROWS)}
    </table>
    <div class="note"><strong>Why.</strong> &ldquo;Clears the living wage&rdquo; is the median
    rule — it counts every job in an occupation on whichever side that occupation&rsquo;s
    midpoint falls. <code>lib/wage.js</code> replaced it on Wage quality; Pathways is the last
    place it survives. It reports that <strong>every</strong> graduate-level job clears the
    benchmark, which is not true of 445 of them. &ldquo;Spread&rdquo; reads the published tier
    ladder, which is the employment-weighted <em>mean</em> of its occupations&rsquo;
    percentiles — a mean of tenth percentiles is not the pooled tenth percentile, and it
    averages away the between-occupation spread that is most of the spread at a rung.</div>
    {srcblock(
      "Vermont occupation data, 2025 · 796 occupations, 781 with a published pay ladder · "
      "benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Figures", "data/lightcast.json → allOcc[].t, .j · data/percentiles.json → occ[], tiers[]"),
       ("Built by", "scripts/build.py, scripts/build_pct.py"),
       ("Upstream", "Lightcast Vermont occupation export; BLS OEWS wage percentiles 2025"),
       ("Computed", "lib/wage.js shareBelow() rolled up by entry credential; ladders pooled across member occupations weighted by employment")])}
  </div>

  <hr class="sep">

  <div class="opt">
    <span class="tag">Option A</span>
    <h2>The pay ladder</h2>
    <p class="sub">One chart in place of three. Each rung is drawn as the pay range its work
    actually covers, and the living wage is ruled straight down the five, so where the line
    cuts each rung <em>is</em> the sufficiency measure.</p>
  </div>

  <div class="panel">
    <div class="chips"><span class="lab">Measure</span>
      <span class="chip on">The pay ladder</span>
      <span class="chip">Share of jobs</span>
      <span class="chip">Which doors open</span></div>
    <h3>What does each rung of the ladder actually pay?</h3>
    <p class="cap">The middle bar is the middle half of the work at that entry credential;
    the whiskers reach the lowest- and highest-paid tenth; the heavy tick is the midpoint
    job. Pooled across the occupations at each rung and weighted by their employment, so
    the spread is the real one. Click a rung for the occupations inside it.</p>
    <div class="legend">
      <span><i style="background:var(--ord2)"></i>Middle half of the work</span>
      <span><i style="background:var(--ord5);width:3px;border-radius:0"></i>Midpoint job</span>
      <span><i style="background:var(--ord3);height:2px"></i>Lowest to highest-paid tenth</span>
    </div>
    <div class="cwrap">{chart_a()}</div>
    <div class="note">The ladder is not evenly spaced. The midpoint high-school job pays
    <strong>{money(hs["box"]["p50"])}</strong> — {money(hs["box"]["p50"] - LWA)} above a living
    wage for one adult, which is the margin the whole rung rests on. Half of
    Vermont&rsquo;s employment sits on the two rungs where the benchmark falls inside the
    middle half.</div>
    {srcblock(
      "Vermont occupation data, 2025 · " + fmt(F["pricedJobs"]) + " jobs with a published pay "
      "distribution · pooled across the occupations at each entry credential, weighted by "
      "employment · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Pay ladder", "data/percentiles.json → occ[].p10…p90 (BLS OEWS 2025, as published)"),
       ("Employment and credential", "data/lightcast.json → allOcc[].j, .t (Lightcast Vermont export, 2025)"),
       ("Benchmark", "data/lightcast.json → livingWage (MIT Living Wage, Vermont 2025)"),
       ("Built by", "scripts/build_pct.py, scripts/build.py, scripts/get_lw.py"),
       ("Computed in app", "pooled ladder + lib/wage.js shareBelow(), both in the browser so the selector moves them")])}
  </div>

  <div class="opt">
    <span class="tag">Option B</span>
    <h2>What a step buys</h2>
    <p class="sub">The same ladder read as four moves rather than five levels. This is the
    question a student or an advisor actually brings: what does the next credential get me?</p>
  </div>

  <div class="panel">
    <h3>What does moving up one rung buy?</h3>
    <p class="cap">The gain in what the midpoint job pays, and the gain in how much of the
    work clears a living wage, for each step up the ladder.</p>
    <div class="cwrap">{chart_b()}</div>
    <div class="note">Two of the four steps carry almost all of the gain. Finishing high
    school is worth <strong>+{money(step_hs)}</strong> and {hs["above"] - nf["above"]:.0f} points
    of living-wage clearance; a bachelor&rsquo;s over a sub-baccalaureate credential is worth
    <strong>+{money(step_ba)}</strong> and {ba["above"] - sb["above"]:.0f} points. The
    sub-baccalaureate step itself is worth +{money(step_sb)}, and the graduate step adds
    {gr["above"] - ba["above"]:.0f} points because the rung below it already clears at
    {ba["above"]:.0f}%.</div>
    {srcblock(
      "Vermont occupation data, 2025 · the difference between adjacent rungs, pooled "
      "midpoints · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Figures", "the Option A ladder, differenced between adjacent rungs"),
       ("Pay ladder", "data/percentiles.json → occ[].p10…p90 (BLS OEWS 2025)"),
       ("Employment and credential", "data/lightcast.json → allOcc[].j, .t (Lightcast, 2025)"),
       ("Not a causal claim", "a difference between two groups of jobs, not what one worker would gain")])}
  </div>

  <div class="opt">
    <span class="tag">Option C</span>
    <h2>Which doors open</h2>
    <p class="sub">The section that is a plain table today, drawn. It counts occupations
    rather than jobs, so it reads as how many doors a credential opens — and then asks how
    many of those doors lead anywhere.</p>
  </div>

  <div class="panel">
    <h3>Which credentials lead to work that both hires and pays?</h3>
    <p class="cap">Every Vermont occupation at each entry credential, narrowed twice: to
    those hiring in volume — at least {F["minOpen"]} openings a year — and then to those
    whose typical job pays a living wage. The right-hand column converts the same filter
    into annual openings.</p>
    <div class="legend">
      <span><i style="background:var(--track)"></i>All occupations</span>
      <span><i style="background:var(--ord3)"></i>Hiring {F["minOpen"]}+ a year</span>
      <span><i style="background:var(--ord5)"></i>And paying a living wage</span>
    </div>
    <div class="cwrap">{chart_c()}</div>
    <div class="note">At the bottom of the ladder the narrowing is brutal:
    <strong>{FUN["No formal credential"]["nPaying"]} of
    {FUN["No formal credential"]["nAll"]}</strong> occupations requiring no formal credential
    both hire in volume and pay a living wage —
    {fmt(FUN["No formal credential"]["openPaying"])} of
    {fmt(FUN["No formal credential"]["openAll"])} annual openings, or
    {FUN["No formal credential"]["openPaying"] / FUN["No formal credential"]["openAll"] * 100:.0f}%.
    The graduate rung reads lower than the bachelor&rsquo;s rung on that column only because
    {FUN["Graduate / professional"]["nAll"] - FUN["Graduate / professional"]["nHiring"]} of its
    {FUN["Graduate / professional"]["nAll"]} occupations are too small to clear the volume
    filter, not because the work pays less.</div>
    {srcblock(
      "Vermont occupation data, 2025 · entry credential · openings &ge; " + str(F["minOpen"]) +
      "/yr · occupation median against the benchmark · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Occupations and credential", "data/lightcast.json → allOcc[].t, .n"),
       ("Openings", "data/lightcast.json → allOcc[].o — Lightcast 2021–2025 openings ÷ 4"),
       ("Median pay", "data/lightcast.json → allOcc[].m (BLS OEWS 2025 median)"),
       ("Built by", "scripts/build.py"),
       ("Computed in app", "lib/data.js credentialFunnel()"),
       ("Caveat", "this column is the only place the median rule is still correct — it asks about the occupation, not about its jobs")])}
  </div>

  <hr class="sep">

  <div class="rec">
    <h3>What I would build</h3>
    <ol>
      <li><strong>Fix the two measures first</strong>, whichever layout you pick. They change
      the headline on three of the four current charts and one of them is visibly false at
      100%.</li>
      <li><strong>Option A as the default view</strong>, replacing the <em>Typical pay</em>,
      <em>Above living wage</em> and <em>Range of outcomes</em> chips with one chart. Those
      three are the same distribution asked three ways, and splitting them is what hides the
      step shape.</li>
      <li><strong>Keep a measure chip</strong> with two more entries:
      <em>Share of jobs</em> — the existing employment-share bars, which answer a different
      question and should stay — and <strong>Option C</strong>, which becomes a chart instead
      of a table.</li>
      <li><strong>Option B as the read-out</strong> rather than its own chart, if you would
      rather Pathways stayed at two sections. The step figures are a sentence under Option A,
      and the chart earns its place only if the step is the thing you want people to
      take away.</li>
    </ol>
  </div>
</div>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="").write(HTML)
print("wrote", os.path.abspath(OUT), len(HTML), "bytes")
